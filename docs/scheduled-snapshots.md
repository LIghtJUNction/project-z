# Scheduled source snapshots

The scheduled workflow observes all repositories registered in `.gitmodules` at 00:17, 06:17, 12:17 and 18:17 UTC. Manual runs always stage locally on GitHub-hosted runners. The existing maintenance audit and the manual release workflow keep their original triggers.

| Observation | Result |
| --- | --- |
| No gitlink changed | Stop after audit. Registry availability or a documentation edit cannot start a release. |
| A lock, nested source, generated index or default branch disagrees | Fail with the coordinator's consumer and source diagnostic. |
| A clean candidate exists | Transfer its commit in a Git bundle. The reusable CI checks that exact parent and SHA, validates dependency locks and runs its existing Linux, Windows and macOS matrix. Linux also tests affected Rust consumers and runs the suite’s own check when impacted. |
| Full CI passed, source changed, package versions stayed the same | Stage the verified gitlink update. When writes are enabled, fast-forward the aggregate without a tag. |
| Full CI passed and a changed repository introduces a new package version | Check historical stable tags for the version and source cohort. Stage one aggregate patch with the official release packager, including the source archive and `commits.txt`. A decrease blocks. Build metadata alone does not qualify. |
| A required check, permission or source identity fails | Stop the affected transition. The job log identifies the failed gate. |

Project Z has no root crate. Its patch tag identifies a GitHub source snapshot. Package versions come from Cargo metadata and the non-Cargo version manifests explicitly registered in `project-z.toml`. Other Git-only components still synchronize. A version change in a registered package can qualify that snapshot, including an internal package. The coordinator never edits a child version or lockfile.

For a read-only diagnosis of an existing PR, manually run **Coordinate Project Z**
on its branch with `diagnose_recorded_sources` enabled. When unit tests and
full locked resolution pass, this permits platform tests to report their own
results even if the source check fails. The dependency job and overall CI
still fail. Scheduled and formal release calls keep their normal prerequisites.

## Enabling scheduled writes

After merging, run **Sync and test Project Z** manually on main to review a dry run. An unset `PROJECT_Z_SCHEDULED_WRITES` repository variable leaves scheduled runs in staging. To enable writes, configure the `project-z-snapshot` GitHub Environment for main, its required reviewers if applicable, and set the variable to the exact string `true`. Release authorization is limited to the aggregate repository's `contents: write` job. The repository and organization must permit that workflow token to fast-forward main and create release tags and GitHub Releases under their existing rules. Where a reviewed PR is mandatory, the atomic push is rejected. Keep protection in place and use the normal reviewed path.

One scheduled run runs at a time. Its write job shares the formal release workflow's concurrency group. Read-only jobs use their own group. Reserve the `vX.Y.Z` namespace for those serialized release writers. Before writing, the job checks the candidate's parent, permitted paths, live upstreams, main, planned version, archived SHA and asset digests. One ordinary atomic Git push compares the advertised main SHA and absence of the new tag, then writes both refs. Snapshot-only updates write main alone. Source repositories have independent refs; a default branch can advance after the last check. The release manifest always identifies the exact tested sources.

For interrupted publication, choose **Re-run failed jobs** on the same run while its artifacts are retained. The writer recognizes the already reserved SHA/tag, verifies existing draft assets by SHA-256, uploads missing assets, checks the final asset set, refs and sources, then publishes the draft. A completed release is idempotent. A conflicting release, moved main, stale source or expired artifacts requires maintainer review. A later no-change audit never repairs a release by inventing another patch. Disable scheduled writes by clearing the repository variable.

## Owner-controlled crates.io publication

Changed versions are queried individually. A published or yanked version is never overwritten. No child has opted in by default. The root keeps no crates.io token. An owner may request a reviewed `[registry_handoffs.<crate-name>]` entry in `project-z.toml` with these fields:

| Field | Required evidence |
| --- | --- |
| `repository` | Exact GitHub owner/repo from the registered source |
| `crate_owner` | Verified existing crates.io owner login, including the full team login for a team |
| `workflow` and `workflow_blob` | Filename and reviewed Git blob SHA of the official child workflow in `.github/workflows/` |

Review must verify the owner explicitly opted in, the official workflow grants publication only in the child repository and stages an exact registry projection from the committed lock. Its dispatch contract accepts `source_sha`, `package`, `version` and `archive_sha256`, checks the branch still points to that SHA, and publishes only the exact version and preapproved archive bytes. It must serialize per crate/version and safely skip an already published version, including when a dispatch is retried before the registry reflects its first run. Review all reusable actions and scripts reached by the child entrypoint. A changed workflow blob needs renewed approval. GitHub-only releases, private or `publish=false` packages, unknown ownership and unverified workflows have no handoff.

Configure the protected environment `project-z-crate-<crate-name>` for main. Its `CHILD_ACTIONS_TOKEN` must be limited to that one child repository with workflow dispatch permission (Actions write and the read access required to verify the source). Never set this as an organization-wide release credential. The child controls its own trusted publisher or scoped crates.io token. After the aggregate release, the handoff rechecks crates.io ownership, package absence, remote default SHA and workflow identity before dispatch. Child completion and registry receipts remain visible in the owner repository.


The owner supplies signed-off staging evidence before opt-in. Store the exact-source archive receipts in `docs/registry-receipts.json`, using the [receipt schema](release-projection.md), and pin their independently verified SHA-256 in `[scheduled].registry_receipts_sha256`. Each opted-in crate and its internal runtime/build dependencies need receipts for their exact versions and commits. Updating an owner-approved release cohort requires new receipts. Package staging saves the dependency-ordered versions, source commits, archive checksums and prerequisites in `registry-plan.json`. The write job verifies it against the trusted base policy and publishes this file alongside the aggregate assets.

If an upstream crate publishes and its consumer fails, use **Re-run failed jobs**. Each leg loads the original plan, probes the registry as a fresh Cargo consumer with an exact dependency, runs locked metadata, and verifies the downloaded archive checksum and VCS provenance. A matching upstream is skipped. Any missing prerequisite or conflicting digest blocks the consumer. Immediately before dispatching a missing crate, the job checks the aggregate refs and the complete observed cohort again. The handoff waits up to ten minutes for publication to become consumable. A later retry can finish an owner workflow that took longer. A second unchanged six-hour tick never produces another plan.
