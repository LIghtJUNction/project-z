import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from deslop_observation import safe_path, scan_manifests, targets


def commit(cwd):
    subprocess.run(["git", "-c", "user.email=test@example.invalid", "-c", "user.name=Test",
                    "commit", "--quiet", "--message=fixture"], cwd=cwd, check=True)
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=cwd, text=True).strip()


@unittest.skipUnless(sys.platform != "win32", "requires POSIX process groups and shell fixtures")
class ObservationTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.temp = Path(temp.name)
        self.repo = self.temp / "source"
        self.repo.mkdir()
        self.output = self.temp / "output"
        self.output.mkdir()
        self.bin = self.temp / "bin"
        self.bin.mkdir()
        self.summary = self.temp / "summary"
        subprocess.run(["git", "init", "--quiet", self.repo], check=True)
        for name in ("", "nested", "failed", "dirty"):
            path = self.repo / name
            path.mkdir(exist_ok=True)
            (path / "Cargo.toml").write_text("synthetic", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=self.repo, check=True)
        self.sha = commit(self.repo)
        self.tool("cargo", 'test "$PWD" != "$SOURCE/failed"')
        self.tool("deslop-please", '''
case "$PWD" in
  "$SOURCE/nested") echo "synthetic module-cycle"; exit 1 ;;
  "$SOURCE/dirty") echo change >> Cargo.toml; exit 1 ;;
  "$SOURCE") exit 0 ;;
  *) exit 2 ;;
esac
''')
        env_patch = patch.dict(os.environ, {"PATH": f"{self.bin}:{os.environ['PATH']}",
                                           "SOURCE": str(self.repo), "GITHUB_STEP_SUMMARY": str(self.summary)})
        env_patch.start()
        self.addCleanup(env_patch.stop)

    def tool(self, name, body):
        tool = self.bin / name
        tool.write_text("#!/bin/sh\n" + body + "\n", encoding="utf-8")
        tool.chmod(0o755)

    def test_nested_findings_and_failures_are_not_clean(self):
        manifests = tuple(safe_path(p) for p in ("Cargo.toml", "nested/Cargo.toml", "absent/Cargo.toml",
                                                   "failed/Cargo.toml", "dirty/Cargo.toml"))
        rows = list(scan_manifests(self.repo, self.output, "deslop-please",
                                   ("fixture", "", self.sha, manifests), True, ["git"], os.environ))
        self.assertEqual([r["status"] for r in rows],
                         ["clean", "findings", "tool_error", "tool_error", "tool_error"])
        logs = [(self.output / r["log"]).read_text() for r in rows]
        self.assertIn("synthetic module-cycle", logs[1])
        self.assertIn("missing", logs[2])
        self.assertIn("manifest could not be resolved", logs[3].lower())
        self.assertIn("Tracked files changed", logs[4])

    def test_catalog_overrides_and_owner_are_verified(self):
        root = self.temp / "aggregate"
        root.mkdir()
        subprocess.run(["git", "init", "--quiet", root], check=True)
        u = "https://github.com/LIghtJUNction/fixture.git"
        (root / ".gitmodules").write_text(f'[submodule "fixture"]\npath = fixture\nurl = {u}\n')
        records = [
            {"name": "fixture", "path": "fixture", "url": u, "commit": self.sha,
             "manifests": ["Cargo.toml", "nested/Cargo.toml"]},
            {"name": "outside", "path": "outside", "url": "https://github.com/outside/outside.git",
             "commit": self.sha, "manifests": ["Cargo.toml"]},
        ]
        catalog = root / "catalog.json"
        catalog.write_text(json.dumps({"schema_version": 1, "repositories": records}))
        subprocess.run(["git", "add", "."], cwd=root, check=True)
        subprocess.run(["git", "update-index", "--add", "--cacheinfo", f"160000,{self.sha},fixture"],
                       cwd=root, check=True)
        commit(root)
        chosen, skipped = targets(root, set())
        self.assertEqual(len(chosen), 1)
        self.assertEqual(len(chosen[0][-1]), 2)
        self.assertEqual(skipped, ["outside"])
        with self.assertRaisesRegex(ValueError, "ineligible"):
            targets(root, {"outside"})
        records[0]["commit"] = "0" * 40
        catalog.write_text(json.dumps({"schema_version": 1, "repositories": records}))
        with self.assertRaisesRegex(ValueError, "differs from HEAD gitlink"):
            targets(root, set())

    def test_unsafe_paths(self):
        for invalid in ("/tmp/Cargo.toml", "a/../Cargo.toml", "-x/Cargo.toml", "a/.git/Cargo.toml"):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                safe_path(invalid)
