# Development

Use this workspace to change a component, validate its integration and prepare a suite release. Development follows each component's latest default branch. The suite records the observed revisions and builds that exact source combination.

## Clone the workspace

```sh
git clone --recurse-submodules https://github.com/LIghtJUNction/oh-my-ztty.git
cd oh-my-ztty
python3 scripts/workspace.py status
```

Development uses Git, Python 3, make, zsh and the Rust toolchain required by the component you change. Installation from a release does not need Rust or Python.

Use a machine-readable view when integrating with another tool:

```sh
python3 scripts/workspace.py status --json
```

Status reads local repository state and makes no network request.

## Validate a change

```sh
python3 scripts/workspace.py check
```

This runs the zshard, zdot, zrc, zfetch and zmem checks, then the suite's installer and integration tests. Use `--component suite` for the suite checks alone. Full ztty and ssmcp test suites remain in their own repositories; the bundle build compiles their programs and subsequent smoke tests exercise the integration.

Run the relevant checks locally after a change. Manual validation workflows are available. Routine code pushes and pull requests do not start a duplicate daily test matrix.

Keep [benchmark runs](performance.md#reproduce-a-result) separate from correctness checks, and record the source, binary, machine, configuration and workload behind each number.

## Work in a submodule

A freshly cloned submodule starts at a detached commit. Create a branch before editing:

```sh
git -C components/zshard switch -c improve-completion
make -C components/zshard check
```

Commit component changes and merge them into the repository's default branch before synchronizing the suite. Review the parent gitlink together with its source-lock record.

## Synchronize default branches

Synchronize the current default-branch heads of all seven components:

```sh
python3 scripts/workspace.py sync
python3 scripts/workspace.py check
```

Sync resolves the live default branch of each canonical GitHub repository, fetches its observed head, checks out that source and updates nested submodules recursively. `dependencies.lock.json` schema 2 records the repository URL, branch, exact commit and observation time; its top-level timestamp records the completed synchronization. Commit the changed gitlinks and source lock together after validation.

The first migration from the old release-asset lock requires a full `sync`. Once schema 2 is present, an optional component limits the update:

```sh
python3 scripts/workspace.py sync zshard
```

Every synchronization observes the current remote head again. The saved commit identifies the input selected for a build. Component publication and suite publication remain separate, explicit steps.

### Local state and recovery

Sync requires clean selected source checkouts, including initialized nested repositories, and a committed dependency lock. It refuses a nonempty uninitialized submodule directory and preserves its contents.

Ignored paths in an initialized nested repository are also refused. These paths may be ordinary build caches; the restriction exists because Git's recursive checkout can overwrite ignored files. The error names the repository and paths to move aside. An ignored cache at the component's top level can remain if it does not collide with the new revision.

The source lock is replaced after all selected checkouts succeed. If an update fails, sync attempts to restore the changed component and nested commits, their checkout branches, and saved submodule URL configuration. It leaves the lock unchanged and preserves concurrent lock edits. Newly initialized directories can remain and are listed for inspection.

A failed recovery is reported alongside the original failure. For example, a source edit made while sync is running can prevent Git from restoring an old checkout. Inspect the reported paths before retrying.

## Build the source-locked bundle

```sh
python3 scripts/build_bundle.py
python3 scripts/smoke_bundle.py "dist/oh-my-ztty-$(cat VERSION)-linux-$(uname -m).tar.gz"
```

The build requires all seven checkouts to be clean and match schema 2's recorded commits. It compiles ztty, ssmcp, zdot, zfetch and zmem with Cargo's `--locked --release` options. The ztty build enables Wayland, and ssmcp's JavaScript helper is copied from its matching source checkout. `BUILD.json` records the component commits, branch names and source-lock synchronization time.

Cargo discovers executable paths through its build output and respects the user's configured target directory, including shared output caches. Native builds use normal release outputs. A different `--arch` selects a cross target and requires its Rust standard library, linker and system development libraries. The resulting executable architecture is checked before packaging.

See [the release workflow](https://github.com/LIghtJUNction/oh-my-ztty/blob/main/.github/workflows/release.yml) for the native development libraries. Builds consume the source lock without refreshing component branches; use `workspace.py sync` to select newer sources. Source and lock consistency are checked again before the archive is written.

## Bump and release

Prepare the suite's next version with:

```sh
python3 scripts/bump.py patch
```

This updates version files for review. In the suite it also synchronizes the current release version and installation examples in the documentation. Historical performance results and release evidence keep their original version links. Use `minor` or `major` when appropriate.

From a clean, validated main branch, the release form checks, commits, tags and pushes:

```sh
python3 scripts/bump.py patch --release
```

Synchronize component sources, validate the assembled bundle, then bump oh-my-ztty when preparing publication. The suite's release-tag workflow builds and validates Linux x86_64 and ARM64 on native runners. Historical releases retain their original source and evidence; the [0.2.6 report](https://github.com/LIghtJUNction/oh-my-ztty/blob/main/docs/reports/0.2.6/release.zh-CN.md) describes that shipped version.

## Release evidence

A release record should identify the source lock, seven gitlinks, archive checksums, local check results and a full installation lifecycle. Store text measurements and artifact links in Git; keep generated screenshots and release archives in the artifact destination.

Use `--no-memory-manager` when testing in an isolated home so bundle tests leave the host services alone. Validate system adoption separately through zmem. Install twice in that home, exercise the actual shell and bundled programs, then uninstall. Include pre-existing files so preservation checks test real data. Keep startup, first completion, live memory and active AI sessions as distinct measurement scopes.

The [0.1.1 report](https://github.com/LIghtJUNction/oh-my-ztty/blob/main/docs/reports/release-0.1.1.md) shows the evidence format. The [formal workflow](https://github.com/LIghtJUNction/oh-my-ztty/actions/runs/44609624654) and [public download audit](https://github.com/LIghtJUNction/oh-my-ztty/blob/main/docs/reports/public-release-0.1.1.json) verify the published result.

## Edit this documentation

Pages are Markdown files in `site/content/`. Navigation is declared in `site/nav.json`. The build produces static HTML for GitHub Pages.

Create the isolated build environment and render the site:

```sh
python3 -m venv .cache/docs-venv
.cache/docs-venv/bin/python -m pip install --require-hashes -r site/requirements.txt
.cache/docs-venv/bin/python scripts/build_site.py
```

Preview the generated pages locally:

```sh
python3 -m http.server 8765 --bind 127.0.0.1 --directory _site
```

Check desktop and narrow layouts, keyboard navigation, search, copy controls and links before publishing a site change. The Pages workflow handles website deployment independently of binary releases.

See [the site authoring guide](https://github.com/LIghtJUNction/oh-my-ztty/blob/main/site/README.md) and [repository contribution guide](https://github.com/LIghtJUNction/oh-my-ztty/blob/main/CONTRIBUTING.md).
