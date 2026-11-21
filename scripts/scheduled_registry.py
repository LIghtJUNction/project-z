"""Delegate an explicitly approved crate to its owner-controlled release workflow."""
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time
import tomllib
from urllib.parse import quote
from urllib.request import Request, urlopen

from project_z import ordered
from release_receipts import read_receipts, verify_archives
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


def source_receipt(pkg, repos, receipts):
    repo = repos[pkg["repository"]]
    receipt = receipts.get((pkg["name"], pkg["version"]))
    if not receipt or github_identity(receipt["github"]) != github_identity(repo["url"]) or receipt["git_sha"] != repo["commit"]:
        raise ValueError(f"{pkg['name']}@{pkg['version']}: missing exact owner-approved archive receipt")
    return receipt


def child_targets(updates, data, root, *, audit=True):
    policy = tomllib.loads((root / "project-z.toml").read_text(encoding="utf-8"))
    rules = policy.get("registry_handoffs", {})
    repos = {repo["name"]: repo for repo in data["repositories"]}
    packages = {p["name"]: p for p in data["packages"]}
    targets = {}
    for p in updates:
        target = approved_target(p, repos, rules)
        if target:
            targets[p["name"]] = target
        elif audit and p["publish"]:
            try:
                status = registry_status(p)["status"]
            except MaintenanceError as error:
                status = f"unverified ({error})"
            print(f"{p['name']}@{p['version']}: crates.io {status}; no approved owner handoff")
    if not targets:
        return []
    receipts = read_receipts(root / "docs/registry-receipts.json", policy["scheduled"]["registry_receipts_sha256"])
    graph = {}
    for name, target in targets.items():
        target["receipt"] = source_receipt(packages[name], repos, receipts)
        deps = sorted({d["name"] for d in packages[name]["dependencies"] if d["kind"] != "dev" and d["name"] in packages})
        target["prerequisites"] = [source_receipt(packages[dep], repos, receipts) for dep in deps]
        graph[name] = set(deps) & targets.keys()
    result = [targets[name] for name in ordered(graph)]
    if audit:
        for target in result:
            if present(target["receipt"]):
                status = "already consumable with approved checksum"
            elif eligible(target):
                status = "missing; owner handoff eligible"
            else:
                status = "missing; owner handoff unavailable"
            print(f"{target['name']}@{target['version']}: {status}")
    return result


def consume(receipt, registry_config=""):
    """Resolve, fetch and verify this exact archive as a fresh Cargo consumer."""
    name, version = receipt["package"], receipt["version"]
    with tempfile.TemporaryDirectory(prefix="project-z-registry-") as directory:
        root = Path(directory)
        home = root / "cargo-home"
        home.mkdir()
        if registry_config:
            (home / "config.toml").write_text(registry_config, encoding="utf-8")
        (root / "src").mkdir()
        (root / "src/lib.rs").touch()
        (root / "Cargo.toml").write_text(
            '[package]\nname="project-z-consumption-probe"\nversion="0.0.0"\nedition="2024"\n'
            f'[dependencies]\n{name}="={version}"\n', encoding="utf-8")
        env = {**os.environ, "CARGO_HOME": str(home)}
        for args in (["generate-lockfile"], ["metadata", "--locked", "--format-version", "1"]):
            subprocess.run(["cargo", *args], cwd=root, env=env, stdout=subprocess.DEVNULL, check=True, timeout=180)
        lock = tomllib.loads((root / "Cargo.lock").read_text(encoding="utf-8"))
        rows = [p for p in lock["package"] if p["name"] == name and p["version"] == version]
        if len(rows) != 1 or rows[0].get("source") != "registry+https://github.com/rust-lang/crates.io-index" or rows[0]["checksum"] != receipt["archive_sha256"]:
            raise ValueError(f"{name}@{version}: registry lock checksum/source differs from the staged receipt")
        archives = list((home / "registry/cache").glob(f"*/{name}-{version}.crate"))
        if len(archives) != 1:
            raise ValueError(f"{name}@{version}: missing verified Cargo download")
        verify_archives([receipt], {(name, version): receipt}, archives[0].parent)


def present(receipt):
    row = registry_status(dict(name=receipt["package"], version=receipt["version"], repository=receipt["github"]))
    if row["status"] == "missing":
        return False
    if row["status"] != "present":
        raise ValueError(f"{receipt['package']}: existing version is {row['status']}")
    consume(receipt)
    return True


def publish_missing(target, before_dispatch=None):
    for receipt in target["prerequisites"]:
        if not present(receipt):
            raise ValueError(f"required upstream is not consumable: {receipt['package']}@{receipt['version']}")
    receipt = target["receipt"]
    if present(receipt):
        print(f"Already consumable: {target['name']}@{target['version']}")
        return
    if not eligible(target):
        print(f"Skipping unverified owner, source or workflow for {target['name']}")
        return
    if before_dispatch:
        before_dispatch()
    subprocess.run(["gh", "workflow", "run", target["workflow"], "--repo", target["repository"],
                    "--ref", target["branch"], "-f", "source_sha=" + target["sha"],
                    "-f", "package=" + target["name"], "-f", "version=" + target["version"],
                    "-f", "archive_sha256=" + receipt["archive_sha256"]], check=True)
    for attempt in range(30):
        if present(receipt):
            return
        if attempt < 29:
            time.sleep(20)
    raise ValueError(f"{target['name']}: owner dispatch has not produced a consumable archive; retry this plan")


def dispatch():
    if not os.environ.get("GH_TOKEN"):
        raise ValueError("missing repository-scoped owner dispatch permission")
    from scheduled import fresh, git, remote_refs, require, verify
    def verify_cohort():
        sha, tag = os.environ["CANDIDATE"], os.environ["RELEASE_TAG"]
        git("fetch", "--no-tags", "origin", "refs/heads/main")
        refs = remote_refs()
        require(git("rev-parse", "FETCH_HEAD") == sha and refs.get("refs/heads/main") == sha and
                refs.get("refs/tags/" + tag) == sha, "aggregate source moved since CI")
        verify(os.environ["GITHUB_SHA"], sha)
        fresh(sha)
    publish_missing(json.loads(os.environ["CHILD_TARGET"]), verify_cohort)


if __name__ == "__main__":
    dispatch()
