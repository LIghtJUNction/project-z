#!/usr/bin/env python3
"""Stage a reviewable Cargo registry projection; never publish or mutate source."""

from __future__ import annotations

import argparse
import configparser
from datetime import date, datetime, time
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import tarfile
import tempfile
import tomllib

from cargo_versions import satisfies


ROOT = Path(__file__).resolve().parents[1]
DEPS = ("dependencies", "build-dependencies", "dev-dependencies")
GITHUB = re.compile(r"https://github\.com/([A-Za-z0-9-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?/?", re.I)
SHA = re.compile(r"(?:[a-f0-9]{40}|[a-f0-9]{64})")
NUMBER = r"(0|[1-9][0-9]*)"
STABLE = re.compile(rf"{NUMBER}\.{NUMBER}\.{NUMBER}")
SEMVER = re.compile(
    STABLE.pattern + r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
)


class ProjectionError(ValueError):
    pass


def git(repo, *args, stdout=subprocess.PIPE):
    return subprocess.run(
        ["git", "-C", str(repo), *args], check=True, stdout=stdout, stderr=subprocess.PIPE,
        env={**os.environ, "GIT_NO_REPLACE_OBJECTS": "1"},
    ).stdout


def require_commit(repo, value):
    if not SHA.fullmatch(value) or git(repo, "rev-parse", "--verify", value + "^{commit}").decode().strip() != value:
        raise ProjectionError("--commit must be the full object ID of an existing commit")


def relative_manifest(value):
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or path.name != "Cargo.toml" or ":" in value or "\\" in value:
        raise ProjectionError("manifest paths must be repository-relative Cargo.toml paths")
    return path


def github_url(value):
    match = GITHUB.fullmatch(value) if isinstance(value, str) else None
    if match and match[2] not in (".", ".."):
        return "https://github.com/" + "/".join(part.lower() for part in match.groups())
    return None


def internal_repositories():
    config = configparser.ConfigParser(interpolation=None)
    if not config.read(ROOT / ".gitmodules"):
        raise ProjectionError("cannot load Project Z's repository allowlist (.gitmodules)")
    return {source for section in config.sections()
            if (source := github_url(config.get(section, "url", fallback="")))}


def parse_lock(lock):
    result = {}
    for package in lock.get("package", []):
        source = package.get("source", "")
        if not source.startswith("git+"):
            continue
        url_and_selector, delimiter, commit = source[4:].rpartition("#")
        endpoint, query, _ = url_and_selector.partition("?")
        if not (canonical := github_url(endpoint)):
            continue
        address = (package["name"], canonical)
        result.setdefault(address, []).append((package["version"], commit if delimiter and SHA.fullmatch(commit) else None, bool(query)))
    return result


def exact_pin(locks, name, source):
    matches = locks.get((name, source), [])
    if len(matches) != 1:
        raise ProjectionError(f"{name} ({source}): expected one Git lock entry, found {len(matches)}")
    value, sha, selected = matches[0]
    if selected or sha is None:
        raise ProjectionError(f"{name} ({source}): lock entry needs a full Git SHA and no selector")
    match = SEMVER.fullmatch(value)
    if not match or (match[4] and any(x.isdigit() and len(x) > 1 and x.startswith("0") for x in match[4].split("."))):
        raise ProjectionError(f"{name} ({source}): invalid Cargo.lock SemVer")
    # SemVer build metadata never participates in Cargo's version matching.
    if "+" in value:
        raise ProjectionError(f"{name} ({source}): cannot exact-pin a version with build metadata")
    return value, sha


def dependency_tables(document):
    for kind in DEPS:
        yield kind, document.get(kind, {})
    for target, subsection in document.get("target", {}).items():
        for kind in DEPS:
            yield f"target.{target}.{kind}", subsection.get(kind, {})
    yield "workspace.dependencies", document.get("workspace", {}).get("dependencies", {})


def rewrite(document, locks, allowlist, manifest):
    conversions = []
    for kind, dependencies in dependency_tables(document):
        for alias, declaration in dependencies.items():
            if not isinstance(declaration, dict) or "git" not in declaration:
                continue
            url = github_url(declaration["git"])
            if url not in allowlist:
                continue
            name = declaration.get("package", alias)
            if {"rev", "branch", "tag", "path", "registry", "registry-index", "workspace"} & declaration.keys():
                raise ProjectionError(f"{manifest}: {alias}: expected a GitHub URL without a selector or alternate source")
            version, sha = exact_pin(locks, name, url)
            if "version" in declaration:
                requirement = declaration["version"]
                try:
                    compatible = satisfies(version, requirement)
                except ValueError as error:
                    raise ProjectionError(
                        f"{manifest}: {alias}: invalid version requirement {requirement!r}: {error}"
                    ) from error
                if not compatible:
                    raise ProjectionError(
                        f"{manifest}: {alias}: locked version {version} does not satisfy "
                        f"version requirement {requirement!r}"
                    )
            del declaration["git"]
            declaration["version"] = f"={version}"
            conversions.append({"manifest": manifest, "table": kind, "alias": alias, "package": name,
                                "github": url, "git_sha": sha, "version": version})
    return conversions


def quoted(value):
    return json.dumps(value, ensure_ascii=False).replace("\x7f", r"\u007f")


def toml_value(value):
    if isinstance(value, str):
        return quoted(value)
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, (int, float)):
        return repr(value)
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, list):
        return "[" + ", ".join(map(toml_value, value)) + "]"
    if isinstance(value, dict):
        return "{ " + ", ".join(f"{quoted(key)} = {toml_value(item)}" for key, item in value.items()) + " }"
    raise ProjectionError("unsupported TOML type")


def render(document):
    lines = []

    def table(path, data):
        if path:
            lines.extend(("", "[" + ".".join(map(quoted, path)) + "]"))
        lines.extend(f"{quoted(key)} = {toml_value(value)}" for key, value in data.items() if not isinstance(value, dict))
        for key, value in data.items():
            if isinstance(value, dict):
                table((*path, key), value)

    table((), document)
    rendered = "\n".join(lines).lstrip("\n") + "\n"
    if tomllib.loads(rendered) != document:
        raise ProjectionError("the rendered manifest did not round-trip")
    return rendered


def stage(repo, commit, workspace_manifest, output, allowlist, members=()):
    require_commit(repo, commit)
    workspace_manifest = relative_manifest(workspace_manifest)
    members = tuple(relative_manifest(value) for value in members)
    workspace_dir = workspace_manifest.parent
    if any(not member.is_relative_to(workspace_dir) for member in members):
        raise ProjectionError("--member-manifest must be inside the selected workspace")
    lock_path = workspace_dir / "Cargo.lock"
    source_lock = git(repo, "show", f"{commit}:{lock_path}")
    locks = parse_lock(tomllib.loads(source_lock.decode()))
    repo_root = Path(os.fsdecode(git(repo, "rev-parse", "--show-toplevel").rstrip(b"\n"))).resolve()
    output = output.resolve()
    if output.is_relative_to(repo_root):
        raise ProjectionError("--output must be outside the source checkout")
    # Git archive omits submodule contents. Fail rather than stage an incomplete checkout.
    if any(line.startswith(b"160000 ") for line in git(repo, "ls-tree", "-rz", commit).split(b"\0")):
        raise ProjectionError("source uses submodules; recursive immutable staging is not supported")
    output.mkdir()
    try:
        source = output / "source"
        source.mkdir()
        with tempfile.TemporaryFile() as archive_file:
            git(repo, "archive", "--format=tar", commit, stdout=archive_file)
            archive_file.seek(0)
            with tarfile.open(fileobj=archive_file, mode="r:") as archive:
                archive.extractall(source, filter="data")
        root_manifest = source / workspace_manifest
        if not root_manifest.is_file() or root_manifest.is_symlink():
            raise ProjectionError("workspace manifest is not a regular file in the committed archive")
        staged_lock = source / lock_path
        if staged_lock.is_symlink():
            raise ProjectionError("workspace Cargo.lock must not be a symlink")
        if staged_lock.is_file() and staged_lock.read_bytes() != source_lock:
            raise ProjectionError("Cargo.lock changed in the archive")
        paths = [root_manifest, *(source / member for member in members)] if members else sorted(root_manifest.parent.rglob("Cargo.toml"))
        conversions = []
        remaining = []
        manifest_digests = {}
        for manifest in dict.fromkeys(paths):
            if not manifest.is_file() or manifest.is_symlink():
                raise ProjectionError("a selected Cargo.toml is not a regular archived file")
            label = manifest.relative_to(source).as_posix()
            original = manifest.read_bytes()
            if original != git(repo, "show", f"{commit}:{label}"):
                raise ProjectionError(f"{label}: differs from the committed Git blob")
            document = tomllib.loads(original.decode())
            converted = rewrite(document, locks, allowlist, label)
            conversions.extend(converted)
            for key, dependencies in dependency_tables(document):
                remaining.extend({"manifest": label, "table": key, "alias": alias}
                                 for alias, spec in dependencies.items() if isinstance(spec, dict) and "git" in spec)
            if converted:
                manifest.write_text(render(document), encoding="utf-8")
                manifest_digests[label] = hashlib.sha256(manifest.read_bytes()).hexdigest()
        if not conversions:
            raise ProjectionError("no Project Z Git dependencies found in the selected manifests")
        staged_lock.unlink(missing_ok=True)
        report = {"schema_version": 1, "status": "STAGING_ONLY_UNVERIFIED_NO_PUBLISH",
                  "source_commit": commit, "workspace_manifest": workspace_manifest.as_posix(),
                  "source_lock_sha256": hashlib.sha256(source_lock).hexdigest(),
                  "conversions": conversions, "projected_manifest_sha256": manifest_digests,
                  "remaining_git_dependencies": remaining}
        (output / "projection.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        return report
    except BaseException:
        shutil.rmtree(output)
        raise


def stable_version(value):
    match = STABLE.fullmatch(value) if isinstance(value, str) else None
    if not match:
        raise ProjectionError("version calculation requires a stable MAJOR.MINOR.PATCH manifest version")
    return tuple(map(int, match.groups()))


def calculate_version(repo, commit, manifest, workspace_manifest, bump, tag_prefix):
    require_commit(repo, commit)
    manifest = relative_manifest(manifest)
    workspace_manifest = relative_manifest(workspace_manifest)
    package = tomllib.loads(git(repo, "show", f"{commit}:{manifest}").decode()).get("package", {})
    current = package.get("version")
    if current == {"workspace": True}:
        workspace = tomllib.loads(git(repo, "show", f"{commit}:{workspace_manifest}").decode())
        current = workspace.get("workspace", {}).get("package", {}).get("version")
    if not re.fullmatch(r"[a-zA-Z0-9._/-]+", tag_prefix):
        raise ProjectionError("use an explicit, non-empty stable tag prefix")
    prefix_length = len(tag_prefix)
    tags = git(repo, "tag", "--list").decode().splitlines()
    baseline = max([stable_version(current)] + [
        stable_version(tag[prefix_length:]) for tag in tags
        if tag.startswith(tag_prefix) and STABLE.fullmatch(tag[prefix_length:])
    ])
    position = ("major", "minor", "patch").index(bump)
    version = list(baseline)
    version[position:] = [version[position] + 1] + [0] * (2 - position)
    candidate = ".".join(map(str, version))
    return {"package": package.get("name"), "current": current, "base": ".".join(map(str, baseline)),
            "version": candidate, "tag": tag_prefix + candidate, "source_commit": commit}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="action", required=True)
    staged = subparsers.add_parser("stage")
    versioned = subparsers.add_parser("next-version")
    for command in (staged, versioned):
        command.add_argument("--repo", type=Path, required=True)
        command.add_argument("--commit", required=True)
        command.add_argument("--workspace-manifest", default="Cargo.toml")
    staged.add_argument("--output", type=Path, required=True)
    staged.add_argument("--member-manifest", action="append", default=[])
    versioned.add_argument("--manifest", default="Cargo.toml")
    versioned.add_argument("--bump", choices=("major", "minor", "patch"), default="patch")
    versioned.add_argument("--tag-prefix", default="v")
    args = parser.parse_args()
    try:
        if args.action == "stage":
            report = stage(args.repo, args.commit, args.workspace_manifest, args.output,
                           internal_repositories(), args.member_manifest)
        else:
            report = calculate_version(args.repo, args.commit, args.manifest, args.workspace_manifest,
                                       args.bump, args.tag_prefix)
        print(json.dumps(report, indent=2))
    except (ProjectionError, OSError, tarfile.TarError, tomllib.TOMLDecodeError) as error:
        parser.error(str(error))
    except subprocess.CalledProcessError as error:
        parser.error(f"Git exited {error.returncode}: {error.stderr.decode(errors='replace').strip()}")


if __name__ == "__main__":
    main()
