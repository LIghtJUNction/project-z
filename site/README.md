# Project Z documentation

This site gives every registered Project Z repository a dedicated documentation address, with the warm Ink design extracted from [oh-my-ztty](https://lightjunction.github.io/oh-my-ztty/). The public portal is [lightjunction.github.io/project-z-site](https://lightjunction.github.io/project-z-site/).

The pages contain complete, pre-rendered documentation. JavaScript adds project filtering, full-text search, theme switching and code copying. Navigation and reading work without it. Styles, scripts and the search index are served locally; no analytics, external fonts or application API is required.

## Build and preview

Use Python 3.11 or later. Install the same pinned Markdown renderer used by oh-my-ztty:

```sh
python3 -m venv site/.cache/venv
site/.cache/venv/bin/python -m pip install --require-hashes -r site/requirements.txt
site/.cache/venv/bin/python site/scripts/check.py
site/.cache/venv/bin/python site/scripts/build.py
python3 -m http.server 8000 --bind 127.0.0.1 --directory site/dist
```

Open `http://127.0.0.1:8000/`. A project overview lives at `/<project>/`; its guides live at `/<project>/<chapter>/`. `--base-url` changes canonical and sitemap URLs when hosting under another prefix.

## Source documents and introductions

`content-manifest.json` records each public repository, exact default-branch commit, source path and local Markdown file. `content/projects/` contains the source documents. Chinese READMEs are preferred when available. The collector follows existing links to installation, configuration, API and other user guides, with up to twelve pages per project; it excludes operational reports, internal records and test evidence. Links to further source files remain available in the rendered document.

The project scope comes from the aggregate `catalog.json`. The explicitly listed additional project, zchat, identifies itself as Project Z in its public README. Repository names alone do not establish membership.

Refresh public documents in the development workspace:

```sh
python3 site/scripts/collect_docs.py --inventory
python3 site/scripts/collect_docs.py
python3 site/scripts/collect_docs.py --only ztty zuse
```

The collector uses anonymous public GitHub metadata and immutable source URLs, with a local ignored download cache. An HTTP failure does not establish that a repository is private. A failed refresh returns an error and preserves the previous complete project snapshot.

`curation.json` supplies the reviewed Chinese introductions and six browsing categories. New projects must be covered there before a build succeeds. Introductions describe observable behavior and retain the distinction between currently implemented features and plans. Commands, prerequisites and limitations remain in their original source context.

## Rendering and checks

The renderer uses CommonMark, tables and strikethrough. It escapes code, strips active content and event attributes from source HTML, gives headings unique anchors and rewrites collected Markdown links to local pages. Other source links point at the recorded commit. Source figures remain links to their originals, keeping the static documentation independent of external image services.

The build checks every local page, asset and fragment before replacing the previous output. `check.py` also verifies registered-project coverage, search-route completeness, unsafe HTML handling, literal code, table wrappers, nested links and duplicate headings. A failed build leaves the previous complete site in place.

Browser acceptance covers the catalog, category and text filtering, global search and empty results, code copying, keyboard access, dark/light theme persistence, project switching and mobile navigation. Review representative short and long pages at desktop and narrow widths. Generated screenshots belong in ignored `site/_validation/`, never in source history.

The [2026-11-22 acceptance record](evidence/documentation-20261122.json) records the 49-project coverage, source hashes, static checks, observed browser interactions and the limits of the narrow-screen check.

## Publish

The source and build tools live in `LIghtJUNction/project-z`. The generated site is published from `LIghtJUNction/project-z-site`, whose GitHub Pages source is the root of `main`.

Only copy the built `site/dist/` contents into the public website checkout, preserving its Git metadata and README. Do not copy the source checkout, collector cache, configuration files or validation screenshots. Review the exact generated paths before committing. A push to the public website repository runs its Pages deployment; check the live homepage and representative nested documentation URLs after it completes.

The manually invoked source-repository workflow installs the pinned renderer, checks the stored public documentation snapshot and exports the static bundle. It does not alter source dependencies or repository visibility.

## Design source

The design comes from oh-my-ztty commit `69771be7940818548d851dc1038424ac2c614638`: warm dark and light palettes, system typography, the `z_` wordmark, a three-column reading layout, restrained separators and responsive native navigation. It is also available as the reusable **Oh My Ztty 文档风格** (`oh-my-ztty-docs`) skill. The portal adds a project directory and cross-project search while using those same tokens and layout rules.

See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for design attribution. Each source project retains its own license, linked from its documentation.
