# 共享实现规则与 zbridge 登记交接

日期：2026-11-23（Asia/Taipei）。聚合基线：`dbeecf0c038d9184825e6fb2a25dfdc5eb951e40`。

本次完成共享实现规则、根仓库 zbridge 登记、ssmcp-desktop 扫描入口补齐和对应局部验证。全图依赖验收仍有明确阻碍：协调端既有 `check` 与 `resolve --all` 均退出 1；本次维护审计因一次远端查询超时退出 2。以下记录保留各自快照、执行者与范围，不能作为全图发布通过的凭据。[证据目录](evidence/taskC-aa215-20261123/)

## 1. 本次变更与边界

| 变更 | 作用 | 核对依据 |
| --- | --- | --- |
| [AGENTS.md](../../AGENTS.md)、[CONTRIBUTING.md](../../CONTRIBUTING.md) | 将共享实现审查纳入维护要求，并指向同一份详细规则 | 本次差异 |
| [共享实现规则](../shared-implementations.md) | 以实际消费者和行为契约判断复用或抽库；区分生产副本、平台后端、独立测试参考、生成代码与薄适配 | 规则中的分类表、迁移步骤、验收表和记录模板 |
| [.gitmodules](../../.gitmodules)、[project-z.toml](../../project-z.toml)、根 `zbridge` gitlink | 将独立协议库登记为受协调的 library，manifest 为 `Cargo.toml` | [登记校验](evidence/taskC-aa215-20261123/registration.json) |
| `project-z.toml` 中的 ssmcp manifests | 显式包含根 `Cargo.toml` 和 `apps/ssmcp-desktop/Cargo.toml`，让扫描覆盖独立桌面 workspace | [桌面入口证据](evidence/taskC-aa215-20261123/desktop-registration.json) |
| 本交接与文本证据 | 将实际通过项、历史复用项和待办交给集成维护者 | 各节对应原始记录 |

工作在独立 clone 中完成，分支为 `task/astra-maintenance-20261123`。本次没有改写协调脚本、已有测试、`catalog.json`、`docs/PROJECTS.md` 或既有子仓库提交；46 个原有 gitlink 均保持基线值。完整索引由协调者接收各消费者提交后统一生成。[登记校验](evidence/taskC-aa215-20261123/registration.json)

规则约束后续工作，但不宣称现有代码已经全量去重。ztty/zmcl 的实际 hex 调用迁移由对应消费者负责人执行；本次没有以规范文档替代其源码、锁文件和行为验收。

## 2. zbridge 来源与实际门禁

规范 URL 来自协调快照的 `ssmcp/.gitmodules`：`https://github.com/LIghtJUNction/zbridge.git`。实际 `ls-remote --symref` 观察到默认分支 `main`，提交为 `1cfeb5b1f11c26c35cf7456c9b8b60d1f2d5d8de`；随后 fetch 与 detached checkout 得到同一提交。根 gitlink 也与 ssmcp 当时的 `crates/zbridge` gitlink 相同。[命令记录](evidence/taskC-aa215-20261123/zbridge-registration-commands.json) · [父子来源核对](evidence/taskC-aa215-20261123/registration.json)

zbridge 版本为 0.1.0，声明 Rust 1.85；直接依赖为 serde 和 serde_json。本次没有把 ssmcp 的 zi18n tag 问题归给 zbridge。[manifest 摘要](evidence/taskC-aa215-20261123/registration.json)

现有 `repositories(..., allow_uninitialized=True)` 实际读取 47 个登记项，并确认 zbridge 的 URL、默认分支、版本提交、library 角色与 manifest。现有 `verify_source_checkout` 对 zbridge 的独立 checkout 校验通过，源码保持干净。这里只核验登记和已检出的 zbridge，没有在其余未初始化目录上声称完成全图检查。

在 sandbox 中，最外层统一持有 `/var/tmp/project-z-cargo-target/.project-z-cargo-owner.lock`，`CARGO_TARGET_DIR` 为同目录。使用 Rust 1.100.0 和已有缓存，于台北时间 23:12:47–23:12:57 顺序执行：

| 实际命令 | 结果 | 用时 |
| --- | --- | --- |
| `cargo fmt --all -- --check` | 退出 0 | 0.202 秒 |
| `cargo test --locked --offline --all-targets` | 9 项测试通过，退出 0 | 6.588 秒 |
| `cargo clippy --locked --offline --all-targets -- -D warnings` | 退出 0 | 3.022 秒 |

[门禁记录、环境与日志哈希](evidence/taskC-aa215-20261123/zbridge-gates.json) · [测试输出](evidence/taskC-aa215-20261123/zbridge-test.stdout.log)

这些测试覆盖已有协议断言，包括权限与世代检查、请求/响应界限、事件保留与游标、大整数计数、迟到结果及不确定命令效果。Cargo.lock 前后 SHA-256 相同，均为 `87827aba6a44bbc7ac08d20b7c6bddcdce2b283d3f59f6360915090bf5cda1f7`。本次没有验证 Rust 1.85、浏览器、GUI、设备或跨平台集成；Rust 1.100 通过不能代替最低工具链验证。[测试与锁证据](evidence/taskC-aa215-20261123/zbridge-gates.json)

### 独立桌面 workspace 的扫描入口

协调者补充确认 ssmcp-desktop 是实际消费者。本次在 ssmcp 提交 `7bb087582e74e7b75cdb2e6997d61d826d5cebd8` 的 Git tree 中读取到受跟踪的 `apps/ssmcp-desktop/Cargo.toml` 和独立 Cargo.lock；manifest 声明自己的 `[workspace]`，通过 `path = "../.."` 使用同仓 ssmcp，并声明 `publish = false`。因此只扫描根 manifest 会漏掉该应用自己的依赖与锁。[原文件身份与登记结果](evidence/taskC-aa215-20261123/desktop-registration.json)

本次只补根策略的 manifest 列表。上述消费者提交还带有 zgpui 的 `rev` 限定，协调者已安排消费者负责人更新声明和独立锁；本次未改该源码，也未执行桌面端 Cargo 门禁。最终集成须一并接收已验证的 ssmcp 新提交，重新生成 inventory，并确认桌面 workspace 的 locked 解析确实执行。

## 3. 已集成的归属修复不重复实施

公开基线已经包含 `9f3a46cffabdd6f271cc3db7b4f61c5d4d92820c`，即原任务补丁 `680773d664be3effc6b5d4ba69ea060a371e628e` 的主线集成。本次逐字节比较 `scripts/project_z.py`、`tests/test_recursive_sources.py`、`tests/test_project_z.py` 和 `tests/test_maintenance.py`，均与集成提交相同；校验值保存在[复用依据](evidence/taskC-aa215-20261123/ownership-fix-reuse.json)。

[原验证文档](2026-11-23-submodule-ownership.md)记录：旧实现的 4 项反例失败；修复后相关 39 项通过；协调端在主线独立 clone 上再次运行 39 项通过。本次复用这些记录，没有重跑未变的测试，也没有将历史测试计入本次 zbridge 的 9 项结果。

## 4. 全图检查的真实阻碍

以下是协调端 22:55 的实际 `check` / `resolve --all` 记录及 22:59 的 readiness 快照。本次读取原始文件并按原字节保存，来源路径和 SHA-256 见[出处清单](evidence/taskC-aa215-20261123/coordinator-evidence-provenance.json)。协调端当时已下载 46 个来源、得到 73 个 package，完成 51 个嵌套来源初始化；不能由下载完成推导验收通过。

| 实际门禁 | 结果 | 解释 |
| --- | --- | --- |
| `python3 scripts/project_z.py check` | 退出 1，5.500 秒 | 存在来源、嵌套 checkout、内部声明和锁问题 |
| `python3 scripts/project_z.py resolve --all` | 退出 1，2.933 秒 | 在来源预检失败，未完成全图 Cargo 解析 |

[完整原始错误](evidence/taskC-aa215-20261123/coordinator-gates.json) · [readiness 快照](evidence/taskC-aa215-20261123/coordinator-sandbox-readiness.json)

### 4.1 六个直接过时的嵌套 gitlink

下表提交缩写仅便于阅读，完整值保留在[来源预检](evidence/taskC-aa215-20261123/coordinator-source-link-preflight.json)及 readiness 中。“目标”指记录快照所期望的提交；最终集成时仍需核对届时的远端默认分支。

| 消费者路径 | 当时记录 → 快照目标 | 已分配负责人 |
| --- | --- | --- |
| `ztty/crates/zgpui` | `eeb909e956ed` → `d34c41f79dda` | ztty/zmcl 去重任务负责人 |
| `ztty/crates/zterm` | `c0860ae44dbf` → `f1da2db1613f` | ztty/zmcl 去重任务负责人 |
| `zmcl/vendor/zgpui` | `eeb909e956ed` → `d34c41f79dda` | ztty/zmcl 去重任务负责人 |
| `zcall-gui/vendor/zgpui` | `eeb909e956ed` → `d34c41f79dda` | 主协调者 |
| `ztype/vendor/zgpui` | `eeb909e956ed` → `d34c41f79dda` | 主协调者 |
| `oh-my-ztty/components/ssmcp` | `87c4a17faf0dd` → `7bb087582e74` | 主协调者 |

递归快照另外出现 `oh-my-ztty/components/ztty/crates/zgpui`、`oh-my-ztty/components/ztty/crates/zterm` 和 `zcalld/apps/zcall-gui/vendor/zgpui`。因此是六个直接消费者 pin、九个路径出现位置；包装仓库仍需跟进消费者的新提交。

### 4.2 七条旧锁记录与一个声明问题

| 消费者 Cargo.lock | 旧内部包条目 | 跟进方式 |
| --- | --- | --- |
| ztty | zgpui 0.1.8、zterm 0.5.2 | 与该消费者 gitlink / 实际调用迁移一起更新并验证 |
| zmcl | zgpui 0.1.8 | 同上 |
| zcall-gui | zgpui 0.1.8 | 主协调者更新消费者后重算锁 |
| ztype | zgpui 0.1.8、zgpui-raster 0.1.0 | 主协调者更新消费者后重算锁 |
| ssmcp | zi18n 0.1.0 | 先修正带 tag 的声明，再更新锁并验收 |

[七条锁错误及完整期望来源](evidence/taskC-aa215-20261123/coordinator-locked-source-errors.json)

ssmcp 声明中的 `tag = "v0.1.0"` 使旧 zi18n 来源为 `?tag=v0.1.0#b90984b...`；记录快照期望无 tag 的默认分支提交 `755549f82fa513c4e4f2f5aaf6fdeea8da4a6347`。版本号相同而来源提交不同，仍然需要传播更新。当前规则要求真实适配，不通过继续固定旧内部来源、path 或 registry 覆盖消除报错。[原门禁错误](evidence/taskC-aa215-20261123/coordinator-gates.json)

## 5. 本次远端维护审计

在自己的开发机独立 clone 上实际运行：

```sh
python3 -B scripts/maintenance.py --require-catalog \
  --workers 4 --timeout 15 --owner LIghtJUNction \
  --output docs/maintenance/evidence/taskC-aa215-20261123/remote-audit.json \
  --report docs/maintenance/evidence/taskC-aa215-20261123/remote-audit.md
```

原 job `e968dedf4e63a140c6b2d941182288ad-972` 完成，退出码 2，stdout / stderr 均已读到 EOF；没有在观察超时后重新执行。报告时间为台北 23:03:07，基线根目录当时干净。[观察记录](evidence/taskC-aa215-20261123/remote-audit-observation.json) · [完整 JSON](evidence/taskC-aa215-20261123/remote-audit.json) · [报告](evidence/taskC-aa215-20261123/remote-audit.md)

审计观察到四个上游提交变化：lmm-api-source、ssmcp、zgpui、zterm；16 个记录版本在 registry 查询中为 missing；另有 zaccel、zbridge、zchat、zobs、zrun、zuse-skills 六个候选仓库。候选不自动加入，missing 也不自动构成发布指令；角色、实际发布意图和消费者由协调者审查。本次只接收任务已明确授权的 zbridge 登记。

唯一审计错误是 `zcall-gui.git` 的 `git ls-remote --symref -- ... HEAD` 查询在 15 秒超时。因此不能宣称全部上游查询完成；协调者在最终集成的远端新鲜度检查中补齐此项即可，不必重放已经完成的旧审计来覆盖其历史结论。

对提交中保存的 46 仓库 / 73 package catalog 调用已有 `repository_impact` 函数，九个输入仓库的传播闭包包含 27 个仓库（含输入自身）。完整逐提供者清单见[记录快照影响范围](evidence/taskC-aa215-20261123/recorded-catalog-impact.json)。这次只读取已记录 catalog，没有执行会读取 Cargo metadata 的 CLI `impact`；该旧 catalog 尚不含 zbridge，亦不能体现尚未合并的 ztty/zmcl → zhex 新关系。

## 6. 按依赖顺序接手

1. **基础库任务负责人**提交六库范围内实际发生的依赖和辅助锁变化。已通过且源码未变的基线按原记录复用；zconv fuzz 的 cc 精确更新由主协调者验证。
2. **ztty/zmcl 负责人**交付真实 `zhex::encode_lower` 调用、被替代生产副本的删除、消费者嵌套来源和锁更新，以及对应行为门禁。
3. **主协调者**整合 ssmcp、zcall-gui、ztype 的声明 / 锁 / gitlink，包括 ssmcp-desktop 的独立 manifest 与锁；再按新消费者提交推进 oh-my-ztty、zcalld 等包装来源。先有已验证子提交，再更新父 gitlink。
4. **主协调者**在完整独立快照接收本提交与各消费者提交，核对远端默认分支，重新生成全量 catalog 和项目索引。登记 zbridge 后要确认其真实消费者和嵌套来源进入生成结果。
5. **主协调者**在同一完整快照执行来源检查和全图 locked 解析；有行为变化的消费者保留自己的 GUI、设备、服务或发行门禁。失败记录按具体消费者继续处理，不以局部通过替代。
6. **主协调者**完成提交、推送、远端读回和所需发行验证后，才更新发布状态。本 worker 的交接不表示这些步骤已完成。

用于最终完整快照的门禁命令如下。执行前应已完成来源更新和全量索引生成；这组命令是交接步骤，本次没有再执行：

```sh
export CARGO_TARGET_DIR=/var/tmp/project-z-cargo-target
mkdir -p "$CARGO_TARGET_DIR"
flock "$CARGO_TARGET_DIR/.project-z-cargo-owner.lock" sh -eu -c '
  python3 -B scripts/project_z.py impact --repositories zbridge zconv zclap zhex zfetch zcall zmcpio zgpui zterm ssmcp
  python3 -B scripts/project_z.py check
  python3 -B scripts/project_z.py resolve --all
'
```

共享锁只由最外层获取。上述门禁要在已配置工具链的完整独立 checkout 执行，不在生产主 checkout 上自动同步。协调端另有 zfetch 环境依赖记录：缺少 `/sys/devices/system/cpu/online`；该应用验收尚待其负责人处理，本次没有改写或重试。[readiness 中的环境记录](evidence/taskC-aa215-20261123/coordinator-sandbox-readiness.json)

## 7. 交付前证据复核

| 复核维度 | 结论与限制 |
| --- | --- |
| 实际贡献 | 规则成为根维护入口；zbridge 从候选变为已验证登记；补齐独立桌面 workspace 扫描入口。没有声称完成所有消费者去重 |
| 清晰度 | 区分实际新运行、已完成任务的历史复用、协调端现有失败记录和未来命令 |
| 验证力度 | zbridge 三项门禁和 9 项现有断言实际通过；源码归属与登记验证通过。未验证 MSRV、GUI、设备和全图成功 |
| 完整性 | 列出六个直接 pin、九个路径出现位置、七个旧锁条目、一个 tag 声明问题和一次审计超时，并保留来源 |
| 设计合理性 | 共同契约决定共享边界；保护必要后端和独立测试预期。自动来源检查不承担语义去重判断 |

原样保存的 `remote-audit.md` 与 `zbridge-test.stdout.log` 在末尾含空行，完整 `git diff --cached --check` 因此退出 2。保留这些输出的原始字节；排除这两个证据文件后，源码、策略和文档的差异检查退出 0。对应检查记录及范围见[交付核验](evidence/taskC-aa215-20261123/delivery-verification.json)。
