# Project Z maintenance

Project Z pins independent repositories to a source snapshot that can be validated together. Read this repository's README and CONTRIBUTING, then the target submodule's own AGENTS.md before editing it.

## Propagation principle

When you change a foundational library, you own propagation to every affected direct and transitive consumer, including libraries, applications, runtime services and installers. Enumerate with `python3 scripts/project_z.py impact --repositories <repository-or-package>`, inspect actual manifests, and register missing relationships. Coordinate with active owners and use isolated checkouts instead of overwriting their work.

Update compatibility code, version constraints, pinned commits and lockfiles in dependency order. Run the relevant consumer checks, commit and push in meaningful batches, and verify remote state. A published library or delivered message does not complete propagation. Record any real blocker, the affected consumer, the next owner and the exact reusable source commit until it is resolved.

## Local validation and release workflows

Day-to-day development, fixes and merges are validated locally. Do not trigger, repeatedly rerun or wait for routine push/PR CI, CodeQL or remote review. Keep required formal release builds, signing, artifact and deployment pipelines; the coordinator workflow remains manually callable and reusable for those workflows. Report only platforms and native behaviors actually verified.

## Snapshot checks

- Regenerate `catalog.json`, `.cargo/project-z.toml` and `docs/PROJECTS.md` with `python3 scripts/project_z.py sync`; do not edit generated content by hand.
- Run `python3 scripts/project_z.py check` and `python3 scripts/project_z.py resolve --all` before accepting the snapshot.
- Use `python3 scripts/project_z.py run --affected <name> -- <cargo-command>` for affected Rust consumers, and retain each application's native, service, device and packaging acceptance gates.
- Publish subrepository commits before updating aggregate gitlinks. Preserve active branches, uncommitted work and private runtime configuration.
- Do not run concurrent Cargo jobs that modify the same checkout. Coordinator lockfile restoration preserves pre-existing edits; it is not a substitute for separate worktrees.
