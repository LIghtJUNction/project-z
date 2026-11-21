"""Offline regressions for same-version/different-commit release dependencies."""

import gzip
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import release_receipts as verifier


PACKAGE = "zuse-computer"
VERSION = "0.2.2"
URL = "https://github.com/lightjunction/zuse"
LOCKED = "a1bb8fd2cbce0a9d85134999883c578358065242"
PUBLISHED = "94c837551a7a2fd8ec9f577a3e2f57309bd5ce5a"
LABEL = f"{PACKAGE}-{VERSION}"
DEP = b'''[package]
name = "ssmcp"
version = "0.10.14"
edition = "2024"
[dependencies]
zuse = { git = "https://github.com/LIghtJUNction/zuse.git", package = "zuse-computer", default-features = false }
'''
LOCK = f'''version = 4
[[package]]
name = "{PACKAGE}"
version = "{VERSION}"
source = "git+https://github.com/LIghtJUNction/zuse#{LOCKED}"
'''.encode()


def fixture_archive(revision, new_motion=False, dirty=False, repo=URL):
    manifest = f'[package]\nname = "{PACKAGE}"\nversion = "{VERSION}"\nrepository = "{repo}"\n'
    vcs = json.dumps({"git": {"sha1": revision, "dirty": dirty}, "path_in_vcs": ""})
    motion = "pub fn programmed_motion() {}\n" if new_motion else "pub fn old_motion() {}\n"
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode="w", format=tarfile.USTAR_FORMAT) as archive:
        for name, payload in {"Cargo.toml": manifest, ".cargo_vcs_info.json": vcs,
                              "src/motion.rs": motion}.items():
            data = payload.encode()
            member = tarfile.TarInfo(f"{LABEL}/{name}")
            member.size = len(data)
            archive.addfile(member, io.BytesIO(data))
    return gzip.compress(output.getvalue(), mtime=0)


class ReceiptTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.repo = self.root / "source"
        self.repo.mkdir()
        self.receipt = self.root / "receipts.json"
        self.archive = self.root / f"{LABEL}.crate"
        git = ["git", "-C", str(self.repo)]
        subprocess.run([*git, "init", "-q"], check=True)
        (self.repo / "Cargo.toml").write_bytes(DEP)
        (self.repo / "Cargo.lock").write_bytes(LOCK)
        subprocess.run([*git, "add", "Cargo.toml", "Cargo.lock"], check=True)
        subprocess.run([*git, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                        "-c", "commit.gpgsign=false", "-c", "core.hooksPath=/dev/null",
                        "commit", "-qm", "fixture"], check=True)
        self.commit = subprocess.check_output([*git, "rev-parse", "HEAD"], text=True).strip()
        self.plans = verifier.source_plan(self.repo, self.commit, "Cargo.toml", (), {URL})
        self.assertEqual([(p["alias"], p["git_sha"]) for p in self.plans], [("zuse", LOCKED)])

    def make_receipt(self, contents, revision, url=URL):
        self.archive.write_bytes(contents)
        doc = {"schema_version": 1, "receipts": [
            {"package": PACKAGE, "version": VERSION, "github": url, "git_sha": revision,
             "archive_sha256": hashlib.sha256(contents).hexdigest()},
        ]}
        payload = json.dumps(doc, sort_keys=True).encode()
        self.receipt.write_bytes(payload)
        return hashlib.sha256(payload).hexdigest()

    def check(self, pin):
        receipts = verifier.read_receipts(self.receipt, pin)
        return verifier.verify_archives(self.plans, receipts, self.root)

    def test_rejects_published_zuse_0_2_2_even_with_trusted_old_archive(self):
        # Mirrors the SSMCP -> zuse-computer incident: name, version and
        # repository are identical; old crates.io source lacks the new motion.
        old = fixture_archive(PUBLISHED)
        pin = self.make_receipt(old, PUBLISHED)
        with self.assertRaisesRegex(verifier.ProjectionError, "differs from locked Git SHA"):
            self.check(pin)

    def test_even_relabeling_a_valid_archive_hash_cannot_override_commit(self):
        pin = self.make_receipt(fixture_archive(PUBLISHED), LOCKED)
        with self.assertRaisesRegex(verifier.ProjectionError, "exact clean locked Git commit"):
            self.check(pin)

    def test_matching_receipt_bytes_identity_and_commit_accept(self):
        candidate = fixture_archive(LOCKED, new_motion=True)
        pin = self.make_receipt(candidate, LOCKED)
        record, = self.check(pin)
        self.assertEqual(record, {"package": PACKAGE, "version": VERSION, "github": URL,
                                  "git_sha": LOCKED, "archive_sha256": hashlib.sha256(candidate).hexdigest()})
        self.assertEqual((self.repo / "Cargo.toml").read_bytes(), DEP)
        self.assertEqual((self.repo / "Cargo.lock").read_bytes(), LOCK)

    def test_archive_swap_and_receipt_swap_are_rejected(self):
        original = fixture_archive(LOCKED, new_motion=True)
        pin = self.make_receipt(original, LOCKED)
        with self.subTest("archive changed"), self.assertRaisesRegex(verifier.ProjectionError, "archive SHA-256"):
            self.archive.write_bytes(fixture_archive(LOCKED))
            self.check(pin)
        with self.subTest("receipt changed"), self.assertRaisesRegex(verifier.ProjectionError, "trusted receipt SHA-256"):
            self.receipt.write_bytes(self.receipt.read_bytes() + b"\n")
            self.check(pin)

    def test_dirty_archive_and_wrong_repo_are_rejected(self):
        for payload, repo, reason in (
            (fixture_archive(LOCKED, dirty=True), URL, "exact clean locked Git commit"),
            (fixture_archive(LOCKED), "https://github.com/wrong/zuse", "receipt repository"),
            (fixture_archive(LOCKED, repo="https://github.com/wrong/zuse"), URL, "archive package, version, or repository"),
        ):
            with self.subTest(reason=reason), self.assertRaisesRegex(verifier.ProjectionError, reason):
                self.check(self.make_receipt(payload, LOCKED, url=repo))


if __name__ == "__main__":
    unittest.main()
