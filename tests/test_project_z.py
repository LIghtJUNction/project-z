"""Coordination invariants independent of the installed Cargo toolchain."""

from contextlib import redirect_stderr, redirect_stdout
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import tomllib
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import project_z as pz


def dependency(name, *, kind="normal", path=None, requirement="^1", explicit=True):
    return {
        "name": name, "alias": None, "kind": kind, "target": None,
        "optional": False, "default_features": True, "features": [],
        "source": None if path else "registry+https://github.com/rust-lang/crates.io-index",
        "path": path, "requirement": requirement, "explicit_version": explicit,
    }


def package(name, *, repo=None, deps=(), version="1.0.0", manifest=None, publish=True):
    repo = repo or name
    return {
        "name": name, "version": version, "repository": repo,
        "manifest": manifest or f"{repo}/Cargo.toml", "workspace": repo,
        "publish": publish, "rust_version": "1.85", "library": True,
        "features": {}, "dependencies": list(deps),
    }


def catalog(*packages):
    names = sorted({item["repository"] for item in packages})
    return {
        "schema_version": 1,
        "repositories": [
            {"name": name, "path": name, "url": f"https://example.invalid/{name}.git",
             "branch": "main", "commit": "0" * 40, "role": "library", "manifests": ["Cargo.toml"]}
            for name in names
        ],
        "packages": list(packages),
    }


class FilesystemFixture(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="project-z-tests-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def write(self, path, content):
        destination = self.root / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")
        return destination

    def generated(self, data):
        for path, content in pz.generated(data).items():
            self.write(path, content)


class DependencyGraphTests(unittest.TestCase):
    def test_dependencies_and_build_tools_precede_consumers(self):
        data = catalog(
            package("frontend", deps=[dependency("runtime"), dependency("generator", kind="build")]),
            package("runtime", deps=[dependency("kernel")]),
            package("kernel"), package("generator"),
        )
        result = pz.ordered(pz.dependency_graph(data))
        self.assertEqual(set(result), {"frontend", "runtime", "kernel", "generator"})
        positions = {name: i for i, name in enumerate(result)}
        for upstream, downstream in [("kernel", "runtime"), ("runtime", "frontend"), ("generator", "frontend")]:
            self.assertLess(positions[upstream], positions[downstream])

    def test_normal_cycles_fail_but_dev_cycles_do_not_block_release_order(self):
        normal = catalog(package("a", deps=[dependency("b")]), package("b", deps=[dependency("a")]))
        with self.assertRaisesRegex(pz.CoordinationError, "cycle"):
            pz.ordered(pz.dependency_graph(normal))
        development = catalog(package("a", deps=[dependency("b", kind="dev")]), package("b", deps=[dependency("a")]))
        self.assertEqual(pz.ordered(pz.dependency_graph(development)), ["a", "b"])
        self.assertEqual(set(pz.impact(development, ["b"])), {"a", "b"})

    def test_impact_includes_transitive_and_development_consumers(self):
        data = catalog(
            package("core"), package("runtime", deps=[dependency("core")]),
            package("app", deps=[dependency("runtime")]),
            package("comparison", deps=[dependency("core", kind="dev")]),
            package("unrelated"),
        )
        self.assertEqual(set(pz.impact(data, ["core"])), {"core", "runtime", "app", "comparison"})
        self.assertEqual(pz.impact(data, ["app"]), ["app"])
        with self.assertRaisesRegex(pz.CoordinationError, "unknown"):
            pz.impact(data, ["missing"])

    def test_repository_impact_seeds_all_its_packages(self):
        data = catalog(
            package("codec", repo="protocols", manifest="protocols/codec/Cargo.toml"),
            package("transport", repo="protocols", manifest="protocols/transport/Cargo.toml"),
            package("app", deps=[dependency("codec")]),
        )
        self.assertEqual(set(pz.impact(data, ["protocols"])), {"codec", "transport", "app"})

    def test_dependency_alias_does_not_change_package_identity(self):
        dep = dependency("kernel")
        dep["alias"] = "renamed_kernel"
        data = catalog(package("kernel"), package("app", deps=[dep]))
        self.assertEqual(pz.dependency_graph(data)["app"], {"kernel"})

    def test_two_distinct_manifests_cannot_supply_one_package_name(self):
        data = catalog(package("core", repo="one"), package("core", repo="two"))
        with self.assertRaisesRegex(pz.CoordinationError, "duplicate package core"):
            pz.package_map(data)

    def test_runtime_and_installer_consumers_join_package_impact(self):
        data = catalog(package("core"), package("daemon", deps=[dependency("core")]), package("gui"))
        next(repo for repo in data["repositories"] if repo["name"] == "gui")["requires"] = ["daemon"]
        data["repositories"].append({"name": "installer", "requires": ["gui"], "manifests": []})
        self.assertEqual(pz.impact(data, ["core"]), ["core", "daemon"])
        self.assertEqual(pz.repository_impact(data, ["core"]), ["core", "daemon", "gui", "installer"])
        self.assertEqual({repo["name"] for repo in pz.selected_repositories(data, ["core"], True)},
                         {"core", "daemon", "gui"})
        self.assertEqual(pz.repository_impact(data, ["installer"]), ["installer"])

    def test_missing_runtime_repository_is_not_silently_ignored(self):
        data = catalog(package("gui"))
        data["repositories"][0]["requires"] = ["missing-daemon"]
        self.assertTrue(any("unknown required repositories missing-daemon" in error
                            for error in pz.validate(data, {})))


class InventoryTests(FilesystemFixture):
    def test_multiple_manifests_of_one_workspace_do_not_duplicate_members(self):
        repo = {"name": "suite", "path": "suite", "manifests": ["Cargo.toml", "crates/core/Cargo.toml"]}
        cargo_package = {
            "id": "path+file:///fixture/suite/crates/core#core@1.0.0", "name": "core", "version": "1.0.0",
            "manifest_path": str(self.root / "suite/crates/core/Cargo.toml"),
            "dependencies": [], "publish": None, "rust_version": "1.85", "features": {},
            "targets": [{"kind": ["lib"]}],
        }
        metadata = {"workspace_members": [cargo_package["id"]], "packages": [cargo_package],
                    "workspace_root": str(self.root / "suite")}
        with patch.object(pz, "repositories", return_value=[repo]), patch.object(pz, "metadata", return_value=metadata):
            result = pz.inventory(self.root)
        self.assertEqual(len(result["packages"]), 1)
        self.assertEqual(result["packages"][0]["manifest"], "suite/crates/core/Cargo.toml")
        self.assertEqual(set(pz.package_map(result)), {"core"})

    def test_generated_patch_covers_publishable_package_names_and_paths(self):
        data = catalog(
            package("core", repo="suite", manifest="suite/crates/core/Cargo.toml"),
            package("private-tool", repo="suite", manifest="suite/tools/Cargo.toml", publish=False),
        )
        parsed = tomllib.loads(pz.patch_text(data))["patch"]["crates-io"]
        self.assertEqual(parsed, {"core": {"path": "suite/crates/core"}})

    def test_project_documentation_uses_pinned_manifests_and_runtime_dependencies(self):
        data = catalog(package("core", repo="suite", manifest="suite/crates/core/Cargo.toml"),
                       package("desktop", deps=[dependency("core")]))
        next(repo for repo in data["repositories"] if repo["name"] == "desktop")["requires"] = ["service"]
        document = pz.generated(data)[pz.PROJECTS]
        self.assertIn("https://example.invalid/suite/blob/" + "0" * 40 + "/crates/core/Cargo.toml", document)
        self.assertIn("service, suite", document)
        self.assertIn("注册表是否已发布", document)


class LockfileTransactionTests(FilesystemFixture):
    def setUp(self):
        super().setUp()
        self.data = catalog(package("core", repo="suite", manifest="suite/crates/core/Cargo.toml"))
        self.repo = self.data["repositories"][0]
        self.repo["manifests"] = ["crates/core/Cargo.toml"]
        self.write("suite/crates/core/Cargo.toml", "[package]\nname = 'core'\nversion = '1.0.0'\n")

    def test_member_workspace_restores_existing_dirty_bytes_and_permissions(self):
        lock = self.write("suite/Cargo.lock", "user's existing edits\r\n")
        lock.chmod(0o640)
        original, mode = lock.read_bytes(), lock.stat().st_mode
        with pz.preserved_workspace_locks(self.data, self.repo, self.root):
            lock.write_bytes(b"Cargo's patched resolution\n")
            lock.chmod(0o600)
        self.assertEqual(lock.read_bytes(), original)
        self.assertEqual(lock.stat().st_mode, mode)
        self.assertFalse(list(lock.parent.glob(".Cargo.lock.project-z-*")))

    def test_new_lock_is_removed_even_when_metadata_fails(self):
        lock = self.root / "suite/Cargo.lock"
        with self.assertRaisesRegex(pz.CoordinationError, "metadata failed"):
            with pz.preserved_workspace_locks(self.data, self.repo, self.root):
                lock.write_text("generated\n")
                raise pz.CoordinationError("metadata failed")
        self.assertFalse(lock.exists())

    def test_existing_lock_is_restored_when_metadata_fails(self):
        lock = self.write("suite/Cargo.lock", "original\n")
        with self.assertRaisesRegex(pz.CoordinationError, "metadata failed"):
            with pz.preserved_workspace_locks(self.data, self.repo, self.root):
                lock.unlink()
                raise pz.CoordinationError("metadata failed")
        self.assertEqual(lock.read_text(), "original\n")

    def test_restore_error_preserves_original_and_restores_other_workspaces(self):
        first = self.write("suite/a/Cargo.lock", "first user's existing edits\r\n")
        second = self.write("suite/b/Cargo.lock", "second user's existing edits\r\n")
        target = self.write("elsewhere.lock", "another writer's file\n")
        first.chmod(0o640)
        second.chmod(0o600)
        original_first, first_mode = first.read_bytes(), first.stat().st_mode
        original_second, second_mode = second.read_bytes(), second.stat().st_mode
        probe = self.root / "symlink-probe"
        try:
            probe.symlink_to(target)
            probe.unlink()
        except OSError as error:
            self.skipTest(f"symlinks unavailable: {error}")
        data = catalog(
            package("first", repo="suite", manifest="suite/a/Cargo.toml"),
            package("second", repo="suite", manifest="suite/b/Cargo.toml"),
        )
        for item, workspace in zip(data["packages"], ["suite/a", "suite/b"]):
            item["workspace"] = workspace

        with self.assertRaises(pz.CoordinationError) as failure:
            with pz.preserved_workspace_locks(data, data["repositories"][0], self.root):
                first.unlink()
                first.symlink_to(target)
                second.write_bytes(b"temporary Cargo resolution\n")
                second.chmod(0o644)

        self.assertTrue(first.is_symlink())
        self.assertEqual(target.read_text(), "another writer's file\n")
        self.assertEqual(second.read_bytes(), original_second)
        self.assertEqual(second.stat().st_mode, second_mode)
        backups = list(first.parent.glob(".Cargo.lock.project-z-*"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_bytes(), original_first)
        self.assertEqual(backups[0].stat().st_mode, first_mode)
        self.assertIn("lockfile must be a regular file", str(failure.exception))
        self.assertIn(str(backups[0]), str(failure.exception))

    def test_lock_symlink_is_refused_without_touching_its_target(self):
        target = self.write("elsewhere.lock", "preserve\n")
        lock = self.root / "suite/Cargo.lock"
        try:
            lock.symlink_to(target)
        except OSError:
            self.skipTest("symlinks unavailable")
        with self.assertRaises(pz.CoordinationError):
            with pz.preserved_workspace_locks(self.data, self.repo, self.root):
                self.fail("must refuse before invoking Cargo")
        self.assertEqual(target.read_text(), "preserve\n")


class VersionDeclarationTests(FilesystemFixture):
    def test_path_only_prerelease_is_accepted_but_explicit_star_is_checked(self):
        manifest = self.write("app/Cargo.toml", '[dependencies]\ncore = { path = "../core" }\n')
        declaration = {"name": "core", "rename": None, "kind": None, "target": None}
        explicit = pz.explicit_version(manifest, self.root / "app", declaration)
        self.assertFalse(explicit)
        data = catalog(package("core", version="0.1.0-alpha.1"), package("app", deps=[
            dependency("core", path="core", requirement="*", explicit=explicit)]))
        self.assertEqual(pz.validate(data, {}, self.root), [])
        manifest.write_text('[dependencies]\ncore = { path = "../core", version = "*" }\n')
        self.assertTrue(pz.explicit_version(manifest, self.root / "app", declaration))
        data["packages"][1]["dependencies"][0]["explicit_version"] = True
        self.assertTrue(any("requires core" in error for error in pz.validate(data, {}, self.root)))

    def test_workspace_inherited_alias_retains_explicit_version_information(self):
        manifest = self.write("app/Cargo.toml", '[dependencies]\nengine = { workspace = true }\n')
        workspace = self.write("Cargo.toml", '[workspace.dependencies]\nengine = { package = "core", path = "core" }\n')
        declaration = {"name": "core", "rename": "engine", "kind": None, "target": None}
        self.assertFalse(pz.explicit_version(manifest, self.root, declaration))
        workspace.write_text('[workspace.dependencies]\nengine = { package = "core", path = "core", version = "=0.1.0-alpha.1" }\n')
        self.assertTrue(pz.explicit_version(manifest, self.root, declaration))

    def test_cargo_normalized_cfg_spacing_keeps_path_version_constraint(self):
        manifest = self.write("app/Cargo.toml", '''[target.'cfg(target_os="linux")'.dependencies]
core = { path = "../core", version = "=1.0.0" }
''')
        declaration = {"name": "core", "rename": None, "kind": None, "target": 'cfg(target_os = "linux")'}
        self.assertTrue(pz.explicit_version(manifest, self.root / "app", declaration))

    def test_cfg_normalization_preserves_spaces_inside_string_values(self):
        manifest = self.write("app/Cargo.toml", '''[target.'cfg(custom="a b")'.dependencies]
core = { path = "../core", version = "=1.0.0" }
[target.'cfg(custom="ab")'.dependencies]
core = { path = "../core" }
''')
        declaration = {"name": "core", "rename": None, "kind": None, "target": 'cfg(custom = "ab")'}
        self.assertFalse(pz.explicit_version(manifest, self.root / "app", declaration))
        declaration["target"] = 'cfg(custom = "a b")'
        self.assertTrue(pz.explicit_version(manifest, self.root / "app", declaration))


class LocalConfigTests(FilesystemFixture):
    def setUp(self):
        super().setUp()
        self.content = '[patch.crates-io]\ncore = { path = "core" }\n'
        self.write(pz.PATCH, self.content)
        self.config = self.root / ".cargo/config.toml"

    def test_owned_configuration_is_removed_after_failure(self):
        with self.assertRaisesRegex(RuntimeError, "command failed"):
            with pz.local_config(self.root):
                self.assertEqual(self.config.read_text(), self.content)
                raise RuntimeError("command failed")
        self.assertFalse(self.config.exists())

    def test_preexisting_matching_configuration_is_preserved(self):
        self.config.write_text(self.content)
        with pz.local_config(self.root):
            pass
        self.assertEqual(self.config.read_text(), self.content)

    def test_other_configuration_is_never_overwritten(self):
        original = '[build]\njobs = 2\n'
        self.config.write_text(original)
        with self.assertRaises(pz.CoordinationError):
            with pz.local_config(self.root):
                self.fail("conflicting configuration must not be entered")
        self.assertEqual(self.config.read_text(), original)

    def test_configuration_changed_during_command_is_not_deleted(self):
        changed = '[build]\njobs = 3\n'
        with pz.local_config(self.root):
            self.config.write_text(changed)
        self.assertEqual(self.config.read_text(), changed)

    def test_workspace_override_is_temporary_and_does_not_rewrite_generated_patch(self):
        override = '[patch.crates-io]\ncore = { path = "app/vendor/core" }\n'
        with self.assertRaisesRegex(RuntimeError, "fixture failed"):
            with pz.local_config(self.root, content=override):
                self.assertEqual(self.config.read_text(), override)
                self.assertEqual((self.root / pz.PATCH).read_text(), self.content)
                raise RuntimeError("fixture failed")
        self.assertFalse(self.config.exists())
        self.assertEqual((self.root / pz.PATCH).read_text(), self.content)

    def test_workspace_override_preserves_a_preexisting_canonical_configuration(self):
        self.config.write_text(self.content)
        override = '[patch.crates-io]\ncore = { path = "app/vendor/core" }\n'
        with self.assertRaises(pz.CoordinationError):
            with pz.local_config(self.root, content=override):
                self.fail("a caller-owned configuration must not be replaced")
        self.assertEqual(self.config.read_text(), self.content)


class PathBoundaryTests(FilesystemFixture):
    def test_relative_path_normalizes_internal_parent_components(self):
        self.assertEqual(pz.relative(self.root / "core/nested/../Cargo.toml", self.root), "core/Cargo.toml")
        with self.assertRaisesRegex(pz.CoordinationError, "escapes"):
            pz.relative(self.root.parent / "outside/Cargo.toml", self.root)

    def test_repository_symlink_cannot_escape_coordination_root(self):
        outside = tempfile.TemporaryDirectory(prefix="project-z-outside-")
        self.addCleanup(outside.cleanup)
        target = Path(outside.name)
        (target / ".git").mkdir()
        try:
            (self.root / "linked").symlink_to(target, target_is_directory=True)
        except OSError as error:
            self.skipTest(f"symlinks unavailable: {error}")
        self.write(".gitmodules", '[submodule "linked"]\npath = linked\nurl = https://example.invalid/linked.git\n')
        with patch.object(pz, "command", return_value="0" * 40), self.assertRaises(pz.CoordinationError):
            pz.repositories(self.root)

    def test_configured_manifest_cannot_borrow_another_repository(self):
        self.write("one/Cargo.toml", "[workspace]\n")
        self.write("two/Cargo.toml", "[workspace]\n")
        repo = {"name": "one", "path": "one"}
        with patch.object(pz, "command", return_value="{}") as invoke:
            with self.assertRaises(pz.CoordinationError):
                pz.metadata(repo, "../two/Cargo.toml", self.root)
            invoke.assert_not_called()


class CliTests(FilesystemFixture):
    def cargo_result(self, packages, *, returncode=0, stderr=""):
        return SimpleNamespace(returncode=returncode, stdout=json.dumps({"packages": packages}), stderr=stderr)

    def test_resolve_all_detects_an_application_using_an_external_core(self):
        data = catalog(package("core"), package("app", deps=[dependency("core")]))
        next(repo for repo in data["repositories"] if repo["name"] == "app")["role"] = "application"
        self.generated(data)
        self.write("core/Cargo.toml", '[package]\nname = "core"\nversion = "1.0.0"\n')
        self.write("outside/core/Cargo.toml", '[package]\nname = "core"\nversion = "1.0.0"\n')

        def metadata(repo, *_args, **_kwargs):
            directory = "outside/core" if repo["name"] == "app" else "core"
            return {"packages": [{"name": "core", "version": "1.0.0",
                                  "manifest_path": str(self.root / directory / "Cargo.toml")}]}

        stderr = io.StringIO()
        with patch.object(pz, "inventory", return_value=data), patch.object(pz, "metadata", side_effect=metadata), \
                redirect_stdout(io.StringIO()), redirect_stderr(stderr):
            self.assertEqual(pz.main(["--root", str(self.root), "resolve"]), 0)
            self.assertEqual(pz.main(["--root", str(self.root), "resolve", "--all"]), 1)
        self.assertIn("app: Cargo resolved core 1.0.0 outside the canonical checkout", stderr.getvalue())
        self.assertFalse((self.root / ".cargo/config.toml").exists())

    def test_locked_preflight_does_not_rewrite_the_lockfile(self):
        data = catalog(package("core"))
        self.generated(data)
        manifest = self.write("core/Cargo.toml", '[package]\nname = "core"\nversion = "1.0.0"\n')
        lock = self.write("core/Cargo.lock", "original locked resolution\n")
        resolved = [{"name": "core", "version": "1.0.0", "manifest_path": str(manifest)}]

        def cargo(argv, **_):
            if "metadata" in argv and "--locked" not in argv:
                lock.write_text("resolver rewrote dependencies\n")
            return self.cargo_result(resolved)

        with patch.object(pz, "inventory", return_value=data), patch.object(pz.subprocess, "run", side_effect=cargo), \
             redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            code = pz.main(["--root", str(self.root), "run", "--repo", "core", "--", "test", "--locked"])
        self.assertEqual(code, 0)
        self.assertEqual(lock.read_text(), "original locked resolution\n")

    def test_offline_and_frozen_preflights_cannot_access_network(self):
        data = catalog(package("core"))
        self.generated(data)
        manifest = self.write("core/Cargo.toml", '[package]\nname = "core"\nversion = "1.0.0"\n')
        resolved = [{"name": "core", "version": "1.0.0", "manifest_path": str(manifest)}]
        for flag in ["--offline", "--frozen"]:
            network_attempts = []

            def cargo(argv, **_):
                if "--offline" not in argv and "--frozen" not in argv:
                    network_attempts.append(argv)
                return self.cargo_result(resolved)

            with self.subTest(flag=flag), patch.object(pz, "inventory", return_value=data), \
                 patch.object(pz.subprocess, "run", side_effect=cargo), \
                 redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                code = pz.main(["--root", str(self.root), "run", "--repo", "core", "--", "test", flag])
                self.assertEqual(code, 0)
                self.assertEqual(network_attempts, [])

    def test_feature_enabled_registry_fallback_is_stopped_before_tests(self):
        dep = dependency("core")
        dep["optional"] = True
        data = catalog(package("core"), package("app", deps=[dep]))
        self.generated(data)
        manifest = self.write("app/Cargo.toml", '[package]\nname = "app"\nversion = "1.0.0"\n')
        registry_manifest = self.write("registry-copy/Cargo.toml", '[package]\nname = "core"\nversion = "1.1.0"\n')
        current = {"name": "app", "version": "1.0.0", "manifest_path": str(manifest)}
        fallback = {"name": "core", "version": "1.1.0", "manifest_path": str(registry_manifest)}
        for feature_args in [["--all-features"], ["--features", "experimental"], ["-F", "experimental"], ["--features=experimental"]]:
            executed = []

            def cargo(argv, **_):
                if argv[0] == "git":
                    return self.cargo_result([], returncode=1, stderr="not a Git repository")
                if "metadata" in argv:
                    enabled = any(value in {"--all-features", "--features", "-F"} or value.startswith("--features=") for value in argv)
                    return self.cargo_result([current, fallback] if enabled else [current])
                executed.append(argv)
                return self.cargo_result([])

            with self.subTest(features=feature_args), patch.object(pz, "inventory", return_value=data), \
                 patch.object(pz.subprocess, "run", side_effect=cargo), \
                 redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                code = pz.main(["--root", str(self.root), "run", "--repo", "app", "--", "test", *feature_args])
                self.assertEqual(code, 1)
                self.assertEqual(executed, [])

    def test_test_binary_arguments_stay_after_cargo_manifest_option(self):
        data = catalog(package("core"))
        self.generated(data)
        with patch.object(pz, "inventory", return_value=data), patch.object(pz, "resolved_paths", return_value=[]), \
             patch.object(pz.subprocess, "run", return_value=SimpleNamespace(returncode=0)) as invoke, \
             redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            code = pz.main(["--root", str(self.root), "run", "--repo", "core", "--", "test", "--", "--nocapture"])
        self.assertEqual(code, 0)
        self.assertEqual(invoke.call_args.args[0], ["cargo", "test", "--manifest-path", str(self.root / "core/Cargo.toml"), "--", "--nocapture"])
        self.assertFalse((self.root / ".cargo/config.toml").exists())

    def test_stale_patch_prevents_any_test_process(self):
        data = catalog(package("core"))
        self.generated(data)
        self.write(pz.PATCH, "[patch.crates-io]\n")
        with patch.object(pz, "inventory", return_value=data), \
             patch.object(pz.subprocess, "run") as invoke, \
             redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()) as error:
            code = pz.main(["--root", str(self.root), "run", "--repo", "core", "--", "test"])
        self.assertEqual(code, 1)
        self.assertIn("stale", error.getvalue())
        invoke.assert_not_called()
        self.assertFalse((self.root / ".cargo/config.toml").exists())

    def test_registry_resolution_is_rejected_and_configuration_cleaned(self):
        data = catalog(package("core"))
        self.generated(data)
        outside = tempfile.TemporaryDirectory(prefix="project-z-registry-")
        self.addCleanup(outside.cleanup)
        manifest = Path(outside.name) / "Cargo.toml"
        manifest.write_text('[package]\nname = "core"\nversion = "1.0.0"\n')
        resolved = {"packages": [{"name": "core", "version": "1.0.0", "manifest_path": str(manifest)}]}
        with patch.object(pz, "metadata", return_value=resolved):
            errors = pz.resolved_paths(data, data["repositories"], self.root)
        self.assertTrue(any("outside the canonical checkout" in error for error in errors))
        self.assertFalse((self.root / ".cargo/config.toml").exists())


@unittest.skipUnless(shutil.which("git"), "workspace source fixtures require Git")
class WorkspacePatchTests(FilesystemFixture):
    """A real path consumer and registry consumer must share one package identity."""

    def git(self, *args, cwd):
        return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True,
                              check=True).stdout.strip()

    def commit(self, directory):
        self.git("add", "--all", cwd=directory)
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                 "-c", "commit.gpgsign=false", "-c", f"core.hooksPath={self.hooks}",
                 "commit", "-qm", "fixture", cwd=directory)

    def clone(self, source, destination):
        destination.parent.mkdir(parents=True, exist_ok=True)
        self.git("-c", "protocol.file.allow=always", "clone", "-q", "--no-hardlinks",
                 "--recurse-submodules", str(source), str(destination), cwd=self.root)
        return destination

    def item(self, name):
        return next(item for item in self.data["packages"] if item["name"] == name)

    def repository(self, name):
        return next(repo for repo in self.data["repositories"] if repo["name"] == name)

    def patches(self, repository="consumer", manifest="Cargo.toml"):
        text = pz.workspace_patch_text(self.data, self.repository(repository), manifest, self.root)
        return tomllib.loads(text)["patch"]["crates-io"]

    def setUp(self):
        super().setUp()
        self.hooks = self.root / "empty-hooks"
        self.hooks.mkdir()
        self.shared = self.root / "shared"
        self.write("shared/Cargo.toml", '[workspace]\nmembers = ["runtime", "macros", "private"]\nresolver = "2"\n')
        self.write("shared/runtime/Cargo.toml", '''[package]
name = "fixture-plugin"
version = "1.0.0"
edition = "2021"
[dependencies]
fixture-plugin-macros = { path = "../macros", version = "=1.0.0" }
''')
        self.write("shared/runtime/src/lib.rs", "pub fn value() -> u32 { 1 }\n")
        self.write("shared/macros/Cargo.toml", '''[package]
name = "fixture-plugin-macros"
version = "1.0.0"
edition = "2021"
[lib]
proc-macro = true
''')
        self.write("shared/macros/src/lib.rs", "extern crate proc_macro;\n")
        self.write("shared/private/Cargo.toml", '''[package]
name = "fixture-private"
version = "1.0.0"
edition = "2021"
publish = false
''')
        self.write("shared/private/src/lib.rs", "pub struct Internal;\n")
        self.git("init", "-q", "-b", "main", cwd=self.shared)
        self.commit(self.shared)
        self.nested = self.clone(self.shared, self.root / "consumer/vendor/shared")
        self.write("bridge/Cargo.toml", '''[package]
name = "fixture-bridge"
version = "1.0.0"
edition = "2021"
[dependencies]
fixture-plugin = "=1.0.0"
fixture-plugin-macros = "=1.0.0"
''')
        self.write("bridge/src/lib.rs", "pub struct Bridge;\n")
        self.write("consumer/Cargo.toml", '''[package]
name = "consumer"
version = "1.0.0"
edition = "2021"
publish = false
[workspace]
[dependencies]
fixture-plugin = { path = "vendor/shared/runtime", version = "=1.0.0" }
fixture-bridge = { path = "../bridge", version = "=1.0.0" }
''')
        self.write("consumer/src/lib.rs", "pub struct Consumer;\n")
        self.data = catalog(
            package("fixture-plugin", repo="shared", manifest="shared/runtime/Cargo.toml",
                    deps=[dependency("fixture-plugin-macros", path="shared/macros")]),
            package("fixture-plugin-macros", repo="shared", manifest="shared/macros/Cargo.toml"),
            package("fixture-private", repo="shared", manifest="shared/private/Cargo.toml", publish=False),
            package("fixture-bridge", repo="bridge", deps=[dependency("fixture-plugin"),
                                                          dependency("fixture-plugin-macros")]),
            package("consumer", publish=False,
                    deps=[dependency("fixture-plugin", path="consumer/vendor/shared/runtime"),
                          dependency("fixture-bridge", path="bridge")]),
        )
        self.repository("shared")["commit"] = self.git("rev-parse", "HEAD", cwd=self.shared)

    def second_workspace(self):
        nested = self.clone(self.shared, self.root / "consumer/tools/vendor/shared")
        self.write("consumer/tools/Cargo.toml", '''[package]
name = "other-consumer"
version = "1.0.0"
edition = "2021"
publish = false
[workspace]
[dependencies]
fixture-plugin = { path = "vendor/shared/runtime", version = "=1.0.0" }
fixture-bridge = { path = "../../bridge", version = "=1.0.0" }
''')
        self.write("consumer/tools/src/lib.rs", "pub struct Other;\n")
        other = package("other-consumer", repo="consumer", manifest="consumer/tools/Cargo.toml",
                        publish=False, deps=[dependency("fixture-plugin", path="consumer/tools/vendor/shared/runtime"),
                                             dependency("fixture-bridge", path="bridge")])
        other["workspace"] = "consumer/tools"
        self.data["packages"].append(other)
        self.repository("consumer")["manifests"].append("tools/Cargo.toml")
        return nested

    def bridge_with_vendor(self, *, dev=False):
        bridge = self.root / "bridge"
        declaration = 'fixture-plugin = { path = "vendor/shared/runtime", version = "=1.0.0" }\n'
        self.write("bridge/Cargo.toml", '''[package]
name = "fixture-bridge"
version = "1.0.0"
edition = "2021"
[dependencies]
fixture-plugin-macros = "=1.0.0"
''' + ('[dev-dependencies]\n' if dev else '') + declaration)
        self.git("init", "-q", "-b", "main", cwd=bridge)
        self.git("-c", "protocol.file.allow=always", "submodule", "add", "-q",
                 str(self.shared), "vendor/shared", cwd=bridge)
        self.commit(bridge)
        self.item("fixture-bridge")["dependencies"][0] = dependency(
            "fixture-plugin", path="bridge/vendor/shared/runtime", kind="dev" if dev else "normal")
        self.repository("bridge")["commit"] = self.git("rev-parse", "HEAD", cwd=bridge)
        return bridge

    def test_explicit_vendor_redirects_runtime_and_macros_as_one_repository(self):
        patches = self.patches()
        self.assertEqual(patches["fixture-plugin"], {"path": "consumer/vendor/shared/runtime"})
        self.assertEqual(patches["fixture-plugin-macros"], {"path": "consumer/vendor/shared/macros"})
        self.assertEqual(patches["fixture-bridge"], {"path": "bridge"})
        self.assertNotIn("fixture-private", patches)
        self.assertNotIn("consumer", patches)

    def test_distinct_clean_commits_are_rejected_even_with_identical_package_version(self):
        (self.nested / "runtime/src/lib.rs").write_text("pub fn value() -> u32 { 2 }\n")
        self.commit(self.nested)
        self.assertEqual(self.git("status", "--porcelain", cwd=self.nested), "")
        with self.assertRaisesRegex(pz.CoordinationError, "noncanonical"):
            self.patches()

    def test_dirty_canonical_or_vendor_tree_cannot_supply_an_equivalent_copy(self):
        for directory in [self.shared, self.nested]:
            for tracked in [False, True]:
                with self.subTest(directory=directory, tracked=tracked):
                    path = directory / ("runtime/src/lib.rs" if tracked else "runtime/build.rs")
                    previous = path.read_bytes() if path.exists() else None
                    path.write_text("// unpublished local change\n")
                    try:
                        with self.assertRaisesRegex(pz.CoordinationError, "noncanonical"):
                            self.patches()
                    finally:
                        if previous is None:
                            path.unlink()
                        else:
                            path.write_bytes(previous)

    def test_same_commit_does_not_allow_a_different_package_relative_path(self):
        self.item("consumer")["dependencies"][0]["path"] = "consumer/vendor/shared/macros"
        with self.assertRaisesRegex(pz.CoordinationError, "noncanonical"):
            self.patches()

    def test_two_explicit_roots_in_one_workspace_are_a_conflict(self):
        second = self.clone(self.shared, self.root / "consumer/vendor/second")
        self.item("consumer")["dependencies"].append(
            dependency("fixture-plugin-macros", path=str(second.relative_to(self.root) / "macros")))
        with self.assertRaisesRegex(pz.CoordinationError, "conflict") as failure:
            self.patches()
        self.assertIn("consumer/vendor/shared", str(failure.exception))
        self.assertIn("consumer/vendor/second", str(failure.exception))

    def test_explicit_canonical_and_vendor_roots_cannot_be_silently_unified(self):
        self.item("consumer")["dependencies"].append(dependency("fixture-plugin-macros", path="shared/macros"))
        with self.assertRaisesRegex(pz.CoordinationError, "conflict"):
            self.patches()

    def test_workspace_choices_do_not_pollute_other_workspaces_or_catalog(self):
        self.second_workspace()
        before = json.dumps(self.data, sort_keys=True)
        first = self.patches()
        second = self.patches(manifest="tools/Cargo.toml")
        canonical = self.patches(repository="shared")
        self.assertEqual(first["fixture-plugin"]["path"], "consumer/vendor/shared/runtime")
        self.assertEqual(second["fixture-plugin"]["path"], "consumer/tools/vendor/shared/runtime")
        self.assertEqual(second["fixture-plugin-macros"]["path"], "consumer/tools/vendor/shared/macros")
        self.assertEqual(canonical["fixture-plugin"]["path"], "shared/runtime")
        self.assertEqual(self.patches(), first)
        self.assertEqual(json.dumps(self.data, sort_keys=True), before)

    def test_registry_optional_and_dev_dependencies_propagate_vendor_constraints(self):
        self.bridge_with_vendor()
        for kind, optional in [("normal", False), ("normal", True), ("build", False), ("dev", False)]:
            declaration = dependency("fixture-bridge", kind=kind)
            declaration["optional"] = optional
            self.item("consumer")["dependencies"] = [declaration]
            with self.subTest(kind=kind, optional=optional):
                patches = self.patches()
                self.assertEqual(patches["fixture-plugin"]["path"], "bridge/vendor/shared/runtime")
                self.assertEqual(patches["fixture-plugin-macros"]["path"], "bridge/vendor/shared/macros")

    def test_transitive_dev_path_does_not_constrain_the_consuming_workspace(self):
        self.bridge_with_vendor(dev=True)
        patches = self.patches()
        self.assertEqual(patches["fixture-plugin"]["path"], "consumer/vendor/shared/runtime")
        self.assertEqual(patches["fixture-plugin-macros"]["path"], "consumer/vendor/shared/macros")
        # Building the bridge's own tests does include its development dependency.
        bridge_patches = self.patches(repository="bridge")
        self.assertEqual(bridge_patches["fixture-plugin"]["path"], "bridge/vendor/shared/runtime")

    def test_transitive_paths_move_with_the_selected_parent_repository(self):
        bridge = self.bridge_with_vendor()
        nested = self.clone(bridge, self.root / "consumer/vendor/bridge")
        chosen = nested.relative_to(self.root).as_posix()
        self.item("consumer")["dependencies"] = [
            dependency("fixture-bridge", path=chosen),
            dependency("fixture-plugin", path=chosen + "/vendor/shared/runtime"),
        ]
        patches = self.patches()
        self.assertEqual(patches["fixture-bridge"]["path"], chosen)
        self.assertEqual(patches["fixture-plugin"]["path"], chosen + "/vendor/shared/runtime")
        self.assertEqual(patches["fixture-plugin-macros"]["path"], chosen + "/vendor/shared/macros")
        self.assertEqual(self.git("status", "--porcelain", cwd=bridge), "")
        self.assertEqual(self.git("status", "--porcelain", cwd=nested), "")

    def test_resolve_and_run_use_the_same_workspace_config_and_restore_locks(self):
        self.second_workspace()
        self.generated(self.data)
        expected = {"Cargo.toml": "consumer/vendor/shared", "tools/Cargo.toml": "consumer/tools/vendor/shared"}
        locks = {manifest: self.write(str(Path("consumer") / Path(manifest).parent / "Cargo.lock"),
                                     "original lock bytes\r\n") for manifest in expected}
        originals = {manifest: path.read_bytes() for manifest, path in locks.items()}
        seen = []

        def observe(kind, manifest):
            content = (self.root / ".cargo/config.toml").read_text()
            patches = tomllib.loads(content)["patch"]["crates-io"]
            self.assertEqual(patches["fixture-plugin"]["path"], expected[manifest] + "/runtime")
            self.assertEqual(patches["fixture-plugin-macros"]["path"], expected[manifest] + "/macros")
            locks[manifest].write_text("temporary resolution\n")
            seen.append((kind, manifest, content))

        def metadata(repo, manifest, *_args, **_kwargs):
            observe("metadata", manifest)
            return {"packages": [
                {"name": name, "version": "1.0.0", "manifest_path": str(self.root / expected[manifest] / inner / "Cargo.toml")}
                for name, inner in [("fixture-plugin", "runtime"), ("fixture-plugin-macros", "macros")]
            ]}

        real_run = subprocess.run

        def execute(argv, **kwargs):
            if argv[0] != "cargo":
                return real_run(argv, **kwargs)
            manifest = Path(argv[argv.index("--manifest-path") + 1]).relative_to(self.root / "consumer").as_posix()
            observe("run", manifest)
            return SimpleNamespace(returncode=0)

        with patch.object(pz, "inventory", return_value=self.data), patch.object(pz, "metadata", side_effect=metadata), \
             patch.object(pz.subprocess, "run", side_effect=execute), \
             redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()) as error:
            self.assertEqual(pz.main(["--root", str(self.root), "resolve", "consumer"]), 0, error.getvalue())
            self.assertFalse((self.root / ".cargo/config.toml").exists())
            self.assertEqual(pz.main(["--root", str(self.root), "run", "--repo", "consumer", "--", "test", "--offline"]), 0, error.getvalue())
        self.assertEqual(len(seen), 6)
        for manifest in expected:
            configurations = [content for _, observed, content in seen if observed == manifest]
            self.assertEqual(len(configurations), 3)
            self.assertEqual(len(set(configurations)), 1)
            self.assertEqual(locks[manifest].read_bytes(), originals[manifest])
        self.assertFalse((self.root / ".cargo/config.toml").exists())
        self.assertEqual((self.root / pz.PATCH).read_text(), pz.patch_text(self.data))

    def test_workspace_config_and_lock_are_restored_after_resolution_or_command_failure(self):
        self.generated(self.data)
        lock = self.write("consumer/Cargo.lock", "user lock\r\n")
        original = lock.read_bytes()
        real_run = subprocess.run
        for stage in ["resolve", "run"]:
            def metadata(*_args, **_kwargs):
                lock.write_text("temporary preflight\n")
                if stage == "resolve":
                    raise pz.CoordinationError("fixture resolution failed")
                return {"packages": []}

            def execute(argv, **kwargs):
                if argv[0] != "cargo":
                    return real_run(argv, **kwargs)
                lock.write_text("temporary failed command\n")
                return SimpleNamespace(returncode=7)

            args = ["resolve", "consumer"] if stage == "resolve" else ["run", "--repo", "consumer", "--", "test"]
            with self.subTest(stage=stage), patch.object(pz, "inventory", return_value=self.data), \
                 patch.object(pz, "metadata", side_effect=metadata), patch.object(pz.subprocess, "run", side_effect=execute), \
                 redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(pz.main(["--root", str(self.root), *args]), 1)
                self.assertFalse((self.root / ".cargo/config.toml").exists())
                self.assertEqual(lock.read_bytes(), original)

    @unittest.skipUnless(shutil.which("cargo"), "offline Cargo metadata fixture requires Cargo")
    def test_real_cargo_collision_is_removed_for_both_runtime_and_macro_packages(self):
        self.generated(self.data)
        env = dict(os.environ, CARGO_HOME=str(self.root / "cargo-home"), CARGO_NET_OFFLINE="true",
                   CARGO_TARGET_DIR=str(self.root / "metadata-target"), CARGO_BUILD_JOBS="1",
                   RUSTC_WRAPPER="", RUSTC_WORKSPACE_WRAPPER="")
        argv = ["cargo", "metadata", "--offline", "--format-version", "1", "--manifest-path",
                str(self.root / "consumer/Cargo.toml")]

        with pz.preserved_workspace_locks(self.data, self.repository("consumer"), self.root), \
             pz.local_config(self.root, content=pz.patch_text(self.data)):
            baseline = subprocess.run(argv, cwd=self.root, env=env, capture_output=True, text=True, timeout=30)
        self.assertNotEqual(baseline.returncode, 0, "the fixture must reproduce Cargo's actual duplicate-path failure")
        self.assertIn("collision", baseline.stderr.lower(), baseline.stderr)
        self.assertIn("lockfile", baseline.stderr.lower(), baseline.stderr)

        content = pz.workspace_patch_text(self.data, self.repository("consumer"), "Cargo.toml", self.root)
        with pz.preserved_workspace_locks(self.data, self.repository("consumer"), self.root), \
             pz.local_config(self.root, content=content):
            resolved = subprocess.run(argv, cwd=self.root, env=env, capture_output=True, text=True, timeout=30)
        self.assertEqual(resolved.returncode, 0, resolved.stderr)
        packages = json.loads(resolved.stdout)["packages"]
        for name, inner in [("fixture-plugin", "runtime"), ("fixture-plugin-macros", "macros")]:
            matches = [item for item in packages if item["name"] == name]
            self.assertEqual(len(matches), 1)
            self.assertEqual(Path(matches[0]["manifest_path"]).resolve(), self.nested / inner / "Cargo.toml")

        # Cargo resolves dev dependencies only for the selected workspace, not
        # for every transitive library whose metadata contains a dev edge.
        self.bridge_with_vendor(dev=True)
        content = pz.workspace_patch_text(self.data, self.repository("consumer"), "Cargo.toml", self.root)
        with pz.preserved_workspace_locks(self.data, self.repository("consumer"), self.root), \
             pz.local_config(self.root, content=content):
            development = subprocess.run(argv, cwd=self.root, env=env, capture_output=True, text=True, timeout=30)
        self.assertEqual(development.returncode, 0, development.stderr)
        packages = json.loads(development.stdout)["packages"]
        for name, inner in [("fixture-plugin", "runtime"), ("fixture-plugin-macros", "macros")]:
            matches = [item for item in packages if item["name"] == name]
            self.assertEqual(len(matches), 1)
            self.assertEqual(Path(matches[0]["manifest_path"]).resolve(), self.nested / inner / "Cargo.toml")
        self.assertFalse((self.root / ".cargo/config.toml").exists())
        self.assertFalse((self.root / "consumer/Cargo.lock").exists())
        self.assertEqual(self.git("status", "--porcelain", cwd=self.shared), "")
        self.assertEqual(self.git("status", "--porcelain", cwd=self.nested), "")


@unittest.skipUnless(shutil.which("git"), "source-equivalence fixtures require Git")
class EquivalentSourceTests(FilesystemFixture):
    def git(self, *args, cwd):
        return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True).stdout

    def setUp(self):
        super().setUp()
        self.shared = self.root / "shared"
        self.write("shared/Cargo.toml", '[workspace]\nmembers = ["crates/core"]\n[workspace.package]\nversion = "1.0.0"\n')
        self.write("shared/crates/core/Cargo.toml", '[package]\nname = "core"\nversion.workspace = true\nedition = "2021"\n')
        self.write("shared/crates/core/src/lib.rs", "pub fn value() -> u32 { 1 }\n")
        hooks = self.root / "empty-hooks"
        hooks.mkdir()
        self.git("init", "-q", "-b", "main", cwd=self.shared)
        self.git("add", ".", cwd=self.shared)
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "-c", "commit.gpgsign=false", "-c", f"core.hooksPath={hooks}", "commit", "-qm", "fixture", cwd=self.shared)
        self.nested = self.root / "consumer/vendor/shared"
        self.nested.parent.mkdir(parents=True)
        self.git("clone", "-q", "--no-hardlinks", str(self.shared), str(self.nested), cwd=self.root)
        self.pkg = package("core", repo="shared", manifest="shared/crates/core/Cargo.toml")
        self.data = catalog(self.pkg)

    def equivalent(self):
        return pz.equivalent_source("consumer/vendor/shared/crates/core", self.pkg, self.data, self.root)

    def test_identical_clean_pinned_copy_is_accepted(self):
        self.assertTrue(self.equivalent())

    def test_resolver_lock_changes_are_restored_before_nested_source_proof(self):
        self.generated(self.data)

        def resolve(*_args, **_kwargs):
            (self.shared / "Cargo.lock").write_text("temporary local patch resolution\n")
            return {"packages": [{"name": "core", "version": "1.0.0",
                                  "manifest_path": str(self.nested / "crates/core/Cargo.toml")}]}

        with patch.object(pz, "metadata", side_effect=resolve):
            self.assertEqual(pz.resolved_paths(self.data, self.data["repositories"], self.root), [])
        self.assertEqual(self.git("status", "--porcelain", cwd=self.shared), "")
        self.assertTrue(self.equivalent())

    def test_untracked_build_script_makes_copy_different(self):
        (self.nested / "crates/core/build.rs").write_text('fn main() { println!("cargo:rustc-cfg=changed"); }\n')
        self.assertFalse(self.equivalent())

    def test_changed_workspace_manifest_makes_member_copy_different(self):
        manifest = self.nested / "Cargo.toml"
        manifest.write_text(manifest.read_text().replace('version = "1.0.0"', 'version = "1.1.0"'))
        self.assertFalse(self.equivalent())


if __name__ == "__main__":
    unittest.main()
