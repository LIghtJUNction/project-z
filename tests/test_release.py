"""Release entry-point checks using local Git fixtures, without Cargo or network."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
COORDINATOR = """import json
import os
from pathlib import Path
import sys

def emit(text, *, error=False):
    if os.environ.get("PROJECT_Z_RELEASE_UTF8"):
        text += " \\u201d\\u4e2d\\u6587"
    stream = sys.stderr if error else sys.stdout
    stream.buffer.write((text + "\\n").encode("utf-8"))

root = Path(__file__).resolve().parents[1]
args = sys.argv[1:]
with Path(os.environ["PROJECT_Z_RELEASE_TRACE"]).open("a") as trace:
    trace.write(json.dumps(args) + "\\n")
failure = os.environ.get("PROJECT_Z_RELEASE_FAILURE")
if args == ["check"]:
    if failure == "check":
        emit("catalog validation failed", error=True)
        sys.exit(1)
    emit("catalog validated")
elif args == ["resolve", "--all"]:
    if failure == "resolve":
        emit("application dependency source could not be resolved", error=True)
        sys.exit(1)
    if failure == "dirty":
        (root / "source.txt").write_text("modified during resolution\\n")
    emit("all Rust workspaces resolved")
else:
    print("unexpected coordinator arguments: " + repr(args), file=sys.stderr)
    sys.exit(2)
"""


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="project-z-release-tests-")
        self.addCleanup(temporary.cleanup)
        self.temporary = Path(temporary.name)
        self.root = self.temporary / "project-z"
        self.component = self.temporary / "component"
        self.output = self.temporary / "dist"
        self.trace = self.temporary / "validation.jsonl"
        for path in (self.root, self.component):
            path.mkdir()
            self.git(path, "init", "--quiet", "--initial-branch=main")
            self.git(path, "config", "user.name", "Project Z tests")
            self.git(path, "config", "user.email", "tests@example.invalid")
            self.git(path, "config", "commit.gpgsign", "false")

        (self.component / "lib.rs").write_text("pub const VALUE: u8 = 1;\n")
        self.git(self.component, "add", "lib.rs")
        self.git(self.component, "commit", "--quiet", "-m", "Component source")
        self.component_commit = self.git(self.component, "rev-parse", "HEAD").strip()

        (self.root / "scripts").mkdir()
        shutil.copyfile(ROOT / "scripts/release.py", self.root / "scripts/release.py")
        (self.root / "scripts/project_z.py").write_text(COORDINATOR)
        (self.root / "source.txt").write_text("Project Z source\n")
        self.git(
            self.root, "-c", "protocol.file.allow=always",
            "submodule", "add", "--quiet", str(self.component), "component",
        )
        self.git(self.root, "add", ".")
        self.git(self.root, "commit", "--quiet", "-m", "Source snapshot")
        self.commit = self.git(self.root, "rev-parse", "HEAD").strip()

    @staticmethod
    def git(cwd, *args):
        return subprocess.run(
            ["git", *args], cwd=cwd, check=True, capture_output=True, text=True,
        ).stdout

    def release(self, failure="", *, utf8=False):
        environment = os.environ.copy()
        environment.update({
            "PROJECT_Z_RELEASE_TRACE": str(self.trace),
            "PROJECT_Z_RELEASE_FAILURE": failure,
        })
        if utf8:
            environment.update({
                "LC_ALL": "C", "LANG": "C", "PYTHONUTF8": "0",
                "PYTHONCOERCECLOCALE": "0", "PYTHONIOENCODING": "ascii:strict",
                "PROJECT_Z_RELEASE_UTF8": "1",
            })
        return subprocess.run(
            [sys.executable, str(self.root / "scripts/release.py"), "patch", str(self.output)],
            cwd=self.root, env=environment, capture_output=True, encoding="utf-8",
        )

    def validations(self):
        return [json.loads(line) for line in self.trace.read_text().splitlines()]

    def test_resolution_failure_prevents_release_artifacts(self):
        result = self.release("resolve")
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("application dependency source could not be resolved", result.stderr)
        self.assertEqual(self.validations(), [["check"], ["resolve", "--all"]])
        self.assertFalse(self.output.exists())

    def test_catalog_failure_stops_before_resolution(self):
        result = self.release("check")
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("catalog validation failed", result.stderr)
        self.assertEqual(self.validations(), [["check"]])
        self.assertFalse(self.output.exists())

    def test_resolution_changes_are_checked_before_packaging(self):
        result = self.release("dirty")
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("tracked files and submodule commits must match HEAD", result.stderr)
        self.assertEqual(self.validations(), [["check"], ["resolve", "--all"]])
        self.assertFalse(self.output.exists())

    def test_validated_snapshot_keeps_tag_manifest_and_archive_contract(self):
        result = self.release()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "v0.0.1\n")
        self.assertIn("catalog validated", result.stderr)
        self.assertIn("all Rust workspaces resolved", result.stderr)
        self.assertEqual(self.validations(), [["check"], ["resolve", "--all"]])
        manifest = (self.output / "commits.txt").read_text()
        self.assertIn(f"project_z\t{self.commit}\n", manifest)
        self.assertIn(f"component\t{self.component_commit}\n", manifest)
        with tarfile.open(self.output / "project-z-v0.0.1.tar.gz") as archive:
            prefix = "project-z-v0.0.1"
            self.assertEqual(
                archive.extractfile(f"{prefix}/commits.txt").read().decode(), manifest,
            )
            self.assertEqual(
                archive.extractfile(f"{prefix}/component/lib.rs").read(),
                b"pub const VALUE: u8 = 1;\n",
            )
            self.assertEqual(
                archive.extractfile(f"{prefix}/source.txt").read(), b"Project Z source\n",
            )

    def test_utf8_validation_output_survives_legacy_locale(self):
        result = self.release(utf8=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "v0.0.1\n")
        self.assertIn("catalog validated \u201d\u4e2d\u6587", result.stderr)
        self.assertIn("all Rust workspaces resolved \u201d\u4e2d\u6587", result.stderr)
        self.assertEqual(self.validations(), [["check"], ["resolve", "--all"]])

    def test_utf8_resolution_error_preserves_diagnostic_and_blocks_artifacts(self):
        result = self.release("resolve", utf8=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("application dependency source could not be resolved \u201d\u4e2d\u6587", result.stderr)
        self.assertEqual(self.validations(), [["check"], ["resolve", "--all"]])
        self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()
