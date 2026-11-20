#!/usr/bin/env python3
"""Audit upstream commits and releases; optionally prepare an isolated snapshot."""

from __future__ import annotations

import argparse
import configparser
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen
import uuid

ROOT = Path(__file__).resolve().parents[1]
GENERATED = ("catalog.json", ".cargo/project-z.toml", "docs/PROJECTS.md")


class MaintenanceError(RuntimeError):
    pass


def run(argv, root, timeout=90):
    try:
        result = subprocess.run([str(arg) for arg in argv], cwd=root,
                                capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise MaintenanceError(f"{argv[0]}: {error}") from error
    if result.returncode:
        raise MaintenanceError(f"{argv[0]} exited {result.returncode}: {result.stderr.strip()[-3000:]}")
    return result.stdout.strip()


def github_identity(url):
    match = re.fullmatch(r"(?:https://github\.com/|git@github\.com:|ssh://git@github\.com/)"
                        r"([A-Za-z0-9-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?/?", url)
    return tuple(match.groups()) if match else None


def modules(root, *, validate_branches=True):
    config = configparser.ConfigParser(interpolation=None)
    try:
        if not config.read(root / ".gitmodules", encoding="utf-8"):
            raise MaintenanceError("missing .gitmodules")
    except configparser.Error as error:
        raise MaintenanceError(f"invalid .gitmodules: {error}") from error
    result = []
    seen = set()
    for section in config.sections():
        values = config[section]
        path = values["path"]
        if (not path or path == "." or Path(path).is_absolute()
                or any(part in ("..", ".git") for part in Path(path).parts)
                or "\\" in path or any(ord(char) < 32 for char in path)):
            raise MaintenanceError(f"invalid submodule path: {path!r}")
        try:
            (root / path).resolve().relative_to(root.resolve())
        except ValueError as error:
            raise MaintenanceError(f"submodule path escapes checkout: {path}") from error
        if path in seen:
            raise MaintenanceError(f"duplicate submodule path: {path}")
        seen.add(path)
        branch = values.get("branch", "main")
        if branch == "." and validate_branches:
            branch = run(["git", "symbolic-ref", "--short", "HEAD"], root)
        if validate_branches:
            run(["git", "check-ref-format", f"refs/heads/{branch}"], root)
        result.append({"path": path, "url": values["url"], "branch": branch})
    return sorted(result, key=lambda row: row["path"])


def pinned_commit(root, path):
    fields = run(["git", "ls-tree", "HEAD", "--", path], root).split(maxsplit=3)
    if len(fields) != 4 or fields[:2] != ["160000", "commit"]:
        raise MaintenanceError(f"{path}: no committed gitlink at HEAD")
    return fields[2]


def load_catalog(root, required=False):
    path = root / "catalog.json"
    if required:
        raw = run(["git", "show", "HEAD:catalog.json"], root)
    else:
        raw = path.read_text(encoding="utf-8") if path.is_file() else run(
            [sys.executable, root / "scripts/project_z.py", "--root", root, "inventory"], root, 600)
    data = json.loads(raw)
    if (not isinstance(data, dict) or data.get("schema_version") != 1 or not isinstance(data.get("packages"), list)
            or not isinstance(data.get("repositories"), list)):
        raise MaintenanceError("unsupported catalog schema")
    for field, keys in (("repositories", ("path", "url", "commit")),
                        ("packages", ("name", "version", "repository"))):
        for row in data[field]:
            if not isinstance(row, dict) or any(not isinstance(row.get(key), str) for key in keys):
                raise MaintenanceError(f"invalid catalog {field} record")
    paths = [row["path"] for row in data["repositories"]]
    if len(paths) != len(set(paths)):
        raise MaintenanceError("duplicate catalog repository paths")
    return data


def upstream_status(root, module, timeout):
    pinned = pinned_commit(root, module["path"])
    ref = f"refs/heads/{module['branch']}"
    lines = run(["git", "ls-remote", "--refs", "--", module["url"], ref], root, timeout).splitlines()
    heads = [line.split()[0] for line in lines if line.split()[-1] == ref]
    if len(heads) != 1 or not re.fullmatch(r"[0-9a-f]{40,64}", heads[0]):
        raise MaintenanceError(f"{module['path']}: upstream branch not found: {ref}")
    return {**module, "pinned": pinned, "upstream": heads[0], "changed": pinned != heads[0]}


def registry_status(package, timeout=30):
    name, version = package["name"], package["version"]
    url = f"https://crates.io/api/v1/crates/{quote(name, safe='')}/{quote(version, safe='')}"
    request = Request(url, headers={
        "User-Agent": "project-z-maintenance/1 (https://github.com/LIghtJUNction/project-z)",
        "Accept": "application/json",
    })
    row = {"name": name, "version": version, "repository": package["repository"]}
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = json.load(response)
    except HTTPError as error:
        error.close()
        if error.code == 404:
            return {**row, "status": "missing"}
        raise MaintenanceError(f"crates.io {name}@{version}: HTTP {error.code}") from error
    except (OSError, URLError, ValueError, KeyError) as error:
        raise MaintenanceError(f"crates.io {name}@{version}: {error}") from error
    if not isinstance(payload, dict) or not isinstance(payload.get("version"), dict):
        raise MaintenanceError(f"crates.io malformed version record for {name}@{version}")
    record = payload["version"]
    if (record.get("num") != version or record.get("crate") != name
            or not isinstance(record.get("yanked"), bool)):
        raise MaintenanceError(f"crates.io returned another package/version for {name}@{version}")
    return {**row, "status": "yanked" if record.get("yanked") else "present"}


def candidate_repositories(rows, known, owner):
    """Names/topics are discovery hints, never an instruction to add a gitlink."""
    identities = {tuple(part.lower() for part in identity) for identity in known}
    result = []
    for row in rows:
        name = row.get("name", "")
        actual_owner = row.get("owner", {}).get("login", "")
        topics = row.get("topics") or []
        if actual_owner.lower() != owner.lower() or (actual_owner.lower(), name.lower()) in identities:
            continue
        hints = []
        if re.fullmatch(r"z[A-Za-z0-9_.-]+", name):
            hints.append("z-name")
        if "project-z" in topics:
            hints.append("project-z-topic")
        if not hints or row.get("archived") or row.get("fork"):
            continue
        result.append({"repository": f"{actual_owner}/{name}",
                       "url": f"https://github.com/{actual_owner}/{name}",
                       "description": row.get("description") or "",
                       "language": row.get("language"), "topics": topics,
                       "discovery_hints": hints, "requires_semantic_review": True})
    return sorted(result, key=lambda row: row["repository"].lower())


def audit(root, owner=None, workers=4, timeout=30, require_catalog=False):
    report = {"schema_version": 1, "created_at": datetime.now(timezone.utc).isoformat(),
              "root_head": run(["git", "rev-parse", "HEAD"], root),
              "source_dirty": bool(run(["git", "status", "--porcelain", "--untracked-files=normal",
                                         "--ignore-submodules=none"], root)),
              "upstreams": [], "registry": [], "candidates": [], "errors": []}
    known = modules(root)
    catalog = None
    try:
        catalog = load_catalog(root, required=require_catalog)
    except (MaintenanceError, ValueError, OSError) as error:
        report["errors"].append(f"catalog unavailable: {error}")
    catalog_repos = {row["path"]: row for row in catalog.get("repositories", [])} if catalog else {}
    for path in catalog_repos.keys() - {module["path"] for module in known}:
        report["errors"].append(f"{path}: catalog repository absent from .gitmodules")
    with ThreadPoolExecutor(max_workers=workers) as pool:
        jobs = [(module, pool.submit(upstream_status, root, module, timeout)) for module in known]
        for module, job in jobs:
            try:
                row = job.result()
                report["upstreams"].append(row)
                if catalog is not None:
                    entry = catalog_repos.get(module["path"])
                    if (entry is None or entry.get("commit") != row["pinned"] or entry.get("url") != row["url"]
                            or entry.get("branch", "main") != row["branch"]):
                        report["errors"].append(f"{module['path']}: catalog differs from committed gitlink/source")
            except MaintenanceError as error:
                report["errors"].append(str(error))
        packages = {(row["name"], row["version"]): row for row in catalog.get("packages", [])
                    if row.get("publish")} if catalog else {}
        jobs = [(key, pool.submit(registry_status, package, timeout)) for key, package in sorted(packages.items())]
        for key, job in jobs:
            try:
                report["registry"].append(job.result())
            except MaintenanceError as error:
                report["errors"].append(str(error))
    try:
        if owner is None:
            origin = github_identity(run(["git", "remote", "get-url", "origin"], root))
            if origin is None:
                raise MaintenanceError("cannot infer GitHub owner; provide --owner")
            owner = origin[0]
        if not re.fullmatch(r"[A-Za-z0-9-]+", owner):
            raise MaintenanceError("invalid GitHub owner")
        pages = json.loads(run(["gh", "api", "--paginate", "--slurp",
                               f"users/{owner}/repos?per_page=100&type=owner"], root, timeout * 3))
        if (not isinstance(pages, list) or any(not isinstance(page, list) for page in pages)
                or any(not isinstance(row, dict) or not isinstance(row.get("name"), str)
                       or not isinstance(row.get("owner"), dict)
                       or not isinstance(row["owner"].get("login"), str)
                       for page in pages for row in page)):
            raise MaintenanceError("malformed GitHub repository response")
        rows = [row for page in pages for row in page]
        identities = [identity for row in known if (identity := github_identity(row["url"]))]
        report["candidates"] = candidate_repositories(rows, identities, owner)
        report["owner"] = owner
    except (MaintenanceError, ValueError, TypeError) as error:
        report["errors"].append(f"GitHub discovery incomplete: {error}")
    report["needs_maintenance"] = bool(report["errors"] or report["candidates"]
                                       or any(row["changed"] for row in report["upstreams"])
                                       or any(row["status"] != "present" for row in report["registry"]))
    return report


def require_clean(root, seen=None):
    root = root.resolve()
    seen = set() if seen is None else seen
    if root in seen or Path(run(["git", "rev-parse", "--show-toplevel"], root)).resolve() != root:
        raise MaintenanceError(f"invalid or cyclic repository checkout: {root}")
    seen.add(root)
    status = run(["git", "status", "--porcelain", "--untracked-files=all", "--ignore-submodules=none"], root)
    if status:
        raise MaintenanceError("source checkout is dirty; preserve it and rerun from a clean checkout")
    if (root / ".gitmodules").is_file():
        for module in modules(root, validate_branches=False):
            child = root / module["path"]
            if (child / ".git").exists():
                require_clean(child, seen)
            elif child.exists() and any(child.iterdir()):
                raise MaintenanceError(f"uninitialized submodule contains local files: {child}")


def isolated_destination(root, destination, known):
    if destination.exists() or destination.is_symlink():
        raise MaintenanceError(f"worktree destination already exists: {destination}")
    destination = destination.resolve()
    if ".git" in destination.parts:
        raise MaintenanceError("worktree destination cannot be inside Git metadata")
    for ancestor in destination.parents:
        if not ancestor.exists():
            continue
        if not ancestor.is_dir():
            raise MaintenanceError("worktree parent is not a directory")
        if ((ancestor / "HEAD").is_file() and (ancestor / "objects").is_dir()
                and (ancestor / "config").is_file()):
            raise MaintenanceError("worktree destination cannot be inside a bare Git repository")
        if (ancestor / ".git").exists():
            if ancestor != root.resolve():
                raise MaintenanceError("worktree destination is inside another repository")
            for path in known:
                if destination.is_relative_to((root / path).resolve()):
                    raise MaintenanceError("worktree destination is inside a source submodule")
            try:
                run(["git", "check-ignore", "--quiet", "--no-index", "--",
                     str(destination.relative_to(root.resolve()))], root)
            except MaintenanceError as error:
                raise MaintenanceError("worktree destination inside source must be ignored staging") from error
            break
    return destination


def coordinate(root):
    output = {}
    for action in (("sync",), ("check",), ("resolve", "--all")):
        output[action[0]] = run([sys.executable, root / "scripts/project_z.py", "--root", root, *action], root, 600)
    return output


def apply_snapshot(root, report, destination=None):
    """Only this explicit entry point mutates Git, and only in a new worktree."""
    require_clean(root)
    if run(["git", "rev-parse", "HEAD"], root) != report["root_head"]:
        raise MaintenanceError("source HEAD changed during audit; rerun")
    if report["errors"]:
        raise MaintenanceError("audit is incomplete; resolve reported errors before applying")
    updates = [row for row in report["upstreams"] if row["changed"]]
    if not updates:
        return {"status": "no_changes"}
    known = {row["path"]: row for row in modules(root)}
    for row in updates:
        if row["path"] not in known or any(row[key] != known[row["path"]][key] for key in ("url", "branch")):
            raise MaintenanceError("apply plan contains a repository outside .gitmodules")
        if pinned_commit(root, row["path"]) != row["pinned"]:
            raise MaintenanceError("pinned gitlink changed during audit; rerun")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6]
    branch = "coord/maintenance-" + stamp
    destination = isolated_destination(root, destination or root / "dist/maintenance/worktrees" / stamp, known)
    run(["git", "worktree", "add", "-b", branch, destination, report["root_head"]], root)
    result = {"status": "blocked", "branch": branch, "worktree": str(destination), "base": report["root_head"]}
    try:
        run(["git", "-c", "submodule.recurse=false", "submodule", "update", "--init"], destination, 600)
        for row in updates:
            repository = destination / row["path"]
            require_clean(repository)
            run(["git", "fetch", "--no-tags", "origin", f"refs/heads/{row['branch']}"], repository, 120)
            if run(["git", "rev-parse", "FETCH_HEAD"], repository) != row["upstream"]:
                raise MaintenanceError(f"{row['path']}: upstream moved after audit; rerun in a new worktree")
            try:
                run(["git", "merge-base", "--is-ancestor", row["pinned"], row["upstream"]], repository)
            except MaintenanceError as error:
                raise MaintenanceError(f"{row['path']}: upstream is not a fast-forward; review the divergence") from error
            run(["git", "-c", "submodule.recurse=false", "checkout", "--detach", row["upstream"]], repository)
        # Populate nested trees only after their parent reaches its final pin.
        # Root update would reset new pins; old nested trees may have been removed.
        for path in known:
            repository = destination / path
            run(["git", "submodule", "sync", "--recursive"], repository, 600)
            run(["git", "submodule", "update", "--init", "--recursive"], repository, 600)
        result["validation"] = coordinate(destination)
        # A dirty submodule cannot be represented by a reproducible root gitlink.
        for path in known:
            require_clean(destination / path)
        for row in updates:
            if run(["git", "rev-parse", "HEAD"], destination / row["path"]) != row["upstream"]:
                raise MaintenanceError("an updated gitlink changed during validation")
        allowed = {row["path"] for row in updates} | set(GENERATED)
        changed = set(run(["git", "diff", "--name-only"], destination).splitlines())
        untracked = set(run(["git", "ls-files", "--others", "--exclude-standard"], destination).splitlines())
        if not (changed | untracked) <= allowed:
            raise MaintenanceError("validation changed files outside the expected snapshot")
        run(["git", "add", "--", *sorted(allowed)], destination)
        staged = set(run(["git", "diff", "--cached", "--name-only"], destination).splitlines())
        if not staged or not staged <= allowed:
            raise MaintenanceError("unexpected or empty staged snapshot")
        require_clean(root)
        if run(["git", "rev-parse", "HEAD"], root) != report["root_head"]:
            raise MaintenanceError("source HEAD changed during validation; review the isolated worktree")
        run(["git", "commit", "-m", "chore: coordinate verified upstream gitlinks"], destination)
        require_clean(destination)
        result.update(status="ready", commit=run(["git", "rev-parse", "HEAD"], destination),
                      updated=[row["path"] for row in updates],
                      push_command=["git", "-C", str(destination), "push", "origin", branch])
    except MaintenanceError as error:
        result["error"] = str(error)
    return result


def markdown(report):
    def cell(value):
        return str(value).replace("\n", " ").replace("|", "\\|").replace("`", "'")
    updates = [row for row in report.get("upstreams", []) if row["changed"]]
    missing = [row for row in report.get("registry", []) if row["status"] != "present"]
    candidates = report.get("candidates", [])
    errors = report.get("errors", [])
    lines = ["# Project Z maintenance audit", "", f"UTC: {report['created_at']}", "",
             f"Upstream updates: **{len(updates)}** · Missing/yanked versions: **{len(missing)}** · "
             f"Candidates for review: **{len(candidates)}** · Audit errors: **{len(errors)}**", ""]
    if report.get("source_dirty"):
        lines += ["The source checkout has local changes; automatic apply is blocked.", ""]
    if updates:
        lines += ["## Known upstream updates", "", "| Repository | Pinned | Observed upstream |", "|---|---|---|"]
        lines += [f"| {cell(row['path'])} | {row['pinned'][:12]} | {row['upstream'][:12]} |" for row in updates]
        lines.append("")
    if missing:
        lines += ["## Registry work", ""]
        lines += [f"- `{cell(row['name'])}@{cell(row['version'])}`: {row['status']}" for row in missing]
        lines.append("")
    if candidates:
        lines += ["## Candidates requiring semantic review", ""]
        lines += [f"- {cell(row['repository'])} ({cell(row['language'] or 'unknown language')}): "
                  f"{cell(row['description'])}" for row in candidates]
        lines += ["", "Candidates are not added automatically. Review package role, dependencies and system boundaries.", ""]
    if errors:
        lines += ["## Incomplete checks", "", *[f"- {cell(error)}" for error in errors], ""]
    if snapshot := report.get("snapshot"):
        lines += ["## Isolated snapshot", "", f"Status: **{snapshot['status']}**"]
        for key in ("branch", "worktree", "commit", "error"):
            if key in snapshot:
                lines.append(f"- {key}: `{cell(snapshot[key])}`")
        lines.append("")
    return "\n".join(lines) + "\n"


def write_atomic(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as stream:
        stream.write(text)
        temporary = Path(stream.name)
    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--owner", help="GitHub owner to inspect; defaults to origin's owner")
    parser.add_argument("--output", type=Path, help="machine JSON; default dist/maintenance/audit.json")
    parser.add_argument("--report", type=Path, help="Markdown; default dist/maintenance/summary.md")
    parser.add_argument("--workers", type=int, choices=range(1, 9), default=4)
    parser.add_argument("--timeout", type=int, choices=range(1, 301), default=30)
    parser.add_argument("--require-catalog", action="store_true",
                        help="read committed HEAD:catalog.json; never invoke Cargo or inventory")
    parser.add_argument("--apply", action="store_true", help="prepare a local commit in a new isolated worktree")
    parser.add_argument("--worktree", type=Path, help="new destination for --apply; must not exist")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    result = {"schema_version": 1, "created_at": datetime.now(timezone.utc).isoformat(), "errors": []}
    try:
        if args.worktree and not args.apply:
            raise MaintenanceError("--worktree requires --apply")
        result = audit(root, args.owner, args.workers, args.timeout, args.require_catalog)
        if args.apply:
            result["snapshot"] = apply_snapshot(root, result, args.worktree)
            if result["snapshot"]["status"] == "blocked":
                result["errors"].append(result["snapshot"]["error"])
    except (MaintenanceError, OSError, ValueError, KeyError) as error:
        result["errors"].append(str(error))
    result["needs_maintenance"] = bool(result.get("needs_maintenance") or result["errors"])
    text = markdown(result)
    write_atomic(args.output or root / "dist/maintenance/audit.json", json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    write_atomic(args.report or root / "dist/maintenance/summary.md", text)
    print(text, end="")
    return 2 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
