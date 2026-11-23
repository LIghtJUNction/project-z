"""Reviewed migration regressions, independent of Cargo and the network."""
import hashlib
import json
from pathlib import Path
import re
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import project_z as pz
import rust_source as rust
import shared_implementations as shared
from test_project_z import FilesystemFixture, catalog, dependency, package

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures/shared_implementations"
GOOD_HEX = "fn encode(bytes: &[u8], out: &mut [u8]) { zhex::encode_lower(bytes, out).unwrap(); }\n"


def historical_fragment(record):
    text = (ROOT / record["fixture"]).read_text(encoding="utf-8")
    matches = [f for f in rust.functions(text) if f["name"] == record["source"]["function"]]
    if len(matches) != 1:
        raise AssertionError(f"fixture must contain one named historical function: {record['id']}")
    function = matches[0]
    return text[function["start"]:function["end"]], function


def retained_fragment(record):
    text = (ROOT / record["fixture"]).read_text(encoding="utf-8")
    matches = [f for f in rust.functions(text)
               if f["name"] == record["function"] and f["line"] == record["fixture_line"]]
    if len(matches) != 1:
        raise AssertionError(f"retained fixture location is not unique: {record}")
    function = matches[0]
    return text[function["start"]:function["end"]], function


def contract_proof():
    return json.loads((ROOT / shared.load_policy()["additional_proofs"][0]).read_text(encoding="utf-8"))


def retained_source(repository, path):
    return "\n".join(retained_fragment(record)[0] for record in contract_proof()["retained_functions"]
                     if record["repository"] == repository and record["path"] == path)


class HistoricalRules(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = shared.load_policy()

    def test_policy_matches_the_ten_reviewed_consumers(self):
        reviewed = {}
        for path in [self.policy["proof"], *self.policy["additional_proofs"]]:
            proof = json.loads((ROOT / path).read_text(encoding="utf-8"))
            for row in proof["rows"]:
                combined = reviewed.setdefault(row["repo"], {"providers": set(), "files": set(), "bases": set()})
                combined["providers"].update(row["providers"])
                combined["files"].update(row["files"])
                combined["bases"].add(row["base"])
        consumers = {row["repository"]: row for row in self.policy["consumers"]}
        self.assertEqual(set(consumers), set(reviewed))
        self.assertEqual(len(consumers), 10)
        self.assertEqual(sum(len(row["routes"]) for row in consumers.values()), 21)
        for name, row in consumers.items():
            self.assertEqual(pz.github_identity(row["url"]), ("lightjunction", name))
            self.assertEqual({provider for route in row["routes"] for provider in route["providers"]},
                             set(reviewed[name]["providers"]))
            for route in row["routes"]:
                self.assertIn(route["path"], reviewed[name]["files"])
                self.assertTrue(rust.production_path(route["path"], generated=row["generated_paths"]))
                reference = route.get("reference_path", route["path"])
                self.assertIn(reference, reviewed[name]["files"])
                self.assertTrue(rust.production_path(reference, generated=row["generated_paths"]))
                self.assertNotIn("..", Path(reference).parts)
            for path, reason in row["generated_paths"].items():
                self.assertTrue(reason.strip())
                self.assertFalse(Path(path).is_absolute())
                self.assertNotIn("..", Path(path).parts)
        self.assertEqual({r["source"]["repository"] for r in self.policy["historical_bodies"]}, set(reviewed))
        for record in self.policy["historical_bodies"]:
            source = record["source"]
            if source["repository"] == "ssmcp":
                self.assertEqual(source["commit"], "1388cf11458eb88618ceedd4be8194d9ec026277")
                self.assertIn("Immediate parent", source["note"])
            else:
                self.assertIn(source["commit"], reviewed[source["repository"]]["bases"])
            self.assertRegex(source["file_sha256"], r"^[0-9a-f]{64}$")

    def test_all_real_historical_fragments_are_detected_with_exact_provenance(self):
        self.assertEqual(len(self.policy["historical_bodies"]), 34)
        for record in self.policy["historical_bodies"]:
            with self.subTest(record=record["id"]):
                fragment, function = historical_fragment(record)
                self.assertEqual(hashlib.sha256(fragment.encode()).hexdigest(), record["fragment_sha256"])
                for field in ("tokens", "body_sha256", "identifiers_sha256"):
                    self.assertEqual(function[field], record[field])
                self.assertTrue(list(shared.historical_matches(fragment, self.policy)))

    def test_function_and_simple_binding_renames_do_not_hide_history(self):
        record = next(row for row in self.policy["historical_bodies"] if row["id"] == "ztty-hex")
        fragment, original = historical_fragment(record)
        renamed = re.sub(r"\bbytes\b", "payload", fragment)
        renamed = re.sub(r"\bout\b", "encoded", renamed).replace("fn hex(", "fn local_adapter(")
        renamed = renamed.replace("\n", "\n /* changed formatting */ ")
        function = next(rust.functions(renamed))
        self.assertNotEqual(function["body_sha256"], original["body_sha256"])
        self.assertEqual(function["identifiers_sha256"], original["identifiers_sha256"])
        self.assertTrue(list(shared.historical_matches(renamed, self.policy)))

    def test_operations_calls_fields_paths_and_literals_remain_distinct(self):
        original = 'fn run(input: &[u8]) { let out = adapter::encode(input); out.push("protocol"); out.field + 2 }'
        expected = next(rust.functions(original))["identifiers_sha256"]
        for changed in (original.replace("+ 2", "- 2"), original.replace("2", "3"),
                        original.replace("encode", "decode"), original.replace("push", "append"),
                        original.replace("adapter::", "other::"), original.replace(".field", ".different"),
                        original.replace('"protocol"', '"different"')):
            with self.subTest(changed=changed):
                self.assertNotEqual(next(rust.functions(changed))["identifiers_sha256"], expected)

    def test_retained_real_adapters_md5_and_small_wrappers_are_legal(self):
        text = (FIXTURES / "retained_adapters.rs").read_text(encoding="utf-8")
        self.assertEqual(len(list(rust.functions(text))), 14)
        self.assertEqual(list(shared.historical_matches(text, self.policy)), [])

        # Similar short wrapper shapes are not evidence of a returned algorithm.
        text = '''
fn first(input: &[u8]) -> String { provider::encode(input) }
fn second(input: &[u8]) -> String { protocol::validate(input) }
fn digit(byte: u8) -> bool { matches!(byte, b'0'..=b'9' | b'a'..=b'f') }
'''
        self.assertEqual(list(shared.historical_matches(text, self.policy)), [])

    def test_shorthand_field_names_are_not_normalized_as_local_variables(self):
        first = "fn run(field: u8) { Record { field } }"
        other = "fn run(different: u8) { Record { different } }"
        self.assertNotEqual(next(rust.functions(first))["identifiers_sha256"],
                            next(rust.functions(other))["identifiers_sha256"])

    def test_retained_contract_adapters_parsers_and_token_owner_policy_are_legal(self):
        proof = contract_proof()
        self.assertEqual(len(proof["retained_functions"]), 18)
        text = (FIXTURES / "retained_contracts.rs").read_text(encoding="utf-8")
        # Identity::current includes its original nested TokenOwner query helper.
        self.assertEqual(len(list(rust.functions(text))), 19)
        self.assertEqual(list(shared.historical_matches(text, self.policy)), [])
        for record in proof["retained_functions"]:
            with self.subTest(repository=record["repository"], function=record["function"]):
                fragment, _ = retained_fragment(record)
                self.assertEqual(hashlib.sha256(fragment.encode()).hexdigest(), record["fragment_sha256"])
        self.assertEqual({record["function"] for record in proof["retained_functions"]
                          if record["repository"] == "ssmcp"}, {"current", "verify_private"})


class LexicalBoundaries(unittest.TestCase):
    def test_array_signatures_do_not_stop_at_type_semicolons(self):
        text = "fn compress(s: &mut [u32; 8], block: &[u8; 64]) -> [u8; 32] { [0; 32] }"
        self.assertEqual([f["name"] for f in rust.functions(text)], ["compress"])

    def test_nested_comments_raw_strings_chars_and_doc_text_are_not_code(self):
        text = '''/* outer /* fn hidden() {} */ comment */
const S: &str = r##"#[cfg(test)] fn hidden() { zhex::encode_lower(x,y); }"##;
const B: &[u8] = br#"fn byte_hidden() { zhex::encode_lower(x,y); }"#;
const C: &[u8] = b"zhex::encode_lower(x,y) /* not a comment */";
fn kept() { let marker = b'}'; let quote = '\\''; }
'''
        self.assertEqual([f["name"] for f in rust.functions(text)], ["kept"])
        self.assertEqual(shared.provider_references(rust.production_tokens(text), "zhex"), set())

    def test_nested_and_stacked_test_attributes_exclude_only_test_items(self):
        text = '''
#[cfg(test)] #[cfg_attr(any(), allow({ tokens }))]
mod tests { fn hidden() { fn nested() {} } }
#[test] fn direct_test() {}
mod inner { #![cfg(test)] fn hidden_inner() {} }
#[cfg(all(windows, test))] fn both() {}
#[cfg(any(windows, test))] fn platform() {}
#[cfg(not(test))] fn production() {}
#[cfg(feature = "test")] fn feature_is_not_test() {}
#[cfg_attr(test, ignore)] fn conservative_cfg_attr() {}
#[cfg(test)] mod external_tests;
fn trailing() {}
'''
        self.assertEqual([f["name"] for f in rust.functions(text)],
                         ["platform", "production", "feature_is_not_test", "conservative_cfg_attr", "trailing"])
        self.assertEqual(list(rust.functions("#![cfg(test)] fn hidden() {}")), [])

    def test_imports_alone_and_unrelated_namespaces_do_not_count(self):
        text = '''use zhex::encode_lower as encode;
// zhex::encode_lower(bytes, out)
fn run() { let s = "zhex::encode_lower"; other::encode(x, y); object.encode(x); }
#[cfg(test)] fn only_test() { encode(x, y); }
'''
        self.assertEqual(shared.provider_references(rust.production_tokens(text), "zhex"), set())

    def test_explicit_import_aliases_nested_use_trees_and_function_values(self):
        cases = [
            ('use zhex::{self as hex, encode_lower as enc}; fn run() { enc(x,y); hex::decode(x,y); }', "zhex", {"encode_lower", "decode"}),
            ('use sha2 as hash; use hash::{Digest, Sha256 as Hash}; fn run() { Hash::digest(x); }', "sha2", {"Sha256::digest"}),
            ('extern crate zhex as hex; fn run() { let encoder = hex::encode_lower; }', "zhex", {"encode_lower"}),
            ('use {zhex::{encode_lower as enc}, other::Thing}; fn run() { enc(x,y); }', "zhex", {"encode_lower"}),
        ]
        for text, crate, expected in cases:
            with self.subTest(text=text):
                self.assertEqual(shared.provider_references(rust.production_tokens(text), crate), expected)


class GateIntegration(FilesystemFixture):
    def setUp(self):
        super().setUp()
        self.policy = shared.load_policy()
        self.data = catalog(package("ssmcp", deps=[dependency("zhex", explicit=False)]))
        self.data["repositories"][0]["url"] = "https://github.com/LIghtJUNction/ssmcp.git"
        self.dep = self.data["packages"][0]["dependencies"][0]
        self.dep["source"] = self.policy["provider_sources"]["zhex"]
        self.write("ssmcp/src/hex.rs", GOOD_HEX)
        self.repo = self.root / "ssmcp"
        pz.command(["git", "init", "--quiet"], self.repo)
        self.track()

    def track(self):
        pz.command(["git", "add", "--all"], self.repo)

    def errors(self):
        return shared.errors(self.data, self.root, command=pz.command, relative=pz.relative,
                             identity=pz.github_identity, policy=self.policy)

    def test_validate_uses_the_same_gate_for_a_registered_consumer(self):
        self.assertEqual(pz.validate(self.data, {}, self.root), [])
        self.write("ssmcp/src/hex.rs", "use zhex::encode_lower; fn encode() {}")
        errors = pz.validate(self.data, {}, self.root)
        self.assertTrue(any("provider reference missing" in error for error in errors), errors)

    def test_only_registered_identity_is_required_no_full_ten_repo_fixture(self):
        self.assertEqual(self.errors(), [])
        self.data["repositories"][0]["url"] = "https://github.com/ProjectZTests/ssmcp.git"
        self.write("ssmcp/src/hex.rs", "fn unrelated() {}")
        self.assertEqual(self.errors(), [])

    def test_dev_build_missing_or_replacement_provider_dependency_fails(self):
        for kind in ("dev", "build"):
            with self.subTest(kind=kind):
                self.dep["kind"] = kind
                self.assertTrue(any("normal dependency" in error for error in self.errors()))
        self.dep["kind"] = "normal"
        self.dep["source"] = "registry+https://github.com/rust-lang/crates.io-index"
        self.assertTrue(any("normal dependency" in error for error in self.errors()))
        self.data["packages"][0]["dependencies"] = []
        self.assertTrue(any("normal dependency" in error for error in self.errors()))

    def test_optional_platform_normal_dependency_and_alias_are_valid(self):
        self.dep.update(alias="hex-codec", optional=True, target='cfg(target_os = "windows")')
        self.write("ssmcp/src/hex.rs", GOOD_HEX.replace("zhex::", "hex_codec::"))
        self.assertEqual(self.errors(), [])

    def test_unused_accepted_dependency_cannot_borrow_another_source_alias(self):
        trusted = dependency("sha2")
        trusted["source"] = self.policy["provider_sources"]["sha2"]
        untrusted = dependency("sha2")
        untrusted.update(alias="other_hash", source="git+https://github.com/ProjectZTests/sha2.git")
        contracts = [dependency(name, explicit=False) for name in ("zconv", "zsys")]
        for dep in contracts:
            dep["source"] = self.policy["provider_sources"][dep["name"]]
        self.data = catalog(package("zcall-gui", manifest="ssmcp/Cargo.toml",
                                    deps=[trusted, untrusted, self.dep, *contracts]))
        self.data["packages"][0]["workspace"] = "ssmcp"
        self.data["repositories"][0].update(path="ssmcp", url="https://github.com/LIghtJUNction/zcall-gui.git")
        source = "fn digest(input: &[u8], out: &mut [u8]) { zhex::encode_lower(&other_hash::Sha256::digest(input), out).unwrap(); }"
        self.write("ssmcp/src/updater.rs", source)
        self.write("ssmcp/src/json.rs", retained_source("zcall-gui", "src/json.rs"))
        self.write("ssmcp/src/core_install_windows.rs", retained_source("zcall-gui", "src/core_install_windows.rs"))
        self.track()
        for errors in (self.errors(), pz.validate(self.data, {}, self.root)):
            self.assertTrue(any("provider reference missing: sha2::Sha256" in error for error in errors), errors)
        self.write("ssmcp/src/updater.rs", source.replace("other_hash::", "sha2::"))
        self.assertEqual(pz.validate(self.data, {}, self.root), [])

    def test_provider_type_mode_import_comments_and_tests_are_insufficient(self):
        for source in (
                "use zhex::encode_lower; fn run() {}",
                '// zhex::encode_lower\nfn run() { let s = "zhex::encode_lower"; }',
                "#[cfg(test)] mod tests { " + GOOD_HEX + " }",
                "fn run() { let mode = zhex::Mode::Lower; }",
        ):
            with self.subTest(source=source):
                self.write("ssmcp/src/hex.rs", source)
                self.assertTrue(any("provider reference missing" in error for error in self.errors()))

    def test_removed_route_untracked_route_and_missing_owner_are_diagnostics(self):
        pz.command(["git", "rm", "--cached", "src/hex.rs"], self.repo)
        self.assertTrue(any("untracked or excluded" in error for error in self.errors()))
        self.track()
        self.data["packages"] = []
        self.assertTrue(any("no owning catalog package" in error for error in self.errors()))
        (self.repo / "src/hex.rs").unlink()
        self.assertTrue(any("cannot inspect" in error for error in self.errors()))

    def test_history_fails_even_with_valid_provider_and_another_file_name(self):
        body = (FIXTURES / "ztty.rs").read_text(encoding="utf-8")
        self.write("ssmcp/src/renamed.rs", body)
        self.track()
        errors = self.errors()
        self.assertEqual(len(errors), 4, errors)
        self.assertTrue(all("shared-implementation history" in error for error in errors))
        self.assertTrue(all("ssmcp/src/renamed.rs:" in error for error in errors))

    def test_dependency_reference_and_history_failures_are_independent(self):
        self.write("ssmcp/src/hex.rs", (FIXTURES / "ssmcp.rs").read_text(encoding="utf-8"))
        self.data["packages"][0]["dependencies"] = []
        errors = self.errors()
        for marker in ("shared-implementation history", "normal dependency", "provider reference missing"):
            self.assertTrue(any(marker in error for error in errors), errors)

    def test_test_vendor_and_reference_paths_are_excluded(self):
        body = (FIXTURES / "ssmcp.rs").read_text(encoding="utf-8")
        for path in ("tests/oracle.rs", "vendor/copy.rs", "fixtures/independent.rs", "src/codec_test.rs", "build.rs"):
            self.write("ssmcp/" + path, body)
        self.write("ssmcp/src/reference.rs", "#[cfg(test)] mod oracle {\n" + body + "\n}")
        self.track()
        self.assertEqual(self.errors(), [])

    def test_generated_marker_and_generated_directory_cannot_hide_history(self):
        body = "// @generated DO NOT EDIT\n" + (FIXTURES / "ssmcp.rs").read_text(encoding="utf-8")
        self.write("ssmcp/src/generated/copy.rs", body)
        self.track()
        self.assertTrue(any("shared-implementation history" in error for error in self.errors()))
        consumer = next(row for row in self.policy["consumers"] if row["repository"] == "ssmcp")
        consumer["generated_paths"]["src/generated/copy.rs"] = "Test-only demonstration of an explicitly reviewed generated path."
        self.assertEqual(self.errors(), [])

    def test_tracked_symlink_cannot_read_outside_the_consumer(self):
        target = self.write("outside.rs", "fn outside() {}")
        (self.repo / "src/link.rs").symlink_to(target)
        self.track()
        self.assertTrue(any("path escapes coordination checkout" in error for error in self.errors()))


class ContractRoutes(FilesystemFixture):
    def setUp(self):
        super().setUp()
        self.policy = shared.load_policy()

    def normal(self, name):
        dep = dependency(name, explicit=False)
        dep["source"] = self.policy["provider_sources"][name]
        return dep

    def consumer(self, name, paths, packages, sources):
        consumer = next(row for row in self.policy["consumers"] if row["repository"] == name)
        consumer["routes"] = [route for route in consumer["routes"] if route["path"] in paths]
        self.assertEqual({route["path"] for route in consumer["routes"]}, set(paths))
        self.policy["consumers"] = [consumer]
        self.data = catalog(*packages)
        self.data["repositories"][0]["url"] = consumer["url"]
        self.repo = self.root / name
        self.repo.mkdir(exist_ok=True)
        pz.command(["git", "init", "--quiet"], self.repo)
        for path, source in sources.items():
            self.write(name + "/" + path, source)
        self.track()
        return consumer["routes"]

    def track(self):
        pz.command(["git", "add", "--all"], self.repo)

    def errors(self):
        return shared.errors(self.data, self.root, command=pz.command, relative=pz.relative,
                             identity=pz.github_identity, policy=self.policy)

    def json_route(self, indirect=False):
        name = "zuse" if indirect else "zmem"
        entry = "src/platform/mod.rs" if indirect else "src/json.rs"
        dep = self.normal("zconv")
        dep["optional"] = True
        sources = {"src/json.rs": retained_source(name, "src/json.rs")}
        if indirect:
            sources[entry] = retained_source(name, entry)
        routes = self.consumer(name, [entry], [package(name, deps=[dep])], sources)
        return routes[0], dep

    def privacy_route(self, name="zcall-gui"):
        path = "src/core_install_windows.rs" if name == "zcall-gui" else "src/privacy_windows.rs"
        dep = self.normal("zsys")
        dep["target"] = "cfg(windows)"
        routes = self.consumer(name, [path], [package(name, deps=[dep])],
                               {path: retained_source(name, path)})
        return routes[0], dep

    def test_json_requires_writer_constructor_and_unicode_policy_in_production(self):
        self.json_route()
        self.assertEqual(self.errors(), [])
        good = retained_source("zmem", "src/json.rs")
        for source in (
                "use zconv::json::{Writer, ControlEscapes}; fn quote() {}",
                "fn quote() { let policy = zconv::json::ControlEscapes::Unicode; }",
                good.replace("ControlEscapes::Unicode", "ControlEscapes::Short"),
                "#[cfg(test)] mod tests {\n" + good + "\n}",
        ):
            with self.subTest(source=source[:80]):
                self.write("zmem/src/json.rs", source)
                self.assertTrue(self.errors())

    def test_json_and_privacy_require_normal_canonical_sources(self):
        for provider in ("zconv", "zsys"):
            with self.subTest(provider=provider):
                self.policy = shared.load_policy()
                _, dep = self.json_route() if provider == "zconv" else self.privacy_route()
                self.assertEqual(self.errors(), [])
                original = dict(dep)
                for changes in ({"kind": "dev"}, {"kind": "build"},
                                {"source": "registry+https://github.com/rust-lang/crates.io-index"},
                                {"path": "replacement"}):
                    dep.update(changes)
                    self.assertTrue(any("normal dependency" in error for error in self.errors()))
                    dep.clear()
                    dep.update(original)

    def test_untrusted_aliases_cannot_supply_json_or_privacy_references(self):
        for provider in ("zconv", "zsys"):
            with self.subTest(provider=provider):
                self.policy = shared.load_policy()
                route, dep = self.json_route() if provider == "zconv" else self.privacy_route()
                replacement = dict(dep, alias="other_provider", source=f"git+https://github.com/ProjectZTests/{provider}.git")
                self.data["packages"][0]["dependencies"].append(replacement)
                path = self.repo / route["path"]
                path.write_text(path.read_text().replace(provider + "::", "other_provider::"))
                self.assertTrue(any("provider reference missing" in error for error in self.errors()))

    def test_reference_paths_reject_nonproduction_untracked_and_noncanonical_files(self):
        route, _ = self.json_route(indirect=True)
        self.assertEqual(self.errors(), [])
        good = retained_source("zuse", "src/json.rs")
        for name in ("vendor/json.rs", "tests/json.rs", "src/json_test.rs", "src/json.txt"):
            self.write("zuse/" + name, good)
        (self.repo / "src/vendor_alias.rs").symlink_to(self.repo / "vendor/json.rs")
        self.write("zuse/src/test_only.rs", "#![cfg(test)]\n" + good)
        self.write("zuse/src/only_oracles.rs", "#[cfg(test)] mod tests {\n" + good + "\n}")
        self.track()
        self.write("zuse/src/untracked.rs", good)
        for reference in ("/outside.rs", "../outside.rs", "src/../src/json.rs", "C:/outside.rs", "C:\\outside.rs", "", None,
                          "vendor/json.rs", "tests/json.rs", "src/json_test.rs", "src/json.txt", "src/vendor_alias.rs", "src/test_only.rs",
                          "src/only_oracles.rs", "src/untracked.rs", "src/missing.rs"):
            with self.subTest(reference=reference):
                route["reference_path"] = reference
                self.assertTrue(any("reference path" in error or "reference source" in error for error in self.errors()))

    def test_reference_path_cannot_cross_a_tracked_symlink(self):
        route, _ = self.json_route(indirect=True)
        outside = self.write("outside.rs", retained_source("zuse", "src/json.rs"))
        (self.repo / "src/link.rs").symlink_to(outside)
        self.track()
        route["reference_path"] = "src/link.rs"
        self.assertTrue(any("path escapes coordination checkout" in error for error in self.errors()))

    def test_reference_path_does_not_recurse_into_nested_gitlinks(self):
        route, _ = self.json_route(indirect=True)
        nested = self.repo / "embedded"
        self.write("zuse/embedded/src/json.rs", retained_source("zuse", "src/json.rs"))
        pz.command(["git", "init", "--quiet"], nested)
        pz.command(["git", "add", "--all"], nested)
        pz.command(["git", "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                    "commit", "--quiet", "-m", "fixture"], nested)
        self.track()
        route["reference_path"] = "embedded/src/json.rs"
        self.assertTrue(any("reference source" in error for error in self.errors()))

    def test_installer_shared_source_requires_its_own_normal_dependency(self):
        installer = "crates/zcalld-installer/src/private.rs"
        shared_path = "src/privacy_windows.rs"
        daemon_dep, installer_dep = self.normal("zsys"), self.normal("zsys")
        installer_dep["target"] = "cfg(windows)"
        self.consumer("zcalld", [shared_path, installer], [
            package("zcalld", deps=[daemon_dep]),
            package("zcalld-installer", repo="zcalld", manifest="zcalld/crates/zcalld-installer/Cargo.toml", deps=[installer_dep]),
        ], {shared_path: retained_source("zcalld", shared_path),
            installer: '#[cfg(windows)] #[path="../../../src/privacy_windows.rs"] mod privacy_windows;\n'})
        self.assertEqual(self.errors(), [])
        self.data["packages"][1]["dependencies"] = []
        errors = self.errors()
        self.assertTrue(any("normal dependency" in error and "crates/zcalld-installer/Cargo.toml" in error for error in errors), errors)
        self.assertFalse(any(error.startswith("zcalld/src/privacy_windows.rs:") for error in errors), errors)

    def test_windows_inheritance_policies_remain_distinct(self):
        for name, expected, wrong in (("zcall-gui", "ObjectOnly", "FilesAndDirectories"),
                                   ("zcalld", "FilesAndDirectories", "ObjectOnly")):
            with self.subTest(repository=name):
                self.policy = shared.load_policy()
                route, _ = self.privacy_route(name)
                self.assertEqual(self.errors(), [])
                path = self.repo / route["path"]
                path.write_text(path.read_text().replace("DirectoryInheritance::" + expected, "DirectoryInheritance::" + wrong))
                self.assertTrue(any("DirectoryInheritance::" + expected in error for error in self.errors()))

    def test_real_json_and_acl_bodies_fail_even_with_valid_provider_routes(self):
        self.json_route()
        records = {row["id"]: row for row in self.policy["historical_bodies"]}
        bodies = [historical_fragment(records[name])[0] for name in ("zmem-json-quote", "zcall-gui-windows-check_private")]
        self.write("zmem/src/restored.rs", "#[cfg(windows)] mod restored {\n" + "\n".join(bodies) + "\n}")
        self.track()
        errors = self.errors()
        self.assertEqual(len(errors), 2, errors)
        self.assertTrue(all("shared-implementation history" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
