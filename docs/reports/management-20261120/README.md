# Project Z 管理进展 — 2026-11-20

本轮已完成两项主线改进：Project Z 支持按仓库分批准备更新；zmcpio 已接入 zcall 0.4.0，并完成库、源码包及直接消费者 zuse 的验证。两项 PR 均已合并。现有 43 个组件的稳定聚合指针继续保持上一轮验收组合。本文时间使用 Asia/Taipei（UTC+8）。

## 1. 已交付的源码

| 项目 | 已交付结果 | 固定来源 |
| --- | --- | --- |
| Project Z | 新增可重复的 `--repo PATH`，完整保留审计与全部 Rust 工作区的依赖解析 | [PR #5](https://github.com/LIghtJUNction/project-z/pull/5)；合并提交 [0d638519](https://github.com/LIghtJUNction/project-z/commit/0d638519117e375410743e61013114a6187b7f96) |
| zmcpio | 精确依赖升级为 zcall 0.4.0，更新锁文件和说明；现有 Rust 实现无需适配 | [PR #2](https://github.com/LIghtJUNction/zmcpio/pull/2)；合并提交 [a88d2acc](https://github.com/LIghtJUNction/zmcpio/commit/a88d2accf0fa642eded27c844aaf7d7bb6dd3501) |
| 独立复核 | ChatGPT 独立审查及用户授权的 agy 静态复核完成，无剩余阻断项 | [被审源码 c96e4cdb](https://github.com/LIghtJUNction/project-z/commit/c96e4cdbf4bcb08019975bff7e738b5fe62475b3)；[复核回执](https://github.com/LIghtJUNction/project-z/blob/main/docs/reports/management-20261120/review.json) |

Project Z 的实现先提交为 c96e4cdb，随后追加测试与上游审计记录，再合入主线。GitHub 的提交对比确认，这一批只修改维护脚本、对应测试、使用说明和证据文件；组件 gitlink、catalog 及 Cargo 协调配置均未变化。[完整差异](https://github.com/LIghtJUNction/project-z/compare/76dd114c11685d430dd55bb0d78b064a7349af73...0d638519117e375410743e61013114a6187b7f96)

## 2. 按仓库更新，同时检查全部消费者

组件的 gitlink 记录它所使用的精确提交。新的选择参数只决定哪些 gitlink 前进；随后 Cargo 仍解析全部库和应用。这样可以逐组推进已经准备好的依赖，同时发现未选应用与新库之间的不兼容。

本轮落实了以下行为：

- `--repo` 可重复指定，路径必须来自 `.gitmodules`；重复参数会去重。
- 未知路径和显式空范围在创建工作树前被拒绝；单独使用 `--repo` 会提示需要 `--apply`。
- JSON 和 Markdown 同时记录 `selected` 与 `deferred`，保留全局待办。
- 所选仓库没有变化时返回 `no_changes`，其它上游变化仍列为暂缓项。
- 省略选择参数时，继续采用原来的全部已知更新行为。
- 候选依次通过 `sync`、`check`、`resolve --all`，再形成提交。

回归测试包含一个独立消费者场景：只选择更新底层库，移除另一个未选应用需要的 feature，完整解析会拒绝该候选并保留原始检出。具体用法见[维护说明](https://github.com/LIghtJUNction/project-z/blob/0d638519117e375410743e61013114a6187b7f96/docs/automation.md)。

## 3. 实际验证结果

| 验证范围 | 结果 | 对应源码 |
| --- | --- | --- |
| Project Z 完整协调器回归 | 96 项通过，21.553 秒 | c96e4cdb |
| zmcpio 全目标、全部功能 | 209 项通过；另有 2 个子进程入口按既有设计由父测试启动 | ec43faa5 |
| zmcpio 无默认功能 | 170 项通过 | ec43faa5 |
| zmcpio 格式、依赖闭包、Clippy、WASM 编译 | 全部通过；默认依赖闭包维持 3 个包 | ec43faa5 |
| zmcpio 实际传输与源码包 | stdio、MCP client/bridge、HTTP JSON/SSE 和 `cargo package --locked --offline` 通过 | ec43faa5 |
| zuse 直接消费者 | 110 项库测试通过，12 项真实传输检查全部通过 | zuse 94c83755 + zmcpio ec43faa5 |
| agy 独立静态复核 | 主审查和定向补读均退出 0，均返回 SUCCESS，无阻断项 | c96e4cdb |

运行环境为 Linux x86_64、Rust/Cargo 1.100.0。WASM 结果属于编译验证。Project Z 的小型离线测试使用独立的 512 MiB、零 swap、单 CPU scope；只有该测试进程清空编译 wrapper，系统全局 Cargo 配置保持原值。96 项测试的完整输出和配置已保存。[验证回执](https://github.com/LIghtJUNction/project-z/blob/0d638519117e375410743e61013114a6187b7f96/docs/reports/management-20261120/coordinator-validation.json) · [测试输出](https://github.com/LIghtJUNction/project-z/blob/0d638519117e375410743e61013114a6187b7f96/docs/reports/management-20261120/coordinator-tests.txt)

zuse 通过临时 Cargo patch 选择确切的 zmcpio 源码，并测试真实 stdio、回环 HTTP、Unix socket、消息与权限校验，以及私有 Xvfb 显示中的实际截图。验证结束后恢复原锁文件。测试绑定 zuse 0.2.2 的 94c83755；后续主线观察到的差异属于文档和一个发行检查脚本，验收记录继续使用实际被测提交。[zmcpio 与消费者完整证据](https://github.com/LIghtJUNction/zmcpio/blob/61dfc3212ff3abd632eeed9b32718efbf54fd251/docs/validation-zcall-0.4.md)

agy 按用户许可执行独立静态审查，没有运行测试。它完成了主审查以及测试文件的定向补读；测试结论由上述实际运行回执支持。

## 4. 上游管理清单

19:55:51 的审计以固定聚合 76dd114c 为基准，核对了 43 个仓库和 44 个声明可发布的包版本，发现 22 个仓库的上游已有新提交、11 个快照版本在 crates.io 不存在；待发现的新仓库为 0，审计错误为 0。[完整机器记录](https://github.com/LIghtJUNction/project-z/blob/0d638519117e375410743e61013114a6187b7f96/docs/reports/management-20261120/upstream-audit.json)

| 尚未在 crates.io 找到的快照版本 | 所属仓库 |
| --- | --- |
| mechrevo-console-cli/core/gui 0.1.0 | mechrevo-drivers |
| ssmcp 0.10.14 | ssmcp |
| zcall-gui 0.1.1 | zcall-gui |
| zcalld、zcalld-plugin-api、zcalld-plugin-routing 0.2.5 | zcalld |
| zdot 0.2.0 | zdot |
| zmcl 0.1.1、zmcl-core 0.1.0 | zmcl |

这些记录用于区分源码快照与注册表发行状态。各包继续按自身用途、发布策略和已验证的依赖组合处理；本轮已经完成所选管理工具与 MCP 依赖源码的工作。

现有稳定组合包含 43 个仓库、62 个 Cargo 包。其上一轮 38 个 Rust 仓库的完整解析与实际组件验收记录保存在[既有交付报告](https://github.com/LIghtJUNction/project-z/blob/76dd114c11685d430dd55bb0d78b064a7349af73/docs/reports/ui-unification-20261120/project-z-iteration-2026-11-20.md)。

## 5. 下一批发行与传播

zmcpio 的新代码已经合入 main，CHANGELOG 保持 Unreleased；正式最新 Release 仍为 [v0.4.0](https://github.com/LIghtJUNction/zmcpio/releases/tag/v0.4.0)。其公开的 `zmcpio::zcall` 和 bridge 类型现在引用 zcall 0.4 的 crate，因此下一次正式发行应使用 0.5.0，再同步消费者的精确约束。

已核对发行流程仅在发行请求文件变化或手动调用时启动。本次没有修改该请求文件。正式 0.5.0 发行继续使用仓库现有的 Linux、Windows、macOS 验证及发布流程。[发行流程](https://github.com/LIghtJUNction/zmcpio/blob/bc89d7fa3b0249b3a9037748e2113b31615e8c89/.github/workflows/release.yml)

| 传播范围 | 已有证据与下一步 | 负责范围 |
| --- | --- | --- |
| zmcpio → zuse | 实际源码兼容及传输验证完成；0.5.0 可获取后更新 zuse 精确依赖和发行锁文件 | 库发行维护者、zuse 维护者 |
| zuse → ssmcp / zrc / ztype / oh-my-ztty | 使用新的确定来源组合，完成对应应用、运行连接与安装验收 | 各应用现有维护者，Project Z 协调者收齐结果 |
| zcall 0.4 / zharness 0.6 / zcalld | 统一精确约束、嵌套源码及实际调用入口，完成正在推进的消费批次 | 共享调用链与应用维护者 |
| 新版 zgpui 及界面消费者 | 收齐同一版本的依赖和嵌套指针，完成实际窗口验收 | 界面库与现有 GUI、终端、输入法维护者 |
| 下一份聚合快照 | 用新的分批更新入口组装，执行完整依赖解析和相应应用验收 | Project Z 协调者 |

## 6. 证据与结论复核

| 复核问题 | 结论与依据 |
| --- | --- |
| 是否解决当前管理问题？ | 已提供按仓库推进更新的可执行入口，完整待办继续可见。 |
| 是否清楚解释了行为？ | 选择范围决定更新的提交指针；所有消费者仍参加解析。 |
| 通过结果是否绑定来源？ | 96 项协调器测试绑定 c96e4cdb；MCP 与 zuse 验收绑定 ec43faa5 / 94c83755。 |
| 是否覆盖主要失败路径？ | 已覆盖错误选择、无变化选择、默认全部更新和未选消费者不兼容。 |
| 是否保留必要边界？ | 代码合并、注册表发行、应用接入和聚合验收分别记录，当前阶段均有明确来源。 |
