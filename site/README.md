# Project Z public site

This directory builds the Project Z introduction page with plain HTML, CSS and JavaScript. Python 3.11 or newer is used only to prepare and check the static files. The deployed page needs no package manager, framework, font service, analytics or runtime API request.

## Build and preview

```sh
python3 site/scripts/check.py
python3 site/scripts/build.py
python3 -m http.server 8000 --bind 127.0.0.1 --directory site/dist
```

Open the localhost address in a separate browser profile. Search and categories progressively enhance an already complete HTML list. With JavaScript disabled or unavailable, every project and its source/documentation links remain present.

## Public data and sources

`curation.json` contains the reviewed project IDs, categories and short descriptions. `projects.json` contains only confirmed public repository metadata, public README hashes, source-version references and verified crates.io versions/checksums. Source versions are labelled separately from published crate versions. The page counts are generated from those records.

Descriptions summarize the corresponding public README or published crate description. They do not claim performance rankings or completed platform validation. Retired UI package entries are excluded.

Refresh reviewed entries with:

```sh
python3 site/scripts/refresh_public.py
python3 site/scripts/refresh_public.py --only zrc zgpui
python3 site/scripts/refresh_public.py --verify-only
```

The refresh checks public visibility before fetching project content and matches Cargo package ownership to the public repository. It preserves the existing snapshot if a request or validation fails. Rate limits are errors, not evidence that a project is private or unpublished. An optional ephemeral `GH_TOKEN` or `GITHUB_TOKEN` is sent only to the official GitHub API and is never copied into generated data.

## Deployment boundary

The build reads no aggregate catalog, submodule or application configuration. It writes exactly six files:

- `index.html`
- `style.css`
- `app.js`
- `favicon.svg`
- `projects.json`
- `.nojekyll`

Only `site/dist` is a deployment artifact. The builder rejects extra snapshot fields, nonpublic repository records, unreviewed project IDs, foreign documentation/crate links and output directories containing unrelated files. It also rejects symlinked build inputs.

The manual Pages workflow verifies current public visibility and the exact published crate versions, then uploads only this directory. It does not change repository visibility or initialize submodules. Deployment configuration and final workflow dispatch belong to the repository maintainer.

The intended separate public repository, `LIghtJUNction/project-z-site`, should receive only the six generated files and its own minimal deployment workflow. All asset paths also work under its `/project-z-site/` prefix. Do not copy the aggregate checkout or its catalog into that repository.

## Local review

With Node.js 22 or newer and Chromium already installed, run:

```sh
node site/scripts/check_browser.mjs
```

Set `CHROMIUM` to an alternate executable path when needed. Screenshots and the acceptance report are written to the ignored `site/_validation` directory. The browser uses a fresh temporary profile and a loopback-only server, both closed after validation.

`site/scripts/check.py` verifies the output boundary, pre-rendered fallback, escaping and rejection of private/unreviewed data. Browser acceptance uses an isolated, unsigned-in Chromium profile and checks desktop/mobile layout, search, category selection, keyboard access, empty results and the JavaScript-disabled view.

The action interfaces were read from the official action repositories: [checkout v4](https://github.com/actions/checkout/tree/v4), [configure-pages v5](https://github.com/actions/configure-pages/tree/v5), [upload-pages-artifact v3](https://github.com/actions/upload-pages-artifact/tree/v3) and [deploy-pages v5](https://github.com/actions/deploy-pages/tree/v5). Ordinary source pushes do not dispatch deployment.

## Visual reference

The warm Ink palette, restrained borders and z_ family wordmark follow the public [oh-my-ztty website](https://lightjunction.github.io/oh-my-ztty/). The page starts in warm dark mode and offers a warm light theme; the selection stays in local browser storage. Reference sources are [styles](https://github.com/LIghtJUNction/oh-my-ztty/blob/6d95c7eaa1a4ef27df2ae246edd7bddde5f3b31b/site/style.css), [wordmark/template](https://github.com/LIghtJUNction/oh-my-ztty/blob/6d95c7eaa1a4ef27df2ae246edd7bddde5f3b31b/site/template.html) and [favicon](https://github.com/LIghtJUNction/oh-my-ztty/blob/6d95c7eaa1a4ef27df2ae246edd7bddde5f3b31b/site/favicon.svg). The catalog layout is specific to this page.

The saved [2026-11-20 validation record](VALIDATION.md) includes the before/after screenshots, browser checks and hashes of the six-file bundle.
