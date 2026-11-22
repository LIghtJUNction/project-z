# Host responsiveness investigation — 22 November 2026

This record describes a changing development workload on a Linux desktop with 16,476,700,672 bytes of RAM. It distinguishes source validation, host configuration and short observations. It is not a mouse-input benchmark, a controlled before/after comparison or a guarantee that memory pressure cannot recur.

## What caused the capacity problem

During the reported stutter, memory full PSI reached approximately 38% for its ten-second average. An observed zram sample held roughly 15.7 GB of uncompressed pages in 8.28 GB of physical memory. Available RAM fell below 1 GB while background development checks and foreground applications repeatedly faulted pages back in. Free disk Swap capacity did not imply that the active working sets fitted in RAM.

The largest development checks observed in this phase included a Clippy process with approximately 2.3 GiB of logical swapped pages and a TypeScript native `tsgo` process with approximately 1.58 GiB RSS plus 1.76 GiB of logical Swap. The type checker had inherited a graphical terminal's cgroup. A child launched inside a terminal does not become an independently managed background workload merely because its command is a build.

There was also a previously identified filesystem scanner, `project-bees.service`. Its declared `IOWeight=10` had not established an available I/O controller for the existing user session. The [zmem 0.3.1 acceptance record](https://github.com/LIghtJUNction/zmem/blob/v0.3.1/docs/acceptance-0.3.1.md) documents the earlier controller diagnosis and bounded scanner comparison.

## Applied host measures

- Installed zmem 0.3.1 while preserving the existing configuration and all 15 active Swap entries' paths, types, sizes and priorities. The locally built candidate's identity is recorded in its versioned acceptance document; formal release binaries have their own build checksums.
- Installed the owned, additive user-manager I/O delegation and accounting drop-in. Removed this investigation's temporary runtime overrides after verifying that the persistent default still exposed the controller.
- Kept the filesystem scanner at a per-device read limit of 8 MiB/s and write limit of 2 MiB/s, confirmed in `io.max`. The persistent host configuration uses a stable device identifier.
- Applied a temporary limit to the already isolated Clippy scope: one CPU core's total quota, CPU/IO weight 10, reads 4 MiB/s and writes 1 MiB/s. Its existing memory limits remained intact. These settings belong to that transient scope and are not universal zmem defaults.
- Paused verified background compiler processes and the scanner for bounded intervals. Independent systemd timers were armed first. Process identity checks guarded compiler resumption against PID reuse; processes were not terminated to discard their progress.
- Retained protection for 17 identified interactive scopes. The daemon reported complete protection and no errors after the system-manager reload.

The five-minute recovery timer subsequently completed successfully. All four compiler processes targeted by that timer later exited; the filesystem scanner was populated and unfrozen. No targeted process was left suspended by this investigation.

During the quieter interval, memory full PSI's ten-second average reached 0.00–0.01%. A later sample was approximately 3.54%, so the low readings were not a permanent ceiling. The workload changed, `tsgo` exited and background work resumed during these observations. No percentage improvement in desktop speed is inferred from them.

A subsequent 30.03-second observation of zmem 0.3.1 collected 16 system samples and 300 scheduler-wakeup samples without adding an artificial workload. Memory full PSI calculated from counter deltas averaged 3.03% over that window. Available RAM ranged from 1.43 to 2.57 GiB, while Swap-in traffic averaged about 33.4 MiB/s. The scheduler-wakeup p95 was 0.182 ms with no skipped deadlines. Sixteen Hyprland monitor-query probes had a 125.5 ms p95 and no timeouts; that measurement includes helper-process startup and IPC, not mouse or frame latency. These results show continuing paging variation despite a responsive observation process, and establish a pre-admission window rather than a controlled comparison.

The live zram device was preserved. `zram_percent=50` is already in the persistent configuration and applies when a device is initialized at a subsequent normal boot. That setting specifies logical device size, not a promise that compression is free or that every workload will use the same physical memory.

## Launch future heavy work in its own group

The Project Z and oh-my-ztty build helpers wrap heavy Cargo operations in zmem background scopes when a compatible CLI and daemon are available. With zmem 0.4 these submissions also check launch admission. Cargo metadata queries are excluded. Other build entry points still need explicit grouping:

```sh
zmem run --class background -- cargo clippy --locked --all-targets
zmem run --class background --wait-timeout 300 -- cargo build --release --locked
zmem run --class background -- bun run typecheck
```

Grouping a task at launch gives subsequent descendants the same resource boundary and avoids mixing its working set with a protected terminal. The new gate waits before starting a target when memory conditions are unsuitable, then lets the daemon budget the running background group. The default wait is 60 seconds; timeout returns 75 without starting the target. Interactive work bypasses admission. A permanent one-core limit is not part of this default. Choosing Cargo `-j 1` remains an optional concurrency tradeoff, not a memory limit for a single compiler.

The [0.4.0 native acceptance record](https://github.com/LIghtJUNction/zmem/blob/v0.4.0/docs/acceptance-0.4.0.md) documents actual timeout, cancellation, raw-argument and systemd scope checks. Under natural pressure, one twenty-second background attempt remained unstarted and timed out. A subsequent fresh invocation passed its initial check at 2,356,547,584 available bytes and 0.82% memory full PSI, then ran in the managed background hierarchy. Different conditions and per-invocation recovery history explain these outcomes; they are not a measured speedup.

The local 0.4.0 candidate was installed with the existing configuration and all 15 active Swap entries unchanged. Its SHA-256 was `c37f7d064be2e7012a09987ee91099202a021748f050bf91463c63026a6e5e74`. The fresh daemon report was identity verified, and interactive protection completed without errors. The source gate passed 212 tests with three existing privileged tests ignored. Formal release binaries have separate checksums.

The 0.4.0 publication subsequently stopped at its ARM64 gate: directory-opening flags had used the x86 numeric ABI. The fix centralizes architecture-correct flags and adds three actual file-operation tests. Version 0.4.1 passed all 215 local tests, followed by both native architecture gates in the [successful formal release](https://github.com/LIghtJUNction/zmem/actions/runs/45017220881). Its source is `24951ae66df31387f736f61b34d21a1963df9730`; the original 0.4.0 tag was retained. Both official archives, their manifests and architecture headers, the published crate's checksum and VCS identity, and the live Pages version were independently checked. Admission policy and configuration did not change in this ABI correction. These release checks do not relabel the earlier host observations as measurements of the 0.4.1 binary.

## Final official installation and remaining pressure

The [official oh-my-ztty 0.2.13 release](https://github.com/LIghtJUNction/oh-my-ztty/releases/tag/v0.2.13) was installed through its verified installer with system memory management enabled. The 9,147,557-byte x86_64 archive has SHA-256 `7070303753317e8d8eae37f2fd1996f97f60d6317cb13f3cb5a4b729c8379882`. All 136 manifest entries were checked, and all seven component identities matched the release's source lock. Its zmem executable is 1,158,968 bytes with SHA-256 `4fc79e29fe11d22a70a4d6c21ec0fbcd04b45aa6c19bc71a1ef6b253bdafb6e1`; the bundled executable, root-owned installed copy and running daemon image matched.

The active suite link points to `releases/0.2.13-linux-x86_64`. All 15 active Swap entries retained their paths, types, sizes and priorities. The 165 protected files covering personal shell/completion configuration, zmem configuration and the previously verified host adjustments remained byte-identical. The service was active, with zero restarts, a fresh process-identity-verified 0.4.1 report, complete protection for the 15 currently identified critical scopes and no protection or daemon errors. `doctor` passed, including the available user I/O controller. A later daemon RSS snapshot was 3,264 KiB; this is an observed process footprint, not a universal memory ceiling.

An actual interactive invocation entered its documented `app.slice/zmem-interactive-*.scope`, preserved literal `$HOME`, an empty argument and stdin, and returned the target's exit code 37. A background invocation with an immediate admission check returned 75 under natural memory pressure and did not start its target. The external verification harness initially assumed a nonexistent interactive slice; its path assertion was corrected against the shipped implementation. The product and installed bundle were unchanged by that correction.

The following natural-workload observation used the official 0.4.1 binary. It added no artificial memory load and collected 16 system samples and 300 scheduler samples over 30.39 seconds. Counter-derived rates cover the valid intervals between those samples, about 30.00 seconds.

| Observation | Actual result |
| --- | --- |
| Available RAM | 0.887–1.465 GiB |
| Memory full PSI from counter deltas | 10.91% time-weighted mean |
| Direct page scans | 381.83 MiB/s; scans are not bytes successfully reclaimed |
| File-page / anonymous-page refaults | 184.19 / 39.45 MiB/s |
| Logical Swap-in / Swap-out | 37.87 / 64.85 MiB/s |
| Scheduler-wakeup p95 | 0.212 ms, no skipped deadlines |
| Hyprland process-startup and IPC p95 | 233.12 ms, 16 successful probes, no timeouts; not input or frame latency |
| Daemon provenance | All 16 reports were fresh 0.4.1 daemon-cache observations with no diagnostic occurrences |

**This window does not establish that desktop paging has been solved.** Its full-stall mean exceeded the earlier 0.3.1 observation, but the workloads and observation times were different; neither a causal improvement nor a causal regression percentage follows from those two windows. The new gate can prevent another heavy submission from entering; it cannot remove the working sets of already running applications.

A later five-second process observation found active major faults in Quickshell, the filesystem scanner, browser/ChatGPT processes, the network proxy and monitoring services. No new large compiler was identified as the cause in that window. The desktop scope's actual `memory.low` was about 1.30 GB, yet its `memory.events.local low` counter still increased. This demonstrates the limit of best-effort protection when the machine has insufficient reclaimable memory; a successful control write does not make the protected pages immune to reclaim. The scanner's block-device I/O readback remained bounded: approximately 38.20 MB was read on the capped device over 5.00 seconds, below its 8 MiB/s limit. Larger process-level logical-I/O counts were not treated as evidence that this physical-device limit failed.

The retained zram device had no backing device, zero writeback counters, and about 8.35 GB of physical allocation for 15.82 GB of logical data at a subsequent observation. Its existing layout therefore still occupied a substantial part of this 16.48 GB machine. The configured 50% logical zram layout takes effect at a subsequent normal initialization; no live zram drain, reset, cache purge or foreground-application termination was used to force a favorable result.

The filesystem scanner remained in its existing service group. Current zmem can account for a background systemd service placed in `zmem-background.slice`, but changing an already active service's `Slice=` requires a controlled new start. Its ability to resume application progress had not been established, so no restart or manual cross-cgroup process migration was performed for this report.

zmem's automatic background budget and admission cover explicitly submitted jobs, not every arbitrary process on the machine. They do not predict a command's future peak memory or automatically checkpoint its application state.

Use `zmem status --json` to inspect measured paging and the daemon's actual control readback. Use `zmem doctor --json` to distinguish available user I/O controls from a configuration that still needs an existing manager refreshed. Global I/O PSI includes time spent waiting on a background bandwidth cap; inspect relevant cgroups before interpreting it as physical-drive saturation.

## Preserve Rust build reuse

The observed Clippy job used a new temporary target directory, which could not reuse the ordinary shared target directory's compiled artifacts. Keep the existing shared target and outer build-owner lock for repeated local validation. Heavy builds for this change were performed in the separate build environment or the formal release runners.

The oh-my-ztty release workflow now caches public Cargo downloads, unpacked registry/Git sources, and explicit final-output and intermediate-build directories. Keys separate architectures, runners, toolchain identity and source/lock identity. All original validation and build steps still run. A Cargo 1.100.0 fixture with a real registry dependency reported both crates fresh after an archive/remove/restore cycle; this verifies that fixture's cache recovery, not the speed of a complete published bundle.

The 0.2.13 formal run saved both architecture caches, but its tag-scoped dispatch could not share those caches with a different tag. A [one-line follow-up](https://github.com/LIghtJUNction/oh-my-ztty/commit/2eb8340987a96fd8ecacc81a8e83742c86716525) changes the workflow-dispatch ref to `main`, retaining the immutable release tag as an explicit input. Both build and publication still check out that tag, and the cache source key still uses the actual checked-out commit. This follows [GitHub's cache-scope rules](https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching#restrictions-for-accessing-a-cache). The first subsequent main-scoped release may still be cold; later bumps can reuse that scope. No warm-release speedup percentage has been measured. The official 0.2.13 tag and assets were not rewritten.

## Source and documentation verification

The final aggregate gate verified 47 repositories and 73 packages against the latest default-branch heads, nested source links and locks. Real locked Cargo resolution passed for all 40 Rust repositories. The affected Project Z Python suites passed 8 managed-build tests and 58 coordinator tests, including their real local Git/Cargo fixtures. LMM's selected source update did not require a new internal dependency lock; no production database migration was performed or claimed.

The unified documentation snapshot contains 49 sources, 262 documents and 264 HTML pages. Its renderer checks passed all 40,653 local links. A native rebuild using Python 3.14.10 with pinned markdown-it-py 4.3.0 and mdurl 0.1.2 reproduced all 274 generated files, 11,436,209 bytes, exactly against the separately validated Python 3.12 snapshot. The full relative-path-sorted output digest is `e41385f5dd3a8ef037c02809ca16f66c9f9759e52fbc8b869966011a730a449b`. Existing end-of-file blank lines in three copied SSMCP documents were preserved as source bytes and are not represented as a clean whitespace check.

## Clipboard, Quickshell and Node findings

Only sizes, counts, source code and process metadata were used for the clipboard investigation.

| Observation | Measured scope |
| --- | --- |
| Clipboard history JSON | 83,496 bytes; 170 entries. |
| Text history | 132 entries; 67,818 UTF-8 bytes in total; largest 12,281 bytes. |
| Image references in current history | 38. |
| Image directory | 832 files, 246,366,998 logical bytes. |
| Images absent from the current index | 794 files, 242,584,034 logical bytes. They were retained. |
| Two `wl-paste` watchers | About 1 MiB RSS each in the observed sample. |
| Nine Node runtimes | RSS summed to approximately 25.9 MiB; logical `VmSwap` summed to 311.3 MiB. Shared resident pages can be counted more than once. |
| Quickshell | One sample had about 635 MiB RSS and 319 MiB logical Swap; an earlier proportional-set sample was about 409 MiB PSS. These are different observations and are not additive. |

Most Node instances belonged to development plugins and tools. The much larger `tsgo` process was a separate native type checker, even though it was launched by Bun and stored beneath `node_modules`.

The clipboard implementation already caps history at 500 entries, display/search results at 50, and displayed text at 8,192 characters per row. Its image component also constrains decode size. The small current history does not explain all of Quickshell's memory. Unreferenced image files are a disk-retention issue and cannot be counted as RAM savings.

A candidate clipboard change released the display model after the panel closed and avoided rebuilding it while closed. Nine offline lifecycle checks and a native Qt 6.12 syntax parse passed. A runtime activation probe after a plugin rescan still returned an unknown method, so the running shell's adoption of the change was not established.

The original Omarchy 4.5.0-3 `Clipboard.qml` was restored from the verified backup. Its final SHA-256 is `af90eeec633f1e18af3e561def188206a106326e3708dc3067144acdb65bc002`. The candidate is not installed and is not part of the default memory-management solution. No clipboard contents or image files were deleted, and no RAM saving is attributed to that experiment.

## Recording check

After the request to stop recording, the desktop recording helper reported no recorder process. Process and portal/PipeWire metadata also showed no active desktop screen recording or screen-capture video stream. The audio-effects session was left running. No saved recording file or terminated recorder is claimed.

## Limits

These measures preserve sessions and reduce competition; they do not make a finite RAM budget unlimited. zmem does not checkpoint arbitrary applications, recover unsaved content after an application exits, or automatically classify every inherited terminal child as background work. The earlier native KSM merge/COW and positive inactive-Swap cleanup exercises remain deferred under pressure; the unit and ownership tests are not substitutes for those host experiments.

Mechanism references: [Linux PSI](https://docs.kernel.org/accounting/psi.html), [zram](https://docs.kernel.org/admin-guide/blockdev/zram.html), [cgroup v2](https://docs.kernel.org/admin-guide/cgroup-v2.html), and [systemd resource controls](https://www.freedesktop.org/software/systemd/man/latest/systemd.resource-control.html).
