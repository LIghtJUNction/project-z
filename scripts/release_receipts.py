#!/usr/bin/env python3
"""Read-only gate for exact Project Z release dependency provenance."""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
from pathlib import Path
import re
import subprocess
import tarfile
import tomllib

from release_projection import (
    ProjectionError, SEMVER, SHA, github_url, git, internal_repositories, parse_lock,
    relative_manifest, require_commit, rewrite,
)


DIGEST = re.compile(r"[a-f0-9]{64}")
PACKAGE = re.compile(r"[A-Za-z0-9_-]+")
FIELDS = {"package", "version", "github", "git_sha", "archive_sha256"}
MAX_METADATA = 1024 * 1024


def unique_json(data):
    def object_fields(pairs):
        fields = dict(pairs)
        if len(fields) != len(pairs):
            raise ProjectionError("JSON object has duplicate fields")
        return fields

    return json.loads(data, object_pairs_hook=object_fields)


def read_receipts(path, trusted_digest):
    if not DIGEST.fullmatch(trusted_digest):
        raise ProjectionError("expected receipt digest must be a full lowercase SHA-256 from a trusted channel")
    payload = path.read_bytes()
    if not hmac.compare_digest(hashlib.sha256(payload).hexdigest(), trusted_digest):
        raise ProjectionError("trusted receipt SHA-256 mismatch")
    doc = unique_json(payload)
    if (not isinstance(doc, dict) or set(doc) != {"schema_version", "receipts"}
            or type(doc["schema_version"]) is not int or doc["schema_version"] != 1
            or not isinstance(doc["receipts"], list)):
        raise ProjectionError("unsupported receipt schema")
    receipts = {}
    for item in doc["receipts"]:
        if not isinstance(item, dict) or set(item) != FIELDS or not all(isinstance(v, str) for v in item.values()):
            raise ProjectionError("invalid receipt record")
        if (not PACKAGE.fullmatch(item["package"]) or not SEMVER.fullmatch(item["version"])
                or not SHA.fullmatch(item["git_sha"])
                or not DIGEST.fullmatch(item["archive_sha256"]) or not github_url(item["github"])):
            raise ProjectionError("invalid receipt package, version, source, Git SHA, or archive SHA-256")
        key = item["package"], item["version"]
        if key in receipts:
            raise ProjectionError(f"duplicate receipts for {key[0]} {key[1]}")
        receipts[key] = item
    return receipts


def source_plan(repo, commit, workspace_manifest, members, allowlist):
    require_commit(repo, commit)
    root_manifest = relative_manifest(workspace_manifest)
    directory = root_manifest.parent
    if members:
        paths = {root_manifest, *map(relative_manifest, members)}
        if any(not item.is_relative_to(directory) for item in paths):
            raise ProjectionError("--member-manifest must be inside the selected workspace")
    else:
        listed = git(repo, "ls-tree", "--full-tree", "-rz", "--name-only", commit, "--", directory.as_posix())
        paths = {relative_manifest(name.decode()) for name in listed.split(b"\0") if name.rsplit(b"/", 1)[-1] == b"Cargo.toml"}
        paths.add(root_manifest)
    lock = parse_lock(tomllib.loads(git(repo, "show", f"{commit}:{directory / 'Cargo.lock'}").decode()))
    plans = []
    for manifest in sorted(paths):
        data = tomllib.loads(git(repo, "show", f"{commit}:{manifest}").decode())
        plans.extend(rewrite(data, lock, allowlist, manifest.as_posix()))
    if not plans:
        raise ProjectionError("no Project Z Git dependencies found in the selected manifests")
    return plans


def archive_fields(file, label):
    wanted = {f"{label}/Cargo.toml": None, f"{label}/.cargo_vcs_info.json": None}
    with tarfile.open(fileobj=file, mode="r:gz") as archive:
        for member in archive:
            if member.name not in wanted:
                continue
            if wanted[member.name] is not None or not member.isfile() or member.size > MAX_METADATA:
                raise ProjectionError(f"{label}: invalid or duplicate archive provenance metadata")
            with archive.extractfile(member) as field:
                wanted[member.name] = field.read()
    manifest, vcs = wanted.values()
    if manifest is None or vcs is None:
        raise ProjectionError(f"{label}: archive lacks Cargo.toml or .cargo_vcs_info.json")
    return tomllib.loads(manifest.decode()).get("package"), unique_json(vcs)


def verify_archives(plans, receipts, archives):
    verified = []
    checked = set()
    for plan in plans:
        package, version, url, revision = (plan[field] for field in ("package", "version", "github", "git_sha"))
        key = package, version, url, revision
        if key in checked:
            continue
        receipt = receipts.get((package, version))
        label = f"{package}-{version}"
        if receipt is None:
            raise ProjectionError(f"{label}: missing trusted receipt")
        if github_url(receipt["github"]) != url:
            raise ProjectionError(f"{label}: receipt repository differs from Cargo.lock")
        if receipt["git_sha"] != revision:
            raise ProjectionError(f"{label}: receipt Git SHA {receipt['git_sha']} differs from locked Git SHA {revision}")
        with (archives / f"{label}.crate").open("rb") as file:
            digest = hashlib.file_digest(file, "sha256").hexdigest()
            if not hmac.compare_digest(digest, receipt["archive_sha256"]):
                raise ProjectionError(f"{label}: archive SHA-256 does not match the trusted receipt")
            file.seek(0)
            metadata, vcs = archive_fields(file, label)
        if (not isinstance(metadata, dict) or metadata.get("name") != package or metadata.get("version") != version
                or github_url(metadata.get("repository")) != url):
            raise ProjectionError(f"{label}: archive package, version, or repository differs from the locked identity")
        vcs_git = vcs.get("git") if isinstance(vcs, dict) else None
        if not isinstance(vcs_git, dict) or vcs_git.get("sha1") != revision or vcs_git.get("dirty", False) is not False:
            raise ProjectionError(f"{label}: archive VCS metadata does not identify the exact clean locked Git commit")
        checked.add(key)
        verified.append({"package": package, "version": version, "github": url,
                         "git_sha": revision, "archive_sha256": digest})
    return verified


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--workspace-manifest", default="Cargo.toml")
    parser.add_argument("--member-manifest", action="append", default=[])
    parser.add_argument("--receipts", type=Path, required=True)
    parser.add_argument("--trusted-receipts-sha256", required=True)
    parser.add_argument("--archives", type=Path, required=True)
    args = parser.parse_args()
    try:
        receipts = read_receipts(args.receipts, args.trusted_receipts_sha256)
        plans = source_plan(args.repo, args.commit, args.workspace_manifest, args.member_manifest,
                            internal_repositories())
        verified = verify_archives(plans, receipts, args.archives)
        print(json.dumps({"status": "LOCKED_DEPENDENCY_RECEIPTS_VERIFIED_NO_UPLOAD",
                          "source_commit": args.commit, "dependencies": verified}, indent=2))
    except subprocess.CalledProcessError as error:
        parser.error(f"Git exited {error.returncode}: {error.stderr.decode(errors='replace').strip()}")
    except (OSError, ValueError, tarfile.TarError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
