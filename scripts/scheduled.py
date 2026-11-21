"""Prepare, test and record a scheduled Project Z GitHub snapshot."""
import argparse
import base64
from functools import cache
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import tomllib

import maintenance
from cargo_versions import version_key
from project_z import freshness_errors, repository_impact
import release


def git(*args):
    return subprocess.check_output(["git", *args], encoding="utf-8").rstrip("\n")


def require(ok, message):
    if not ok:
        raise ValueError(message)


def output(**values):
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as stream:
        for key, value in values.items():
            require("\n" not in value and "\r" not in value, "invalid workflow output")
            print(f"{key}={value}", file=stream)


def catalog(ref):
    return json.loads(git("show", f"{ref}:catalog.json"))


def links(ref):
    result = {}
    for entry in git("ls-tree", "-rz", ref).split("\0"):
        if entry:
            identity, path = entry.split("\t", 1)
            mode, _, sha = identity.split()
            if mode == "160000":
                result[path] = sha
    return result


def verify(base, sha):
    require(all(re.fullmatch("[0-9a-f]{40}", s) for s in (base, sha)), "invalid commit")
    require(git("show", "-s", "--format=%P", sha) == base, "candidate parent differs from base")
    old, new = links(base), links(sha)
    require(new.keys() == old.keys(), "registration changes need review")
    changed = {p for p in new if old[p] != new[p]}
    require(changed, "no changed gitlinks")
    fields = git("diff", "--raw", "--no-renames", "-z", base, sha).split("\0")
    for header, path in zip(fields[::2], fields[1::2]):
        modes = header.split()[:2]
        require((path in changed and modes == [":160000", "160000"]) or
                (path in maintenance.GENERATED and modes == [":100644", "100644"]),
                f"unexpected candidate change: {path}")
    rows = catalog(sha)["repositories"]
    urls = {r["path"]: r["url"] for r in catalog(base)["repositories"]}
    require(len(rows) == len(new) and {r["path"]: r["commit"] for r in rows} == new and
            all(r["name"] == r["path"] and r["url"] == urls[r["path"]] for r in rows),
            "candidate catalog is inconsistent with trusted sources")
    return changed


def bundle():
    report = json.loads(Path("dist/maintenance/audit.json").read_text())
    snapshot = report["snapshot"]
    require(not report["errors"], "audit incomplete")
    if snapshot["status"] == "no_changes":
        print("No upstream gitlink updates.")
        return
    require(snapshot["status"] == "ready", "candidate did not pass maintenance gates")
    sha = snapshot["commit"]
    verify(os.environ["GITHUB_SHA"], sha)
    git("branch", "cohort", sha)
    git("bundle", "create", str(Path(os.environ["RUNNER_TEMP"]) / "cohort.bundle"),
        os.environ["GITHUB_SHA"] + "..refs/heads/cohort")
    output(sha=sha, bundle="cohort-" + os.environ["GITHUB_RUN_ATTEMPT"])


@cache
def native_version(url, sha, manifest):
    require(manifest in {"VERSION", "pyproject.toml", "zuse.json"}, "unknown version manifest")
    owner, repo = maintenance.github_identity(url)
    blob = json.loads(gh("api", f"repos/{owner}/{repo}/contents/{manifest}?ref={sha}"))
    require(blob["type"] == "file" and blob["encoding"] == "base64", "invalid version manifest")
    text = base64.b64decode(blob["content"]).decode("utf-8")
    if manifest == "VERSION":
        return text.strip()
    if manifest == "pyproject.toml":
        return tomllib.loads(text)["project"]["version"]
    return json.loads(text)["version"]


def packages(ref, changed):
    data = catalog(ref)
    result = [p for p in data["packages"] if p["repository"] in changed]
    policy = tomllib.loads(Path("project-z.toml").read_text(encoding="utf-8"))
    manifests = policy.get("scheduled", {}).get("version_manifests", {})
    for repo in data["repositories"]:
        name = repo["name"]
        if name in changed and name in manifests:
            version = native_version(repo["url"], repo["commit"], manifests[name])
            version_key(version)
            result.append(dict(repository=name, name=name, version=version, publish=False))
    return result


def versions(ref, changed):
    return {(p["repository"], p["name"]): p["version"] for p in packages(ref, changed)}


def version_changes(base, sha, changed):
    old = versions(base, changed)
    result = []
    for p in packages(sha, changed):
        key = (p["repository"], p["name"])
        if old.get(key) == p["version"]:
            continue
        if key in old:
            previous, current = version_key(old[key]), version_key(p["version"])
            require(current >= previous, f"{key}: version decreased")
            if current == previous:
                continue
        result.append(p)
    return result


def plan(base, sha):
    changed = verify(base, sha)
    updates = version_changes(base, sha, changed)
    if not updates:
        return "", []
    tags = sorted((tuple(map(int, m.groups())), tag) for tag in git("tag", "--list").splitlines()
                  if (m := release.VERSION.fullmatch(tag)))
    require(tags, "bootstrap the first official Project Z release manually")
    cohort = links(sha)
    # A historical snapshot or an already released package version cannot
    # justify another patch, even after unrelated root commits or a rollback.
    seen = set()
    for _, tag in tags:
        if links(tag) == cohort:
            return "", []
        seen.update((repo, name, v) for (repo, name), v in versions(tag, changed).items())
    updates = [p for p in updates if (p["repository"], p["name"], p["version"]) not in seen]
    if not updates:
        return "", []
    major, minor, patch = tags[-1][0]
    return f"v{major}.{minor}.{patch + 1}", updates


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def package():
    base, sha = os.environ["GITHUB_SHA"], git("rev-parse", "HEAD")
    tag, updates = plan(base, sha)
    if not tag:
        print("Verified synchronization only. No unpublished version change.")
        return
    # Registry availability is separate from the aggregate GitHub snapshot.
    from scheduled_registry import child_targets
    children = child_targets(updates, catalog(sha)["repositories"], Path.cwd())
    print(f"{len(children)} approved owner handoffs in staging")
    dest = Path(os.environ["RUNNER_TEMP"]) / "release-assets"
    actual = subprocess.check_output([sys.executable, "scripts/release.py", "patch", str(dest)],
                                     encoding="utf-8").strip()
    require(actual == tag, "official packager selected a different tag")
    output(tag=tag, assets="snapshot-" + os.environ["GITHUB_RUN_ATTEMPT"],
           archive_digest=digest(dest / f"project-z-{tag}.tar.gz"),
           manifest_digest=digest(dest / "commits.txt"))
    print(f"Staged {tag} for {sha}")


def remote_refs():
    return {ref: oid for oid, ref in (line.split("\t") for line in
            git("ls-remote", "--refs", "origin", "refs/heads/main", "refs/tags/v*").splitlines())}


def compare_push(lines, base, sha, tag):
    expected = {"refs/heads/main": (sha, base)}
    if tag:
        expected["refs/tags/" + tag] = (sha, "0" * 40)
    actual = {}
    for line in lines:
        _, local_oid, remote_ref, remote_oid = line.split()
        actual[remote_ref] = (local_oid, remote_oid)
    require(actual == expected, "remote refs changed before atomic push")


def reserve(base, sha, tag):
    # The hook checks the server's advertisement on this push connection.
    # receive-pack subsequently compares those same old OIDs under ref locks.
    with tempfile.TemporaryDirectory() as temp:
        hook = Path(temp) / "pre-push"
        hook.write_text('#!/bin/sh\nexec python3 scripts/scheduled.py pre-push\n', encoding="utf-8")
        hook.chmod(0o755)
        refs = [sha + ":refs/heads/main"]
        if tag:
            refs.append(sha + ":refs/tags/" + tag)
        subprocess.run(["git", "-c", f"core.hooksPath={temp}", "push", "--atomic", "origin", *refs],
                       check=True, env={**os.environ, "GITHUB_SHA": base, "CANDIDATE": sha, "RELEASE_TAG": tag})


def gh(*args):
    return subprocess.check_output(["gh", *args], encoding="utf-8").strip()


def finish_release(tag, files):
    # A draft with different assets or ownership is a conflict. Only complete
    # drafts created by this workflow for this exact candidate can be resumed.
    repo = os.environ["GITHUB_REPOSITORY"]
    marker = f"Project Z scheduled snapshot {tag} at {os.environ['CANDIDATE']}"
    rows = json.loads(gh("api", "--paginate", "--slurp", f"repos/{repo}/releases?per_page=100"))
    matches = [r for page in rows for r in page if r["tag_name"] == tag]
    require(len(matches) <= 1, "ambiguous GitHub release")
    if not matches:
        gh("release", "create", tag, "--verify-tag", "--draft", "--title", f"Project Z {tag}", "--notes", marker)
    info = json.loads(gh("release", "view", tag, "--json", "body,isDraft,assets"))
    require(info["body"] == marker, "existing release belongs to another operation")
    assets = {a["name"]: a for a in info["assets"]}
    require(assets.keys() <= files.keys(), "unexpected release asset")
    for name, (path, checksum) in files.items():
        if name in assets:
            require(assets[name]["digest"] == "sha256:" + checksum, "release asset digest conflict")
        else:
            require(info["isDraft"], "published release is incomplete")
            gh("release", "upload", tag, str(path))
    if info["isDraft"]:
        receipt = json.loads(gh("release", "view", tag, "--json", "body,isDraft,assets"))
        require(receipt["isDraft"] and receipt["body"] == marker and
                {a["name"]: a["digest"] for a in receipt["assets"]} ==
                {name: "sha256:" + checksum for name, (_, checksum) in files.items()},
                "uploaded assets differ from staged digests")
        fresh(os.environ["CANDIDATE"])
        refs = remote_refs()
        require(refs.get("refs/heads/main") == os.environ["CANDIDATE"] and
                refs.get("refs/tags/" + tag) == os.environ["CANDIDATE"], "release refs moved")
        gh("release", "edit", tag, "--draft=false")


def fresh(sha):
    errors = freshness_errors(catalog(sha), Path.cwd())
    require(not errors, "\n".join(errors))


def authorize_writer():
    repo = "LIghtJUNction/project-z"
    require(os.environ.get("GITHUB_EVENT_NAME") == "schedule" and
            os.environ.get("PROJECT_Z_SCHEDULED_WRITES") == "true" and
            os.environ.get("GITHUB_REF") == "refs/heads/main" and
            os.environ.get("GITHUB_REPOSITORY") == repo and
            maintenance.github_identity(git("remote", "get-url", "--push", "origin")) == tuple(repo.split("/")),
            "production writes require the enabled schedule on the canonical main repository")


def record():
    authorize_writer()
    base, sha, tag = (os.environ[k] for k in ("GITHUB_SHA", "CANDIDATE", "RELEASE_TAG"))
    verify(base, sha)
    require(not tag or release.VERSION.fullmatch(tag), "invalid tag")
    refs = remote_refs()
    head = refs["refs/heads/main"]
    files = {}
    if tag:
        dest = Path(os.environ["RUNNER_TEMP"]) / "release-assets"
        for name, key in [(f"project-z-{tag}.tar.gz", "ARCHIVE_DIGEST"), ("commits.txt", "MANIFEST_DIGEST")]:
            path = dest / name
            require(not path.is_symlink() and path.is_file() and digest(path) == os.environ[key],
                    f"unverified artifact: {name}")
            files[name] = path, os.environ[key]
        require((dest / "commits.txt").read_text().splitlines()[:2] == [f"Project Z {tag}", f"project_z\t{sha}"],
                "manifest does not identify the tested candidate")
    fresh(sha)
    if head == base:
        local = {ref: oid for oid, ref in (line.split() for line in git("show-ref", "--tags").splitlines())
                 if release.VERSION.fullmatch(ref.removeprefix("refs/tags/"))}
        remote = {ref: oid for ref, oid in refs.items() if release.VERSION.fullmatch(ref.removeprefix("refs/tags/"))}
        require(local == remote and plan(base, sha)[0] == tag, "version plan changed since CI")
        if local:
            latest = max((tuple(map(int, release.VERSION.fullmatch(ref[10:]).groups())), ref[10:]) for ref in local)[1]
            require(gh("release", "view", latest, "--json", "isDraft,isPrerelease", "--jq",
                       "(.isDraft or .isPrerelease)") == "false", "previous stable release is incomplete")
        reserve(base, sha, tag)
    else:
        require(head == sha, "main moved since CI")
    if tag:
        current = remote_refs()
        require(current.get("refs/heads/main") == sha and current.get("refs/tags/" + tag) == sha,
                "reserved release refs disagree")
        finish_release(tag, files)
        from scheduled_registry import child_targets
        changed = verify(base, sha)
        updates = version_changes(base, sha, changed)
        # The write job reads policy and executes code only from the trusted
        # base. Environment names for dispatch are never accepted from CI.
        historical = {(*key, v) for old_tag in git("tag", "--list").splitlines()
                      if old_tag != tag and release.VERSION.fullmatch(old_tag)
                      for key, v in versions(old_tag, changed).items()}
        pending = [p for p in updates if (p["repository"], p["name"], p["version"]) not in historical]
        targets = child_targets(pending, catalog(sha)["repositories"], Path.cwd())
        output(children=json.dumps(targets, separators=(",", ":")))


def affected_tests():
    sha = git("rev-parse", "HEAD")
    changed = verify(os.environ["GITHUB_SHA"], sha)
    data = catalog(sha)
    affected = set(repository_impact(data, changed))
    if any(p["repository"] in affected for p in data["packages"]):
        selection = [arg for name in sorted(changed) for arg in ("--affected", name)]
        subprocess.run([sys.executable, "scripts/project_z.py", "run", *selection, "--", "test", "--tests"],
                       check=True)
    if "oh-my-ztty" in affected:
        subprocess.run(["make", "-C", "oh-my-ztty", "check"], check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    verify_cmd = sub.add_parser("verify")
    verify_cmd.add_argument("base")
    verify_cmd.add_argument("sha")
    for cmd in ["bundle", "package", "record", "pre-push", "affected-tests"]:
        sub.add_parser(cmd)
    args = parser.parse_args()
    if args.cmd == "verify":
        verify(args.base, args.sha)
    elif args.cmd == "pre-push":
        compare_push(sys.stdin, os.environ["GITHUB_SHA"], os.environ["CANDIDATE"], os.environ["RELEASE_TAG"])
    else:
        {"bundle": bundle, "package": package, "record": record, "affected-tests": affected_tests}[args.cmd]()


if __name__ == "__main__":
    main()
