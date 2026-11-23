# Project Z maintenance

Read README, CONTRIBUTING and the target repository's AGENTS.md. Work in isolated checkouts and preserve other sessions' branches, uncommitted work and private configuration.

## Internal dependencies

- Cross-repository Project Z Cargo dependencies use `git = "https://github.com/<owner>/<repo>.git"` and the latest default branch. Do not use a registry-only declaration, cross-repository path, fixed branch, tag or rev.
- Keep same-repository workspace/path dependencies. Preserve external dependency sources and feature boundaries.
- Internal cross-repository development declarations must not contain `version`, including publishable crates, normal/build/dev dependencies and workspace-inherited declarations. Keep package versions and lockfile versions as source identity.
- For external registry publication, use `scripts/release_projection.py` to create a separate staging manifest with exact versions from the committed lock. Compatible historical `version` + `git` inputs remain supported by that staging tool; they are not valid new development declarations.
- Update consumers in dependency order: compatibility code, Git declarations, Cargo.lock and nested source gitlinks. Commit and push those changes before recording aggregate gitlinks. A lock records one verified update; it must not keep an older source on the next synchronization.
- `python3 scripts/project_z.py sync` fetches default branches into clean, detached submodule checkouts. It records exact commits and regenerates catalog.json and docs/PROJECTS.md. It does not repair consumer source or overwrite active branches.
- `check` verifies remote freshness and internal source identities. `resolve --all` uses real Cargo `--locked` resolution without local registry/path patches. A compatibility failure must be fixed or reported with its exact consumer and source; never hide it by retaining an old internal release.
- Normal builds use the recorded lock. Run sync and validation for a new update; do not make builds silently choose different commits.

## Shared implementations

- Follow [shared implementation rules](docs/shared-implementations.md) before adding another production implementation of an existing cross-repository capability. Identify concrete consumers and compare their behavior contracts; reuse an appropriate Project Z provider, or extract a shared library when the common responsibility has a sound boundary.
- Record source commits and locations, provider ownership, API/error/resource contracts, feature/MSRV/platform constraints, and the migration plan. Similar syntax or a common algorithm alone is not proof of duplicate responsibility.
- Keep necessary platform backends, thin adapters and independent test oracles explicit. Do not introduce a crate for a trivial local helper, create dependency cycles, or share the implementation that computes a test's expected result.
- Accept only the documented migrated scope: real callers use the provider, replaced production logic is removed or tracked with an owner, and affected source/lock/gitlink and local behavior gates are verified. A new library, fewer lines, or one migrated consumer does not establish graph-wide completion or a measured performance improvement.

## Propagation and verification

Use `python3 scripts/project_z.py impact --repositories <repository-or-package>` to enumerate direct and transitive consumers, including runtime services and installers. Register missing relationships and coordinate existing owners.

Run `check`, `resolve --all` and the affected behavior's actual tests before accepting a snapshot. Keep application GUI, device, service, ABI and packaging gates. A notification, published library or open consumer PR does not complete propagation. Record real blockers, owners and reusable commits.

Day-to-day changes are verified locally. Do not trigger, rerun or wait for routine push/PR CI, CodeQL or remote review. Preserve formal release builds, signing, artifacts and deployment workflows. Report only platforms and behaviors actually tested.

## Artifacts and build outputs

- Keep generated screenshots, archives, APKs and compiled outputs outside Git history. Store them in the requested artifact destination and commit text evidence or links.
- Use precise ignore rules. Keep necessary source icons, fonts, test fixtures and bootstrap inputs; do not ignore every image or binary extension.
- History cleanup requires the user's authorization, backups, source-equivalence proof and exact expected-SHA leases. Notify existing owners so old history is not pushed back.
- On the shared development machine, ordinary Rust work uses `/var/tmp/project-z-cargo-target`. The outer batch holds `flock /var/tmp/project-z-cargo-target/.project-z-cargo-owner.lock` across related Cargo resolution, build and acceptance commands; do not acquire that lock again inside the batch.
- Remove only confirmed idle, regenerable build outputs. Preserve active work, source, patches, evidence, archives and Git metadata.
