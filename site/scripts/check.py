#!/usr/bin/env python3
"""Check the deployment allowlist, public-data boundary and rendered fallback."""
import copy
import json
from pathlib import Path
import tempfile

import build


def rejected(data, curation):
    try:
        build.validate(data, curation)
    except ValueError:
        return
    raise AssertionError("unreviewed public data was accepted")


def main():
    data = json.loads((build.SITE / "projects.json").read_text())
    curation = json.loads((build.SITE / "curation.json").read_text())
    with tempfile.TemporaryDirectory(prefix="project-z-page-check-") as temporary:
        output = Path(temporary) / "site"
        result = build.build(output)
        assert {path.name for path in output.iterdir()} == build.OUTPUT_FILES
        assert all(path.is_file() and not path.is_symlink() for path in output.iterdir())
        page = (output / "index.html").read_text()
        assert page.count('<li data-project=') == len(data["projects"])
        assert "project-controls\" hidden" in page
        assert '<ul id="project-list"' in page
        assert not any(forbidden in page for forbidden in ("catalog.json", "project-z.toml", "zui-native", "/zui/"))
        # An accidental output path must not overwrite unrelated work.
        keep = output / "do-not-replace"
        keep.write_text("private")
        try:
            build.build(output)
        except ValueError:
            pass
        else:
            raise AssertionError("an output containing unrelated files was accepted")
        assert keep.read_text() == "private"
    private = copy.deepcopy(data)
    private["projects"][0]["repository"]["visibility"] = "private"
    rejected(private, curation)
    extra = copy.deepcopy(data)
    extra["private_catalog"] = {"not_for_publication": True}
    rejected(extra, curation)
    external = copy.deepcopy(data)
    external["projects"][0]["documentation"]["url"] = "https://example.com/unverified"
    rejected(external, curation)
    wrong_crate = copy.deepcopy(data)
    next(item for item in wrong_crate["projects"] if item["crate"])["crate"]["repository"] = "https://github.com/other/private"
    rejected(wrong_crate, curation)
    # Public descriptions are treated as text, even if they contain markup.
    escaped, edited = copy.deepcopy(data), copy.deepcopy(curation)
    escaped["projects"][0]["summary"] = '<script>alert("test")</script>'
    edited["projects"][0]["summary"] = escaped["projects"][0]["summary"]
    build.validate(escaped, edited)
    rendered = build.render(escaped)
    assert '<script>alert("test")</script>' not in rendered
    assert "&lt;script&gt;" in rendered
    print(json.dumps({"checks": "passed", **result}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
