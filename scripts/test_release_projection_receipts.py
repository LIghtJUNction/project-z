"""Focused proof-boundary tests using real Git archives and official staging.

Only Cargo package rebuilding is substituted: the final byte-for-byte Cargo
acceptance gate runs with the actual Rust toolchain in release verification.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import io
import json
import marshal
import os
from pathlib import Path
import shutil
import subprocess
import struct
import sys
import tarfile
import tempfile
import tomllib
import unittest
from unittest.mock import patch


SCRIPTS = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "project_z_receipts_under_test", SCRIPTS / "release_projection_receipts.py"
)
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)

NAME = "zobs"
VERSION = "0.1.0"
LABEL = f"{NAME}-{VERSION}"
REPOSITORY = "https://github.com/LIghtJUNction/zobs"
DEPENDENCY_REPO = "https://github.com/LIghtJUNction/zclap.git"
DEPENDENCY_SHA = "b" * 40
REGISTRY = "registry+https://github.com/rust-lang/crates.io-index"
COMMITTED_SOURCE = b"pub const VERSION: &str = \"0.1.0\";\n"


def digest(payload):
    return hashlib.sha256(payload).hexdigest()


def official_script(name):
    local = SCRIPTS / name
    if local.is_file():
        return local.read_bytes()
    # The authoring sandbox may hold the companion script in its read-only
    # checkout. A normal Project Z checkout uses the adjacent file above.
    reference = SCRIPTS.parents[1] / "project-z-main-review" / "scripts" / name
    return reference.read_bytes()


def run_git(repo, *arguments):
    environment = {
        **os.environ,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_AUTHOR_NAME": "Projection test",
        "GIT_AUTHOR_EMAIL": "projection-test@example.invalid",
        "GIT_COMMITTER_NAME": "Projection test",
        "GIT_COMMITTER_EMAIL": "projection-test@example.invalid",
        "GIT_AUTHOR_DATE": "2026-01-01T00:00:00Z",
        "GIT_COMMITTER_DATE": "2026-01-01T00:00:00Z",
        "GIT_NO_REPLACE_OBJECTS": "1",
    }
    return subprocess.run(
        ["git", "-C", str(repo), *arguments], check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=environment,
    ).stdout.decode().strip()


def commit(repo, message="Fixture source"):
    run_git(repo, "add", "--all")
    run_git(repo, "commit", "--quiet", "--no-gpg-sign", "-m", message)
    return run_git(repo, "rev-parse", "HEAD")


class ProjectionReceiptTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="project-z-receipts-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.repo = self.root / "source-repo"
        self.tools = self.root / "tool-repo"
        self.archives = self.root / "archives"
        self.registry_locks = self.root / "registry-locks"
        for directory in (self.repo, self.tools, self.archives, self.registry_locks):
            directory.mkdir()
        for repository in (self.repo, self.tools):
            run_git(repository, "init", "--quiet", "--initial-branch=main")

        scripts = self.tools / "scripts"
        scripts.mkdir()
        for filename in ("release_projection.py", "cargo_versions.py"):
            (scripts / filename).write_bytes(official_script(filename))
        (self.tools / ".gitmodules").write_text(
            '[submodule "zclap"]\n'
            '\tpath = zclap\n'
            f'\turl = {DEPENDENCY_REPO}\n', encoding="utf-8",
        )
        self.tool_sha = commit(self.tools, "Pinned official projection tools")

        self.source_manifest = (
            '[package]\nname = "zobs"\nversion = "0.1.0"\nedition = "2024"\n'
            f'repository = "{REPOSITORY}"\nlicense = "MIT"\n'
            '[dependencies]\n'
            f'zclap = {{ git = "{DEPENDENCY_REPO}", features = ["std"] }}\n'
        )
        (self.repo / "Cargo.toml").write_text(self.source_manifest, encoding="utf-8")
        self.source_lock = (
            'version = 4\n\n[[package]]\nname = "zobs"\nversion = "0.1.0"\n'
            'dependencies = ["zclap"]\n\n[[package]]\nname = "zclap"\n'
            f'version = "0.1.4"\nsource = "git+{DEPENDENCY_REPO}#{DEPENDENCY_SHA}"\n'
        ).encode()
        (self.repo / "Cargo.lock").write_bytes(self.source_lock)
        (self.repo / "src").mkdir()
        (self.repo / "src/lib.rs").write_bytes(COMMITTED_SOURCE)
        self.source_sha = commit(self.repo)

        self.registry_lock = (
            'version = 4\n\n[[package]]\nname = "zobs"\nversion = "0.1.0"\n'
            'dependencies = ["zclap"]\n\n[[package]]\nname = "zclap"\n'
            f'version = "0.1.4"\nsource = "{REGISTRY}"\nchecksum = "{"c" * 64}"\n'
        ).encode()
        self.lock_path = self.registry_locks / f"{LABEL}.Cargo.lock"
        self.lock_path.write_bytes(self.registry_lock)
        self.archive_path = self.archives / f"{LABEL}.crate"
        self.make_archive()
        self.receipt = {
            "package": NAME, "version": VERSION, "github": REPOSITORY,
            "source_git_sha": self.source_sha, "projection_tool_sha": self.tool_sha,
            "registry_lock_sha256": digest(self.registry_lock),
            "archive_sha256": digest(self.archive_path.read_bytes()),
        }
        self.receipt_path = self.root / "receipts.json"
        self.receipts = self.read_document()
        self.work_serial = 0
        self.previous_modules = {
            name: sys.modules.get(name) for name in ("release_projection", "cargo_versions")
        }
        self.addCleanup(self.restore_modules)

    def restore_modules(self):
        for name, module in self.previous_modules.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module

    def make_archive(self, extra=None):
        package_manifest = (
            '[package]\nname = "zobs"\nversion = "0.1.0"\n'
            f'repository = "{REPOSITORY}"\n'
            '[dependencies.zclap]\nversion = "=0.1.4"\nfeatures = ["std"]\n'
        ).encode()
        files = {"Cargo.toml": package_manifest, "src/lib.rs": COMMITTED_SOURCE}
        files.update(extra or {})
        with tarfile.open(self.archive_path, "w:gz") as archive:
            for name, payload in files.items():
                member = tarfile.TarInfo(f"{LABEL}/{name}")
                member.size = len(payload)
                member.mode = 0o644
                archive.addfile(member, io.BytesIO(payload))

    def read_document(self, document=None):
        if document is None:
            document = {"schema_version": 2, "receipts": [self.receipt]}
        payload = json.dumps(document, sort_keys=True).encode()
        self.receipt_path.write_bytes(payload)
        return gate.read_receipts(self.receipt_path, digest(payload))

    def refresh_receipt(self):
        self.receipt["source_git_sha"] = self.source_sha
        self.receipt["registry_lock_sha256"] = digest(self.lock_path.read_bytes())
        self.receipt["archive_sha256"] = digest(self.archive_path.read_bytes())
        self.receipts = self.read_document()

    def fake_rebuild(self, manifest, target):
        """Assert real staging semantics, then substitute the Cargo executable."""
        staged = tomllib.loads(manifest.read_text())
        dependency = staged["dependencies"]["zclap"]
        self.assertEqual(dependency["version"], "=0.1.4")
        self.assertNotIn("git", dependency)
        self.assertEqual(dependency["features"], ["std"])
        self.assertEqual((manifest.parent / "src/lib.rs").read_bytes(), COMMITTED_SOURCE)
        self.assertEqual((manifest.parent / "Cargo.lock").read_bytes(), self.registry_lock)
        self.assertFalse((manifest.parent / ".git").exists())
        self.assertFalse((manifest.parent / ".cargo_vcs_info.json").exists())
        package = target / "package"
        package.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(self.archive_path, package / f"{LABEL}.crate")

    def verify(self, *, rebuild=None, receipts=None, source_sha=None):
        self.work_serial += 1
        work = self.root / f"verified-{self.work_serial}"
        with patch.object(gate, "rebuild_package", side_effect=rebuild or self.fake_rebuild) as mocked:
            result = gate.verify_package(
                self.repo, source_sha or self.source_sha, self.tools,
                self.receipts if receipts is None else receipts,
                self.archives, self.registry_locks, work,
                target_dir=work / "target",
            )
        self.assertEqual(mocked.call_count, 1)
        return result, work

    def test_success_uses_committed_source_and_official_projection(self):
        # An unrelated dirty worktree must not replace the trusted Git snapshot.
        (self.repo / "src/lib.rs").write_text("uncommitted replacement\n")
        (self.repo / "Cargo.toml").write_text('[package]\nname = "wrong"\n')
        result, work = self.verify()
        self.assertEqual(result["status"], "PROJECTED_RELEASE_REBUILT_AND_VERIFIED")
        self.assertEqual(result["source_git_sha"], self.source_sha)
        self.assertEqual(result["projection_tool_sha"], self.tool_sha)
        self.assertEqual(result["registry_lock_sha256"], digest(self.registry_lock))
        self.assertEqual(result["archive_sha256"], digest(self.archive_path.read_bytes()))
        report = json.loads((work / "stage/projection.json").read_text())
        self.assertEqual(report["conversions"][0]["git_sha"], DEPENDENCY_SHA)
        self.assertEqual(report["conversions"][0]["version"], "0.1.4")
        self.assertEqual(report["remaining_git_dependencies"], [])
        self.assertEqual(result["source_lock_sha256"], digest(self.source_lock))
        self.assertIn("Cargo.toml", result["projected_manifest_sha256"])
        self.assertEqual(json.loads((work / "verification.json").read_text()), result)

    def test_receipt_requires_an_independently_matching_full_pin(self):
        for pin in ("f" * 64, "A" * 64, "abbreviated", ""):
            with self.subTest(pin=pin), self.assertRaises(gate.ReceiptError):
                gate.read_receipts(self.receipt_path, pin)

    def test_duplicate_and_invalid_receipt_documents_are_rejected(self):
        invalid_documents = [
            b'{"schema_version":2,"schema_version":2,"receipts":[]}',
            json.dumps({"schema_version": 2, "receipts": [self.receipt, self.receipt]}).encode(),
            json.dumps({"schema_version": 1, "receipts": [self.receipt]}).encode(),
            json.dumps({"schema_version": True, "receipts": [self.receipt]}).encode(),
            json.dumps({"schema_version": 2, "receipts": [{**self.receipt, "unexpected": "field"}]}).encode(),
            json.dumps({"schema_version": 2, "receipts": [{**self.receipt, "archive_sha256": "abc"}]}).encode(),
        ]
        for payload in invalid_documents:
            with self.subTest(payload=payload):
                self.receipt_path.write_bytes(payload)
                with self.assertRaises(gate.ReceiptError):
                    gate.read_receipts(self.receipt_path, digest(payload))

    def test_tool_commit_and_each_loaded_tool_file_are_pinned(self):
        wrong = copy.deepcopy(self.receipts)
        wrong[(NAME, VERSION)]["projection_tool_sha"] = "f" * 40
        with self.assertRaisesRegex(gate.ReceiptError, "tool revision"):
            self.verify(receipts=wrong)
        for relative in gate.TOOL_FILES:
            path = self.tools / relative
            original = path.read_bytes()
            with self.subTest(file=relative):
                path.write_bytes(original + b"\n# dirty tool bytes\n")
                try:
                    with self.assertRaisesRegex(gate.ReceiptError, "differs from its pinned commit"):
                        self.verify()
                finally:
                    path.write_bytes(original)

    def test_verified_source_is_executed_instead_of_untracked_bytecode(self):
        payloads = {
            "cargo_versions.py": "def satisfies(version, requirement):\n    return True\n",
            "release_projection.py": "raise RuntimeError('untracked bytecode executed')\n",
        }
        for name, payload in payloads.items():
            source = self.tools / "scripts" / name
            metadata = source.stat()
            cache = Path(importlib.util.cache_from_source(str(source)))
            cache.parent.mkdir(parents=True, exist_ok=True)
            # A timestamp cache can appear valid while its executable code has
            # no relationship to the Git-pinned .py bytes. Preserve the real
            # source's timestamp and size in the cache header to exercise that.
            header = importlib.util.MAGIC_NUMBER + struct.pack(
                "<III", 0, int(metadata.st_mtime) & 0xFFFFFFFF,
                metadata.st_size & 0xFFFFFFFF,
            )
            cache.write_bytes(header + marshal.dumps(compile(payload, str(source), "exec")))
            self.assertEqual(
                source.read_bytes(),
                subprocess.run(
                    ["git", "-C", str(self.tools), "show", f"{self.tool_sha}:scripts/{name}"],
                    check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                ).stdout,
            )
        projection = gate.load_projection(self.tools, self.tool_sha)
        self.assertFalse(projection.satisfies("0.1.4", "=999.0.0"))
        result, _ = self.verify()
        self.assertEqual(result["status"], "PROJECTED_RELEASE_REBUILT_AND_VERIFIED")

    def test_source_commit_must_have_a_matching_receipt(self):
        (self.repo / "src/lib.rs").write_text("pub fn changed() {}\n")
        different = commit(self.repo, "Different immutable source")
        with self.assertRaisesRegex(gate.ReceiptError, "identifies this source commit"):
            self.verify(source_sha=different)

    def test_archive_digest_rejects_changed_candidate_bytes(self):
        with self.archive_path.open("ab") as archive:
            archive.write(b"untrusted appended data")
        with self.assertRaisesRegex(gate.ReceiptError, "archive does not match"):
            self.verify()

    def test_registry_lock_digest_rejects_untrusted_edit(self):
        self.lock_path.write_bytes(self.registry_lock + b"\n# untrusted edit\n")
        with self.assertRaisesRegex(gate.ReceiptError, "independently trusted digest"):
            self.verify()

    def test_git_sources_cannot_survive_in_lock_or_projection(self):
        with self.subTest(location="registry lock"):
            self.lock_path.write_bytes(self.source_lock)
            self.refresh_receipt()
            with self.assertRaisesRegex(gate.ReceiptError, "without Git sources"):
                self.verify()
        self.lock_path.write_bytes(self.registry_lock)
        (self.repo / "Cargo.toml").write_text(
            self.source_manifest + 'external = { git = "https://github.com/fixture-vendor/external" }\n'
        )
        self.source_sha = commit(self.repo, "Unprojectable external Git dependency")
        self.refresh_receipt()
        with self.subTest(location="projected manifest"):
            with self.assertRaisesRegex(gate.ReceiptError, "still contains Git dependencies"):
                self.verify()

    def test_registry_resolution_cannot_change_internal_version(self):
        self.lock_path.write_bytes(self.registry_lock.replace(b'version = "0.1.4"', b'version = "0.1.5"'))
        # A trusted digest binds bytes; it does not waive the source graph check.
        self.refresh_receipt()
        with self.assertRaisesRegex(gate.ReceiptError, "internal identity: zclap 0.1.4"):
            self.verify()

    def test_fabricated_vcs_metadata_is_rejected_in_archive_and_source(self):
        metadata = json.dumps({"git": {"sha1": self.source_sha}, "path_in_vcs": ""}).encode()
        with self.subTest(location="archive"):
            self.make_archive({".cargo_vcs_info.json": metadata})
            self.refresh_receipt()
            with self.assertRaisesRegex(gate.ReceiptError, "must not manufacture Cargo VCS"):
                self.verify()
        self.make_archive()
        (self.repo / ".cargo_vcs_info.json").write_bytes(metadata)
        self.source_sha = commit(self.repo, "Source containing fabricated VCS metadata")
        self.refresh_receipt()
        with self.subTest(location="source snapshot"):
            with self.assertRaisesRegex(gate.ReceiptError, "fabricated Cargo VCS"):
                self.verify()

    def test_rebuilt_archive_must_match_the_trusted_bytes(self):
        def mismatch(manifest, target):
            self.fake_rebuild(manifest, target)
            with (target / "package" / f"{LABEL}.crate").open("ab") as archive:
                archive.write(b"different rebuild")
        with self.assertRaisesRegex(gate.ReceiptError, "Rebuilt crate differs"):
            self.verify(rebuild=mismatch)

    def test_packaging_must_preserve_the_verified_registry_lock(self):
        def changed_lock(manifest, target):
            self.fake_rebuild(manifest, target)
            (manifest.parent / "Cargo.lock").write_bytes(self.registry_lock + b"\n# changed by packaging\n")
        with self.assertRaisesRegex(gate.ReceiptError, "modified the verified registry lock"):
            self.verify(rebuild=changed_lock)


if __name__ == "__main__":
    unittest.main()
