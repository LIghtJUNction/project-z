# Memory and Swap

zmem is the suite's default system memory manager. The release installer sets it up with administrator privileges, enables `zmem.service`, and hands management of existing Swap to zmem. The terminal, shell and AI tools use the same system policy.

## See what the system is doing

```sh
omztty memory
omztty memory status --json --processes
omztty memory status --live --json
omztty memory plan --json
omztty memory doctor --json
```

`status` uses the report of the active zmem daemon after checking its process identity. The report retains that daemon's policy history, measured paging rates, worker state and errors. `--processes` adds a current process list. The `observation` fields identify the report source, sampling age and stale data; process measurements have their own timestamp. `omztty doctor` also shows whether the system memory service is active.

`status --live` and `plan` take an independent sample and show a proposed action without applying it. They begin with a new policy state, and paging rates are `null` until measurements are available. If the daemon report cannot be used, ordinary `status` labels its fallback as an independent snapshot and records the cache error. AI clients should check this provenance before interpreting a decision as a daemon report.

## Read pressure, controls and coverage

Memory pressure and IO congestion are separate signals. zmem observes available RAM, memory stalls, file-page refaults and swap activity to decide whether to adjust memory budgets or Swap capacity. Busy IO alone does not establish the cost of disk Swap. Without confirmed disk Swap reads, file-refault evidence can favor retaining file cache; otherwise zmem uses a neutral paging preference with hysteresis. That neutral preference can lower an earlier elevated setting. Confirmed disk Swap read pressure follows a separate reduction path.

From zmem 0.3.1, `reclaim_latency_guard` blocks automatic promotion when memory full stalls reach 1%, direct scans reach 64 MiB/s and anonymous refaults reach 4 MiB/s in the same warmed observation. It requests a ceiling of 60 and preserves an actual value already below that ceiling. The guard uses the ordinary adjustment rules: 10 seconds of supporting evidence, 30-second spacing between confirmed changes and steps of at most 20. These are conservative control thresholds, not measurements of input latency. If the current swappiness cannot be read, zmem reports `readback_unavailable`, leaves the requested value `null` and skips the sysctl write.

The `controls` object reports requested and actual swappiness, its reason, the actual page-cluster value, the protection budget and the count of successfully protected scopes. `protection_sampled_at_unix` and `protection_errors` retain the most recent protection check's time and diagnostics between checks. `managed` reports background groups, populated groups, task counts, memory usage and eligible reclaim candidates. The `protection_complete` and `coverage_complete` flags expose incomplete control operations or observations. A plan's requested bytes describe an intended action; observed reclaim progress is reported separately.

The `background` object reports `requested_budget_bytes`, `actual_budget_bytes` and per-group limits. The actual aggregate comes from reading back the limits of populated groups; `plan_available`, `readback_complete` and `applied_complete` identify available plans, complete observations and successful application. With complete information, a `null` budget means no temporary requested ceiling or an unlimited observed group; otherwise it is unavailable. `plan.background_high_percent` remains a pressure-severity hint. Use the byte fields to inspect requested and actual quotas.

An empty background scope has no work to constrain or reclaim. zmem applies background budgets to jobs started in its managed class. Existing applications outside those groups keep their current placement. Interactive protection follows recognized desktop, terminal and remote-access processes into their nested cgroups and distributes a bounded budget through the hierarchy. Recursive kernel protection can pass an ancestor's budget to children even when a child's local `memory.low` is zero.

## Keep background jobs manageable

The suite's source-bundle builder, direct Cargo commands in its component checker, and Project Z's build coordinator automatically start new Cargo builds, checks, tests, benchmarks, Clippy, documentation and compiler jobs in zmem's background class when an active, identity-verified zmem 0.2 or newer is available. This gives the daemon a separate group to budget before the job allocates memory. The existing outer Cargo build lock still coordinates shared build files.

If the required Linux systemd manager or verified zmem daemon is unavailable, the build entry point reports the reason and runs the command normally. Set `ZMEM_BUILD_BACKGROUND=0` for a build batch to keep the caller's current classification. This automatic routing applies to those source entry points' direct Cargo invocations; it does not add `--dedup` or register build memory for merging. Other background commands can use the explicit form below.

Start a build or other background job through the managed scope:

```sh
omztty memory run --class background -- cargo build
```

Interactive work can use `--class interactive`. The `disposable` class is for work you explicitly allow to encounter a hard memory limit. Use the class before starting the process so the kernel accounts for its memory in the intended group.

### Wait before starting more heavy work

With zmem 0.4, background and disposable commands check available RAM and memory PSI before execution. The default wait is 60 seconds. A timeout returns exit code 75 without starting the target; an interactive command bypasses admission. The suite's managed Cargo entry points inherit this behavior when the installed manager is upgraded.

```sh
# Allow a batch job up to five minutes to find sufficient headroom.
omztty memory run --class background --wait-timeout 300 -- cargo build --release --locked

# Check once and leave the command unstarted if conditions are unsuitable.
omztty memory run --class background --wait-timeout 0 -- YOUR_COMMAND
```

A healthy first observation can pass immediately. After pressure or a missing observation, memory must satisfy stricter recovery conditions for three seconds. Launch reservations by the same user are spaced by at least three seconds to limit a simultaneous burst; scheduling can still change actual execution timing. Waiting emits JSON events on stderr, keeps stdout for the command, and can be cancelled with SIGINT or SIGTERM. This is not a persistent FIFO queue or a prediction of a program's peak memory.

Admission does not install a permanent CPU quota or storage bandwidth cap. The [zmem admission guide](https://github.com/LIghtJUNction/zmem/blob/main/docs/background-admission.md) describes the launch reserve, thresholds and exit codes. Existing running programs outside the managed groups retain their placement; arbitrary terminal commands are not automatically intercepted.

### Reuse compilation work

Keep the shared Cargo target directory when repeating local checks. Fresh temporary target directories cannot reuse that directory's earlier compiled artifacts. The source helpers retain the existing outer build lock and do not move Cargo metadata queries into admission.

Official releases cache Cargo downloads, unpacked registry and Git dependency sources, final outputs and intermediate build artifacts. The cache is separated by architecture, runner and actual Rust toolchain identity, with source and lock identities in the key. Cargo still checks restored fingerprints, and installer, source-lock, smoke and graphical checks continue to run. The first run populates the cache; a warm-cache speedup has not yet been measured. See the [Cargo build-cache documentation](https://doc.rust-lang.org/cargo/reference/build-cache.html) for the separate target and build directories.

Background jobs inherit the managed aggregate's dynamic budget. Starting a background job adds no fixed half-RAM limit to its child scope. During pressure, the daemon calculates the aggregate from current managed usage, available RAM and the configured reserve plus a safety margin. Populated groups share the budget; empty groups receive no share. Existing external limits remain in force.

Changes tighten groups before relaxing any limits. A failed tightening blocks that batch's relaxations, and a failed relaxation stops the remaining ones. Incomplete observations hold existing controls; only kernel readback confirms the resulting budget. Measured spare headroom allows gradual recovery even while the current `memory.high` limit produces PSI stalls, so work can regain capacity as room becomes available. Healthy policy removes the temporary restriction.

Proactive reclaim selects populated managed groups with eligible clean file pages. Empty groups and groups without suitable pages are skipped; requests that produce no observed progress trigger a retry backoff. The current coverage and progress reports show which work this policy can affect.

The default policy preserves processes. It does not discard application data, clear the entire page cache or provide application checkpoints. Applications remain responsible for saving their documents and progress.

## Enable IO controls for user jobs

Setup with zmem 0.3.1 adds IO delegation and accounting to `user@.service` through `/etc/systemd/system/user@.service.d/50-zmem-io.conf`. The drop-in appends `Delegate=io` and enables `IOAccounting=yes`, preserving existing CPU, memory and PID delegation. An existing external file at the same path is kept, even if its contents match. A separate ownership journal lets rollback remove only an unchanged file that zmem created; changed or replaced files are preserved.

Existing user managers may report `user_io.state = needs_refresh`. Installation does not restart user sessions or refresh every user's manager automatically. In the affected user's session, reload the manager's executable while keeping its processes:

```sh
systemctl --user daemon-reexec
omztty memory doctor --json
```

Check `user_io.io_available` and `io_enabled_for_children`, then inspect the returned `manager_cgroup`: `cgroup.controllers` and `cgroup.subtree_control` should include `io`, and `io.stat` should exist. Managed child groups also need the relevant `io.weight` or `io.max` files. Unavailable observations remain `null`; the report checks the caller's manager, or the originating user when invoked through sudo.

Delegation makes these controls available; a configured `IOWeight` does not establish its scheduling effect. Weight control also needs a supporting device backend, such as BFQ or enabled IO cost control, and kernel readback. `io_weight_effective` stays `null` because those configuration checks do not measure workload impact. The [zmem 0.3.1 acceptance record](https://github.com/LIghtJUNction/zmem/blob/main/docs/acceptance-0.3.1.md) separates host-specific observations from general policy. No fixed IO limit or desktop responsiveness gain is implied for another machine.

## Automatic Swap maintenance

zmem 0.3 grows disk Swap in configured chunks and revisits retained owned files automatically. Maintenance attempts are at least 60 seconds apart, with one candidate per attempt, after growth or managed-background reclaim work. Cleanup uses an identity-checked, kernel-guarded unlink without migrating pages; a missing canonical pathname does not prove that a file is inactive.

Active retirement waits for sustained healthy conditions, 600 seconds by default, and rechecks RAM and remaining Swap against the candidate's entire capacity. Known used files are skipped. Shared locking covers zmem's allocation and syscall-helper lifetimes, including a helper that outlives a timeout. Maintenance does not rewrite or apply filesystem deduplication to active Swap. See the [zmem lifecycle guide](https://github.com/LIghtJUNction/zmem/blob/main/docs/swap-lifecycle-and-dedup.md) for the separate cleanup and retirement gates.

## Register trusted jobs for memory deduplication

With zmem 0.3 or newer, explicitly register a compatible background or disposable workload:

```sh
omztty memory run --class background --dedup -- YOUR_TRUSTED_COMMAND
omztty memory run --class disposable --max-memory 2048 --dedup -- YOUR_TRUSTED_BATCH_COMMAND
```

The default `dedup_enabled = true` allows the daemon to manage scanning for registered tasks. It does not enroll other applications, and ordinary background commands keep their existing registration state. `--dedup` is unavailable for the interactive class. Unsupported or unverifiable process registration produces an error before the target command starts.

KSM matching is system-wide: process, user and cgroup boundaries do not isolate its matching domain, and other software may already have registered eligible pages. Choose trusted workloads whose data may share that domain. zmem preserves external KSM controllers and advisors. For controls it owns, CPU, memory or IO pressure pauses scanning with `run=0`; 30 seconds of stable observations are required before scanning resumes. The 128-page batch and 100 ms sleep are scan settings, not a hard CPU quota. Pausing preserves merged pages; zmem does not force an unmerge with `run=2` or `PR_SET_MEMORY_MERGE=0`.

The `dedup` report exposes observed and target state, reason, ownership and bounded task discovery refreshed every 10 seconds. Check its observation age and coverage flags. The `ksm` report contains actual controls and a signed system-wide profit estimate; missing metrics remain `null`, and global profit is not attributable solely to zmem. Independent `--live` and `plan` previews do not have the daemon's registered-task history.

The earlier [0.2.0 acceptance record](https://github.com/LIghtJUNction/zmem/blob/main/docs/acceptance-0.2.0.md) does not measure these lifecycle or dedup additions. No fixed memory saving or responsiveness gain is implied by enabling them.

## Default policy

The suite ships `config/zmem/zmem.conf`. On first setup, zmem copies this policy to `/etc/zmem/zmem.conf`. Later installs preserve the existing system configuration.

| Setting | Default |
| --- | --- |
| Observation interval | 2 seconds |
| Disk Swap growth step | 2 GiB |
| Maximum managed disk Swap | 32 GiB |
| Disk space kept available | 8 GiB |
| Target free Swap | 4 GiB |
| RAM reserve | Scaled to installed RAM |
| New zram capacity | 50% of RAM |
| Session protection | Enabled |
| Swappiness management | Enabled |
| KSM scanning control | Enabled for explicitly registered tasks; registration remains opt-in |
| Profile | Balanced |

Edit `/etc/zmem/zmem.conf` with administrator privileges, then restart `zmem.service`. Existing occupied Swap stays active during adoption; the configured zram layout applies when zmem initializes a device at boot. The [zmem documentation](https://github.com/LIghtJUNction/zmem) defines the configuration keys, policy limits and recovery behavior.

Use `dedup_enabled = false` to disable zmem's scanning policy; this does not forcibly unmerge existing pages or take over an external controller. Use `protect_sessions = false` to disable automatic session protection. While protection is enabled, an already owned `memory.low` control reset to its original zero can be reapplied if the cgroup identity is unchanged; manually writing zero is not a persistent opt-out. Nonzero external settings remain protected.

## Setup, updates and recovery

The normal release installation includes system memory setup. For a container, a non-systemd environment or a per-user-only installation, use:

```sh
sh install.sh --no-memory-manager
```

This skips system setup and records the choice for future updates. It does not stop an existing system manager. Enable zmem later with:

```sh
omztty memory setup
omztty update --memory-manager
```

`memory setup` installs the bundled version immediately. `update --memory-manager` also records that system memory management should be included in future suite updates. The setup command copies the executable to root-owned `/usr/local/bin/zmem`; the system service runs that copy, independently of the user-writable suite directory.

To restore the memory managers and configuration recorded before zmem took over:

```sh
omztty memory rollback
```

The system memory service has its own lifetime. Removing the per-user terminal suite keeps it available, along with `/etc/zmem/zmem.conf`. If the suite has already been removed, its recovery command is:

```sh
sudo /usr/local/bin/zmem rollback
```

Package-managed installations can use `omztty memory setup` when their bundle includes zmem. Their ordinary runtime updates continue through the distribution's package manager.
