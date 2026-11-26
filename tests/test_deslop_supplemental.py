import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from deslop_supplemental import coverage_summary, plan


class SupplementalTests(unittest.TestCase):
    def test_all_eligible_covered_once(self):
        _, coverage = plan(ROOT, "smoke")
        selected = set()
        expect = {(r["repo"], r["manifest"]) for r in coverage if r["status"] == "not_selected"}
        self.assertEqual(len(coverage), 35)
        self.assertEqual(len(expect), 26)
        for i in range((len(expect) + 3) // 4):
            groups, rows = plan(ROOT, str(i))
            found = {(n, str(p)) for n, _, _, paths in groups for p in paths}
            self.assertEqual(len(rows), 35)
            self.assertTrue(0 < len(found) <= 4)
            self.assertFalse(found & selected)
            selected |= found
        self.assertEqual(selected, expect)
        with self.assertRaises(ValueError):
            plan(ROOT, "999")

    def test_followup_shards_exclude_smoke(self):
        smoke, inventory = plan(ROOT, "smoke")
        smoke_set = {(n, str(p)) for n, _, _, paths in smoke for p in paths}
        remaining = {(r["repo"], r["manifest"]) for r in inventory
                     if r["status"] == "not_selected"} - smoke_set
        self.assertEqual(len(remaining), 22)
        found = set()
        for i in range(6):
            groups, _ = plan(ROOT, f"remaining-{i}")
            shard = {(n, str(p)) for n, _, _, paths in groups for p in paths}
            self.assertTrue(0 < len(shard) <= 4)
            self.assertFalse(shard & (smoke_set | found))
            found |= shard
        self.assertEqual(found, remaining)

    def test_smoke_reports_failures_and_environment_hold(self):
        groups, coverage = plan(ROOT, "smoke")
        self.assertEqual([n for n, *_ in groups], ["bilibilive", "coolapk-cli", "emailctl", "markref"])
        row = dict(repo="bilibilive", manifest="Cargo.toml", status="tool_error", log="x.log", workspace=None)
        self.assertEqual(coverage_summary(coverage, [row]), dict(clean=0, findings=0, tool_error=1,
                                                                 environment_review=9, not_selected=25))

    def test_native_profile_is_bounded_and_host_is_pinned(self):
        groups, coverage = plan(ROOT, "native")
        self.assertEqual({(n, str(m)) for n, _, _, paths in groups for m in paths},
                         {("LightFlow", "Cargo.toml"), ("lightflow-rig", "Cargo.toml"),
                          ("magpie-rs-source", "apps/desktop/Cargo.toml")})
        with_context = [r for r in coverage if "context_host_commit" in r]
        self.assertEqual([(r["repo"], r["context_host_commit"]) for r in with_context],
                         [("lightflow-rig", "ba52a3cfdd234eeb0206d70d02e63c59aeb478c0")])
        self.assertEqual(next(r for r in coverage if r["repo"] == "lightflow-std")["status"],
                         "environment_review")

    def test_cannot_override_canonical_or_escape_manifest(self):
        for mutation in ("owner_overlap", "escape", "badsha"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as td:
                p = Path(td)
                (p / "docs").mkdir()
                (p / "catalog.json").write_text('{"schema_version":1,"repositories":[{"name":"zuse"}]}')
                name, sha, manifest = "example", "0"*40, "Cargo.toml"
                if mutation == "owner_overlap":
                    name = "ZuSe"
                elif mutation == "escape":
                    manifest = "../Cargo.toml"
                else:
                    sha = "main"
                payload = {"schema_version":1, "repositories":[{"name":name, "commit":sha,
                           "workspaces":[{"manifest":manifest,"validation":"unscanned_candidate"}]}]}
                (p / "docs/supplemental-rust-catalog.json").write_text(json.dumps(payload))
                with self.assertRaises(ValueError):
                    plan(p, "0")


if __name__ == "__main__":
    unittest.main()
