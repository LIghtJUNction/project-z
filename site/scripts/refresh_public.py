#!/usr/bin/env python3
"""Refresh a public-only snapshot, or verify its public sources before deployment."""
import argparse
import concurrent.futures
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import tomllib
import urllib.error
import urllib.request

SITE = Path(__file__).resolve().parents[1]
OWNER = "LIghtJUNction"


def request(url):
    headers = {"User-Agent": "Project-Z-public-page/1.0"}
    # An optional, ephemeral Actions token raises the normal GitHub API quota.
    # It is sent only to api.github.com and is never serialized or logged.
    if url.startswith("https://api.github.com/"):
        headers["Accept"] = "application/vnd.github+json"
        token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = "Bearer " + token
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as response:
            return response.status, response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return 404, ""
        raise RuntimeError("public source returned HTTP " + str(error.code) + ": " + url) from None


def repository(name):
    url = "https://api.github.com/repos/" + OWNER + "/" + name
    code, body = request(url)
    if code != 200:
        raise ValueError("public repository is unavailable: " + name)
    data = json.loads(body)
    if data.get("private") is not False or data.get("visibility") != "public" or data.get("archived"):
        raise ValueError("repository is not active and public: " + name)
    if data["full_name"].lower() != (OWNER + "/" + name).lower():
        raise ValueError("repository identity changed: " + name)
    return data


def snapshot_from_evidence(item, evidence):
    """Reduce verified public evidence to the exact fields allowed in the site."""
    if evidence.get("public") is not True or evidence.get("error"):
        raise ValueError("public evidence is required")
    name = item["id"]
    repo_name = OWNER + "/" + name
    if evidence["repository"] != repo_name or evidence["readme_status"] != 200:
        raise ValueError("public README evidence is required")
    now = evidence["checked_at"]
    branch = evidence["default_branch"]
    repo_url = "https://github.com/" + repo_name
    raw = "https://raw.githubusercontent.com/" + repo_name + "/" + branch + "/"
    source = None
    if evidence.get("source_version"):
        source = {"version": evidence["source_version"], "source": raw + evidence.get("source_version_file", "Cargo.toml" if evidence["cargo_status"] == 200 else "VERSION")}
    published = evidence.get("published")
    crate = None
    if published:
        suffix = published["name"] + "/" + published["version"]
        crate = {
            "name": published["name"], "version": published["version"],
            "url": "https://crates.io/crates/" + suffix,
            "source": published["api"], "checksum": published["checksum"],
            "repository": published["repository"], "verified_at": now,
        }
    status = "published" if crate else ("not_found" if evidence["crate_status"] == 404 else ("repository_mismatch" if evidence["crate_status"] == "repository_mismatch" else "no_active_version"))
    return {
        "id": name, "summary": item["summary"], "category": item["category"], "kind": item["kind"],
        "repository": {"name": repo_name, "url": repo_url, "default_branch": branch,
                       "visibility": "public", "verified_at": now, "source": evidence["repository_api"]},
        "documentation": {"url": repo_url + "/blob/" + branch + "/README.md",
                          "source": raw + "README.md", "sha256": hashlib.sha256(evidence["readme"].encode()).hexdigest()},
        "source_version": source, "crate": crate,
        "crate_lookup": {"name": item["package"], "source": "https://crates.io/api/v1/crates/" + item["package"],
                         "status": status, "checked_at": now},
    }


def refresh(item):
    name = item["id"]
    meta = repository(name)
    repo = OWNER + "/" + name
    branch = meta["default_branch"]
    raw = "https://raw.githubusercontent.com/" + repo + "/" + branch + "/"
    readme_status, readme = request(raw + "README.md")
    cargo_status, cargo = request(raw + "Cargo.toml")
    version_status, version_text = request(raw + "VERSION")
    manifest = tomllib.loads(cargo) if cargo_status == 200 else {}
    version = manifest.get("package", {}).get("version")
    source_file = "Cargo.toml"
    if isinstance(version, dict):
        version = manifest.get("workspace", {}).get("package", {}).get("version")
    if not version and version_status == 200:
        version = version_text.strip()
        source_file = "VERSION"
    package = item["package"]
    crate_status, body = request("https://crates.io/api/v1/crates/" + package)
    published = None
    if crate_status == 200:
        data = json.loads(body)
        crate = data["crate"]
        expected = ("https://github.com/" + repo).lower()
        actual = (crate.get("repository") or "").rstrip("/").removesuffix(".git").lower()
        if actual == expected:
            target = crate.get("default_version") or crate.get("max_stable_version") or crate.get("newest_version")
            selected = next((value for value in data["versions"] if value["num"] == target and not value["yanked"]), None)
            if selected:
                published = {"name": package, "version": selected["num"], "checksum": selected["checksum"],
                             "repository": crate["repository"], "api": "https://crates.io/api/v1/crates/" + package + "/" + selected["num"]}
        else:
            crate_status = "repository_mismatch"
    evidence = {
        "name": name, "repository": repo, "public": True, "default_branch": branch,
        "repository_api": "https://api.github.com/repos/" + repo,
        "readme_status": readme_status, "readme": readme,
        "cargo_status": cargo_status, "source_version": version, "source_version_file": source_file,
        "crate_status": crate_status, "published": published,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }
    return snapshot_from_evidence(item, evidence)


def verify(project):
    repository(project["id"])
    crate = project["crate"]
    if crate:
        status, text = request(crate["source"])
        if status != 200:
            raise ValueError("published crate version is unavailable: " + crate["name"])
        version = json.loads(text)["version"]
        if version["num"] != crate["version"] or version["checksum"] != crate["checksum"] or version["yanked"]:
            raise ValueError("crate evidence no longer matches the registry: " + crate["name"])
    return project["id"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-only", action="store_true", help="check current public visibility and exact published versions")
    parser.add_argument("--only", nargs="+", help="refresh only these reviewed project IDs")
    args = parser.parse_args()
    from build import validate
    curation = json.loads((SITE / "curation.json").read_text())
    data = json.loads((SITE / "projects.json").read_text())
    validate(data, curation)
    if args.verify_only:
        if args.only:
            parser.error("--only cannot be combined with --verify-only")
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            verified = list(pool.map(verify, data["projects"]))
        print(json.dumps({"verified_public_projects": len(verified)}))
        return
    names = set(args.only or [item["id"] for item in curation["projects"]])
    if names - {item["id"] for item in curation["projects"]}:
        parser.error("unknown project; review curation before adding a repository")
    selected = [item for item in curation["projects"] if item["id"] in names]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        refreshed = {project["id"]: project for project in pool.map(refresh, selected)}
    data["projects"] = [refreshed.get(project["id"], project) for project in data["projects"]]
    data["generated_at"] = datetime.now(timezone.utc).isoformat()
    validate(data, curation)
    # All requests and checks finish before replacing the reviewed snapshot.
    path = SITE / "projects.json"
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(path)
    print(json.dumps({"refreshed_public_projects": len(refreshed)}))


if __name__ == "__main__":
    main()
