# Project Z 维护进展

更新：2026-11-21 01:32（Asia/Taipei）。

## 主要结果

**正在完成历史附件清理与内部依赖迁移。** 内部跨仓依赖使用 GitHub 默认分支最新源码；每次同步刷新锁文件和子模块引用，记录实际提交。Cargo 发布供外部使用。生成截图、压缩证据和编译产物移出 Git，必要构建输入与测试夹具按实际引用保留。

旧源码树的 43 仓、67 包、38 个 Rust 仓库解析已经通过，结果仅适用于原记录的提交。[Project Z PR #6](https://github.com/LIghtJUNction/project-z/pull/6) 已合并。新规则另建后续 PR，并将独立的 LMM CLI 纳入第 44 个仓库；历史改写后的完整 Git 依赖图仍需重新检查。

初始 85 项 PR：已合并 55 项、已关闭 14 项、仓库已归档 9 项、具体阻塞 5 项、验收／集成中 2 项。每个 PR 只计一次，后续集成 PR 单独记录。[完整清单与证据](2026-11-20-pr-and-dependencies.json)保留全部条目。

## 本轮改动

- **MagicBox。** 极简界面及共享运行时已合并到主分支。两种构建各 96 项 JVM 测试、APK 完整性、5 项 Android 模拟器流程和真实两跳代理检查通过；已查看明暗界面的实际截图。新增忽略规则防止验收附件进入 Git，尚未进行 rooted 实机 TUN/eBPF 验证。
- **Git 依赖规则。** 跨仓依赖改为规范的 GitHub `.git` 地址，跟随默认分支；保留原版本约束形式，同次刷新实际包版本、Cargo.lock 和内部子模块。同仓 workspace/path 关系保留，历史报告中的源码副本保持原样。
- **维护工具。** 默认分支同步、实际 locked 来源检查、内部 gitlink 更新和第 44 仓目录已实现。开发机通过 80 项测试，包括真实本地 Git/Cargo 夹具，零跳过；这项工具测试不替代各应用和最终完整依赖图的验收。
- **此前依赖修复。** zgpui 字体位图边界、独立 raster 包、zterm 旧锁以及各消费者的集成已完成。逐项报告保留原提交与范围，新 Git 来源需要重新解析和验证。
- **积压与开发机。** 完成多组依赖适配和冲突修复，包括 sing-box、Magpie、LMM、LightFlow/Flux、Weyriva 与 MSG；各自的提交、检查结果和限制保留在 JSON。SSMCP 本地子模块与既有 gitlink 的错位已修复，未替换运行中的服务。

- **开发机空间。** Cargo 默认共用 `/var/tmp/project-z-cargo-target`，多步验证批次用外层锁串行保护。已核实 `/home` 可用空间从 33.5 GB 增至 136.2 GB；闲置缓存清理仍在继续。活动构建目录和必要源码均保留。

## 已完成的历史附件清理

下列默认分支已推送并读回核对。生成附件先完整备份到 Google 云盘，再更新受控分支和标签；源码、必要构建输入和真实测试夹具按引用保留。

| 仓库 | 清理后的默认分支提交 |
|---|---|
| LIghtJUNction/ztty | [`d8845547b4`](https://github.com/LIghtJUNction/ztty/commit/d8845547b4da8fbc1fb6437c2765cf11981e598c) |
| LIghtJUNction/zmcl | [`c6f83236bd`](https://github.com/LIghtJUNction/zmcl/commit/c6f83236bd7fcaa89aa3404d34890ac86ced1eaa) |
| LIghtJUNction/ztype | [`bd1b0b3b28`](https://github.com/LIghtJUNction/ztype/commit/bd1b0b3b28401b4f52b1cec148e5477d84152529) |
| LIghtJUNction/zcalld | [`9baad8ccab`](https://github.com/LIghtJUNction/zcalld/commit/9baad8ccabce51e8625883162d70a7b78823330b) |
| LIghtJUNction/magpie-context-folding | [`cf571b9733`](https://github.com/LIghtJUNction/magpie-context-folding/commit/cf571b9733f7ac68d5233db6d37b828d8350e893) |
| LIghtJUNction/sing-box | [`4e81e25789`](https://github.com/LIghtJUNction/sing-box/commit/4e81e2578948203fff5f017f8c00879a904ae90f) |
| TokenNotIncluded/hireferry | [`dd3c20e400`](https://github.com/TokenNotIncluded/hireferry/commit/dd3c20e40093892cf14f50fe09cd8c6c93350525) |
| TokenNotIncluded/msg | [`35952527e5`](https://github.com/TokenNotIncluded/msg/commit/35952527e58f5b2c5b540944bdcc7e92dfb7c5dd) |
| LIghtJUNction/zcall-gui | [`2cc7b2bdb4`](https://github.com/LIghtJUNction/zcall-gui/commit/2cc7b2bdb479b29e5e687d2a9bc5f3c8db1dd104) |

SSMCP 仍在处理旧发布清单与标签提交绑定的兼容问题，已确认运行时 `brand-mark.png` 必须保留。GitHub 管理的 PR 引用和服务端缓存不属于可写范围；这里的完成状态指已核实的受控引用，不代表服务端所有旧对象已物理删除。

新规则与后续源码同步：[当前聚合 PR](https://github.com/LIghtJUNction/project-z/pull/7)。

## 真实剩余

- [KernelSU #1](https://github.com/LIghtJUNction/KernelSU/pull/1)：包含大范围上游迁移及文档移动，缺少对应设备适配和真实设备验证。
- [video-work-api #11](https://github.com/LIghtJUNction/video-work-api/pull/11)：torch/torchaudio 与固定 FunClip/CosyVoice 约束冲突，仍需模型和 CUDA 验证。
- [zcalld #1](https://github.com/LIghtJUNction/zcalld/pull/1)：原负责人仍在完成固定组合的 native P1；旧 ef439/be72 的 32 项记录不能作为当前聚合源码通过的依据。
- [codewhale-lmm-provider #3](https://github.com/TokenNotIncluded/codewhale-lmm-provider/pull/3)：按用户组隔离的后端接口、客户端注册及真实宿主验收条件尚未齐备。
- [hireferry #21](https://github.com/TokenNotIncluded/hireferry/pull/21)：当前 Android 返回桌面以及 WebView/服务组合验收仍在推进。
- [lmm-api-source #10](https://github.com/TokenNotIncluded/lmm-api-source/pull/10)：后继源码已完成原升级回归的定向修复和复验；最终组合验证及真实生产升级材料尚未闭合。
- [lmm-api-source #11](https://github.com/TokenNotIncluded/lmm-api-source/pull/11)：流式请求出现已预留但未结算；锁超时与失败的因果关系尚未确认。

旧图中的 SSMCP 来源为 `2126b7b7f09e`，仅保留为历史证据；后续将跟随清理后的最新默认分支并重新验收。已发布安装包的来源与摘要单独核对。开发源码更新不代表新安装包已经发布或安装。

## 证据链接

- [完整维护 JSON](2026-11-20-pr-and-dependencies.json)：85 项清单、旧 43 仓验收、新 44 仓迁移进度、历史清理与逐项证据。
- [ztty 锁传播报告](https://github.com/LIghtJUNction/ztty/blob/66d39d021d195d981c50ca88a7715a2b37552854/docs/reports/dependency-lock-propagation-20261120/README.md)与[GPU 实验报告](https://github.com/LIghtJUNction/ztty/blob/d9d4ce40b10dd427ce4b59c901c8b03e2fc0ed70/docs/benchmarks/text-run-scratch-20261120/report.zh-CN.md)：分别标明固定源码和覆盖范围。
- [MagicBox PR #4](https://github.com/LIghtJUNction/MagicBox/pull/4)：已合并，最新实现的构建与模拟器记录分别见 `magicbox_current_build` 和 `magicbox_current_emulator`。
