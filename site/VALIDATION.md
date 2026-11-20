# Project Z page validation — 2026-11-20

The initial visual acceptance snapshot contained 37 reviewed repositories and 26 verified crate entries. Current counts come from the snapshot in [projects.json](projects.json), which records public source URLs, visibility evidence, versions and registry checksums. The build does not read the aggregate catalog.

## Visual review

The final design follows the warm palette and `z_` wordmark of [oh-my-ztty at 6d95c7e](https://github.com/LIghtJUNction/oh-my-ztty/tree/6d95c7eaa1a4ef27df2ae246edd7bddde5f3b31b/site). It starts in warm dark mode and includes a warm light theme. The saved images came from an isolated Chromium instance rendering the actual generated files.

| View | Evidence |
| --- | --- |
| Previous light/blue design | [Before desktop](evidence/before-desktop.jpg) |
| Warm dark desktop, 1440 × 1000 | [Desktop](evidence/desktop.jpg) |
| Project search and catalog | [Desktop projects](evidence/desktop-projects.jpg) |
| Mobile, 390 × 844 | [Mobile](evidence/mobile.jpg) |
| Warm light theme | [Light desktop](evidence/desktop-light.jpg) |

The screenshots were inspected for text wrapping, spacing, navigation, project links and visible focus. No horizontal overflow was observed at 1440, 768, 390 or 320 CSS pixels.

## Behavior checked

The [browser report](evidence/browser-validation.json) records the executed checks, browser version and result. The run passed with Chrome 157.0.8103.38 on the actual `/project-z-site/` subpath.

- Search by keyboard, Escape reset and Tab/Enter category selection.
- Chinese and full-width input, category intersection and URL state after reload.
- Empty results and keyboard recovery.
- Named search, navigation and main regions in the accessibility tree.
- Keyboard theme switch and persistence after reload.
- Mobile search reaching the verified zrc 0.1.2 registry entry.
- Complete project links when JavaScript is disabled or the application script fails to load.
- No page JavaScript exceptions or external page requests.

This run checks the documented flows in Chromium. It is not a claim of an exhaustive accessibility audit or cross-browser certification.

## Build and publication boundary

The following commands completed successfully:

```sh
python3 site/scripts/check.py
python3 site/scripts/build.py
node --check site/assets/app.js
node --check site/scripts/check_browser.mjs
TMPDIR=/var/tmp node site/scripts/check_browser.mjs
```

The builder produced exactly six regular files: `index.html`, `style.css`, `app.js`, `favicon.svg`, `projects.json` and `.nojekyll`. The original visual-acceptance bundle contained 116,533 bytes. The original public-manifest SHA-256 was `227cf3d7ebbccad0d82aeb093a7060a159b0827ee10589007bdbaaaa65eda4f2`. Current output hashes, updated separately from the original visual acceptance, are in [bundle-manifest.json](evidence/bundle-manifest.json).

The public destination is the separate `LIghtJUNction/project-z-site` repository. Only those six files belong in its site payload. The aggregate repository, catalog, history, local browser profiles and validation files are not part of that payload. Every asset URL is relative, so the page works under `https://lightjunction.github.io/project-z-site/`.

These are the original local acceptance results. Subsequent data and publication checks are recorded separately below.

## Published package data refresh

The [release refresh record](evidence/release-refresh-20261120.json) records the current public-source and registry checks for zfetch 0.1.1, zgpui 0.1.2, zpty 0.2.3, zterm 0.5.2 and zrc 0.1.2. The refresh also records the public oh-my-ztty 0.2.4 source version after its formal release. All 37 repositories were rechecked for active public visibility, and every displayed crate version was checked against its registry checksum. The updated page contains 27 verified crate entries.

The CSS, JavaScript, favicon and no-Jekyll marker are unchanged. The existing static checks and six-file build boundary passed again; the original visual acceptance images remain the evidence for the unchanged design. The current file hashes are in [bundle-manifest.json](evidence/bundle-manifest.json). Publication is recorded in the refresh record after the live files have been checked.
