# Windows privacy and JSON duplication review

## Baseline and decisions

The review uses the source catalog in Project Z commit `2e32aacc3cd243aa7a4f43564e8e895ab3ba732c`. All consumer edits were made in separate checkouts at that catalog's exact commits. The complete search and caller inventory is in `baseline-callers.json`; it records the `git grep` commands and their versioned results.

Two shared contracts were confirmed and migrated:

- **Windows private-object security:** zcall-gui and zcalld share the same handle-based owner/DACL validator. The small creation-policy difference is now an explicit argument to `zsys::windows::privacy`. The installer compiles the same zcalld adapter through its existing source inclusion.
- **JSON string output:** five repositories share the same escaping rules, including lowercase `\u0008` and `\u000c`. They now use `zconv::json::Writer::string_with_control_escapes` with `ControlEscapes::Unicode`. Existing zconv callers keep the default short `\b` / `\f` spelling.

The four parser implementations and SSMCP's Windows storage policy have observably different contracts. They remain in place. Their differences below are grounded in exact source and, for parser acceptance/output, an executable comparison of the original source.

## Confirmed consumer paths

| Consumer implementation | Shared provider | Calling boundary retained |
| --- | --- | --- |
| `zcall-gui/src/core_install_windows.rs` | `zsys::windows::privacy` | `core_install_io.rs` checks existing files/directories and protects exclusively created objects before payload writes. |
| `zcalld/src/privacy_windows.rs` | `zsys::windows::privacy` | `state_json.rs`, `extensions.rs`, `keys.rs`, `desktop.rs`, `maintenance.rs`; BCrypt randomness used by `events.rs` remains separate. |
| `zcalld/crates/zcalld-installer/src/private.rs` | Same zcalld adapter and zsys | Existing inclusion of `../../../src/privacy_windows.rs`; both daemon and installer declare their own Windows zsys dependency. |
| `zcall-gui/src/json.rs::quote` | zconv string writer | `Json::stringify` retains sorted object keys and unchanged parser behavior. |
| `zcalld/crates/zcalld-compat-client/src/lib.rs::quote` | zconv string writer | Existing compatibility client and installer callers retain the public `&str -> String` interface. |
| `zmem/src/json.rs::quote` | zconv string writer | Reports, admission, background management and metadata output retain their existing adapters. zconv is optional under `std`. |
| `zuse/src/json.rs::quote` and `src/platform/mod.rs::quote` | zconv string writer | The platform helper delegates to the existing JSON adapter, covering native responses and runtime/session output. zconv is optional under `std`. |
| `ztty/src/json.rs::stringify` | zconv string writer for strings/keys | One accumulating output buffer is retained. Object insertion order and unmodified number text are preserved. |

The owned string adapters first ask the bounded writer for its required byte count, allocate that exact output buffer, then write into it. ztty writes directly into the appended portion of its existing buffer. The adapters contain no separate character-to-escape algorithm.

## Windows contract

The original duplicate validator is in [zcall-gui's catalog source](https://github.com/LIghtJUNction/zcall-gui/blob/3b9a0f4673c08a9aa259b52e02858c0a88f43f6b/src/core_install_windows.rs) and [zcalld's catalog source](https://github.com/LIghtJUNction/zcalld/blob/6eab1150e8d58d330583c1b3206bf91e7862dc9a/src/privacy_windows.rs). The shared implementation is published in [zsys commit 48c4cafa](https://github.com/LIghtJUNction/zsys/blob/48c4cafaf940fd7a404b885adefd2e1201b51881/src/windows/privacy.rs).

The validator reads security through the caller's existing file handle. It requires owner equality with the current process's `TokenUser`, a protected nonempty DACL, and one or two ordinary allow entries containing only that user and SYSTEM, with both roles represented. When the current identity is SYSTEM, one entry may satisfy both roles. File ACE flags must be zero. Each directory ACE independently permits zero flags or object/container inheritance together; mixed entries are allowed. The original validator did not require a particular access mask, and that acceptance rule is retained.

`check_private` does not rewrite ownership or the DACL. `protect` changes only the DACL and retains the existing ability to reprotect an object without `WRITE_OWNER`. `protect_created` sets owner, then DACL, then checks the result; its caller must have exclusively created the object before writing payload. The provider retains the same token-storage bound, SID-text bound, native allocation cleanup, and user-visible error messages. Type, reparse and hard-link checks remain with the consumer's I/O code.

| Creation policy | GUI | Daemon / installer |
| --- | --- | --- |
| Directory inheritance | `ObjectOnly`: no inheritable entries | `FilesAndDirectories`: OI/CI for directories |
| Regular-file inheritance | No flags | No flags |
| Existing-directory reader | Read-only security check | Read-only security check where used |
| Existing-directory reprotection | No separate production caller | DACL-only; no new ownership requirement |

One Win32 precondition was corrected while extracting the shared implementation: `IsValidSid` now precedes `GetLengthSid`. Microsoft's [GetLengthSid contract](https://learn.microsoft.com/en-us/windows/win32/api/securitybaseapi/nf-securitybaseapi-getlengthsid) requires a valid SID before the length call. The existing ACE bounds check remains. The [SetSecurityInfo contract](https://learn.microsoft.com/en-us/windows/win32/api/aclapi/nf-aclapi-setsecurityinfo) also explains why the two directory inheritance policies must remain explicit.

### SSMCP remains a separate policy

[SSMCP's catalog implementation](https://github.com/LIghtJUNction/ssmcp/blob/b5fdceea9af1b14f6f178bbc1677969fd3ff73c9/src/platform_windows.rs) differs at `Identity::current`, `verify_private`, and the private-directory/file entry points:

| Observable rule | Shared GUI / daemon policy | SSMCP policy |
| --- | --- | --- |
| Accepted owner | Current `TokenUser` | `TokenUser` or `TokenOwner` |
| DACL protection requirement | Files and directories | Directories; inherited child-file ACLs can remain valid |
| ACE count | One or two | Any nonzero count |
| Presence of identities | Current user and SYSTEM both required | Every accepted ACE must name current user or SYSTEM; both are not required |
| Directory ACE flags | Each entry has zero or OI/CI | No equivalent flag predicate in `verify_private` |
| Native failure representation | Existing fixed consumer strings, now provider error display | `io::Error`, including native OS error codes |
| Storage interface | Existing consumer file handle | Capability directory, path/reparse checks and singly-linked regular-file checks |

For example, a user-owned directory with three ordinary user/SYSTEM allow entries passes SSMCP's ACE-count rule but fails the shared policy. A private file owned by the process's distinct `TokenOwner` can pass SSMCP and fail the shared owner rule. These are source-derived acceptance differences; no Windows runtime result is claimed for these examples. No SSMCP production source was changed.

## JSON parser contracts

The earlier lexical matches were private `hex4` / `hex_quad` helpers. A short loop over four hex digits does not establish equivalence of the complete parser or its public error/resource contract.

| Implementation | Value / storage contract | Limits and diagnostics |
| --- | --- | --- |
| [ztty JSON](https://github.com/LIghtJUNction/ztty/blob/963afbd7f9463f6de61a96e1968fdf26d3bc8990/src/json.rs) | Owned values; insertion-ordered object vector; original number text | 1 MiB public messages, 32 MiB private checkpoints, 65,536 values excluding object keys; depth checked on every value; static string errors |
| [zcall-gui JSON](https://github.com/LIghtJUNction/zcall-gui/blob/3b9a0f4673c08a9aa259b52e02858c0a88f43f6b/src/json.rs) | Owned values; sorted `BTreeMap`; original number text | 2 MiB; depth checked on every value; ASCII whitespace acceptance; consumer-specific owned error strings |
| [zmem JSON](https://github.com/LIghtJUNction/zmem/blob/5997b9581f5b6962c9d9cd12774a2ce119e46ca7/src/json.rs) | Owned values; sorted `BTreeMap`; original number text | 1 MiB; no separate value-count limit; depth checked on every value; strict JSON whitespace; errors include exact byte offsets |
| [zgpui wire](https://github.com/LIghtJUNction/zgpui/blob/d34c41f79ddab343e7468c5192885a82ca487687/src/wire.rs) | Typed command/fields; borrowed unescaped strings through `Cow`; bounded unsigned integers | Known-field bitsets, typed unknown/duplicate-field errors, per-field string/node/reference/extent limits; no generic DOM/token tape |
| [zconv JSON](https://github.com/LIghtJUNction/zconv/blob/f9448d27997dc70dac05f0c0e58857bcce43ab72/src/json.rs) | Borrowed document backed by the caller's token tape | Container-depth accounting with a hard cap of 64; default 16 MiB, 262,144 tokens and 16,384 object fields; typed errors and required workspace counts |

The private hex helpers also differ directly. zmem returns `u16`, advances its cursor only after each valid digit, and reports the failing byte offset. ztty and zgpui return `u32` and advance before classifying the current byte, with different error types. GUI first takes a four-byte string slice, calls `u32::from_str_radix`, and advances only after successful conversion; its checked byte range, UTF-8 boundary and accepted numeric spelling differ from the byte loops.

### Executed counterexamples

`parser-contracts/results.json` identifies the exact original source SHA-256 values, compiler, commands and observations. The probe compiles the original three generic parsers, the unchanged zgpui library, and the actual public zconv source. It is a read-only behavioral comparison, separate from consumer Cargo integration acceptance.

| Input / condition | Actual result |
| --- | --- |
| Form feed before `null` | GUI accepts; zmem, ztty and zconv reject. |
| String escape `"\u+123"` | GUI's legacy `from_str_radix` helper accepts the leading plus; zmem, ztty and zconv reject it. This pre-existing nonstandard acceptance is preserved by leaving the parser unchanged. |
| Invalid hex digit in `"\u0G00"` | GUI returns its Unicode-escape message; zmem reports byte 4; ztty returns its static escape error; zconv reports typed invalid Unicode at byte 4. |
| 33 nested empty arrays | GUI accepts; zconv configured to depth 32 rejects. |
| 33 nested arrays containing a scalar | GUI rejects; increasing zconv's depth to 33 accepts. Raising one numeric limit therefore does not reproduce GUI's boundary. |
| 65 nested empty arrays | zmem and ztty accept; zconv rejects even if requested depth is 65 because its hard cap is 64. |
| Array with 65,536 scalar elements | GUI and zmem accept; ztty rejects because the root array is also a counted value. Default zconv accepts with 65,537 tokens. |
| Three object fields, zconv token budget four | ztty accepts its four values; zconv runs out of tokens because object keys also occupy the tape. |
| `[1,]` | GUI: `Invalid JSON value`; zmem: `expected a JSON value at byte 3`; ztty: `expected JSON value`; zconv: typed syntax error at byte 3. |
| Decoded duplicate keys `x` and `\u0078` | All reject, with different error text/types and reported offsets. |
| `{"z":1e+02,"a":9007199254740993}` | ztty writes `z` before `a`; GUI and zmem write `a` before `z`. All retain the original number spelling. |
| Valid JSON capability command containing an extra field | zgpui returns `UnknownField`; zconv accepts the JSON document. |
| Capability command with version `1.0`, or generic `[]` | zgpui returns `Syntax`; zconv accepts the JSON document. |

`parser-source-identity.json` proves that the complete production parser regions of zmem, zcall-gui and ztty are byte-for-byte unchanged by the string-output migration. zgpui remains at its unchanged catalog commit. Existing resource limits, object representations and parser diagnostics are retained.

## Validation boundaries

Provider tests cover all 32 control bytes, literal backslash spellings, quotes, Unicode, exact output capacity, short buffers, and invalid UTF-8. zconv was tested on Rust 1.100.0 and the relevant consumer's real Rust 1.99.1 toolchain. Its default output is unchanged. The Windows provider and its eight native test bodies cross-compile; the coordinator additionally checked the published combined zsys source with its declared Rust 1.95 toolchain.

zmem's final candidate passed 266 ordinary tests with three existing environment-specific tests ignored, four JSON tests on Rust 1.99.1, no-default-features checking, and Clippy. zcall-gui's full native-feature Linux binary passed all 45 tests and Clippy after using the existing native development sysroot. Its real `core_install_io.rs` and unchanged four Windows test names also passed focused Windows-target compilation and Clippy against public zsys. This focused check does not compile the native Windows GUI C component or execute Windows tests.

zuse's full library run recorded 192 passing tests, four existing ignored tests and one failure in an unchanged `UnixListener::bind` fixture. A separate `AF_UNIX` socket-creation probe returned EPERM before any application code; the source file's baseline/current SHA-256 values match. The JSON-output and session-frame tests, no-std library check and Clippy passed. Listener-dependent session integration was not executed after the library command stopped. `zuse-environment-blocker.json` and `zuse-candidate.json` retain this limitation.

zcalld's final candidate uses all published upstream commits in both its Cargo lock and its five updated vendor/application gitlinks. The compatibility-client library passed 11 tests and the installer library passed 15 Linux tests. The daemon recorded 86 passes and five failures at native Unix socket creation; its `transport.rs` is byte-for-byte identical to the baseline. Complete daemon and installer test targets passed Windows MSVC cross-compilation and Clippy, and all three affected packages passed Linux Clippy. `zcalld-environment-blocker.json` and `zcalld-candidate.json` preserve the remaining runtime limits.

ztty's final lock and gitlinks include the published zinput/zterm chain. Its new golden test plus JSON, MCP, terminal-frame and workspace-state integration suites passed 62 tests on that final lock. The no-std check and Clippy passed. The earlier full library preflight recorded 28 passes, eight existing EGL/font ignores and one failure: the sandbox's `/tmp` is owned by user 1000 with mode 0755, so the unchanged cleanup guard retains the file instead of treating its parent as a root-owned sticky or private directory. The test source and production cleanup source match the baseline exactly. The last zterm publication changed neither its source tree nor its Cargo manifest, and those identities are recorded. `ztty-candidate.json`, `ztty-environment-blocker.json` and `zterm-final-source-identity.json` distinguish preliminary full-suite coverage from the final focused acceptance.

Formal Windows execution is still required for all eight zsys permission tests, four GUI tests, three daemon tests and three installer tests. The formal Linux run must cover zuse's full library/session suite in an environment permitting owned listening sockets. No local cross-check is recorded as native Windows execution. Candidate receipts record all real commands, failures, follow-up results, source hashes and canonical Git lock sources.
