#!/usr/bin/env python3
"""Collect public Project Z documentation at exact default-branch commits.

Run from any directory. No credentials, repository clones, binaries, or private
files are used. Metadata is verified against GitHub's anonymous public listings;
Markdown is downloaded directly from immutable raw URLs. Failed refreshes retain
the previous complete project snapshot. --inventory only reports public scope.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import gzip
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import posixpath
import re
import subprocess
import sys
import tempfile
import threading
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote, unquote, urlsplit
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "site"
CACHE = SITE / ".cache" / "public-docs"
MANIFEST = SITE / "content-manifest.json"
ADDITIONAL = ("zchat", "zobs")
README_NAMES = (
    "README.zh-CN.md", "README.zh_CN.md", "README.zh.md", "README_zh.md",
    "README-ZH.md", "README_ZH.md", "README_CN.md", "README.cn.md", "README.md",
)
EXCLUDED_PARTS = {
    ".github", ".git", "github", "agents", "contributing", "security", "license",
    "changelog", "changes", "roadmap", "todo", "tasks", "plans", "plan",
    "reports", "report", "evidence", "maintenance", "audit", "audits",
    "secrets", "secret", "private", "internal", "test", "tests", "testing",
    "fixtures", "logs", "log", "releases", "release", "releasing", "publishing",
    "benchmarks", "benchmark", "validation", "verification", "acceptance",
}
PRIORITY = (
    "getting-started", "quickstart", "quick-start", "install", "setup",
    "usage", "guide", "configuration", "config", "cli", "command",
    "api", "reference", "architecture", "design", "language", "session",
    "protocol", "platform", "plugin", "compatibility", "example",
)


class FetchError(RuntimeError):
    pass


class Http:
    def __init__(self, refresh: bool = False):
        self.refresh = refresh
        self.bytes = 0
        self.requests = 0
        self.lock = threading.Lock()
        CACHE.mkdir(parents=True, exist_ok=True)

    def get(self, url: str, *, immutable: bool = False, optional: bool = False) -> bytes | None:
        key = hashlib.sha256(url.encode()).hexdigest()
        cached = CACHE / (key + ".body")
        missing = CACHE / (key + ".missing")
        if immutable and cached.exists():
            return cached.read_bytes()
        if immutable and missing.exists():
            return None
        for attempt in range(3):
            try:
                request = Request(url, headers={
                    "User-Agent": "Project-Z-public-documentation/1.0",
                    "Accept": "application/vnd.github+json" if "api.github.com/" in url else "*/*",
                    "Accept-Encoding": "gzip",
                })
                with urlopen(request, timeout=35) as response:
                    data = response.read(6_000_001)
                    with self.lock:
                        self.bytes += len(data)
                        self.requests += 1
                    if len(data) > 6_000_000:
                        raise FetchError(f"Response exceeds text-document limit: {url}")
                    if response.headers.get("Content-Encoding") == "gzip":
                        data = gzip.decompress(data)
                    if immutable:
                        atomic_write(cached, data)
                    return data
            except HTTPError as exc:
                if exc.code == 404 and optional:
                    if immutable:
                        atomic_write(missing, b"404\n")
                    return None
                if exc.code in {429, 500, 502, 503, 504} and attempt < 2:
                    time.sleep(attempt + 1)
                    continue
                # A rate limit or denied request is an error, never proof that
                # a repository is private or suitable for exclusion.
                raise FetchError(f"HTTP {exc.code}: {url}") from exc
            except (URLError, TimeoutError, OSError) as exc:
                if attempt < 2:
                    time.sleep(attempt + 1)
                    continue
                raise FetchError(f"Download failed: {url}: {exc}") from exc
        raise AssertionError("unreachable")


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".collect-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def public_repositories(http: Http, owner: str) -> dict[str, dict]:
    cached = CACHE / f"{owner}-repos.json"
    if cached.exists() and not http.refresh:
        document = json.loads(cached.read_text())
        fetched = datetime.fromisoformat(document["fetched_at"])
        if (datetime.now(timezone.utc) - fetched).total_seconds() < 900:
            return {item["full_name"].lower(): item for item in document["items"]}
    rows = []
    for page in range(1, 101):
        url = f"https://api.github.com/users/{quote(owner)}/repos?per_page=100&page={page}"
        data = json.loads(http.get(url))
        if not isinstance(data, list):
            raise FetchError(f"Unexpected public repository listing for {owner}")
        rows.extend(data)
        if len(data) < 100:
            break
    else:
        raise FetchError(f"Public repository listing did not finish for {owner}")
    document = {"fetched_at": datetime.now(timezone.utc).isoformat(), "items": rows}
    atomic_write(cached, json.dumps(document, ensure_ascii=False).encode())
    return {item["full_name"].lower(): item for item in rows}


def default_head(repository: str) -> tuple[str, str]:
    env = dict(os.environ)
    env.update({"GIT_TERMINAL_PROMPT": "0", "GIT_CONFIG_NOSYSTEM": "1",
                "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_ASKPASS": "/bin/false"})
    env.pop("GIT_CONFIG_COUNT", None)
    command = ["git", "-c", "credential.helper=", "-c", "http.extraheader=",
               "-c", "http.cookiefile=", "ls-remote", "--symref", repository + ".git", "HEAD"]
    result = subprocess.run(command, check=False, capture_output=True, text=True,
                            timeout=60, env=env)
    branch = re.search(r"^ref: refs/heads/(.+)\s+HEAD$", result.stdout, re.M)
    commit = re.search(r"^([0-9a-f]{40})\s+HEAD$", result.stdout, re.M)
    if result.returncode or not branch or not commit:
        raise FetchError(f"Cannot resolve public default branch: {repository}")
    return branch.group(1), commit.group(1)


def raw(http: Http, full_name: str, commit: str, path: str) -> bytes | None:
    url = f"https://raw.githubusercontent.com/{full_name}/{commit}/{quote(path, safe='/')}"
    data = http.get(url, immutable=True, optional=True)
    if data is not None:
        if len(data) > 2_000_000:
            raise FetchError(f"Document too large: {full_name}/{path}")
        try:
            data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise FetchError(f"Non-UTF-8 document: {full_name}/{path}") from exc
    return data


def readmes(http: Http, full_name: str, commit: str) -> dict[str, bytes]:
    found = {}
    with ThreadPoolExecutor(max_workers=4) as pool:
        jobs = {pool.submit(raw, http, full_name, commit, path): path for path in README_NAMES}
        for job in as_completed(jobs):
            data = job.result()
            if data is not None:
                found[jobs[job]] = data
    if not found:
        for path in ("readme.md", "Readme.md", "README.markdown", "README.MD"):
            data = raw(http, full_name, commit, path)
            if data is not None:
                found[path] = data
                break
    if not found:
        raise FetchError(f"No public Markdown README found: {full_name}")
    return found


def allowed_document(path: str) -> bool:
    if not path.lower().endswith((".md", ".markdown")):
        return False
    parts = re.split(r"[/_.\s-]+", path.lower())
    if any(part in EXCLUDED_PARTS for part in parts):
        return False
    if re.search(r"20\d{2}[-_]?\d{2}[-_]?\d{2}", path):
        return False
    if any(word in path for word in ("审计", "报告", "测试", "证据", "维护", "私有", "密钥")):
        return False
    return True


def linked_paths(text: str, current: str, full_name: str, branch: str, commit: str) -> list[str]:
    links = re.findall(r"\[[^\]]*\]\(\s*<?([^\s)>]+)", text)
    links += re.findall(r"^\s*\[[^\]]+\]:\s*<?([^\s>]+)", text, re.M)
    links += re.findall(r"href=[\"']([^\"']+)[\"']", text)
    result = []
    for link in links:
        parsed = urlsplit(link)
        path = unquote(parsed.path)
        if parsed.scheme or parsed.netloc:
            prefixes = [f"/{full_name}/blob/{ref}/" for ref in (branch, commit, "main", "master")]
            if parsed.netloc not in {"github.com", "www.github.com"}:
                continue
            prefix = next((prefix for prefix in prefixes if path.lower().startswith(prefix.lower())), None)
            if not prefix:
                continue
            path = path[len(prefix):]
        else:
            path = path.lstrip("/") if path.startswith("/") else posixpath.normpath(posixpath.join(posixpath.dirname(current), path))
        if path.startswith("../") or path == ".." or not allowed_document(path):
            continue
        if path not in result:
            result.append(path)
    return result


def nav_paths(data: bytes) -> list[str]:
    result = []

    def visit(item):
        if isinstance(item, dict):
            explicit_source = next((item[key] for key in ("source", "file", "path", "href")
                                    if isinstance(item.get(key), str) and urlsplit(item[key]).path.endswith((".md", ".markdown"))), None)
            for key, value in item.items():
                if key in {"path", "file", "source", "href", "slug"} and isinstance(value, str):
                    if explicit_source is not None and value != explicit_source:
                        continue
                    path = urlsplit(value).path.lstrip("/")
                    if urlsplit(value).netloc or not path or ".." in PurePosixPath(path).parts:
                        continue
                    if path.endswith((".md", ".markdown")):
                        candidates = [path] if path.startswith(("docs/", "site/")) else ["site/" + path if path.startswith("content/") else "site/content/" + path]
                    else:
                        path = path.removeprefix("docs/")
                        candidates = [f"site/content/{path}.md", f"site/content/{path}/index.md"]
                    for candidate in candidates:
                        if allowed_document(candidate) and candidate not in result:
                            result.append(candidate)
                elif isinstance(value, (dict, list)):
                    visit(value)
        elif isinstance(item, list):
            for child in item:
                visit(child)

    try:
        visit(json.loads(data))
    except json.JSONDecodeError as exc:
        raise FetchError("Invalid site/nav.json") from exc
    return result


def doc_priority(path: str) -> tuple[int, str]:
    lower = path.lower()
    priority = next((index for index, word in enumerate(PRIORITY) if word in lower), len(PRIORITY))
    return priority, lower


def title_from(data: bytes, path: str) -> str:
    text = data.decode("utf-8")
    metadata_title = None
    frontmatter = re.match(r"\A\ufeff?---\r?\n(.*?)\r?\n---(?:\r?\n|$)", text, re.S)
    if frontmatter:
        text = text[frontmatter.end():]
        for key in ("title", "name"):
            value = re.search(rf"^{key}:\s*(.+?)\s*$", frontmatter[1], re.M)
            if value and value[1] not in {"|", ">"}:
                metadata_title = value[1].strip("\"'")
                break
    match = re.search(r"^#{1,6}\s+(.+?)(?:\s+#+)?\s*$", text, re.M)
    if match:
        return re.sub(r"[*`_]", "", match.group(1)).strip()
    lines = text.splitlines()
    for index, line in enumerate(lines[1:], 1):
        if re.fullmatch(r"\s*[=-]{3,}\s*", line) and lines[index - 1].strip():
            return lines[index - 1].strip()
    return metadata_title or PurePosixPath(path).stem.replace("-", " ")


def slug_for(path: str, used: set[str]) -> str:
    if path == "README.md":
        base = "readme-en"
    else:
        stripped = re.sub(r"^(?:site/content/|docs/|doc/)", "", path)
        base = re.sub(r"[^a-z0-9]+", "-", str(PurePosixPath(stripped).with_suffix("")).lower()).strip("-")
        base = base[:75] or "page"
    if base == "index":
        base = "documentation-overview"
    slug = base
    if slug in used:
        slug = base + "-" + hashlib.sha256(path.encode()).hexdigest()[:6]
    used.add(slug)
    return slug


def collect_project(http: Http, item: dict, metadata: dict, *, inventory: bool = False) -> dict:
    full_name = metadata["full_name"]
    repository = "https://github.com/" + full_name
    branch, commit = default_head(repository)
    found = readmes(http, full_name, commit)
    primary = next((path for path in README_NAMES if path in found), next(iter(found)))
    if item["additional"] and not any(re.search(r"\bProject[ -]+Z\b", value.decode("utf-8"), re.I) for value in found.values()):
        return {"excluded": {"id": item["name"], "reason": "Public README does not identify the project as Project Z."}}
    project = {"id": item["name"], "name": metadata["name"], "repository": repository,
               "branch": branch, "commit": commit, "description": metadata.get("description") or "",
               "visibility": "public", "metadata_source": f"https://api.github.com/repos/{full_name}",
               "role": item["role"], "additional": item["additional"],
               "readme_source": f"{repository}/blob/{commit}/{quote(primary, safe='/')}", "pages": []}
    if inventory:
        return {"project": project, "documents": {}}
    documents = {primary: found[primary]}
    english = next((path for path in ("README.md", "readme.md", "Readme.md") if path in found and path != primary), None)
    if english:
        documents[english] = found[english]
    frontier = []
    for path, data in found.items():
        frontier.extend(linked_paths(data.decode("utf-8"), path, full_name, branch, commit))
    navigation = raw(http, full_name, commit, "site/nav.json")
    navigation_paths = []
    if navigation is not None:
        navigation_paths = [path for path in nav_paths(navigation)
                            if PurePosixPath(path).stem.lower() not in {"index", "readme"}]
        preferred_names = {PurePosixPath(path).name.lower() for path in navigation_paths}
        frontier = [path for path in frontier if PurePosixPath(path).name.lower() not in preferred_names]
        frontier.extend(navigation_paths)
    navigation_order = {path: index for index, path in enumerate(navigation_paths)}
    seen = set(found)
    for _depth in range(2):
        candidates = sorted(set(frontier) - seen,
                            key=lambda path: (0, navigation_order[path]) if path in navigation_order else (1, doc_priority(path)))
        frontier = []
        candidates = [path for path in candidates if allowed_document(path)]
        offset = 0
        with ThreadPoolExecutor(max_workers=4) as pool:
            while offset < len(candidates) and len(documents) < 12:
                batch = candidates[offset:offset + min(4, 12 - len(documents))]
                offset += len(batch)
                fetched = pool.map(lambda path: raw(http, full_name, commit, path), batch)
                for path, data in zip(batch, fetched):
                    seen.add(path)
                    if data is None:
                        print(f"SKIP missing document {full_name}/{path}", file=sys.stderr, flush=True)
                        continue
                    documents[path] = data
                    frontier.extend(linked_paths(data.decode("utf-8"), path, full_name, branch, commit))
        if len(documents) >= 12 or not frontier:
            break
    outputs = {}
    used_slugs = {""}
    for index, (path, data) in enumerate(documents.items()):
        slug = "" if index == 0 else slug_for(path, used_slugs)
        filename = "index" if not slug else slug
        relative = f"content/projects/{item['name']}/{filename}.md"
        project["pages"].append({"slug": slug, "title": "概览" if index == 0 else title_from(data, path),
                                 "file": relative, "source": f"{repository}/blob/{commit}/{quote(path, safe='/')}", "path": path})
        outputs[relative] = data
    return {"project": project, "documents": outputs}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", nargs="+", help="Limit to project names (space or comma separated)")
    parser.add_argument("--inventory", action="store_true", help="Verify public scope; do not write document snapshots")
    parser.add_argument("--refresh", action="store_true", help="Refresh public metadata; immutable Markdown cache remains valid")
    parser.add_argument("--workers", type=int, default=6, help="Concurrent repositories (default: 6)")
    args = parser.parse_args()
    catalog = json.loads((ROOT / "catalog.json").read_text())["repositories"]
    items = [{**entry, "additional": False} for entry in catalog]
    registered = {item["name"].lower() for item in items}
    items += [{"name": name, "url": f"https://github.com/LIghtJUNction/{name}.git", "role": "application", "additional": True}
              for name in ADDITIONAL if name.lower() not in registered]
    if args.only:
        selected = {part.lower() for value in args.only for part in value.split(",")}
        unknown = selected - {item["name"].lower() for item in items}
        if unknown:
            parser.error("Unknown project(s): " + ", ".join(sorted(unknown)))
        items = [item for item in items if item["name"].lower() in selected]
    http = Http(args.refresh)
    owners = sorted({urlsplit(item["url"]).path.strip("/").split("/")[0] for item in items})
    public = {}
    try:
        with ThreadPoolExecutor(max_workers=min(4, len(owners))) as pool:
            for result in pool.map(lambda owner: public_repositories(http, owner), owners):
                public.update(result)
    except FetchError as exc:
        print(f"ERROR: Public metadata verification failed; existing snapshots unchanged. {exc}", file=sys.stderr)
        return 1
    excluded, available = [], []
    for item in items:
        full_name = urlsplit(item["url"]).path.strip("/").removesuffix(".git")
        metadata = public.get(full_name.lower())
        if metadata is None:
            excluded.append({"id": item["name"], "reason": "Not present in the owner's complete anonymous public GitHub repository listing."})
        elif metadata.get("private") is not False or metadata.get("visibility", "public") != "public":
            excluded.append({"id": item["name"], "reason": "GitHub metadata does not confirm public visibility."})
        else:
            available.append((item, metadata))
    print(f"PUBLIC {len(available)}/{len(items)}; excluded {len(excluded)}", flush=True)
    projects, outputs, failures = {}, {}, []
    with ThreadPoolExecutor(max_workers=max(1, min(args.workers, 12))) as pool:
        jobs = {pool.submit(collect_project, http, item, metadata, inventory=args.inventory): item for item, metadata in available}
        for job in as_completed(jobs):
            item = jobs[job]
            try:
                result = job.result()
                if "excluded" in result:
                    excluded.append(result["excluded"])
                    continue
                project = result["project"]
                projects[project["id"]] = project
                outputs.update(result["documents"])
                print(f"OK {project['id']} {project['commit']} {len(project['pages'])} pages", flush=True)
            except Exception as exc:
                failures.append({"id": item["name"], "error": str(exc)})
                print(f"ERROR {item['name']}: {exc}; previous snapshot retained", file=sys.stderr, flush=True)
    if not args.inventory:
        previous = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {"projects": [], "excluded": []}
        old_projects = {project["id"]: project for project in previous["projects"]}
        # Explicit public exclusions leave no old published entry. Transient
        # failures retain the last successful snapshot, including its commit.
        excluded_ids = {entry["id"] for entry in excluded}
        selected_ids = {item["name"] for item in items}
        for project_id, project in old_projects.items():
            if project_id not in projects and project_id not in excluded_ids:
                projects[project_id] = project
        if args.only:
            excluded.extend(entry for entry in previous.get("excluded", []) if entry["id"] not in selected_ids)
        for relative, data in outputs.items():
            atomic_write(SITE / relative, data)
        manifest = {"schema_version": 1, "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    "projects": sorted(projects.values(), key=lambda project: project["id"].lower()),
                    "excluded": sorted(excluded, key=lambda item: item["id"].lower())}
        atomic_write(MANIFEST, (json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode())
        # Remove only obsolete Markdown snapshots managed by the prior manifest.
        current_files = {page["file"] for project in projects.values() for page in project["pages"]}
        old_files = {page["file"] for project in previous["projects"] for page in project["pages"]}
        for relative in old_files - current_files:
            path = SITE / relative
            if path.is_relative_to(SITE / "content" / "projects"):
                path.unlink(missing_ok=True)
    print(json.dumps({"projects": len(projects), "additional": sum(p["additional"] for p in projects.values()),
                      "pages": sum(len(p["pages"]) for p in projects.values()), "excluded": excluded,
                      "failures": failures, "download_bytes": http.bytes, "requests": http.requests,
                      "written_markdown_bytes": sum(len(value) for value in outputs.values())}, ensure_ascii=False), flush=True)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
