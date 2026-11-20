# Project Z 与 PR 积压维护记录

状态快照：2026-11-20 22:53:40 CST。本文件记录仍在推进中的批次；每条结果均关联具体 PR、提交或验收记录。

## 范围与计数

用户授权继续管理 Project Z、检查开发机，随后增加清理积压 PR、解决冲突及更新项目依赖的任务。初始清单共 85 项。

| 状态 | 初始 PR 数 |
| --- | ---: |
| 已合并 | 52 |
| 已关闭 | 14 |
| 仓库已归档 | 9 |
| 具体阻塞 | 6 |
| 验收／集成中 | 4 |

同一个 PR 只计一次；用于保留原作者提交历史的新集成 PR 单独记录。Pi #16 由原活跃负责人完成合并，本报告对该状态进行了回读，不把它记为本协调者的写入。

## Project Z 与开发机

已完成 43 个组件及嵌套子模块的初始化。第一轮审计选取 23 个更新源码；`sync` 识别 43 个仓库、65 个包。`check` 随后检出 6 处真实的消费者版本或共享源码身份差异，处理记录见 JSON。最终统一源码集合与 `sync`、`check`、`resolve --all` 结果将在本批收尾时写入。

SSMCP 的旧聚合源码与新主线存在历史分叉。核对发现旧隔离桌面、完整 X11 文本投递及私有桌面测试的关键文件已由 PR #113 的 squash 集成保留；旧验收报告继续作为旧提交证据保存。

zuse 选取正式 0.2.2 源码 `94c837551a7a2fd8ec9f577a3e2f57309bd5ce5a`；zi18n 选取正式 0.1.0 源码 `b90984b48465a764bcb699ad2bb3251fa7020024`。后续主线差异仅涉及文档、证据或发行浏览器验证脚本。这些选择保留精确源码身份检查，未放宽验证器。

[zgpui 的上游集成 PR #1](https://github.com/LIghtJUNction/zgpui/pull/1) 保留 ztype 已使用的共享 Linux 字体及独立 raster companion，修复字体位图行距和 packed MONO 边界，并补齐 workspace 与 native 验证。正式合并源码为 `b4d5493e0cd985d00558c7be0b5726965ab5163a`；raster 保持 `publish=false`。zcall-gui、ztype、ztty、zmcl 的传播在独立工作树验收。

开发机 SSMCP 的 `cargo install` 解析故障已修复：父仓库 gitlink 本来要求 zharness 0.6.0，但本地子模块停在 0.5.1；同步到既有精确 gitlink 后，`cargo metadata --locked` 通过。此操作修复源码检出状态，没有替换正在运行的服务。

此前完成的 [Project Z 选择性维护 PR #5](https://github.com/LIghtJUNction/project-z/pull/5) 与 [zmcpio 的 zcall 0.4 迁移 PR #2](https://github.com/LIghtJUNction/zmcpio/pull/2) 继续保留。zmcpio 的新 API 尚未正式发行，后续版本应为 0.5.0；本批没有将它冒称为已发布的 0.4.1。

## 主要合并结果与验证

- sing-box：清理原分支冲突，补齐 OriginalIP 回退的网络策略与错误传播回归。8 个受影响 Go 测试包及 vet 通过；完整构建使用记录中的 `-checklinkname=0` 兼容参数。231 项可更新模块的审计单独保留，没有把广泛大版本迁移算作已经完成。
- Magpie：刷新约束内依赖并修正基准工具与当前只读 hash 归档接口的偏差；549 项 Bun、Harbor、Python 与 Rust SDK 测试通过。
- LMM：两项重叠本地化 PR 保留当前 Pi、CC Switch、凭据隔离及 keyring 行为；最终 129 项 Rust 测试、11 项 Python checker 测试、261 个翻译键检查与严格 Clippy 通过，2 项既有隔离 SecretService 测试保持 opt-in。
- LightFlow / Flux：补齐固定源码 fixture，修复 bindgen 对 C `size_t` 的生成偏差；Flux 的真实 C++ CPU 库、Clippy、12 项非模型测试和 2 项 FFI seam 通过，63 项需模型的测试明确保留 ignored。LightFlow 190 项测试通过，并已传播实际 Flux 合并 SHA。
- Weyriva / BossKit / 视频 API：分别通过 174、243、237 项测试及各自构建／格式／静态检查。
- MSG：完整 48 项测试通过。前期 OOM 与 `/tmp` 内存盘 ENOSPC 均保留日志，随后把本组测试数据迁到磁盘目录完成验证；没有降低断言。

## MagicBox 验收

[PR #4](https://github.com/LIghtJUNction/MagicBox/pull/4) 的冲突修复保留原分支及当前 main 的父提交，统一 Compose 入口、双版本打包及既有 Alpha 制品契约。当前固定源为 `8d6723d3ac0cbe36c1f2e278742b13a551795bd8`。

已通过 25 项打包／promotion 回归、Linux 真实双跳转发、Go 1.26.7 的 Linux 与 Android 双 ABI 构建。UI 与 universal 各 96 项 JVM 测试通过；应用与 instrumentation APK 均已生成，签名、包名、原生隔离、源码资产及 6 个运行时组件哈希校验通过。独立 API 35 模拟器验收仍需以最终记录为准。

## 具体保留项

归档仓库继续保持归档。退休或已由当前行为取代的 PR 按证据关闭；涉及不兼容机器学习依赖、缺失真实设备移植、活跃 API 发行门槛及宿主／后端契约缺口的项目保留明确阻塞。SSMCP 和 native P1 的正式验收由原负责人使用其约定的固定源码集合推进，历史成功记录没有转用于另一组源码。

## 85 项原始清单

下表给出初始清单的逐项状态。JSON 保存完整提交标识、验证范围及阻塞说明。

| PR | 状态 | 合并提交或当前源码 |
| --- | --- | --- |
| [LIghtJUNction/android-mainline-port #1](https://github.com/LIghtJUNction/android-mainline-port/pull/1) | 已合并 | [fedd14889c6c](https://github.com/LIghtJUNction/android-mainline-port/commit/fedd14889c6c65d0a454f6f0ef71715ecd944c0d) |
| [LIghtJUNction/androiduse-zygisk-loader #1](https://github.com/LIghtJUNction/androiduse-zygisk-loader/pull/1) | 已合并 | [248019d3ce9e](https://github.com/LIghtJUNction/androiduse-zygisk-loader/commit/248019d3ce9edc4d1d0720fef2ff79e0c335c6ef) |
| [LIghtJUNction/AstrBotCanary #2](https://github.com/LIghtJUNction/AstrBotCanary/pull/2) | 仓库已归档 | [765b89c99e92](https://github.com/LIghtJUNction/AstrBotCanary/commit/765b89c99e92b77f896d287d690eeee94a703010) |
| [LIghtJUNction/AstrBotCanary #3](https://github.com/LIghtJUNction/AstrBotCanary/pull/3) | 仓库已归档 | [3334c2d64324](https://github.com/LIghtJUNction/AstrBotCanary/commit/3334c2d643243fba3e5758b49cca4f3071da4e30) |
| [LIghtJUNction/AstrBotCanary #4](https://github.com/LIghtJUNction/AstrBotCanary/pull/4) | 仓库已归档 | [19152a0f7644](https://github.com/LIghtJUNction/AstrBotCanary/commit/19152a0f7644308859ad7760e9c9d3d955931acb) |
| [LIghtJUNction/AstrBotCanary #5](https://github.com/LIghtJUNction/AstrBotCanary/pull/5) | 仓库已归档 | [59d741daff3c](https://github.com/LIghtJUNction/AstrBotCanary/commit/59d741daff3c91326a4b128b33040e1f5a0251e9) |
| [LIghtJUNction/AstrBotCanary #6](https://github.com/LIghtJUNction/AstrBotCanary/pull/6) | 仓库已归档 | [a421d93ed57d](https://github.com/LIghtJUNction/AstrBotCanary/commit/a421d93ed57d57a81a1d9b278e2f34b3b074c55b) |
| [LIghtJUNction/blog #28](https://github.com/LIghtJUNction/blog/pull/28) | 仓库已归档 | [181721f992e5](https://github.com/LIghtJUNction/blog/commit/181721f992e5d007adf12185d34152062f0bda99) |
| [LIghtJUNction/blog #29](https://github.com/LIghtJUNction/blog/pull/29) | 仓库已归档 | [900190385e5e](https://github.com/LIghtJUNction/blog/commit/900190385e5e0cd846e1df58e7bb2818f30ebab8) |
| [LIghtJUNction/blog #30](https://github.com/LIghtJUNction/blog/pull/30) | 仓库已归档 | [4ac28004b3dc](https://github.com/LIghtJUNction/blog/commit/4ac28004b3dc9436704ff206e04eb5185fd6233d) |
| [LIghtJUNction/BossKit #4](https://github.com/LIghtJUNction/BossKit/pull/4) | 已合并 | [eef9a1a82223](https://github.com/LIghtJUNction/BossKit/commit/eef9a1a82223da48901f6541091ea810860dcfd6) |
| [LIghtJUNction/codensity #4](https://github.com/LIghtJUNction/codensity/pull/4) | 已合并 | [64a23d1db979](https://github.com/LIghtJUNction/codensity/commit/64a23d1db979d4ec777b80c2cb9f76a51ca60909) |
| [LIghtJUNction/codensity #5](https://github.com/LIghtJUNction/codensity/pull/5) | 已合并 | [327ffb1a9123](https://github.com/LIghtJUNction/codensity/commit/327ffb1a91239a9c11b28f92ba5f5195f13972d0) |
| [LIghtJUNction/codex-sync #1](https://github.com/LIghtJUNction/codex-sync/pull/1) | 已合并 | [4e2762f60e51](https://github.com/LIghtJUNction/codex-sync/commit/4e2762f60e51eb83485df7d1568dfa0bff7dd75a) |
| [LIghtJUNction/cortexfs #334](https://github.com/LIghtJUNction/cortexfs/pull/334) | 已关闭 | [b3eb1ee94d8b](https://github.com/LIghtJUNction/cortexfs/commit/b3eb1ee94d8bc77f7ae7adb38d9f783dfe56d35c) |
| [LIghtJUNction/cortexfs #335](https://github.com/LIghtJUNction/cortexfs/pull/335) | 已关闭 | [3e9c340f22e1](https://github.com/LIghtJUNction/cortexfs/commit/3e9c340f22e17937a841bde3b8717fe8a5099b5b) |
| [LIghtJUNction/cortexfs #338](https://github.com/LIghtJUNction/cortexfs/pull/338) | 已关闭 | [767e130cbcbd](https://github.com/LIghtJUNction/cortexfs/commit/767e130cbcbd3bb926c89862a879f81fbb622dcf) |
| [LIghtJUNction/cortexfs #339](https://github.com/LIghtJUNction/cortexfs/pull/339) | 已关闭 | [99d1efe4eee3](https://github.com/LIghtJUNction/cortexfs/commit/99d1efe4eee315ea7f97f89bf2ec0348212bfec9) |
| [LIghtJUNction/cortexfs #340](https://github.com/LIghtJUNction/cortexfs/pull/340) | 已关闭 | [405048addb82](https://github.com/LIghtJUNction/cortexfs/commit/405048addb82f5e1ae5e898ec3a038b641332917) |
| [LIghtJUNction/cortexfs #343](https://github.com/LIghtJUNction/cortexfs/pull/343) | 已关闭 | [7c765e5e1e87](https://github.com/LIghtJUNction/cortexfs/commit/7c765e5e1e878423779edb875c8d14bc44862b4a) |
| [LIghtJUNction/cortexfs #344](https://github.com/LIghtJUNction/cortexfs/pull/344) | 已关闭 | [c7d2502c2cb4](https://github.com/LIghtJUNction/cortexfs/commit/c7d2502c2cb4513f8a5fe8c5e404d4ccdf99c1f5) |
| [LIghtJUNction/dash.astrbot.men #11](https://github.com/LIghtJUNction/dash.astrbot.men/pull/11) | 已合并 | [c3181926f71b](https://github.com/LIghtJUNction/dash.astrbot.men/commit/c3181926f71b9d43e5f675c84f44474a3998ea8d) |
| [LIghtJUNction/dsh-context-folding #1](https://github.com/LIghtJUNction/dsh-context-folding/pull/1) | 已合并 | [3141e803cffe](https://github.com/LIghtJUNction/dsh-context-folding/commit/3141e803cffe2f7791fd271cf8b8816bac6a096f) |
| [LIghtJUNction/emailctl #4](https://github.com/LIghtJUNction/emailctl/pull/4) | 已合并 | [ce023dbc7c9d](https://github.com/LIghtJUNction/emailctl/commit/ce023dbc7c9d8850feb8d65b71d4c716e2c786e6) |
| [LIghtJUNction/go.lmm.best #2](https://github.com/LIghtJUNction/go.lmm.best/pull/2) | 已合并 | [58c978ecd1e4](https://github.com/LIghtJUNction/go.lmm.best/commit/58c978ecd1e406f621f47242d32a6e017fc83524) |
| [LIghtJUNction/KernelSU #1](https://github.com/LIghtJUNction/KernelSU/pull/1) | 具体阻塞 | [e0d6ead7f04d](https://github.com/LIghtJUNction/KernelSU/commit/e0d6ead7f04d6f78abc8fe98aebb27c119040972) |
| [LIghtJUNction/lab-safety-system #10](https://github.com/LIghtJUNction/lab-safety-system/pull/10) | 已合并 | [8aa1674daf00](https://github.com/LIghtJUNction/lab-safety-system/commit/8aa1674daf001905e8911a106ddba035bbd1f51f) |
| [LIghtJUNction/lab-safety-system-frontend #6](https://github.com/LIghtJUNction/lab-safety-system-frontend/pull/6) | 已合并 | [9529c575f435](https://github.com/LIghtJUNction/lab-safety-system-frontend/commit/9529c575f43534b93f0c48cc251bf63d8df0cc40) |
| [LIghtJUNction/LightFlow #61](https://github.com/LIghtJUNction/LightFlow/pull/61) | 已合并 | [ba52a3cfdd23](https://github.com/LIghtJUNction/LightFlow/commit/ba52a3cfdd234eeb0206d70d02e63c59aeb478c0) |
| [LIghtJUNction/lightflow-flux #2](https://github.com/LIghtJUNction/lightflow-flux/pull/2) | 已合并 | [748dc404c940](https://github.com/LIghtJUNction/lightflow-flux/commit/748dc404c94003e4aa9472456248408b011f2c50) |
| [LIghtJUNction/MagicBox #4](https://github.com/LIghtJUNction/MagicBox/pull/4) | 验收／集成中 | [8d6723d3ac0c](https://github.com/LIghtJUNction/MagicBox/commit/8d6723d3ac0cbe36c1f2e278742b13a551795bd8) |
| [LIghtJUNction/magicnet-android #5](https://github.com/LIghtJUNction/magicnet-android/pull/5) | 已合并 | [387fe9ec7aba](https://github.com/LIghtJUNction/magicnet-android/commit/387fe9ec7aba14033e2c6ac1c23dca19ae6bff8d) |
| [LIghtJUNction/magpie-context-folding #9](https://github.com/LIghtJUNction/magpie-context-folding/pull/9) | 已关闭 | [e79305030714](https://github.com/LIghtJUNction/magpie-context-folding/commit/e793050307149e8ebbf91776491a3010799b8d33) |
| [LIghtJUNction/magpie-context-folding #13](https://github.com/LIghtJUNction/magpie-context-folding/pull/13) | 已关闭 | [0c85ab62b80d](https://github.com/LIghtJUNction/magpie-context-folding/commit/0c85ab62b80d3e8a9fa41f0cfd7658e0381bf944) |
| [LIghtJUNction/magpie-context-folding #15](https://github.com/LIghtJUNction/magpie-context-folding/pull/15) | 已关闭 | [11dca8537276](https://github.com/LIghtJUNction/magpie-context-folding/commit/11dca8537276709819f0d3c93ea2aceef601be4f) |
| [LIghtJUNction/magpie-context-folding #18](https://github.com/LIghtJUNction/magpie-context-folding/pull/18) | 已合并 | [c049157242d2](https://github.com/LIghtJUNction/magpie-context-folding/commit/c049157242d2d055e75834261fcdaa0deb7b5023) |
| [LIghtJUNction/magpie-rs-source #4](https://github.com/LIghtJUNction/magpie-rs-source/pull/4) | 已合并 | [8aef4dc63960](https://github.com/LIghtJUNction/magpie-rs-source/commit/8aef4dc63960863799669005f767f774804c26c4) |
| [LIghtJUNction/matchplane #46](https://github.com/LIghtJUNction/matchplane/pull/46) | 仓库已归档 | [b230de1283ca](https://github.com/LIghtJUNction/matchplane/commit/b230de1283ca34fbdd55f867edc67b38e0ef2a9d) |
| [LIghtJUNction/mechrevo-drivers #5](https://github.com/LIghtJUNction/mechrevo-drivers/pull/5) | 已关闭 | [2592a1fef987](https://github.com/LIghtJUNction/mechrevo-drivers/commit/2592a1fef987a62b5721d4d6d9bc11897500883a) |
| [LIghtJUNction/Mimic-Node #11](https://github.com/LIghtJUNction/Mimic-Node/pull/11) | 已合并 | [f1e71cf5edf0](https://github.com/LIghtJUNction/Mimic-Node/commit/f1e71cf5edf05e978ad22b1700314a1b61a452c4) |
| [LIghtJUNction/Mimic-Node #12](https://github.com/LIghtJUNction/Mimic-Node/pull/12) | 已合并 | [4d7370f21d4f](https://github.com/LIghtJUNction/Mimic-Node/commit/4d7370f21d4fbf285c1cefec08949cabbce1d337) |
| [LIghtJUNction/Mimic-Node #13](https://github.com/LIghtJUNction/Mimic-Node/pull/13) | 已合并 | [0b7151e92282](https://github.com/LIghtJUNction/Mimic-Node/commit/0b7151e92282dc1b0e649a3e82769885ebc9d580) |
| [LIghtJUNction/Mimic-Node #14](https://github.com/LIghtJUNction/Mimic-Node/pull/14) | 已合并 | [d7e9082e45fd](https://github.com/LIghtJUNction/Mimic-Node/commit/d7e9082e45fdc4c9deafdb3aca252e38298a494e) |
| [LIghtJUNction/sing-box #355](https://github.com/LIghtJUNction/sing-box/pull/355) | 已合并 | [06eaf4aeae04](https://github.com/LIghtJUNction/sing-box/commit/06eaf4aeae04bb51609a5202e114244c142fbb61) |
| [LIghtJUNction/sing-box #356](https://github.com/LIghtJUNction/sing-box/pull/356) | 已关闭 | [90cbec409ec9](https://github.com/LIghtJUNction/sing-box/commit/90cbec409ec98caf684a85bdbe3f82611aa04add) |
| [LIghtJUNction/sing-box #357](https://github.com/LIghtJUNction/sing-box/pull/357) | 已关闭 | [5c2c000cde46](https://github.com/LIghtJUNction/sing-box/commit/5c2c000cde4612c69f31c1449fe3c91d6d2aaa8c) |
| [LIghtJUNction/sing-box #358](https://github.com/LIghtJUNction/sing-box/pull/358) | 已合并 | [237850717abe](https://github.com/LIghtJUNction/sing-box/commit/237850717abea766c234e4c5e66ce9be41ec5cf2) |
| [LIghtJUNction/sing-box #759](https://github.com/LIghtJUNction/sing-box/pull/759) | 已合并 | [7f97a54c2c25](https://github.com/LIghtJUNction/sing-box/commit/7f97a54c2c25cf36cc00ec8a918b37f310d568ae) |
| [LIghtJUNction/sing-box #760](https://github.com/LIghtJUNction/sing-box/pull/760) | 已合并 | [0157843d264c](https://github.com/LIghtJUNction/sing-box/commit/0157843d264c06e54c6bcc4f46e6dde5e68e50b0) |
| [LIghtJUNction/sing-box #761](https://github.com/LIghtJUNction/sing-box/pull/761) | 已合并 | [a0369fe08f21](https://github.com/LIghtJUNction/sing-box/commit/a0369fe08f21d5e8f080cdafd18713ddf26c24b7) |
| [LIghtJUNction/sing-box #762](https://github.com/LIghtJUNction/sing-box/pull/762) | 已合并 | [514d112b05b3](https://github.com/LIghtJUNction/sing-box/commit/514d112b05b346b0efcdfccc20da51c4714838eb) |
| [LIghtJUNction/sing-box #763](https://github.com/LIghtJUNction/sing-box/pull/763) | 已合并 | [61c0a37d9772](https://github.com/LIghtJUNction/sing-box/commit/61c0a37d97726d44dc530020ca717a1d2d3b1f2d) |
| [LIghtJUNction/sing-box #764](https://github.com/LIghtJUNction/sing-box/pull/764) | 已合并 | [d35cc9cb1ae9](https://github.com/LIghtJUNction/sing-box/commit/d35cc9cb1ae9196fb54de23d338e703d7e8bc895) |
| [LIghtJUNction/sing-box #805](https://github.com/LIghtJUNction/sing-box/pull/805) | 已合并 | [819226241929](https://github.com/LIghtJUNction/sing-box/commit/8192262419295dcd2a217f62167cd450fc50cf85) |
| [LIghtJUNction/sing-box #2958](https://github.com/LIghtJUNction/sing-box/pull/2958) | 已合并 | [9fd9791d4564](https://github.com/LIghtJUNction/sing-box/commit/9fd9791d4564d2375244c448678722b3a7bcb911) |
| [LIghtJUNction/ssmcp #119](https://github.com/LIghtJUNction/ssmcp/pull/119) | 验收／集成中 | — |
| [LIghtJUNction/video-work-api #11](https://github.com/LIghtJUNction/video-work-api/pull/11) | 具体阻塞 | [b78012904aa9](https://github.com/LIghtJUNction/video-work-api/commit/b78012904aa9054b582033808f41cab018b72e38) |
| [LIghtJUNction/video-work-api #12](https://github.com/LIghtJUNction/video-work-api/pull/12) | 已合并 | [8b85d18f4936](https://github.com/LIghtJUNction/video-work-api/commit/8b85d18f49368097488c7ef0ce046aba7aa4a776) |
| [LIghtJUNction/weyriva-shell #4](https://github.com/LIghtJUNction/weyriva-shell/pull/4) | 已合并 | [6a79f3f59d80](https://github.com/LIghtJUNction/weyriva-shell/commit/6a79f3f59d80456d6930566fe7fe8687177ec209) |
| [LIghtJUNction/zcalld #1](https://github.com/LIghtJUNction/zcalld/pull/1) | 验收／集成中 | — |
| [LIghtJUNction/zcalld-compat #1](https://github.com/LIghtJUNction/zcalld-compat/pull/1) | 已合并 | [ec2a19fdec71](https://github.com/LIghtJUNction/zcalld-compat/commit/ec2a19fdec71f8016307240903fadaf4f6b6d845) |
| [LIghtJUNction/zcalld-compat #2](https://github.com/LIghtJUNction/zcalld-compat/pull/2) | 已合并 | [bd01b740ba7e](https://github.com/LIghtJUNction/zcalld-compat/commit/bd01b740ba7e0d15a8dd3a8dee518e71eebdcb20) |
| [TokenNotIncluded/codewhale-lmm-provider #3](https://github.com/TokenNotIncluded/codewhale-lmm-provider/pull/3) | 具体阻塞 | [67f059fa5c57](https://github.com/TokenNotIncluded/codewhale-lmm-provider/commit/67f059fa5c577a523a6ef292cfa9fe76dbaf91b0) |
| [TokenNotIncluded/hireferry #21](https://github.com/TokenNotIncluded/hireferry/pull/21) | 具体阻塞 | [89120ef07e45](https://github.com/TokenNotIncluded/hireferry/commit/89120ef07e4558cb2e7d7c7ac1ab186c65217100) |
| [TokenNotIncluded/hireferry #22](https://github.com/TokenNotIncluded/hireferry/pull/22) | 已合并 | [397addaaeb95](https://github.com/TokenNotIncluded/hireferry/commit/397addaaeb9568063f7f3806d3835ae035aff871) |
| [TokenNotIncluded/hireferry #24](https://github.com/TokenNotIncluded/hireferry/pull/24) | 验收／集成中 | — |
| [TokenNotIncluded/lmm #1](https://github.com/TokenNotIncluded/lmm/pull/1) | 已合并 | [166bd76f1473](https://github.com/TokenNotIncluded/lmm/commit/166bd76f147348553940f0fa657e9f53fc7ae860) |
| [TokenNotIncluded/lmm #2](https://github.com/TokenNotIncluded/lmm/pull/2) | 已合并 | [755c98664b72](https://github.com/TokenNotIncluded/lmm/commit/755c98664b72943552fc7adb1ef5888086513427) |
| [TokenNotIncluded/lmm #3](https://github.com/TokenNotIncluded/lmm/pull/3) | 已合并 | [b0587b003c8b](https://github.com/TokenNotIncluded/lmm/commit/b0587b003c8b4a3b9b3699f7f30ed76052c19a91) |
| [TokenNotIncluded/lmm-api-source #10](https://github.com/TokenNotIncluded/lmm-api-source/pull/10) | 具体阻塞 | [bbf72df77a6c](https://github.com/TokenNotIncluded/lmm-api-source/commit/bbf72df77a6c144462fc17976a586b4ea4d5b51b) |
| [TokenNotIncluded/lmm-api-source #11](https://github.com/TokenNotIncluded/lmm-api-source/pull/11) | 具体阻塞 | [2ee27e8efe51](https://github.com/TokenNotIncluded/lmm-api-source/commit/2ee27e8efe51c58460251de80ea2522e71b388af) |
| [TokenNotIncluded/msg #246](https://github.com/TokenNotIncluded/msg/pull/246) | 已关闭 | [9c44fe981fab](https://github.com/TokenNotIncluded/msg/commit/9c44fe981fabe89921a595fac73f3668eac139d2) |
| [TokenNotIncluded/msg #247](https://github.com/TokenNotIncluded/msg/pull/247) | 已合并 | [446e206cc653](https://github.com/TokenNotIncluded/msg/commit/446e206cc6533cc8e9ff81020e72a55bb2c1bfab) |
| [TokenNotIncluded/msg #248](https://github.com/TokenNotIncluded/msg/pull/248) | 已合并 | [c71a41d8b2b3](https://github.com/TokenNotIncluded/msg/commit/c71a41d8b2b3601c63e734c344c8e58b5a52b676) |
| [TokenNotIncluded/pay.lmm.best #4](https://github.com/TokenNotIncluded/pay.lmm.best/pull/4) | 已合并 | [272aa59c4658](https://github.com/TokenNotIncluded/pay.lmm.best/commit/272aa59c465862966c41a65c7636ae49de2e1375) |
| [TokenNotIncluded/pay.lmm.best #5](https://github.com/TokenNotIncluded/pay.lmm.best/pull/5) | 已合并 | [7732e4de0282](https://github.com/TokenNotIncluded/pay.lmm.best/commit/7732e4de02824911cf841c862891633dbfbf4083) |
| [TokenNotIncluded/pay.lmm.best #6](https://github.com/TokenNotIncluded/pay.lmm.best/pull/6) | 已合并 | [249b52b46541](https://github.com/TokenNotIncluded/pay.lmm.best/commit/249b52b46541138c9181198f6cc8e89b9ccd2c5e) |
| [TokenNotIncluded/pay.lmm.best #7](https://github.com/TokenNotIncluded/pay.lmm.best/pull/7) | 已合并 | [3a017f8f33f7](https://github.com/TokenNotIncluded/pay.lmm.best/commit/3a017f8f33f75f8247bf296bbc2511a8faca4e1f) |
| [TokenNotIncluded/pay.lmm.best #8](https://github.com/TokenNotIncluded/pay.lmm.best/pull/8) | 已合并 | [91e6d47902c9](https://github.com/TokenNotIncluded/pay.lmm.best/commit/91e6d47902c91a74b53e4dae4ab8a2a1ab675f15) |
| [TokenNotIncluded/pay.lmm.best #10](https://github.com/TokenNotIncluded/pay.lmm.best/pull/10) | 已合并 | [56ed5b917138](https://github.com/TokenNotIncluded/pay.lmm.best/commit/56ed5b9171389717efe8dd37cb1db93167b9f3da) |
| [TokenNotIncluded/pay.lmm.best #12](https://github.com/TokenNotIncluded/pay.lmm.best/pull/12) | 已合并 | [f02ac67bd1f1](https://github.com/TokenNotIncluded/pay.lmm.best/commit/f02ac67bd1f1b22a7e34c9885405d0690074b360) |
| [TokenNotIncluded/pay.lmm.best #13](https://github.com/TokenNotIncluded/pay.lmm.best/pull/13) | 已合并 | [2207a0e87941](https://github.com/TokenNotIncluded/pay.lmm.best/commit/2207a0e879417801926b8a7d7d20bdf01f5d0dab) |
| [TokenNotIncluded/pay.lmm.best #14](https://github.com/TokenNotIncluded/pay.lmm.best/pull/14) | 已合并 | [3f10f0c7883f](https://github.com/TokenNotIncluded/pay.lmm.best/commit/3f10f0c7883f554ba26dceb52780830b1bd1a44f) |
| [TokenNotIncluded/pi-lmm-provider #15](https://github.com/TokenNotIncluded/pi-lmm-provider/pull/15) | 已合并 | [198ba195fc58](https://github.com/TokenNotIncluded/pi-lmm-provider/commit/198ba195fc58c2e6fc2a65333aad7a580b0fa413) |
| [TokenNotIncluded/pi-lmm-provider #16](https://github.com/TokenNotIncluded/pi-lmm-provider/pull/16) | 已合并 | [b5eb63210611](https://github.com/TokenNotIncluded/pi-lmm-provider/commit/b5eb63210611ddb1bc0ca8255b87a13905212e62) |

## 证据使用边界

本记录分别标注源码、构建、合成 fixture、真实本机进程、模拟器和正式发行的验证范围。未执行的硬件、生产服务、真实支付或正式发布步骤仍需各自的验收记录。
