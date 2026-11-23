"""Capability checks and process-boundary behavior for optional build routing."""
from contextlib import redirect_stderr
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import managed_build as managed


def report(**changes):
    observation = dict(source="daemon_cache", daemon_active=True, stale=False,
                       instance_verification="proc_identity")
    observation.update(changes)
    return {"version": "0.2.0", "observation": observation}


class ManagedBuildTests(unittest.TestCase):
    def setUp(self):
        managed._selection.cache_clear()
        managed._notice.cache_clear()
        self.addCleanup(managed._selection.cache_clear)
        self.addCleanup(managed._notice.cache_clear)
        patches = [patch.dict(os.environ, {"ZMEM_BUILD_BACKGROUND": "1"}),
                   patch.object(managed.sys, "platform", "linux"),
                   patch.object(managed, "_candidates", return_value=["/installed/zmem"]),
                   patch.object(managed.shutil, "which", return_value="/usr/bin/systemctl"),
                   patch.object(managed.os, "access", return_value=True),
                   patch.object(managed.os, "geteuid", return_value=1000)]
        for item in patches:
            item.start()
            self.addCleanup(item.stop)
        self.stderr = io.StringIO()
        context = redirect_stderr(self.stderr)
        context.__enter__()
        self.addCleanup(context.__exit__, None, None, None)

    def probe(self, status=None, version="zmem 0.2.0", manager="262.2\n"):
        status = report() if status is None else status
        def read(argv):
            if argv[-1] == "--version":
                return version
            if argv[1:] == ["status", "--json"]:
                return json.dumps(status)
            return manager
        return patch.object(managed, "_probe", side_effect=read)

    def test_verified_daemon_prefix_preserves_arguments_and_probes_once(self):
        command = ["cargo", "test", "--manifest-path", "a path/Cargo.toml", "--", "--nocapture"]
        with self.probe() as probe:
            result = managed.background_command(command)
            self.assertEqual(managed.background_command(command), result)
        self.assertEqual(result, ["/installed/zmem", "run", "--class", "background", "--", *command])
        self.assertEqual(command[0], "cargo")
        self.assertEqual(probe.call_count, 3)
        self.assertIn("--user", probe.call_args.args[0])
        self.assertEqual(self.stderr.getvalue().count("build memory:"), 1)

    def test_old_cli_cannot_claim_new_daemon_capabilities(self):
        with self.probe(version="zmem 0.1.2") as probe:
            self.assertEqual(managed.background_command(["cargo", "check"]), ["cargo", "check"])
        self.assertEqual(probe.call_count, 1)

    def test_invalid_or_stale_provenance_falls_back_without_classification(self):
        statuses = [None, {}, report(source="independent_live"), report(stale=True),
                    report(daemon_active=False), report(instance_verification="legacy_age"),
                    {**report(), "version": "0.1.2"}, {**report(), "observation": []}]
        for status in statuses:
            with self.subTest(status=status):
                managed._selection.cache_clear()
                with patch.object(managed, "_probe", side_effect=["zmem 0.2.0", json.dumps(status)]):
                    self.assertEqual(managed.background_command(["cargo", "build"]), ["cargo", "build"])

    def test_absent_user_manager_does_not_prevent_build(self):
        with self.probe(manager=None):
            self.assertEqual(managed.background_command(["cargo", "check"]), ["cargo", "check"])
        self.assertIn("manager for this caller is unavailable", self.stderr.getvalue())

    def test_root_checks_system_manager(self):
        with patch.object(managed.os, "geteuid", return_value=0), self.probe() as probe:
            self.assertNotEqual(managed.background_command(["cargo", "check"])[0], "cargo")
        self.assertNotIn("--user", probe.call_args.args[0])

    def test_optout_nonlinux_and_nonbuild_commands_never_probe(self):
        with patch.object(managed, "_probe", side_effect=AssertionError("unexpected probe")):
            with patch.dict(os.environ, {"ZMEM_BUILD_BACKGROUND": "0"}):
                self.assertEqual(managed.background_command(["cargo", "build"]), ["cargo", "build"])
            with patch.object(managed.sys, "platform", "darwin"):
                self.assertEqual(managed.background_command(["cargo", "check"]), ["cargo", "check"])
            for command in (["cargo", "run", "--", "game"], ["cargo", "metadata"], ["make", "check"]):
                self.assertEqual(managed.background_command(command), command)

    def test_probe_timeout_is_bounded_and_does_not_read_build_stdin(self):
        with patch.object(managed.subprocess, "run", side_effect=subprocess.TimeoutExpired(["probe"], 2)) as invoke:
            self.assertIsNone(managed._probe(["probe"]))
        self.assertEqual(invoke.call_args.kwargs["timeout"], 2)
        self.assertEqual(invoke.call_args.kwargs["stdin"], subprocess.DEVNULL)

    @unittest.skipUnless(os.name == "posix", "process and flock fixture requires Unix")
    def test_started_command_keeps_io_cwd_environment_lock_and_exit_without_retry(self):
        import fcntl
        with tempfile.TemporaryDirectory(prefix="managed build ") as temp:
            root = Path(temp)
            cargo = root / "cargo"
            cargo.write_text("#!" + sys.executable + "\n" +
                "import fcntl,json,os,sys\n"
                "from pathlib import Path\n"
                "with open('executions','a') as f: f.write('once\\n')\n"
                "lock=open('owner.lock','a')\n"
                "try: fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB); held=False\n"
                "except BlockingIOError: held=True\n"
                "print(json.dumps({'cwd':os.getcwd(),'stdin':sys.stdin.read(),'args':sys.argv[1:],"
                "'target':os.environ['CARGO_TARGET_DIR'],'outer_lock_held':held}))\n"
                "print('child diagnostic',file=sys.stderr)\n"
                "sys.exit(23)\n")
            launcher = root / "zmem"
            launcher.write_text("#!" + sys.executable + "\nimport os,sys\n"
                                "assert sys.argv[1:5]==['run','--class','background','--']\n"
                                "os.execv(sys.argv[5],sys.argv[5:])\n")
            cargo.chmod(0o755)
            launcher.chmod(0o755)
            command = [str(cargo), "test", "--", "a spaced argument"]
            with (root / "owner.lock").open("a") as lock, \
                    patch.object(managed, "_selection", return_value=(str(launcher), "ready")):
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                result = subprocess.run(managed.background_command(command), cwd=root,
                                        input="input payload", text=True, capture_output=True,
                                        env={**os.environ, "CARGO_TARGET_DIR": "existing shared target"})
            self.assertEqual(result.returncode, 23)
            self.assertEqual(result.stderr, "child diagnostic\n")
            self.assertEqual(json.loads(result.stdout), {
                "cwd": str(root), "stdin": "input payload", "args": command[1:],
                "target": "existing shared target", "outer_lock_held": True})
            self.assertEqual((root / "executions").read_text(), "once\n")


if __name__ == "__main__":
    unittest.main()
