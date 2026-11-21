# U/r12、bd7 与 zuse 后继报告独立审阅

**结论：0 项实质不一致，0 项发布阻断。** 本次审阅固定于 **2026-11-21 03:42:51 UTC（台北 11:42:51）** 的报告候选。作者封存的 31 份文件保持原样；另有一份已经核实的 zuse CI 详情 JSON，由发布负责人作为第 32 份文本加入，补齐证据内部的相对引用。加上本审阅两份文件，拟发布集为 34 份文本。最终 GitHub 提交与远端读回由发布负责人完成。

完整字段、证据身份和范围见 [独立审阅 JSON](U-r12-bd7-report-independent-review.json)。被审主报告为 [维护报告](../2026-11-20-pr-and-dependencies.md) 和 [结构化报告](../2026-11-20-pr-and-dependencies.json)。

## 1. 文件、旧记录与引用

独立读取 GitHub 基线提交 `33fd62fdbb376b6b64f14e604a63452abc654a1b`、树 `903c194f17396292f4780a4729171196250bf70a` 的完整 352 叶清单后，与候选逐项核对。31 份文件的字节数、SHA-256 和 Git blob 均匹配；其中 28 份复制原件与其实际来源逐字节相同。

原 352 个路径全部保留：350 个旧叶的完整条目不变，2 份主报告更新，新增 29 叶，构成作者候选的 381 叶。报告增量没有修改产品源码、gitlink、目录清单或工作流。原始 85 项分类仍为 **56 已合并、14 已关闭、9 已归档、5 具体阻塞、1 验收／集成中**；旧图、组件集成、Q/r11 里程碑、C 的失败记录及 FC、0af8 原有身份没有被新结果替换。移入历史快照的 15 项旧状态字段与基线原值全部相同，包括早前不可访问的 cloud Q 候选“未独立审阅、未声称原字节恢复”的边界。

主报告的 132 处 Markdown 引用、432 处结构化 JSON 引用和 438 处字符串引用均解析成功。这三个计数不包含被引用 JSON 内部的所有字段。zuse 独审原件的 `$.details_file` 指向 [ci-extracted-results.json](zuse-67e-ci-44860554142/ci-extracted-results.json)，作者 31 文件清单未复制它；本次已核实实际原件 **32,092 B / SHA-256 caee487d2c9874bebc6f9a4dbfccb94e3b1906a127f3c5df6a780b16eb34c1c5**，发布负责人确认全文读回一致并加入第 32 份载荷。无需为此复制三份完整 CI 日志或未发布的 CI 审阅 Markdown。

主 JSON 为 **1,011,176 B**，较基线增加 **18,986 B**，距 1 MiB 尚余 **37,400 B**。上述引用统计和字节核对是文档审阅结果，不是产品测试数量。

## 2. SSMCP U 的三个验收范围

[U/r12 Gate 独审摘要](ssmcp-U-r12-gate-review/ssmcp-U-r12-gate-review-summary.json) 固定源码 `784370b5fe1b817c788273a5f7b1ab826c743965`、树 `2c60d011da8c2b31aefd80367bf7f19e28f10b62`。U 自身实际 35 阶段全部退出 0，包含 26 个 Rust 父结果阶段；没有继承 Q 的运行成绩。私有库结果为 2050 passed、0 failed、23 ignored、6 filtered，宿主输入组另为 6 passed。19 个普通集成目标合计 101 passed，指定 worker 再有 1 passed；额外强制 ignored 组为 4 阶段、14 passed。原 17 项是 2050 内部子集，嵌套子进程结果不重复计数。

两次严格 Clippy 通过，同时保留 unused qrcodegen manifest warning。U 独审原件已经建立其 212 份文本、35 日志、55 probe 对、26 编译链和 5 份受控产物的来源关系；本次只核报告与这些既有证据的一致性，没有再散列大型 ELF 或重跑整套门禁。已收集的 unit 状态、原 PID 消失及锁释放是有时间范围的观察，不等于持续或全局空闲。

[Runtime18 回执](ssmcp-U-r12-runtime18/runtime18-root-receipt-read.json) 支持后续 **12 项私有 MCP + 6 项传输检查通过**，同 U 身份、输入前后相同，受控进程已清理。回执明确没有再次读取五个 ELF 本体，实际 job ac8 标识来自原执行者而非本次 root 读取其输出；报告保留了这个范围。

[首次 UI 失败回执](ssmcp-U-ui24-first-attempt/ui-first-failure-root-receipt-read.json) 对应实际 ae2，退出 1、running=false、双 EOF。前三组 message_references／force_send／listener_transports 分别完成 **53／137／74 项检查并通过**；第四组 zuse_worker 在私有 Xvfb 就绪前失败，**1.552 秒、0 项检查**。计划 24 次执行中的其余 **20 次未运行**，alias=0，P1 仍待验。四个已启动的受控子进程已回收、输入集未改。报告没有把缺失 Xvfb stderr 解释成已确认的产品根因，也没有纳入本快照之后的续作结果。

## 3. zcalld 与 zuse 的身份和范围

[zcalld bd7 handoff](zcalld-bd7-20261121/handoff.json) 对应 `bd7a30c0a9e3865f137af229d5883e8fb984f518`／树 `cbd4a29ec9851a42dc36149fc099fb288c9623de`。220 叶中 218 叶相对 0af8 不变，仅 GUI gitlink 与发行说明改变。唯一 a64 批次实际退出 0，87 条命令包含身份读取，不能当成 87 个测试。实际根 release fresh=false、受控 CLI 2,964,896 B，SHA-256 `d5464f6f24da08204840d5c84f1780249d3635aa18ffd696dd5f6060c5621ecb`；8 组实际 TCP／Unix curl 取消和半关闭检查通过。

这次窄门禁没有运行 workspace Rust 全套、严格 Clippy、GUI 或 P1。原 882 的 182 项 Rust（含 7 项 listener 子集）和两次 Clippy 仍保留为原 0af8 身份的历史证据，不能移用于 bd7。元数据比较只规范化根路径；受控 scope、PID 和锁清理也没有被推广为全局持续空闲。PR1 仍为 draft。

[zuse 固定 CI 独审](zuse-67e-ci-44860554142/zuse-67e-ci-independent-review.json) 的实际 run `44860554142` 对应 `67e2d6a4cee0d106f46bdf064013e163c0aa3337`／树 `af46f28f9db1b4cd9f1103dc0f97687669b770d5`。三平台工作全部成功，默认测试分别为 Linux **289/0/5**、macOS **267/0/3**、Windows **263/0/2**（passed/failed/ignored），native 与 Wasm no_std 检查、严格 Clippy 均通过。Linux PTY 5 组和合成 USB 11 组独立陈述，不加入 Rust 测试总数；未启用的私有 MPX 实体及旧 no_std 20 项执行结果不借用。

[实际合并对象](zuse-67e-ci-44860554142/merge-fe47f96.json) 为 `fe47f963e604c13a2646baf5d391df5a7c69fc36`，父提交为 `83663988ebf736ec8de05d6372eef485c3d9ebac` 与 `67e2d6a4cee0d106f46bdf064013e163c0aa3337`，树与被测树完全相同。PR2 仍 open/draft，zuse main 仍 a1。这里的 a1 是 zuse 主线；当前 SSMCP 候选是 U，其冻结 zuse 依赖没有因 PR4 合并而传播更新。较早 368、2ffe 失败轮次仍保留各自身份。

## 4. Google Doc v4 与审阅限制

[Doc v4 交付回执](project-z-google-doc-20261121/delivery-v4.json) 的内容截止时间为 **03:38:30.890 UTC**，依据归档提交 33fd；标题、正文、表格、样式、链接和父目录已经结构化读回。回执记录 25 段非空正文、1 个 7×3 表格及 14 个链接，但没有浏览器视觉渲染验收。它不是后来 03:42:51 报告候选已经发布的证明，原始 MD／JSON 归档字节保持不变。

本次仅执行读取、哈希、差量和引用检查。没有执行作者生成器或验证器，没有启动 Cargo、产品测试、CI、GUI、输入操作或新的最终 44 图检查，也没有改候选、canonical、Git refs 或 Drive。报告文件描述符、所有核对范围及发布相对路径保存在本审阅 JSON；发布后仍须由负责人核对实际提交的文件集合和远端字节。
