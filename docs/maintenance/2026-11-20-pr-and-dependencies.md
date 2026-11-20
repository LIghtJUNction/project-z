# Project Z 维护进展

更新：2026-11-21 05:53（Asia/Taipei）。

## 当前结果

**内部 Git 源迁移已完成本页列出的 19 个仓库本轮发布；受控 Git 历史中的生成附件清理已完成 14 个完整核实的仓库。** oh-my-ztty 的 23 个引用、74 个原提交和 14 份历史图片也已完成独立复核。开发机首批 129 个闲置 Cargo 目录、另外 3 个 LMM 缓存和 4 个 WGT 缓存均已处理完成。当前继续推进其余消费者、上游新提交的定向传播、最新组合的原生验收、完整 44 仓依赖图及新版本发布。

初始 85 项 PR 仍按原清单去重计数：**已合并 56、已关闭 14、仓库已归档 9、具体阻塞 5、验收／集成中 1**。新建的依赖迁移 PR 单独记录。[完整清单与逐项证据](2026-11-20-pr-and-dependencies.json)保留全部 85 项条目和历史验证范围。

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
| ztype | [`76c43579b9`](https://github.com/LIghtJUNction/ztype/pull/2) | 已合并，原 28 项私有 Wayland 检查使用 GTK 接收端；新增 ztty 兼容验收见下文 |
| ztty | [`be29c6763d`](https://github.com/LIghtJUNction/ztty/commit/be29c6763d3f63832f77c21746d7d62aa70e7d62) | 原迁移门禁通过；最新内存回收修复已合入 febc9065，实际验证与合并树一致 |
| API | [`304f49d87d`](https://github.com/TokenNotIncluded/lmm-api-source/commit/304f49d87df1c2fb83d4145386c569d237af8c90) | 已发布，13 项定向单元测试与源码、锁文件等价核对通过 |

8 个核心仓库各自的 fmt、测试、严格 Clippy 及适用的 no_std/Wasm 检查已通过，固定提交、源码树、命令和日志摘要在 JSON 的 `core_git_source_migrations` 中。不同 feature 配置的重复运行不计作新增独立测试。

三个应用仓库同时修正了共享 Cargo 构建目录的使用方式。安装、打包和验收脚本通过 Cargo metadata 找到真实产物路径；`zcalld` 保留并发更新的 `f32a25bb` 业务修复，完整官方门禁、私有原生包和安装器夹具通过。其监听功能仍由 [PR #1](https://github.com/LIghtJUNction/zcalld/pull/1) 单独集成和验收。

ztype 原迁移完成 28 项私有 Wayland 验收，接收端为 GTK；对应 ELF 与该轮 Rust、Clippy、CLI、私有安装和 Xvfb 检查一致，[PR #2](https://github.com/LIghtJUNction/ztype/pull/2) 的合并树也与测试树一致。这些结果保持原源码和接收端范围。当前针对真实 ztty 窗口的新一轮兼容验证单独记录。

ztty 采用原维护者已发布的 be29c676：规范 Git 源、实际 Cargo compiler-artifact 路径、独立插件夹具和锁文件一起完成迁移。[已发布验收记录](https://github.com/LIghtJUNction/ztty/blob/be29c6763d3f63832f77c21746d7d62aa70e7d62/docs/reports/default-branch-sources-20261121/results.json)包含 530 项 Rust 通过、9 项原有忽略、22 项插件 CLI 检查，以及软件和 GPU 两种模式各 12 次 reload 尝试。GPU 使用私有 Xvfb 下的 Mesa llvmpipe；这轮是源码集成，未更新桌面安装或发行版。验收脚本的 Cargo 配置目录解析补丁也已随 [PR #21](https://github.com/LIghtJUNction/ztty/pull/21) 合入 c7c2a3e8。仅共享配置、绝对环境路径、异地启动的相对环境路径三种真实 metadata 场景均通过，8 组 GUI／Wayland 命令参数全部指向实际产物。该补丁只改一个 Python 文件；此前完整运行门禁仍保留 be29 的源码身份。

用户追加的 ztty 迭代已完成两种模式各七阶段的内存基线。固定 c7c2a3e8 源码和同一 ELF，在私有 Xvfb 中从一个窗口增至十个，再关闭九个：软件模式的 broker PSS 从 6.5 MB 变为 8.4 MB；GPU 代码路径从 138.8 MB 变为 289.5 MB。这里的 GPU 使用 Mesa llvmpipe，不能外推硬件显存或真实 GPU 延迟。[完整基线](https://drive.google.com/file/d/12PscZCsQ0KP0I2jYPLLhS8vp2jjnbzXk/view)已下载逐字节核对，既有 72 个 worktree 保持原样。

后续[分配器诊断](evidence/ztty-allocator-diagnosis-20261121.json)确认，渲染 context 和 surface 均正常销毁；关闭九个窗口后，活跃分配回到约 42.4 MB，但分配器仍保留约 335.4 MB 空闲块。诊断性归还空闲页后，匿名 PSS 回到 43.85 MB，活跃分配量保持不变。因此修复放在实际窗口视图销毁、布局移除之后，由 GNU libc 尽力归还空闲页；其他 libc 保留原行为。

[ztty PR #22](https://github.com/LIghtJUNction/ztty/pull/22) 已合并为 **febc9065**，合并树 ca160bd3 与实际验证的 **bfee445f** 完全一致。该提交保留并行主线 c6dc42c8 的搜索缓存更新，仅新增三个文件中的 19 行。固定产物完成实际源码 Clippy、release 编译、34 项窗口生命周期检查、6 组共 66 个采样阶段和 162 次关闭 RPC。对照使用软件模式 AB、GPU 代码路径 ABBA 顺序；后者在私有 Xvfb、Mesa llvmpipe、两个渲染线程下运行。

| 最终对照指标 | 主线 c6dc42c8 | 内存修复 bfee445f |
| --- | ---: | ---: |
| GPU 代码路径第三轮关闭后 broker 匿名 PSS，两次运行 | 323.8–324.3 MB | 44.3–44.6 MB |
| GPU 代码路径关闭 RPC 中位耗时，54 次 | 1.995 ms | 3.021 ms |
| GPU 代码路径关闭 RPC 最大耗时 | 3.530 ms | 4.192 ms |
| 软件模式关闭 RPC 中位耗时，27 次 | 0.132 ms | 0.181 ms |

内存采用十进制 MB，取 broker 进程每阶段三次 `Pss_Anon` 采样的中位数。时间覆盖整个关闭请求的协议、销毁、内存回收和调度；物理 GPU、显存、帧时间与键盘输入延迟留待各自环境测量。[最终验证](evidence/ztty-memory-bfee-20261121.json)、[合并来源](evidence/ztty-memory-publication-20261121.json)、[逐项独立复核](evidence/ztty-bfee-independent-review-20261121.json)及[131 份文本证据包](https://drive.google.com/file/d/1kbVMmeWDPEmuYPJRlofrjwE06zTv0ARV/view)均已保存。GNU／musl 模块探针复用字节相同的代码与同一编译器的已通过结果。全部自有进程已回收；当前发布结果是源码合并。

zcalld 监听器已更新到 **d5314fe9**，完整吸收当前 c4b4bbab 主线的安装器修复和 0.4.3 改动，同时刷新 zcall-gui 文档提交。逐叶比较确认保留 212 个其余主线条目，五个监听器文件与已审查版本一致。新候选实际通过 **179 项 Rust 测试、严格 Clippy、release 构建和 8 项 TCP／Unix curl 取消测试**，共 22 条命令、零跳过；实际外锁、构建来源和固定二进制摘要均保留在[完整回执](evidence/zcalld-listener-d531-20261121.json)及[云盘副本](https://drive.google.com/file/d/1lVa3-tGuOzOwhsOSooMiUX51kD4i0p_d/view)。现有 SSMCP 负责人正在准备最终固定组合的 Gate10/P1，PR #1 仍为草稿。原 97d 的 177 项测试与找回的 job39a 启动审计保持原身份；最终联调仍要求真实跨进程阻塞生成取消，不把旧 32 项集合中无关的 shared-library、Go、打包／安装检查计成本轮通过。

`zrc`、`zdot`、`LMM`、`Oni` 和 `mechrevo-drivers` 也已发布；API 的三个 Git 源与最新 LMM gitlink 已随 304f49d8 发布，合计 13 项目标单元测试通过：1 项 hex、3 项流兼容和 9 项 CLI 参数解析。锁文件、26 份源码／feature 等价和格式检查也已保留。首轮 3 GiB 内存不足与续跑时误选 5 项缺少 DATABASE_URL 的 SQLx 测试均如实记录；之后以精确解析器选择器完成剩余检查，未连接数据库。聚合工具最初通过 80 项测试，规范 Git URL 修正另通过 21 项定向真实 Git/Cargo 测试，均零跳过；它们不替代各应用和新 44 仓完整图的验收。最终图将显式登记已确认活跃的独立 fuzz／插件测试工作区，并保留比较基准的有意旧版本来源。

**递归源码检查已修复**：[Project Z PR #9](https://github.com/LIghtJUNction/project-z/pull/9) 已合入 PR #7 的协调分支，提交为 9d725a15。检查器逐层核对实际 Git 仓库、所固定的提交和工作区改动，并在整个子树通过后缓存结果；同步前先完成检查，保护已有文件。四层真实 Git 夹具覆盖深层修改、旧提交和缺失检出，最终 **91 项测试通过**，其中已包含 8 项递归检查和 9 项 SourceLink 检查。[合并核对](evidence/project-z-pr9-merge-20261121.json)与[原始证据包](https://drive.google.com/file/d/1r5nus_vSPZDMid_TMDYsuzxGdrPMJe9a/view)保留源码及原始测试结果。完整 44 仓图将使用更新后的检查器，在最终组件版本就位后执行。

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

oh-my-ztty 已发布清理后主线 [dbc1aed3](https://github.com/LIghtJUNction/oh-my-ztty/commit/dbc1aed3259c0f665affba220b6e2e1ce1d45d50)。 [历史证明](https://github.com/LIghtJUNction/oh-my-ztty/blob/dbc1aed3259c0f665affba220b6e2e1ce1d45d50/docs/reports/history-cleanup-20261121.json)和[源码验收](https://github.com/LIghtJUNction/oh-my-ztty/blob/dbc1aed3259c0f665affba220b6e2e1ce1d45d50/docs/reports/source-acceptance-20261121.json)均已发布。原维护者记录 13 个分支、10 个标签、74 份保留源码等价证明及 112 项检查，并保护 3 个工作区和 2 处未提交源码。独立复核已从原始恢复 bundle 补齐全部 74 个旧提交，逐项核对保留路径、文件模式、blob、gitlink、父顺序和提交内容，确认 10 个附注标签仅更换目标对象行。全部 23 个可写引用已读回，新历史不含这 14 个目标路径；原始 bundle 校验值保持不变。[14 份历史图片归档](https://drive.google.com/file/d/1CV-2aZmRSPvoEy59w0xv-jViiMpdz8Be/view)也已完整下载核对内容与 SHA-256。随后原维护者通过普通源码更新将主线推进到 [d671295f](https://github.com/LIghtJUNction/oh-my-ztty/commit/d671295f63e5d72e8e8b683fd0c75dc0b1395072)，消费 SSMCP cbe／ztty be29，并记录 112 项检查、实际 bundle 与隔离安装验收。仅补充 ztty c7c 工具提交的 [草稿 PR #7](https://github.com/LIghtJUNction/oh-my-ztty/pull/7) 又完成了精确 a8c 候选的 112 项检查及六组件源码验证，[回执已归档](https://drive.google.com/file/d/17T3wOD6ZNRDX-H6STHcGcHtCcW8wbMrC/view)；该小补丁未重新构建 bundle，最终 SSMCP 来源传播由同一维护链接力。

完成范围是已核对的受控 Git 引用。GitHub 管理的 PR 引用、缓存和服务端物理垃圾回收不属于本次可写及可验证范围；旧 tag 自带的旧打包脚本也不会自动获得新辅助逻辑。

## 开发机与磁盘

Cargo 默认共用 `/var/tmp/project-z-cargo-target`，多步构建通过同一外层锁保护。首批 129 个闲置目标目录处理完成后，`/home` 的可用空间实测从 **33.50 GB 增至 289.69 GB**。续跑回执为 128 个已删除、1 个在先前尝试中已删除。

另外 3 个 LMM 缓存也已删除；这段操作前后可用空间实测 **289.19 GB → 291.38 GB**，净变化约 **2.19 GB**。目录 `du` 合计约 8.55 GB，受共享块和并发活动影响，不能把该合计当作实测释放空间。

WGT 的 4 个精确 Cargo 缓存目录已全部删除并逐项验证。执行前重新取得共享锁及各目录 Cargo 锁，复核 inode、进程、挂载和容器；执行后源码提交、状态、权重和 8 个保留缓存目录身份一致。操作窗口可用空间实测 **288.87 GB → 344.75 GB**，净增 **55.88 GB（52.04 GiB）**；目录 du 合计 89.62 GB 仅表示目录统计值。[完整删除回执](https://drive.google.com/file/d/1nc-aFcN4c58WQP_4S0nVCnQmZNJV892d/view)已下载核对 SHA-256，首轮只等锁的记录也保留。SSMCP 当前源码、发布证明、活动构建以及整个共享 Cargo 目录仍在保护范围内。

## 产品与发布

**MagicBox** 的极简界面和文档已随 [PR #4](https://github.com/LIghtJUNction/MagicBox/pull/4) 合并。两个构建各 96 项 JVM 检查、APK 完整性、5 项 Android 模拟器流程和真实两跳代理验收通过；明暗界面已实际查看。rooted 实机 TUN/eBPF 验证仍未执行。

**SSMCP 新版本**由现有发布维护者继续处理。[PR #152](https://github.com/LIghtJUNction/ssmcp/pull/152) 已合并至 cbe3d0ef；发布前的固定基线构建、六个粘贴场景、后续粘贴补丁和最新 zcalld 监听组合的最终 Gate10/P1 分别保留各自证据。旧候选的 277 个包源码审计与 100 项 Python 检查保持原提交范围，正式新版本尚未发布。

追加的 **Docker context 式本地／远程统一化** 已随 [PR #153](https://github.com/LIghtJUNction/ssmcp/pull/153) 合入。独立验收又发现两个问题：前台 reload 重新解析旧 context，会在配置切换或删除后改变目标或失败；UI 的严格配置结构遗漏共享 config.toml 中的 contexts 表，导致启动失败。[PR #155](https://github.com/LIghtJUNction/ssmcp/pull/155) 已修复并由原主线负责人于 21:02 UTC 合入 cf0ab581。重载固定使用启动时已解析的本地／HTTPS 目标，保留字面参数、保存会话入口、cwd 和环境；UI 复用现有 typed context 校验，继续拒绝未知字段和凭据字段。

固定 bbebfaef 候选实际通过 **84 项单元测试、17 项 CLI 检查、严格 Clippy，以及 3 次真实本地前台重载**。三个场景分别从命令行、环境变量、持久默认配置选择 context，随后更改或删除配置，再验证实际重载保持原目标。终端重连曾在 101 项 Rust 测试完成后中断构建；续跑先校验同一源码、锁文件、Git 来源和完整日志，再只补完产物构建与三次重载。原中断和更早失败记录均保留。已测试 tree 为 1356b94a，合并 tree 为 bd2bcce3，后者含并行主线改动，因此没有把此门禁标作整个新主线或最终 P1 的通过结果。[完整来源与验收回执](evidence/ssmcp-context-bbeb-20261121.json)和[原始证据包](https://drive.google.com/file/d/1I39T3KPk6004lvbh5HSOJOJNE_YrBo6m/view)已经校验归档。配置优先级、按 origin 隔离凭据及保存会话固定目标的规则保留；现行运行代码不提供 SSH 设备连接。

**开发机证据恢复**：19:32–19:34 UTC，多个现有维护者检查发现部分 `GITHUB/ssmcp-*` 源码／验收目录已不存在，根因尚未确定。本轮有回执的缓存删除没有包含这些路径。主 SSMCP Git 仓库、Project Z 内的 context 隔离树和 zcalld 交接目录仍在；原发布维护者正在从已有副本恢复源码与证据。缺失的五个基线二进制需要重新实编，旧测试记录保持原身份。

**HireFerry 移动端**的 [PR #21](https://github.com/TokenNotIncluded/hireferry/pull/21) 已合并为 **0d900c29**，合并树 b6e3e543 与实际通过验收的 5d9313df 候选完全一致。原先在界面线程同步查询 WebView URL 导致的 Focus ANR／SendError／SIGABRT 已修复，原 45 秒基线全部通过。随后在私有 Android 模拟器上实际完成 WebView → Chrome 明确授权 → 应用返回的流程，验证了授权前未勾选、确认码一致、独立应用会话、浏览器原会话保持、生命周期保持、拒绝重复兑换和返回本地设置页。新的流程没有 ANR 或崩溃，私有服务器、数据库与模拟器均已关闭。[最终验收回执](evidence/hireferry-21-final-20261121.json)及[云盘副本](https://drive.google.com/file/d/1j3JXDIKZQl9zzB_aLbWO06TLzOC85QDv/view)保留先前失败和修复边界；iOS 仍仅引用原历史验证，没有新增实机或正式签名／商店发布声明。

**最新上游传播**：zuse [a1bb8fd2](https://github.com/LIghtJUNction/zuse/commit/a1bb8fd2cbce0a9d85134999883c578358065242) 已被 ztype [da6feb1a](https://github.com/LIghtJUNction/ztype/commit/da6feb1a3c5488f3854c63d5e5db173ca250dba4) 和 SSMCP [4237eea2](https://github.com/LIghtJUNction/ssmcp/commit/4237eea2cab8253b8dff84d81861ba1e1adf4246) 消费。ztype 的维护者记录 72 项通过、1 项可选词典测试忽略；SSMCP 的锁文件来源已独立核对。oh-my-ztty [f04f6ea8](https://github.com/LIghtJUNction/oh-my-ztty/commit/f04f6ea8ae909e121edabbd766ee725a472f8146) 又消费了 SSMCP 4237，原维护者记录 112 项检查。其 ztty c7 草稿与 SSMCP 后续 context／当前功能提交仍需在同一维护链合流，最终 44 仓实际 sync/check/resolve 尚未完成。

**ztype 与 ztty 兼容及界面更新**：当前 0.4.2 候选在独立工作区延续已安装 0.4.1 的焦点保护与不透明候选框，按 Material 的文字与颜色角色整理布局。固定 ELF 已通过编译、严格 Clippy、8 项 CLI 与 15 项私有安装检查；真实 X11／XIM ztty 接收端另通过 **13 项检查**，覆盖中文句子、非首候选、多窗口、焦点、候选框、晚启动和重连。[本轮 XIM 原始记录](evidence/ztype-xim-ui-20261121.json)绑定前后相同的两个二进制。

真实 native Wayland ztty 接收端发现一个待修复问题：候选框呈现和隐藏成功，但 PTY 收到 `ihaoshijie`，预期为中文“你好世界”。现有维护者正在沿 text-input-v3 事件与提交路径定位，并已收到新合并 ztty 的固定产物用于复核。当前 0.4.2 草稿发布及完整原生兼容验收仍在进行；用户现有 0.4.1 安装和输入法配置保留。

**SSMCP 输入与消息处理**：完整原始记录确认这是两个独立参数。`--input` 选择输入来源，默认 `terminal`，并支持 web 的 host／port、MCP 的 stdio／HTTP、默认或自定义 sock 路径及管道输入；用户最新补充，显式 `--input none` 禁用聊天框。`--agent` 指定聊天框消息的处理者，支持 Codex、Claude Code、其他 coding agent 或另一个 SSMCP，默认名称最终更正为 `next-caller`，表示交付到下一次符合条件的工具调用结果。当前源码负责人及原 CLI 线程统一实现。[只读架构核对](evidence/ssmcp-input-agent-contract-20261121.md)已明确输入、处理方、现有消息队列及保存重载的边界，并列出八组建议验收；建议尚未当作已运行结果。前一版报告把 input 解释为处理目标的错误已纠正，未据此修改源码。

该功能已推送至 [SSMCP 草稿 PR #159](https://github.com/LIghtJUNction/ssmcp/pull/159)，当前冻结提交 cae35a82、树 2657970b。源码包含显式 `--input none` 的连接级聊天禁用、独立消息处理方及保存重载规则。原负责人正在完成五个固定产物的实际编译与来源校验，随后执行对应原生运行门禁；zcalld d531 的最终 Gate10/P1 仍待该组合就位。

## 仍需闭合的初始 PR

| 项目 | 当前剩余 |
| --- | --- |
| [KernelSU #1](https://github.com/LIghtJUNction/KernelSU/pull/1) | 大范围上游迁移、设备适配与真实设备验证。 |
| [video-work-api #11](https://github.com/LIghtJUNction/video-work-api/pull/11) | torch/torchaudio 与固定 FunClip/CosyVoice 约束及模型、CUDA 验证。 |
| [zcalld #1](https://github.com/LIghtJUNction/zcalld/pull/1) | 最新 d531 候选已过 179 项 Rust 与 8 项实际取消测试；等待固定 SSMCP 组合的 native Gate10/P1，再核对合并树。 |
| [codewhale-lmm-provider #3](https://github.com/TokenNotIncluded/codewhale-lmm-provider/pull/3) | 按用户组隔离的后端接口、客户端注册及真实宿主验收材料。 |
| [lmm-api-source #10](https://github.com/TokenNotIncluded/lmm-api-source/pull/10) | 原定向回归已修复，最终组合验证及真实生产升级材料仍待闭合。 |
| [lmm-api-source #11](https://github.com/TokenNotIncluded/lmm-api-source/pull/11) | 预留未结算与锁超时之间的实际因果关系。 |

维护报告与归档位置：[GitHub PR #7](https://github.com/LIghtJUNction/project-z/pull/7)、[Google 云盘目录](https://drive.google.com/drive/folders/1vjkFko8onQm9WiScrw7QBopK9vNGTLx0)。完整 JSON 保留每个结果对应的源码、命令、日志和验证边界。
