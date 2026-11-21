# Project Z dependency projection (review only)

Project Z development manifests use GitHub default-branch sources for internal
cross-repository dependencies, without `version`, `branch`, `tag` or `rev`.
Package versions and the committed Git lockfile remain part of the source identity.
For external publication, crates.io requires registry versions for normal/build
dependencies that use Git during development, so
use a separate staging directory for the registry manifest. This tool does not
change the source manifest or source lock, create tags, or publish anything.

Select a repository with the GitHub dependencies already migrated, and the
full SHA of its release source commit. Run from the Project Z checkout:

    python3 scripts/release_projection.py next-version \
      --repo "$SOURCE_REPO" --commit "$SOURCE_SHA" --bump patch

    python3 scripts/release_projection.py stage \
      --repo "$SOURCE_REPO" --commit "$SOURCE_SHA" \
      --output "$NEW_STAGE_DIR"

The version command calculates a tag, not a bump commit. It increments the
greater of the selected package's stable manifest version and the highest local
stable tag with the requested prefix (default v). Use the intended release
repository with synchronized tags. For multi-package repositories, select the
package manifest and a dedicated prefix using --manifest and --tag-prefix.
Pass --workspace-manifest for version inheritance or staging in a nested Cargo
workspace. A release owner should apply the version to source and commit it
before staging the resulting post-bump SHA. The Git source snapshot and staging
must start from this same commit.

Staging archives tracked files from that commit and reads its committed workspace
Cargo.lock. It rewrites only HTTPS GitHub dependency declarations whose canonical
repository URL is listed in Project Z's .gitmodules. A unique name + URL Git lock
entry with a full Git SHA is required. Historical commits may include `version`
beside `git`; staging accepts them only when the locked version satisfies that
Cargo requirement. Malformed requirements
and mismatches are rejected before conversion. Selectors (`rev`, `branch`,
`tag`) and mixed path, registry or workspace sources remain rejected. The result
uses exact =VERSION constraints from the lock, preserving aliases, features,
optional/default-feature settings, targets and dependency kinds. The default scope is all Cargo.toml files under the selected workspace
folder. Use repeatable --member-manifest to select members explicitly when
excluded aux projects have separate lockfiles. The workspace's own Cargo.toml
is always processed. The first version requires tracked Cargo.lock and does
not support source repositories containing Git submodules.

The output contains source/ and a separate projection.json outside the package.
The report logs the originating commit, source lock digest, each converted Git
SHA and version, changed manifest digests, and remaining Git dependencies. The
staged workspace Git lock is removed; generate a new registry lock only in
source/. The status is always STAGING_ONLY_UNVERIFIED_NO_PUBLISH. Even a successful
offline metadata check or package build cannot prove that the registry crate
with the same name and version was produced from the locked Git SHA. Verify
registry source provenance and checksum, publish prerequisites in dependency
order, and ensure exact registry versions are available before enabling a release
workflow. This tool is not wired into CI or the GitHub release workflow.

## Verify upstream registry receipts

Use this separate read-only check before treating the staged dependency pins as
release candidates. It recomputes the plan from the specified commit and lock,
not from an editable staging report. It applies the same version-requirement
check as staging. Use the same workspace/member flags as in staging. The archive directory holds files named PACKAGE-VERSION.crate.

    python3 scripts/release_receipts.py \
      --repo "$SOURCE_REPO" --commit "$SOURCE_SHA" \
      --receipts "$RECEIPTS_JSON" --trusted-receipts-sha256 "$TRUSTED_PIN" \
      --archives "$LOCAL_CRATE_ARCHIVES"

Receipt schema v1 is a JSON object with schema_version: 1 and a receipts
array. Each record contains only package, version, github, git_sha, and
archive_sha256. The release authority must independently establish the mapping
from the exact source commit to the specific archive bytes and send the SHA-256
of the receipt file through an authenticated channel. Do not derive the trusted
pin from the same untrusted delivery as the receipts/archives. Cargo's VCS
metadata is a cross-check, not an attestation by itself.

The gate checks package, version, canonical repository URL, exact Git commit,
and archive SHA-256 against those receipts. It rejects missing/malformed or dirty
archive provenance and never accepts an allegedly equivalent alternate commit.
For example, a lock pointing to zuse-computer 0.2.2 at a1bb8fd2 cannot use an
existing 0.2.2 archive from 94c83755, even though its name, version and repository
match. No upload or network call is made. This check does not verify registry
availability, yank state, the complete transitive graph, or validate/install
the staged package. It does not change the staging-only label or enable CI.

Cargo's [multiple locations rule](https://doc.rust-lang.org/cargo/reference/specifying-dependencies.html#multiple-locations)
permits `version` together with `git`. Project Z's development policy is stricter:
internal cross-repository declarations use Git without a version selector. The
projection retains compatibility with historical multiple-location declarations
and still requires an exact source receipt before accepting a registry archive
for release.
