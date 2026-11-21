# SSMCP W 候选验收与主线整合

**固定知识截止：2026-11-21 06:23:03 UTC／台北 14:23:03。**

SSMCP W/r14 的 **35 阶段门禁和运行时 18 项检查已通过，但 UI 批次在第 7 个独立用例 account_compat 失败**。24 个独立 UI 计划中执行 7 个，6 个通过，余下 17 个未跑，包含 composer；P1 未跑。PR159 已由既有远端操作合入 main，合入后的源码树与 W 完全相同。源码合入不改变这次 UI 失败，也不产生一轮新的 main 产品测试。[结构化结果与证据索引](2026-11-21-w-candidate-and-main-integration.json)

## 1. 固定 W 的门禁与运行时结果

W 是 `4de17310ce2ecdbc8b6c6ab86ee365653f753ee8`，树为 `5be29af415b915ef3307bfed08c6cefec2798898`，唯一父提交是 V2 `f42baae1d5227bd6db8315aef778160b80b57274`。两棵树唯一的叶节点差异为 `scripts/e2e_composer.py` 第 515 行：显式标题 `next caller` 改为 `Next caller`。其余 1,113 个叶节点与四个 gitlink 保持。[源码与覆盖证明](evidence/ssmcp-W-r14/independent-review/source-controls-coverage.json)

### Gate35

run `3e89242560e0a243bde3d8442ce7e1db` 于 **05:42:51.112874—05:56:01.212636 UTC** 执行，35 阶段全部退出 0，包含 26 份 Rust 父阶段结果。06:09:54.033330 UTC 封存的独立审阅核对了本轮 213 份文本原件，结论为 **0 阻断、0 实质不一致**。[独审正文](evidence/ssmcp-W-r14/independent-review/ssmcp-W-r14-gate-independent-review.md)／[原门禁摘要](evidence/ssmcp-W-r14/root-completed-gate-review.json)

| Rust 结果范围 | 本轮计数 |
| --- | --- |
| Library private | 2,057 通过，23 ignored；新增 7 项与原 17 项均是其中子集 |
| Library HOST | 6 通过，与 private 选择互斥 |
| 普通集成 | 19 个目标、101 通过 |
| Worker ignored-exact | 另列 1 通过 |
| 额外 mandatory ignored | 4 个阶段、14 通过 |

独审核对了 26 条 selected `fresh=false` 编译链、37 条 wrapper 记录，以及五份受控产物的实际字节。五份产物分别是一个 debug 库测试、三个 release bin 和一个 release example。四份 release/example 哈希虽与 r13 相同，本轮新编译记录与 owned 副本仍已分别验证；library-test 哈希不同。两个 Clippy 阶段退出 0，但保留 unused `qrcodegen`／manifest warning。

**Gate35 没有执行 composer 原生 UI 用例。** 覆盖集合相同或门禁通过，均不能代替这次 UI 的实际结果。锁和退出证明限于本轮原始记录，不声称连续内核锁轨迹或当前全局空闲。

### Runtime18

同一 W 源码的 **private MCP 12 项与 transport 6 项全部通过**。原执行作业退出 0，外层耗时 8,289 ms；原件记录进程退出并回收、短临时目录移除。输入与 helper 前后身份一致，4 份文本输入和 5 个二进制描述符与 W 证明匹配。[运行时原件核对](evidence/ssmcp-W-r14-runtime/root-runtime-readback.json)

这项只读核对没有重新散列 ELF 或运行产品。记录明确 `models_started=false`、`TLS_verified=false`；18 项单独列示，不加入 Gate 的 Rust 数字，也不沿用历史 U／V2 或转移为新 main 的一次实际测试。

## 2. W UI：账户兼容用例失败

原 acceptance 记录批次于 **06:10:05—06:12:42 UTC** 执行，耗时 156.116 秒。24 个独立计划中执行 7 个：6 个通过，`account_compat` 第 7 个失败，余下 17 个未运行。1 项 alias 只表示覆盖关系，不算额外独立执行；本次没有到达 composer。[UI 原件核对](evidence/ssmcp-W-r14-ui/root-ui-readback.json)

失败 producer 保存了 **62 条检查：61 条为 true、1 条为 false**。唯一失败项为 `new-main:another_subject_cannot_list_connection`。失败 acceptance 行和 wrapper suite 没有 `checks` 字段；整批 stdout 显示的 wrapper `checks=0` 也不能解释为“0 个断言执行”。
[原始日志](evidence/ssmcp-W-r14-ui/account-compat-run.log)／[producer 报告](evidence/ssmcp-W-r14-ui/account-compat-producer-report.json)／[wrapper 记录](evidence/ssmcp-W-r14-ui/account-compat-wrapper-suite.json)

Root 已完整读取 native job `92eb2e0c47ccd1044fd6f6414c55af55-1c8`：**实际退出 1、nonrunning、双 EOF**，stdout 为 2,094 字节。七个 wrapper 的输入前后经精确比较一致，七个受控子进程均有 reaped 记录；未据此声称完成全部后代进程扫描。[作业完整 stdout](evidence/ssmcp-W-r14-ui/native-job-stdout.log)

失败检查对应的 HTTP 状态和响应正文没有记入原报告。因此现有证据不能确认权限漏洞或根因。原执行者正在准备一次同 W、原断言、原范围和原时限的定点诊断，仅增加脱敏上下文；**截至本报告截止，Root 尚未取得该诊断的结果**。这句话不推断诊断未执行，也不预判通过，后继结果不会覆盖本轮失败原件。

## 3. main 已整合，源码等价与提交历史分开记录

[SSMCP PR159](https://github.com/LIghtJUNction/ssmcp/pull/159) 已于 **06:13:34 UTC** 由既有远端操作 squash 合并，不是本轮 Project Z root 执行。Root 的 GitHub 独立读回确认以下实际对象：

| 身份 | 提交 | 父提交 |
| --- | --- | --- |
| 候选 F | `f1de4bf70d5406cf9f38347e298a829456b92e57` | W `4de17310ce2ecdbc8b6c6ab86ee365653f753ee8` 与 `c12fdf1d413501ddeb03a2dd2fb8c47731d2129f` |
| 实际 main P | `ea2bfcae6aea9672d8955f832a8ec5bd1e0749f4` | 唯一父提交 `c12fdf1d413501ddeb03a2dd2fb8c47731d2129f` |

F、P 和 W 的 Git 树均为 `5be29af415b915ef3307bfed08c6cefec2798898`。但 `W...P` 的历史比较为 diverged，ahead 2、behind 46，共同基点为 `f33ed8f14fc14aff05a2e4098743eb07e8527c06`；**W 不是 P 的祖先**。本报告保留 W 的 Gate、runtime 和失败 UI 的原身份，只证明源码树相同，不声称 P 又完成了一轮产品测试。[源码等价证明](evidence/ssmcp-W-main-integration/source-tree-equivalence.json)／[F 原对象](evidence/ssmcp-W-main-integration/github-F-commit.json)／[P 原对象](evidence/ssmcp-W-main-integration/github-P-commit.json)

原作者稍后完成的本地计划 M，在推送前发现实际 F 已存在后停止，没有覆盖远端；本报告采用真实 F/P，不将 M 写成发布提交。此次源码整合也不表示正式发行已经完成。

## 4. 后续范围与原始清单

原执行者已明确 **本轮 P1 未跑**。P1 候选继续是 zcalld `bd7a30c0a9e3865f137af229d5883e8fb984f518`；Gate、runtime 与 UI 的检查都不能替代 P1。

本轮 v25 保留 W 的四个 gitlink，`crates/zuse` 仍固定 `a1bb8fd2cbce0a9d85134999883c578358065242`。后续 zuse、zcalld 和 main 消费者传播单列，不并入本次 W 证明；最终 44 源图尚未完成。

原始 85 项分类保持 **56 merged／14 closed／9 archived／5 blocked／1 in progress**。最后一项是 **zcalld PR1**；SSMCP PR159 是后续工作，不新增或改写原始清单计数。历史成功、失败和旧报告均保留。[状态与边界](evidence/ssmcp-W-main-integration/source-tree-equivalence.json)

## 5. Google Doc 与本次证据包

Doc v7 已发布并完整读回，固定截止为 **2026-11-21 05:46:09 UTC**，引用报告提交 `1154d2e7ea28c5a03838d9c9dc735f6ec7f6929d`。31 个非空段落、7×3 表格、26 个来源链接和 3 个编号步骤对应这个历史快照，未倒填稍后的 W 门禁、运行时或 main 整合结果。旧 v6 与原始 Drive 的 0d73 MD／JSON 保持。[v7 交付](evidence/project-z-google-doc-20261121/delivery-v7.json)／[读回验证](evidence/project-z-google-doc-20261121/readback-verification-v7.json)

本候选选择 **22 份证据，共 301,276 字节**；加上本 MD 与同名 JSON，共 24 个文本载荷。JSON 列明每份证据的大小、SHA-256 和 Git blob，不包含自身哈希或尚未产生的发布提交。原 delivery 仍记录未复制的 raw-audit 和两份脚本的原生来源，不宣称整个审计目录已经归档。此次文件准备没有重跑产品、Cargo、GUI、CI 或 merge-tree，也没有改写旧报告、Doc、源码或 refs。
