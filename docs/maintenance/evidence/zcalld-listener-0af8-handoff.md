# zcalld listener — current-source local validation

The fixed candidate `0af8f65653bc4035888380b8b2f390d774fd30fd` / tree `ca3cdf4a464543a1323b057d241d45983cba6a05` passed the local Rust, CLI and curl batch. Final SSMCP P1 is still pending with the existing acceptance owner.

The candidate preserves main `37c82ee7cec35594771a02869f7f72f12a3ace1d` and uses GUI `d491b627223807da7b2929f3feea7461393d124c` and compat `56a15b330384531b3a6c444190f53b6d3720bd5e`. Its tracked source map contains 220 leaves; all worktree blob bytes match the listed Git objects. The source remained clean through validation and evidence collection.

## Actual results

- Job `26c4545eae1eab8d27485f4a48077d3c-882` exited 0 in 71.635 seconds with both output streams at EOF.
- Workspace tests: 182 passed, 0 ignored. The seven listener cases are a subset of this total.
- Strict Clippy: 2 actual root compiler invocations; the original Cargo argv and raw logs are included.
- Release CLI: actual compiler-artifact `fresh=false`, release opt-level3, and the recorded root compiler invocation bind the copied binary to this source.
- Eight actual TCP/Unix cancellation and half-close cases passed without skips.

## Immutable CLI

Path: `/home/lightjunction/Documents/GITHUB/pr-core-zcalld-listen-gui-d491-20261121/gates/20261121T005053Z/zcalld`  
Size: 2964896 bytes  
SHA-256: `dbe2db6d7130a7751616162fe503468c5f77df0ee7b9c517cd690c2d0e95c63b`

The CLI was copied while the actual parent flock, kernel lock row and matching file descriptor were observed. The binary remains on the development machine; the archive contains text evidence and its descriptor, not an executable copy.

## Cleanup and remaining boundary

The owned scope is inactive/dead, its control group is empty, and the launcher and flock processes have exited. Postflight observed a different holder, PID3756319, so this report does not claim the global lock was empty. No further Core heavy task is scheduled.

The earlier 8fe freshness failure, E1 GUI source hold, and 0af foreign-lock prelaunch remain separate records. Historical test totals are not assigned to this candidate. The GUI AUR packaging change and final SSMCP P1 retain their own owners and acceptance requirements.

`handoff.json` maps each claim to original driver, ordered logs, source manifest, lock, compiler artifacts, actual start/status, lock observations and cleanup receipts. The evidence collector ran no product tests or builds.
