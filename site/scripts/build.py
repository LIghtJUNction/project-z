#!/usr/bin/env python3
"""Build a standalone public site from the reviewed public-only snapshot."""
import argparse
from collections import Counter
from datetime import datetime
import hashlib
import html
import json
from pathlib import Path
import re

SITE = Path(__file__).resolve().parents[1]
OUTPUT_FILES = {"index.html", "style.css", "app.js", "favicon.svg", "projects.json", ".nojekyll"}
KINDS = {"library": "LIBRARY", "tool": "TOOL", "bindings": "BINDINGS", "integration": "INTEGRATION"}
OWNER = "LIghtJUNction"


def read_regular(path):
    path = Path(path)
    if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(SITE):
        raise ValueError("site inputs must be regular files inside site/")
    for parent in (path, *path.parents):
        if parent == SITE:
            break
        if parent.is_symlink():
            raise ValueError("symlinked site input")
    return path.read_text()


def validate(data, curation):
    if set(data) != {"schema_version", "generated_at", "categories", "projects"} or data["schema_version"] != 1:
        raise ValueError("unsupported public snapshot schema")
    datetime.fromisoformat(data["generated_at"])
    if data["categories"] != curation["categories"]:
        raise ValueError("categories differ from reviewed curation")
    reviewed = {item["id"]: item for item in curation["projects"]}
    if len(reviewed) != len(curation["projects"]):
        raise ValueError("duplicate curated project")
    projects = data["projects"]
    if {item["id"] for item in projects} != set(reviewed) or len(projects) != len(reviewed):
        raise ValueError("public snapshot must contain exactly the reviewed projects")
    categories = {item["id"] for item in data["categories"]}
    for project in projects:
        if set(project) != {"id", "summary", "category", "kind", "repository", "documentation", "source_version", "crate", "crate_lookup"}:
            raise ValueError("unexpected public project fields")
        name = project["id"]
        if not re.fullmatch(r"(?:z[a-z0-9-]+|oh-my-ztty)", name) or name in {"zui", "zui-native"}:
            raise ValueError("retired or unrelated project entry")
        for field in ("summary", "category", "kind"):
            if project[field] != reviewed[name][field]:
                raise ValueError("project text differs from reviewed public curation")
        if project["category"] not in categories or project["kind"] not in KINDS:
            raise ValueError("unknown project category or kind")
        repo = project["repository"]
        expected = "https://github.com/" + OWNER + "/" + name
        if set(repo) != {"name", "url", "default_branch", "visibility", "verified_at", "source"}:
            raise ValueError("unexpected repository metadata fields")
        if repo["visibility"] != "public" or repo["name"] != OWNER + "/" + name or repo["url"] != expected:
            raise ValueError("only confirmed public repositories may be rendered")
        if repo["source"] != "https://api.github.com/repos/" + repo["name"]:
            raise ValueError("repository evidence does not match its public source")
        datetime.fromisoformat(repo["verified_at"])
        branch = repo["default_branch"]
        if not re.fullmatch(r"[A-Za-z0-9._/-]+", branch) or ".." in branch.split("/"):
            raise ValueError("invalid public branch")
        document = project["documentation"]
        raw = "https://raw.githubusercontent.com/" + repo["name"] + "/" + branch + "/"
        if set(document) != {"url", "source", "sha256"} or document["url"] != expected + "/blob/" + branch + "/README.md":
            raise ValueError("documentation must belong to the verified public repository")
        if document["source"] != raw + "README.md" or not re.fullmatch(r"[a-f0-9]{64}", document["sha256"]):
            raise ValueError("missing public documentation evidence")
        source = project["source_version"]
        if source is not None:
            if set(source) != {"version", "source"} or source["source"] not in {raw + "Cargo.toml", raw + "VERSION"}:
                raise ValueError("invalid source version provenance")
            if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(?:[-+][A-Za-z0-9.+-]+)?", source["version"]):
                raise ValueError("invalid source version")
        lookup = project["crate_lookup"]
        package = reviewed[name]["package"]
        if set(lookup) != {"name", "source", "status", "checked_at"} or lookup["name"] != package:
            raise ValueError("unreviewed Cargo package")
        if lookup["source"] != "https://crates.io/api/v1/crates/" + package:
            raise ValueError("crate lookup must use the official registry")
        if lookup["status"] not in {"published", "not_found", "repository_mismatch", "no_active_version"}:
            raise ValueError("unverified crate lookup result")
        datetime.fromisoformat(lookup["checked_at"])
        crate = project["crate"]
        if crate is not None:
            if set(crate) != {"name", "version", "url", "source", "checksum", "repository", "verified_at"}:
                raise ValueError("unexpected crate fields")
            if lookup["status"] != "published" or crate["name"] != package or crate["repository"].rstrip("/").removesuffix(".git").lower() != expected.lower():
                raise ValueError("crate ownership is not the reviewed public repository")
            if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(?:[-+][A-Za-z0-9.+-]+)?", crate["version"]):
                raise ValueError("invalid published version")
            suffix = package + "/" + crate["version"]
            if crate["url"] != "https://crates.io/crates/" + suffix or crate["source"] != "https://crates.io/api/v1/crates/" + suffix:
                raise ValueError("unverified registry link")
            if not re.fullmatch(r"[a-f0-9]{64}", crate["checksum"]):
                raise ValueError("missing registry checksum")
            datetime.fromisoformat(crate["verified_at"])
        elif lookup["status"] == "published":
            raise ValueError("published lookup lacks version evidence")


def esc(value):
    return html.escape(str(value), quote=True)


def render(data):
    categories = {item["id"]: item for item in data["categories"]}
    projects = data["projects"]
    counts = Counter(item["category"] for item in projects)
    filters = ['<button class="filter-button" type="button" data-category="all" aria-pressed="true">全部 <span class="filter-count">' + str(len(projects)) + '</span></button>']
    for category in data["categories"]:
        filters.append('<button class="filter-button" type="button" data-category="' + esc(category["id"]) + '" aria-pressed="false">' + esc(category["label"]) + ' <span class="filter-count">' + str(counts[category["id"]]) + '</span></button>')
    cards = []
    for project in projects:
        name, category, repo = project["id"], categories[project["category"]], project["repository"]
        crate, source = project["crate"], project["source_version"]
        search = " ".join([name, project["summary"], category["label"], category["english"], project["kind"], crate["name"] if crate else ""])
        if crate:
            version = '<span class="version-label">crate</span><span>' + esc(crate["version"]) + '</span>'
            if source and source["version"] != crate["version"]:
                version += '<span class="source-version">源码 ' + esc(source["version"]) + '</span>'
        elif source:
            version = '<span class="version-label">源码</span><span>' + esc(source["version"]) + '</span>'
        else:
            version = '<span class="version-label">源码项目</span>'
        links = '<a href="' + esc(repo["url"]) + '" aria-label="' + esc(name) + ' 源码">源码 <span aria-hidden="true">↗</span></a>'
        links += '<a href="' + esc(project["documentation"]["url"]) + '" aria-label="' + esc(name) + ' 文档">文档 <span aria-hidden="true">↗</span></a>'
        if crate:
            links += '<a class="crate-link" href="' + esc(crate["url"]) + '" aria-label="' + esc(crate["name"] + " " + crate["version"]) + ' on crates.io">crates.io <span aria-hidden="true">↗</span></a>'
        cards.append(
            '<li data-project="' + esc(name) + '" data-category="' + esc(project["category"]) + '" data-search="' + esc(search) + '">'
            '<article class="project-card" aria-labelledby="project-' + esc(name) + '">'
            '<div class="card-topline"><span>' + esc(category["label"]) + '</span><span class="kind-label">' + KINDS[project["kind"]] + '</span></div>'
            '<h3 id="project-' + esc(name) + '">' + esc(name) + '</h3>'
            '<p class="card-description">' + esc(project["summary"]) + '</p>'
            '<p class="card-version">' + version + '</p>'
            '<div class="card-links">' + links + '</div></article></li>'
        )
    replacements = {
        "PROJECT_COUNT": str(len(projects)),
        "CRATE_COUNT": str(sum(project["crate"] is not None for project in projects)),
        "CATEGORY_COUNT": str(len(data["categories"])),
        "CHECKED_DATE": min(project["repository"]["verified_at"][:10] for project in projects),
        "CATEGORY_FILTERS": "\n".join(filters),
        "PROJECT_CARDS": "\n".join(cards),
    }
    result = read_regular(SITE / "templates/index.html")
    for key, value in replacements.items():
        result = result.replace("{{" + key + "}}", value)
    if re.search(r"{{[A-Z_]+}}", result):
        raise ValueError("unfilled page template")
    return result


def build(output):
    data = json.loads(read_regular(SITE / "projects.json"))
    curation = json.loads(read_regular(SITE / "curation.json"))
    validate(data, curation)
    files = {"index.html": render(data), "projects.json": json.dumps(data, ensure_ascii=False, indent=2) + "\n", ".nojekyll": ""}
    for name in ("style.css", "app.js", "favicon.svg"):
        files[name] = read_regular(SITE / "assets" / name)
    output = Path(output)
    if output.is_symlink() or (output.exists() and not output.is_dir()):
        raise ValueError("output must be a regular directory")
    if output.exists() and any(path.name not in OUTPUT_FILES or path.is_symlink() or not path.is_file() for path in output.iterdir()):
        raise ValueError("output contains files outside the deployment allowlist")
    output.mkdir(parents=True, exist_ok=True)
    for name, text in files.items():
        (output / name).write_text(text)
    return {
        "projects": len(data["projects"]),
        "verified_crates": sum(project["crate"] is not None for project in data["projects"]),
        "output": str(output), "files": sorted(files),
        "bytes": sum(len(text.encode()) for text in files.values()),
        "public_manifest_sha256": hashlib.sha256(files["projects.json"].encode()).hexdigest(),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=SITE / "dist")
    args = parser.parse_args()
    print(json.dumps(build(args.output), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
