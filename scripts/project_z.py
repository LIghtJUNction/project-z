#!/usr/bin/env python3
"""Synchronize GitHub default branches and verify locked Project Z sources."""

from __future__ import annotations

import argparse
import configparser
import json
import re
import subprocess
import sys
import tomllib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from cargo_versions import satisfies
from catalog_docs import render as render_catalog_docs

ROOT = Path(__file__).resolve().parents[1]
CATALOG = Path("catalog.json")
PATCH = Path(".cargo/project-z.toml")
PROJECTS = Path("docs/PROJECTS.md")


class CoordinationError(RuntimeError):
    pass


def command(argv, cwd=ROOT, timeout=600):
    result = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, timeout=timeout)
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


def github_url(url):
    """Use one Cargo identity for a repository, with no branch/tag/revision."""
    if not re.fullmatch(r"https://github\.com/[A-Za-z0-9-]+/[A-Za-z0-9_.-]+\.git", url):
        raise CoordinationError(f"noncanonical GitHub URL: {url!r}; use https://github.com/<owner>/<repo>.git")
    return url


def github_identity(url):
    match = re.fullmatch(r"(?:https://github\.com/|git@github\.com:|ssh://git@github\.com/)"
                        r"([A-Za-z0-9-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?/?", url, re.IGNORECASE)
    return tuple(value.lower() for value in match.groups()) if match else None


def git_source_identity(source):
    if not source or not source.startswith("git+"):
        return None
    return github_identity(source[4:].split("#", 1)[0].split("?", 1)[0])


def default_head(url, root=ROOT, timeout=90):
    lines = command(["git", "ls-remote", "--symref", "--", url, "HEAD"], root, timeout).splitlines()
    branches = [line.split()[1].removeprefix("refs/heads/") for line in lines
                if line.startswith("ref: refs/heads/") and line.split()[-1] == "HEAD"]
    heads = [line.split()[0] for line in lines if not line.startswith("ref:")
             and len(line.split()) == 2 and line.split()[1] == "HEAD"]
    if len(branches) != 1 or len(heads) != 1 or not re.fullmatch(r"[0-9a-f]{40,64}", heads[0]):
        raise CoordinationError(f"{url}: cannot identify one default branch and HEAD")
    command(["git", "check-ref-format", "refs/heads/" + branches[0]], root)
    return {"branch": branches[0], "commit": heads[0]}


def latest_heads(repos, root=ROOT):
    with ThreadPoolExecutor(max_workers=4) as pool:
        values = list(pool.map(lambda repo: default_head(github_url(repo["url"]), root), repos))
    return {repo["name"]: value for repo, value in zip(repos, values)}


def freshness_errors(data, root=ROOT):
    heads = latest_heads(data["repositories"], root)
    return [f"{repo['name']}: snapshot {repo['commit']} ({repo['branch']}) differs from latest default "
            f"{heads[repo['name']]['commit']} ({heads[repo['name']]['branch']}); run sync and propagate consumers"
            for repo in data["repositories"]
            if any(repo[key] != heads[repo["name"]][key] for key in ("branch", "commit"))]


def repositories(root=ROOT):
    config = configparser.ConfigParser(interpolation=None)
    if not config.read(root / ".gitmodules"):
        raise CoordinationError("missing .gitmodules")
    result = []
    overrides = policy(root).get("repositories", {})
    recorded = json.loads((root / CATALOG).read_text()).get("repositories", []) if (root / CATALOG).exists() else []
    recorded_branches = {repo["name"]: repo.get("branch") for repo in recorded}
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
        default_ref = command(["git", "for-each-ref", "--format=%(symref)", "refs/remotes/origin/HEAD"], source).strip()
        result.append({
            "name": name,
            "path": path,
            "url": config[section]["url"],
            "branch": default_ref.removeprefix("refs/remotes/origin/") or recorded_branches.get(name),
            "commit": command(["git", "rev-parse", "HEAD"], source).strip(),
            "role": options.get("role", "library"),
            "manifests": manifests,
            "requires": sorted(options.get("requires", [])),
        })
    unknown = set(overrides) - {repo["name"] for repo in result}
    if unknown:
        raise CoordinationError(f"policy contains unknown repositories: {', '.join(sorted(unknown))}")
    return sorted(result, key=lambda repo: repo["name"])


def sync_sources(root=ROOT):
    """Advance only clean isolated submodule checkouts; never edit consumers."""
    repos = repositories(root)
    errors = checkout_errors({"repositories": repos}, root, allow_uninitialized=True)
    if errors:
        raise CoordinationError("\n".join(errors))
    heads = latest_heads(repos, root)
    for repo in repos:
        source = root / repo["path"]
        if repo["commit"] != heads[repo["name"]]["commit"]:
            if command(["git", "rev-parse", "--abbrev-ref", "HEAD"], source).strip() != "HEAD":
                raise CoordinationError(f"{repo['name']}: active branch; use a detached isolated checkout before sync")
    for repo in repos:
        source = root / repo["path"]
        wanted = heads[repo["name"]]
        branch = wanted["branch"]
        remote_ref = "refs/remotes/origin/" + branch
        command(["git", "fetch", "--no-tags", "--no-recurse-submodules", "--", repo["url"],
                 f"+refs/heads/{branch}:{remote_ref}"], source)
        if command(["git", "rev-parse", remote_ref], source).strip() != wanted["commit"]:
            raise CoordinationError(f"{repo['name']}: default branch moved during sync; inspect and synchronize again")
        command(["git", "symbolic-ref", "refs/remotes/origin/HEAD", remote_ref], source)
        if repo["commit"] != wanted["commit"]:
            command(["git", "-c", "submodule.recurse=false", "checkout", "--detach", wanted["commit"]], source)
    # Check recorded nested pins before recursive fetch can recover old history.
    data = {"repositories": repositories(root)}
    errors = source_link_errors(data, policy(root), root, check_checkouts=False)
    if errors:
        raise CoordinationError("\n".join(errors))
    for repo in repos:
        source = root / repo["path"]
        command(["git", "submodule", "sync", "--recursive"], source)
        command(["git", "submodule", "update", "--init", "--recursive", "--jobs", "1"], source)


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


def verify_source_checkout(checkout, wanted, root=ROOT, *, checked=None, allow_uninitialized=False):
    """Check every recorded gitlink directly; parent status can hide descendants."""
    source = Path(checkout)
    checkout = source.resolve()
    label = relative(checkout, root)
    checked = set() if checked is None else checked
    if (checkout, wanted) in checked:
        return
    if not (checkout / ".git").exists():
        if allow_uninitialized and not source.is_symlink() and (
                not source.exists() or (source.is_dir() and not any(source.iterdir()))):
            return
        raise CoordinationError(f"{label}: initialize the source repository first; preserve any local files")
    actual_root = Path(command(["git", "rev-parse", "--show-toplevel"], checkout).strip()).resolve()
    if actual_root != checkout:
        raise CoordinationError(f"{label}: source path is not its own repository")
    if command(["git", "rev-parse", "HEAD"], checkout).strip() != wanted:
        raise CoordinationError(f"{label}: checkout differs from its recorded source")
    entries = command(["git", "ls-tree", "-r", "-z", "HEAD"], checkout)
    for entry in filter(None, entries.split("\0")):
        identity, path = entry.split("\t", 1)
        mode, kind, pinned = identity.split()
        if mode != "160000":
            continue
        nested = checkout / path
        relative(nested, checkout)
        if nested.resolve() == checkout or kind != "commit":
            raise CoordinationError(f"{label}/{path}: invalid nested source repository")
        verify_source_checkout(nested, pinned, root, checked=checked, allow_uninitialized=allow_uninitialized)
    if command(["git", "status", "--porcelain", "--untracked-files=normal", "--ignore-submodules=none"], checkout):
        raise CoordinationError(f"{label}: source checkout is not clean")
    checked.add((checkout, wanted))


def source_link_errors(data, rules, root=ROOT, *, check_checkouts=True):
    """Verify every registered cross-repository gitlink, including excluded apps."""
    errors = []
    checked = set()
    repos = {repo["name"]: repo for repo in data["repositories"]}
    identities = {github_identity(repo["url"]): repo["name"] for repo in repos.values()
                  if repo.get("url") and github_identity(repo["url"])}
    link_rules = {name: dict(options) for name, options in rules.get("repositories", {}).items()}
    for repo in repos.values():
        module_file = root / repo.get("path", repo["name"]) / ".gitmodules"
        if not module_file.exists():
            continue
        config = configparser.ConfigParser(interpolation=None)
        config.read(module_file)
        options = link_rules.setdefault(repo["name"], {})
        links = options.get("source_links", {})
        if not isinstance(links, dict):
            continue
        options["source_links"] = links = dict(links)
        for section in config.sections():
            target = identities.get(github_identity(config[section]["url"]))
            if target:
                path = config[section]["path"]
                if path in links and links[path] != target:
                    errors.append(f"{repo['name']}/{path}: source_links disagrees with .gitmodules")
                links[path] = target
    for owner, options in link_rules.items():
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
                if not check_checkouts:
                    continue
                for checkout, wanted in [(consumer, repos[owner]["commit"]), (nested, pinned), (canonical, expected)]:
                    verify_source_checkout(checkout, wanted, root, checked=checked)
            except (CoordinationError, ValueError) as error:
                errors.append(f"{label}: {error}")
    return errors


def validate(data, rules, root=ROOT):
    packages = package_map(data)
    errors = source_link_errors(data, rules, root)
    forbidden = set(rules.get("policy", {}).get("forbidden_packages", []))
    repo_names = {repo["name"] for repo in data["repositories"]}
    repos = {repo["name"]: repo for repo in data["repositories"]}
    identities = {github_identity(repo.get("url", "")) for repo in repos.values()} - {None}
    for repo in data["repositories"]:
        if repo.get("url"):
            try:
                github_url(repo["url"])
            except CoordinationError as error:
                errors.append(f"{repo['name']}: {error}")
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
                if git_source_identity(dep["source"]) in identities:
                    errors.append(f"{name} -> {dep['name']}: package from a registered repository is missing from the catalog")
                continue
            if dep["explicit_version"]:
                try:
                    compatible = satisfies(target["version"], dep["requirement"])
                except ValueError as error:
                    errors.append(f"{name} -> {dep['name']}: {error}")
                    continue
                if not compatible:
                    errors.append(f"{name} requires {dep['name']} {dep['requirement']}, snapshot has {target['version']}")
            if target["repository"] == package["repository"]:
                expected_path = (root / target["manifest"]).parent.resolve()
                if dep["source"] or not dep["path"] or (root / dep["path"]).resolve() != expected_path:
                    errors.append(f"{name} -> {dep['name']}: same-repository dependency must use its workspace/path source")
            else:
                expected_source = "git+" + repos[target["repository"]]["url"]
                if dep["source"] != expected_source or dep["path"]:
                    errors.append(f"{name} -> {dep['name']}: use {expected_source} at its default branch, without path, branch, tag or rev")
                if package["publish"] and dep["kind"] != "dev" and not dep["explicit_version"]:
                    errors.append(f"{name} -> {dep['name']}: keep version metadata beside Git for a publishable normal/build dependency")
    errors.extend(internal_override_errors(data, root))
    try:
        ordered(dependency_graph(data))
    except CoordinationError as error:
        errors.append(str(error))
    return errors


def internal_override_errors(data, root=ROOT):
    """Local patches must not hide a stale registry or Git dependency."""
    names = set(package_map(data))
    paths = {root / package["workspace"] / "Cargo.toml" for package in data["packages"]}
    for base in [root, *(root / repo["path"] for repo in data["repositories"] if repo.get("path"))]:
        paths.update(base / ".cargo" / name for name in ("config", "config.toml"))
    errors = []
    for path in sorted(paths):
        if not path.exists():
            continue
        document = tomllib.loads(path.read_text())
        tables = [document.get("replace", {}), *document.get("patch", {}).values()]
        for table in tables:
            for key, value in table.items():
                name = value.get("package", key.split(":", 1)[0]) if isinstance(value, dict) else key.split(":", 1)[0]
                if name in names:
                    errors.append(f"{relative(path, root)}: internal source override for {name}; remove it and update the Git dependency")
    if (root / PATCH).exists():
        errors.append(f"{PATCH}: obsolete registry override; run sync to remove it")
    return errors


def generated(data):
    return {CATALOG: json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            PROJECTS: render_catalog_docs(data)}


def stale_generated(data, root=ROOT):
    return [f"{path}: stale; run python3 scripts/project_z.py sync"
            for path, content in generated(data).items()
            if not (root / path).exists() or (root / path).read_text() != content]


def checkout_errors(data, root=ROOT, *, allow_uninitialized=False):
    errors = []
    checked = set()
    for repo in data["repositories"]:
        try:
            verify_source_checkout(root / repo["path"], repo["commit"], root,
                                   checked=checked, allow_uninitialized=allow_uninitialized)
        except (CoordinationError, ValueError) as error:
            errors.append(str(error))
    return errors


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


def locked_cargo_args(cargo_args):
    if cargo_args[0] in {"update", "generate-lockfile"}:
        raise CoordinationError("update lockfiles in each consumer repository, validate and commit them, then sync the aggregate")
    locked_commands = {"build", "check", "test", "bench", "clippy", "doc", "run", "rustc", "rustdoc", "metadata", "tree", "package", "publish", "fetch"}
    head = cargo_args[:cargo_args.index("--")] if "--" in cargo_args else cargo_args
    if cargo_args[0] in locked_commands and not any(flag in head for flag in ("--locked", "--frozen")):
        return [cargo_args[0], "--locked", *cargo_args[1:]]
    return cargo_args


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


def locked_source_errors(data, repos, root=ROOT):
    canonical = package_map(data)
    sources = {repo["name"]: repo for repo in data["repositories"]}
    identities = {github_identity(repo.get("url", "")) for repo in sources.values()} - {None}
    errors = []
    for repo in repos:
        workspaces = {package["workspace"] for package in data["packages"] if package["repository"] == repo["name"]}
        for workspace in sorted(workspaces):
            lock = root / workspace / "Cargo.lock"
            relative(lock, root / repo["path"])
            if lock.is_symlink() or not lock.is_file():
                errors.append(f"{workspace}/Cargo.lock: missing regular lockfile; refresh and commit it in the consumer repository")
                continue
            document = tomllib.loads(lock.read_text())
            for package in [*document.get("package", []), *document.get("patch", {}).get("unused", [])]:
                expected = canonical.get(package["name"])
                if not expected:
                    if git_source_identity(package.get("source")) in identities:
                        errors.append(f"{workspace}/Cargo.lock: internal package {package['name']} is missing from the catalog")
                    continue
                owner = sources[expected["repository"]]
                source = None if owner["name"] == repo["name"] else f"git+{owner['url']}#{owner['commit']}"
                if package.get("source") != source or package["version"] != expected["version"]:
                    errors.append(f"{workspace}/Cargo.lock: stale internal {package['name']} {package['version']} from {package.get('source')!r}; "
                                  f"expected {expected['version']} from {source!r}; update and commit the consumer lock")
    return errors


def resolved_paths(data, repos, root=ROOT, options=()):
    canonical = package_map(data)
    sources = {repo["name"]: repo for repo in data["repositories"]}
    identities = {github_identity(repo.get("url", "")) for repo in sources.values()} - {None}
    errors = locked_source_errors(data, repos, root)
    if errors:
        return errors
    options = list(options)
    if not any(flag in options for flag in ("--locked", "--frozen")):
        options.append("--locked")
    for repo in repos:
        for manifest in repo["manifests"]:
            resolved = metadata(repo, manifest, root, resolve=True, options=options)
            for package in resolved["packages"]:
                expected = canonical.get(package["name"])
                if expected:
                    owner = sources[expected["repository"]]
                    if owner["name"] == repo["name"]:
                        matches = (package.get("source") is None and
                                   Path(package["manifest_path"]).resolve() == (root / expected["manifest"]).resolve())
                    else:
                        matches = package.get("source") == f"git+{owner['url']}#{owner['commit']}"
                    if not matches or package["version"] != expected["version"]:
                        errors.append(f"{repo['name']}: Cargo resolved {package['name']} {package['version']} from "
                                      f"{package.get('source')!r}, outside the recorded Git source")
                elif git_source_identity(package.get("source")) in identities:
                    errors.append(f"{repo['name']}: resolved internal package {package['name']} is missing from the catalog")
    return errors


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    commands = parser.add_subparsers(dest="action", required=True)
    sync = commands.add_parser("sync", help="Fetch latest default branches and record their exact source identities")
    sync.add_argument("--record", action="store_true", help="Only record already selected sources; check still verifies remote freshness")
    check = commands.add_parser("check", help="Check Git source policy, locked commits, remote freshness and generated files")
    check.add_argument("--skip-generated", action="store_true")
    commands.add_parser("inventory", help="Print the current machine-readable inventory")
    commands.add_parser("order", help="List publishable packages in dependency order")
    graph = commands.add_parser("graph", help="Print the internal package dependency graph")
    graph.add_argument("--format", choices=["json", "mermaid"], default="json")
    affected = commands.add_parser("impact", help="Find transitive downstream packages")
    affected.add_argument("--repositories", action="store_true", help="Include runtime and installer consumers")
    affected.add_argument("names", nargs="+")
    resolve = commands.add_parser("resolve", help="Verify Cargo --locked resolves the recorded GitHub sources")
    resolve.add_argument("--all", action="store_true", help="Resolve every Rust workspace, including applications")
    resolve.add_argument("names", nargs="*")
    run = commands.add_parser("run", help="Run explicit Cargo arguments across selected repositories")
    run.add_argument("--repo", action="append", default=[])
    run.add_argument("--affected", action="append", default=[])
    run.add_argument("cargo_args", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        if args.action == "sync" and not args.record:
            sync_sources(root)
        data = inventory(root)
        if args.action == "inventory":
            print(json.dumps(data, indent=2, ensure_ascii=False))
            return 0
        if args.action == "sync":
            legacy = root / PATCH
            if legacy.exists():
                if not legacy.read_text().startswith("# Generated by scripts/project_z.py sync;"):
                    raise CoordinationError(f"{PATCH}: unrecognized configuration; preserve it and remove internal overrides explicitly")
                legacy.unlink()
            for path, content in generated(data).items():
                destination = root / path
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(content)
            print(f"Recorded {len(data['repositories'])} repositories and {len(data['packages'])} packages; run check and resolve --all")
            return 0
        if args.action == "check":
            errors = validate(data, policy(root), root) + checkout_errors(data, root)
            errors.extend(locked_source_errors(data, selected_repositories(data, [repo['name'] for repo in data['repositories'] if repo['manifests']]), root))
            if not args.skip_generated:
                errors.extend(stale_generated(data, root))
            if not errors:
                errors.extend(freshness_errors(data, root))
            if errors:
                raise CoordinationError("\n".join(errors))
            print(f"OK: {len(data['repositories'])} repositories, {len(data['packages'])} packages; Git sources, locks and latest default heads agree")
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
            errors = validate(data, policy(root), root) + stale_generated(data, root) + checkout_errors(data, root)
            if errors:
                raise CoordinationError("\n".join(errors))
            names = [repo["name"] for repo in data["repositories"] if repo["manifests"]] if args.all else args.names
            repos = selected_repositories(data, names)
            errors = resolved_paths(data, repos, root)
            if errors:
                raise CoordinationError("\n".join(errors))
            print(f"OK: locked Git sources resolved in {len(repos)} repositories")
        elif args.action == "run":
            cargo_args = args.cargo_args[1:] if args.cargo_args[:1] == ["--"] else args.cargo_args
            if not cargo_args:
                raise CoordinationError("provide Cargo arguments after --, for example -- test --lib")
            cargo_args = locked_cargo_args(cargo_args)
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
                    print(f"[{repo['name']}] cargo {' '.join(cargo_args)}", flush=True)
                    invocation = cargo_invocation(cargo_args, root / repo["path"] / manifest)
                    result = subprocess.run(invocation, cwd=root)
                    if result.returncode:
                        failures.append(f"{repo['name']}: exit {result.returncode}")
            if failures:
                raise CoordinationError("\n".join(failures))
    except (CoordinationError, OSError, ValueError, KeyError, configparser.Error, subprocess.TimeoutExpired) as error:
        print(f"project-z: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
