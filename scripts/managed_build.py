"""Classify new Cargo builds when a verified zmem daemon is available.

Set ZMEM_BUILD_BACKGROUND=0 to retain the caller's current classification.
Selection is bounded and cached for this Python batch. This module never
retries a started command, moves existing processes or acquires Cargo locks.
"""
from functools import lru_cache
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

BUILD_COMMANDS = {"build", "check", "test", "bench", "clippy", "doc", "rustc", "rustdoc"}


def _version(value):
    if not isinstance(value, str):
        return False
    match = re.fullmatch(r"(?:zmem )?(\d+)\.(\d+)\.(\d+)(?:\+[\w.-]+)?", value.strip())
    return bool(match and tuple(map(int, match.groups())) >= (0, 2, 0))


def _probe(argv):
    try:
        result = subprocess.run(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                stderr=subprocess.DEVNULL, text=True, encoding="utf-8",
                                timeout=2)
        return result.stdout if result.returncode == 0 else None
    except (OSError, UnicodeError, subprocess.TimeoutExpired):
        return None


def _candidates():
    paths = []
    # The installed manager can be newer than an older suite's PATH entry.
    for path in ("/usr/local/bin/zmem", shutil.which("zmem")):
        if path and os.access(path, os.X_OK) and Path(path).is_file():
            resolved = str(Path(path).resolve())
            if resolved not in paths:
                paths.append(resolved)
    return paths


@lru_cache(maxsize=1)
def _selection():
    if sys.platform != "linux":
        return None, "Linux is unavailable"
    candidates = _candidates()
    if not candidates:
        return None, "zmem is unavailable"
    systemctl = shutil.which("systemctl")
    if not systemctl or not os.access("/usr/bin/systemd-run", os.X_OK):
        return None, "systemd scope tools are unavailable"
    for executable in candidates:
        if not _version(_probe([executable, "--version"])):
            continue
        try:
            status = json.loads(_probe([executable, "status", "--json"]) or "null")
        except (ValueError, TypeError):
            continue
        if not isinstance(status, dict) or not _version(status.get("version")):
            continue
        observation = status.get("observation")
        if not isinstance(observation, dict) or not (
            observation.get("source") == "daemon_cache"
            and observation.get("daemon_active") is True
            and observation.get("stale") is False
            and observation.get("instance_verification") == "proc_identity"
        ):
            continue
        manager = [systemctl] + ([] if os.geteuid() == 0 else ["--user"])
        if not (_probe([*manager, "show", "--property=Version", "--value"]) or "").strip():
            return None, "the systemd manager for this caller is unavailable"
        return executable, "verified zmem daemon"
    return None, "a zmem >=0.2 CLI and identity-verified active daemon are unavailable"


@lru_cache(maxsize=None)
def _notice(message):
    print("build memory: " + message, file=sys.stderr)


def background_command(argv):
    """Return an argv prefix only; the caller keeps its IO, cwd and exit handling."""
    command = list(argv)
    if len(command) < 2 or Path(command[0]).name != "cargo" or command[1] not in BUILD_COMMANDS:
        return command
    if os.environ.get("ZMEM_BUILD_BACKGROUND") == "0":
        _notice("ZMEM_BUILD_BACKGROUND=0; keeping the caller's classification")
        return command
    executable, reason = _selection()
    if not executable:
        _notice(reason + "; running without zmem classification")
        return command
    _notice("starting Cargo in the zmem background class")
    return [executable, "run", "--class", "background", "--", *command]
