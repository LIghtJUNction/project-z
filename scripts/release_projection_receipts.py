#!/usr/bin/env python3
"""Verify projected crate receipts by rebuilding from the exact trusted source."""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import tomllib
from types import ModuleType

SHA = re.compile(r"(?:[a-f0-9]{40}|[a-f0-9]{64})")
DIGEST = re.compile(r"[a-f0-9]{64}")
PACKAGE = re.compile(r"[A-Za-z0-9_-]+")
VERSION = re.compile(r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)(?:-[0-9A-Za-z.-]+)?")
GITHUB = re.compile(r"https://github\.com/([A-Za-z0-9-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?/?", re.I)
FIELDS = {"package", "version", "github", "source_git_sha", "projection_tool_sha", "registry_lock_sha256", "archive_sha256"}
REGISTRIES = {"registry+https://github.com/rust-lang/crates.io-index", "registry+sparse+https://index.crates.io/"}
TOOL_FILES = (".gitmodules", "scripts/release_projection.py", "scripts/cargo_versions.py")


class ReceiptError(ValueError):
    pass


def github_url(value):
    match = GITHUB.fullmatch(value) if isinstance(value, str) else None
    return "https://github.com/" + "/".join(part.lower() for part in match.groups()) if match else None


def unique_json(payload):
    def fields(items):
        result = dict(items)
        if len(result) != len(items):
            raise ReceiptError("JSON object contains duplicate fields")
        return result
    return json.loads(payload, object_pairs_hook=fields)


def read_receipts(path: Path, trusted_digest: str):
    if not DIGEST.fullmatch(trusted_digest):
        raise ReceiptError("The trusted receipt pin must be a full lowercase SHA-256")
    payload = path.read_bytes()
    if not hmac.compare_digest(hashlib.sha256(payload).hexdigest(), trusted_digest):
        raise ReceiptError("Trusted projection receipt SHA-256 mismatch")
    document = unique_json(payload)
    if (not isinstance(document, dict) or set(document) != {"schema_version", "receipts"}
            or type(document["schema_version"]) is not int or document["schema_version"] != 2
            or not isinstance(document["receipts"], list)):
        raise ReceiptError("Expected projection receipt schema_version 2")
    receipts = {}
    for item in document["receipts"]:
        if not isinstance(item, dict) or set(item) != FIELDS or not all(isinstance(v, str) for v in item.values()):
            raise ReceiptError("Invalid projection receipt fields")
        if (not PACKAGE.fullmatch(item["package"]) or not VERSION.fullmatch(item["version"])
                or not github_url(item["github"])
                or any(not SHA.fullmatch(item[key]) for key in ("source_git_sha", "projection_tool_sha"))
                or any(not DIGEST.fullmatch(item[key]) for key in ("registry_lock_sha256", "archive_sha256"))):
            raise ReceiptError("Malformed projection receipt identity or digest")
        key = item["package"], item["version"]
        if key in receipts:
            raise ReceiptError(f"Duplicate projection receipt for {key}")
        receipts[key] = item
    return receipts


def git(repo, *arguments):
    return subprocess.run(
        ["git", "-C", str(repo), *arguments], check=True, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, env={**os.environ, "GIT_NO_REPLACE_OBJECTS": "1"},
    ).stdout


def load_projection(tools_root: Path, expected_commit: str):
    if not SHA.fullmatch(expected_commit):
        raise ReceiptError("Projection tool revision must be a full Git SHA")
    tools_root = tools_root.resolve()
    if git(tools_root, "rev-parse", "HEAD").decode().strip() != expected_commit:
        raise ReceiptError("Project Z tool checkout does not match the trusted receipt")
    verified_sources = {}
    for relative in TOOL_FILES:
        path = tools_root / relative
        expected = git(tools_root, "show", f"{expected_commit}:{relative}")
        if path.is_symlink() or not path.is_file() or path.read_bytes() != expected:
            raise ReceiptError(f"Projection tool file differs from its pinned commit: {relative}")
        verified_sources[relative] = expected
    # Execute the authenticated source bytes themselves. Importing by path can
    # silently execute an untracked, timestamp-matched __pycache__ file instead.
    for name in ("cargo_versions", "release_projection"):
        relative = f"scripts/{name}.py"
        module = ModuleType(name)
        module.__file__ = str(tools_root / relative)
        module.__package__ = ""
        sys.modules[name] = module
        exec(compile(verified_sources[relative], module.__file__, "exec"), module.__dict__)
    return sys.modules["release_projection"]


def package_identity(repo, commit, manifest, workspace_manifest, projection):
    projection.require_commit(repo, commit)
    manifest = projection.relative_manifest(manifest)
    workspace_manifest = projection.relative_manifest(workspace_manifest)
    package = tomllib.loads(git(repo, "show", f"{commit}:{manifest}").decode()).get("package", {})
    workspace = tomllib.loads(git(repo, "show", f"{commit}:{workspace_manifest}").decode()).get("workspace", {}).get("package", {})
    identity = {}
    for field in ("name", "version", "repository"):
        value = package.get(field)
        identity[field] = workspace.get(field) if value == {"workspace": True} else value
    if (not isinstance(identity["name"], str) or not PACKAGE.fullmatch(identity["name"])
            or not isinstance(identity["version"], str) or not VERSION.fullmatch(identity["version"])
            or not github_url(identity["repository"])):
        raise ReceiptError("The source commit lacks a publishable package identity")
    return identity


def validate_registry_lock(payload, source_lock, identity, projection, allowlist):
    document = tomllib.loads(payload.decode())
    packages = document.get("package", [])
    if not isinstance(packages, list):
        raise ReceiptError("Registry lock is missing package entries")
    own = [p for p in packages if p.get("name") == identity["name"] and p.get("source") is None]
    if len(own) != 1 or own[0].get("version") != identity["version"]:
        raise ReceiptError("Registry lock does not identify the selected source package")
    for package in packages:
        source = package.get("source")
        if source is not None and (source not in REGISTRIES or not DIGEST.fullmatch(package.get("checksum", ""))):
            raise ReceiptError("Projected release lock must use checksummed crates.io entries, without Git sources")
    locks = projection.parse_lock(tomllib.loads(source_lock.decode()))
    for (name, url) in locks:
        if url not in allowlist:
            continue
        version, _ = projection.exact_pin(locks, name, url)
        actual = [p for p in packages if p.get("name") == name]
        if len(actual) != 1 or actual[0].get("version") != version or actual[0].get("source") not in REGISTRIES:
            raise ReceiptError(f"Registry lock changed the source graph's internal identity: {name} {version}")
    return document


def archive_identity(path: Path, name: str, version: str):
    wanted = f"{name}-{version}/Cargo.toml"
    manifest = None
    with tarfile.open(path, "r:gz") as archive:
        for member in archive:
            if member.name == f"{name}-{version}/.cargo_vcs_info.json":
                raise ReceiptError("Projected archive must not manufacture Cargo VCS metadata")
            if member.name == wanted:
                if manifest is not None or not member.isfile() or member.size > 1024 * 1024:
                    raise ReceiptError("Invalid or duplicate packaged manifest")
                with archive.extractfile(member) as stream:
                    manifest = tomllib.loads(stream.read().decode()).get("package", {})
    if not isinstance(manifest, dict) or manifest.get("name") != name or manifest.get("version") != version:
        raise ReceiptError("Archive package identity differs from the trusted receipt")
    return manifest


def rebuild_package(manifest: Path, target_dir: Path):
    subprocess.run(
        ["cargo", "package", "--locked", "--registry", "crates-io", "--manifest-path", str(manifest),
         "--target-dir", str(target_dir)], cwd=manifest.parent, check=True,
    )


def verify_package(repo: Path, commit: str, tools_root: Path, receipts, archives: Path,
                   registry_locks: Path, work_dir: Path, *, manifest="Cargo.toml",
                   workspace_manifest="Cargo.toml", target_dir: Path | None = None):
    if not SHA.fullmatch(commit):
        raise ReceiptError("Source revision must be a full Git SHA")
    candidates = [item for item in receipts.values() if item["source_git_sha"] == commit]
    if not candidates:
        raise ReceiptError("No trusted projection receipt identifies this source commit")
    tool_commit = git(tools_root, "rev-parse", "HEAD").decode().strip()
    if not any(item["projection_tool_sha"] == tool_commit for item in candidates):
        raise ReceiptError("No source receipt trusts this projection tool revision")
    projection = load_projection(tools_root, tool_commit)
    identity = package_identity(repo, commit, manifest, workspace_manifest, projection)
    name, version = identity["name"], identity["version"]
    receipt = receipts.get((name, version))
    if (receipt is None or receipt["source_git_sha"] != commit
            or receipt["projection_tool_sha"] != tool_commit
            or github_url(receipt["github"]) != github_url(identity["repository"])):
        raise ReceiptError("Source package, repository or tool identity differs from its receipt")
    label = f"{name}-{version}"
    archive_path = archives / f"{label}.crate"
    with archive_path.open("rb") as archive:
        archive_digest = hashlib.file_digest(archive, "sha256").hexdigest()
    if not hmac.compare_digest(archive_digest, receipt["archive_sha256"]):
        raise ReceiptError("Candidate archive does not match the trusted receipt")
    packaged = archive_identity(archive_path, name, version)
    if github_url(packaged.get("repository")) != github_url(identity["repository"]):
        raise ReceiptError("Archive repository differs from the source identity")
    registry_lock = (registry_locks / f"{label}.Cargo.lock").read_bytes()
    if not hmac.compare_digest(hashlib.sha256(registry_lock).hexdigest(), receipt["registry_lock_sha256"]):
        raise ReceiptError("Registry lock does not match the independently trusted digest")
    source_lock_path = projection.relative_manifest(workspace_manifest).parent / "Cargo.lock"
    source_lock = git(repo, "show", f"{commit}:{source_lock_path}")
    allowlist = projection.internal_repositories()
    validate_registry_lock(registry_lock, source_lock, identity, projection, allowlist)
    work_dir = work_dir.resolve()
    work_dir.mkdir(parents=True, exist_ok=False)
    report = projection.stage(repo, commit, workspace_manifest, work_dir / "stage", allowlist)
    if report["remaining_git_dependencies"]:
        raise ReceiptError("Projection still contains Git dependencies")
    source = work_dir / "stage" / "source"
    if subprocess.run(["git", "-C", str(source), "rev-parse", "--show-toplevel"],
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0:
        raise ReceiptError("Rebuild staging must not be inside a Git checkout")
    if (source / ".cargo_vcs_info.json").exists():
        raise ReceiptError("Source snapshot must not provide fabricated Cargo VCS metadata")
    staged_lock = source / source_lock_path
    staged_lock.write_bytes(registry_lock)
    if target_dir is None:
        configured = os.environ.get("CARGO_TARGET_DIR")
        target_dir = Path(configured).resolve() if configured else work_dir / "build"
    target_dir = target_dir.resolve()
    rebuild_package(source / projection.relative_manifest(manifest), target_dir)
    if staged_lock.read_bytes() != registry_lock:
        raise ReceiptError("Packaging modified the verified registry lock")
    rebuilt = target_dir / "package" / f"{label}.crate"
    with rebuilt.open("rb") as archive:
        rebuilt_digest = hashlib.file_digest(archive, "sha256").hexdigest()
    if not hmac.compare_digest(rebuilt_digest, archive_digest):
        raise ReceiptError("Rebuilt crate differs from the trusted published archive")
    result = {"schema_version": 2, "status": "PROJECTED_RELEASE_REBUILT_AND_VERIFIED",
              **receipt, "source_lock_sha256": report["source_lock_sha256"],
              "projected_manifest_sha256": report["projected_manifest_sha256"],
              "archive_bytes": archive_path.stat().st_size}
    (work_dir / "verification.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--project-z-tools", required=True, type=Path)
    parser.add_argument("--receipts", required=True, type=Path)
    parser.add_argument("--trusted-receipts-sha256", required=True)
    parser.add_argument("--archives", required=True, type=Path)
    parser.add_argument("--registry-locks", required=True, type=Path)
    parser.add_argument("--work-dir", required=True, type=Path)
    parser.add_argument("--manifest", default="Cargo.toml")
    parser.add_argument("--workspace-manifest", default="Cargo.toml")
    parser.add_argument("--target-dir", type=Path)
    arguments = parser.parse_args()
    try:
        receipts = read_receipts(arguments.receipts, arguments.trusted_receipts_sha256)
        result = verify_package(
            arguments.repo, arguments.commit, arguments.project_z_tools, receipts,
            arguments.archives, arguments.registry_locks, arguments.work_dir,
            manifest=arguments.manifest, workspace_manifest=arguments.workspace_manifest,
            target_dir=arguments.target_dir,
        )
        print(json.dumps(result, indent=2))
    except (ValueError, OSError, KeyError, tarfile.TarError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"Projection receipt verification failed: {error}\n")


if __name__ == "__main__":
    main()
