# Project Z：消费者验收与下一轮固定版本

记录时间：2026-11-20 03:18 UTC。本记录承接已经合入 main 的 [PR #3](https://github.com/LIghtJUNction/project-z/pull/3)。当前正式聚合基线为 `46e98822e8357b25670cea52794af3009d66660f`；本文列出的新候选尚未因报告入库而自动改变聚合 Gitlink。

## 已经成立的事实

统一清单已经覆盖 42 个仓库、60 个 Cargo 包。协调器的 80 项回归及原快照中 36 个 Rust 仓库的实际依赖解析通过。它解决的是“这些仓库应当使用哪一组源码和版本”：库、应用、运行时和安装套件分别保留自己的发布边界。完整机制和原始证据见[协调层报告](shared-cohort-20261120.zh-CN.md)。

本轮继续收集实际消费者和正式发布证据。下列三处来源已经有足以进入协调层候选的源码审计；独立检出中的全图同步、检查与解析仍在执行，完成后再更新固定项。

| 仓库 | 当前聚合固定 | 下一候选 | 已核对的证据 |
| --- | --- | --- | --- |
| OniMods | `f0819fa207c5` | `14dba75a5752c3142039a8660ce37cdf57d7082a` | 完整变化范围、71 项 Rust、Jlib 2,391 项断言及四个发布构建步骤；游戏场景与 Workshop 上传另计 |
| zterm | `13d5e2c74571`，0.5.0 | `a2074bac4c030cfd7c0b2514c852a89dcf54648f`，0.5.1 | 正式 tag、注册表实际 crate、包内 37 个文件、三系统正式构建测试 |
| ztty | `1a2f165983d7` | `9f5a77a1299093d0ba609bfafa2cec3b0ba931dd` | 472 项 Rust、另次 6 项 EGL、21 阶段共 365 项 GUI，以及六条实际 registry 消费命令 |

来源与边界分别保存在 [OniMods 采纳审计](../evidence/2026-11-20/onimods-f081-to-14d-acceptance.json)、[zterm 发布与 ztty 消费审计](../evidence/2026-11-20/zterm-0.5.1-propagation-audit.json)、[ztty 后续 GUI 收口](../evidence/2026-11-20/ztty-9f5-gui-increment.json)。zterm 审计记录早于最终 GUI 收口，两份记录保留各自时间，后者补足已完成结果。

zterm 0.5.1 的实际下载包为 78,051 字节，SHA-256 为 `fc48bcaf9892a77d17ab235316448c3e235b0dccd00e5963b542586585c26c91`。ztty 对应锁文件 SHA-256 为 `b86e3438a14ff8710a28b09bafa33ab1861f8cf116b722dc94be83133d4543b5`。应用 0.5.0 正式发布和 oh-my-ztty 安装传播尚未闭合；功能验收也没有消除先前已测出的终端性能回退。

## SSMCP：构建完成，原生行为仍待验收

新组合的实际构建源码固定为 `c44c2cfecb6ba5dae3a63d67a3af08c77eb7b2cc`，聚合暂仍固定 `ecc450f`。候选把应用输入适配改为整段文本送达，并修复私有显示分配与辅助功能总线继承。原生预检已通过 73 项发布脚本测试、格式与 GTK C 语法；之前 Clippy 受全机余量门槛停止的记录保持不变。

同一份源码与锁文件已在独立云工作区通过 Clippy、测试程序和 CLI/daemon/插件夹具构建。实际运行结果为：

| 阶段 | 结果 | 解释 |
| --- | --- | --- |
| computer 单元集合 | 44 通过、2 失败、9 忽略 | 两项失败均在 Unix socket bind 遭遇 EPERM，不能把整个集合记为通过 |
| PTY | 4/4 通过 | 真实 PTY 的隔离、输入输出、关闭及参数边界 |
| MCP 账户与终端集合 | 先完成 69 项检查，整套未通过 | 第一条 code_mode terminal.write 被 bwrap NETLINK_ROUTE EPERM 阻断 |
| 原机二进制传输 | 摘要、逐个 ELF 散列与动态链接检查通过 | 使用实际冻结二进制，未在原机重编译 |
| 两个原生 socket 用例 | 未启动 | 03:09:18 UTC 可用内存低于该 128 MiB 任务的准入门槛；保留 exit 75 收据 |

完整白名单结果见 [SSMCP 云与原机交接回执](../evidence/2026-11-20/ssmcp-c44-cloud-validation.json)，并可回读[原仓库同一文件](https://github.com/LIghtJUNction/ssmcp/blob/be64c61bc6baf296fd18daaf7624362a03eef955/docs/reports/shared-cohort-20261120/cloud-validation.json)。云环境不支持的系统调用没有通过修改测试、认证或隔离规则绕开。

下一步仍是对冻结程序完成原生输入、同一 Computer 恢复与取消、私有桌面清理和 MCP 行为验收。编译通过不能替代这些操作确实正确。

## 正式应用与安装套件的传播

已核对的 SSMCP 正式版本仍为 0.10.13。旧发布候选与新 c44 组合均标记包版本 0.10.14，但它们的源码、zuse、zharness 和 zplugin 依赖不同，必须分别追踪。不能把旧候选的制品验收交给新候选使用，或覆盖已建立的 tag。

已安装 oh-my-ztty 0.2.1 的固定来源仍为 `7b69b751772a839f090e408228d94f810fd96d1e`，其发行锁仍引用 SSMCP 0.10.10 和 ztty 0.4.1。套件更新需要正式 tag 对应的源码、两个架构的真实附件与摘要，再完成 bundle 和安装验收。zrc 的真实连接还须核对 Neovim 实际找到的 ssmcp 路径、散列与行为；单改源码 Gitlink 不会改变这条执行链。详见[安装传播核查](../evidence/2026-11-20/ssmcp-installation-propagation.json)。

## 其他并行接续

zcalld 已出现正式 [0.2.0](https://github.com/LIghtJUNction/zcalld/releases/tag/v0.2.0) 和 [0.2.1](https://github.com/LIghtJUNction/zcalld/releases/tag/v0.2.1)；后者 tag 对应 `b853e264eced9fbd25120d261eb188a3a8e3b1df`，并配套 compat 0.1.4。原聚合仍固定 `c72a1cb9`。完整差异包括隐私历史事务、worker 审计和 builtin 初始化修复，正在独立审计。先前一次部署在 legacy MCP tools/list 验收失败后回滚；最新正式发布不能单独证明主机已完成接管，当前服务结果由唯一部署负责人提供回执。

固定版本的 zgpui/GPUI CPU 对照已完成第一次 release 构建。独立几何检查发现 GPUI 夹具把根宽度留为 Auto，未表达预期 viewport 宽度，第一例得到宽度 0 而独立预期为 32。失败程序与记录保留在 [68de 回执](https://github.com/LIghtJUNction/zgpui/blob/36689a61901bd6fa05f1e1cfed4e4b25149605c0/benchmarks/gpui-comparison/resource-gates/20261120T030008Z/build-and-geometry.json)。夹具显式设为 100% 根宽度后，第二次 release 构建通过，但相同几何门禁进一步发现测试窗口默认倍率为 2.0，而布局写入与读取使用 1.0，首例得到 64 而非 32。正通过既有公开 test-support API 将测试窗口统一设为 1.0，再运行相同门禁。两次失败均按真实程序保留；独立预期、两库算法、锁文件与优化参数不变。当前没有性能样本，不作领先结论。

## 后续提交规则

新来源先通过对应范围的真实验证，再更新聚合 Gitlink、版本清单和生成文件。库更新沿直接与传递消费者继续传播到应用和安装套件；对未完成项保留负责人、不可变来源、实际阻碍和下一步。日常验证在本地执行，正式构建、发布和部署继续使用其专门流程。
