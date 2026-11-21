# Project Z 维护进展

更新：2026-11-21 08:39（Asia/Taipei；UTC 2026-11-21 00:39；各来源以链接中的固定观察时间为准）。

## 当前结果

**SSMCP 固定 781／FC 的输入对照已完整通过并独立核对：普通 16 KiB 输入从 2439.16 ms 降至 27.85 ms；这是每类每版各一次的观察，变慢的子指标也保留在下文。zuse 固定 356 的私有原生验收已通过，回执修复 PR #3 已合入 PR #2 的功能分支，合并树与被测树完全一致。** ztype 0.4.2、ztty 中文输入和光标修复保持已合并。SSMCP 新 main 与 zcalld 后继源码仍需完成各自最终运行与 Gate10/P1，完整 44 仓图等待最终组件。

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
| ztype | [`76c43579b9`](https://github.com/LIghtJUNction/ztype/pull/2) | 已合并，原迁移门禁保留；0.4.2 PR #3 与真实 ztty 输入兼容验收已完成，见下文 |
| ztty | [`be29c6763d`](https://github.com/LIghtJUNction/ztty/commit/be29c6763d3f63832f77c21746d7d62aa70e7d62) | 原迁移门禁通过；内存 PR #22、输入 PR #23、光标 PR #24 分别合入；最新 99ef7a0f 与光标测试树一致 |
| API | [`304f49d87d`](https://github.com/TokenNotIncluded/lmm-api-source/commit/304f49d87df1c2fb83d4145386c569d237af8c90) | 已发布，13 项定向单元测试与源码、锁文件等价核对通过 |

8 个核心仓库各自的 fmt、测试、严格 Clippy 及适用的 no_std/Wasm 检查已通过，固定提交、源码树、命令和日志摘要在 JSON 的 `core_git_source_migrations` 中。不同 feature 配置的重复运行不计作新增独立测试。

三个应用仓库同时修正了共享 Cargo 构建目录的使用方式。安装、打包和验收脚本通过 Cargo metadata 找到真实产物路径；`zcalld` 保留并发更新的 `f32a25bb` 业务修复，完整官方门禁、私有原生包和安装器夹具通过。其监听功能仍由 [PR #1](https://github.com/LIghtJUNction/zcalld/pull/1) 单独集成和验收。

ztype 原迁移完成 28 项私有 Wayland 验收，接收端为 GTK；对应 ELF 与该轮 Rust、Clippy、CLI、私有安装和 Xvfb 检查一致，[PR #2](https://github.com/LIghtJUNction/ztype/pull/2) 的合并树也与测试树一致。这些结果保持原源码和接收端范围。新增真实 ztty 窗口的兼容验收已经完成，按其实际源码与产物单独记录。

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

**ztty 的 Wayland 输入修复已随 [PR #23](https://github.com/LIghtJUNction/ztty/pull/23) 合并为 01e8b573**，其 a7a99b41 源码树与实际测试的 076bc6ac 完全一致。改动限于 `native/wayland_services.c`，保留首次启用、外部编辑、焦点与序号保护。独立核对已把实际 C 编译输入、object、archive、rlib 和最终 ELF c5debb5f 连到同一源码，并确认主程序真实编译。与固定 ztype 产物配对的原生中文输入已通过；[合并与验收来源](evidence/ztty-ime-publication-20261121.json)、[构建身份复核](evidence/ztty-pr23-build-independent-review-20261121.json)分别记录证据。此前 PR #22 的 66 阶段内存结果仍属于 bfee 候选，本次没有重跑或改标其来源。

zcalld 的历史监听器候选 **d5314fe9** 曾完整吸收当时 c4b4bbab 主线的安装器修复和 0.4.3 改动，同时刷新 zcall-gui 文档提交。逐叶比较确认保留 212 个其余主线条目，五个监听器文件与已审查版本一致。该历史候选实际通过 **179 项 Rust 测试、严格 Clippy、release 构建和 8 项 TCP／Unix curl 取消测试**，共 22 条命令、零跳过；实际外锁、构建来源和固定二进制摘要均保留在[完整回执](evidence/zcalld-listener-d531-20261121.json)及[云盘副本](https://drive.google.com/file/d/1lVa3-tGuOzOwhsOSooMiUX51kD4i0p_d/view)。这些验收保留 d531 身份。当前 PR #1 已到下文的 E1 来源后继，仍为草稿；新候选产品门禁及最终 SSMCP Gate10/P1 另行记录。原 97d 的 177 项测试与找回的 job39a 启动审计保持原身份；最终联调仍要求真实跨进程阻塞生成取消，不把旧 32 项集合中无关的 shared-library、Go、打包／安装检查计成本轮通过。

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

**00:27:50 UTC 的开发机只读快照**记录 `/home` 可用 391.14 GB、可用内存 6.73 GB、1 分钟 load 2.13，当时未观察到 Cargo／rustc 进程。[原始观察](evidence/developer-machine-observation-20261121-0027.json)只描述该时间点；空间变化不全归因于本轮清理，也不代替下一批任务的实际外锁检查。

## 产品与发布

**MagicBox** 的极简界面和文档已随 [PR #4](https://github.com/LIghtJUNction/MagicBox/pull/4) 合并。两个构建各 96 项 JVM 检查、APK 完整性、5 项 Android 模拟器流程和真实两跳代理验收通过；明暗界面已实际查看。rooted 实机 TUN/eBPF 验证仍未执行。

**SSMCP 新版本**由现有发布维护者继续处理。[PR #152](https://github.com/LIghtJUNction/ssmcp/pull/152) 已合并至 cbe3d0ef；发布前的固定基线构建、六个粘贴场景、后续粘贴补丁和最新 zcalld 监听组合的最终 Gate10/P1 分别保留各自证据。旧候选的 277 个包源码审计与 100 项 Python 检查保持原提交范围，该候选的最终发布验收尚未完成；另一条后续 main 发布链在下文分别记录。

追加的 **Docker context 式本地／远程统一化** 已随 [PR #153](https://github.com/LIghtJUNction/ssmcp/pull/153) 合入。独立验收又发现两个问题：前台 reload 重新解析旧 context，会在配置切换或删除后改变目标或失败；UI 的严格配置结构遗漏共享 config.toml 中的 contexts 表，导致启动失败。[PR #155](https://github.com/LIghtJUNction/ssmcp/pull/155) 已修复并由原主线负责人于 21:02 UTC 合入 cf0ab581。重载固定使用启动时已解析的本地／HTTPS 目标，保留字面参数、保存会话入口、cwd 和环境；UI 复用现有 typed context 校验，继续拒绝未知字段和凭据字段。

固定 bbebfaef 候选实际通过 **84 项单元测试、17 项 CLI 检查、严格 Clippy，以及 3 次真实本地前台重载**。三个场景分别从命令行、环境变量、持久默认配置选择 context，随后更改或删除配置，再验证实际重载保持原目标。终端重连曾在 101 项 Rust 测试完成后中断构建；续跑先校验同一源码、锁文件、Git 来源和完整日志，再只补完产物构建与三次重载。原中断和更早失败记录均保留。已测试 tree 为 1356b94a，合并 tree 为 bd2bcce3，后者含并行主线改动，因此没有把此门禁标作整个新主线或最终 P1 的通过结果。[完整来源与验收回执](evidence/ssmcp-context-bbeb-20261121.json)和[原始证据包](https://drive.google.com/file/d/1I39T3KPk6004lvbh5HSOJOJNE_YrBo6m/view)已经校验归档。配置优先级、按 origin 隔离凭据及保存会话固定目标的规则保留；现行运行代码不提供 SSH 设备连接。

**开发机证据恢复**：19:32–19:34 UTC，多个现有维护者检查发现部分 `GITHUB/ssmcp-*` 源码／验收目录已不存在，根因尚未确定。本轮有回执的缓存删除没有包含这些路径。主 SSMCP Git 仓库、Project Z 内的 context 隔离树和 zcalld 交接目录仍在；原发布维护者正在从已有副本恢复源码与证据。当时缺失的五个基线二进制已在固定 781b87df 上重新构建完成，运行验收继续推进；旧测试记录保持原身份。

**HireFerry 移动端**的 [PR #21](https://github.com/TokenNotIncluded/hireferry/pull/21) 已合并为 **0d900c29**，合并树 b6e3e543 与实际通过验收的 5d9313df 候选完全一致。原先在界面线程同步查询 WebView URL 导致的 Focus ANR／SendError／SIGABRT 已修复，原 45 秒基线全部通过。随后在私有 Android 模拟器上实际完成 WebView → Chrome 明确授权 → 应用返回的流程，验证了授权前未勾选、确认码一致、独立应用会话、浏览器原会话保持、生命周期保持、拒绝重复兑换和返回本地设置页。新的流程没有 ANR 或崩溃，私有服务器、数据库与模拟器均已关闭。[最终验收回执](evidence/hireferry-21-final-20261121.json)及[云盘副本](https://drive.google.com/file/d/1j3JXDIKZQl9zzB_aLbWO06TLzOC85QDv/view)保留先前失败和修复边界；iOS 仍仅引用原历史验证，没有新增实机或正式签名／商店发布声明。

**zuse 的既有来源与新分支保持分开。** 当前冻结组合继续使用 [a1bb8fd2](https://github.com/LIghtJUNction/zuse/commit/a1bb8fd2cbce0a9d85134999883c578358065242)。旧反向审计中的直接 Cargo 消费者为 SSMCP 和 ztype，oh-my-ztty 通过套件 gitlink、zrc 通过运行时关系间接受影响；在完整初始化 checkout 上执行的[只读 impact](evidence/zuse-existing-impact-20261121.json)实际返回 `oh-my-ztty / ssmcp / zrc / ztype / zuse`，耗时 0.69 秒、exit 0。它没有刷新来源或执行 sync/check/resolve，因此不替代最终 44 仓图。

后续多鼠标、脚本作用域、串并行取消和 NumLock 改动先单独推送至 [zuse 草稿 PR #2](https://github.com/LIghtJUNction/zuse/pull/2)，当时 head 为 bb838b35、树为 285dcbe6；完成下述修复与新候选验收后，功能分支已推进至 83663988／0d1d1900。作者报告了 Rust、no_std、跨平台及原生检查结果，其原始运行门禁的独立核对仍待完成；这些结果没有并入当前 a1bb 验收组合。[本轮跟进状态](evidence/input-ui-followups-20261121.json)保留作者报告与已独立核对事实的区别。

该固定草稿的[独立静态审查](evidence/zuse-pr2-static-review-20261121.md)发现一项回执容量问题：显式提高脚本步数后，合法能力查询生成的结果可能超过后续 JSON token 或 MCP 转义输出容量，使完成回执丢失或被误判为失败。独立 [PR #3](https://github.com/LIghtJUNction/zuse/pull/3) 先在生产源码未改的 44ffb599 上实际复现三个失败，再于修复提交 **35664746／0d1d1900** 通过 6 项 CLI／MCP 入口测试、10 项调度器测试，以及格式、锁定 metadata 和对应严格 Clippy。[RED 原件](evidence/zuse-pr3-red-20261121.json)、[GREEN 原件](evidence/zuse-pr3-green-20261121.json)和[回执复核](evidence/zuse-pr3-targeted-root-review-20261121.json)保留真实命令、退出码、源码与锁持有者。

修复只在容量不足时省略后续事件明细，并明确记录省略数和清理结果；动作仍按原步数、等待、所有权与取消规则执行。错误、取消、动作与清理同时失败均保留失败语义。输出大小不足时只重新编码一次，不重放动作；默认 256 步和 32 MiB 上限不变。[固定实现的独立审查](evidence/zuse-pr3-independent-review-20261121.md)未发现新增阻塞；[定向修复证据包](https://drive.google.com/file/d/15KpLTU4BgQl76r71kcI7Gppskl_T7eje/view)已下载核对哈希。原 PR #2 的[历史来源核对](evidence/zuse-pr2-original-provenance-20261121.md)已恢复 12 份原始文本，确认存在 7 组 Hyprland 结果、CLI 原生输出和 1 项 AT-SPI 原始 Cargo 测试；286 Rust、20 no_std、2 项 MPX 等完整原始命令记录及源码到原 ELF 的构建清单仍缺失。共享目录中的当前二进制哈希已经不同于原记录，不能据其旁边的依赖文件补认原产物。这些缺失属于原 PR #2 的历史证据；本轮固定 356 的新验收独立记录。当前 main／a1bb 和下游冻结来源保持原样。

**固定 356 的新 portable 验收已完成。** 唯一作业 6dc 运行 61.129 秒并 exit 0。默认测试 harness 记录 **289 通过、0 失败、5 忽略**；其中两项 private X11 测试在未开启环境开关时提前返回，不能计作真实 MPX 输入验证。no_std 的 **20 项通过**包含 tests/core.rs 的 17 项；此前 16 项定向修复与默认套件存在重叠，不相加。native 与 wasm32 no_std、Windows GNU、macOS x86/ARM、Linux ARM 的 all-targets 检查及严格 all-targets Clippy 均实际 exit 0；缺失的 Linux ARM target 在本次有界窗口内安装成功。

[原始 portable 回执](evidence/zuse-356-portable-result-20261121.json)与[完整交接](evidence/zuse-356-portable-handoff-20261121.md)保留固定 source356/tree0d1、未变化锁文件、真实编译产物到自有副本的映射，以及 25 次候选根目标的 Clippy 调用。执行结束后 scope inactive/dead、进程组为空、外层锁无持有者或等待者。包含 39 份原始文本、driver 和编译日志，加一份清单（共 40 个成员）的[云盘证据包](https://drive.google.com/file/d/1I_8ldn-U5A1yb-22o4nEYYldTotgfdf8/view)已完整下载复核整包哈希；不包含二进制。[独立复核](evidence/zuse-356-portable-independent-review-20261121.json)已从原始日志重新求和，并核对整包与逐文件哈希；25 次 Clippy 根调用涉及 23 个不同源码路径。随后同一执行者完成了下述私有原生批次。[原 PR #2 来源与当前计划归档](https://drive.google.com/file/d/1AV7fFGqPwhVezRx1OVF9OtqvqqEHRxMU/view)也已完成下载与逐文件校验；它不补认原 PR #2 缺失的完整门禁。


**固定 356 的私有原生批次已闭合。** 唯一作业 **7c9** 实际 exit 0、双 EOF，用时 13.107 秒，六条驱动命令全部通过：认证私有 Xvfb 中两项 MPX 真实启用测试、私有 X11 CLI 正常退出和取消回收、一个显式 AT-SPI 测试、七组私有 Wayland、五组自有 PTY 与十一组合成 USB。两项 MPX 已在 portable 289 的条目中，本次补齐真实环境执行，不累计为 291；AT-SPI 只补齐原五项 ignored 中的一项。各原生夹具组数也不累计为 Rust 测试总数。[原始执行](evidence/zuse-356-native-evidence/native/result.json)、[完整交接](evidence/zuse-356-native-handoff.md)与[独立复核](evidence/zuse-356-native-independent-review.md)保留实际命令、源码与产物链。

运行使用 portable 中真实编译并保留的 CLI **7a6a6d99**、库测试 **e36daa41**，AT-SPI 实际产物也与编译记录和保留副本一致；运行前后源码、Cargo.lock 和产物哈希不变。AT-SPI 原辅助脚本的嵌套 Cargo 实际没有 `--locked`，只确认离线运行及锁文件未变。Wayland 使用自有 headless Cage 0.3.1 和私有 Hyprland 0.57.2，记录零物理 input/KMS 文件描述符及无宿主连接；本轮没有保留 GL renderer 名，不能称重新验证了 llvmpipe 或物理 GPU。串口与 USB 分别使用自有内核 PTY 和合成 ABI。

结束后的[独立清理回执](evidence/zuse-356-native-evidence/native-postflight.json)确认 scope inactive/dead、ControlGroup 为空、九个记录的自有 PID 消失、外锁记录为空。先前因另一合法验收持锁而未启动的[窗口观察](evidence/zuse-356-native-window-blocked.json)仍保留。包含 **73 份文本与一份清单，共 74 个成员**的[云盘原件包](https://drive.google.com/file/d/1_4o5_1MuigO8fMdlw7hOd67TZvW6yP6l/view)已下载逐字节并逐项核对，未重复 portable 或原生门禁。

随后 [PR #3](https://github.com/LIghtJUNction/zuse/pull/3) 合入 PR #2 功能分支为 **83663988**，实际父提交为 bb838b35 与被测 35664746，树精确等于 **0d1d1900**。[GitHub 合并读回](evidence/zuse-pr3-merge-publication-20261121.json)确认 PR #2 仍为草稿，main 仍为 a1bb8fd2；这一步没有刷新 SSMCP／ztype 的依赖或代替下游联调。


**ztype 0.4.2 已随 [PR #3](https://github.com/LIghtJUNction/ztype/pull/3) 合并为 e3e8c101。** 最终 head 为 677d7ca9、树为 930b79b4；实际运行产物来自 053eb39e／2c7bcdf4，ELF 为 1a2b96c0。最终提交只补文档与三份验收辅助脚本，运行源码保持同一内容，辅助脚本哈希也与实际执行记录逐项匹配。[发布来源](evidence/ztype-pr3-publication-20261121.json)与[原始运行交接](evidence/ztype-native-runtime-handoff-20261121.json)明确区分最终提交和实际编译来源。

| 本轮实际验收 | 结果 | 接收端及范围 |
| --- | ---: | --- |
| Rust／CLI／私有安装 | 72 项 Rust 通过，1 项原有可选忽略；CLI 8 项、安装 15 项通过 | 固定 ztype 0.4.2 ELF；严格 Clippy、实际 release 编译通过 |
| GTK Wayland | 28 项通过 | 私有嵌套 compositor 与 GTK 接收端 |
| 原生 ztty Wayland | 7 项通过 | 固定 076bc6ac／c5debb5f 接收端，真实 PTY 收到“你好世界” |
| X11／XIM ztty | 13 项通过 | 固定二进制配对，含多字提交、非首候选、多窗口、焦点及重连 |

原先 PTY 收到 `ihaoshijie` 的失败已经保留为历史，接收端修复后的记录确认收到完整中文。两次运行实际使用的入口与 terminal 辅助脚本字节相同；旧回执第三项覆盖的是未调用的通用脚本，新回执登记实际调用的 popup 脚本，不能把整份脚本清单说成完全相同。[独立原始回执核对](evidence/ztype-ztty-fixed-runtime-review-20261121.json)及[218 份原始文件与清单组成的证据包](https://drive.google.com/file/d/141WFsEjk1e_TK64v6H6K4odz1Vyc19Nq/view)均已完成哈希核对，云盘整包下载与源文件一致。

候选窗采用浅色界面、16/12/14 像素字号和 20 像素左右留白；选中项有浅蓝底与加粗提示，四组文字对比度最低为 4.919:1。视觉省略只作用于显示副本，完整提交路径保持独立。[只读 UI 审查](evidence/ztype-ui-independent-review-20261121.json)限于浅色、scale 1 和现有截图，不扩大为全面无障碍认证。用户已安装的 0.4.1、输入法配置与系统 compositor 库均保持原样。

**行内预编辑定位修复已合并。** 光标闪烁隐藏时，原 `last_cursor` 会变为 `None`，使预编辑文字回到 `(0,0)`。 [ztty PR #24](https://github.com/LIghtJUNction/ztty/pull/24) 将输入法使用的逻辑光标与闪烁绘制状态分开，实际运行补丁在三个文件增 8 行、删 2 行。运行源码 **49c8024b／27dbb8a5** 完成实际主程序 Clippy、release 编译及构建身份检查，ELF 为 **73e9a96c**。后续 9eaed366 只调整验收脚本；合并提交 **99ef7a0f** 的 **79b48dbf** 树与实际测试树完全一致。

本次私有 Sway 1.12／软件 Mesa EGL 回归共 **16 项通过**：在两处非零行列分别确认初始光标亮／灭，各采样 17 帧、持续超过 1.3 秒，预编辑下划线位置、左上角标记和提示文字稳定；隐藏光标、滚动历史、焦点切换和恢复均符合预期，中文“你好世界”只提交到原有 PTY 一次。位置由真实 PTY 的 DSR 与 CSI16t 响应和画面像素共同核对；没有声称捕获合成器光标矩形协议，也没有给每一合成帧单独标记闪烁相位。四个已知自有进程均退出，scope 已结束、进程组为空、外锁可获取。包含固定 ELF、截图和全部历史尝试的[148 份原始证据包](https://drive.google.com/file/d/1byru2K-yBHIZCPlS9zQCZsmapGML2I7n/view)已完整下载，并逐文件核对大小与哈希。[原始检查](evidence/ztty-pr24-gui-checks-20261121.json)、[构建与合并来源](evidence/ztty-pr24-publication-20261121.json)及[独立复核](evidence/ztty-pr24-independent-review-20261121.json)均已保留。早期两次验收启动问题保持原记录：一次缺少私有合成器路径，一次未能读取已守护化 broker 的标准错误；它们均发生在光标位置断言之前。

**SSMCP 输入与消息处理**：完整原始记录确认这是两个独立参数。`--input` 选择输入来源，默认 `terminal`，并支持 web 的 host／port、MCP 的 stdio／HTTP、默认或自定义 sock 路径及管道输入；用户最新补充，显式 `--input none` 禁用聊天框。`--agent` 指定聊天框消息的处理者，支持 Codex、Claude Code、其他 coding agent 或另一个 SSMCP，默认名称最终更正为 `next-caller`，表示交付到下一次符合条件的工具调用结果。当前源码负责人及原 CLI 线程统一实现。[只读架构核对](evidence/ssmcp-input-agent-contract-20261121.md)已明确输入、处理方、现有消息队列及保存重载的边界，并列出八组建议验收；建议尚未当作已运行结果。前一版报告把 input 解释为处理目标的错误已纠正，未据此修改源码。

[SSMCP 草稿 PR #159](https://github.com/LIghtJUNction/ssmcp/pull/159) 已完成基线的源码为 **781b87df／6bf7beb1**。随后原作者发布了性能候选 **fc06728a／088fe1cd**，其唯一父提交为 781，仅改动四个终端、测试与性能辅助脚本路径，依赖和锁文件未变。[当时的 GitHub 来源读回](evidence/ssmcp-fc-source-observation-20261121.json)确认 PR head 已到 FC；原负责人已用相同构建方法和冻结 r3 夹具完成 FC 的独立构建与配对运行。下列原基线五产物仍专属 781；FC 的构建与运行原件单独保存，二者在下表配对。此前阶段补齐了 `--input none` 的 reload 保持、三种 UI 及 portable attach `--local`；独立 GitHub 差异核对确认，781 只修改一个 `Cargo.toml`，为三个已有文件增加 include 声明，运行源码、脚本、依赖和 gitlink 均未变化。

[实际构建回执](evidence/ssmcp-781-baseline-build-20261121.json)记录三条构建命令全部 exit 0，library test fixture、ssmcp、ssmcp-frontend、ssmcpd 和 vt_snapshot 五个目标均实际重新编译，链接输出、公开目标路径和保留副本大小、哈希一致。协调者此前已重新读取五份保留产物并独立计算哈希。本轮运行报告另外记录四个实际使用产物的前后哈希；没有声称此套件运行了第五个 frontend。

随后实际作业 **6c1** 在同一固定源码与产物上完成全部基线，执行 exit 0、耗时 27.38 秒，quiet lock 正常释放。六个粘贴样本的 **80 项夹具检查**与私有 Ctrl+V 的 **31 项夹具检查**全部通过，输入前后保持一致；这些数字不作为 Rust 单元测试数量。[原始执行回执](evidence/ssmcp-781-complete-baseline/execution-receipt.json)、[六样本报告](evidence/ssmcp-781-complete-baseline/six-cases-report.json)、[Ctrl+V 报告](evidence/ssmcp-781-complete-baseline/ctrlv-report.json)及[独立复核](evidence/ssmcp-781-complete-independent-review-20261121.md)保留完整来源和时钟定义。

FC 的实际构建作业 **73a** 完成三条命令，五个目标均有真实编译及 `fresh=false` 记录；其运行作业 **770** 也已实际 exit 0、双 EOF，六样本 80 项及 Ctrl+V 31 项检查均通过。两版依赖与工具链、输入、断言顺序和冻结夹具哈希一致；源码分别固定为 781 与 FC，后者有上述四路径变化。CLI 与库测试产物变化，frontend、daemon 和 VT decoder 虽真实重编译，字节仍相同。运行套件实际使用四个产物，frontend 只在构建证据范围内。 [新增 Rust 回归范围核对](evidence/ssmcp-fc-new-tests-execution-scope.json)确认七个新测试函数本轮只随 `cargo test --lib --no-run` 编译，尚未取得执行通过结论；80＋31 项输入夹具检查仍单独计数。[候选构建](evidence/ssmcp-fc-complete-candidate/build-receipt.json)与[候选执行](evidence/ssmcp-fc-complete-candidate/execution-receipt.json)保留完整身份链。

| 样本 | 781：首次 PTY 写入至可见完成 | FC：同一定义 |
| --- | ---: | ---: |
| 多行 2,738 B | 67.904495 ms | 14.919875 ms |
| 多行 64 KiB | 34.839222 ms | 28.644784 ms |
| 多行 4 MiB 接受 | 370.222459 ms | 55.933765 ms |
| 4 MiB＋1 B 拒绝 | 337.795869 ms | 44.152384 ms |
| 普通 16 KiB | **2439.160607 ms** | **27.853111 ms** |
| Busy 多行 2,738 B | 43.186361 ms | 29.151625 ms |
| 私有 Ctrl+V 2,738 B | 50.066292 ms | 46.399351 ms |

[独立配对复核](evidence/ssmcp-781-fc-independent-comparison.md)从原始单调时钟时间戳重新计算七项结果，未发现实质不一致。**每类每版只有一次记录**，不能外推统计置信或整套系统稳定倍数。忙碌样本首次反馈 **5.377071 → 29.151625 ms**，超限拒绝的最后写入到完成 **9.789428 → 21.776079 ms**，均变慢；Ctrl+V 的 Preparing 到完成 **34.330081 → 34.711120 ms**。三项 PTY 写入差别仅微秒量级，不据此断言稳定退化。Ctrl+V 整步墙钟 **3.975164 → 5.381131 秒**包含准备、校验和回收，不能与输入完成延迟混用。

Ctrl+V 使用私有假 `wl-paste`，不代表系统剪贴板。Busy 的 producer 在输入前后均继续运行；tick 为 20 → 14，但观察窗口不同，不能解释成吞吐退化。770 总墙钟 193.300145 秒中，169.038702 秒是在等另一合法任务释放 quiet lock；拿锁后至回执完成 24.261430 秒，锁于 **00:02:29.965308 UTC** 释放，等待不计入表中时间。两版八份原始构建／运行 JSON、两份原始 ZIP 及复核组成的 **20 份载荷加一份清单**已[配对归档](https://drive.google.com/file/d/1exRBgnPGqpC9E6j5exa1-1tAOpizbK0V/view)，云盘下载、逐文件及开发机镜像均已核对；[交付证明](evidence/ssmcp-781-fc-paired-evidence-delivery.json)给出完整哈希。


三个早期失败均保留原身份：首轮旧 Next-caller 路由断言停止，第二轮在队列结果转为附件后停止，第三轮五个样本通过但 busy 物理标记未出现在折叠预览中。继任夹具分别修正显式 `target == "next"` 且 `native_recipient == null`、精确完整队列投影，以及相同输出负载中的标记顺序；未放宽输入、超时或完整结果断言。[第三次运行原始观察](evidence/ssmcp-781-third-baseline-observation-20261121.json)没有被覆盖。四路径性能候选的上述对照已闭合；最终主线整合后的运行验收仍按新源码身份执行。

**新主线整合是独立的后续步骤。** 此前 GitHub 固定观察中的 main 为 **f208a03b／7eeb434b**，当时 PR #159 的 781 与它分叉；实际最近共同祖先是 a19ac040。相对该祖先，110 个变化路径中 1 个最终 blob 相同、21 个仅候选变化、64 个仅 main 变化、24 个双方最终 blob 不同。这是对象分类，不是文本冲突数量。[三方审查](evidence/ssmcp-three-way-review-20261121.md)指出：候选 `--agent` 表示聊天消息处理者，main 同名参数表示启动协议加载；必须由原负责人统一命令契约，同时保留 none 的完整消息与重载行为、main 已退休的结束钩子、真实计时和 peer 实现，以及新 Cargo/lock 来源。

既有 v0.10.21 tag 指向 147dae30，属于另一条发布来源，未重指标签。23:48 UTC 的 [v0.10.22 工作流观察](evidence/ssmcp-v22-run-observation-20261121.json)中，总体仍 in_progress，已有两个 Linux 账号流程作业和 Windows ARM 检查失败；其余具体状态逐项记录。原开发机检查点另记录以 f208 为基线的 0.10.23 工作树正在修复这些问题，协调者已将来源差异发给现有负责人。该发布链的结果、781 基线和后续整合候选各自保留身份。 随后的 **00:23:39 UTC** [公开来源观察](evidence/ssmcp-main-f33-observation.json)确认 PR #162 已将 main 推进至 **f33ed8f1／f9bc35bf**，相对 f208 增九个提交、17 个路径，包括 0.10.23 版本／锁、Windows 状态锁和私有显示、验证脚本修正。原负责人随后已发布仅源码整合候选 **24c32869／d8cb76ce**，[GitHub 读回](evidence/ssmcp-24c-source-observation.json)确认 PR #159 仍为草稿；该提交尚未执行新产品门禁。现有负责人正在同一工作链中继续纳入公开 f33，并准备仅源码的 0.10.24 版本后继，再冻结最终组合；FC 输入配对仍属于 FC，另一发布链的构建和发布声明不自动成为本候选的门禁。

退役结束钩子的[原始影响清单](evidence/ssmcp-retired-finish-contract-impact-original.json)已保存：保持 main 对强制续跑、`request_finish`、`ui.finish`、`ui.answer` 的退休，同时保留实际 `ui.reply` 线程结果与普通消息。旧 final25 和 runtime smoke 的预期目录、参数及结束契约需要一致更新，不能恢复旧接口只为通过夹具；P1 自身没有退役 finish 依赖。此清单是只读源码／验收合同审查，未执行新门禁。原件中一处 quiet-wait 文字是生成时的历史观察，当前运行状态以上述 770 实际结束回执为准。

**441 的 CI 成功与本地基线失败分别保留。** 已从 GitHub 独立读取 [run 44826521363](https://github.com/LIghtJUNction/ssmcp/actions/runs/44826521363) 的 completed/success，绑定的 head 是 441814bf；平台明细计数来自作者完整日志读回。该提交的本地 4be 作业中，Cargo library 与 release 均 exit 0，但原始回执在 `preserve-build-release-bins` 阶段因旧输出目录的路径拼接失败，只保留一个 library fixture，产品运行测试为 0。负责人修正产物证明与 recorder 后完成上述唯一 781 r4 构建。22:48 的[进程与锁观察](evidence/ssmcp-781-shared-lock-observation-20261121.json)仍是当时 library 已完成、release 正在编译的历史快照，未改写成最终结果。

更早的 cae35a82 因测试调用缺少布尔参数编译失败，c248d42 修正编译后又因禁用聊天的 reload 回归被负责人取消，均为历史记录。[只读锁诊断](evidence/ssmcp-shared-lock-diagnosis-20261121.json)确认先前 91a 验证进程已退出、外锁曾交给 441；91a 与 441 源码分叉，锁文件相同也不能互换测试结果。781 五产物、完整基线及 FC 性能配对均已完成；整合后原生运行门禁及最终 zcalld Gate10/P1 仍待闭合。本轮候选没有获得正式发布通过结论。


**下游最新来源已重新检查。** 23:43:44 UTC 的[只读快照](evidence/zcalld-ohmy-upstream-observation-20261121.json)确认 zcalld main 已到 **0a0a62cd／69f60a24**，包含安装器验证快照、Windows TCP/ACL/进程处理、0.4.4 版本和内部锁定来源更新。它与 PR #1 的 d531 各有 11 个独有提交，PR 当时 mergeable=false。原 179 项 Rust 和 8 项取消测试仍只属于 d531；[固定三树静态核对](evidence/zcalld-d531-main0a-cross-review-20261121.json)确认唯一交集是 GUI gitlink，原五个监听器 Rust 路径在 main 中保持旧基线内容；新 ca35 又是旧 d357 的后继并适配私有目录权限。因此本轮由原监听器集成者继续作为唯一源码负责人，保留新 main 的完整树和 ca35，再带入五个监听器文件；该来源并入候选 **4cc2fd1c／262cb876**，双父为 d531 与 0a，并已通过 GitHub 插件发布和[逐叶独立核对](evidence/zcalld-262-tree-independent-review.json)。随后 main 的 **37c82ee7** 只新增一份 0.4.4 发布文档；后继对象 **8fe9b42e／65c4d7a3** 已准备并[静态复核](evidence/zcalld-8fe-tree-launcher-independent-review.json)：保留原 219 个叶条目、增加同一文档，相对新 main 仍仅五个监听器 Rust 路径不同。验证启动器只替换六类来源／路径身份，门禁断言和资源约束未变。**8fe 已实际发布**。首次作业 **806** 在 11 个源码／locked metadata／Git 读取命令全部 exit 0 后，因 compat 默认分支从 c521 推进至 56a 而触发来源新鲜度断言，整体 exit 1、双 EOF；尚未进入 fmt、Rust 测试、Clippy、release 构建或八项 curl 测试，产物为 null。[原始回执](evidence/zcalld-8fe-source-guard-original.json)与[差异及清理证明](evidence/zcalld-listener-8fe-source-guard-stop.json)均已保留，scope 和外锁已释放。独立 GitHub 比较确认这一个上游提交只修改 README 中三个 helper 的名称；Core 随后只更新这一 gitlink，已发布 **E1 e1e23cf6／34795b38**，唯一父提交为 8fe。[GitHub 来源读回](evidence/zcalld-e1-source-observation.json)确认差异恰为 compat 指针；[源码复核](evidence/zcalld-e1-pin-independent-review.json)和[启动器参数复核](evidence/zcalld-e1-parameters-independent-review.json)均无阻塞。实际新产品结果仍待 Core 回执，旧 d531 的 179＋8 不迁移到新源码。oh-my-ztty main 为 f04f6ea8、草稿 PR #7 为 a8c97dda；后续传播必须保留 main 的 SSMCP4237 gitlink 与新增验证文档，再纳入最终组件。其旧 112 项检查仍只适用于原 a8 候选。

## 仍需闭合的初始 PR

| 项目 | 当前剩余 |
| --- | --- |
| [KernelSU #1](https://github.com/LIghtJUNction/KernelSU/pull/1) | 大范围上游迁移、设备适配与真实设备验证。 |
| [video-work-api #11](https://github.com/LIghtJUNction/video-work-api/pull/11) | torch/torchaudio 与固定 FunClip/CosyVoice 约束及模型、CUDA 验证。 |
| [zcalld #1](https://github.com/LIghtJUNction/zcalld/pull/1) | compat 仅文档更新已传播至 E1；前次 806 的来源检查中止保留。E1 新产品门禁及最终 SSMCP Gate10/P1 待闭合，d531 的 179＋8 保留历史身份。 |
| [codewhale-lmm-provider #3](https://github.com/TokenNotIncluded/codewhale-lmm-provider/pull/3) | 按用户组隔离的后端接口、客户端注册及真实宿主验收材料。 |
| [lmm-api-source #10](https://github.com/TokenNotIncluded/lmm-api-source/pull/10) | 原定向回归已修复，最终组合验证及真实生产升级材料仍待闭合。 |
| [lmm-api-source #11](https://github.com/TokenNotIncluded/lmm-api-source/pull/11) | 预留未结算与锁超时之间的实际因果关系。 |

维护报告与归档位置：[GitHub PR #7](https://github.com/LIghtJUNction/project-z/pull/7)、[Google 云盘目录](https://drive.google.com/drive/folders/1vjkFko8onQm9WiScrw7QBopK9vNGTLx0)。完整 JSON 保留每个结果对应的源码、命令、日志和验证边界。
