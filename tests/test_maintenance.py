"""Maintenance uses real isolated Git fixtures; network boundaries are mocked."""

from contextlib import redirect_stdout
from copy import deepcopy
import io
import json
import os
import shutil
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import maintenance as maintenance


def git(root, *args):
    result = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)
    if result.returncode:
        raise AssertionError(result.stderr)
    return result.stdout.strip()


class AuditBoundaries(unittest.TestCase):
    def test_registry_missing_is_distinct_from_network_failure_and_yanked(self):
        package = {"name": "zfixture", "version": "1.0.0", "repository": "zfixture"}
        body = io.BytesIO(b"missing")
        with patch.object(maintenance, "urlopen", side_effect=HTTPError("test", 404, "missing", {}, body)):
            self.assertEqual(maintenance.registry_status(package)["status"], "missing")
        self.assertTrue(body.closed)
        for error in [HTTPError("test", 503, "unavailable", {}, None), URLError("offline")]:
            with patch.object(maintenance, "urlopen", side_effect=error):
                with self.assertRaises(maintenance.MaintenanceError):
                    maintenance.registry_status(package)
        response = io.BytesIO(json.dumps({"version": {"crate": "zfixture", "num": "1.0.0", "yanked": True}}).encode())
        with patch.object(maintenance, "urlopen", return_value=response):
            self.assertEqual(maintenance.registry_status(package)["status"], "yanked")

    def test_malformed_registry_records_are_incomplete_checks(self):
        package = {"name": "zfixture", "version": "1.0.0", "repository": "zfixture"}
        for payload in [[], None, {"version": None}, {"version": []},
                        {"version": {"crate": "zfixture", "num": "1.0.0"}}]:
            with self.subTest(payload=payload):
                response = io.BytesIO(json.dumps(payload).encode())
                with patch.object(maintenance, "urlopen", return_value=response):
                    with self.assertRaises(maintenance.MaintenanceError):
                        maintenance.registry_status(package)
                self.assertTrue(response.closed)

    def test_candidates_are_owner_scoped_review_hints(self):
        def row(name, owner="owner", **values):
            return {"name": name, "owner": {"login": owner}, **values}
        rows = [row("zknown"), row("znew", language="Rust", description="Candidate"),
                row("zforeign", owner="elsewhere"), row("zfork", fork=True),
                row("zold", archived=True), row("project-runtime", topics=["project-z"]), row("unrelated")]
        candidates = maintenance.candidate_repositories(rows, [("OWNER", "zknown")], "owner")
        self.assertEqual([item["repository"] for item in candidates], ["owner/project-runtime", "owner/znew"])
        self.assertTrue(all(item["requires_semantic_review"] for item in candidates))
        self.assertEqual(maintenance.github_identity("git@github.com:Owner/znew.git"), ("Owner", "znew"))


class IsolatedApply(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="project-z-maintenance-tests-")
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.root = self.base / "root"
        self.upstream = self.base / "upstream"
        self.destination = self.base / "snapshot"
        for repository in [self.root, self.upstream]:
            repository.mkdir()
            git(repository, "init", "-b", "main")
            git(repository, "config", "user.name", "Project Z test")
            git(repository, "config", "user.email", "project-z-test@example.invalid")
        (self.upstream / "value").write_text("one\n")
        git(self.upstream, "add", "value")
        git(self.upstream, "commit", "-m", "initial library")
        self.old = git(self.upstream, "rev-parse", "HEAD")
        git(self.root, "-c", "protocol.file.allow=always", "submodule", "add", "-b", "main", str(self.upstream), "zfixture")
        (self.root / "README.md").write_text("fixture\n")
        (self.root / "catalog.json").write_text("{}\n")
        (self.root / ".cargo").mkdir()
        (self.root / ".cargo/project-z.toml").write_text("[patch.crates-io]\n")
        (self.root / "docs").mkdir()
        (self.root / "docs/PROJECTS.md").write_text("initial project map\n")
        git(self.root, "add", ".")
        git(self.root, "commit", "-m", "pin initial library")
        self.root_head = git(self.root, "rev-parse", "HEAD")
        (self.upstream / "value").write_text("two\n")
        git(self.upstream, "commit", "-am", "update library")
        self.new = git(self.upstream, "rev-parse", "HEAD")
        self.report = {"root_head": self.root_head, "errors": [],
                       "candidates": [{"repository": "owner/zunknown", "language": "Rust",
                                       "description": "Unregistered candidate"}],
                       "upstreams": [{"path": "zfixture", "url": str(self.upstream), "branch": "main",
                                      "pinned": self.old, "upstream": self.new, "changed": True}]}
        env = patch.dict(os.environ, {"GIT_ALLOW_PROTOCOL": "file"})
        env.start()
        self.addCleanup(env.stop)

    def coordinate(self, worktree):
        self.assertEqual(git(worktree / "zfixture", "rev-parse", "HEAD"), self.new)
        (worktree / "catalog.json").write_text(json.dumps({"commit": self.new}) + "\n")
        (worktree / "docs/PROJECTS.md").write_text(f"pinned {self.new}\n")
        return {"sync": "updated", "check": "passed"}

    def unchanged_source(self):
        self.assertEqual(git(self.root, "rev-parse", "HEAD"), self.root_head)
        self.assertEqual(git(self.root / "zfixture", "rev-parse", "HEAD"), self.old)

    def add_repository(self, name, *, changed=True):
        upstream = self.base / (name + "-upstream")
        upstream.mkdir()
        git(upstream, "init", "-b", "main")
        git(upstream, "config", "user.name", "Project Z test")
        git(upstream, "config", "user.email", "project-z-test@example.invalid")
        (upstream / "value").write_text("old\n")
        git(upstream, "add", ".")
        git(upstream, "commit", "-m", "initial independent repository")
        old = git(upstream, "rev-parse", "HEAD")
        git(self.root, "submodule", "add", "-b", "main", str(upstream), name)
        git(self.root, "commit", "-am", "pin independent repository")
        self.root_head = git(self.root, "rev-parse", "HEAD")
        self.report["root_head"] = self.root_head
        if changed:
            (upstream / "value").write_text("new\n")
            git(upstream, "commit", "-am", "update independent repository")
        new = git(upstream, "rev-parse", "HEAD")
        self.report["upstreams"].append({
            "path": name, "url": str(upstream), "branch": "main",
            "pinned": old, "upstream": new, "changed": changed,
        })
        return old, new

    def test_selected_update_defers_other_changes_and_default_still_updates_all(self):
        old, new = self.add_repository("zdeferred")
        before = deepcopy(self.report)
        with patch.object(maintenance, "coordinate", side_effect=self.coordinate):
            result = maintenance.apply_snapshot(
                self.root, self.report, self.destination, repositories=["zfixture"])
        self.assertEqual(result["status"], "ready", result)
        self.assertEqual(result["selected"], ["zfixture"])
        self.assertEqual(result["updated"], ["zfixture"])
        self.assertEqual(result["deferred"], ["zdeferred"])
        self.assertEqual(git(self.destination, "rev-parse", "HEAD:zfixture"), self.new)
        self.assertEqual(git(self.destination, "rev-parse", "HEAD:zdeferred"), old)
        self.assertEqual(self.report, before)
        self.unchanged_source()
        self.assertEqual(git(self.root / "zdeferred", "rev-parse", "HEAD"), old)
        self.assertEqual(git(self.root, "status", "--porcelain"), "")
        full = self.base / "full-snapshot"
        with patch.object(maintenance, "coordinate", side_effect=self.coordinate):
            result = maintenance.apply_snapshot(self.root, self.report, full)
        self.assertEqual(result["status"], "ready", result)
        self.assertEqual(set(result["updated"]), {"zfixture", "zdeferred"})
        self.assertEqual(result["deferred"], [])
        self.assertEqual(git(full, "rev-parse", "HEAD:zdeferred"), new)
        self.unchanged_source()

    def test_invalid_selection_is_rejected_even_without_upstream_changes(self):
        self.report["upstreams"][0]["changed"] = False
        for selected in ([], [""], ["zunknown"]):
            with self.subTest(selected=selected):
                with self.assertRaisesRegex(maintenance.MaintenanceError, "selection"):
                    maintenance.apply_snapshot(
                        self.root, self.report, self.destination, repositories=selected)
                self.assertFalse(self.destination.exists())
        self.unchanged_source()

    def test_selection_without_changes_keeps_deferred_work_visible(self):
        self.add_repository("zstable", changed=False)
        result = maintenance.apply_snapshot(
            self.root, self.report, self.destination, repositories=["zstable"])
        self.assertEqual(result, {"status": "no_changes", "selected": ["zstable"],
                                  "deferred": ["zfixture"]})
        self.assertFalse(self.destination.exists())
        report = {**self.report, "created_at": "2026-11-20T00:00:00Z", "snapshot": result}
        text = maintenance.markdown(report)
        self.assertIn("Selected repositories: `zstable`", text)
        self.assertIn("Deferred upstream updates: `zfixture`", text)
        self.assertIn("Upstream updates: **1**", text)
        self.unchanged_source()

    def test_cli_repeated_repository_selection_and_audit_only_rejection(self):
        old, new = self.add_repository("zsecond")
        report = {**self.report, "created_at": "2026-11-20T00:00:00Z",
                  "needs_maintenance": True}
        output = self.base / "audit.json"
        summary = self.base / "summary.md"
        args = ["--root", str(self.root), "--output", str(output), "--report", str(summary)]
        with patch.object(maintenance, "audit", return_value=report) as audit:
            with redirect_stdout(io.StringIO()):
                code = maintenance.main([*args, "--repo", "zfixture"])
            self.assertEqual(code, 2)
            audit.assert_not_called()
            self.assertIn("--repo requires --apply", output.read_text())
            with patch.object(maintenance, "coordinate", side_effect=self.coordinate):
                with redirect_stdout(io.StringIO()):
                    code = maintenance.main([
                        *args, "--apply", "--worktree", str(self.destination),
                        "--repo", "zsecond", "--repo", "zfixture", "--repo", "zfixture"])
        self.assertEqual(code, 0)
        result = json.loads(output.read_text())
        self.assertEqual(result["snapshot"]["selected"], ["zfixture", "zsecond"])
        self.assertEqual(result["snapshot"]["deferred"], [])
        self.assertTrue(result["needs_maintenance"])
        self.assertEqual(git(self.destination, "rev-parse", "HEAD:zsecond"), new)
        self.unchanged_source()

    def test_apply_pins_exact_upstream_only_in_new_worktree(self):
        original_modules = (self.root / ".gitmodules").read_bytes()
        with patch.object(maintenance, "coordinate", side_effect=self.coordinate):
            result = maintenance.apply_snapshot(self.root, self.report, self.destination)
        self.assertEqual(result["status"], "ready", result)
        self.assertEqual(git(self.destination, "rev-parse", "HEAD:zfixture"), self.new)
        self.assertEqual(git(self.destination, "show", "HEAD:docs/PROJECTS.md"), f"pinned {self.new}")
        self.assertEqual((self.destination / ".gitmodules").read_bytes(), original_modules)
        self.assertEqual(git(self.destination, "status", "--porcelain"), "")
        self.assertEqual(git(self.root, "status", "--porcelain"), "")
        self.unchanged_source()
        self.assertNotIn("zunknown", git(self.destination, "ls-tree", "--name-only", "HEAD"))

    def test_dirty_source_and_unknown_plans_are_refused_before_creation(self):
        unknown = deepcopy(self.report)
        unknown["upstreams"][0]["path"] = "zunknown"
        with self.assertRaisesRegex(maintenance.MaintenanceError, "outside .gitmodules"):
            maintenance.apply_snapshot(self.root, unknown, self.destination)
        self.assertFalse(self.destination.exists())
        (self.root / "README.md").write_text("active user edit\n")
        with self.assertRaisesRegex(maintenance.MaintenanceError, "dirty"):
            maintenance.apply_snapshot(self.root, self.report, self.destination)
        self.assertFalse(self.destination.exists())
        self.assertEqual((self.root / "README.md").read_text(), "active user edit\n")
        self.unchanged_source()

    def test_failed_dependency_gate_preserves_uncommitted_review_worktree(self):
        with patch.object(maintenance, "coordinate", side_effect=maintenance.MaintenanceError("dependency mismatch")):
            result = maintenance.apply_snapshot(self.root, self.report, self.destination)
        self.assertEqual(result["status"], "blocked")
        self.assertIn("dependency mismatch", result["error"])
        self.assertEqual(git(self.destination, "rev-parse", "HEAD"), self.root_head)
        self.assertEqual(git(self.destination / "zfixture", "rev-parse", "HEAD"), self.new)
        self.unchanged_source()

    def test_upstream_movement_requires_a_new_audit(self):
        (self.upstream / "value").write_text("three\n")
        git(self.upstream, "commit", "-am", "advance after audit")
        result = maintenance.apply_snapshot(self.root, self.report, self.destination)
        self.assertEqual(result["status"], "blocked")
        self.assertIn("moved after audit", result["error"])
        self.assertEqual(git(self.destination, "rev-parse", "HEAD"), self.root_head)
        self.unchanged_source()

    def test_submodule_path_cannot_escape_checkout(self):
        (self.root / ".gitmodules").write_text('[submodule "bad"]\npath = ../outside\nurl = ignored\n')
        with self.assertRaisesRegex(maintenance.MaintenanceError, "invalid submodule path"):
            maintenance.modules(self.root)

    def test_destination_cannot_mutate_existing_source_trees(self):
        for destination in [self.root / "zfixture/new", self.root / "unignored/new",
                            self.root / ".git/new", self.upstream / "new"]:
            with self.subTest(destination=destination):
                with self.assertRaises(maintenance.MaintenanceError):
                    maintenance.apply_snapshot(self.root, self.report, destination)
                self.assertFalse(destination.exists())
        self.unchanged_source()
        self.assertEqual(git(self.root, "status", "--porcelain"), "")

    def test_ci_audit_needs_only_committed_catalog_and_uninitialized_gitlinks(self):
        catalog = {"schema_version": 1, "packages": [], "repositories": [
            {"path": "zfixture", "url": str(self.upstream), "commit": self.old, "branch": "main"}]}
        (self.root / "catalog.json").write_text(json.dumps(catalog))
        git(self.root, "commit", "-am", "store catalog for CI")
        checkout = self.base / "ci"
        git(self.base, "clone", "--depth=1", self.root.as_uri(), str(checkout))
        self.assertFalse((checkout / "zfixture/.git").exists())
        actual_run = maintenance.run
        def only_git_and_gh(argv, root, timeout=90):
            if argv[0] == "gh":
                return "[[]]"
            self.assertEqual(argv[0], "git", "CI must not invoke Cargo or inventory")
            return actual_run(argv, root, timeout)
        with patch.object(maintenance, "run", side_effect=only_git_and_gh):
            report = maintenance.audit(checkout, owner="owner", require_catalog=True)
        self.assertEqual(report["errors"], [])
        self.assertEqual(report["upstreams"][0]["upstream"], self.new)
        self.assertFalse((checkout / "zfixture/.git").exists())

    def test_nested_url_replacement_removal_and_hidden_dirty_source(self):
        leaves = []
        for name in ("old-leaf", "new-leaf"):
            leaf = self.base / name
            leaf.mkdir()
            git(leaf, "init", "-b", "main")
            git(leaf, "config", "user.name", "Project Z test")
            git(leaf, "config", "user.email", "project-z-test@example.invalid")
            (leaf / "value").write_text(name)
            git(leaf, "add", ".")
            git(leaf, "commit", "-m", name)
            leaves.append(leaf)
        git(self.upstream, "submodule", "add", str(leaves[0]), "nested")
        git(self.upstream, "commit", "-am", "pin old nested source")
        self.old = git(self.upstream, "rev-parse", "HEAD")
        source = self.root / "zfixture"
        git(source, "fetch", "origin")
        git(source, "checkout", "--detach", self.old)
        git(source, "submodule", "update", "--init", "--recursive")
        git(self.root, "commit", "-am", "pin nested baseline")
        self.root_head = git(self.root, "rev-parse", "HEAD")
        self.report["root_head"] = self.root_head
        self.report["upstreams"][0]["pinned"] = self.old

        git(self.upstream, "config", "-f", ".gitmodules", "submodule.nested.url", str(leaves[1]))
        git(self.upstream / "nested", "remote", "set-url", "origin", str(leaves[1]))
        git(self.upstream / "nested", "fetch", "origin")
        git(self.upstream / "nested", "checkout", "--detach", git(leaves[1], "rev-parse", "HEAD"))
        git(self.upstream, "commit", "-am", "replace nested source and pin")
        self.new = git(self.upstream, "rev-parse", "HEAD")
        self.report["upstreams"][0]["upstream"] = self.new

        # Nested ignore settings must not conceal uncommitted source work.
        git(source, "config", "submodule.nested.ignore", "all")
        (source / "nested/value").write_text("active nested edit")
        with self.assertRaisesRegex(maintenance.MaintenanceError, "dirty"):
            maintenance.apply_snapshot(self.root, self.report, self.destination)
        self.assertFalse(self.destination.exists())
        (source / "nested/value").write_text("old-leaf")
        with patch.object(maintenance, "coordinate", side_effect=self.coordinate):
            result = maintenance.apply_snapshot(self.root, self.report, self.destination)
        self.assertEqual(result["status"], "ready", result)
        self.assertEqual((self.destination / "zfixture/nested/value").read_text(), "new-leaf")
        self.assertEqual(git(self.destination / "zfixture/nested", "remote", "get-url", "origin"), str(leaves[1]))

        git(self.upstream, "submodule", "deinit", "nested")
        git(self.upstream, "rm", "nested")
        git(self.upstream, "commit", "-m", "remove nested source")
        self.new = git(self.upstream, "rev-parse", "HEAD")
        self.report["upstreams"][0]["upstream"] = self.new
        removed = self.base / "removed-snapshot"
        with patch.object(maintenance, "coordinate", side_effect=self.coordinate):
            result = maintenance.apply_snapshot(self.root, self.report, removed)
        self.assertEqual(result["status"], "ready", result)
        self.assertFalse((removed / "zfixture/nested").exists())
        self.assertEqual((source / "nested/value").read_text(), "old-leaf")
        self.assertEqual(git(source / "nested", "remote", "get-url", "origin"), str(leaves[0]))
        self.unchanged_source()



import test_project_z as source_fixtures


@unittest.skipUnless(shutil.which("git") and shutil.which("cargo"), "offline resolution fixtures require Git and Cargo")
class OfflineResolutionApply(source_fixtures.GitSourceFixture):
    def setUp(self):
        super().setUp()
        source = Path(__file__).resolve().parents[1] / "scripts"
        (self.root / "scripts").mkdir()
        for name in ("project_z.py", "cargo_versions.py", "catalog_docs.py"):
            shutil.copy2(source / name, self.root / "scripts" / name)
        self.root_head = self.commit(self.root, "include coordinator")
        self.destination = self.base / "snapshot"

    def report(self):
        rows = []
        for repo in self.data["repositories"]:
            head = source_fixtures.pz.default_head(repo["url"], self.root)
            rows.append({"path": repo["path"], "url": repo["url"], "branch": head["branch"],
                         "pinned": repo["commit"], "upstream": head["commit"],
                         "changed": repo["commit"] != head["commit"] or repo["branch"] != head["branch"]})
        return {"root_head": self.root_head, "errors": [], "upstreams": rows}

    def unchanged_source(self):
        self.assertEqual(git(self.root, "rev-parse", "HEAD"), self.root_head)
        self.assertEqual(git(self.root, "status", "--porcelain"), "")
        self.assertEqual(git(self.root / "shared", "rev-parse", "HEAD"), self.shared_initial)
        self.assertEqual(git(self.root / "app", "rev-parse", "HEAD"), self.app_initial)
        self.assertFalse((self.root / ".cargo/config.toml").exists())

    def test_application_feature_resolution_failure_cannot_create_ready_snapshot(self):
        manifest = self.app / "Cargo.toml"
        manifest.write_text(manifest.read_text().replace('version = "1.0.0" }', 'version = "1.0.0", features = ["absent"] }'))
        new = self.commit(self.app, "request missing upstream feature")
        result = maintenance.apply_snapshot(self.root, self.report(), self.destination)
        self.assertEqual(result["status"], "blocked", result)
        self.assertIn("does not have that feature", result["error"])
        self.assertNotIn("commit", result)
        self.assertEqual(git(self.destination / "app", "rev-parse", "HEAD"), new)
        self.unchanged_source()

    def test_latest_library_with_unmigrated_consumer_lock_is_blocked(self):
        new = self.advance_shared()
        original = (self.root / "app/Cargo.lock").read_bytes()
        result = maintenance.apply_snapshot(self.root, self.report(), self.destination, repositories=["shared"])
        self.assertEqual(result["status"], "blocked", result)
        self.assertIn("stale internal", result["error"])
        self.assertIn(new, result["error"])
        self.assertEqual((self.destination / "app/Cargo.lock").read_bytes(), original)
        self.assertNotIn("commit", result)
        self.unchanged_source()

    def test_updated_consumer_and_library_are_committed_with_actual_locked_resolution(self):
        self.advance_shared()
        self.cargo(self.app, "update", "-p", "tiny-core")
        new = self.commit(self.app, "refresh internal Git lock")
        result = maintenance.apply_snapshot(self.root, self.report(), self.destination)
        self.assertEqual(result["status"], "ready", result)
        self.assertIn("locked Git sources resolved in 2 repositories", result["validation"]["resolve"])
        self.assertEqual(git(self.destination / "app", "rev-parse", "HEAD"), new)
        self.assertEqual(git(self.destination, "status", "--porcelain"), "")
        self.unchanged_source()

    def test_default_branch_rename_is_recorded_without_editing_source(self):
        self.git(self.shared, "branch", "-m", "main", "development")
        result = maintenance.apply_snapshot(self.root, self.report(), self.destination)
        self.assertEqual(result["status"], "ready", result)
        current = json.loads((self.destination / "catalog.json").read_text())
        repo = next(item for item in current["repositories"] if item["name"] == "shared")
        self.assertEqual(repo["branch"], "development")
        self.assertEqual(repo["commit"], self.shared_initial)
        self.unchanged_source()


if __name__ == "__main__":
    unittest.main()
