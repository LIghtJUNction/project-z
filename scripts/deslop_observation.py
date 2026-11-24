#!/usr/bin/env python3
"""Report architectural diagnostics on the recorded, public Project Z cohort."""

import argparse
import configparser
import json
import os
from pathlib import Path, PurePosixPath
import re
import signal
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor

OWNER_URL = re.compile(r"https://github\.com/LIghtJUNction/([A-Za-z0-9_.-]+)\.git", re.IGNORECASE)
PATH_PART = re.compile(r"[A-Za-z0-9_.-]+")
STATUSES = ("clean", "findings", "tool_error")
REPO_TIMEOUT = 45
SCAN_TIMEOUT = 240
MAX_WORKSPACES = 96
MAX_WORKERS = 3


def safe_path(value):
    if not isinstance(value, str) or any(
        not PATH_PART.fullmatch(part) or part in {".", "..", ".git"} or part.startswith("-")
        for part in value.split("/")
    ):
        raise ValueError(f"invalid catalog path: {value!r}")
    return PurePosixPath(value)


def run(argv, cwd, output, timeout, env=None, *, capture=None):
    # Kill the whole process group, not just the wrapper, when Cargo/RA hangs.
    stdout = capture if capture is not None else output
    stderr = output if capture is not None else subprocess.STDOUT
    with subprocess.Popen(argv, cwd=cwd, stdout=stdout, stderr=stderr,
                          start_new_session=True, env=env) as process:
        try:
            return process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
            print(f"Timed out after {timeout}s.", file=output, flush=True)
            return 2


def targets(root, selected):
    catalog = json.loads((root / "catalog.json").read_text(encoding="utf-8"))
    if catalog["schema_version"] != 1:
        raise ValueError("unknown Project Z catalog schema")
    cfg = configparser.ConfigParser(interpolation=None)
    with (root / ".gitmodules").open(encoding="utf-8") as source:
        cfg.read_file(source)
    urls = {cfg[s]["path"]: cfg[s]["url"] for s in cfg.sections()}
    results, skipped = [], []
    for repo in catalog["repositories"]:
        name = repo["name"]
        if selected and name not in selected:
            continue
        path = safe_path(repo["path"])
        url = repo["url"]
        owner_match = OWNER_URL.fullmatch(url)
        if not repo["manifests"] or owner_match is None:
            skipped.append(name)
            continue
        if safe_path(name).name != name or owner_match[1].casefold() != name.casefold():
            raise ValueError(f"repository name/path mismatch: {name!r}")
        if urls.get(str(path)) != url:
            raise ValueError(f"{name}: catalog URL differs from .gitmodules")
        sha = repo["commit"]
        line = subprocess.check_output(["git", "ls-tree", "HEAD", "--", str(path)],
                                       cwd=root, text=True).strip()
        if not re.fullmatch(r"[a-f0-9]{40}", sha) or line != f"160000 commit {sha}\t{path}":
            raise ValueError(f"{name}: catalog commit differs from HEAD gitlink")
        manifests = tuple(dict.fromkeys(safe_path(p) for p in repo["manifests"]))
        if any(p.name != "Cargo.toml" for p in manifests):
            raise ValueError(f"{name}: expected Cargo.toml manifest name")
        results.append((name, url, sha, manifests))
    if selected.difference(name for name, *_ in results):
        raise ValueError("unknown or ineligible selected repositories")
    count = sum(len(r[-1]) for r in results)
    if not 0 < count <= MAX_WORKSPACES:
        raise ValueError(f"workspace count {count} is outside 1..{MAX_WORKSPACES}")
    return results, sorted(skipped)


def workspace_root(directory, checkout, log):
    with tempfile.TemporaryFile(mode="w+", encoding="utf-8") as metadata:
        if run(["cargo", "metadata", "--locked", "--format-version=1"], directory,
               log, 30, capture=metadata):
            raise ValueError("Manifest could not be resolved with cargo metadata --locked.")
        metadata.seek(0)
        workspace = Path(json.load(metadata)["workspace_root"]).resolve()
    if not workspace.is_relative_to(checkout.resolve()):
        raise ValueError("Cargo workspace root escapes the recorded checkout")
    if not (workspace / "Cargo.toml").is_file() or (workspace / "Cargo.toml").is_symlink():
        raise ValueError("Cargo workspace manifest is missing or a symlink")
    return workspace


def scan_manifests(checkout, output, tool, repo, ready, git, git_env):
    name, _, sha, manifests = repo
    workspace_results = {}
    for i, manifest in enumerate(manifests, 1):
        log = f"{name}-{i}.log"
        directory = (checkout / str(manifest.parent)).resolve()
        code, workspace_path, reused = 2, None, False
        with (output / log).open("w", encoding="utf-8") as stream:
            if not ready:
                print(f"Recorded checkout unavailable. See {name}-checkout.log.", file=stream)
            elif (directory != checkout.resolve() / manifest.parent
                  or not (directory / "Cargo.toml").is_file()
                  or (directory / "Cargo.toml").is_symlink()):
                print(f"Manifest missing or unsafe: {manifest}", file=stream)
            else:
                try:
                    status_cmd = git + ["status", "--porcelain", "--untracked-files=no"]
                    if subprocess.check_output(status_cmd, cwd=checkout, env=git_env):
                        raise ValueError("recorded checkout already contains modifications")
                    workspace = workspace_root(directory, checkout, stream)
                    workspace_path = workspace.relative_to(checkout.resolve()).as_posix()
                    if workspace_path in workspace_results:
                        code, source_log = workspace_results[workspace_path]
                        reused = True
                        print(f"Same workspace and configuration; see {source_log}.", file=stream)
                    else:
                        code = run([tool], workspace, stream, SCAN_TIMEOUT)
                        if subprocess.check_output(status_cmd, cwd=checkout, env=git_env):
                            code = 2
                            print("Tracked files changed during analysis; findings are not accepted.",
                                  file=stream, flush=True)
                        workspace_results[workspace_path] = (code, log)
                except (OSError, subprocess.CalledProcessError, ValueError, KeyError, TypeError) as error:
                    print(f"Tool failed: {error}", file=stream, flush=True)
                    code = 2
        yield {"repo": name, "commit": sha, "manifest": str(manifest), "workspace": workspace_path,
               "reused": reused, "status": STATUSES[code] if code in (0, 1) else "tool_error",
               "log": log}


def scan_repo(output, tool, repo):
    name, url, sha, _ = repo
    # Each repo lives in its own ephemeral checkout, with neither the main
    # repository's credentials nor existing submodule overrides.
    git_env = dict(os.environ, GIT_TERMINAL_PROMPT="0", GIT_CONFIG_GLOBAL="/dev/null",
                   GIT_CONFIG_NOSYSTEM="1")
    git = ["git", "-c", "credential.helper=", "-c", "core.askPass="]
    with tempfile.TemporaryDirectory(prefix="project-z-deslop-") as tmp:
        checkout = Path(tmp)
        commands = (
            git + ["init", "--quiet"],
            git + ["fetch", "--depth=1", "--no-tags", "--", url, sha],
            git + ["checkout", "--quiet", "--detach", sha],
        )
        with (output / f"{name}-checkout.log").open("w", encoding="utf-8") as stream:
            ready = all(run(argv, checkout, stream, REPO_TIMEOUT, git_env) == 0 for argv in commands)
        return list(scan_manifests(checkout, output, tool, repo, ready, git, git_env))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path, help="new report directory")
    parser.add_argument("--repo", action="append", default=[], help="restrict to registered repository (repeatable)")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    chosen, skipped = targets(root, set(args.repo))
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        groups = pool.map(lambda repo: scan_repo(output, "deslop-please", repo), chosen)
        rows = [row for group in groups for row in group]
    statuses = {name: max((STATUSES.index(row["status"]) for row in rows if row["repo"] == name))
                for name, *_ in chosen}
    detected_workspaces = sum(row["workspace"] is not None and not row["reused"] for row in rows)
    duplicate_entries = sum(row["reused"] for row in rows)
    report = {"aggregate_commit": subprocess.check_output(["git", "rev-parse", "HEAD"],
                                                            cwd=root, text=True).strip(),
              "repositories": {name: STATUSES[code] for name, code in statuses.items()},
              "detected_workspaces": detected_workspaces, "duplicate_manifest_entries": duplicate_entries,
              "skipped": skipped, "workspaces": rows}
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    counts = ", ".join(f"{label}: {list(statuses.values()).count(i)}"
                       for i, label in enumerate(STATUSES))
    summary = [f"### Project Z architecture observation\n\n{counts}\n",
               f"{len(rows)} Cargo entries, {detected_workspaces} resolved workspace roots, "
               f"{duplicate_entries} duplicate entries reused.\n",
               "| Repository | Commit | Manifest | Workspace root | Status |", "| --- | --- | --- | --- | --- |"]
    for row in rows:
        workspace = row["workspace"]
        # Do not render an arbitrary path from child-tool output as Markdown.
        workspace = workspace if workspace and re.fullmatch(r"[A-Za-z0-9_./-]+", workspace) else "—"
        status = row["status"] + (" (reused)" if row["reused"] else "")
        summary.append(f"| {row['repo']} | `{row['commit'][:12]}` | `{row['manifest']}` | `{workspace}` | {status} |")
    message = "\n".join(summary) + "\n"
    print(message)
    if path := os.environ.get("GITHUB_STEP_SUMMARY"):
        with Path(path).open("a", encoding="utf-8") as target:
            target.write(message)
    # Architecture findings are reports; actual infrastructure errors are visible in this standalone job.
    return 2 if 2 in statuses.values() else 0


if __name__ == "__main__":
    raise SystemExit(main())
