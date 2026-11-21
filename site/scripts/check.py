#!/usr/bin/env python3
"""Check documentation coverage, safe rendering and the complete static build."""

from __future__ import annotations
import json
from pathlib import Path
import tempfile
from unittest.mock import patch
import build


def rendering_regressions():
    project = {
        "id": "ztest",
        "repository": "https://github.com/example/ztest",
        "branch": "main",
        "commit": "a" * 40,
        "summary": "Test project",
    }
    page = {
        "slug": "guide",
        "path": "docs/guide.md",
        "file": "fixture.md",
        "title": "Guide",
    }
    target = {"slug": "", "path": "README.md"}
    by_source = {("ztest", "README.md"): target}
    by_repo = {"example/ztest": project}
    source = """# Guide

[Overview](../README.md#start)

<script>alert("unsafe")</script>

<a href="javascript:alert(1)" onclick="bad()">unsafe link</a>

<a id="manual-anchor"></a>

## Repeated

## Repeated

```sh
printf '<script>literal</script><h1>literal heading</h1>'
```

| Key | Value |
| --- | --- |
| safe | text |
"""
    with patch.object(build, "read_regular", return_value=source):
        html, toc, text = build.render_markdown(
            build.make_markdown(), project, page, by_source, by_repo
        )
    assert 'href="../../ztest/#start"' in html, "Nested Markdown link did not resolve"
    assert (
        "<script>" not in html and "onclick=" not in html and "javascript:" not in html
    ), "Raw HTML bypassed safe rendering"
    assert (
        "&lt;script&gt;literal&lt;/script&gt;&lt;h1&gt;literal heading&lt;/h1&gt;"
        in html
    ), "Code text must remain literal"
    assert (
        'id="repeated"' in html and 'id="repeated-1"' in html
    ), "Repeated headings need unique anchors"
    assert (
        'class="table-wrap"' in html and 'data-copy="code-1"' in html
    ), "Table or code interactions lost their markup"
    assert (
        'href="#repeated-1"' in toc and "printf" in text
    ), "Search or outline lost content"
    assert (
        build.rewrite_url("mailto:dev@example.com", project, page, by_source, by_repo)
        == "mailto:dev@example.com"
    )
    assert (
        build.rewrite_url(
            "https://github.com/example/ztest", project, page, by_source, by_repo
        )
        == "../../ztest/"
    )
    assert (
        build.rewrite_url("other.md", project, page, by_source, by_repo)
        == project["repository"] + "/blob/" + project["commit"] + "/docs/other.md"
    )


def check():
    rendering_regressions()
    data, _, projects = build.load_sources()
    canonical = json.loads((build.SITE.parent / "catalog.json").read_text())
    expected = {p["name"] for p in canonical["repositories"]}
    covered = {p["id"] for p in projects}
    excluded = {p["id"] for p in data.get("excluded", [])}
    missing = expected - covered - excluded
    assert not missing, f"Missing registered projects: {sorted(missing)}"
    with tempfile.TemporaryDirectory(prefix="project-z-docs-check-") as directory:
        result = build.build(Path(directory) / "site")
        output = Path(result["output"])
        index = json.loads((output / "search-index.json").read_text())
        assert len(index) == sum(len(p["pages"]) for p in projects)
        assert len({entry["url"] for entry in index}) == len(
            index
        ), "Duplicate search routes"
        assert all((output / entry["url"] / "index.html").is_file() for entry in index)
        assert not any(
            p.suffix in {".md", ".py", ".toml", ".log", ".env"}
            for p in output.rglob("*")
            if p.is_file()
        ), "Source or runtime data leaked into public bundle"
        result.pop("output")
        result["registered_projects"] = len(expected)
        result["additional_projects"] = sorted(covered - expected)
        result["rendering_regressions"] = "passed"
        return result


if __name__ == "__main__":
    print(json.dumps(check(), ensure_ascii=False, indent=2))
