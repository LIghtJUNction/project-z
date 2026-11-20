# Project Z：维护快照解析门禁与项目状态

日期：2026-11-20（Asia/Taipei）。本轮代码已经提交并推送到主线，提交为 [b9de9241bf4c](https://github.com/LIghtJUNction/project-z/commit/b9de9241bf4cb9e95fdc079a727bf947da782652)。

## 本轮完成

自动维护现在会在生成候选提交前，依次完成清单生成、声明检查和全部 Rust 工作区的实际依赖解析。应用请求不存在的库功能时，维护结果保持 `blocked`，原工作树保持干净，隔离候选现场保留用于检查；可以解析的升级仍正常产生提交。这个修复把已有 Cargo 解析能力接到了自动维护的提交入口。

本轮没有改变库版本或聚合 gitlink。验证使用原有 42 个仓库、60 个 Cargo 包和其中 36 个 Rust 仓库的固定来源，源码快照基线为 `8e7416ede0753d8758153d944ef7a9d17e4a3f2a`。修复后的协调器与这些来源一起通过了实际验证。

## 问题与修复机制

依赖声明中的版本约束和功能名称回答不同的问题。版本约束决定可以选择哪个版本；Cargo 的 feature 选择还要求该版本实际提供所请求的功能。原维护入口运行 `sync` 和 `check` 后就提交候选，缺少由 Cargo 解析完整依赖的步骤。

真实离线夹具使用一个包含库和应用的工作区：库提供 `allowed` 功能，应用升级后请求 `absent` 功能。声明检查仍通过，Cargo 解析会报告库没有该功能。修复将 `resolve --all` 加入候选提交之前的门禁；`--all` 确保角色为 application 的仓库也参与解析。

| 阶段 | 实际职责 | 通过后的行为 |
| --- | --- | --- |
| `sync` | 从固定源码重建清单、项目索引和本地覆盖 | 进入声明检查 |
| `check` | 核对版本约束、依赖图、源码归属和生成文件 | 进入 Cargo 解析 |
| `resolve --all` | 解析全部 Rust 工作区，并核对选中的 Project Z 源码 | 允许形成候选提交 |

任一门禁失败都保留隔离工作树，候选不产生提交。后续发布仍执行受影响库、应用和目标平台的实际验收。代码见 [maintenance.py](https://github.com/LIghtJUNction/project-z/blob/b9de9241bf4cb9e95fdc079a727bf947da782652/scripts/maintenance.py)，使用说明见 [自动维护说明](https://github.com/LIghtJUNction/project-z/blob/b9de9241bf4cb9e95fdc079a727bf947da782652/docs/automation.md)。

## 实际验证

开发机环境为 Linux、Python 3.14.10、Cargo 1.100.0、Rust 1.100.0。Cargo 使用离线模式，验证复用已具备的依赖缓存。

| 验证 | 结果 | 证据 |
| --- | --- | --- |
| 完整协调器回归 | 82 项通过，0 失败、0 错误、0 跳过；11.770 秒 | [原始回归输出](../evidence/2026-11-20/maintenance-resolution-gate/regressions.log) |
| 新增应用依赖失败用例 | 缺失 feature 被阻断；没有候选提交；原树保持干净 | `OfflineResolutionApply.test_application_feature_resolution_failure_cannot_create_ready_snapshot` |
| 新增有效应用升级用例 | 实际创建候选提交；记录覆盖应用的解析结果 | `OfflineResolutionApply.test_resolved_application_snapshot_is_committed_with_resolution_evidence` |
| 清单生成及声明检查 | 42 仓库、60 包通过 | [sync](../evidence/2026-11-20/maintenance-resolution-gate/sync.log)、[check](../evidence/2026-11-20/maintenance-resolution-gate/check.log) |
| 实际依赖解析 | 36 个 Rust 仓库全部通过 | [resolve](../evidence/2026-11-20/maintenance-resolution-gate/resolve.log) |
| 工作现场保护 | 校验前后原工作树干净；新夹具同时检查临时配置和锁文件恢复 | [机器记录](../evidence/2026-11-20/maintenance-resolution-gate/validation.json) |

可复用的验证命令：

```sh
CARGO_NET_OFFLINE=true PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
python3 scripts/project_z.py sync
python3 scripts/project_z.py check
CARGO_NET_OFFLINE=true python3 scripts/project_z.py resolve --all
```

本轮验证范围是协调器和依赖解析，没有新增各应用的桌面、设备或发行验收，也没有性能改动。

## 依赖整合状态

| 项目 | 本次核对结果 | 后续范围 |
| --- | --- | --- |
| oh-my-ztty | [PR #1](https://github.com/LIghtJUNction/oh-my-ztty/pull/1) 已合并，合并提交 `463f1958555f13694de933b1b34d3ead4b9af642`；聚合已固定其中经过验证的 `0fdc87873c53e7c87d18952f83a7b94fc4149de5` | 套件正式发行及 SSMCP 制品传播继续按现有维护流程推进 |
| SSMCP | [PR #110](https://github.com/LIghtJUNction/ssmcp/pull/110) 仍是草稿，提交 `bc0ef8e0b24f7e0e58271046743c89334041ec51` | v0.10.15 组合源需要原生验收，聚合保留已验证来源 |
| WeightLang / LightNest | 已核对其[独立消费者图](https://github.com/WeightLang/WeightLang/blob/1abd163b4f60d7d4c748a509040708eb2419654f/docs/dependency-propagation.md)；当前 manifest 和锁文件没有真实 Z 库依赖 | 保留既有隔离登记草稿，后续按实际代码关系登记 |
| MatriXpost | 主线 `d9dacc4e88bd176a734e38bd0b23b96b480f7b09` 干净；当前为无运行时 npm 依赖的 Chromium MV3 应用 | 按用户补充要求准备独立 Pro 接力，当前没有新增 Z 库依赖登记 |

已被主线吸收的旧登记分支没有重复合入；带有未提交内容的历史工作树保留原状。

## zdistro 发布状态

zdistro 已有 [GitHub 正式 v0.1.0](https://github.com/LIghtJUNction/zdistro/releases/tag/v0.1.0)，发布标签固定 `6a54a137fc697d372b54ef85105315f2ce522b3d`，也是 Project Z 当前固定来源。Release 提供 wheel、sdist、zipapp、ZIP、Deb、Arch、校验清单、来源记录和验收包。

截至本轮查询，官方 [crates.io 接口](https://crates.io/api/v1/crates/zdistro) 返回 HTTP 404，内容为“crate `zdistro` does not exist”。当前 zdistro 自身使用 Python 3.11+ 标准库，提供 17 个打包后端；其中 `crate` 后端为输入的 Rust 项目调用 `cargo package`。其自身尚无可供 `cargo install zdistro` 安装的 crate。实现和入口见 [当前 README](https://github.com/LIghtJUNction/zdistro/blob/4d656faaa50e125b36060c3e08c2efbb31575c45/README.md)。

本轮读取的既有 Linux 验收矩阵包含 13 种产物验证记录：Deb、Arch、APK、AAB 使用原生工具，另外 9 种完成格式、完整性或元数据检查。macOS PKG/DMG、Windows MSI/MSIX 的本次现场回执尚未取得。开发主线还包含正式标签之后的 Debian 权限、Arch 隔离检查和 Docker Buildx 修正；现有 Release 附件固定在正式标签来源。[状态查询记录](../evidence/2026-11-20/maintenance-resolution-gate/zdistro-status.json)保留了官方接口结果和验证范围。

## zmcl 与 MatriXpost 接力

已核对 zmcl 主线 `3659cf144c69356268f9a185d9ea80eecb50cc7c` 和 MatriXpost 主线 `d9dacc4e88bd176a734e38bd0b23b96b480f7b09`，并分别准备了包含项目目标、现场状态、优先项和验收要求的接力内容。

新 Pro 对话尚未启动。开发机现有 Chrome 的 ChatGPT 页面显示登录入口，没有可用的 Pro 模型选择；页面已保留，等待用户在该浏览器完成登录。两个项目的源码和安装状态没有因本次接力准备而改变。

## 结论与证据核对

| 核对项 | 已有证据与结论 |
| --- | --- |
| 改动价值 | 修复已复现的不可解析候选被标记 ready 的问题 |
| 说明清晰度 | 分开解释版本声明、feature 解析和候选提交条件 |
| 验证强度 | 使用真实 Git 和 Cargo 夹具，并验证完整聚合来源 |
| 验证范围 | 82 项协调器回归和 36 仓库解析；应用运行和发行保留各自门禁 |
| 实现复杂度 | 复用现有解析入口，无新增运行时依赖或配置开关 |
