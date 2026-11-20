#!/usr/bin/env python3
"""Inspect and verify the pinned Project Z repositories without Python dependencies."""

from __future__ import annotations

import argparse
import configparser
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
import tomllib
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from pathlib import Path

from cargo_versions import satisfies
from catalog_docs import render as render_catalog_docs

ROOT = Path(__file__).resolve().parents[1]
CATALOG = Path("catalog.json")
PATCH = Path(".cargo/project-z.toml")
PROJECTS = Path("docs/PROJECTS.md")


class CoordinationError(RuntimeError):
    pass


def command(argv, cwd=ROOT):
    result = subprocess.run(argv, cwd=cwd, capture_output=True, text=True)
    if result.returncode:
        raise CoordinationError(f"{' '.join(map(str, argv))}:\n{result.stderr.strip()}")
    return result.stdout


def relative(path, root=ROOT):
    try:
        return Path(path).resolve().relative_to(root.resolve()).as_posix()
    except ValueError as error:
        raise CoordinationError(f"path escapes coordination checkout: {path}") from error


def policy(root=ROOT):
    path = root / "project-z.toml"
    return tomllib.loads(path.read_text()) if path.exists() else {}


def repositories(root=ROOT):
    config = configparser.ConfigParser(interpolation=None)
    if not config.read(root / ".gitmodules"):
        raise CoordinationError("missing .gitmodules")
    result = []
    overrides = policy(root).get("repositories", {})
    for section in config.sections():
        path = config[section]["path"]
        if Path(path).is_absolute() or ".." in Path(path).parts:
            raise CoordinationError(f"invalid repository path: {path}")
        name = path
        source = root / path
        relative(source, root)
        if not (source / ".git").exists():
            raise CoordinationError(f"{name}: initialize the submodule first")
        options = overrides.get(name, {})
        manifests = options.get("manifests", ["Cargo.toml"] if (source / "Cargo.toml").exists() else [])
        result.append({
            "name": name,
            "path": path,
            "url": config[section]["url"],
            "branch": config[section].get("branch", "main"),
            "commit": command(["git", "rev-parse", "HEAD"], source).strip(),
            "role": options.get("role", "library"),
            "manifests": manifests,
            "requires": sorted(options.get("requires", [])),
        })
    unknown = set(overrides) - {repo["name"] for repo in result}
    if unknown:
        raise CoordinationError(f"policy contains unknown repositories: {', '.join(sorted(unknown))}")
    return sorted(result, key=lambda repo: repo["name"])


def explicit_version(manifest, workspace, dependency):
    """A path-only dependency need not satisfy the registry's prerelease rules."""
    data = tomllib.loads(Path(manifest).read_text())
    table = data
    if dependency.get("target"):
        # Cargo formats cfg expressions; TOML retains the author's whitespace.
        normalized = lambda value: "".join(re.findall(r'"(?:\\.|[^"\\])*"|[^\s]', value))
        wanted = normalized(dependency["target"])
        table = next((value for key, value in data.get("target", {}).items() if normalized(key) == wanted), {})
    section = {None: "dependencies", "normal": "dependencies", "dev": "dev-dependencies", "build": "build-dependencies"}[dependency.get("kind")]
    key = dependency.get("rename") or dependency["name"]
    declared = table.get(section, {}).get(key)
    if isinstance(declared, dict) and declared.get("workspace"):
        source = tomllib.loads((Path(workspace) / "Cargo.toml").read_text())
        declared = source.get("workspace", {}).get("dependencies", {}).get(key)
    return isinstance(declared, str) or isinstance(declared, dict) and "version" in declared


def metadata(repo, manifest, root=ROOT, resolve=False, options=()):
    source = root / repo["path"] / manifest
    relative(source, root / repo["path"])
    if not source.is_file():
        raise CoordinationError(f"{repo['name']}: missing {manifest}")
    args = ["cargo", "metadata", "--format-version", "1", "--manifest-path", str(source)]
    if not resolve:
        args.append("--no-deps")
    args.extend(options)
    return json.loads(command(args, root))


def inventory(root=ROOT):
    repos = repositories(root)
    tasks = [(repo, manifest) for repo in repos for manifest in repo["manifests"]]
    packages = []
    seen_manifests = set()
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda task: metadata(*task, root=root), tasks))
    for (repo, _), data in zip(tasks, results):
        members = set(data["workspace_members"])
        for package in data["packages"]:
            if package["id"] not in members:
                continue
            source_manifest = Path(package["manifest_path"]).resolve()
            if source_manifest in seen_manifests:
                continue
            seen_manifests.add(source_manifest)
            deps = []
            for dependency in package["dependencies"]:
                deps.append({
                    "name": dependency["name"],
                    "alias": dependency.get("rename"),
                    "requirement": dependency["req"],
                    "explicit_version": explicit_version(package["manifest_path"], data["workspace_root"], dependency),
                    "kind": dependency.get("kind") or "normal",
                    "target": dependency.get("target"),
                    "optional": dependency["optional"],
                    "default_features": dependency["uses_default_features"],
                    "features": sorted(dependency["features"]),
                    "source": dependency.get("source"),
                    "path": relative(dependency["path"], root) if dependency.get("path") else None,
                })
            packages.append({
                "name": package["name"],
                "version": package["version"],
                "repository": repo["name"],
                "manifest": relative(package["manifest_path"], root),
                "workspace": relative(data["workspace_root"], root),
                "publish": package["publish"] is None or "crates-io" in package["publish"],
                "rust_version": package.get("rust_version"),
                "library": any(set(target["kind"]) & {"lib", "rlib", "proc-macro", "cdylib", "staticlib"} for target in package["targets"]),
                "features": dict(sorted(package["features"].items())),
                "dependencies": sorted(deps, key=lambda dep: (dep["name"], dep["kind"], dep["target"] or "")),
            })
    return {"schema_version": 1, "repositories": repos, "packages": sorted(packages, key=lambda package: (package["name"], package["manifest"]))}


def package_map(data):
    result = {}
    for package in data["packages"]:
        name = package["name"]
        if name in result:
            raise CoordinationError(f"duplicate package {name}: {result[name]['manifest']} and {package['manifest']}")
        result[name] = package
    return result


def dependency_graph(data, include_dev=False):
    packages = package_map(data)
    return {
        name: {dep["name"] for dep in package["dependencies"] if dep["name"] in packages and (include_dev or dep["kind"] != "dev")}
        for name, package in packages.items()
    }


def ordered(graph):
    """Dependencies precede their consumers; independent packages are alphabetical."""
    pending = {name: set(deps) for name, deps in graph.items()}
    result = []
    while pending:
        ready = sorted(name for name, deps in pending.items() if not deps)
        if not ready:
            raise CoordinationError("dependency cycle: " + ", ".join(sorted(pending)))
        result.extend(ready)
        for name in ready:
            del pending[name]
        for deps in pending.values():
            deps.difference_update(ready)
    return result


def impact(data, changed):
    packages = package_map(data)
    repo_names = {repo["name"] for repo in data["repositories"]}
    unknown = set(changed) - packages.keys() - repo_names
    if unknown:
        raise CoordinationError("unknown package/repository: " + ", ".join(sorted(unknown)))
    affected = {name for name, package in packages.items() if name in changed or package["repository"] in changed}
    graph = dependency_graph(data, include_dev=True)
    while True:
        expanded = affected | {name for name, deps in graph.items() if deps & affected}
        if expanded == affected:
            break
        affected = expanded
    return [name for name in ordered(dependency_graph(data)) if name in affected]


def repository_impact(data, changed):
    """Include declared runtime and installer consumers beyond Cargo links."""
    packages = package_map(data)
    graph = {repo["name"]: set(repo.get("requires", [])) for repo in data["repositories"]}
    unknown = set(changed) - graph.keys() - packages.keys()
    if unknown:
        raise CoordinationError("unknown package/repository: " + ", ".join(sorted(unknown)))
    for name, dependencies in dependency_graph(data, include_dev=True).items():
        owner = packages[name]["repository"]
        graph[owner].update(packages[dependency]["repository"] for dependency in dependencies
                            if packages[dependency]["repository"] != owner)
    affected = {name if name in graph else packages[name]["repository"] for name in changed}
    while True:
        expanded = affected | {name for name, dependencies in graph.items() if dependencies & affected}
        if expanded == affected:
            return sorted(affected)
        affected = expanded


def equivalent_source(path, package, data, root=ROOT):
    """A nested gitlink may reuse exactly the same clean package source."""
    actual = (root / path).resolve()
    expected = (root / package["manifest"]).parent.resolve()
    if actual == expected:
        return True
    try:
        actual_repo = Path(command(["git", "rev-parse", "--show-toplevel"], actual).strip()).resolve()
        expected_repo = (root / next(repo["path"] for repo in data["repositories"] if repo["name"] == package["repository"])).resolve()
        if actual.relative_to(actual_repo) != expected.relative_to(expected_repo):
            return False
        if command(["git", "rev-parse", "HEAD"], actual_repo).strip() != command(["git", "rev-parse", "HEAD"], expected_repo).strip():
            return False
        for repo in [actual_repo, expected_repo]:
            if command(["git", "status", "--porcelain", "--untracked-files=normal"], repo):
                return False
        return True
    except (CoordinationError, ValueError, StopIteration):
        return False


def source_link_errors(data, rules, root=ROOT):
    """Verify explicitly shared source archives, including Cargo-excluded apps."""
    errors = []
    repos = {repo["name"]: repo for repo in data["repositories"]}
    for owner, options in rules.get("repositories", {}).items():
        links = options.get("source_links", {})
        if not isinstance(links, dict):
            errors.append(f"{owner}: source_links must map relative gitlink paths to repository names")
            continue
        for path, target_name in links.items():
            label = f"{owner}/{path!r} -> {target_name!r}"
            if (not isinstance(path, str) or not path or Path(path).is_absolute()
                    or "\\" in path or any(ord(c) < 32 or ord(c) == 127 for c in path)
                    or any(part in {"", ".", ".."} or part.lower() == ".git" for part in path.split("/"))):
                errors.append(f"{label}: invalid source link path")
                continue
            if owner not in repos or not isinstance(target_name, str) or target_name not in repos:
                errors.append(f"{label}: unknown source link repository")
                continue
            try:
                consumer = (root / repos[owner]["path"]).resolve()
                canonical = (root / repos[target_name]["path"]).resolve()
                relative(consumer, root)
                relative(canonical, root)
                nested = (consumer / path).resolve()
                relative(nested, consumer)
                entries = command(["git", "--literal-pathspecs", "ls-tree", "-z", "HEAD", "--", path], consumer)
                entries = entries.rstrip("\0").split("\0") if entries else []
                if len(entries) != 1:
                    raise CoordinationError("declared source link is missing from consumer HEAD")
                identity, recorded_path = entries[0].split("\t", 1)
                mode, kind, pinned = identity.split()
                if mode != "160000" or kind != "commit" or recorded_path != path:
                    raise CoordinationError("declared source link is not an exact gitlink in consumer HEAD")
                expected = repos[target_name]["commit"]
                if pinned != expected:
                    raise CoordinationError(f"pinned source {pinned} differs from snapshot {expected}")
                for checkout, wanted in [(consumer, repos[owner]["commit"]), (nested, pinned), (canonical, expected)]:
                    if not (checkout / ".git").exists():
                        raise CoordinationError(f"{relative(checkout, root)}: initialize the source repository first")
                    actual_root = Path(command(["git", "rev-parse", "--show-toplevel"], checkout).strip()).resolve()
                    if actual_root != checkout:
                        raise CoordinationError(f"{relative(checkout, root)}: source path is not its own repository")
                    if command(["git", "rev-parse", "HEAD"], checkout).strip() != wanted:
                        raise CoordinationError(f"{relative(checkout, root)}: checkout differs from its recorded source")
                    if command(["git", "status", "--porcelain", "--untracked-files=normal", "--ignore-submodules=none"], checkout):
                        raise CoordinationError(f"{relative(checkout, root)}: source checkout is not clean")
            except (CoordinationError, ValueError) as error:
                errors.append(f"{label}: {error}")
    return errors


def validate(data, rules, root=ROOT):
    packages = package_map(data)
    errors = source_link_errors(data, rules, root)
    forbidden = set(rules.get("policy", {}).get("forbidden_packages", []))
    repo_names = {repo["name"] for repo in data["repositories"]}
    for repo in data["repositories"]:
        missing = set(repo.get("requires", [])) - repo_names
        if missing:
            errors.append(f"{repo['name']}: unknown required repositories {', '.join(sorted(missing))}")
    for name, package in packages.items():
        if name in forbidden:
            errors.append(f"{package['manifest']}: retired package name {name}")
        for dep in package["dependencies"]:
            target = packages.get(dep["name"])
            if dep["name"] in forbidden:
                errors.append(f"{package['manifest']}: retired dependency {dep['name']}")
            if target is None:
                continue
            if dep["explicit_version"] or not dep["path"]:
                try:
                    compatible = satisfies(target["version"], dep["requirement"])
                except ValueError as error:
                    errors.append(f"{name} -> {dep['name']}: {error}")
                    continue
                if not compatible:
                    errors.append(f"{name} requires {dep['name']} {dep['requirement']}, snapshot has {target['version']}")
            if dep["source"] and dep["source"].startswith("git+"):
                errors.append(f"{name} -> {dep['name']}: Git source bypasses the shared crates.io patch; use a registry version or canonical path")
            if dep["path"] and not equivalent_source(dep["path"], target, data, root):
                errors.append(f"{name} -> {dep['name']}: noncanonical path {dep['path']} (expected {Path(target['manifest']).parent.as_posix()})")
    try:
        ordered(dependency_graph(data))
    except CoordinationError as error:
        errors.append(str(error))
    return errors


def patch_text(data, paths=None):
    lines = ["# Generated by scripts/project_z.py sync; paths are relative to the checkout root.", "[patch.crates-io]"]
    for name, package in sorted(package_map(data).items()):
        if package["publish"]:
            path = (paths or {}).get(name, Path(package["manifest"]).parent.as_posix())
            lines.append(f"{json.dumps(name)} = {{ path = {json.dumps(path)} }}")
    return "\n".join(lines) + "\n"


def workspace_patch_text(data, repo, manifest, root=ROOT):
    """Unify registry and explicit path dependencies without editing consumers.

    Cargo gives two clean copies different path identities even at the same
    commit. Explicit paths constrain the source; canonical registry patches
    are defaults. Select an entire verified repository, including its macros,
    and propagate the choice through transitive path dependencies.
    """
    packages = package_map(data)
    roots = {item["name"]: (root / item["path"]).resolve() for item in data["repositories"]}
    requested = relative(root / repo["path"] / manifest, root)
    workspaces = {item["workspace"] for item in packages.values()
                  if item["repository"] == repo["name"] and
                  (item["manifest"] == requested or
                   (Path(item["workspace"]) / "Cargo.toml").as_posix() == requested)}
    if len(workspaces) != 1:
        raise CoordinationError(f"{repo['name']}: cannot identify one workspace for {manifest}")
    workspace = workspaces.pop()
    members = {name for name, item in packages.items()
               if item["repository"] == repo["name"] and item["workspace"] == workspace}

    def dependencies(name):
        # Dependency workspaces do not pass their test-only packages to callers.
        return (dep for dep in packages[name]["dependencies"]
                if dep["kind"] != "dev" or name in members)

    reachable = set(members)
    pending = list(reachable)
    while pending:
        for dep in dependencies(pending.pop()):
            if dep["name"] in packages and dep["name"] not in reachable:
                reachable.add(dep["name"])
                pending.append(dep["name"])

    selected = {repo["name"]: roots[repo["name"]]}
    seen = set()
    while True:
        state = tuple(sorted((name, str(path)) for name, path in selected.items()))
        if state in seen:
            raise CoordinationError(f"{repo['name']}: path source choices do not converge")
        seen.add(state)
        constraints = {repo["name"]: {roots[repo["name"]]}}
        for name in sorted(reachable):
            item = packages[name]
            owner = item["repository"]
            actual_root = selected.get(owner, roots[owner])
            for dep in dependencies(name):
                target = packages.get(dep["name"])
                if target is None or not dep["path"]:
                    continue
                offset = os.path.relpath(root / dep["path"], roots[owner])
                actual = (actual_root / offset).resolve()
                relative(actual, root)
                if not equivalent_source(actual, target, data, root):
                    raise CoordinationError(f"{name} -> {dep['name']}: noncanonical path {relative(actual, root)}")
                target_owner = target["repository"]
                inner = (root / target["manifest"]).parent.resolve().relative_to(roots[target_owner])
                source_root = actual
                for _ in inner.parts:
                    source_root = source_root.parent
                # A member-to-member path follows its selected repository and
                # cannot turn that repository's soft default into a constraint.
                if target_owner == owner and source_root == actual_root:
                    continue
                constraints.setdefault(target_owner, set()).add(source_root)
        conflicts = {name: paths for name, paths in constraints.items() if len(paths) != 1}
        updated = {name: next(iter(paths)) for name, paths in constraints.items() if len(paths) == 1}
        updated.update({name: selected[name] for name in conflicts if name in selected})
        if updated == selected:
            if conflicts:
                detail = "; ".join(f"{name}: {', '.join(sorted(relative(path, root) for path in paths))}"
                                   for name, paths in sorted(conflicts.items()))
                raise CoordinationError(f"{repo['name']}: conflicting explicit path sources: {detail}")
            break
        selected = updated
    paths = {}
    for name, item in packages.items():
        owner = item["repository"]
        inner = (root / item["manifest"]).parent.resolve().relative_to(roots[owner])
        paths[name] = relative(selected.get(owner, roots[owner]) / inner, root)
    return patch_text(data, paths)


def generated(data):
    return {CATALOG: json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            PATCH: patch_text(data), PROJECTS: render_catalog_docs(data)}


def stale_generated(data, root=ROOT):
    return [f"{path}: stale; run python3 scripts/project_z.py sync"
            for path, content in generated(data).items()
            if not (root / path).exists() or (root / path).read_text() != content]


def cargo_invocation(cargo_args, manifest):
    """Keep Cargo options before the separator passed to a test or formatter."""
    index = cargo_args.index("--") if "--" in cargo_args else len(cargo_args)
    return ["cargo", *cargo_args[:index], "--manifest-path", str(manifest), *cargo_args[index:]]


def resolution_options(cargo_args):
    """Use the same feature, lockfile and network policy for the preflight."""
    if not cargo_args or cargo_args[0].startswith("+"):
        raise CoordinationError("use the checked-in toolchain and an explicit Cargo subcommand")
    head = cargo_args[:cargo_args.index("--")] if "--" in cargo_args else cargo_args
    options = []
    index = 1
    while index < len(head):
        arg = head[index]
        if arg in ("--all-features", "--no-default-features", "--locked", "--offline", "--frozen"):
            options.append(arg)
        elif arg in ("--features", "-F", "--target"):
            if index + 1 >= len(head):
                raise CoordinationError(f"missing value for {arg}")
            options.extend(["--filter-platform" if arg == "--target" else "--features", head[index + 1]])
            index += 1
        elif arg.startswith("--features="):
            options.append(arg)
        elif arg.startswith("-F") and len(arg) > 2:
            options.extend(["--features", arg[2:]])
        elif arg.startswith("--target="):
            options.append("--filter-platform=" + arg.split("=", 1)[1])
        elif arg in ("--config", "--manifest-path", "--lockfile-path") or any(arg.startswith(flag + "=") for flag in ("--config", "--manifest-path", "--lockfile-path")):
            raise CoordinationError(f"{arg}: managed by the coordinator; use a separate checkout for alternate configuration")
        index += 1
    return options


@contextmanager
def local_config(root=ROOT, content=None):
    """Make the same overrides visible to Cargo processes spawned by tests."""
    path = root / ".cargo/config.toml"
    content = (root / PATCH).read_text() if content is None else content
    owned = False
    if path.exists() or path.is_symlink():
        if path.read_text() != content:
            raise CoordinationError(".cargo/config.toml already contains another configuration; preserve it and use a separate checkout")
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x") as stream:
            stream.write(content)
        owned = True
    try:
        yield
    finally:
        if owned and path.exists() and path.read_text() == content:
            path.unlink()


def selected_repositories(data, names, downstream=False):
    packages = package_map(data)
    if downstream:
        selected = set(repository_impact(data, names))
    elif names:
        selected = set()
        repos = {repo["name"] for repo in data["repositories"]}
        for name in names:
            if name in repos:
                selected.add(name)
            elif name in packages:
                selected.add(packages[name]["repository"])
            else:
                raise CoordinationError(f"unknown package/repository: {name}")
    else:
        selected = {repo["name"] for repo in data["repositories"] if repo["role"] == "library"}
    order = []
    for name in ordered(dependency_graph(data)):
        repo = packages[name]["repository"]
        if repo in selected and repo not in order:
            order.append(repo)
    return [next(repo for repo in data["repositories"] if repo["name"] == name) for name in order]


def _lock_state(path):
    try:
        before = path.lstat()
    except FileNotFoundError:
        return None
    if not stat.S_ISREG(before.st_mode):
        raise CoordinationError(f"{path}: lockfile must be a regular file")
    content = path.read_bytes()
    after = path.lstat()
    fingerprint = lambda item: (item.st_dev, item.st_ino, item.st_size, item.st_mtime_ns, item.st_ctime_ns)
    if fingerprint(before) != fingerprint(after):
        raise CoordinationError(f"{path}: lockfile changed while being read; use a separate checkout")
    return content, stat.S_IMODE(after.st_mode), fingerprint(after)


@contextmanager
def preserved_workspace_locks(data, repo, root=ROOT):
    """Discard local-patch resolutions while preserving pre-existing user edits.

    Workspace roots come from Cargo's inventory, including virtual workspaces
    and member manifests. Use an isolated checkout for concurrent Cargo work.
    """
    workspaces = {package["workspace"] for package in data["packages"]
                  if package["repository"] == repo["name"]}
    snapshots = []
    for workspace in sorted(workspaces):
        path = root / workspace / "Cargo.lock"
        relative(path, root / repo["path"])
        snapshots.append((path, _lock_state(path)))

    def backup_original(path, original):
        descriptor, backup = tempfile.mkstemp(prefix=".Cargo.lock.project-z-", dir=path.parent)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(original[0])
            os.chmod(backup, original[1])
        except BaseException:
            Path(backup).unlink(missing_ok=True)
            raise
        return backup

    try:
        yield
    finally:
        errors = []
        for path, original in snapshots:
            backup = None
            backup_attempted = False
            try:
                observed = _lock_state(path)
                if (original[:2] if original else None) == (observed[:2] if observed else None):
                    continue
                if original is None:
                    if _lock_state(path) != observed:
                        raise CoordinationError(f"{path}: concurrent lockfile change; refusing to remove it")
                    path.unlink()
                    continue
                backup_attempted = True
                backup = backup_original(path, original)
                if _lock_state(path) != observed:
                    raise CoordinationError(f"{path}: concurrent lockfile change")
                os.replace(backup, path)
                backup = None
            except (CoordinationError, OSError) as error:
                detail = str(error)
                if original is not None:
                    if not backup_attempted:
                        try:
                            backup = backup_original(path, original)
                        except OSError as backup_error:
                            detail += f"; backup failed: {backup_error}"
                    if backup is not None:
                        detail += f"; original preserved at {backup}"
                    else:
                        detail += f"; original lockfile backup unavailable for {path}"
                errors.append(detail)
        if errors:
            raise CoordinationError("\n".join(errors))


def resolved_paths(data, repos, root=ROOT, options=()):
    canonical = package_map(data)
    errors = []
    for repo in repos:
        for manifest in repo["manifests"]:
            with local_config(root, workspace_patch_text(data, repo, manifest, root)):
                with preserved_workspace_locks(data, repo, root):
                    resolved = metadata(repo, manifest, root, resolve=True, options=options)
            for package in resolved["packages"]:
                expected = canonical.get(package["name"])
                if expected and not equivalent_source(Path(package["manifest_path"]).parent, expected, data, root):
                    errors.append(f"{repo['name']}: Cargo resolved {package['name']} {package['version']} outside the canonical checkout")
    return errors


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    commands = parser.add_subparsers(dest="action", required=True)
    commands.add_parser("sync", help="Regenerate inventory and every local registry patch")
    check = commands.add_parser("check", help="Check package names, version constraints, cycles and generated files")
    check.add_argument("--skip-generated", action="store_true")
    commands.add_parser("inventory", help="Print the current machine-readable inventory")
    commands.add_parser("order", help="List publishable packages in dependency order")
    graph = commands.add_parser("graph", help="Print the internal package dependency graph")
    graph.add_argument("--format", choices=["json", "mermaid"], default="json")
    affected = commands.add_parser("impact", help="Find transitive downstream packages")
    affected.add_argument("--repositories", action="store_true", help="Include runtime and installer consumers")
    affected.add_argument("names", nargs="+")
    resolve = commands.add_parser("resolve", help="Verify Cargo actually resolves local Project Z packages")
    resolve.add_argument("--all", action="store_true", help="Resolve every Rust workspace, including applications")
    resolve.add_argument("names", nargs="*")
    run = commands.add_parser("run", help="Run explicit Cargo arguments across selected repositories")
    run.add_argument("--repo", action="append", default=[])
    run.add_argument("--affected", action="append", default=[])
    run.add_argument("cargo_args", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        data = inventory(root)
        if args.action == "inventory":
            print(json.dumps(data, indent=2, ensure_ascii=False))
            return 0
        if args.action == "sync":
            for path, content in generated(data).items():
                destination = root / path
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(content)
            print(f"Updated {len(data['repositories'])} repositories and {len(data['packages'])} packages")
            return 0
        if args.action == "check":
            errors = validate(data, policy(root), root)
            if not args.skip_generated:
                errors.extend(stale_generated(data, root))
            if errors:
                raise CoordinationError("\n".join(errors))
            print(f"OK: {len(data['repositories'])} repositories, {len(data['packages'])} packages; versions and graph agree")
        elif args.action == "order":
            packages = package_map(data)
            for name in ordered(dependency_graph(data)):
                if packages[name]["publish"]:
                    print(f"{name}\t{packages[name]['version']}\t{packages[name]['repository']}")
        elif args.action == "impact":
            affected = repository_impact(data, args.names) if args.repositories else impact(data, args.names)
            print("\n".join(affected))
        elif args.action == "graph":
            dependencies = dependency_graph(data)
            if args.format == "json":
                print(json.dumps({name: sorted(deps) for name, deps in dependencies.items()}, indent=2))
            else:
                print("flowchart TD")
                ids = {name: f"p{index}" for index, name in enumerate(sorted(dependencies))}
                for name, deps in dependencies.items():
                    if deps or any(name in other for other in dependencies.values()):
                        print(f'    {ids[name]}["{name}"]')
                    for dep in sorted(deps):
                        print(f"    {ids[dep]} --> {ids[name]}")
        elif args.action == "resolve":
            if args.all and args.names:
                raise CoordinationError("choose --all or explicit package/repository names")
            errors = validate(data, policy(root), root) + stale_generated(data, root)
            if errors:
                raise CoordinationError("\n".join(errors))
            names = [repo["name"] for repo in data["repositories"] if repo["manifests"]] if args.all else args.names
            repos = selected_repositories(data, names)
            errors = resolved_paths(data, repos, root)
            if errors:
                raise CoordinationError("\n".join(errors))
            print(f"OK: local dependencies resolved in {len(repos)} repositories")
        elif args.action == "run":
            cargo_args = args.cargo_args[1:] if args.cargo_args[:1] == ["--"] else args.cargo_args
            if not cargo_args:
                raise CoordinationError("provide Cargo arguments after --, for example -- test --lib")
            if args.repo and args.affected:
                raise CoordinationError("choose --repo or --affected")
            errors = validate(data, policy(root), root) + stale_generated(data, root)
            if errors:
                raise CoordinationError("\n".join(errors))
            repos = selected_repositories(data, args.affected or args.repo, bool(args.affected))
            if not repos:
                raise CoordinationError("no Rust workspaces selected")
            errors = resolved_paths(data, repos, root, resolution_options(cargo_args))
            if errors:
                raise CoordinationError("\n".join(errors))
            failures = []
            for repo in repos:
                for manifest in repo["manifests"]:
                    with local_config(root, workspace_patch_text(data, repo, manifest, root)):
                        print(f"[{repo['name']}] cargo {' '.join(cargo_args)}", flush=True)
                        invocation = cargo_invocation(cargo_args, root / repo["path"] / manifest)
                        with preserved_workspace_locks(data, repo, root):
                            result = subprocess.run(invocation, cwd=root)
                        if result.returncode:
                            failures.append(f"{repo['name']}: exit {result.returncode}")
            if failures:
                raise CoordinationError("\n".join(failures))
    except (CoordinationError, OSError, ValueError, KeyError) as error:
        print(f"project-z: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
