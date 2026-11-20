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

The CSS, JavaScript, favicon and no-Jekyll marker are unchanged. The existing static checks and six-file build boundary passed again; the original visual acceptance images remain the evidence for the unchanged design. The file hashes and live checks for this published snapshot are in the release refresh record.

The refreshed site was deployed from public commit [668080bc](https://github.com/LIghtJUNction/project-z-site/commit/668080bced1eb4c9941e324abc09e645d6e881f3). Its [Pages workflow](https://github.com/LIghtJUNction/project-z-site/actions/runs/44699517717) completed successfully. Live HTTPS checks of the root page and all six files returned HTTP 200 and matched the built byte counts and SHA-256 hashes; the served manifest contained the five updated crate versions and the oh-my-ztty 0.2.4 source version. Exact URLs, hashes and the verification time are saved in the refresh record.

## Published 39-project data refresh

The published site contains 39 projects and 29 verified crates. It adds zi18n and zguard and refreshes all reviewed source and registry records. Source labels describe the public default branch, including oh-my-ztty `0.2.6` from `VERSION`. Registry labels describe verified published crates, including ztty `0.5.2`, zharness `0.6.0`, zgpui `0.1.5` and zcall `0.4.0`. Those versions are independent of the frozen aggregate’s accepted zgpui `0.1.2` source snapshot.

Verification used official GitHub repository metadata captured at `2026-11-20T10:41:56Z` and fresh exact-version crates.io responses. The eight focused refresh tests, static checker and six-file build passed. The template, CSS, JavaScript and favicon match the historical design bytes. The [candidate receipt](evidence/public-data-refresh-20261120.json) records the scoped source pins, capture provenance, version changes and six file hashes. The [current bundle manifest](evidence/bundle-manifest.json) records the six hashes of this publication.

The final aggregate commit `522bc7c` and root receipt commit `78fc357` bind the reviewed site input. Only the oh-my-ztty pin changed among the 39 reviewed repositories. The public default branch points to that pin and both references return the same `0.2.6` VERSION bytes.

[Public commit 5bdd99d](https://github.com/LIghtJUNction/project-z-site/commit/5bdd99dc749de86482f1bafb525693c2acc66b85) deployed through one successful [Pages run 44723433069](https://github.com/LIghtJUNction/project-z-site/actions/runs/44723433069). At `2026-11-20T10:57:45.516128+00:00`, the site root and all six files returned HTTP 200 with the same byte counts and SHA-256 hashes as the 121,945-byte build. The live manifest contained 39 projects and 29 verified crates. The [publication receipt](evidence/publication-20261120.json) records each live URL and digest.
