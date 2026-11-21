"""Delegate an explicitly approved crate to its owner-controlled release workflow."""
import json
import os
from pathlib import Path
import re
import subprocess
import tomllib
from urllib.parse import quote
from urllib.request import Request, urlopen

from maintenance import MaintenanceError, github_identity, registry_status


def gh_api(endpoint):
    return json.loads(subprocess.check_output(["gh", "api", endpoint], encoding="utf-8"))


def owns_crate(name, owner):
    request = Request(f"https://crates.io/api/v1/crates/{quote(name, safe='')}/owners",
                      headers={"User-Agent": "project-z-maintenance/1 (https://github.com/LIghtJUNction/project-z)"})
    with urlopen(request, timeout=30) as response:
        return any(row["login"] == owner for row in json.load(response)["users"])


def approved_target(p, repos, rules):
    rule = rules.get(p["name"])
    if not rule or not p["publish"]:
        return None
    repo = repos[p["repository"]]
    identity = github_identity(repo["url"])
    if not identity or "/".join(identity) != rule["repository"]:
        raise ValueError("registry opt-in repository differs from registered source")
    workflow = rule["workflow"]
    if not (re.fullmatch(r"[A-Za-z0-9_-]+\.ya?ml", workflow) and re.fullmatch("[a-f0-9]{40}", rule["workflow_blob"])):
        raise ValueError("invalid approved workflow")
    if not re.fullmatch("[a-zA-Z0-9_-]+", p["name"]):
        raise ValueError("invalid crate")
    return {"repository": rule["repository"], "workflow": workflow, "workflow_blob": rule["workflow_blob"],
            "owner": rule["crate_owner"], "name": p["name"], "version": p["version"],
            "sha": repo["commit"], "branch": repo["branch"]}


def eligible(target):
    name, repo = target["name"], target["repository"]
    if registry_status(target)["status"] != "missing":
        return False
    if not owns_crate(name, target["owner"]):
        return False
    meta = gh_api(f"repos/{repo}")
    branch = meta["default_branch"]
    if meta["full_name"].lower() != repo.lower() or branch != target["branch"]:
        return False
    head = gh_api(f"repos/{repo}/commits/{quote(branch, safe='')}")
    if head["sha"] != target["sha"]:
        return False
    workflow = gh_api(f"repos/{repo}/contents/.github/workflows/{target['workflow']}?ref={target['sha']}")
    return workflow.get("type") == "file" and workflow.get("sha") == target["workflow_blob"]


def child_targets(updates, repositories, root):
    rules = tomllib.loads((root / "project-z.toml").read_text(encoding="utf-8")).get("registry_handoffs", {})
    repos = {repo["name"]: repo for repo in repositories}
    result = []
    for p in updates:
        target = approved_target(p, repos, rules)
        try:
            if target and eligible(target):
                result.append(target)
            elif p["publish"] and not target:
                status = registry_status(p)["status"]
                print(f"{p['name']}@{p['version']}: crates.io {status}; no approved owner handoff")
        except (MaintenanceError, OSError, subprocess.CalledProcessError, ValueError, KeyError) as error:
            print(f"{p['name']}@{p['version']}: could not verify registry handoff; skipping ({error})")
    return result


def dispatch():
    target = json.loads(os.environ["CHILD_TARGET"])
    if not os.environ.get("GH_TOKEN"):
        raise ValueError("missing repository-scoped owner dispatch permission")
    if eligible(target):
        subprocess.run(["gh", "workflow", "run", target["workflow"], "--repo", target["repository"],
                        "--ref", target["branch"], "-f", "source_sha=" + target["sha"],
                        "-f", "package=" + target["name"], "-f", "version=" + target["version"]], check=True)


if __name__ == "__main__":
    dispatch()
