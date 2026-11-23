"""Scheduled release state transitions with local Git remotes and a fake registry."""
import base64
from contextlib import chdir, ExitStack
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import scheduled as s
import scheduled_registry as registry


class ScheduledTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.dir = Path(self.temp.name)
        self.root = self.dir / "root"
        self.root.mkdir()
        self.ctx = ExitStack()
        self.addCleanup(self.ctx.close)
        self.ctx.enter_context(chdir(self.root))
        self.ctx.enter_context(patch.dict(os.environ, {
            "RUNNER_TEMP": str(self.dir), "GITHUB_OUTPUT": str(self.dir / "out"),
            "GITHUB_REPOSITORY": "test/fixture", "GITHUB_RUN_ATTEMPT": "1",
        }))
        s.git("init", "-b", "main")
        s.git("config", "user.name", "Fixture")
        s.git("config", "user.email", "fixture@example.invalid")
        shutil.copytree(SCRIPTS, "scripts", ignore=shutil.ignore_patterns("__pycache__"))
        Path("project-z.toml").write_text("")
        s.git("add", "scripts", "project-z.toml")
        self.base = self.snapshot("1", "0.1.0")
        s.git("tag", "v0.1.0")
        remote = self.dir / "remote.git"
        s.git("init", "--bare", str(remote))
        s.git("remote", "add", "origin", str(remote))
        s.git("push", "--tags", "origin", "main")

    def snapshot(self, digit, version):
        sha = digit * 40
        repo = dict(name="child", path="child", url="https://github.com/test/child.git", branch="main", commit=sha)
        pkg = dict(name="fixture", repository="child", version=version, publish=True)
        Path("catalog.json").write_text(json.dumps(dict(repositories=[repo], packages=[pkg])))
        s.git("update-index", "--add", "--cacheinfo", f"160000,{sha},child")
        s.git("add", "catalog.json")
        s.git("commit", "-qm", f"fixture {digit}")
        return s.git("rev-parse", "HEAD")

    def test_dry_run_or_wrong_push_destination_denies_writer(self):
        with self.assertRaisesRegex(ValueError, "canonical main"):
            s.authorize_writer()
        with patch.dict(os.environ, dict(GITHUB_EVENT_NAME="schedule", PROJECT_Z_SCHEDULED_WRITES="true",
                                         GITHUB_REF="refs/heads/main", GITHUB_REPOSITORY="LIghtJUNction/project-z")):
            with self.assertRaisesRegex(ValueError, "canonical main"):
                s.authorize_writer()

    def test_verified_bundle_replays_on_shallow_base(self):
        sha = self.snapshot("2", "0.1.1")
        audit = Path("dist/maintenance")
        audit.mkdir(parents=True)
        (audit / "audit.json").write_text(json.dumps({"errors": [], "snapshot": {"status": "ready", "commit": sha}}))
        with patch.dict(os.environ, {"GITHUB_SHA": self.base}):
            s.bundle()
        clone = self.dir / "runner"
        s.git("clone", "--depth", "1", "--branch", "main", (self.dir / "remote.git").as_uri(), str(clone))
        with chdir(clone):
            s.git("fetch", "--no-tags", str(self.dir / "cohort.bundle"), "refs/heads/cohort")
            self.assertEqual(s.git("rev-parse", "FETCH_HEAD"), sha)
            self.assertEqual(s.verify(self.base, sha), {"child"})

    def test_no_changes_do_not_emit_candidate_or_create_tag(self):
        audit = Path("dist/maintenance")
        audit.mkdir(parents=True)
        (audit / "audit.json").write_text(json.dumps({"errors": [], "snapshot": {"status": "no_changes"}}))
        s.bundle()
        self.assertFalse((self.dir / "out").exists())
        self.assertEqual(s.git("tag", "--list"), "v0.1.0")

    def test_updated_sources_without_new_version_sync_only(self):
        self.assertEqual(s.plan(self.base, self.snapshot("2", "0.1.0")), ("", []))

    def test_version_increase_plans_one_patch_existing_digest_skips(self):
        sha = self.snapshot("2", "0.1.1")
        self.assertEqual(s.plan(self.base, sha)[0], "v0.1.1")
        s.git("tag", "v0.1.1", sha)
        self.assertEqual(s.plan(self.base, sha), ("", []))

    def test_non_cargo_version_qualifies_only_the_github_snapshot(self):
        Path("project-z.toml").write_text('[scheduled.version_manifests]\nchild="VERSION"\n')
        def blob(*args):
            version = "2.1.0" if args[-1].endswith("2"*40) else "2.0.0"
            return json.dumps(dict(type="file", encoding="base64", content=base64.b64encode(version.encode()).decode()))
        s.native_version.cache_clear()
        self.addCleanup(s.native_version.cache_clear)
        with patch.object(s, "gh", side_effect=blob):
            tag, updates = s.plan(self.base, self.snapshot("2", "0.1.0"))
        self.assertEqual(tag, "v0.1.1")
        self.assertEqual([(p["version"], p["publish"]) for p in updates], [("2.1.0", False)])
        with patch.object(s, "gh") as remote, self.assertRaisesRegex(ValueError, "unknown version manifest"):
            s.native_version("https://github.com/test/child.git", "2"*40, "../other")
        remote.assert_not_called()

    def test_historical_version_in_another_snapshot_skips(self):
        sha = self.snapshot("2", "0.1.1")
        s.git("tag", "v0.1.1", self.snapshot("3", "0.1.1"))
        self.assertEqual(s.plan(self.base, sha), ("", []))

    def test_release_test_failure_never_emits_publish_outputs(self):
        self.snapshot("2", "0.1.1")
        with patch.dict(os.environ, {"GITHUB_SHA": self.base}), patch.object(registry, "child_targets", return_value=[]):
            # Fail only the official packager subprocess.
            original = subprocess.check_output
            def intercept(args, **kwargs):
                if "scripts/release.py" in args:
                    raise subprocess.CalledProcessError(1, args)
                return original(args, **kwargs)
            with patch.object(subprocess, "check_output", side_effect=intercept), self.assertRaises(subprocess.CalledProcessError):
                s.package()
        self.assertFalse((self.dir / "out").exists())
        self.assertFalse((self.dir / "release-assets").exists())

    def test_atomic_reservation_and_idempotent_recovery(self):
        sha = self.snapshot("2", "0.1.1")
        tag = "v0.1.1"
        dest = self.dir / "release-assets"
        dest.mkdir()
        archive = dest / f"project-z-{tag}.tar.gz"
        archive.write_bytes(b"fixture archive")
        manifest = dest / "commits.txt"
        manifest.write_text(f"Project Z {tag}\nproject_z\t{sha}\n")
        frozen = dest / "registry-plan.json"
        frozen.write_text(json.dumps(dict(base=self.base, candidate=sha, tag=tag, targets=[])))
        self.ctx.enter_context(patch.dict(os.environ, dict(GITHUB_SHA=self.base, CANDIDATE=sha, PLAN_DIGEST=s.digest(frozen),
            RELEASE_TAG=tag, ARCHIVE_DIGEST=s.digest(archive), MANIFEST_DIGEST=s.digest(manifest))))
        self.ctx.enter_context(patch.object(s, "authorize_writer"))
        self.ctx.enter_context(patch.object(s, "fresh"))
        self.ctx.enter_context(patch.object(registry, "child_targets", return_value=[]))
        fake = {"draft": None, "assets": {}, "fail": True, "published": 0}
        def gh(*args):
            if args[0] == "api":
                return json.dumps([[{"tag_name": tag}] if fake["draft"] is not None else []])
            if args[1] == "create":
                self.assertIsNone(fake["draft"])
                fake["draft"] = True
                fake["body"] = args[-1]
            elif args[1] == "view":
                if args[2] == "v0.1.0":
                    return "false"
                return json.dumps(dict(body=fake["body"], assets=list(fake["assets"].values()), isDraft=fake["draft"]))
            elif args[1] == "upload":
                path = Path(args[3])
                if path == manifest and fake["fail"]:
                    raise RuntimeError("upload interrupted")
                self.assertNotIn(path.name, fake["assets"])
                fake["assets"][path.name] = dict(name=path.name, digest="sha256:" + s.digest(path))
            elif args[1] == "edit":
                fake["draft"] = False
                fake["published"] += 1
            return ""
        with patch.object(s, "gh", side_effect=gh):
            with self.assertRaisesRegex(RuntimeError, "upload interrupted"):
                s.record()
            self.assertEqual(s.remote_refs()["refs/heads/main"], sha)
            self.assertEqual(s.remote_refs()["refs/tags/" + tag], sha)
            fake["fail"] = False
            s.record()
            s.record()
        self.assertEqual(fake["published"], 1)

    @unittest.skipIf(os.name == "nt", "POSIX server hook")
    def test_protected_branch_denies_atomic_main_and_tag(self):
        sha = self.snapshot("2", "0.1.1")
        hook = self.dir / "remote.git/hooks/pre-receive"
        hook.write_text("#!/bin/sh\nexit 1\n")
        hook.chmod(0o755)
        with self.assertRaises(subprocess.CalledProcessError):
            s.reserve(self.base, sha, "v0.1.1")
        self.assertEqual(s.remote_refs()["refs/heads/main"], self.base)
        self.assertNotIn("refs/tags/v0.1.1", s.remote_refs())

    def test_moved_base_stale_sources_and_unexpected_paths_block(self):
        sha = self.snapshot("2", "0.1.1")
        with self.assertRaisesRegex(ValueError, "remote refs changed"):
            s.compare_push([f"HEAD {sha} refs/heads/main {'9'*40}"], self.base, sha, "")
        with patch.dict(os.environ, dict(GITHUB_SHA=self.base, CANDIDATE=sha, RELEASE_TAG="")), \
             patch.object(s, "authorize_writer"), patch.object(s, "freshness_errors", return_value=["child moved"]), self.assertRaisesRegex(ValueError, "child moved"):
            s.record()
        Path("unauthorized").write_text("fixture")
        s.git("add", "unauthorized")
        s.git("commit", "--amend", "--no-edit")
        with self.assertRaisesRegex(ValueError, "unexpected candidate change"):
            s.verify(self.base, s.git("rev-parse", "HEAD"))


class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.repo = dict(name="child", commit="1"*40, branch="main", url="https://github.com/test/child.git")
        self.pkg = dict(name="fixture", repository="child", publish=True, version="0.1.1")
        self.rule = dict(repository="test/child", workflow="release.yml", workflow_blob="2"*40, crate_owner="owner")

    def test_private_github_only_and_unapproved_crates_skip(self):
        self.assertIsNone(registry.approved_target(self.pkg, {"child": self.repo}, {}))
        self.assertIsNone(registry.approved_target({**self.pkg, "publish": False}, {"child": self.repo}, {"fixture": self.rule}))

    def test_registry_owner_entrypoint_and_retry(self):
        t = registry.approved_target(self.pkg, {"child": self.repo}, {"fixture": self.rule})
        t.update(receipt={"archive_sha256": "a"*64}, prerequisites=[])
        with patch.object(registry, "present", return_value=False) as check, \
             patch.object(registry, "owns_crate", return_value=False) as owns, \
             patch.object(registry, "gh_api") as api, patch.object(subprocess, "run") as dispatch, \
             patch.dict(os.environ, dict(CHILD_TARGET=json.dumps(t), GH_TOKEN="fixture")):
            registry.publish_missing(t)
            dispatch.assert_not_called()
            owns.return_value = True
            responses = [{"full_name": "test/child", "default_branch": "main"}, {"sha": t["sha"]}]
            api.side_effect = [*responses, {"type": "file", "sha": "unreviewed"}]
            registry.publish_missing(t)
            dispatch.assert_not_called()
            api.side_effect = [*responses, {"type": "file", "sha": t["workflow_blob"]}]
            check.side_effect = [False, True]
            registry.publish_missing(t)
            self.assertIn("source_sha=" + t["sha"], dispatch.call_args.args[0])
            check.side_effect = None
            check.return_value = True
            registry.publish_missing(t)
            dispatch.assert_called_once()
            with patch.dict(os.environ, {"GH_TOKEN": ""}), self.assertRaisesRegex(ValueError, "permission"):
                registry.dispatch()
