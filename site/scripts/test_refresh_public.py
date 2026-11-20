#!/usr/bin/env python3
"""Focused CLI tests for the public snapshot refresh."""
from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import build
import refresh_public


CATEGORIES = [{"id": "data", "label": "数据", "english": "DATA"}]
OWNER = refresh_public.OWNER
VERSION = "1.2.3"
CHECKSUM = "a" * 64


def curated(name):
    return {"id": name, "category": "data", "kind": "library", "summary": name, "package": name}


def public_responses(*names, **overrides):
    responses = {}
    for name in names:
        repo = f"{OWNER}/{name}"
        raw = f"https://raw.githubusercontent.com/{repo}/main/"
        registry = f"https://crates.io/api/v1/crates/{name}"
        version = {"num": VERSION, "yanked": False, "checksum": CHECKSUM}
        responses.update({
            f"https://api.github.com/repos/{repo}": (200, json.dumps({
                "private": False, "visibility": "public", "archived": False,
                "full_name": repo, "default_branch": "main",
            })),
            raw + "README.md": (200, f"# {name}\n"),
            raw + "Cargo.toml": (200, f'[package]\nname = "{name}"\nversion = "1.2.4"\n'),
            raw + "VERSION": (404, ""),
            registry: (200, json.dumps({
                "crate": {"repository": f"https://github.com/{repo}", "default_version": VERSION},
                "versions": [version],
            })),
            f"{registry}/{VERSION}": (200, json.dumps({"version": version})),
        })
    responses.update(overrides)
    return responses.__getitem__


class RefreshCliTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix="project-z-refresh-test-")
        self.addCleanup(directory.cleanup)
        self.site = Path(directory.name)
        self.snapshot = self.site / "projects.json"
        self.write_curation("zold", "zother")
        with patch.object(refresh_public, "request", side_effect=public_responses("zold", "zother")):
            projects = [refresh_public.refresh(curated(name)) for name in ("zother", "zold")]
        self.data = {
            "schema_version": 1, "generated_at": "2026-11-20T00:00:00+00:00",
            "categories": CATEGORIES, "projects": projects,
        }
        self.snapshot.write_text(json.dumps(self.data) + "\n")
        self.before = self.snapshot.read_bytes()

    def write_curation(self, *names):
        self.curation = {"schema_version": 1, "categories": CATEGORIES, "projects": [curated(name) for name in names]}
        (self.site / "curation.json").write_text(json.dumps(self.curation))

    def run_cli(self, *args, responses=None):
        with (
            patch.object(refresh_public, "SITE", self.site),
            patch.object(sys, "argv", ["refresh_public.py", *args]),
            patch.object(refresh_public, "request", side_effect=responses) as requests,
            redirect_stdout(io.StringIO()),
            redirect_stderr(io.StringIO()),
        ):
            try:
                refresh_public.main()
            finally:
                self.requests = requests

    def assert_snapshot_unchanged(self):
        self.assertEqual(self.snapshot.read_bytes(), self.before)
        self.assertFalse(self.snapshot.with_suffix(".json.tmp").exists())

    def test_only_appends_new_reviewed_project_without_placeholder(self):
        self.write_curation("znew", "zold", "zother")
        self.run_cli("--only", "znew", responses=public_responses("znew"))
        data = json.loads(self.snapshot.read_text())
        self.assertEqual(data["projects"][:2], self.data["projects"])
        new = data["projects"][2]
        self.assertEqual(new["id"], "znew")
        self.assertEqual(new["source_version"]["version"], "1.2.4")
        self.assertEqual(new["crate"]["version"], VERSION)
        self.assertEqual(new["crate"]["checksum"], CHECKSUM)
        build.validate(data, self.curation)
        self.run_cli("--verify-only", responses=public_responses("znew", "zold", "zother"))

    def test_default_refresh_appends_all_new_projects_in_curation_order(self):
        self.write_curation("zlast", "zother", "zfirst", "zold")
        self.run_cli(responses=public_responses("zlast", "zother", "zfirst", "zold"))
        data = json.loads(self.snapshot.read_text())
        self.assertEqual([item["id"] for item in data["projects"]], ["zother", "zold", "zlast", "zfirst"])
        build.validate(data, self.curation)

    def test_incomplete_only_selection_and_verify_only_fail_before_requests(self):
        self.write_curation("znew", "zextra", "zold", "zother")
        for args, error, message in [
            (("--only", "znew"), SystemExit, None),
            (("--verify-only",), ValueError, "exactly the reviewed projects"),
        ]:
            with self.subTest(args=args):
                with self.assertRaises(error) as raised:
                    self.run_cli(*args)
                if message:
                    self.assertIn(message, str(raised.exception))
                self.requests.assert_not_called()
                self.assert_snapshot_unchanged()

    def test_unknown_selection_fails_before_requests(self):
        with self.assertRaises(SystemExit):
            self.run_cli("--only", "zunknown")
        self.requests.assert_not_called()
        self.assert_snapshot_unchanged()

    def test_rejects_invalid_existing_rows_before_requests(self):
        self.write_curation("znew", "zold", "zother")
        for rows, message in [
            ([{**self.data["projects"][0], "id": "zforeign"}], "duplicate or unreviewed"),
            ([self.data["projects"][0]] * 2, "duplicate or unreviewed"),
            ([{**self.data["projects"][0], "private_path": "extra"}], "unexpected public project fields"),
        ]:
            with self.subTest(message=message):
                self.before = json.dumps({**self.data, "projects": rows}).encode()
                self.snapshot.write_bytes(self.before)
                with self.assertRaisesRegex(ValueError, message):
                    self.run_cli("--only", "znew")
                self.requests.assert_not_called()
                self.assert_snapshot_unchanged()

    def test_public_evidence_failures_preserve_snapshot(self):
        self.write_curation("zold", "znew", "zother")
        repo = f"https://api.github.com/repos/{OWNER}/znew"
        crate = "https://crates.io/api/v1/crates/znew"
        registry = public_responses("znew")(crate)
        invalid_checksum = json.loads(registry[1])
        invalid_checksum["versions"][0]["checksum"] = "invalid"

        def forbidden(url):
            if url == repo:
                raise RuntimeError("public source returned HTTP 403: " + url)
            return public_responses("zold")(url)

        cases = [
            (forbidden, RuntimeError, "HTTP 403"),
            (public_responses("zold", "znew", **{repo: (200, '{"private":true}')}),
             ValueError, "not active and public"),
            (public_responses("zold", "znew", **{crate: (200, "{")}),
             json.JSONDecodeError, "Expecting property name"),
            (public_responses("zold", "znew", **{crate: (200, json.dumps(invalid_checksum))}),
             ValueError, "missing registry checksum"),
        ]
        for responses, error, message in cases:
            with self.subTest(message=message):
                with self.assertRaisesRegex(error, message):
                    self.run_cli("--only", "zold", "znew", responses=responses)
                self.assert_snapshot_unchanged()

    def test_foreign_crate_name_keeps_new_public_source_only(self):
        self.write_curation("zold", "zother", "znew")
        registry = "https://crates.io/api/v1/crates/znew"
        foreign_repo = "https://github.com/other/znew"
        _, body = public_responses("znew")(registry)
        metadata = json.loads(body)
        metadata["crate"]["repository"] = foreign_repo
        responses = public_responses("znew", **{registry: (200, json.dumps(metadata))})
        self.run_cli("--only", "znew", responses=responses)

        data = json.loads(self.snapshot.read_text())
        self.assertEqual(data["projects"][:2], self.data["projects"])
        new = data["projects"][2]
        self.assertEqual(new["id"], "znew")
        self.assertIsNone(new["crate"])
        self.assertEqual(new["crate_lookup"]["status"], "repository_mismatch")
        build.validate(data, self.curation)
        page = build.render(data)
        self.assertIn('data-project="znew"', page)
        card = page.split('data-project="znew"', 1)[1].split("</li>", 1)[0]
        self.assertIn(f'href="https://github.com/{OWNER}/znew"', card)
        self.assertNotIn("crates.io", card)
        self.assertNotIn(foreign_repo, page)

    def test_established_subset_refresh_leaves_other_row_and_order_intact(self):
        source = f"https://raw.githubusercontent.com/{OWNER}/zold/main/Cargo.toml"
        responses = public_responses("zold", **{source: (200, '[package]\nversion = "1.2.5"\n')})
        self.run_cli("--only", "zold", responses=responses)
        data = json.loads(self.snapshot.read_text())
        self.assertEqual(data["projects"][0], self.data["projects"][0])
        self.assertEqual(data["projects"][1]["id"], "zold")
        self.assertEqual(data["projects"][1]["source_version"]["version"], "1.2.5")
        build.validate(data, self.curation)


if __name__ == "__main__":
    unittest.main()
