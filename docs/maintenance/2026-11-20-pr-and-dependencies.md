# Project Z 维护进展

更新：2026-11-21 03:27（Asia/Taipei）。

## 当前结果

**内部 Git 源迁移已完成本页列出的 18 个仓库本轮发布；受控 Git 历史中的生成附件清理已完成 14 个完整核实的仓库。** oh-my-ztty 的 23 个引用、74 个原提交和 14 份历史图片也已完成独立复核。开发机首批 129 个闲置 Cargo 目录、另外 3 个 LMM 缓存和 4 个 WGT 缓存均已处理完成。当前继续推进其余消费者、上游新提交的定向传播、最新组合的原生验收、完整 44 仓依赖图及新版本发布。

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
| zterm | [`1a761334f0`](https://github.com/LIghtJUNction/zterm/commit/1a761334f0b9cf26da700426a5b82778f0d48c3d) | 后续已同步 zgraphics aa0，193 项独立 Rust 检查通过，1 项原有忽略 |
| zuse | [`0fc2d9cb61`](https://github.com/LIghtJUNction/zuse/pull/1) | 已合并，源码树与门禁记录一致 |
| zcall-gui | [`9a7eab6fa9`](https://github.com/LIghtJUNction/zcall-gui/pull/2) | 已发布，完整本地门禁通过 |
| zmcl | [`a3858a0f73`](https://github.com/LIghtJUNction/zmcl/commit/a3858a0f731ba08cae45bc1672f161218ca4a190) | 已发布，完整本地门禁通过 |
| zcalld | [`4eaef52ce0`](https://github.com/LIghtJUNction/zcalld/pull/3) | 已发布，完整本地门禁通过 |
| zrc | [`2f10ea8dcf`](https://github.com/LIghtJUNction/zrc/pull/1) | 已发布，各自适用门禁通过 |
| zdot | [`a3c6a75b1e`](https://github.com/LIghtJUNction/zdot/pull/1) | 已发布，各自适用门禁通过 |
| lmm | [`7ba45df943`](https://github.com/TokenNotIncluded/lmm/pull/4) | 已发布，各自适用门禁通过 |
| OniMods | [`9d2ffb4f74`](https://github.com/LIghtJUNction/OniMods/commit/9d2ffb4f749919f513313d603daeed5a6767195b) | 已发布，各自适用门禁通过 |
| mechrevo-drivers | [`eb2959aac4`](https://github.com/LIghtJUNction/mechrevo-drivers/pull/10) | 已合并，原正式四项门禁通过 |
| ztype | [`76c43579b9`](https://github.com/LIghtJUNction/ztype/pull/2) | 已合并，最后 28 项私有 Wayland 检查通过 |
| ztty | [`be29c6763d`](https://github.com/LIghtJUNction/ztty/commit/be29c6763d3f63832f77c21746d7d62aa70e7d62) | 原维护者发布；530 项 Rust 和完整适用原生门禁通过 |

8 个核心仓库各自的 fmt、测试、严格 Clippy 及适用的 no_std/Wasm 检查已通过，固定提交、源码树、命令和日志摘要在 JSON 的 `core_git_source_migrations` 中。不同 feature 配置的重复运行不计作新增独立测试。

三个应用仓库同时修正了共享 Cargo 构建目录的使用方式。安装、打包和验收脚本通过 Cargo metadata 找到真实产物路径；`zcalld` 保留并发更新的 `f32a25bb` 业务修复，完整官方门禁、私有原生包和安装器夹具通过。其监听功能仍由 [PR #1](https://github.com/LIghtJUNction/zcalld/pull/1) 单独集成和验收。

ztype 已完成 28 项私有 Wayland 验收，且确认与此前通过 Rust、Clippy、CLI、私有安装和 Xvfb 检查的 ELF 摘要一致；[PR #2](https://github.com/LIghtJUNction/ztype/pull/2) 合并后的源码树也与测试树一致。私有兼容库依据固定源码及两份补丁重建，原环境失败记录完整保留。

ztty 采用原维护者已发布的 be29c676：规范 Git 源、实际 Cargo compiler-artifact 路径、独立插件夹具和锁文件一起完成迁移。[已发布验收记录](https://github.com/LIghtJUNction/ztty/blob/be29c6763d3f63832f77c21746d7d62aa70e7d62/docs/reports/default-branch-sources-20261121/results.json)包含 530 项 Rust 通过、9 项原有忽略、22 项插件 CLI 检查，以及软件和 GPU 两种模式各 12 次 reload 尝试。GPU 使用私有 Xvfb 下的 Mesa llvmpipe；这轮是源码集成，未更新桌面安装或发行版。另一个验收脚本的 Cargo 配置目录解析补丁正在做三种真实 metadata 路径核对，旧候选的过期门禁保持原身份。

zcalld 监听器候选 97d97e39 已保留并发进入主线的 Claude/community 适配、安装器和 0.4.1 改动，完成 177 项 Rust、严格 Clippy、实际 release 构建与 8 项 HTTP/Unix curl 取消检查。新主线 daaa5973 仅更新了该候选已包含的 compat gitlink，逐叶证明确认候选包含全部主线内容。其固定源码和冻结二进制已交现有 SSMCP 维护者作最终 32/P1，PR #1 继续保留草稿状态。

`zrc`、`zdot`、`LMM`、`Oni` 和 `mechrevo-drivers` 也已发布；API 的三个 Git 源与最新 LMM gitlink 继续验收：首轮编译触及 3 GiB 内存限额，已通过的锁文件、26 份源码／feature 等价和格式检查保留；当前以相同输入、4 GiB 内存和仅移除 lmm-core 测试调试符号的方式续跑剩余三组纯单元测试。聚合工具最初通过 80 项测试，规范 Git URL 修正另通过 21 项定向真实 Git/Cargo 测试，均零跳过；它们不替代各应用和新 44 仓完整图的验收。最终图将显式登记已确认活跃的独立 fuzz／插件测试工作区，并保留比较基准的有意旧版本来源。

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
| LIghtJUNction/oh-my-ztty | [`dbc1aed325`](https://github.com/LIghtJUNction/oh-my-ztty/commit/dbc1aed3259c0f665affba220b6e2e1ce1d45d50)（全部 74 个旧提交独立复核） |

SSMCP 两轮共移除 **152 个生成附件路径**。第二轮核对 1,150 个历史源码树的保留条目，原子更新 112 个分支和 29 个标签；116 份原始媒体内容已归档并下载校验。5 个旧公开版本的发布清单保持原始构建身份，新的部署辅助逻辑只接受经证明的固定源码映射。详见[完整清理报告](https://github.com/LIghtJUNction/ssmcp/blob/ccb91955c25969f4779588d4cebb09b72c00f829/docs/reports/generated-history-cleanup-20261121.json)及[媒体归档](https://drive.google.com/file/d/1Rr9t9SpoMdwQJuHbW3eYRbgtg-krhUkF/view)。

oh-my-ztty 已发布清理后主线 [dbc1aed3](https://github.com/LIghtJUNction/oh-my-ztty/commit/dbc1aed3259c0f665affba220b6e2e1ce1d45d50)。 [历史证明](https://github.com/LIghtJUNction/oh-my-ztty/blob/dbc1aed3259c0f665affba220b6e2e1ce1d45d50/docs/reports/history-cleanup-20261121.json)和[源码验收](https://github.com/LIghtJUNction/oh-my-ztty/blob/dbc1aed3259c0f665affba220b6e2e1ce1d45d50/docs/reports/source-acceptance-20261121.json)均已发布。原维护者记录 13 个分支、10 个标签、74 份保留源码等价证明及 112 项检查，并保护 3 个工作区和 2 处未提交源码。独立复核已从原始恢复 bundle 补齐全部 74 个旧提交，逐项核对保留路径、文件模式、blob、gitlink、父顺序和提交内容，确认 10 个附注标签仅更换目标对象行。全部 23 个可写引用已读回，新历史不含这 14 个目标路径；原始 bundle 校验值保持不变。[14 份历史图片归档](https://drive.google.com/file/d/1CV-2aZmRSPvoEy59w0xv-jViiMpdz8Be/view)也已完整下载核对内容与 SHA-256。组件锁中较早的 ztty／SSMCP 来源仍交原维护者做最终刷新。

完成范围是已核对的受控 Git 引用。GitHub 管理的 PR 引用、缓存和服务端物理垃圾回收不属于本次可写及可验证范围；旧 tag 自带的旧打包脚本也不会自动获得新辅助逻辑。

## 开发机与磁盘

Cargo 默认共用 `/var/tmp/project-z-cargo-target`，多步构建通过同一外层锁保护。首批 129 个闲置目标目录处理完成后，`/home` 的可用空间实测从 **33.50 GB 增至 289.69 GB**。续跑回执为 128 个已删除、1 个在先前尝试中已删除。

另外 3 个 LMM 缓存也已删除；这段操作前后可用空间实测 **289.19 GB → 291.38 GB**，净变化约 **2.19 GB**。目录 `du` 合计约 8.55 GB，受共享块和并发活动影响，不能把该合计当作实测释放空间。

WGT 的 4 个精确 Cargo 缓存目录已全部删除并逐项验证。执行前重新取得共享锁及各目录 Cargo 锁，复核 inode、进程、挂载和容器；执行后源码提交、状态、权重和 8 个保留缓存目录身份一致。操作窗口可用空间实测 **288.87 GB → 344.75 GB**，净增 **55.88 GB（52.04 GiB）**；目录 du 合计 89.62 GB 仅表示目录统计值。[完整删除回执](https://drive.google.com/file/d/1nc-aFcN4c58WQP_4S0nVCnQmZNJV892d/view)已下载核对 SHA-256，首轮只等锁的记录也保留。SSMCP 当前源码、发布证明、活动构建以及整个共享 Cargo 目录仍在保护范围内。

## 产品与发布

**MagicBox** 的极简界面和文档已随 [PR #4](https://github.com/LIghtJUNction/MagicBox/pull/4) 合并。两个构建各 96 项 JVM 检查、APK 完整性、5 项 Android 模拟器流程和真实两跳代理验收通过；明暗界面已实际查看。rooted 实机 TUN/eBPF 验证仍未执行。

**SSMCP 新版本**由现有发布维护者继续处理。[PR #152](https://github.com/LIghtJUNction/ssmcp/pull/152) 已合并至 cbe3d0ef；发布前的固定基线构建、六个粘贴场景、后续粘贴补丁和最新 zcalld 监听组合的最终 32/P1 分别保留各自证据。旧候选的 277 个包源码审计与 100 项 Python 检查保持原提交范围，正式新版本尚未发布。

追加的 **Docker context 式本地／远程统一化** 已进入独立工作区的实现准备。命名配置将保存本地或 HTTPS relay 目标，统一处理命令行、环境变量和持久默认选择；凭据继续使用按 origin 隔离的现有存储。已有本地和远程连接共享 broker、wire 和原生 runtime。现行运行代码已移除 SSH 设备连接，因此此次不会把仅保留的旧参数解析器误当作可用 SSH 后端。切换 context 只影响新连接，保存的 session 和已有任务保持原目标。参考 [Docker contexts](https://docs.docker.com/engine/manage-resources/contexts/) 与 [context use](https://docs.docker.com/reference/cli/docker/context/use/)。实现与当前发布冻结源码隔离，尚未合并或发布。

## 仍需闭合的初始 PR

| 项目 | 当前剩余 |
| --- | --- |
| [KernelSU #1](https://github.com/LIghtJUNction/KernelSU/pull/1) | 大范围上游迁移、设备适配与真实设备验证。 |
| [video-work-api #11](https://github.com/LIghtJUNction/video-work-api/pull/11) | torch/torchaudio 与固定 FunClip/CosyVoice 约束及模型、CUDA 验证。 |
| [zcalld #1](https://github.com/LIghtJUNction/zcalld/pull/1) | 最新 97d 候选本地门禁已过；等待现有维护者完成固定组合的 native 32/P1，再核对合并树。 |
| [codewhale-lmm-provider #3](https://github.com/TokenNotIncluded/codewhale-lmm-provider/pull/3) | 按用户组隔离的后端接口、客户端注册及真实宿主验收材料。 |
| [hireferry #21](https://github.com/TokenNotIncluded/hireferry/pull/21) | 私有 Android AVD 上的返回桌面与 WebView／服务组合验收。 |
| [lmm-api-source #10](https://github.com/TokenNotIncluded/lmm-api-source/pull/10) | 原定向回归已修复，最终组合验证及真实生产升级材料仍待闭合。 |
| [lmm-api-source #11](https://github.com/TokenNotIncluded/lmm-api-source/pull/11) | 预留未结算与锁超时之间的实际因果关系。 |

维护报告与归档位置：[GitHub PR #7](https://github.com/LIghtJUNction/project-z/pull/7)、[Google 云盘目录](https://drive.google.com/drive/folders/1vjkFko8onQm9WiScrw7QBopK9vNGTLx0)。完整 JSON 保留每个结果对应的源码、命令、日志和验证边界。
