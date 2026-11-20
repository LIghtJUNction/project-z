# Project Z 维护进展

更新：2026-11-21 02:45（Asia/Taipei）。

## 当前结果

**内部 Git 源迁移已完成本页列出的 16 个仓库本轮发布；受控 Git 历史中的生成附件清理已完成 13 个已审计仓库。** 开发机首批 129 个闲置 Cargo 目录和另外 3 个 LMM 缓存已完成处理。当前继续推进其余消费者、上游新提交的定向传播、最新组合的原生验收、完整 44 仓依赖图及新版本发布。

初始 85 项 PR 仍按原清单去重计数：**已合并 55、已关闭 14、仓库已归档 9、具体阻塞 5、验收／集成中 2**。新建的依赖迁移 PR 单独记录。[完整清单与逐项证据](2026-11-20-pr-and-dependencies.json)保留全部 85 项条目和历史验证范围。

[Project Z PR #6](https://github.com/LIghtJUNction/project-z/pull/6) 已合并，其 43 仓、67 包、38 个 Rust 仓库的结果适用于原提交。[后续 PR #7](https://github.com/LIghtJUNction/project-z/pull/7) 引入新的 Git 来源规则和第 44 仓独立 LMM CLI，完整新图仍待最终组件提交就位后验收。

## Git 依赖迁移

规则已写入维护工具和文档：内部跨仓依赖使用规范 GitHub `.git` 地址并跟随默认分支；同步时刷新真实 Cargo.lock 和内部 gitlink，保留供外部 crates.io 用户使用的版本信息。同仓 workspace/path 关系以及历史报告中的源码副本按各自用途保留。

| 仓库 | 已发布提交／PR | 当前结果 |
| --- | --- | --- |
| zcall | [`564ede15db`](https://github.com/LIghtJUNction/zcall/pull/1) | 已合并，源码树与门禁记录一致 |
| zplugin | [`cf02c1d9db`](https://github.com/LIghtJUNction/zplugin/pull/1) | 已合并，源码树与门禁记录一致 |
| zclick | [`b90a118e8a`](https://github.com/LIghtJUNction/zclick/pull/1) | 已合并，源码树与门禁记录一致 |
| zinput | [`fe1cbaec74`](https://github.com/LIghtJUNction/zinput/pull/1) | 已合并，源码树与门禁记录一致 |
| zharness | [`cb63a9a0aa`](https://github.com/LIghtJUNction/zharness/pull/9) | 已合并，源码树与门禁记录一致 |
| zmcpio | [`84fc4978a2`](https://github.com/LIghtJUNction/zmcpio/pull/3) | 已合并，源码树与门禁记录一致 |
| zterm | [`53f7d1dd01`](https://github.com/LIghtJUNction/zterm/pull/2) | 已合并，源码树与门禁记录一致 |
| zuse | [`0fc2d9cb61`](https://github.com/LIghtJUNction/zuse/pull/1) | 已合并，源码树与门禁记录一致 |
| zcall-gui | [`9a7eab6fa9`](https://github.com/LIghtJUNction/zcall-gui/pull/2) | 已发布，完整本地门禁通过 |
| zmcl | [`a3858a0f73`](https://github.com/LIghtJUNction/zmcl/commit/a3858a0f731ba08cae45bc1672f161218ca4a190) | 已发布，完整本地门禁通过 |
| zcalld | [`4eaef52ce0`](https://github.com/LIghtJUNction/zcalld/pull/3) | 已发布，完整本地门禁通过 |
| zrc | [`2f10ea8dcf`](https://github.com/LIghtJUNction/zrc/pull/1) | 已发布，各自适用门禁通过 |
| zdot | [`a3c6a75b1e`](https://github.com/LIghtJUNction/zdot/pull/1) | 已发布，各自适用门禁通过 |
| lmm | [`7ba45df943`](https://github.com/TokenNotIncluded/lmm/pull/4) | 已发布，各自适用门禁通过 |
| OniMods | [`9d2ffb4f74`](https://github.com/LIghtJUNction/OniMods/commit/9d2ffb4f749919f513313d603daeed5a6767195b) | 已发布，各自适用门禁通过 |
| mechrevo-drivers | [`eb2959aac4`](https://github.com/LIghtJUNction/mechrevo-drivers/pull/10) | 已合并，原正式四项门禁通过 |

8 个核心仓库各自的 fmt、测试、严格 Clippy 及适用的 no_std/Wasm 检查已通过，固定提交、源码树、命令和日志摘要在 JSON 的 `core_git_source_migrations` 中。不同 feature 配置的重复运行不计作新增独立测试。

三个应用仓库同时修正了共享 Cargo 构建目录的使用方式。安装、打包和验收脚本通过 Cargo metadata 找到真实产物路径；`zcalld` 保留并发更新的 `f32a25bb` 业务修复，完整官方门禁、私有原生包和安装器夹具通过。其监听功能仍由 [PR #1](https://github.com/LIghtJUNction/zcalld/pull/1) 单独集成和验收。

`ztty` 原候选的正式 Wayland 本地门禁已通过；补充命令误用 `--all-targets` 的问题已定位。续验在编译前又正确捕获 `zgraphics` 默认分支推进到 `aa0ed19f`：此次实质修改涉及 query-only 状态和 host erase，正在先同步 `zterm`、再验证 `ztty`。旧门禁保留其原源码边界。`ztype` 的 release Rust、Clippy、CLI、实际私有目录安装、Xvfb 输入已通过；私有 Wayland 测试所需的兼容库已按固定源码和补丁重建通过，系统库保持原样，最后的图形验收继续执行。原失败记录保留。

`zrc`、`zdot`、`LMM`、`Oni` 和 `mechrevo-drivers` 也已发布；API 的三个 Git 源与最新 LMM gitlink 继续验收。聚合工具最初通过 80 项测试，规范 Git URL 修正另通过 21 项定向真实 Git/Cargo 测试，均零跳过；它们不替代各应用和新 44 仓完整图的验收。最终图将显式登记已确认活跃的独立 fuzz／插件测试工作区，并保留比较基准的有意旧版本来源。

## 历史附件清理

以下提交是已核实的清理基线，后续业务或依赖更新可以继续推进分支。生成附件先备份并校验，再以精确引用和旧 SHA 租约更新受控分支及标签。必要的运行时品牌图、Gradle wrapper、嵌入式 BPF／驱动对象和实际测试夹具均按引用保留。

| 仓库 | 已核实清理基线 |
| --- | --- |
| LIghtJUNction/ztty | [`d8845547b4`](https://github.com/LIghtJUNction/ztty/commit/d8845547b4da8fbc1fb6437c2765cf11981e598c) |
| LIghtJUNction/zmcl | [`c6f83236bd`](https://github.com/LIghtJUNction/zmcl/commit/c6f83236bd7fcaa89aa3404d34890ac86ced1eaa) |
| LIghtJUNction/ztype | [`bd1b0b3b28`](https://github.com/LIghtJUNction/ztype/commit/bd1b0b3b28401b4f52b1cec148e5477d84152529) |
| LIghtJUNction/zcalld | [`9baad8ccab`](https://github.com/LIghtJUNction/zcalld/commit/9baad8ccabce51e8625883162d70a7b78823330b) |
| LIghtJUNction/magpie-context-folding | [`cf571b9733`](https://github.com/LIghtJUNction/magpie-context-folding/commit/cf571b9733f7ac68d5233db6d37b828d8350e893) |
| LIghtJUNction/sing-box | [`4e81e25789`](https://github.com/LIghtJUNction/sing-box/commit/4e81e2578948203fff5f017f8c00879a904ae90f) |
| TokenNotIncluded/hireferry | [`dd3c20e400`](https://github.com/TokenNotIncluded/hireferry/commit/dd3c20e40093892cf14f50fe09cd8c6c93350525) |
| TokenNotIncluded/msg | [`35952527e5`](https://github.com/TokenNotIncluded/msg/commit/35952527e58f5b2c5b540944bdcc7e92dfb7c5dd) |
| LIghtJUNction/zcall-gui | [`2cc7b2bdb4`](https://github.com/LIghtJUNction/zcall-gui/commit/2cc7b2bdb479b29e5e687d2a9bc5f3c8db1dd104) |
| LIghtJUNction/mechrevo-drivers | [`175b33cfbe`](https://github.com/LIghtJUNction/mechrevo-drivers/commit/175b33cfbe996e1a2044d98ba5fd16126c15de63) |
| LIghtJUNction/video-work-api | [`b89ab69263`](https://github.com/LIghtJUNction/video-work-api/commit/b89ab69263a7f27791b16ddb5372c45edd6fc0f9) |
| TokenNotIncluded/lmm-api-source | [`56b5123684`](https://github.com/TokenNotIncluded/lmm-api-source/commit/56b512368440a6bddbe45daafd4fa787cf744e8d) |
| LIghtJUNction/ssmcp | [`ccb91955c2`](https://github.com/LIghtJUNction/ssmcp/commit/ccb91955c25969f4779588d4cebb09b72c00f829)（两轮清理及文档归档完成） |

SSMCP 两轮共移除 **152 个生成附件路径**。第二轮核对 1,150 个历史源码树的保留条目，原子更新 112 个分支和 29 个标签；116 份原始媒体内容已归档并下载校验。5 个旧公开版本的发布清单保持原始构建身份，新的部署辅助逻辑只接受经证明的固定源码映射。详见[完整清理报告](https://github.com/LIghtJUNction/ssmcp/blob/ccb91955c25969f4779588d4cebb09b72c00f829/docs/reports/generated-history-cleanup-20261121.json)及[媒体归档](https://drive.google.com/file/d/1Rr9t9SpoMdwQJuHbW3eYRbgtg-krhUkF/view)。

完成范围是已核对的受控 Git 引用。GitHub 管理的 PR 引用、缓存和服务端物理垃圾回收不属于本次可写及可验证范围；旧 tag 自带的旧打包脚本也不会自动获得新辅助逻辑。

## 开发机与磁盘

Cargo 默认共用 `/var/tmp/project-z-cargo-target`，多步构建通过同一外层锁保护。首批 129 个闲置目标目录处理完成后，`/home` 的可用空间实测从 **33.50 GB 增至 289.69 GB**。续跑回执为 128 个已删除、1 个在先前尝试中已删除。

另外 3 个 LMM 缓存也已删除；这段操作前后可用空间实测 **289.19 GB → 291.38 GB**，净变化约 **2.19 GB**。目录 `du` 合计约 8.55 GB，受共享块和并发活动影响，不能把该合计当作实测释放空间。

WGT 的 4 个精确 Cargo 缓存候选已审计；第一次删除尝试等待共享锁 60 秒后记为延后，实际删除数为零。后续取得锁时会重新核对进程、挂载及 inode。模型、权重、源码和保留实验继续保留。SSMCP 当前源码、发布证明、活动构建以及整个共享 Cargo 目录仍在保护范围内。

## 产品与发布

**MagicBox** 的极简界面和文档已随 [PR #4](https://github.com/LIghtJUNction/MagicBox/pull/4) 合并。两个构建各 96 项 JVM 检查、APK 完整性、5 项 Android 模拟器流程和真实两跳代理验收通过；明暗界面已实际查看。rooted 实机 TUN/eBPF 验证仍未执行。

**SSMCP 新版本**正在最新源码组合上构建。当前候选的 277 个实际包源码（11 个 Git checkout、264 个 registry 来源）审计和 100 项 Python 检查已通过；最终 Rust、最新 `zcalld` 监听组合的 32/P1 与正式发布仍待完成。历史版本的通过记录不计作当前候选通过。

追加的 **Docker context 式本地／远程统一化** 已纳入后续工作。现有本地和远程已经共享 broker、wire 和原生 runtime；正在核对命名连接配置、统一目标选择、命令优先级和按目标隔离的凭据存储。参考 [Docker contexts](https://docs.docker.com/engine/manage-resources/contexts/) 与 [context use](https://docs.docker.com/reference/cli/docker/context/use/)。此项尚未实现或发布。

## 仍需闭合的初始 PR

| 项目 | 当前剩余 |
| --- | --- |
| [KernelSU #1](https://github.com/LIghtJUNction/KernelSU/pull/1) | 大范围上游迁移、设备适配与真实设备验证。 |
| [video-work-api #11](https://github.com/LIghtJUNction/video-work-api/pull/11) | torch/torchaudio 与固定 FunClip/CosyVoice 约束及模型、CUDA 验证。 |
| [zcalld #1](https://github.com/LIghtJUNction/zcalld/pull/1) | 基于最新 Git 源的 5 文件监听适配、本地门禁和唯一一次最终 native 32/P1。 |
| [codewhale-lmm-provider #3](https://github.com/TokenNotIncluded/codewhale-lmm-provider/pull/3) | 按用户组隔离的后端接口、客户端注册及真实宿主验收材料。 |
| [hireferry #21](https://github.com/TokenNotIncluded/hireferry/pull/21) | 私有 Android AVD 上的返回桌面与 WebView／服务组合验收。 |
| [lmm-api-source #10](https://github.com/TokenNotIncluded/lmm-api-source/pull/10) | 原定向回归已修复，最终组合验证及真实生产升级材料仍待闭合。 |
| [lmm-api-source #11](https://github.com/TokenNotIncluded/lmm-api-source/pull/11) | 预留未结算与锁超时之间的实际因果关系。 |

维护报告与归档位置：[GitHub PR #7](https://github.com/LIghtJUNction/project-z/pull/7)、[Google 云盘目录](https://drive.google.com/drive/folders/1vjkFko8onQm9WiScrw7QBopK9vNGTLx0)。完整 JSON 保留每个结果对应的源码、命令、日志和验证边界。
