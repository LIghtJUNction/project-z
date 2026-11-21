#!/usr/bin/env python3
"""Build the complete Project Z documentation portal from public Markdown."""

from __future__ import annotations
import argparse
from collections import Counter
from datetime import datetime, timedelta, timezone
from html import escape
from html.parser import HTMLParser
import json
from pathlib import Path, PurePosixPath
import posixpath
import re
import shutil
import sys
import tempfile
import unicodedata
from urllib.parse import quote, unquote, urlsplit, urlunsplit
from xml.sax.saxutils import escape as xml_escape

SITE = Path(__file__).resolve().parents[1]
DEFAULT_BASE = "https://lightjunction.github.io/project-z-site/"
MARKER = ".project-z-docs-build"
KINDS = {
    "library": "LIBRARY",
    "tool": "TOOL",
    "bindings": "BINDINGS",
    "integration": "INTEGRATION",
}


class BuildError(ValueError):
    pass


def display_date(value):
    instant = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return instant.astimezone(timezone(timedelta(hours=8))).date().isoformat()


def esc(value):
    return escape(str(value), quote=True)


def read_regular(relative):
    path = SITE / relative
    if not path.resolve().is_relative_to(SITE.resolve()) or not path.is_file():
        raise BuildError(f"Missing or out-of-scope site input: {relative}")
    cursor = path
    while cursor != SITE:
        if cursor.is_symlink():
            raise BuildError(f"Symlinked site input: {relative}")
        cursor = cursor.parent
    return path.read_text(encoding="utf-8")


def route(project, page):
    return project["id"] + "/" + (page["slug"] + "/" if page["slug"] else "")


def root_for(project, page):
    return "../" * route(project, page).count("/")


def load_sources():
    data = json.loads(read_regular("content-manifest.json"))
    curation = json.loads(read_regular("curation.json"))
    if data.get("schema_version") != 1 or not isinstance(data.get("projects"), list):
        raise BuildError("Unsupported documentation manifest")
    datetime.fromisoformat(data["generated_at"].replace("Z", "+00:00"))
    reviewed = {p["id"]: p for p in curation["projects"]}
    categories = {c["id"] for c in curation["categories"]}
    projects, ids = [], set()
    for item in data["projects"]:
        name, repo = item["id"], item["repository"]
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", name) or name in ids:
            raise BuildError(f"Invalid or duplicate project: {name}")
        ids.add(name)
        if name not in reviewed:
            raise BuildError(f"Project has no reviewed introduction: {name}")
        if not re.fullmatch(
            r"https://github\.com/[A-Za-z0-9_-]+/[A-Za-z0-9._-]+", repo
        ):
            raise BuildError(f"Invalid repository: {name}")
        if item.get("visibility") != "public" or item.get(
            "metadata_source"
        ) != repo.replace("https://github.com/", "https://api.github.com/repos/"):
            raise BuildError(f"Missing public-source verification: {name}")
        if not re.fullmatch(r"[a-f0-9]{40}", item["commit"]):
            raise BuildError(f"Missing exact source commit: {name}")
        project = {
            **item,
            **{k: reviewed[name][k] for k in ("summary", "category", "kind")},
        }
        if project["category"] not in categories or project["kind"] not in KINDS:
            raise BuildError(f"Unknown category or kind: {name}")
        slugs, paths = set(), set()
        for page in project["pages"]:
            slug, path = page["slug"], PurePosixPath(page["path"])
            if slug and not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
                raise BuildError(f"Invalid page route: {name}/{slug}")
            if slug in slugs or page["path"] in paths:
                raise BuildError(f"Duplicate page: {name}/{slug}")
            slugs.add(slug)
            paths.add(page["path"])
            if path.is_absolute() or ".." in path.parts:
                raise BuildError(f"Invalid source path: {path}")
            if not page["file"].startswith(f"content/projects/{name}/") or not page[
                "file"
            ].endswith(".md"):
                raise BuildError(f"Markdown path outside project: {page['file']}")
            expected = repo + "/blob/" + project["commit"] + "/" + str(path)
            if unquote(page["source"]) != expected:
                raise BuildError(f"Source does not match commit: {page['file']}")
            read_regular(page["file"])
        if not project["pages"] or project["pages"][0]["slug"] != "":
            raise BuildError(f"Project needs an overview: {name}")
        projects.append(project)
    if not projects:
        raise BuildError("Empty documentation manifest")
    return data, curation, projects


def plain(tokens):
    return "".join(
        (
            t.content
            if t.type in ("text", "code_inline")
            else (
                " " if t.type in ("softbreak", "hardbreak") else plain(t.children or [])
            )
        )
        for t in tokens
    )


def heading_slug(label):
    value = re.sub(r"[^\w\s-]", "", unicodedata.normalize("NFKC", label).lower())
    return re.sub(r"\s", "-", value).strip("-") or "section"


def rewrite_url(href, project, page, by_source, by_repo):
    url = urlsplit(href)
    root = root_for(project, page)
    if url.scheme and url.scheme not in ("https", "http", "mailto"):
        return "#content"
    if url.netloc and not url.scheme:
        return "https:" + href
    if url.netloc == "github.com":
        parts = unquote(url.path).strip("/").split("/")
        target_project = by_repo.get("/".join(parts[:2]).lower())
        if target_project:
            if len(parts) == 2 and not url.fragment:
                return root + target_project["id"] + "/"
            if (
                len(parts) >= 5
                and parts[2] == "blob"
                and parts[3]
                in (
                    target_project["commit"],
                    target_project["branch"],
                    "main",
                    "master",
                )
            ):
                target = by_source.get((target_project["id"], "/".join(parts[4:])))
                if target:
                    return (
                        root
                        + route(target_project, target)
                        + ("#" + url.fragment if url.fragment else "")
                    )
    if url.scheme or url.netloc or not url.path:
        return href
    source = posixpath.normpath(
        posixpath.join(posixpath.dirname(page["path"]), unquote(url.path))
    )
    if url.path.startswith("/"):
        source = url.path.lstrip("/")
    target = by_source.get((project["id"], source))
    if target:
        return urlunsplit(
            ("", "", root + route(project, target), url.query, url.fragment)
        )
    return (
        project["repository"]
        + "/blob/"
        + project["commit"]
        + "/"
        + quote(source, safe="/")
        + ("#" + url.fragment if url.fragment else "")
    )


class RawHTML(HTMLParser):
    allowed = {
        "p",
        "br",
        "hr",
        "div",
        "span",
        "details",
        "summary",
        "table",
        "thead",
        "tbody",
        "tr",
        "th",
        "td",
        "a",
        "strong",
        "em",
        "b",
        "i",
        "code",
        "pre",
        "kbd",
        "sup",
        "sub",
        "blockquote",
        "ul",
        "ol",
        "li",
    }

    def __init__(self, resolver):
        super().__init__(convert_charrefs=True)
        self.output, self.resolver, self.suppressed, self.link_depth = (
            [],
            resolver,
            0,
            0,
        )

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag in {"script", "style", "iframe", "object"}:
            self.suppressed += 1
            return
        if self.suppressed:
            return
        if tag == "img":
            src = values.get("src", "")
            if src and not any(x in src for x in ("shields.io", "/badge", "badge.svg")):
                label = esc(values.get("alt") or "查看图示")
                self.output.append(
                    f'<span class="source-image">{label}</span>'
                    if self.link_depth
                    else f'<a class="source-image" href="{esc(self.resolver(src))}">{label} ↗</a>'
                )
            return
        if tag not in self.allowed:
            return
        if tag == "a":
            self.link_depth += 1
        attrs = (
            ' href="' + esc(self.resolver(values["href"])) + '"'
            if tag == "a" and values.get("href")
            else ""
        )
        if tag == "a" and re.fullmatch(r"[\w-]+", values.get("id", "")):
            attrs += ' id="' + esc(values["id"]) + '"'
        for key in ("colspan", "rowspan"):
            if tag in ("th", "td") and str(values.get(key, "")).isdigit():
                attrs += f' {key}="{values[key]}"'
        self.output.append(f"<{tag}{attrs}>")

    def handle_endtag(self, tag):
        if tag in {"script", "style", "iframe", "object"}:
            self.suppressed = max(0, self.suppressed - 1)
        elif not self.suppressed and tag in self.allowed:
            self.output.append(f"</{tag}>")
            if tag == "a":
                self.link_depth = max(0, self.link_depth - 1)

    def handle_data(self, data):
        if not self.suppressed:
            self.output.append(escape(data))


def make_markdown():
    from markdown_it import MarkdownIt

    md = MarkdownIt("commonmark", {"html": True}).enable(["table", "strikethrough"])

    def fence(tokens, index, options, env):
        token = tokens[index]
        language = token.info.strip().split()[0] if token.info.strip() else "text"
        env["code_number"] += 1
        identifier = "code-" + str(env["code_number"])
        return f'<div class="code-block"><div class="code-toolbar"><span class="code-language">{esc(language)}</span><button class="copy-button" type="button" data-copy="{identifier}" aria-label="复制 {esc(language)} 代码" hidden>复制</button></div><pre id="{identifier}" tabindex="0"><code>{escape(token.content)}</code></pre></div>\n'

    def raw(tokens, index, options, env):
        parser = RawHTML(env["resolver"])
        parser.feed(tokens[index].content)
        return "".join(parser.output)

    def image(tokens, index, options, env):
        token = tokens[index]
        source = token.attrGet("src") or ""
        if any(x in source for x in ("shields.io", "/badge", "badge.svg")):
            return ""
        label = esc(plain(token.children or []) or "查看图示")
        return (
            f'<span class="source-image">{label}</span>'
            if token.meta.get("linked")
            else f'<a class="source-image" href="{esc(env["resolver"](source))}">{label} ↗</a>'
        )

    md.renderer.rules.update(fence=fence, html_block=raw, html_inline=raw, image=image)
    md.renderer.rules["table_open"] = (
        lambda t, i, o, e: '<div class="table-wrap" role="region" aria-label="文档表格" tabindex="0"><table>\n'
    )
    md.renderer.rules["table_close"] = lambda t, i, o, e: "</table></div>\n"
    return md


def normalize_html_headings(source):
    """Promote README HTML headings without changing literal code examples."""
    output, prose, fence = [], [], None

    def flush():
        text = "".join(prose)
        output.append(
            re.sub(
                r"<h([1-6])(?:\s[^>]*)?>(.*?)</h\1>",
                lambda m: "\n"
                + "#" * int(m[1])
                + " "
                + re.sub("<[^>]+>", "", m[2])
                + "\n",
                text,
                flags=re.S | re.I,
            )
        )
        prose.clear()

    for line in source.splitlines(keepends=True):
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line.rstrip("\n"))
        if fence:
            output.append(line)
            if (
                marker
                and marker[1][0] == fence[0]
                and len(marker[1]) >= len(fence)
                and not marker[2].strip()
            ):
                fence = None
        elif marker:
            flush()
            fence = marker[1]
            output.append(line)
        else:
            prose.append(line)
    flush()
    return "".join(output)


def render_markdown(md, project, page, by_source, by_repo):
    from markdown_it.token import Token

    source = read_regular(page["file"])
    source = re.sub(r"\A---\n.*?\n---\n", "", source, flags=re.S)
    source = normalize_html_headings(source)
    resolver = lambda href: rewrite_url(href, project, page, by_source, by_repo)
    env = {"code_number": 0, "resolver": resolver}
    tokens = md.parse(source, env)
    headings, used, h1 = [], Counter(), 0
    searchable = " ".join(
        plain(t.children or []) if t.type == "inline" else t.content
        for t in tokens
        if t.type in ("inline", "fence", "code_block")
    )

    def links(items):
        depth = 0
        for token in items:
            if token.type == "link_open":
                depth += 1
                if token.attrGet("href"):
                    token.attrSet("href", resolver(token.attrGet("href")))
            elif token.type == "link_close":
                depth = max(0, depth - 1)
            elif token.type == "image":
                token.meta["linked"] = depth > 0
            if token.children:
                links(token.children)

    links(tokens)
    for i, token in enumerate(tokens):
        if token.type != "heading_open":
            continue
        level = int(token.tag[1:])
        inline = tokens[i + 1]
        label = plain(inline.children or [])
        base = heading_slug(label)
        anchor = base + ("-" + str(used[base]) if used[base] else "")
        used[base] += 1
        if anchor == "content" or re.fullmatch(r"code-\d+", anchor):
            anchor = "section-" + anchor
        token.attrSet("id", anchor)
        if level == 1:
            h1 += 1
            if h1 > 1:
                level = 2
                token.tag = "h2"
                tokens[i + 2].tag = "h2"
        if level in (2, 3):
            headings.append({"text": label, "id": anchor, "level": level})
            opening = Token("link_open", "a", 1)
            opening.attrs = {
                "class": "heading-anchor",
                "href": "#" + anchor,
                "aria-label": "链接到 " + label,
            }
            symbol = Token("text", "", 0)
            symbol.content = "#"
            inline.children = (inline.children or []) + [
                opening,
                symbol,
                Token("link_close", "a", -1),
            ]
    rendered = md.renderer.render(tokens, md.options, env)
    rendered = re.sub(r"<a\b(?![^>]*\bid=)[^>]*>\s*</a>", "", rendered)
    if not h1:
        rendered = (
            f'<h1 id="page-title">{esc(project["id"] if not page["slug"] else page["title"])}</h1>\n'
            + rendered
        )
    if not page["slug"]:
        rendered = rendered.replace(
            "</h1>",
            '</h1><p class="project-intro">' + esc(project["summary"]) + "</p>",
            1,
        )
    toc = (
        '<ul class="toc-list">'
        + "".join(
            f'<li class="toc-level-{h["level"]}"><a href="#{esc(h["id"])}">{esc(h["text"])}</a></li>'
            for h in headings
        )
        + "</ul>"
        if headings
        else ""
    )
    return rendered, toc, " ".join(searchable.split())


def template(values):
    source = read_regular("templates/docs.html")
    missing = set(re.findall(r"{{([A-Z_]+)}}", source)) - values.keys()
    if missing:
        raise BuildError(f"Unfilled template: {sorted(missing)}")
    return re.sub(r"{{([A-Z_]+)}}", lambda m: values[m[1]], source)


def project_menu(projects, current, root):
    return (
        "<ul>"
        + "".join(
            f'<li><a href="{root}{esc(p["id"])}/"'
            + (' aria-current="page"' if p["id"] == current else "")
            + f'>{esc(p["id"])}</a></li>'
            for p in sorted(projects, key=lambda p: p["id"].lower())
        )
        + "</ul>"
    )


def sidebar(project, page):
    root = root_for(project, page)
    parts = [
        f'<nav class="sidebar-nav" aria-label="{esc(project["id"])} 文档"><div class="nav-group"><p class="nav-label">{esc(project["id"])}</p><ul>'
    ]
    for p in project["pages"]:
        active = ' aria-current="page"' if p["slug"] == page["slug"] else ""
        parts.append(
            f'<li><a class="nav-link" href="{root}{route(project,p)}"{active}>{esc(p["title"])}</a></li>'
        )
    return (
        "".join(parts)
        + f'</ul></div><div class="nav-group"><p class="nav-label">Project Z</p><ul><li><a class="nav-link" href="{root}#projects">全部项目</a></li></ul></div></nav>'
    )


def pagination(project, page):
    index = project["pages"].index(page)
    parts = []
    for delta, direction, label in ((-1, "prev", "上一页"), (1, "next", "下一页")):
        target = index + delta
        if 0 <= target < len(project["pages"]):
            p = project["pages"][target]
            parts.append(
                f'<a class="pagination-link {direction}" href="{root_for(project,page)}{route(project,p)}"><span class="pagination-label">{label}</span><span class="pagination-title">{esc(p["title"])}</span></a>'
            )
    return "".join(parts)


def home_content(projects, curation):
    categories = {c["id"]: c for c in curation["categories"]}
    counts = Counter(p["category"] for p in projects)
    total = sum(len(p["pages"]) for p in projects)
    parts = [
        '<section class="portal-hero"><p class="eyebrow">PROJECT Z / DOCUMENTATION</p><h1 id="welcome">从基础库，<br>到日常工具。</h1><p class="intro">独立、专注、可以组合。查阅每个项目的用法、接口与工作方式，从你需要的那一块开始。</p></section>',
        f'<div class="portal-stats"><div><strong>{len(projects)}</strong><span>个项目</span></div><div><strong>{total}</strong><span>篇文档</span></div><div><strong>{len(categories)}</strong><span>个领域</span></div></div>',
        '<section aria-labelledby="start"><h2 id="start">从这里开始</h2><div class="portal-featured">',
    ]
    names = {p["id"] for p in projects}
    for name, title, detail in (
        ("oh-my-ztty", "搭建终端工作台", "终端、Shell、配置与系统工具"),
        ("ssmcp", "让 Agent 连接工作区", "远程执行、工具与会话"),
        ("zgpui", "构建原生界面", "场景、布局与窗口后端"),
    ):
        if name in names:
            parts.append(
                f'<a class="feature-link" href="{name}/"><strong>{title} <span aria-hidden="true">↗</span></strong><span>{detail}</span><span class="feature-project">{name}</span></a>'
            )
    parts.append(
        '</div></section><section class="portal-catalog" aria-labelledby="projects"><h2 id="projects">全部项目</h2><p>按用途浏览，或直接搜索项目名称。</p><div class="catalog-toolbar"><label class="visually-hidden" for="project-filter">搜索项目</label><input id="project-filter" type="search" placeholder="搜索项目…" autocomplete="off"><span id="project-count" aria-live="polite">'
        + str(len(projects))
        + ' 个项目</span></div><div class="category-filters" aria-label="项目分类"><button type="button" data-category="all" aria-pressed="true">全部</button>'
    )
    for c in curation["categories"]:
        parts.append(
            f'<button type="button" data-category="{c["id"]}" aria-pressed="false">{esc(c["label"])} <span>{counts[c["id"]]}</span></button>'
        )
    parts.append('</div><ul id="project-list">')
    for p in sorted(
        projects, key=lambda p: (list(categories).index(p["category"]), p["id"].lower())
    ):
        name = p["id"]
        category = categories[p["category"]]
        search = " ".join(
            [name, p["summary"], category["label"], category["english"], p["kind"]]
        )
        parts.append(
            f'<li data-project="{esc(name)}" data-category="{p["category"]}" data-search="{esc(search)}"><article class="project-card"><div class="card-topline"><span>{esc(category["label"])}</span><span>{KINDS[p["kind"]]}</span></div><h3><a href="{name}/">{esc(name)} <span aria-hidden="true">↗</span></a></h3><p class="card-description">{esc(p["summary"])}</p><div class="card-links"><a href="{name}/">阅读文档 <span aria-hidden="true">→</span></a><a href="{esc(p["repository"])}" aria-label="{esc(name)} 源码">源码 ↗</a><span>{len(p["pages"])} 篇</span></div></article></li>'
        )
    parts.append(
        '</ul><p id="catalog-empty" hidden>没有找到匹配的项目。试试其他关键词或选择全部分类。</p></section><section><h2 id="about">小模块，各司其职。</h2><p>Project Z 由独立维护的库、工具与应用组成。每个项目保留自己的源码、许可证和发布方式；在这里，用同一套导航找到介绍、安装方法和使用指南。</p><p>各页保留对应的原始文档链接。支持范围、命令和版本说明以该页记录的源文档为准。</p></section>'
    )
    return "\n".join(parts)


class HTMLReferences(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids = set()
        self.duplicates = set()
        self.links = []
        self.h1 = 0

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        self.h1 += tag == "h1"
        if values.get("id"):
            value = values["id"]
            if value in self.ids:
                self.duplicates.add(value)
            self.ids.add(value)
        for key in ("href", "src"):
            if values.get(key):
                self.links.append(
                    (
                        values[key],
                        key == "src"
                        or tag == "link"
                        and values.get("rel") in ("stylesheet", "icon"),
                    )
                )


def validate_site(output, base_url=DEFAULT_BASE):
    output = Path(output).resolve()
    docs = {}
    base = urlsplit(base_url)
    for file in output.rglob("*.html"):
        doc = HTMLReferences()
        doc.feed(file.read_text())
        if doc.duplicates or doc.h1 != 1:
            raise BuildError(
                f"{file.relative_to(output)}: duplicate IDs {sorted(doc.duplicates)}; H1 count {doc.h1}"
            )
        docs[file.resolve()] = doc
    checked = 0
    for file, doc in docs.items():
        for href, asset in doc.links:
            url = urlsplit(href)
            if url.scheme or url.netloc:
                if asset:
                    raise BuildError(f"External runtime asset: {href}")
                if url.scheme not in ("https", "http", "mailto"):
                    raise BuildError(f"Unsafe link: {href}")
                continue
            if url.path.startswith("/"):
                if not url.path.startswith(base.path):
                    raise BuildError(f"Link leaves site prefix: {href}")
                target = output / unquote(url.path[len(base.path) :])
            else:
                target = file.parent / unquote(url.path) if url.path else file
            target = target.resolve()
            if target.is_dir() or url.path.endswith("/"):
                target /= "index.html"
            if not target.is_relative_to(output) or not target.is_file():
                raise BuildError(
                    f"{file.relative_to(output)}: missing local target {href}"
                )
            if (
                url.fragment
                and target.suffix == ".html"
                and unquote(url.fragment) not in docs[target.resolve()].ids
            ):
                raise BuildError(f"{file.relative_to(output)}: missing heading {href}")
            checked += 1
    return checked


def build(output, base_url=DEFAULT_BASE):
    parsed = urlsplit(base_url)
    if parsed.scheme != "https" or not parsed.netloc or parsed.query or parsed.fragment:
        raise BuildError("Use an absolute HTTPS site base")
    base_url = base_url.rstrip("/") + "/"
    output = Path(output)
    if output.is_symlink():
        raise BuildError("Output must not be a symlink")
    output = output.resolve()
    if output == SITE or SITE.is_relative_to(output):
        raise BuildError("Output must not contain source files")
    if output.exists() and not (output / MARKER).is_file():
        raise BuildError(f"Refusing to replace unmarked directory: {output}")
    data, curation, projects = load_sources()
    md = make_markdown()
    by_source = {(p["id"], d["path"]): d for p in projects for d in p["pages"]}
    by_repo = {
        p["repository"].removeprefix("https://github.com/").lower(): p for p in projects
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".docs-build-", dir=output.parent))
    old = None
    try:
        search = []
        routes = [""]
        for project in projects:
            for page in project["pages"]:
                content, toc, body = render_markdown(
                    md, project, page, by_source, by_repo
                )
                root = root_for(project, page)
                name = project["id"]
                values = {
                    "PAGE_TITLE": esc(name + " · " + page["title"] + " · Project Z"),
                    "PAGE_DESCRIPTION": esc(project["summary"]),
                    "ROOT": root,
                    "PROJECT_NAME": esc(name),
                    "PROJECT_HOME": root + name + "/",
                    "REPOSITORY": esc(project["repository"]),
                    "SIDEBAR": sidebar(project, page),
                    "BREADCRUMB": f'<a href="{root}">Project Z</a><span aria-hidden="true">/</span><a href="{root}{name}/">{esc(name)}</a><span aria-hidden="true">/</span><span>{esc(page["title"])}</span>',
                    "CONTENT": content,
                    "TOC": toc,
                    "SOURCE": f'<a href="{esc(page["source"])}">查看原始文档 ↗</a><a href="{esc(project["repository"])}">项目仓库与许可证 ↗</a>',
                    "PAGINATION": pagination(project, page),
                    "PROJECT_MENU": project_menu(projects, name, root),
                    "PAGE_KIND": "project",
                    "UPDATED_AT": display_date(data["generated_at"]),
                }
                rendered = template(values).replace(
                    "</head>",
                    f'<link rel="canonical" href="{esc(base_url+route(project,page))}">\n</head>',
                )
                target = staging / route(project, page) / "index.html"
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(rendered)
                routes.append(route(project, page))
                search.append(
                    {
                        "title": page["title"],
                        "project": name,
                        "body": project["summary"] + " " + body,
                        "url": route(project, page),
                    }
                )
        names = {p["id"] for p in projects}
        home_nav = (
            '<nav class="sidebar-nav" aria-label="文档导航"><div class="nav-group"><p class="nav-label">文档</p><ul><li><a class="nav-link" href="#welcome" aria-current="page">Project Z</a></li><li><a class="nav-link" href="#start">从这里开始</a></li><li><a class="nav-link" href="#projects">全部项目</a></li></ul></div><div class="nav-group"><p class="nav-label">常用入口</p><ul>'
            + "".join(
                f'<li><a class="nav-link" href="{n}/">{n}</a></li>'
                for n in (
                    "oh-my-ztty",
                    "ztty",
                    "ssmcp",
                    "zuse",
                    "zmem",
                    "zharness",
                    "zgpui",
                )
                if n in names
            )
            + "</ul></div></nav>"
        )
        home = {
            "PAGE_TITLE": "Project Z 文档 · 从基础库，到日常工具",
            "PAGE_DESCRIPTION": "Project Z 全部项目的使用指南、接口与原理。统一的文档导航、搜索和快速开始。",
            "ROOT": "./",
            "PROJECT_NAME": "Project Z",
            "PROJECT_HOME": "./",
            "REPOSITORY": "https://github.com/LIghtJUNction/project-z",
            "SIDEBAR": home_nav,
            "BREADCRUMB": "<span>文档 / 总览</span>",
            "CONTENT": home_content(projects, curation),
            "TOC": '<ul class="toc-list"><li><a href="#start">从这里开始</a></li><li><a href="#projects">全部项目</a></li><li><a href="#about">关于 Project Z</a></li></ul>',
            "SOURCE": '<a href="https://github.com/LIghtJUNction/project-z/tree/main/site">改进文档 ↗</a><a href="./design-license.txt">设计许可</a>',
            "PAGINATION": "",
            "PROJECT_MENU": project_menu(projects, None, "./"),
            "PAGE_KIND": "home",
            "UPDATED_AT": display_date(data["generated_at"]),
        }
        (staging / "index.html").write_text(
            template(home).replace(
                "</head>", f'<link rel="canonical" href="{esc(base_url)}">\n</head>'
            )
        )
        prefix = parsed.path.rstrip("/") + "/"
        error = {
            **home,
            "ROOT": prefix,
            "PROJECT_HOME": prefix,
            "PAGE_TITLE": "页面未找到 · Project Z",
            "PAGE_KIND": "project",
            "CONTENT": f'<h1 id="page-not-found">页面未找到</h1><p>这个地址可能已经调整。<a href="{esc(prefix)}">返回全部项目</a>，或搜索你需要的文档。</p>',
            "BREADCRUMB": "404",
            "SIDEBAR": f'<nav class="sidebar-nav"><a class="nav-link" href="{esc(prefix)}">全部项目</a></nav>',
            "TOC": "",
            "SOURCE": "",
            "PROJECT_MENU": project_menu(projects, None, prefix),
        }
        (staging / "404.html").write_text(template(error))
        for name in ("docs.css", "docs.js", "favicon.svg", "theme-init.js"):
            if (SITE / "assets" / name).is_file():
                (staging / name).write_text(read_regular("assets/" + name))
        (staging / "search-index.json").write_text(
            json.dumps(search, ensure_ascii=False, separators=(",", ":")) + "\n"
        )
        public = {
            "schema_version": 2,
            "generated_at": data["generated_at"],
            "projects": [
                {k: p[k] for k in ("id", "summary", "category", "repository", "commit")}
                | {"url": p["id"] + "/", "pages": len(p["pages"])}
                for p in projects
            ],
        }
        (staging / "projects.json").write_text(
            json.dumps(public, ensure_ascii=False, indent=2) + "\n"
        )
        (staging / "sitemap.xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + "".join(
                "<url><loc>" + xml_escape(base_url + r) + "</loc></url>\n"
                for r in routes
            )
            + "</urlset>\n"
        )
        (staging / "design-license.txt").write_text(
            read_regular("THIRD_PARTY_NOTICES.md")
        )
        (staging / "robots.txt").write_text(
            "User-agent: *\nAllow: /\nSitemap: " + base_url + "sitemap.xml\n"
        )
        (staging / ".nojekyll").write_text("")
        (staging / MARKER).write_text("Project Z documentation output\n")
        checked = validate_site(staging, base_url)
        result = {
            "projects": len(projects),
            "documentation_pages": len(search),
            "html_pages": len(search) + 2,
            "local_links_checked": checked,
            "bytes": sum(f.stat().st_size for f in staging.rglob("*") if f.is_file()),
            "excluded": data.get("excluded", []),
            "output": str(output),
        }
        if output.exists():
            old = Path(tempfile.mkdtemp(prefix=".docs-previous-", dir=output.parent))
            old.rmdir()
            output.rename(old)
        try:
            staging.rename(output)
        except BaseException:
            if old:
                old.rename(output)
                old = None
            raise
        if old:
            shutil.rmtree(old)
        return result
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=SITE / "dist")
    parser.add_argument("--base-url", default=DEFAULT_BASE)
    args = parser.parse_args()
    try:
        print(
            json.dumps(build(args.output, args.base_url), ensure_ascii=False, indent=2)
        )
    except (BuildError, KeyError, OSError, ImportError) as exc:
        print(f"Documentation build failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
