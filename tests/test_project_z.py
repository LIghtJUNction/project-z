"""Coordination invariants independent of the installed Cargo toolchain."""

from contextlib import redirect_stderr, redirect_stdout
import io
import json
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
