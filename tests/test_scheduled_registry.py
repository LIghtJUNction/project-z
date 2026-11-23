"""Recover a two-crate release using the real Cargo client and a loopback registry."""
from functools import partial
import hashlib
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
from threading import Thread
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import scheduled_registry as registry


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


class RegistryRecovery(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        server = ThreadingHTTPServer(("127.0.0.1", 0), partial(Handler, directory=str(self.root)))
        self.addCleanup(server.server_close)
        worker = Thread(target=server.serve_forever, daemon=True)
        worker.start()
        self.addCleanup(worker.join)
        self.addCleanup(server.shutdown)
        url = f"http://127.0.0.1:{server.server_port}"
        (self.root / "config.json").write_text(json.dumps({"dl": url + "/archives/{crate}/{version}.crate"}))
        self.config = f'[source.crates-io]\nreplace-with="fixture"\n[source.fixture]\nregistry="sparse+{url}/"\n'

    def archive(self, name, deps):
        version = "0.2.1"
        sha = hashlib.sha1(name.encode()).hexdigest()
        repo = "https://github.com/test/" + name
        manifest = f'[package]\nname="{name}"\nversion="{version}"\nedition="2024"\nrepository="{repo}"\n[dependencies]\n'
        manifest += "".join(f'{dep}="={version}"\n' for dep in deps)
        content = io.BytesIO()
        with tarfile.open(fileobj=content, mode="w:gz") as archive:
            for filename, data in [("Cargo.toml", manifest), ("src/lib.rs", ""),
                                   (".cargo_vcs_info.json", json.dumps({"git": {"sha1": sha}}))]:
                entry = tarfile.TarInfo(f"{name}-{version}/{filename}")
                data = data.encode()
                entry.size = len(data)
                archive.addfile(entry, io.BytesIO(data))
        payload = content.getvalue()
        checksum = hashlib.sha256(payload).hexdigest()
        path = self.root / "archives" / name / f"{version}.crate"
        path.parent.mkdir(parents=True)
        path.write_bytes(payload)
        receipt = dict(package=name, version=version, github=repo, git_sha=sha, archive_sha256=checksum)
        index = {"name": name, "vers": version, "cksum": checksum, "yanked": False, "features": {},
                 "deps": [dict(name=dep, req="=" + version, features=[], optional=False, default_features=True,
                               target=None, kind="normal") for dep in deps]}
        return receipt, index

    def test_partial_failure_replays_exact_versions_and_verified_archives(self):
        up, up_index = self.archive("fixture-up", [])
        down, down_index = self.archive("fixture-down", ["fixture-up"])
        receipt_file = self.root / "docs/registry-receipts.json"
        receipt_file.parent.mkdir()
        receipt_file.write_text(json.dumps({"schema_version": 1, "receipts": [up, down]}))
        rules = ["[scheduled]", f'registry_receipts_sha256="{hashlib.sha256(receipt_file.read_bytes()).hexdigest()}"']
        packages, repos = [], []
        for receipt, deps in [(down, [up]), (up, [])]:
            name = receipt["package"]
            rules += [f"[registry_handoffs.{name}]", f'repository="test/{name}"', 'workflow="release.yml"',
                      'workflow_blob="' + "2"*40 + '"', 'crate_owner="test"']
            repos.append(dict(name=name, url=receipt["github"], commit=receipt["git_sha"], branch="main"))
            packages.append(dict(name=name, repository=name, publish=True, version=receipt["version"],
                                 dependencies=[dict(name=d["package"], kind="normal") for d in deps]))
        (self.root / "project-z.toml").write_text("\n".join(rules))
        data = dict(repositories=repos, packages=packages)
        plan = registry.child_targets(packages, data, self.root, audit=False)
        self.assertEqual([target["name"] for target in plan], ["fixture-up", "fixture-down"])
        self.assertEqual(plan[1]["prerequisites"], [up])
        frozen = json.dumps(plan)
        index = self.root / "fi/xt"
        index.mkdir(parents=True)
        attempts = []
        actual_run = subprocess.run
        actual_consume = registry.consume

        def local_registry(request):
            status = "present" if (index / request["name"]).exists() else "missing"
            return dict(status=status)

        def owner_workflow(args, **kwargs):
            if args[0] != "gh":
                return actual_run(args, **kwargs)
            name = next(arg.split("=", 1)[1] for arg in args if arg.startswith("package="))
            attempts.append(name)
            if attempts == ["fixture-up", "fixture-down"]:
                raise subprocess.CalledProcessError(1, args)
            receipt, row = (up, up_index) if name == "fixture-up" else (down, down_index)
            self.assertIn("archive_sha256=" + receipt["archive_sha256"], args)
            self.assertIn("version=0.2.1", args)
            self.assertFalse((index / name).exists())
            (index / name).write_text(json.dumps(row) + "\n")

        def replay():
            for target in json.loads(frozen):
                registry.publish_missing(target)

        with patch.object(registry, "eligible", return_value=True), \
             patch.object(registry, "registry_status", side_effect=local_registry), \
             patch.object(registry, "consume", side_effect=lambda r: actual_consume(r, self.config)) as consume, \
             patch.object(subprocess, "run", side_effect=owner_workflow):
            with self.assertRaises(subprocess.CalledProcessError):
                replay()
            self.assertTrue((index / "fixture-up").is_file())
            self.assertFalse((index / "fixture-down").exists())
            replay()
            replay()
            self.assertEqual(attempts, ["fixture-up", "fixture-down", "fixture-down"])
            self.assertGreaterEqual(consume.call_count, 6)
            with self.assertRaisesRegex(ValueError, "checksum"):
                registry.present({**up, "archive_sha256": "0"*64})
            self.assertEqual(len(attempts), 3)
