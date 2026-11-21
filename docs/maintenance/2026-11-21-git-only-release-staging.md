# Project Z：Git-only 发行脚本修复与 SSMCP 源码状态

知识截点：**2026-11-21 09:03:55.489 UTC**（台北时间 17:03:55.489）。本文是 [d7dbbf5d 的 07:30:11 固定报告](https://github.com/LIghtJUNction/project-z/blob/d7dbbf5dc0141d0184c960f57d719694228570b2/docs/maintenance/2026-11-21-git-only-policy-and-consumers.md)之后的独立增量，不修改或回填旧报告。截点以后收到的消息不纳入本版。

## 当前结果

zplugin、zcall、zmcpio、zharness 的 Git-only 审计／发行脚本修复均已推送到各自草稿 PR。开发源码继续使用 Git，外发所需的 registry 版本与归档在独立目录中处理；本批实际完成的是源码修复、纯 Python／临时 Git 夹具及独立静态审阅，还没有执行这些候选的真实 Cargo 打包、registry 请求、跨平台 CI 或正式发行。

SSMCP PR165 已合并为主线 S4b4cbff3，但新一轮完整门禁（Gate15，计划 35 阶段）尚未绑定或运行。原作者又发现一个 EOF 故障注入夹具的静态问题，后继源码和新的最终身份待定。旧候选的 Gate、runtime 和 UI 结果不能转挂到 S。

| 组件 | 已发布的草稿源码 | 实际测试口径 | 收口边界 |
| --- | --- | --- | --- |
| zplugin | [PR2](https://github.com/LIghtJUNction/zplugin/pull/2)，[e3e25e33](https://github.com/LIghtJUNction/zplugin/commit/e3e25e33d89a54e98c7a2605bb84cf016992b5a0)，tree a8775f63 | 首候选 31 个方法通过；R2 另做 1 个定点 RED→GREEN。 | 没有在 R2 上重跑完整 32 项；未合并、未发行。 |
| zcall | [PR2](https://github.com/LIghtJUNction/zcall/pull/2)，[17717543](https://github.com/LIghtJUNction/zcall/commit/177175439b053df3931425a9532eac349340eee5)，tree 19c12e12 | R2 的 46 个方法通过，0 失败、0 错误、0 跳过。 | 冷缓存顺序用夹具验证；未实际运行 Cargo fetch 或 registry 发布。 |
| zmcpio | [PR4](https://github.com/LIghtJUNction/zmcpio/pull/4)，[20c08e93](https://github.com/LIghtJUNction/zmcpio/commit/20c08e93055c0d977824b9f5e102f490a9267c1d)，tree d0646243 | R2 的 21 个方法通过，包含原 19 项和 2 项 CRLF 回归，0 跳过。 | CRLF 夹具不能代替真实 Windows CI；未执行 Cargo 或 registry。 |
| zharness | [PR10](https://github.com/LIghtJUNction/zharness/pull/10)，[9d36a299](https://github.com/LIghtJUNction/zharness/commit/9d36a29976c185e8cdad029e6169057a10850ad4)，tree ab7ce418 | 审计 17 项属于 491b8525；R3 发行脚本的 39 项属于 ab7ce418，分开记录。 | 39＝原 29＋新 10，不与此前各轮 39 相加；未合并、未发行。 |

上述“已发布”指分支源码和草稿 PR。截止时四仓默认分支仍分别为 zplugin 592a1be6、zcall 199678d0、zmcpio 04bb6cd0、zharness fb2948f7。草稿没有移动这些已交接的默认分支，也没有更新正式标签或推送 registry 包。[固定来源记录](evidence/git-only-release-staging-20261121/ssmcp-gate15-unrun-fixture-followup.json)

## 为什么需要这一批修复

开发时，Git URL 决定取哪份源码，Cargo.lock 记录已解析的确切提交和包版本。去掉开发 manifest 的 version 条件后，旧审计或发行脚本若仍从该字段取 registry 版本，就会拒绝正确的开发声明，或错误地把外发投影写回开发分支。

本批把两种用途分开：开发审计继续核对规范 Git 来源和已提交锁文件；外发 stage 从唯一匹配的锁条目取得 exact 版本，生成 registry 副本，并保留版本、来源、yank、checksum、归档身份及发布并发检查。包自身版本规划与开发主线保持原有职责。这些脚本逻辑已经用明确的夹具验证，真实发行仍须运行其实际门禁。

## 各仓修复与证据

### zplugin：31 项首候选结果与 R2 定点回归分开

首候选 tree `bcf24a6531ba424f71e25c7b0092e0531dfdcc32` 的 31 个 Python 方法全部通过。R2 修复的是 **SemVer build metadata 中含连字符的版本解析**，例如 `1.2.3+build-01`；这不是 Cargo metadata 回归。同一用例对旧实现失败、对 tree a8775f63 的修复通过。工作流 YAML 另经解析核对，保留原有语义与明确新增的产物路径。

独立静态审阅无实质阻断。发布读回确认 7 个文件全文与候选一致，基线 152 个叶对象到候选 155 个，其中 148 个保持原物。没有把两个不同源码阶段的结果写成“R2 完整 32 项通过”。[发布与测试范围原件](evidence/git-only-release-staging-20261121/zplugin-publication-readback.json)

### zcall：锁条目绑定与隔离发行目录

外发版本从已提交锁文件中的唯一 Git 包身份取得，并核对**工作副本中的该 Git 锁条目与已提交锁条目一致**。这一检查不能描述为整段 Cargo.toml 声明与提交内容完全相同。开发源码保留 Git-only 声明和原版本规划；registry 投影、打包与发布进入独立 stage，开发主线记录与标签继续指向开发源码。

两个正式工作流在离线准备之前增加 locked fetch，避免空缓存直接进入离线解析。两个冷缓存顺序夹具在 R1 上实际报错，在 R2 上通过。R2 的 46 项包含原 32 项、12 项 Git-only 回归和 2 项冷缓存顺序回归，0 失败、0 错误、0 跳过。独立静态审阅核对了隔离目录、来源匹配和调用顺序，原门禁及既有 allow-dirty 边界没有放宽。

发布读回确认 6 个文件与受测内容相同，另 68 个叶对象保持。该结果验证了 Python 逻辑和受控夹具，不能宣布真实 Cargo fetch、打包或 registry 发布已经成功。[发布回执](evidence/git-only-release-staging-20261121/zcall-publication-readback.json)

### zmcpio：开发与发行审计分开，合法 CRLF 不再被误拒

开发审计关联 manifest、已提交锁文件和实际 metadata 所声明的 Git 包身份，保留三包闭包与功能约束；registry 审计在独立发行副本中显式启用。stage 从唯一匹配的 Git 锁条目取得 exact 版本，并保留来源、版本、yank、checksum 与归档检查。主线更新只处理包自身版本，不把 registry 副本写回 main。

首候选 19 项通过后，静态审阅指出 Windows 换行风险：直接比较 Git blob 的 LF 字节与 checkout 的 CRLF 字节，会拒绝合法源码。R2 改用 Git 对指定路径的内容规范化比较；正常 CRLF checkout 可以通过，真实追加内容仍被拒绝。新夹具还覆盖带空格路径和 stage 不改写原源。

有效 RED 的两个方法中，旧 audit 出现 1 个错误，另一个 stage／snapshot 检查通过。修复后原 19 项加 2 项，共 21 个方法通过，0 跳过。此前两个未建立正确前提的夹具尝试保留为准备失败，没有冒充产品 RED。

R2 相对 R1 只修改 audit 和测试。独立静态审阅无实质阻断；20c08e93 的发布读回确认 7 个文件原文与受测内容相同、tree 为 d0646243，其他 73 个叶对象不变。没有执行真实 Windows runner、Cargo、registry 网络或正式发布。[发布与验证原件](evidence/git-only-release-staging-20261121/zmcpio-publication-readback.json)

### zharness：审计 17 项与最终发行脚本 39 项各自绑定

491b8525 已发布的审计修复只修改 audit 和其测试，另外 127 个叶对象保持。一个有效 RED 先失败，GREEN 的 17 个方法通过。该审计继续检查 Git 来源、锁定提交与版本、zplugin 与 zplugin-macros 的共享工作区身份，以及既有依赖闭包和外部 checksum 边界。这 17 项没有在后继发行脚本批次中重新运行。[审计发布原件](evidence/git-only-release-staging-20261121/zharness-audit-publication-readback.json)

后继 9d36a299 以 491b8525 为单父提交，新增隔离 registry stage，并保留开发版本规划、归档恢复、来源／checksum 检查和 main／tag 并发保护。root 已完整读回 7 个文件，候选共 131 个叶对象，124 个与 491 基线原物相同；PR10 继续 open、draft、unmerged，main 仍是 fb2948f7。[后继发布原件](evidence/git-only-release-staging-20261121/zharness-release-publication-readback.json)

R2 的 d4c 原件保持。它的 runner 记录了已跟踪文件，但两个新增模块没有纳入同一次运行的完整前后哈希集合；不能靠另一次写入记录补称完整来源绑定。R3 在同一轮验证前暂存并散列全部 7 个文件，结束后再次核对。源码只改一行测试夹具：`Path(directory.name).resolve()`，使临时根路径与生产目录守卫采用同一规范路径；生产代码、helper、全部 39 个测试方法及断言保持不变。[原始一行差异](evidence/git-only-release-staging-20261121/zharness-r2-to-r3.patch)

最终 R3 的 39 个方法在 08:56:38—08:56:42 UTC 实际通过，包含原 29 项和新增 10 项，0 失败、0 错误、0 跳过。7 份源码前后相同；1,400 个子进程事件全部为本地 Git，临时夹具目录已经清空。Cargo、metadata、registry API 由夹具替代，没有实际调用。独立只读审阅无实质阻断；这不是实际 macOS／Windows 或正式发行证明。各轮 39 不相加，也不与旧审计 17 项合成一个新验收总数。[原始 stderr](evidence/git-only-release-staging-20261121/zharness-r3-stderr.log) · [独立审阅](evidence/git-only-release-staging-20261121/zharness-r3-independent-review.json)

R3 handoff 原件记录的是封存时尚未推送的状态；其后 09:02:37 的实际发布读回确定了 9d36a299 与 PR10 状态。两个时间点各自保留，不修改早先记录。[封存原件](evidence/git-only-release-staging-20261121/zharness-r3-handoff.json)

## SSMCP：S 已进入主线，新的最终验收尚未开始

[PR165](https://github.com/LIghtJUNction/ssmcp/pull/165) 于 08:51:57 UTC 合并。远端 main 为 [S4b4cbff3](https://github.com/LIghtJUNction/ssmcp/commit/4b4cbff311e930a8c8280ff1989a7f036ce7a892)，tree 为 `16c341e1e5f828be0a4b4ee1ef0fe9f2945afe26`，双父为 3f678a7f 与 5623e52a。root 先前在 08:51:28 读到的本地干净 5623e52a 与 S 同 tree，但没有在本地 S checkout 上重新验证。相同内容树不能替代 S 的实际执行回执。[源码发布原件](evidence/git-only-release-staging-20261121/ssmcp-final-source-publication.json)

截至本版，Gate15 **尚未绑定，也尚未运行**。原作者静态发现：测试中的活 Python 子进程只关闭 stdout 时，Linux guardian 可能仍持有该描述符，因而测试可能先触发原 10 秒上限，而不是收到预期 EOF。尚无本次运行复现。原作者计划改用已 flush 的非法 JSON 注入，保持 On、unknown、replay_safe=false、cleanup 断言和原 10 秒边界，并澄清两处 notes。后继源码／合并和新的最终身份仍待确定。[固定截点原件](evidence/git-only-release-staging-20261121/ssmcp-gate15-unrun-fixture-followup.json)

因此，不能写新一轮 35 阶段门禁、runtime、UI 或 P1 已通过，也不再把早先“生产问题仍在 E10 修复”的观察当成当前结论。W 的历史 35 阶段和 runtime18 通过、W UI 的账户失败与其后未复现旧失败的定点诊断仍归原源码，不转挂到 S。原 SSMCP 负责人保留最终验收窗口；本组没有 Cargo、构建、metadata、产品、共享 target 写入或排队任务。

## 保留的历史与下一步

初始 85 项仍按原清单去重：56 已合并、14 已关闭、9 仓库归档、5 具体阻塞、1 验收／集成中。最后一项是 zcalld PR1；本批新草稿另列，不改旧总数。

zcalld bd7 的 release 构建、帮助检查与原 8 个 curl 场景保持历史窄验证结论。旧 0af8 的 182 项 Rust（内含 7 个 listener）、2 次 Clippy、8 个 curl 仍属于旧源码；PR1 和最终 P1 尚未收口。ztype v2 保持已封存、未启动、未排队的范围。最终 44 仓新图没有执行，历史图与局部脚本回归不能替代它。

接下来先由原负责人完成 SSMCP 夹具后继并重新固定源码，再安排其实际 Gate、runtime、UI 与 P1。四仓草稿随后按各自入口完成必要的真实 Cargo、registry、归档和平台门禁；任何正式发布结论都应绑定实际候选与回执。组件来源和验收到位后，再更新最终 44 仓映射并执行 sync／check／resolve。

**范围说明：**本批组件确实修改了源码并执行了上文记录的 Python／本地 Git 夹具；只是这次报告准备和原件读回没有新增产品或 Cargo 执行。五份发布回执、两份 SSMCP 公共原件及选定的 zharness 原件均按原字节纳入，哈希见配套机器清单。原 d7db 报告与 Google Doc v9 保持，原始 Drive Markdown、JSON 仍为 0d73；同一 Doc 的 v10 阅读副本将在本报告实际提交后更新。
