# Automated Project Z maintenance

The maintenance entry point turns upstream changes into an explicit work list.
It compares the committed gitlinks with the branches declared in `.gitmodules`,
checks publishable package versions from `catalog.json` against crates.io, and
looks for potential new repositories under the same GitHub owner. If the catalog
has not been generated, it reads the existing coordinator's `inventory` output.
The audit writes JSON for an agent and Markdown for a person.

## Run an audit

```sh
python3 scripts/maintenance.py
```

The default files are `dist/maintenance/audit.json` and
`dist/maintenance/summary.md`. `--output` and `--report` select other locations;
`--owner` selects the GitHub owner when the origin URL does not identify it.
The implementation uses Python's standard library, Git and `gh`. Catalog
generation uses the existing coordinator and its configured Cargo toolchain.
`--require-catalog` reads `HEAD:catalog.json` and fails with a report if it is
missing; this mode needs neither initialized submodules nor a Rust toolchain.
It reuses existing authentication without reading or printing credential values.

An audit does not fetch into the shared repositories, switch their branches or
change gitlinks. It records dirty sources and catalog/gitlink disagreement.
HTTP 404 means a crate version is missing; rate limits, server errors and network
failures remain incomplete checks rather than being reported as missing releases.
Registry presence is a version-availability check, not proof that an unrelated
crate with the same name belongs to Project Z.

New repository names and the `project-z` topic are discovery hints. The report
includes description, language and topics for semantic review. It excludes known
repositories, forks, archived repositories and other owners. It never adds a
candidate to `.gitmodules` or infers its architectural role solely from a prefix.

The command exits successfully when an audit completes, including when there is
maintenance to do. It exits 2 when checks could not complete. Reports retain the
errors so a failed network request cannot look like an up-to-date project.

## Prepare a known-repository update

```sh
python3 scripts/maintenance.py --apply
```

`--apply` requires a clean source checkout and creates a separate Git worktree
under `dist/maintenance/worktrees/`. A custom `--worktree PATH` must name a new
directory outside existing repositories, or inside ignored staging under the
source root. A destination inside a source submodule, another checkout or Git
metadata is rejected before creating the worktree. If the shared checkout contains active work, the scheduled agent should
use a fresh clean checkout instead of discarding or committing another session's
changes.

The new worktree initializes the pinned submodules, fetches only known updates,
and checks that every fetched branch still names the audited commit. Each update
must be a fast-forward of the old gitlink. The initial checkout populates only
top-level repositories. After every parent reaches its final commit, nested
URLs are synchronized and nested repositories are initialized from that commit.
This avoids populating removed nested trees or retaining old nested URLs. The
root update is not repeated, so its old index cannot reset the new gitlinks.
Unknown candidates do not participate in this operation.

The existing coordinator runs `sync` and `check` against the assembled sources.
After those gates pass, the script commits only the selected gitlinks and the
generated catalog and local registry patch. The JSON includes the branch,
commit, worktree path and an explicit push command. It does not push, create a
pull request or merge anything. This snapshot has passed the dependency graph
and policy checks; the scheduled agent still runs affected resolution, library and
platform tests before publishing or merging the coordinated change.

A failed gate leaves the isolated worktree available for inspection and creates
no snapshot commit. A dirty source or existing destination is rejected without
forced checkout. The script rechecks source HEAD and cleanliness before the
commit to detect concurrent edits during validation.

## Scheduling

`.github/workflows/maintenance.yml` audits once a day at **01:17 UTC** and can be
started with `workflow_dispatch`. It uploads both reports and places the work
list in the Actions job summary. It uses the workflow's normal read-only GitHub
token and does not depend on an unconfigured personal token or a PR bot. It
checks the committed catalog without cloning submodules or installing Rust.
The separately configured ChatGPT maintenance task runs hourly; the GitHub
workflow remains the daily read-only audit.

The scheduled workflow supplies observations. The scheduled maintenance agent owns
semantic review, cross-repository fixes, affected tests, incremental commits and
authorized publication. These are separate responsibilities: the audit cannot
truthfully claim that a newly discovered library has already been integrated.

## Verification

```sh
python3 -m unittest discover -s tests -p test_maintenance.py -v
```

Tests use real temporary Git repositories and worktrees to verify exact gitlink
updates, unchanged source checkouts, rejection of dirty trees and unknown plans,
nested URL replacement and removal, isolated destination paths, shallow CI
audit without initialized sources, and preserved work after a failed dependency
gate. Mocked network boundaries
distinguish missing, yanked and unavailable registry versions and keep discovery
scoped to the requested owner. No test mutates a production checkout or contacts
GitHub or crates.io.
