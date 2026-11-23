#!/usr/bin/env python3
"""Run a bounded Windows ACL probe against the recorded, unmodified zsys crate."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    if sys.platform != "win32":
        raise SystemExit("This diagnostic requires native Windows")
    catalog = json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))
    expected = next(repo["commit"] for repo in catalog["repositories"] if repo["name"] == "zsys")
    actual = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT / "zsys", text=True).strip()
    if actual != expected or subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT / "zsys"):
        raise SystemExit("The diagnostic requires the clean, recorded zsys source")
    built = subprocess.run(
        ["cargo", "build", "--locked", "--manifest-path", str(ROOT / "zsys/Cargo.toml"),
         "--lib", "--message-format=json"],
        cwd=ROOT, text=True, encoding="utf-8", stdout=subprocess.PIPE, check=True,
    )
    libraries = []
    for line in built.stdout.splitlines():
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if entry.get("reason") == "compiler-artifact" and entry.get("target", {}).get("name") == "zsys":
            libraries.extend(Path(name) for name in entry["filenames"] if name.endswith(".rlib"))
    if len(libraries) != 1:
        raise SystemExit("Expected exactly one recorded zsys library artifact")
    with tempfile.TemporaryDirectory(prefix="project-z-acl-probe-") as directory:
        executable = Path(directory) / "privacy-diagnostics.exe"
        subprocess.run(
            ["rustc", "--edition=2024", str(ROOT / "scripts/windows_privacy_diagnostics.rs"),
             "--extern", f"zsys={libraries[0]}", "-L", f"dependency={libraries[0].parent}",
             "-o", str(executable)], check=True,
        )
        subprocess.run([str(executable)], check=True)


if __name__ == "__main__":
    main()
