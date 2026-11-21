# Scheduled source snapshots

The scheduled workflow observes all repositories registered in `.gitmodules` at 00:23, 06:23, 12:23 and 18:23 UTC. Manual runs always stage locally on GitHub-hosted runners. The existing maintenance audit and the manual release workflow keep their original triggers.

| Observation | Result |
| --- | --- |
| No gitlink changed | Stop after audit. Registry availability or a documentation edit cannot start a release. |
| A lock, nested source, generated index or default branch disagrees | Fail with the coordinator's consumer and source diagnostic. |
| A clean candidate exists | Transfer its commit in a Git bundle. The reusable CI checks that exact parent and SHA, validates dependency locks and runs its existing Linux, Windows and macOS matrix. |
| Full CI passed, source changed, package versions stayed the same | Stage the verified gitlink update. When writes are enabled, fast-forward the aggregate without a tag. |
| Full CI passed and a changed repository introduces a new package version | Check historical stable tags for the version and source cohort. Stage one aggregate patch with the official release packager, including the source archive and `commits.txt`. A decrease blocks. Build metadata alone does not qualify. |
| A required check, permission or source identity fails | Stop the affected transition. The job log identifies the failed gate. |

Project Z has no root crate. Its patch tag identifies a GitHub source snapshot. A version change in a registered package can qualify that snapshot, including an internal package. The coordinator never edits a child version or lockfile.

## Enabling scheduled writes

After merging, run **Sync and test Project Z** manually on main to review a dry run. An unset `PROJECT_Z_SCHEDULED_WRITES` repository variable leaves scheduled runs in staging. To enable writes, configure the `project-z-snapshot` GitHub Environment for main, its required reviewers if applicable, and set the variable to the exact string `true`. Release authorization is limited to the aggregate repository's `contents: write` job. The repository and organization must permit that workflow token to fast-forward main and create release tags and GitHub Releases under their existing rules. Where a reviewed PR is mandatory, the atomic push is rejected. Keep protection in place and use the normal reviewed path.

The schedule shares the formal release workflow's concurrency group. Reserve the `vX.Y.Z` namespace for those serialized release writers. Before writing, the job checks the candidate's parent, permitted paths, live upstreams, main, planned version, archived SHA and asset digests. One ordinary atomic Git push compares the advertised main SHA and absence of the new tag, then writes both refs. Snapshot-only updates write main alone. Source repositories have independent refs; a default branch can advance after the last check. The release manifest always identifies the exact tested sources.

For interrupted publication, choose **Re-run failed jobs** on the same run while its artifacts are retained. The writer recognizes the already reserved SHA/tag, verifies existing draft assets by SHA-256, uploads missing assets, checks the final asset set, refs and sources, then publishes the draft. A completed release is idempotent. A conflicting release, moved main, stale source or expired artifacts requires maintainer review. A later no-change audit never repairs a release by inventing another patch. Disable scheduled writes by clearing the repository variable.

## Owner-controlled crates.io publication

Changed versions are queried individually. A published or yanked version is never overwritten. No child has opted in by default. The root keeps no crates.io token. An owner may request a reviewed `[registry_handoffs.<crate-name>]` entry in `project-z.toml` with these fields:

| Field | Required evidence |
| --- | --- |
| `repository` | Exact GitHub owner/repo from the registered source |
| `crate_owner` | Verified existing crates.io owner login, including the full team login for a team |
| `workflow` and `workflow_blob` | Filename and reviewed Git blob SHA of the official child workflow in `.github/workflows/` |

Review must verify the owner explicitly opted in, the official workflow grants publication only in the child repository and stages an exact registry projection from the committed lock. Its dispatch contract accepts `source_sha`, `package` and `version`, checks the branch still points to that SHA, and publishes only that exact version. It must serialize per crate/version and safely skip an already published version, including when a dispatch is retried before the registry reflects its first run. Review all reusable actions and scripts reached by the child entrypoint. A changed workflow blob needs renewed approval. GitHub-only releases, private or `publish=false` packages, unknown ownership and unverified workflows have no handoff.

Configure the protected environment `project-z-crate-<crate-name>` for main. Its `CHILD_ACTIONS_TOKEN` must be limited to that one child repository with workflow dispatch permission (Actions write and the read access required to verify the source). Never set this as an organization-wide release credential. The child controls its own trusted publisher or scoped crates.io token. After the aggregate release, the handoff rechecks crates.io ownership, package absence, remote default SHA and workflow identity before dispatch. Child completion and registry receipts remain visible in the owner repository.
