"""Validate and shard the separate public repository inventory."""

from collections import defaultdict
import json
from pathlib import PurePosixPath
import re

SHARD_SIZE = 4
MAX_CATALOG_WORKSPACES = 128
SMOKE = {"bilibilive", "coolapk-cli", "emailctl", "markref"}
NAME = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.-]{0,99}", re.ASCII)
SHA = re.compile(r"[0-9a-f]{40}", re.ASCII)
ELIGIBLE = {"unscanned_candidate", "environment_review"}


def plan(root, profile):
    canonical = json.loads((root / "catalog.json").read_text(encoding="utf-8"))
    if canonical["schema_version"] != 1:
        raise ValueError("unknown Project Z catalog schema")
    excluded = {repo["name"].casefold() for repo in canonical["repositories"]}
    source = json.loads((root / "docs/supplemental-rust-catalog.json").read_text(encoding="utf-8"))
    if source["schema_version"] != 1:
        raise ValueError("unknown supplemental catalog schema")
    seen = set()
    all_rows = []
    for repo in source["repositories"]:
        name = repo["name"]
        if not NAME.fullmatch(name) or name.casefold() in seen | excluded | {"project-z"}:
            raise ValueError("duplicate, invalid or Project Z-owned supplemental repository name")
        seen.add(name.casefold())
        sha = repo["commit"]
        if not SHA.fullmatch(sha):
            raise ValueError(f"{name}: expected an immutable SHA")
        paths = set()
        if not repo["workspaces"]:
            raise ValueError(f"{name}: expected at least one Cargo workspace")
        for w in repo["workspaces"]:
            p = w["manifest"]
            parts = p.split("/")
            if (not all(NAME.fullmatch(part) and part.casefold() != ".git" for part in parts)
                    or parts[-1] != "Cargo.toml" or p in paths):
                raise ValueError(f"{name}: unsafe or duplicate manifest")
            paths.add(p)
            eligibility = w["validation"]
            if eligibility not in ELIGIBLE:
                raise ValueError(f"{name}: unknown coverage status")
            all_rows.append({"repo": name, "commit": sha, "manifest": p,
                             "status": "environment_review" if eligibility == "environment_review" else "not_selected",
                             "reason": w["known_constraints"] if eligibility == "environment_review" else None})
    all_rows.sort(key=lambda row: (row["repo"].casefold(), row["manifest"]))
    if not 0 < len(all_rows) <= MAX_CATALOG_WORKSPACES:
        raise ValueError("supplemental inventory exceeds its safety limit")
    candidates = [r for r in all_rows if r["status"] == "not_selected"]
    if profile == "smoke":
        chosen = [r for r in candidates if r["repo"] in SMOKE]
        if len(chosen) != SHARD_SIZE or {r["repo"] for r in chosen} != SMOKE:
            raise ValueError("all four smoke workspaces must be present and eligible")
    else:
        match = re.fullmatch(r"(remaining-)?([0-9]{1,3})", profile)
        if not match:
            raise ValueError("expected 'smoke', a non-negative shard number, or 'remaining-N'")
        if match[1]:
            candidates = [r for r in candidates if r["repo"] not in SMOKE]
        i = int(match[2]) * SHARD_SIZE
        chosen = candidates[i:i + SHARD_SIZE]
        if not chosen:
            raise ValueError("unknown supplemental shard")
    by_repo = defaultdict(list)
    for row in chosen:
        by_repo[row["repo"], row["commit"]].append(PurePosixPath(row["manifest"]))
    groups = [(name, f"https://github.com/LIghtJUNction/{name}.git", sha, tuple(paths))
              for (name, sha), paths in by_repo.items()]
    return groups, all_rows


def coverage_summary(report, rows):
    indexed = {(r["repo"], r["manifest"]): r for r in rows}
    for entry in report:
        result = indexed.get((entry["repo"], entry["manifest"]))
        if result:
            entry.update(status=result["status"], log=result["log"], workspace=result["workspace"])
    return {s: sum(e["status"] == s for e in report)
            for s in ("clean", "findings", "tool_error", "environment_review", "not_selected")}
