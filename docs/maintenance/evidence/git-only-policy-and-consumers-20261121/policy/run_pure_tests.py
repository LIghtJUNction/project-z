from pathlib import Path
import datetime
import hashlib
import json
import os
import sys
import time
import unittest

phase, source_arg, output_arg = sys.argv[1:]
source, output = Path(source_arg), Path(output_arg)
assert phase in ("red", "green")
assert source.resolve() == (output / "source").resolve()
assert Path.cwd().resolve() == source.resolve()
selected = {
    "red": [
        "test_project_z.GitPolicyTests.test_git_only_is_allowed_for_all_publish_modes_and_dependency_kinds",
        "test_project_z.GitPolicyTests.test_internal_git_rejects_every_explicit_version",
        "test_project_z.GitPolicyTests.test_workspace_target_and_alias_versions_cannot_bypass_git_only",
        "test_project_z.GitPolicyTests.test_git_source_does_not_bypass_missing_package_checks",
        "test_project_z.GitPolicyTests.test_unknown_internal_package_cannot_hide_behind_alternate_github_spelling",
    ],
    "green": [
        "test_project_z.GitPolicyTests",
        "test_project_z.VersionDeclarationTests",
        "test_release_projection.MatchTests",
    ],
}[phase]
inputs = [
    "AGENTS.md", "README.md", "CONTRIBUTING.md", "docs/release-projection.md",
    "scripts/project_z.py", "scripts/cargo_versions.py", "scripts/catalog_docs.py",
    "scripts/release.py", "scripts/release_projection.py", "scripts/release_receipts.py",
    "tests/test_project_z.py", "tests/test_release.py",
    "tests/test_release_projection.py", "tests/test_release_receipts.py",
]
def descriptors():
    rows = []
    for name in inputs:
        data = (source / name).read_bytes()
        rows.append({"path": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    return rows
before = descriptors()
process_events = []
def audit(event, args):
    if event in ("subprocess.Popen", "os.system", "os.posix_spawn", "os.posix_spawnp", "os.exec", "os.fork"):
        process_events.append({"event": event, "arguments": repr(args[:2])})
sys.addaudithook(audit)
sys.path.insert(0, str(source / "tests"))
class Result(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent_ids = []
        self.failed_parent_ids = set()
    def startTest(self, test):
        self.parent_ids.append(test.id())
        super().startTest(test)
    def addFailure(self, test, err):
        self.failed_parent_ids.add(test.id())
        super().addFailure(test, err)
    def addError(self, test, err):
        self.failed_parent_ids.add(test.id())
        super().addError(test, err)
    def addSubTest(self, test, subtest, err):
        if err is not None:
            self.failed_parent_ids.add(test.id())
        super().addSubTest(test, subtest, err)
class Tee:
    def __init__(self, file):
        self.file = file
    def write(self, data):
        sys.stdout.write(data)
        self.file.write(data)
    def flush(self):
        sys.stdout.flush()
        self.file.flush()
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
tick = time.monotonic()
with (output / (phase + ".log")).open("x", encoding="utf-8") as raw:
    suite = unittest.defaultTestLoader.loadTestsFromNames(selected)
    result = unittest.TextTestRunner(stream=Tee(raw), verbosity=2, resultclass=Result).run(suite)
after = descriptors()
passed = result.wasSuccessful() and before == after and not process_events
receipt = {
    "schema": "project-z-git-only-pure-python.v1",
    "phase": phase, "source_root": str(source), "base": "c9de7a60351b277a4903c9f40781cbae69cd6e5c",
    "started_at": started, "finished_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "duration_seconds": time.monotonic() - tick,
    "argv": [sys.executable, "-I", "-B", str(Path(__file__).resolve()), *sys.argv[1:]],
    "cwd": str(Path.cwd()), "python_version": sys.version, "selected": selected,
    "tests_run": result.testsRun, "parent_test_ids": result.parent_ids,
    "failed_parent_ids": sorted(result.failed_parent_ids),
    "failure_count": len(result.failures), "error_count": len(result.errors),
    "skip_count": len(result.skipped), "expected_failure_count": len(result.expectedFailures),
    "unexpected_success_count": len(result.unexpectedSuccesses),
    "inputs_before": before, "inputs_after": after, "inputs_unchanged": before == after,
    "observed_process_events": process_events, "cargo_executed": False if not process_events else None,
    "shared_target_or_lock_requested": False, "product_or_graph_commands_requested": False,
    "passed": passed, "exit_code": 0 if passed else 1,
}
data = (json.dumps(receipt, ensure_ascii=False, indent=2) + "\n").encode()
destination = output / (phase + ".json")
with destination.open("xb") as file:
    file.write(data)
print(json.dumps({"phase": phase, "tests_run": result.testsRun, "failed_parent_ids": sorted(result.failed_parent_ids),
                  "failures": len(result.failures), "errors": len(result.errors), "skips": len(result.skipped),
                  "process_events": len(process_events), "passed": passed,
                  "receipt": str(destination), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}))
sys.exit(receipt["exit_code"])
