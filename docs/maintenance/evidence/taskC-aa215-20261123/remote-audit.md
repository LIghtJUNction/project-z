# Project Z maintenance audit

UTC: 2026-11-23T15:03:07.534975+00:00

Upstream updates: **4** · Missing/yanked versions: **16** · Candidates for review: **6** · Audit errors: **1**

## Known upstream updates

| Repository | Pinned | Observed upstream |
|---|---|---|
| lmm-api-source | 3385d567ef0e | 15bc9d989dfa |
| ssmcp | 87c4a17faf0d | 7bb087582e74 |
| zgpui | eeb909e956ed | d34c41f79dda |
| zterm | c0860ae44dbf | f1da2db1613f |

## Registry work

- `mechrevo-console-cli@0.1.0`: missing
- `mechrevo-console-core@0.1.0`: missing
- `mechrevo-console-gui@0.1.0`: missing
- `ssmcp@0.10.27`: missing
- `zcall-gui@0.1.6`: missing
- `zcalld@0.4.4`: missing
- `zcalld-plugin-api@0.4.4`: missing
- `zcalld-plugin-routing@0.4.4`: missing
- `zdot@0.2.0`: missing
- `zinput-wayland@0.1.0`: missing
- `zinput-x11@0.1.0`: missing
- `zmcl@0.1.4`: missing
- `zmcl-core@0.1.0`: missing
- `zmem-manager@0.4.5`: missing
- `ztty@0.6.1`: missing
- `zuse-computer@0.6.0`: missing

## Candidates requiring semantic review

- LIghtJUNction/zaccel (Rust): Run bounded WGSL compute scripts on native GPUs
- LIghtJUNction/zbridge (Rust): Bounded, authorized frontend protocol for shared Project Z application cores
- LIghtJUNction/zchat (Rust): AI-native messaging workspace built with zgpui, zplugin and unified MCP interfaces
- LIghtJUNction/zobs (Rust): Lightweight Project Z recording studio with zgpui, CLI and MCP
- LIghtJUNction/zrun (Rust): Independent Rust async runtime with bounded tasks, timers and reproducible benchmarks
- LIghtJUNction/zuse-skills (Python): Composable, non-preemptive GUI skills for zuse

Candidates are not added automatically. Review package role, dependencies and system boundaries.

## Incomplete checks

- Command '['git', 'ls-remote', '--symref', '--', 'https://github.com/LIghtJUNction/zcall-gui.git', 'HEAD']' timed out after 15 seconds

