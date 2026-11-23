# Dependency updates and shared-contract integration

This cohort continues from Project Z `2e32aacc3cd243aa7a4f43564e8e895ab3ba732c`,
the source of [v0.1.1](https://github.com/LIghtJUNction/project-z/releases/tag/v0.1.1).
Work was recorded on 23 November 2026 UTC / 24 November in Asia/Taipei.
The publication ledger in
[`dependency-shared-cohort-20261124/publications.json`](evidence/dependency-shared-cohort-20261124/publications.json)
binds each reviewed candidate tree to its public commit. GitHub creates different
commit metadata, so publication checks compare the complete tree and read back
the default branch after a non-forced, expected-head update.

## Dependency coverage

The final source snapshot contains 49 repositories, 85 cataloged packages and
117 recursive Git submodule references. All 183 coordinator tests passed; the
complete locked resolution passed for 43 Rust repositories, and the source gate
confirmed that Git sources, committed locks and current default-branch heads
agree. The [coordinator receipt](evidence/dependency-shared-cohort-20261124/coordinator-validation.json)
records the commands, outcomes and input hashes. These checks precede the native
platform release matrix.

The library audit covers 26 repositories, 60 active manifests, 41 active lockfiles,
172 registry crate names and 321 locked observations. The separate application
audit covers 17 repositories, 24 active lockfiles, 730 crate names and 872 locked
name/version pairs. These scopes overlap at transitive packages; their crate
counts must not be added as a unique total. The application audit revalidated
729 cached official index records and received one new record, with no query
failures. See the preserved
[library inventory summary](evidence/dependency-shared-cohort-20261124/library-audit.json)
and [application audit](evidence/dependency-shared-cohort-20261124/application-audit.json).

Compatible updates include the library comparison dependencies, sysinfo 0.40.4,
the four Wasmi packages at 2.0.2, ZIP/TOML consumers, LMM dependencies, the Core
service's exact same-line pins, and the wgpu/naga 30.0.2 family. The real Cargo
resolver generated the lockfiles. The Wasmi update replaces the yanked wasmi and
wasmi_core 2.0.0 releases. The Mechrevo console lock replaces yanked
async-executor 1.14.0 and clipboard-win 5.4.1 with 1.14.1 and 5.4.3 respectively.
A yank flag is an observation from the registry, not evidence of a vulnerability.

The three active OniSim workspaces are now explicit catalog inputs:

- `mods/CycleTrim/OniSim/gpu/Cargo.toml`
- `mods/CycleTrim/OniSim/native/Cargo.toml`
- `mods/CycleTrim/OniSim/lean-lab/harness/Cargo.toml`

Their workflow/build references establish current use. Historical transport-lab
workloads, old measurements and archived report lockfiles remain historical data.
Registry MSRV metadata was checked against declared consumer requirements; it is
not a substitute for a compiler run. OniMods root does not declare a minimum Rust
version, so its successful Rust 1.100 build does not establish an MSRV.

Different compatibility lines remain deliberate migration work. Examples include
rusqlite 0.42/0.43, jsonschema 0.61/0.63 and WebAuthn 0.5/0.6. The library audit
records 48 lock-level observations of newer packages in other compatibility lines.
The record does not claim that those migrations are impossible or completed.

## Shared implementations preserve observable contracts

The reusable unit is a behavior with an agreed contract. A consumer can retain a
small adapter for its allocation, output container or error type, while the
algorithm has one implementation.

### JSON output

`zconv::json::Writer` now provides an explicit control-character escape policy.
The normal writer keeps its existing short escapes. Consumers that previously
wrote Unicode escapes select `ControlEscapes::Unicode`, preserving bytes such as
`\\u0008` and `\\u000c`. zmem, zcall-gui, ztty, zuse and the zcalld compatibility
client share this implementation. zuse's platform adapter also delegates to its
existing JSON adapter. ztty retains object order and original number spelling.

The production parsers retain their contracts. Executed counterexamples show
different depth accounting, accepted legacy whitespace/Unicode spelling, value
and token budgets, object ordering and error offsets. Replacing them by a parser
with different limits would change behavior. The
[contract review](evidence/dependency-shared-cohort-20261124/contract-review.md),
[executed counterexamples](evidence/dependency-shared-cohort-20261124/parser-contracts/results.json)
and [parser source identities](evidence/dependency-shared-cohort-20261124/parser-source-identity.json)
record these distinctions.

### Windows private objects

`zsys::windows::privacy` owns the common handle-based owner and protected-DACL
checks. The GUI uses object-only inheritance; the daemon and installer use the
directory-children policy. The provider preserves each caller's current-account
and SYSTEM allowance, legacy accepted inheritance flags and access-mask policy.
SID validity is checked before its length is read. Creation and inspection remain
separate operations, and existing objects are not silently repaired by inspection.

SSMCP's different TokenOwner/inherited-ACE policy was reviewed and retained.
Treating similar-looking permission code as interchangeable would change which
existing objects are accepted. The independent source review and frozen consumer
hash bindings are preserved with this cohort.

### Preventing known regressions

The coordinator checks canonical normal-dependency sources, registered production
entry points, and fingerprints of implementations that were removed. The same
Rust lexer is shared by the audit and regression gate. A wrong-source alias cannot
satisfy a trusted provider reference, and struct shorthand field names stay literal
when local bindings are normalized. The JSON and Windows routes extend the same
gate; see [Shared implementations](../shared-implementations.md) for its exact
current scope and limitations.

This is a bounded source regression check. It does not prove whole-program
reachability or rule out every semantically equivalent algorithm, macro expansion
or rewritten control flow. Those changes still need a contract review.

## Validation at source freeze

The frozen source record distinguishes completed local checks from the required
formal release execution. The coordinator's complete local suite passed all 183
tests. Selected completed checks include:

| Scope | Observed result |
| --- | --- |
| Library comparison updates | 81 behavior tests; zclap shared grammar check; real Rust 1.99.1 checks |
| zsys | Combined provider source checked with its declared Rust 1.95 toolchain; native Windows execution remains a release gate |
| zplugin | Final public provider graph: workspace/all-target/all-feature check and 30 Wasm behavior tests on Rust 1.100 |
| zharness | Real Rust 1.99.1 all-feature tests: 133 passed, including 7 tests using a compiled Wasm guest |
| zmem | 266 ordinary tests passed, 3 existing environment-specific ignores; JSON checks on Rust 1.99.1 |
| zcall-gui | 45 Linux binary tests and strict Clippy passed using existing native headers |
| ztty | Final production locks: 62 serialization/protocol tests, no-std check and strict Clippy passed; both updated standalone plugin fixtures resolved and compiled with Rust 1.100 |
| zinput / zterm | Independent native plugin ABI test passed; 11 clipboard tests and no-std check passed |
| LMM | 129 tests passed, 2 existing opt-in ignores; strict Clippy and actual Rust 1.99.1 all-target check |
| OniMods / OniSim | Root 93 tests; all four workspace lock resolutions; 3 WGSL validations and native library check on Rust 1.99.1 |
| zaccel | 34 host/CLI tests and 6 offline acceptance tests; successful jobs=1 retry after an earlier compiler SIGKILL |
| Mechrevo console | Full locked metadata, actual Linux GUI-feature compilation and 25 controller tests |

The final aggregate check caught two additional stale lockfiles in ztty's dedent
example and text-plugin fixture. Real Cargo updates aligned their zplugin,
zplugin-macros and zsys sources, and both native cdylibs compiled with locked
dependencies. The suite then recorded the follow-up terminal commit. The
[fixture follow-up](evidence/dependency-shared-cohort-20261124/ztty-fixture-followup.json)
records the commands; the publication ledger retains both original and follow-up
commit identities. No production source changed in that follow-up.

The original failures remain part of the record. z58 and zdwire's strict Clippy
failures were reproduced on their unchanged baselines. A sandbox restriction
prevented native Unix listener tests in zuse, zcalld and zrc. ztty's complete
library preflight encountered an unchanged temporary-directory ownership
assumption; its final focused tests passed. ztype passed 22 composition/plugin
tests with `desktop,plugins`, while the default feature build still lacked XCB/IME
development packages after reusing the available font sysroot.

Core's library compiler and SSMCP's full library-test and production-Clippy
compiler processes received SIGKILL in the sandbox. These are not successful interface or behavior checks, and the
record does not infer an OOM cause without evidence. Their locked metadata passed.
The formal release requires the complete Core library interface check, SSMCP's
production strict Clippy, and its original archive/configuration/context/embedded-lock tests.

The release workflow additionally requires all three native library platforms,
eight named zsys Windows privacy tests, four GUI privacy tests, three daemon
privacy tests and three installer privacy tests. Linux runs the complete terminal
library, input service, automation library/sessions, daemon transports,
compatibility client, configuration and system-information checks. Required
validation must succeed before packaging or publishing. Routine source commits
use `[skip ci]`; only the authorized formal Release runs this matrix.

No GPU performance claim, actual ONI gameplay result, Mechrevo hardware operation,
service deployment or real account/broadcast operation is implied by these checks.
The subsequent Release page records the actual hosted outcomes and artifact
checksums for the immutable tagged source.
