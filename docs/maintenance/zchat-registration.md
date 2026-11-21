# zchat source registration

Status: source registration prepared; the full Project Z snapshot has not passed validation.

This change registers zchat as an application and records its non-Cargo distribution
dependency on zdistro. The root Cargo workspace supplies zchat, zchat-core,
zchat-plugin-api and zchat-providers. The committed zchat gitlink identifies the
application source; its own repository maintains native build, runtime acceptance,
registry publication and release evidence.

## Evidence boundary

The integration attempt was captured on 2026-11-22 (Asia/Taipei), from aggregate
baseline `6e786250812849079c870804ce4141b74f88f7d3`. The isolated worktree included
13 unstaged updates to other repository gitlinks after fetching their default heads.
Those updates are not part of this registration change.

The coordinator reads checked-out child repository HEADs. Consequently, the attached
logs describe that latest-source integration attempt, not a clean checkout test of
this registration commit. The zchat registration gitlink was finalized afterward.
No generated catalog or full synchronization snapshot is accepted by this change.

- `check` exited 1: [complete output](zchat-integration-check.txt).
- `resolve --all` exited 1 during prerequisite validation, before Cargo resolution:
  [complete output](zchat-integration-resolve.txt).
- [Unstaged child gitlink differences](zchat-integration-gitlinks.diff) record the
  source set used by those checks.

## Consumer source links that blocked the initial synchronization

| Owning consumer and nested path | Commit recorded by consumer | Dependency checkout observed |
| --- | --- | --- |
| ssmcp/crates/zharness | `5f9a9f58f090326bf2d43f4df2cc90c1bc674c21` | `8907262ce6c8494f2849f8e5abd84f7a3da2e405` |
| oh-my-ztty/components/ssmcp | `ffb7f32f527357202194b41be7b7a904153a02ba` | `f2e9dcf22df7d37df7672bb7d41d1bcf7e6fc690` |
| zmcl/vendor/zclap | `4d87f3ae3743e81509d5ac5500909955667c860f` | `a4c7e6f3e0ff860de701573117248fe8538c71e5` |
| zmcl/vendor/zi18n | `cdff8dea19e97268d296afa827767ea689420591` | `755549f82fa513c4e4f2f5aaf6fdeea8da4a6347` |

The owning repositories must commit these changes before aggregate synchronization.
Update ssmcp before oh-my-ztty, because the latter distributes the former.
The two zmcl vendor links can be repaired in one consumer update. Moving only an
aggregate pointer or nested working directory does not repair a consumer HEAD.

## Font fix propagation and other remaining checks

zchat also prompted the published zgpui 0.1.8 fixed-strike font repair,
`eeb909e956ed0cff05e14525d4f29f5a78c553ec`.
The observed source set still records the earlier zgpui commit
`174a8b73087deeac2ecfa036cad8bddba71c612f` in ztty, zcall-gui, ztype and zmcl
nested source links, and in their locks plus zterm's lock. Those owning consumers
still require dependency updates and their actual GUI/runtime tests. The library
release and zchat's successful local use do not complete that propagation.

The check log also records other outdated consumer locks and uninitialized nested
repositories, including lmm, lmm-api-source, mechrevo-drivers, OniMods, zclick,
zdot, zuse and ssmcp. These observations are separate from zchat registration.
They must be re-evaluated against current default heads before accepting a snapshot.

## Completing aggregate integration

Preserve this registration commit as a reusable source change. After the owning
consumers have committed and pushed compatible source links and locks:

1. Use a clean isolated checkout with initialized source repositories.
2. Run `python3 scripts/project_z.py sync` and `python3 scripts/project_z.py check`.
3. Run `python3 scripts/project_z.py resolve --all` under the documented shared
   Cargo build lock, then run the affected behavior, GUI, ABI and packaging gates.
4. Record only the verified child gitlinks and regenerated `catalog.json` and
   `docs/PROJECTS.md`; merge this registration with that verified snapshot.

Do not use `sync --record` or old dependency locks to make these checks appear to
pass. This registration remains a blocked draft until the required gates pass.
