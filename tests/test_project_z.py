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
        "source": None if path else f"git+https://github.com/ProjectZTests/{name}.git",
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
            {"name": name, "path": name, "url": f"https://github.com/ProjectZTests/{name}.git",
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

    def test_generated_inventory_has_no_source_override(self):
        data = catalog(package("core"), package("private-tool", publish=False))
        self.assertEqual(set(pz.generated(data)), {pz.CATALOG, pz.PROJECTS})
        self.assertNotIn("patch.crates-io", "\n".join(pz.generated(data).values()))

    def test_project_documentation_uses_pinned_manifests_and_runtime_dependencies(self):
        data = catalog(package("core", repo="suite", manifest="suite/crates/core/Cargo.toml"),
                       package("desktop", deps=[dependency("core")]))
        next(repo for repo in data["repositories"] if repo["name"] == "desktop")["requires"] = ["service"]
        document = pz.generated(data)[pz.PROJECTS]
        self.assertIn("https://github.com/ProjectZTests/suite/blob/" + "0" * 40 + "/crates/core/Cargo.toml", document)
        self.assertIn("service, suite", document)
        self.assertIn("注册表发布服务于外部消费者", document)




class VersionDeclarationTests(FilesystemFixture):
    def test_path_only_prerelease_is_accepted_but_explicit_star_is_checked(self):
        manifest = self.write("app/Cargo.toml", '[dependencies]\ncore = { path = "../core" }\n')
        declaration = {"name": "core", "rename": None, "kind": None, "target": None}
        explicit = pz.explicit_version(manifest, self.root / "app", declaration)
        self.assertFalse(explicit)
        data = catalog(package("core", repo="app", manifest="app/core/Cargo.toml", version="0.1.0-alpha.1"), package("app", deps=[
            dependency("core", path="app/core", requirement="*", explicit=explicit)]))
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
        self.write(".gitmodules", '[submodule "linked"]\npath = linked\nurl = https://github.com/ProjectZTests/linked.git\n')
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




class SourceLinkTests(FilesystemFixture):
    """A source-distributed app must be checked even when Cargo excludes it."""

    def git(self, *args, cwd):
        return pz.command(["git", *args], cwd).strip()

    def commit(self, checkout, message):
        self.git("add", "-A", cwd=checkout)
        self.git("-c", "user.name=Project Z tests", "-c", "user.email=tests@example.invalid",
                 "commit", "-qm", message, cwd=checkout)
        return self.git("rev-parse", "HEAD", cwd=checkout)

    def setUp(self):
        super().setUp()
        self.gui = self.root / "gui"
        self.write("gui/source.txt", "original\n")
        self.git("init", "-q", cwd=self.gui)
        self.old = self.commit(self.gui, "Initial GUI")
        self.consumer = self.root / "daemon"
        self.write("daemon/Cargo.toml", '[workspace]\nexclude = ["apps/gui"]\n')
        self.write("daemon/.gitmodules", '[submodule "apps/gui"]\npath = apps/gui\nurl = https://github.com/ProjectZTests/gui.git\n')
        self.git("init", "-q", cwd=self.consumer)
        self.nested = self.consumer / "apps/gui"
        self.nested.parent.mkdir(parents=True)
        self.git("clone", "-q", "--no-hardlinks", str(self.gui), str(self.nested), cwd=self.root)
        self.commit(self.consumer, "Distribute the excluded GUI")
        self.data = catalog(package("daemon"), package("gui", publish=False))
        self.refresh()
        self.rules = {"repositories": {"daemon": {"source_links": {"apps/gui": "gui"}}}}
        self.write("project-z.toml", '[repositories.daemon]\nsource_links = { "apps/gui" = "gui" }\n')

    def refresh(self):
        for repo in self.data["repositories"]:
            repo["commit"] = self.git("rev-parse", "HEAD", cwd=self.root / repo["path"])

    def errors(self):
        return pz.validate(self.data, self.rules, self.root)

    def advance_gui(self):
        (self.gui / "source.txt").write_text("new GUI source\n")
        result = self.commit(self.gui, "Update GUI")
        self.refresh()
        return result

    def test_exact_clean_excluded_source_is_accepted(self):
        self.assertEqual(self.errors(), [])

    def test_check_and_resolve_reject_stale_excluded_app_before_cargo(self):
        self.advance_gui()
        self.generated(self.data)
        with patch.object(pz, "inventory", return_value=self.data), patch.object(pz, "resolved_paths") as resolve:
            for action in [["check"], ["resolve", "--all"]]:
                with self.subTest(action=action), redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()) as err:
                    self.assertEqual(pz.main(["--root", str(self.root), *action]), 1)
                    self.assertIn("pinned source", err.getvalue())
            resolve.assert_not_called()

    def test_checkout_drift_is_rejected_even_when_recorded_pins_match(self):
        new = self.advance_gui()
        self.git("fetch", "-q", str(self.gui), new, cwd=self.nested)
        self.git("checkout", "-q", new, cwd=self.nested)
        self.git("checkout", "-q", self.old, cwd=self.gui)
        self.refresh()
        self.assertTrue(any("not clean" in error or "checkout differs" in error for error in self.errors()))

    def test_staged_gitlink_drift_cannot_hide_behind_old_head(self):
        new = self.advance_gui()
        self.git("checkout", "-q", self.old, cwd=self.gui)
        self.refresh()
        self.git("update-index", "--cacheinfo", f"160000,{new},apps/gui", cwd=self.consumer)
        self.assertTrue(any("not clean" in error for error in self.errors()))

    def test_dirty_nested_and_canonical_sources_are_rejected(self):
        for checkout in [self.nested, self.gui]:
            with self.subTest(checkout=checkout):
                original = (checkout / "source.txt").read_bytes()
                (checkout / "source.txt").write_text("uncommitted change\n")
                self.assertTrue(any("not clean" in error for error in self.errors()))
                (checkout / "source.txt").write_bytes(original)
        self.assertEqual(self.errors(), [])

    def test_missing_gitlink_and_unknown_target_are_rejected(self):
        for links, message in [({"apps/missing": "gui"}, "missing from consumer HEAD"),
                               ({"Cargo.toml": "gui"}, "not an exact gitlink"),
                               ({"apps/gui": "unknown"}, "source_links disagrees")]:
            with self.subTest(links=links):
                self.rules["repositories"]["daemon"]["source_links"] = links
                self.assertTrue(any(message in error for error in self.errors()))

    def test_invalid_source_paths_are_rejected(self):
        for path in ["", ".", "../gui", "/tmp/gui", ".git", "apps/.git/objects", "apps/../gui",
                     "apps//gui", "apps\\gui", "apps/\x1b"]:
            with self.subTest(path=path):
                self.rules["repositories"]["daemon"]["source_links"] = {path: "gui"}
                self.assertTrue(any("invalid source link path" in error for error in self.errors()))

    def test_symlink_outside_consumer_is_rejected(self):
        outside = self.root / "outside"
        outside.mkdir()
        link = self.consumer / "apps/outside"
        link.symlink_to(outside, target_is_directory=True)
        self.rules["repositories"]["daemon"]["source_links"] = {"apps/outside": "gui"}
        self.assertTrue(any("escapes coordination checkout" in error for error in self.errors()))

    def test_registered_gitlinks_are_checked_without_an_explicit_source_links_rule(self):
        self.advance_gui()
        self.assertTrue(any("pinned source" in error for error in pz.validate(self.data, {}, self.root)))


class GitPolicyTests(FilesystemFixture):
    def data(self, dep=None):
        return catalog(package("core"), package("app", deps=[dep or dependency("core")]))

    def test_latest_git_with_publish_version_is_allowed(self):
        self.assertEqual(pz.validate(self.data(), {}, self.root), [])

    def test_registry_cross_path_and_every_fixed_git_selector_are_rejected(self):
        for source, path in [
            ("registry+https://github.com/rust-lang/crates.io-index", None),
            (None, "core"),
            ("git+https://github.com/ProjectZTests/core.git?branch=main", None),
            ("git+https://github.com/ProjectZTests/core.git?tag=v1.0.0", None),
            ("git+https://github.com/ProjectZTests/core.git?rev=" + "1" * 40, None),
            ("git+https://github.com/ProjectZTests/core", None),
        ]:
            with self.subTest(source=source, path=path):
                dep = dependency("core")
                dep.update(source=source, path=path)
                self.assertTrue(any("default branch" in error for error in pz.validate(self.data(dep), {}, self.root)))

    def test_target_optional_dev_and_alias_dependencies_have_the_same_source_rule(self):
        dep = dependency("core", kind="dev")
        dep.update(alias="engine", target='cfg(target_os = "windows")', optional=True,
                   source="registry+https://github.com/rust-lang/crates.io-index")
        self.assertTrue(any("default branch" in error for error in pz.validate(self.data(dep), {}, self.root)))

    def test_same_repository_paths_remain_valid(self):
        data = catalog(package("core", repo="app", manifest="app/core/Cargo.toml"),
                       package("app", deps=[dependency("core", path="app/core")]))
        self.assertEqual(pz.validate(data, {}, self.root), [])

    def test_git_source_does_not_bypass_current_version_or_missing_package_checks(self):
        dep = dependency("core", requirement="=0.9.0")
        self.assertTrue(any("requires core" in error for error in pz.validate(self.data(dep), {}, self.root)))
        dep = dependency("missing")
        dep["source"] = "git+https://github.com/ProjectZTests/core.git"
        self.assertTrue(any("missing from the catalog" in error for error in pz.validate(self.data(dep), {}, self.root)))

    def test_publishable_git_dependencies_keep_version_metadata(self):
        for kind in ("normal", "build"):
            with self.subTest(kind=kind):
                data = self.data(dependency("core", kind=kind, explicit=False))
                self.assertTrue(any("version metadata" in error for error in pz.validate(data, {}, self.root)))
                data["packages"][1]["publish"] = False
                self.assertEqual(pz.validate(data, {}, self.root), [])
        self.assertEqual(pz.validate(self.data(dependency("core", kind="dev", explicit=False)), {}, self.root), [])

    def test_unknown_internal_package_cannot_hide_behind_alternate_github_spelling(self):
        for source in ("git+https://github.com/ProjectZTests/core",
                       "git+https://GITHUB.COM/projectztests/CORE.git?branch=main",
                       "git+ssh://git@github.com/projectztests/core.git#" + "1" * 40):
            with self.subTest(source=source):
                dep = dependency("new-companion")
                dep["source"] = source
                data = self.data(dep)
                self.assertTrue(any("missing from the catalog" in error for error in pz.validate(data, {}, self.root)))
                self.write("app/Cargo.lock", 'version = 4\n[[package]]\nname = "new-companion"\nversion = "1.0.0"\nsource = ' + json.dumps(source) + '\n')
                app = next(repo for repo in data["repositories"] if repo["name"] == "app")
                self.assertTrue(any("missing from the catalog" in error for error in pz.locked_source_errors(data, [app], self.root)))
                resolved = {"packages": [{"name": "new-companion", "version": "1.0.0", "source": source}]}
                with patch.object(pz, "locked_source_errors", return_value=[]), patch.object(pz, "metadata", return_value=resolved):
                    self.assertTrue(any("missing from the catalog" in error for error in pz.resolved_paths(data, [app], self.root)))

    def test_unknown_external_git_packages_remain_allowed(self):
        data = self.data()
        source = "git+https://github.com/OtherOwner/core.git#" + "1" * 40
        self.write("app/Cargo.lock", 'version = 4\n[[package]]\nname = "external-companion"\nversion = "1.0.0"\nsource = ' + json.dumps(source) + '\n')
        app = next(repo for repo in data["repositories"] if repo["name"] == "app")
        self.assertEqual(pz.locked_source_errors(data, [app], self.root), [])
        resolved = {"packages": [{"name": "external-companion", "version": "1.0.0", "source": source}]}
        with patch.object(pz, "metadata", return_value=resolved):
            self.assertEqual(pz.resolved_paths(data, [app], self.root), [])

    def test_internal_patch_in_manifest_or_configuration_is_rejected_without_deleting_it(self):
        for location in ["app/Cargo.toml", "app/.cargo/config.toml", ".cargo/config.toml"]:
            path = self.write(location, '[patch."https://github.com/ProjectZTests/core.git"]\ncore = { path = "replacement" }\n')
            before = path.read_bytes()
            self.assertTrue(any("internal source override" in error for error in pz.validate(self.data(), {}, self.root)))
            self.assertEqual(path.read_bytes(), before)
            path.unlink()

    def test_source_urls_cannot_select_another_host_or_revision(self):
        for url in ["https://example.invalid/core.git", "https://github.com/a/b.git?rev=old", "git@github.com:a/b.git"]:
            with self.subTest(url=url), self.assertRaises(pz.CoordinationError):
                pz.github_url(url)

    def test_build_flags_keep_locked_and_feature_semantics_before_separator(self):
        args = pz.locked_cargo_args(["test", "--features", "optional", "--", "--locked"])
        self.assertEqual(args, ["test", "--locked", "--features", "optional", "--", "--locked"])
        self.assertEqual(pz.resolution_options(args), ["--locked", "--features", "optional"])
        self.assertEqual(pz.locked_cargo_args(["test", "--frozen"]), ["test", "--frozen"])
        self.assertEqual(pz.locked_cargo_args(["fmt", "--check"]), ["fmt", "--check"])
        for command in ["update", "generate-lockfile"]:
            with self.assertRaises(pz.CoordinationError):
                pz.locked_cargo_args([command])

    def test_external_configuration_and_dependencies_are_preserved(self):
        config = self.write(".cargo/config.toml", '[build]\njobs = 1\n')
        data = catalog(package("app", deps=[dependency("external")]))
        data["packages"][0]["dependencies"][0]["source"] = "registry+https://github.com/rust-lang/crates.io-index"
        self.assertEqual(pz.validate(data, {}, self.root), [])
        self.assertEqual(config.read_text(), '[build]\njobs = 1\n')


class GitSourceFixture(FilesystemFixture):
    """Real local transports stand in for GitHub; no Cargo build or network."""
    def git(self, repo, *args):
        return pz.command(["git", *args], repo).strip()

    def commit(self, repo, message):
        self.git(repo, "add", "-A")
        self.git(repo, "-c", "user.name=Project Z tests", "-c", "user.email=tests@example.invalid", "commit", "-qm", message)
        return self.git(repo, "rev-parse", "HEAD")

    def cargo(self, repo, *args):
        return pz.command(["cargo", *args], repo)

    def setUp(self):
        super().setUp()
        self.base = self.root
        self.root = self.base / "aggregate"
        self.root.mkdir()
        self.remotes = self.base / "remotes"
        self.remotes.mkdir()
        self.url = "https://github.com/ProjectZTests/"
        environment = patch.dict(os.environ, {
            "GIT_CONFIG_COUNT": "2",
            "GIT_CONFIG_KEY_0": f"url.{self.remotes.as_uri()}/.insteadOf",
            "GIT_CONFIG_VALUE_0": self.url,
            "GIT_CONFIG_KEY_1": "protocol.file.allow",
            "GIT_CONFIG_VALUE_1": "always",
            "GIT_ALLOW_PROTOCOL": "file",
            "CARGO_HOME": str(self.base / "cargo-home"),
            "CARGO_NET_GIT_FETCH_WITH_CLI": "true",
            "CARGO_NET_OFFLINE": "false",
            "PYTHONDONTWRITEBYTECODE": "1",
        })
        environment.start()
        self.addCleanup(environment.stop)
        self.shared = self.remotes / "shared.git"
        self.app = self.remotes / "app.git"
        for repo in (self.shared, self.app, self.root):
            repo.mkdir(exist_ok=True)
            self.git(repo, "init", "-q", "-b", "main")
            self.git(repo, "config", "user.name", "Project Z tests")
            self.git(repo, "config", "user.email", "tests@example.invalid")
            self.git(repo, "config", "commit.gpgsign", "false")
        (self.shared / "Cargo.toml").write_text('[workspace]\nmembers = ["core", "private"]\nresolver = "2"\n')
        for name in ("core", "private"):
            folder = self.shared / name
            (folder / "src").mkdir(parents=True)
            (folder / "Cargo.toml").write_text(f'[package]\nname = "tiny-{name}"\nversion = "1.0.0"\nedition = "2021"\n' + ('publish = false\n' if name == "private" else '') + '[features]\nallowed = []\n')
            (folder / "src/lib.rs").write_text('pub fn value() -> u8 { 1 }\n')
        self.cargo(self.shared, "generate-lockfile")
        self.shared_initial = self.commit(self.shared, "initial shared source")
        (self.app / "src").mkdir()
        (self.app / "src/main.rs").write_text('fn main() {}\n')
        (self.app / "Cargo.toml").write_text(
            '[package]\nname = "tiny-app"\nversion = "1.0.0"\nedition = "2021"\npublish = false\n'
            '[dependencies]\ntiny-core = { git = "' + self.url + 'shared.git", version = "1.0.0" }\n'
            'tiny-private = { git = "' + self.url + 'shared.git", version = "1.0.0", optional = true }\n'
            '[features]\nexperimental = ["dep:tiny-private"]\n')
        self.cargo(self.app, "generate-lockfile")
        self.app_initial = self.commit(self.app, "initial consumer lock")
        for name in ("shared", "app"):
            self.git(self.root, "submodule", "add", "-q", self.url + name + ".git", name)
            self.git(self.root / name, "checkout", "-q", "--detach")
        self.write("project-z.toml", '[repositories.app]\nrole = "application"\n')
        self.write(".gitignore", '__pycache__/\n')
        pz.sync_sources(self.root)
        self.data = pz.inventory(self.root)
        self.generated(self.data)
        self.root_head = self.commit(self.root, "record source cohort")

    def record(self):
        self.data = pz.inventory(self.root)
        self.generated(self.data)
        return self.data

    def advance_shared(self):
        (self.shared / "core/src/lib.rs").write_text('pub fn value() -> u8 { 2 }\n')
        return self.commit(self.shared, "change implementation without version change")


@unittest.skipUnless(shutil.which("git") and shutil.which("cargo"), "requires Git and Cargo")
class GitSourceIntegrationTests(GitSourceFixture):
    def test_real_locked_git_resolution_includes_private_optional_package(self):
        self.assertEqual(pz.validate(self.data, pz.policy(self.root), self.root), [])
        self.assertEqual(pz.freshness_errors(self.data, self.root), [])
        self.assertEqual(pz.resolved_paths(self.data, self.data["repositories"], self.root, ["--all-features"]), [])
        self.assertEqual(set(pz.package_map(self.data)), {"tiny-app", "tiny-core", "tiny-private"})
        self.assertFalse(pz.package_map(self.data)["tiny-private"]["publish"])
        self.assertFalse((self.root / ".cargo/config.toml").exists())

    def test_same_version_old_git_commit_is_stopped_without_rewriting_lock(self):
        lock = self.root / "app/Cargo.lock"
        original = lock.read_bytes()
        new = self.advance_shared()
        self.assertTrue(any(new in error for error in pz.freshness_errors(self.data, self.root)))
        pz.sync_sources(self.root)
        self.record()
        errors = pz.resolved_paths(self.data, self.data["repositories"], self.root)
        self.assertTrue(any("stale internal tiny-core" in error and new in error for error in errors))
        self.assertEqual(lock.read_bytes(), original)

    def test_committed_consumer_update_closes_the_source_graph(self):
        self.advance_shared()
        self.cargo(self.app, "update", "-p", "tiny-core")
        self.commit(self.app, "refresh consumer Git lock")
        pz.sync_sources(self.root)
        self.record()
        self.assertEqual(pz.locked_source_errors(self.data, self.data["repositories"], self.root), [])
        self.assertEqual(pz.resolved_paths(self.data, self.data["repositories"], self.root), [])
        self.assertEqual(pz.freshness_errors(self.data, self.root), [])

    def test_same_version_registry_and_optional_old_version_cannot_hide_in_lock(self):
        lock = self.root / "app/Cargo.lock"
        original = lock.read_text()
        source = f'git+{self.url}shared.git#{self.shared_initial}'
        lock.write_text(original.replace(source, "registry+https://github.com/rust-lang/crates.io-index"))
        self.assertTrue(any("stale internal tiny-core" in error for error in pz.resolved_paths(self.data, self.data["repositories"], self.root)))
        lock.write_text(original + '\n[[package]]\nname = "tiny-private"\nversion = "0.9.0"\nsource = "registry+https://github.com/rust-lang/crates.io-index"\n')
        self.assertTrue(any("tiny-private 0.9.0" in error for error in pz.resolved_paths(self.data, self.data["repositories"], self.root)))

    def test_sync_follows_renamed_default_branch_even_when_commit_is_unchanged(self):
        self.git(self.shared, "branch", "-m", "main", "development")
        self.assertEqual(pz.default_head(self.url + "shared.git", self.root)["branch"], "development")
        self.assertTrue(pz.freshness_errors(self.data, self.root))
        pz.sync_sources(self.root)
        self.record()
        self.assertEqual(pz.freshness_errors(self.data, self.root), [])
        self.assertEqual(next(r for r in self.data["repositories"] if r["name"] == "shared")["branch"], "development")

    def test_sync_refuses_dirty_or_active_checkout_without_overwriting_source(self):
        checkout = self.root / "shared"
        source = checkout / "core/src/lib.rs"
        original = source.read_text()
        source.write_text("uncommitted work\n")
        with self.assertRaisesRegex(pz.CoordinationError, "not clean"):
            pz.sync_sources(self.root)
        self.assertEqual(source.read_text(), "uncommitted work\n")
        source.write_text(original)
        self.git(checkout, "switch", "-c", "active-work")
        self.advance_shared()
        with self.assertRaisesRegex(pz.CoordinationError, "active branch"):
            pz.sync_sources(self.root)
        self.assertEqual(self.git(checkout, "rev-parse", "HEAD"), self.shared_initial)

    def test_check_requires_freshness_but_locked_resolution_reproduces_saved_cohort(self):
        self.advance_shared()
        self.assertEqual(pz.resolved_paths(self.data, self.data["repositories"], self.root), [])
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()) as errors:
            self.assertEqual(pz.main(["--root", str(self.root), "check"]), 1)
        self.assertIn("latest default", errors.getvalue())

    def test_missing_lock_fails_instead_of_implicitly_creating_one(self):
        lock = self.root / "app/Cargo.lock"
        lock.unlink()
        self.assertTrue(any("missing regular lockfile" in error for error in pz.resolved_paths(self.data, self.data["repositories"], self.root)))
        self.assertFalse(lock.exists())

    def test_run_checks_real_sources_and_keeps_test_arguments_after_separator(self):
        original_run = subprocess.run
        executed = []
        before = (self.root / "app/Cargo.lock").read_bytes()
        def invoke(argv, **kwargs):
            if argv[:2] == ["cargo", "test"]:
                executed.append(argv)
                return SimpleNamespace(returncode=0)
            return original_run(argv, **kwargs)
        with patch.object(pz.subprocess, "run", side_effect=invoke), redirect_stdout(io.StringIO()):
            code = pz.main(["--root", str(self.root), "run", "--repo", "app", "--", "test", "--offline", "--", "--nocapture"])
        self.assertEqual(code, 0)
        self.assertEqual(len(executed), 1)
        self.assertIn("--locked", executed[0][:executed[0].index("--")])
        self.assertEqual(executed[0][-2:], ["--", "--nocapture"])
        self.assertEqual((self.root / "app/Cargo.lock").read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
