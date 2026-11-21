"""Tests for release staging. No external Git, registry, or publishing calls."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import release_projection as projection


URL = "https://github.com/lightjunction/zconv"
SHA = "a" * 40
LOCK = f"""version = 4

[[package]]
name = "zconv"
version = "0.4.0"
source = "git+https://github.com/LIghtJUNction/zconv.git#{SHA}"

[[package]]
name = "zconv"
version = "0.3.0"
source = "registry+https://github.com/rust-lang/crates.io-index"

[[package]]
name = "zconv"
version = "0.1.0"
source = "git+https://github.com/other/zconv#{'b' * 40}"
"""
MANIFEST = '''[workspace]
members = ["member"]

[workspace.package]
version = "0.9.0"

[workspace.dependencies]
kernel = { package = "zconv", git = "https://github.com/LightJunction/zconv", version = "^0.4.0", default-features = false }

[package]
name = "projection-fixture"
version.workspace = true
edition = "2021"

[dependencies]
kernel.workspace = true

[features]
default = []
'''
MEMBER = '''[package]
name = "projection-member"
version.workspace = true
edition = "2021"

[target.'cfg(unix)'.dev-dependencies.dev_alias]
package = "zconv"
git = "https://github.com/lightjunction/zconv.git/"
version = ">=0.4, <0.5"
default-features = false
features = ["fixture-feature"]

[build-dependencies.build_alias]
package = "zconv"
git = "https://github.com/LIghtJUNction/zconv.git"
version = "~0.4.0"

[[example]]
name = "one"
path = "examples/one.rs"

[package.metadata.fixture]
note = """keep # characters, \\u007f and apostrophes: it's fine"""
'''


class MatchTests(unittest.TestCase):
    def test_exactly_one_git_pin_not_registry_or_other_repo(self):
        locks = projection.parse_lock(tomllib.loads(LOCK))
        self.assertEqual(projection.exact_pin(locks, "zconv", URL), ("0.4.0", SHA))
        self.assertIsNone(projection.github_url("https://github.com/lightjunction/zconv?rev=some"))
        self.assertIsNone(projection.github_url("https://github.com.evil.invalid/lightjunction/zconv"))

    def test_missing_malformed_selector_and_ambiguous_fail_closed(self):
        for raw in (
            "",
            LOCK.replace(SHA, "abc"),
            LOCK.replace(".git#", ".git?branch=main#"),
            LOCK + f'''
[[package]]
name = "zconv"
version = "0.5.0"
source = "git+https://github.com/lightjunction/zconv#{'c' * 40}"
''',
        ):
            with self.subTest(raw=raw[-170:]), self.assertRaises(projection.ProjectionError):
                projection.exact_pin(projection.parse_lock(tomllib.loads(raw)), "zconv", URL)

    def test_preserves_unknown_external_dependency_and_rejects_selectors(self):
        lock = projection.parse_lock(tomllib.loads(LOCK))
        document = {"dependencies": {"alias": {
            "git": "https://github.com/other/zconv", "package": "zconv", "version": "=0.4.0",
        }}}
        original = deepcopy(document)
        self.assertFalse(projection.rewrite(document, lock, {URL}, "Cargo.toml"))
        self.assertEqual(document, original)
        for key, value in {
            "rev": SHA, "branch": "main", "tag": "v0.4.0", "path": "../zconv",
            "registry": "other", "registry-index": "https://example.invalid/index",
            "workspace": True,
        }.items():
            with self.subTest(key=key):
                document = {"dependencies": {"alias": {
                    "git": URL, "package": "zconv", "version": "=0.4.0", key: value,
                }}}
                original = deepcopy(document)
                with self.assertRaisesRegex(projection.ProjectionError, "alternate source"):
                    projection.rewrite(document, lock, {URL}, "Cargo.toml")
                self.assertEqual(document, original)

    def test_compatible_version_metadata_preserves_options_and_uses_locked_pin(self):
        lock = projection.parse_lock(tomllib.loads(LOCK))
        for requirement in ("0.4", "^0.4.0", "~0.4.0", ">=0.3, <0.5", "=0.4.0", "0.4.*"):
            with self.subTest(requirement=requirement):
                options = {"package": "zconv", "default-features": False,
                           "optional": True, "features": ["fixture-feature"]}
                document = {"dependencies": {"kernel": {
                    **options, "git": URL, "version": requirement,
                }}}
                records = projection.rewrite(document, lock, {URL}, "Cargo.toml")
                self.assertEqual(document["dependencies"]["kernel"],
                                 {**options, "version": "=0.4.0"})
                self.assertEqual([(item["alias"], item["version"], item["git_sha"])
                                  for item in records], [("kernel", "0.4.0", SHA)])

    def test_mismatched_or_invalid_version_metadata_is_rejected_unchanged(self):
        lock = projection.parse_lock(tomllib.loads(LOCK))
        cases = [(value, "does not satisfy") for value in ("^0.5", ">=1", "=0.4.1")]
        cases += [(value, "invalid version requirement")
                  for value in ("", "not-a-version", "0.4 || 0.5", None, True, 1, {}, [])]
        for requirement, reason in cases:
            with self.subTest(requirement=requirement):
                document = {"dependencies": {"kernel": {
                    "package": "zconv", "git": URL, "version": requirement,
                }}}
                original = deepcopy(document)
                with self.assertRaisesRegex(projection.ProjectionError, reason):
                    projection.rewrite(document, lock, {URL}, "Cargo.toml")
                self.assertEqual(document, original)


class RepositoryTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.git("init", "-q")
        self.git("config", "user.name", "Release Fixture")
        self.git("config", "user.email", "fixture@example.invalid")
        self.git("config", "commit.gpgsign", "false")
        self.git("config", "core.hooksPath", str(self.root / "no-hooks"))
        for filename, contents in {
            "Cargo.toml": MANIFEST,
            "Cargo.lock": LOCK,
            "member/Cargo.toml": MEMBER,
            "src/lib.rs": "pub fn one() {}\n",
            "member/src/lib.rs": "pub fn two() {}\n",
            "member/examples/one.rs": "fn main() {}\n",
        }.items():
            path = self.repo / filename
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(contents, encoding="utf-8")
        self.git("add", ".")
        self.git("commit", "-qm", "fixture Git without registry versions")
        self.commit = self.git("rev-parse", "HEAD").strip()

    def git(self, *args):
        return subprocess.check_output(["git", *args], cwd=self.repo, text=True)

    def test_stage_only_clean_snapshot_with_aliases_features_and_targets(self):
        (self.repo / "src/lib.rs").write_text("uncommitted work\n")
        (self.repo / "local.txt").write_text("not a staged file\n")
        output = self.root / "stage"
        report = projection.stage(self.repo, self.commit, "Cargo.toml", output, {URL})
        staged = output / "source"
        self.assertEqual(report["status"], "STAGING_ONLY_UNVERIFIED_NO_PUBLISH")
        self.assertEqual(report["source_commit"], self.commit)
        self.assertEqual(report["source_lock_sha256"], hashlib.sha256(LOCK.encode()).hexdigest())
        self.assertEqual(report, json.loads((output / "projection.json").read_text()))
        self.assertEqual(len(report["conversions"]), 3)
        self.assertTrue(all(item["git_sha"] == SHA for item in report["conversions"]))
        self.assertFalse((staged / "Cargo.lock").exists())
        self.assertFalse((staged / "local.txt").exists())
        self.assertFalse((staged / ".git").exists())
        self.assertEqual((staged / "src/lib.rs").read_text(), "pub fn one() {}\n")
        self.assertEqual((self.repo / "src/lib.rs").read_text(), "uncommitted work\n")
        self.assertEqual((self.repo / "Cargo.toml").read_text(), MANIFEST)
        self.assertEqual((self.repo / "Cargo.lock").read_text(), LOCK)
        for filename, original in [("Cargo.toml", MANIFEST), ("member/Cargo.toml", MEMBER)]:
            expected = deepcopy(tomllib.loads(original))
            for _, declarations in projection.dependency_tables(expected):
                for spec in declarations.values():
                    if isinstance(spec, dict) and spec.pop("git", None):
                        spec["version"] = "=0.4.0"
            file_bytes = (staged / filename).read_bytes()
            self.assertEqual(tomllib.loads(file_bytes.decode()), expected)
            self.assertEqual(report["projected_manifest_sha256"][filename], hashlib.sha256(file_bytes).hexdigest())

        if shutil.which("cargo"):
            result = subprocess.run(
                ["cargo", "metadata", "--offline", "--no-deps", "--format-version=1"],
                cwd=staged, check=True, capture_output=True, text=True,
            )
            self.assertEqual(len(json.loads(result.stdout)["workspace_members"]), 2)

    def test_failures_leave_stage_and_checkout_untouched(self):
        with self.assertRaisesRegex(projection.ProjectionError, "outside"):
            projection.stage(self.repo, self.commit, "Cargo.toml", self.repo / "bad", {URL})
        with self.assertRaisesRegex(projection.ProjectionError, "full"):
            projection.stage(self.repo, "HEAD", "Cargo.toml", self.root / "bad", {URL})
        with self.assertRaises(projection.ProjectionError):
            projection.stage(self.repo, self.commit, "Cargo.toml", self.root / "bad", {URL},
                             ["no-member/Cargo.toml"])
        self.assertFalse((self.repo / "bad").exists())
        self.assertFalse((self.root / "bad").exists())
        self.assertFalse(self.git("status", "--porcelain"))

    def test_auto_version_ignores_prereleases_and_other_tag_names(self):
        for tag in ["v0.2.0", "v0.10.0", "v999.0.0-rc.1", "legacy-v99.0.0", "member-v1.2.0"]:
            self.git("tag", tag)
        cases = [
            ("Cargo.toml", "major", "v", "v1.0.0"),
            ("Cargo.toml", "patch", "v", "v0.10.1"),
            ("member/Cargo.toml", "minor", "member-v", "member-v1.3.0"),
            ("member/Cargo.toml", "patch", "new-v", "new-v0.9.1"),
        ]
        for manifest, bump, prefix, tag in cases:
            with self.subTest(tag=tag):
                report = projection.calculate_version(self.repo, self.commit, manifest, "Cargo.toml", bump, prefix)
                self.assertEqual(report["tag"], tag)
                self.assertEqual(report["current"], "0.9.0")
        self.assertFalse(self.git("status", "--porcelain"))
        self.assertEqual(len(self.git("tag").splitlines()), 5)


if __name__ == "__main__":
    unittest.main()
