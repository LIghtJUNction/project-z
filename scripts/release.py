#!/usr/bin/env python3
"""Package the checked-out Project Z snapshot and calculate its release tag."""

import argparse
import re
import subprocess
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = re.compile(r"v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)")


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def next_tag(bump):
    versions = [
        tuple(map(int, match.groups()))
        for tag in git("tag", "--list").decode("utf-8").splitlines()
        if (match := VERSION.fullmatch(tag))
    ]
    version = list(max(versions, default=(0, 0, 0)))
    position = ("major", "minor", "patch").index(bump)
    version[position] += 1
    version[position + 1:] = [0] * (2 - position)
    return "v" + ".".join(map(str, version))


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bump", choices=["major", "minor", "patch"])
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    for arguments in (["check"], ["resolve", "--all"]):
        verification = subprocess.run(
            [sys.executable, str(ROOT / "scripts/project_z.py"), *arguments],
            cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
        )
        if verification.returncode:
            detail = verification.stderr.strip() or verification.stdout.strip()
            parser.error(f"{' '.join(arguments)} failed: {detail or verification.returncode}")
        if verification.stdout.strip():
            print(verification.stdout.strip(), file=sys.stderr)

    commit = git("rev-parse", "HEAD").decode("utf-8").strip()
    if git("status", "--porcelain", "--untracked-files=no", "--ignore-submodules=none"):
        parser.error("tracked files and submodule commits must match HEAD")

    submodules = git("submodule", "status", "--recursive").decode("utf-8").splitlines()
    if not submodules or any(line[0] != " " for line in submodules):
        parser.error("initialize all submodules at their recorded commits")

    tag = next_tag(args.bump)
    prefix = f"project-z-{tag}"
    args.output.mkdir(parents=True, exist_ok=True)
    manifest = [f"Project Z {tag}", f"project_z\t{commit}", ""]
    for line in submodules:
        sha, path, *_ = line[1:].split()
        manifest.append(f"{path}\t{sha}")
    (args.output / "commits.txt").write_text("\n".join(manifest) + "\n", encoding="utf-8")

    files = git("ls-files", "--cached", "--recurse-submodules", "-z").split(b"\0")
    with tarfile.open(args.output / f"{prefix}.tar.gz", "w:gz") as bundle:
        for filename in filter(None, files):
            path = Path(filename.decode("utf-8", errors="surrogateescape"))
            bundle.add(ROOT / path, arcname=f"{prefix}/{path}", recursive=False)
        bundle.add(args.output / "commits.txt", arcname=f"{prefix}/commits.txt")
    print(tag)


if __name__ == "__main__":
    main()
