"""Real-Git regressions for recursively verified source checkouts.

The repositories and submodule clone URLs are local temporary paths. Explicit
source_links supply the canonical relationships, so no network or Cargo process
is needed to exercise the production checkout/source-link gates.
"""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "project_z_recursive_sources", PROJECT_ROOT / "scripts" / "project_z.py"
)
assert SPEC is not None and SPEC.loader is not None
project_z = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = project_z
# project_z imports sibling helpers such as cargo_semver and catalog_docs.
# Add their directory only while importing this isolated module instance.
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
try:
    SPEC.loader.exec_module(project_z)
finally:
    sys.path.remove(str(PROJECT_ROOT / "scripts"))


class RecursiveSourceCheckoutTests(unittest.TestCase):
    """A -> B -> C -> D, with a separate canonical checkout for each source."""

    MODULE_NAME = "registered.source"

    def setUp(self):
        # Isolate Git configuration in this test process, not in the user's
        # global files. Keep normal process variables such as PATH and HOME.
        isolated_env = {
            key: value for key, value in os.environ.items()
            if not key.startswith("GIT_")
        }
        isolated_env.update({
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_ALLOW_PROTOCOL": "file",
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_AUTHOR_NAME": "Project Z fixture",
            "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
            "GIT_COMMITTER_NAME": "Project Z fixture",
            "GIT_COMMITTER_EMAIL": "fixture@example.invalid",
            "LC_ALL": "C",
        })
        env_patch = mock.patch.dict(os.environ, isolated_env, clear=True)
        env_patch.start()
        self.addCleanup(env_patch.stop)

        temp = tempfile.TemporaryDirectory(prefix="project z recursive sources ")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)

        leaf = self._create_repo("D")
        self.old_leaf_head = self.git(leaf, "rev-parse", "HEAD")
        (leaf / "tracked.txt").write_text("D current\n")
        self.git(leaf, "commit", "--quiet", "-am", "update leaf")
        self._create_repo("C", "D")
        self._create_repo("B", "C")
        self._create_repo("A", "B")

        self.data = {"repositories": [
            {
                "name": name,
                "path": name,
                "url": f"https://github.com/project-z-fixture/{name}.git",
                "commit": self.git(self.root / name, "rev-parse", "HEAD"),
                "branch": "main",
                "role": "library",
                "manifests": [],
                "requires": [],
            }
            for name in "ABCD"
        ]}
        self.rules = {"repositories": {
            owner: {"source_links": {"nested": target}}
            for owner, target in zip("ABC", "BCD")
        }}
        self.deep_parent = self.root / "A" / "nested" / "nested"
        self.deep_leaf = self.deep_parent / "nested"
        # This local setting is the regression: ordinary status at A or its
        # direct B copy does not expose a change below this ignored gitlink.
        self.git(self.deep_parent, "config", f"submodule.{self.MODULE_NAME}.ignore", "all")

    def git(self, cwd, *args):
        result = subprocess.run(
            ["git", "-c", "protocol.file.allow=always",
             "-c", f"core.hooksPath={os.devnull}", *args],
            cwd=cwd,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode:
            self.fail(
                f"fixture git command failed ({result.returncode}): {args!r}\n"
                f"{result.stdout}\n{result.stderr}"
            )
        return result.stdout.strip()

    def _create_repo(self, name, target=None):
        path = self.root / name
        path.mkdir()
        self.git(path, "init", "--quiet", "--initial-branch=main")
        (path / "tracked.txt").write_text(name + "\n")
        self.git(path, "add", "tracked.txt")
        self.git(path, "commit", "--quiet", "-m", "initial source")
        if target is not None:
            self.git(
                path, "submodule", "add", "--quiet", "--name", self.MODULE_NAME,
                str(self.root / target), "nested",
            )
            self.git(
                path, "submodule", "update", "--init", "--recursive", "--quiet"
            )
            self.git(path, "add", ".gitmodules", "nested")
            self.git(path, "commit", "--quiet", "-m", "record nested source")
        return path

    def _assert_both_gates_reject(self):
        for name, gate in (
            ("checkout_errors", lambda: project_z.checkout_errors(self.data, self.root)),
            ("source_link_errors", lambda: project_z.source_link_errors(
                self.data, self.rules, self.root
            )),
        ):
            with self.subTest(gate=name):
                errors = gate()
                self.assertTrue(
                    errors,
                    f"{name} accepted a changed/uninitialized third-level source",
                )

    def _source_state(self):
        """Record every fixture checkout's HEAD and actual tracked text."""
        result = {}
        for name, depth in (("A", 3), ("B", 2), ("C", 1), ("D", 0)):
            checkout = self.root / name
            for _ in range(depth + 1):
                result[str(checkout.relative_to(self.root))] = {
                    "head": self.git(checkout, "rev-parse", "HEAD"),
                    "tracked": (checkout / "tracked.txt").read_bytes(),
                }
                checkout = checkout / "nested"
        return result

    def test_clean_recursive_sources_pass(self):
        self.assertEqual(project_z.checkout_errors(self.data, self.root), [])
        self.assertEqual(
            project_z.source_link_errors(self.data, self.rules, self.root), []
        )

    def test_deep_tracked_edit_is_rejected_despite_ignore_all(self):
        (self.deep_leaf / "tracked.txt").write_text("uncommitted edit\n")
        self._assert_both_gates_reject()

    def test_deep_untracked_file_is_rejected_despite_ignore_all(self):
        (self.deep_leaf / "untracked.txt").write_text("uncommitted source\n")
        self._assert_both_gates_reject()

    def test_deep_old_head_is_rejected_despite_ignore_all(self):
        self.git(self.deep_leaf, "checkout", "--detach", self.old_leaf_head)
        self.assertNotEqual(
            self.git(self.deep_leaf, "rev-parse", "HEAD"),
            self.data["repositories"][-1]["commit"],
        )
        self._assert_both_gates_reject()

    def test_deep_uninitialized_source_is_rejected_despite_ignore_all(self):
        self.git(self.deep_parent, "submodule", "deinit", "--force", "--", "nested")
        self.assertFalse((self.deep_leaf / ".git").exists())
        self._assert_both_gates_reject()

    def test_sync_rejects_deep_edit_before_any_source_mutation(self):
        (self.deep_leaf / "tracked.txt").write_text("preserve this edit\n")
        before = self._source_state()
        commands = []
        original_command = project_z.command

        def traced_command(argv, *args, **kwargs):
            commands.append(tuple(argv))
            git_commands = set(argv[1:]) if argv and argv[0] == "git" else set()
            forbidden = {
                "fetch", "checkout", "switch", "reset", "read-tree",
                "update-index", "update-ref", "symbolic-ref",
            }
            if git_commands & forbidden or (
                "submodule" in git_commands and git_commands & {"update", "sync"}
            ):
                self.fail(f"sync mutated a source before rejecting its deep edit: {argv!r}")
            return original_command(argv, *args, **kwargs)

        heads = {
            repo["name"]: {"branch": "main", "commit": repo["commit"]}
            for repo in self.data["repositories"]
        }
        with (
            mock.patch.object(project_z, "repositories", return_value=self.data["repositories"]),
            mock.patch.object(project_z, "latest_heads", return_value=heads),
            mock.patch.object(project_z, "command", side_effect=traced_command),
        ):
            with self.assertRaises(project_z.CoordinationError):
                project_z.sync_sources(self.root)

        self.assertTrue(commands, "sync did not inspect any source checkout")
        self.assertEqual(self._source_state(), before)

    def _sync_local_sources(self, relocated=None):
        relocated = {} if relocated is None else relocated
        repositories = [
            {**repo, "path": relocated.get(repo["name"], repo["path"]),
             "url": str(self.root / repo["path"])}
            for repo in self.data["repositories"]
        ]
        heads = {
            repo["name"]: {"branch": "main", "commit": repo["commit"]}
            for repo in repositories
        }
        with (
            mock.patch.object(project_z, "repositories", return_value=repositories),
            mock.patch.object(project_z, "latest_heads", return_value=heads),
            mock.patch.object(project_z, "policy", return_value=self.rules),
        ):
            project_z.sync_sources(self.root)

    def test_sync_initializes_empty_deep_source_with_local_git(self):
        before = self._source_state()
        self.git(self.deep_parent, "submodule", "deinit", "--force", "--", "nested")
        self.assertFalse((self.deep_leaf / ".git").exists())
        self.assertEqual(list(self.deep_leaf.iterdir()), [])

        with mock.patch.object(project_z, "command", wraps=project_z.command) as commands:
            self._sync_local_sources()

        actual_commands = [call.args[0] for call in commands.call_args_list]
        self.assertTrue(any(argv[:2] == ["git", "fetch"] for argv in actual_commands))
        self.assertTrue(any(
            argv[:3] == ["git", "submodule", "update"] for argv in actual_commands
        ))
        self.assertTrue((self.deep_leaf / ".git").exists())
        self.assertEqual(
            self.git(self.deep_leaf, "rev-parse", "HEAD"),
            self.data["repositories"][-1]["commit"],
        )
        self.assertEqual((self.deep_leaf / "tracked.txt").read_text(), "D current\n")
        self.assertEqual(self._source_state(), before)
        self.assertEqual(project_z.checkout_errors(self.data, self.root), [])

    def test_missing_owned_checkout_passes_preflight_without_rewriting_metadata(self):
        module = Path(self.git(self.deep_leaf, "rev-parse", "--absolute-git-dir"))
        self.git(self.deep_parent, "submodule", "deinit", "--force", "--", "nested")
        self.deep_leaf.rmdir()
        config = module / "config"
        before = config.read_bytes()
        self.assertEqual(project_z.checkout_errors(
            {"repositories": [{"path": "nested", "commit": self.data["repositories"][-1]["commit"]}]},
            self.deep_parent, allow_uninitialized=True,
        ), [])
        self.assertEqual(config.read_bytes(), before)
        self.assertFalse(self.deep_leaf.exists())

    def _assert_foreign_metadata_rejected(self, *, owner_exists, checkout_exists, relative_owner):
        module = Path(self.git(self.deep_leaf, "rev-parse", "--absolute-git-dir"))
        owner = self.root / "foreign leaf"
        self.deep_leaf.rename(owner)
        if checkout_exists:
            self.deep_leaf.mkdir()
        (owner / ".git").write_text(f"gitdir: {module}\n", encoding="utf-8")
        if not owner_exists:
            shutil.rmtree(owner)
        owner_value = os.path.relpath(owner, module) if relative_owner else str(owner)
        config = module / "config"
        self.git(
            self.deep_parent, "config", "--file", str(config),
            "core.worktree", owner_value,
        )
        before = config.read_bytes()

        def foreign_state():
            if not owner_exists:
                return None
            return {
                "head": self.git(owner, "rev-parse", "HEAD"),
                "toplevel": self.git(owner, "rev-parse", "--show-toplevel"),
                "status": self.git(owner, "status", "--porcelain"),
                "tracked": (owner / "tracked.txt").read_bytes(),
            }

        original_owner = foreign_state()
        # Exercise the top-level entry too: its parent is the supplied root,
        # while sync below reaches the same path through recursive gitlinks.
        errors = project_z.checkout_errors(
            {"repositories": [{"path": "nested", "commit": self.data["repositories"][-1]["commit"]}]},
            self.deep_parent, allow_uninitialized=True,
        )
        self.assertTrue(errors, "preflight accepted retained metadata belonging to another checkout")
        self.assertIn("retained submodule metadata", "\n".join(errors))
        self.assertIn(str(owner), "\n".join(errors))
        self.assertIn(str(self.deep_leaf), "\n".join(errors))

        commands = []
        original_command = project_z.command

        def traced_command(argv, *args, **kwargs):
            commands.append(tuple(argv))
            git_commands = set(argv[1:]) if argv and argv[0] == "git" else set()
            forbidden = {
                "clone", "fetch", "checkout", "switch", "reset", "read-tree",
                "update-index", "update-ref", "symbolic-ref",
            }
            if git_commands & forbidden or (
                "submodule" in git_commands and git_commands & {"init", "update", "sync"}
            ):
                self.fail(f"sync mutated a source before rejecting foreign metadata: {argv!r}")
            return original_command(argv, *args, **kwargs)

        with mock.patch.object(project_z, "command", side_effect=traced_command):
            with self.assertRaisesRegex(project_z.CoordinationError, "retained submodule metadata"):
                self._sync_local_sources()

        self.assertTrue(commands, "sync did not inspect any source checkout")
        self.assertEqual(config.read_bytes(), before)
        self.assertEqual(foreign_state(), original_owner)
        self.assertEqual(owner.exists(), owner_exists)
        self.assertEqual(self.deep_leaf.exists(), checkout_exists)
        if checkout_exists:
            self.assertEqual(list(self.deep_leaf.iterdir()), [])

    def test_sync_rejects_retained_metadata_for_existing_foreign_checkout(self):
        self._assert_foreign_metadata_rejected(
            owner_exists=True, checkout_exists=True, relative_owner=True,
        )

    def test_sync_rejects_retained_metadata_for_missing_foreign_checkout(self):
        self._assert_foreign_metadata_rejected(
            owner_exists=False, checkout_exists=True, relative_owner=False,
        )

    def test_sync_rejects_foreign_metadata_when_checkout_path_is_missing(self):
        self._assert_foreign_metadata_rejected(
            owner_exists=True, checkout_exists=False, relative_owner=False,
        )

    def test_sync_rejects_missing_foreign_target_when_checkout_path_is_missing(self):
        self._assert_foreign_metadata_rejected(
            owner_exists=False, checkout_exists=False, relative_owner=True,
        )

    def _assert_isolated_sync(self, *, linked):
        before = self._source_state()
        original_module = Path(self.git(self.deep_leaf, "rev-parse", "--absolute-git-dir"))
        original_config = (original_module / "config").read_bytes()
        isolated = self.root / ("A-linked" if linked else "A-fresh")
        if linked:
            self.git(self.root / "A", "worktree", "add", "--detach", str(isolated), "HEAD")
        else:
            self.git(
                self.root, "clone", "--quiet", "--no-recurse-submodules",
                str(self.root / "A"), str(isolated),
            )
        retained = Path(self.git(
            isolated, "rev-parse", "--path-format=absolute", "--git-path",
            f"modules/{self.MODULE_NAME}",
        ))
        self.assertFalse(retained.exists())

        self._sync_local_sources({"A": isolated.name})

        leaf = isolated / "nested" / "nested" / "nested"
        isolated_module = Path(self.git(leaf, "rev-parse", "--absolute-git-dir"))
        self.assertNotEqual(isolated_module, original_module)
        self.assertEqual((original_module / "config").read_bytes(), original_config)
        self.assertEqual(self.git(leaf, "rev-parse", "HEAD"), self.git(self.deep_leaf, "rev-parse", "HEAD"))
        self.assertEqual(Path(self.git(leaf, "rev-parse", "--show-toplevel")), leaf)
        self.assertEqual(self._source_state(), before)
        self.assertEqual(
            Path(self.git(isolated / "nested", "rev-parse", "--absolute-git-dir")),
            retained,
        )

    def test_sync_initializes_plain_clone_with_independent_nested_metadata(self):
        self._assert_isolated_sync(linked=False)

    def test_sync_initializes_linked_worktree_with_independent_nested_metadata(self):
        self._assert_isolated_sync(linked=True)

    def test_sync_preserves_user_file_in_uninitialized_deep_source(self):
        self.git(self.deep_parent, "submodule", "deinit", "--force", "--", "nested")
        user_file = self.deep_leaf / "keep-user-work.txt"
        user_file.write_text("preserve this user file\n")
        before_heads = {
            repo["name"]: self.git(self.root / repo["path"], "rev-parse", "HEAD")
            for repo in self.data["repositories"]
        }
        commands = []
        original_command = project_z.command

        def traced_command(argv, *args, **kwargs):
            commands.append(tuple(argv))
            git_commands = set(argv[1:]) if argv and argv[0] == "git" else set()
            forbidden = {
                "fetch", "checkout", "switch", "reset", "read-tree",
                "update-index", "update-ref", "symbolic-ref",
            }
            if git_commands & forbidden or (
                "submodule" in git_commands and git_commands & {"update", "sync"}
            ):
                self.fail(f"sync mutated a source containing a user file: {argv!r}")
            return original_command(argv, *args, **kwargs)

        with mock.patch.object(project_z, "command", side_effect=traced_command):
            with self.assertRaises(project_z.CoordinationError):
                self._sync_local_sources()

        self.assertTrue(commands, "sync did not inspect any source checkout")
        self.assertEqual(user_file.read_text(), "preserve this user file\n")
        self.assertEqual(list(self.deep_leaf.iterdir()), [user_file])
        self.assertFalse((self.deep_leaf / ".git").exists())
        self.assertEqual({
            repo["name"]: self.git(self.root / repo["path"], "rev-parse", "HEAD")
            for repo in self.data["repositories"]
        }, before_heads)


if __name__ == "__main__":
    unittest.main()
