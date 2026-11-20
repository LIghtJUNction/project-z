# Project Z 维护进展

更新：2026-11-21 00:18（Asia/Taipei）。

## 主要结果

**源码依赖图已通过。** 43 个仓库、67 个包，38 个 Rust 仓库完成实际解析；`sync`、`check`、`resolve --all` 和影响范围检查全部成功。各组件提交、干净状态与共享源码固定点已核对，临时锁文件和 Cargo 配置均已还原。

验证源码树：`4c76d171ef7322680281bbd1bbbc18f85c394d36`。本次更新 22 个组件引用及 3 个生成文件，影响 24 个仓库。发布入口：[Project Z PR #6](https://github.com/LIghtJUNction/project-z/pull/6)。

初始 85 项 PR：已合并 54 项、已关闭 14 项、仓库已归档 9 项、具体阻塞 5 项、验收／集成中 3 项。每个 PR 只计一次，后续集成 PR 单独记录。[完整清单与证据](2026-11-20-pr-and-dependencies.json)保留全部条目。

## 本轮改动

- **共享依赖。** 合入 zgpui 字体位图边界修复和独立 raster 包，同步 ztty、zmcl、zcall-gui、ztype 的固定源码；新增的 raster 与 zcalld-installer 均为 `publish=false`，仍纳入完整依赖图检查。
- **补齐独立锁。** 全图解析发现 zterm 的已提交锁仍选中 zgpui 0.1.2，已由 [zterm #1](https://github.com/LIghtJUNction/zterm/pull/1) 修正，并经 [ztty #20](https://github.com/LIghtJUNction/ztty/pull/20) 传播。当前 zterm [`cd9abc5`](https://github.com/LIghtJUNction/zterm/commit/cd9abc560d28c2d8ad6ed2073e8d9a7c27810da1)、ztty [`66d39d0`](https://github.com/LIghtJUNction/ztty/commit/66d39d021d195d981c50ca88a7715a2b37552854)。ztty 保留新合入的 GPU 文本缓存优化；锁变更前后完整解析图相同。新 GPU 实验、旧 UI 验收和这次锁检查分别保留来源。
- **服务消费者。** zcalld [`1c14414`](https://github.com/LIghtJUNction/zcalld/commit/1c1441404ddc54416cf24b57d276958a8b98b811) 已接入新 GUI 固定点；当前 core、CLI、Linux 安装器/打包及 compat helper 检查通过。这些结果不替代 native P1 的独立验收。
- **积压与开发机。** 完成多组依赖适配和冲突修复，包括 sing-box、Magpie、LMM、LightFlow/Flux、Weyriva 与 MSG；各自的提交、检查结果和限制保留在 JSON。SSMCP 本地子模块与既有 gitlink 的错位已修复，未替换运行中的服务。

## 真实剩余

- [KernelSU #1](https://github.com/LIghtJUNction/KernelSU/pull/1)：包含大范围上游迁移及文档移动，缺少对应设备适配和真实设备验证。
- [MagicBox #4](https://github.com/LIghtJUNction/MagicBox/pull/4)：旧 `8d6723d` 已通过 Android 模拟器验收；当前正按要求重写极简 UI，PR 保持 draft，新候选的验收另记。
- [video-work-api #11](https://github.com/LIghtJUNction/video-work-api/pull/11)：torch/torchaudio 与固定 FunClip/CosyVoice 约束冲突，仍需模型和 CUDA 验证。
- [zcalld #1](https://github.com/LIghtJUNction/zcalld/pull/1)：原负责人仍在完成固定组合的 native P1；旧 ef439/be72 的 32 项记录不能作为当前聚合源码通过的依据。
- [codewhale-lmm-provider #3](https://github.com/TokenNotIncluded/codewhale-lmm-provider/pull/3)：按用户组隔离的后端接口、客户端注册及真实宿主验收条件尚未齐备。
- [hireferry #21](https://github.com/TokenNotIncluded/hireferry/pull/21)：当前 Android 返回桌面以及 WebView/服务组合验收仍在推进。
- [lmm-api-source #10](https://github.com/TokenNotIncluded/lmm-api-source/pull/10)：数据库升级门禁仍受其他连接或预备事务阻塞，具体来源未定位。
- [lmm-api-source #11](https://github.com/TokenNotIncluded/lmm-api-source/pull/11)：流式请求出现已预留但未结算；锁超时与失败的因果关系尚未确认。

SSMCP 聚合来源保持 `2126b7b7f09e`；原负责人后续合入的提交不自动进入本批已验收源码图。oh-my-ztty 继续使用已发布 ztty v0.5.2、SSMCP v0.10.20 的制品摘要。开发源码更新不代表新安装包已经发布或安装。

## 证据链接

- [完整维护 JSON](2026-11-20-pr-and-dependencies.json)：85 项清单、43 个固定源码、逐项门禁、失败修复记录和消费者验证。
- [ztty 锁传播报告](https://github.com/LIghtJUNction/ztty/blob/66d39d021d195d981c50ca88a7715a2b37552854/docs/reports/dependency-lock-propagation-20261120/README.md)与[GPU 实验报告](https://github.com/LIghtJUNction/ztty/blob/d9d4ce40b10dd427ce4b59c901c8b03e2fc0ed70/docs/benchmarks/text-run-scratch-20261120/report.zh-CN.md)：分别标明固定源码和覆盖范围。
- [MagicBox PR #4](https://github.com/LIghtJUNction/MagicBox/pull/4)：旧源码的模拟器结果保存在 JSON 的 `magicbox_prior_emulator_validation`，新 UI 继续单独验证。
