# Project Z 后续进展：发行投影修复与 SSMCP V2/r13 门禁

**状态快照：2026-11-21 05:31:38.652772 UTC／台北 13:31:38.652772。**

本轮已完成三项工作：Project Z 的 `version+git` 发行投影兼容修复已发布到协调分支；SSMCP V2/r13 的 35 阶段门禁全部通过，完整原件独立复核没有发现阻断；同一 V2 源码随后通过 12 项 private MCP 和 6 项 transport 运行时检查。UI 本轮实际执行 13/24 组：12 组通过，`composer` 第 13 组失败，11 组未运行；原来失败的 `session_groups` 已通过 108 项检查。P1 和最终 44 源图尚未完成。各项结果及 27 份证据的逐文件身份见[结构化索引](2026-11-21-release-and-v2-gates.json)。

UI 实际于 05:31:00 UTC 结束，属于上述快照范围；其原件在 05:38—05:44 UTC 才完成本报告的直接读回。这里补入迟到证据，保留真实失败。05:35:22 的源码后继单独列在第 6 节，不计入快照内的通过结果。

## 1. Project Z：兼容合法的 version+git 声明

修复已发布到 `coord/git-source-policy-20261120`，提交为 [`88fa3610f24cc21705107bff4917a6ec26c022d0`](https://github.com/LIghtJUNction/project-z/commit/88fa3610f24cc21705107bff4917a6ec26c022d0)，树为 `ad123c0aeda12ff63b3b1c1efb7804ff4a9282f4`，父提交为 `ba666696e38c350c7bf3cdcc01fd940fcfa69145`。400 个叶节点中仅 4 个文件改变，另外 396 个保持原样；远端树和四个文件内容均与被测版本一致。[发布读回](evidence/project-z-release-compat-88fa361/publication-readback.json)

原问题是发行投影拒绝了符合项目依赖策略的 `version+git` 组合。现在先用未改动的 `cargo_versions.satisfies` 检查版本要求与唯一锁定版本是否兼容，再把发行暂存内容投影为锁中的 `=exact`。非法或不兼容版本仍然拒绝；对 `rev/branch/tag/path/registry/registry-index/workspace` 与内部 Git 混用的限制没有放宽。别名、features、optional、目标平台和 workspace 继承语义保持，原源码 manifest、锁文件与外部依赖不被暂存步骤改写。`STAGING_ONLY_UNVERIFIED_NO_PUBLISH` 标签和源码回执、归档来源校验继续生效；这次修复不构成正式发行或 registry 可用性证明。[实现与边界](evidence/project-z-release-compat-88fa361/handoff.json)

| 实际验证 | 结果与计数口径 |
| --- | --- |
| 修改测试、保持旧生产代码的 RED | 选定 2 个方法，实际退出 1；7 个子例／设置错误不算 7 个方法 |
| 固定修复树的 GREEN | 18 个方法通过，0 失败、0 错误、0 跳过；release 4、projection 8、receipts 6 |
| 保留的真实 Cargo metadata 检查 | `cargo metadata --offline --no-deps --format-version=1` 实际执行一次、退出 0 |

该批次未运行完整项目图、Rust 产品门禁、GUI 或 P1。原批次退出和清理记录仅说明该次受控任务已结束，不代表共享锁持续空闲。[RED 原件](evidence/project-z-release-compat-88fa361/red-result.json)／[GREEN 原件](evidence/project-z-release-compat-88fa361/green-result.json)

## 2. SSMCP V2/r13：35 阶段门禁完成

本次源码是 [`f42baae1d5227bd6db8315aef778160b80b57274`](https://github.com/LIghtJUNction/ssmcp/commit/f42baae1d5227bd6db8315aef778160b80b57274)，树 `64b40eb8a3e0188076cf376229d3d87074d27dcc`，父提交 `18f43d69715538582ddc2806434009170f188e3c`，manifest 版本 0.10.25。原 `scripts/e2e_session_groups.py` 仍与 U 相同，blob 为 `62245b4f655befd1ac5967cd2de68e1573ad9ca6`；该原用例的本轮 UI 实测已通过，整轮 UI 的后续失败见第 4 节。[覆盖与来源比较](evidence/ssmcp-V2-r13/independent-review/contract-comparison.json)

run `f6121dd70d3f8c4fb3d747a9bf2697bf` 于 04:59:22.538104 开始、05:09:54.138883 UTC 完成，耗时 631.601 秒。35 个阶段均退出 0，其中有 26 份 Rust 父阶段结果。05:27:55.992049 UTC 封存的独立复核检查了 213 份原始文本，结论为 **0 阻断、0 实质不一致**。[完整独审说明](evidence/ssmcp-V2-r13/independent-review/ssmcp-V2-r13-gate-independent-review.md)／[紧凑复核结果](evidence/ssmcp-V2-r13/independent-review/ssmcp-V2-r13-gate-review-summary.json)

| 结果组 | 本轮实际结果 | 计数边界 |
| --- | --- | --- |
| library private | 2,057 通过、0 失败、23 ignored、6 filtered | 新增 7 个回归和原 17 个目标均已包含在 2,057 中 |
| library HOST | 6 通过、0 失败；2,080 filtered | 与 private 的选择分开 |
| 普通集成目标 | 19 个目标、101 通过 | worker ignored-exact 另计 1 项 |
| 额外 mandatory ignored 阶段 | 4 个阶段、14 通过 | 独立列示，不与嵌套输出重复累计 |
| Python 策略检查 | release-policy 100；deployment-policy 35 | 属于本次 35 阶段，不加入 Rust 计数 |

与 r12 的覆盖比较只新增 7 个 private 测试，没有删除测试，阶段和集成清单保持；r13 的通过结果来自本轮原件。独审还核对了 26 条 selected `fresh=false` 编译链、1,545 个源码文件及 304 个目录，并对本轮 5 个受控产物实际流式计算哈希。这 5 个产物分别是 **1 个 debug 库测试、3 个 release 可执行文件、1 个 release example**，不能统称“五个 release ELF”。两个严格 Clippy 阶段虽退出 0，仍有 unused `qrcodegen`／manifest warning。[编译与产物绑定](evidence/ssmcp-V2-r13/independent-review/compile-time-binding.json)

## 3. 同一 V2 的运行时 18 项检查完成

后续运行时检查使用同一 `f42baae` 源码与 r13 产物身份。原报告记载 05:25:12—05:25:19 UTC 执行，运行时耗时 7,764 ms，外层耗时 8,120 ms；**private MCP 12 项与 transport 6 项全部通过，errors 为空，外层退出 0**。这 18 项单独列示，不加入门禁的 Rust 计数，也不借用历史 U 的结果。[原件核对摘要](evidence/ssmcp-V2-r13-runtime/root-runtime-readback.json)

Root 已读取原 launch 与 runtime 两份 JSON、核对其完整字节哈希，并以精确比较确认输入前后相同、transport 绑定相同；另重新计算 4 份文本输入哈希，核对 5 个产物描述符与本轮 Gate 一致。原件中的模块清理、外层进程退出并回收、短临时目录移除均一致。此次读回没有再次散列 ELF 或重跑产品。记录明确 `models_started=false`、`TLS_verified=false`；这些结果不证明实际模型启动、TLS、UI 或 P1 已验收。

## 4. UI 的实际失败与后续验收

原 native job `92eb2e0c47ccd1044fd6f6414c55af55-1a4` 已直接读至双 EOF，实际退出 1。验收记录为 05:27:26—05:31:00 UTC，持续 214.15 秒：24 个计划独立 suite 中执行 13 个，12 个通过，`composer` 失败，其余 11 个未运行。`human_finish` 由 interactions 覆盖，是 1 个 alias，不是额外独立通过。12 个通过组的检查数算术和为 996，不能当作去重后的全局测试数。[UI 原件核对](evidence/ssmcp-V2-r13-ui/root-ui-readback.json)／[完整 wrapper 输出](evidence/ssmcp-V2-r13-ui/native-job-stdout.log)

- 原 `session_groups` 用例通过 **108 项检查、8 个记录帧**，producer 记录 12.33 秒，suite wrapper 记录 13.919 秒。它使用未改动的原场景，补上了 U 先前未通过的首次查询与组选择路径。[原用例日志](evidence/ssmcp-V2-r13-ui/session-groups-run.log)
- `composer` 的原日志已有 **61 条 PASS**，独立 producer 报告也记录 61 个已完成检查；随后等待 explicit Next caller 选择返回编辑界面时超时。wrapper 输出为 `checks: 0`，acceptance 失败行则没有 `checks` 字段；二者不能解释为零断言。producer 记录 21.378 秒，wrapper 记录 22.754 秒。[原失败日志](evidence/ssmcp-V2-r13-ui/composer-run.log)
- 13 份执行前后输入记录精确相同，13 个 wrapper 子进程均记录已回收；失败 producer 没有完成的内部 cleanup 摘要。这次读回没有再次散列 ELF、重算 producer 的 input-set 哈希公式，或独立检查所有后代进程。

原脚本第 515 行传入小写 `next caller`；`editing_queue()` 对完整标题逐字比较，而实际画面标题为 `Edit queue · Enter sends · Next caller`。这一大小写不匹配确定会使该谓词失败。修正后的实际 UI 验收仍须单独完成，源码后继见第 6 节。

P1 在本次 UI 停止后未执行。zcalld PR1 的 `bd7a30c0a9e3865f137af229d5883e8fb984f518` 仍为 draft，等待实际 P1。zuse PR4 已合入功能分支为 `fe47f963e604c13a2646baf5d391df5a7c69fc36`，PR2 仍为 draft，main 保持 `a1bb8fd2cbce0a9d85134999883c578358065242`。最终 44 源图尚未完成。

原始 85 项分类保持 **56 merged／14 closed／9 archived／5 blocked／1 in progress**。旧主报告 `c08d6e8`、整合提交 `efe912e`、`ba66669` 保存的 UI 第二轮失败，以及更早 U 的成功／失败记录均保留。各轮成功和失败继续绑定各自源码；本次增量不表示正式发行已经验收。

## 5. Google Doc 与证据归档范围

[同一 Google Doc](https://docs.google.com/document/d/1X7wuVkub_mHe93NTofh-VmB7a32_RWFJBY8E3ddDEgw) 的 v6 已完成发布和完整读回：31 个非空段落、7×3 表格、22 个来源链接、3 个编号步骤，31 段加 21 个单元格的 52 份文本均与预期一致。其固定快照是 **05:07:21 UTC**，因此当时记载“r13 running”正确，尚未包括 05:09:54 的完成结果。原始 Drive MD／JSON 仍是 0d73 版本；该 Doc 与本 Git 增量保留各自的固定快照。[Doc 交付](evidence/project-z-google-doc-20261121/delivery-v6.json)／[读回验证](evidence/project-z-google-doc-20261121/readback-verification-v6.json)

本次增量引用 **27 份证据，共 605,067 字节**：14 份既有原件、8 份独审选择交付、1 份 runtime 核对摘要，以及 4 份 UI 原件／核对记录。加上本 MD 与同名 JSON，共 29 个文本文件。27 份证据的大小、SHA-256 和 Git blob 均列入 JSON；这不表示完整 213 份原始文本或原生独审目录全部 11 个文件均进入本次 Git 归档。两份摘要不嵌入自身哈希或尚未产生的发布提交，也不包含 ELF、凭据或配置正文。

## 6. 快照后的源码后继：仅修正显式目标标签

后继提交 [`4de17310ce2ecdbc8b6c6ab86ee365653f753ee8`](https://github.com/LIghtJUNction/ssmcp/commit/4de17310ce2ecdbc8b6c6ab86ee365653f753ee8) 的提交时间为 05:35:22 UTC，tree 为 `5be29af415b915ef3307bfed08c6cefec2798898`，唯一父提交为 `f42baae`。GitHub 完整比较仅显示 `scripts/e2e_composer.py` 一行由 `next caller` 改为 `Next caller`；生产 Rust 没有变化。

固定产品代码在显式 `target == "next"` 时显示 `Next caller`，没有显式目标时的默认标签才是 `next caller`。因此只修这一次显式选择的期望，保留其他默认目标的小写期望。完整标题比较、页面和列位置、光标可见性，以及后续请求 ID、目标、正文、实际投递与 delivered 断言均保留。[固定产品逻辑](https://github.com/LIghtJUNction/ssmcp/blob/f42baae1d5227bd6db8315aef778160b80b57274/src/client/terminal/conversation.rs)

既有执行者继续准备该后继的 r14 与 runtime／UI／P1 验收。这里仅记录已发布源码及静态核对，不把 V2/r13 的通过结果转给后继，也不宣称后继验收已经通过。
