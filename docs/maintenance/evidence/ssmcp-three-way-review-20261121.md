# SSMCP 三方来源审查：cf0 / 781 / f208

时间：2026-11-20 23:40:17 UTC（台北时间 2026-11-21 07:40 UTC+8）。仅使用 GitHub 插件读取固定提交、递归树和 diff；未构建、测试、启动服务或改写仓库。

## 结论

**781 不能作为已验候选直接沿用到 f208。** 两边不仅包含相同改动，也存在独立的运行行为；最需要 source owner 处理的是同名 `--agent` 的不同语义，以及 `--input none` 与 main 已退休的 finish／强制继续 hooks 的交叉。整合后须固定新的源码与产物组合，旧回执仍归原提交。

| 角色 | Commit | Tree |
| --- | --- | --- |
| 旧审计祖先 | `cf0ab581700918a37fcccbebb93de2e0cab02841` | `bd2bcce33baffa69b82d69d9cff3abdb85baa0fb` |
| PR159 候选 | `781b87df1d364137b6885f17f631a3e9e991bd58` | `6bf7beb143cfdce3878df856c27785164695430f` |
| main 快照 | `f208a03b5403332214f3acf6ee0b176752b5d2c9` | `7eeb434be1d24e14b453488f5fbca90d933e12b9` |

GitHub 的实际最近共同祖先为 **`a19ac040b1c7e9daa6a2144db79cfaa1bee09954`**。相对此点，781 独有 22 个提交，f208 独有 25 个。cf0 是更早的共同审计基点。PR159 本次读回仍为 draft781、`mergeable=false`；其 `base_sha=cf0` 不能代替当前 main。

| 比较基点 | 同一最终 blob | 仅候选变化 | 仅 main 变化 | 双方不同 blob | 变化路径合计 |
| --- | ---: | ---: | ---: | ---: | ---: |
| cf0 | 10 | 19 | 63 | 27 | 119 |
| 实际 merge-base a19 | 1 | 21 | 64 | 24 | 110 |

这里按路径、文件模式、对象类型及 SHA 比较；**不同 blob 数量不是文本冲突数量**。三棵目标树与 a19 树均完整，两个 cf0 compare 的 56／100 个文件记录与对应树的 SHA 全部一致。

## 原 source owner 的重点合并事项

1. **先统一 `--agent` 契约。** 781 的 `chat_io::Flags` 默认 `next-caller`，表示聊天收件人；其程序路径实际使用 Codex exec、Claude print 等处理消息，SSMCP 对端是精确 recipient/account。f208 的 `agent::Selection` 默认 None，选择启动时加载的协议/catalog；它增加 provider list、`--agent=...`、`--` 后原生参数，SSMCP 对端则是带 OAuth 的 MCP gateway。两个 parser arm 不能直接拼接，也不能把相同 flag 当作同一行为。证据：[781 chat options](https://github.com/LIghtJUNction/ssmcp/blob/781b87df1d364137b6885f17f631a3e9e991bd58/src/client/chat_io/options.rs)、[781 process dispatch](https://github.com/LIghtJUNction/ssmcp/blob/781b87df1d364137b6885f17f631a3e9e991bd58/src/client/chat_io/process.rs)、[f208 agent selection](https://github.com/LIghtJUNction/ssmcp/blob/f208a03b5403332214f3acf6ee0b176752b5d2c9/src/client/agent.rs)。

2. **保留 none 的端到端控制边界。** 781 的禁用聊天贯穿 relay capability ACK、broker、runtime、catalog、saved attach 与 steering，不能简化成隐藏 composer。其 `Manager::reload_ready` 在无聊天房间时仍允许等待实际 ReloadCommit，并保留旧草稿与 outbox；f208 的 reload 另增加 native separator、agent 和 local socket 的保存测试。两边须在一个生命周期中成立。证据：[781 steering](https://github.com/LIghtJUNction/ssmcp/blob/781b87df1d364137b6885f17f631a3e9e991bd58/src/client/steering.rs)、[f208 reload](https://github.com/LIghtJUNction/ssmcp/blob/f208a03b5403332214f3acf6ee0b176752b5d2c9/src/client/reload.rs)。

3. **不要复活已退休 hooks。** 781 修改 `http/finish_request.rs` 并在动态 guide 保留 finish approval 文案；f208 已删除此文件、reminders 和旧 finish receipts，新增 `retired_tool_error`、no-dispatch 测试，并让最终消息在真实 owner 下直接提交。此处存在 modify/delete。none 的禁用断言应针对仍有效的聊天入口；旧 finish/answer 应保持退休结果，不能用旧测试反推恢复入口。证据：[f208 retired hooks tests](https://github.com/LIghtJUNction/ssmcp/blob/f208a03b5403332214f3acf6ee0b176752b5d2c9/src/http/question_delivery_tests/retired_hooks.rs)、[781 dynamic guide](https://github.com/LIghtJUNction/ssmcp/blob/781b87df1d364137b6885f17f631a3e9e991bd58/src/runtime/capabilities.rs)。

4. **计时应保留主线的新数据模型。** 781 主要区分倒计时、经过时间和 observation wait；f208 新增绝对 deadline／interval／list、Entry 字段和 typed ExecutionTiming，并把实际原生 job 时间接入 render/panel。整份取旧 timing.rs 会丢失此链路。要同时保留“等待预算不等于 job deadline”和“到期不代表已完成”，以及拒绝由 provider JSON 伪造 native 时间。证据：[f208 terminal timing](https://github.com/LIghtJUNction/ssmcp/blob/f208a03b5403332214f3acf6ee0b176752b5d2c9/src/client/terminal/conversation/timing.rs)、[f208 render](https://github.com/LIghtJUNction/ssmcp/blob/f208a03b5403332214f3acf6ee0b176752b5d2c9/src/client/render.rs)。

5. **粘贴核心相同，只能复用方法。** `client/input.rs`、`input/paste.rs`、`references/paste.rs`、`terminal/conversation/paste.rs` 三方同 SHA；composer 和 benchmark helper 的最终 blob 两侧也相同。但候选新增 configured-agent、pending/unconfirmed 回执与草稿保留，main 修改真实时钟、footer 和 history hit-test 的预期。新组合的真实 PTY、字节/光标、收件人及退出清理仍需绑定新 ELF，不能借用 781 或其他提交的 P1 结果。证据：[781 conversation](https://github.com/LIghtJUNction/ssmcp/blob/781b87df1d364137b6885f17f631a3e9e991bd58/src/client/terminal/conversation.rs)、[f208 terminal](https://github.com/LIghtJUNction/ssmcp/blob/f208a03b5403332214f3acf6ee0b176752b5d2c9/src/client/terminal.rs)。

6. **Cargo 差异可以明确收敛。** 781 只追加 3 条 include，lock 相对 cf0 不变。f208 的 8 条新增 include 已含全部这 3 条；版本改为 0.10.22，lock 只变本包版本和 zcall `564ede15→317c52f1`。保留所选 main 的版本/lock/include 集合，避免整份取候选导致回退。证据：[f208 Cargo.toml](https://github.com/LIghtJUNction/ssmcp/blob/f208a03b5403332214f3acf6ee0b176752b5d2c9/Cargo.toml)、[f208 Cargo.lock](https://github.com/LIghtJUNction/ssmcp/blob/f208a03b5403332214f3acf6ee0b176752b5d2c9/Cargo.lock)。

## 可以直接辨识的相同内容与独有内容

两侧相同的 10 个最终 blob：local-mode 文档、benchmark_client_memory、e2e_local_socket、account/send、composer、computer_control、interface/computer、local/socket、terminal/computer、connection_context 测试。这是内容相同证明，不是它们在新组合中执行通过的证明。

候选独有的 19 路径主要是完整 chat_io、none 控制贯通、程序回复的原 owner 记录、saved attach 和 portable helper 的 `attach --local` 修正。main 独有的 63 路径主要是 agent/peer 协议、time 扩展、退休 hooks、相关 HTTP/steering 和测试/文档。全部路径及三方 SHA 见独立 inventory；27 个不同 blob 已在 JSON 列表中给出，未尝试本地合并或判定具体文本冲突。

## 新固定来源与证据边界

先由唯一 source owner 形成一个新 commit/tree，并记录 manifest、lock、关键 helper、实际 compiler-artifact root source 及五产物 SHA；再由原有资源与 quiet/outer 锁编排安排有限回归。441 的 CI、781 的 baseline、147/v21 和 57d/PR161 的记录继续只属于各自来源。此审查没有运行任何测试，也不改写 v21/v22 tags、release 资产或生产部署。

详细 JSON：`ssmcp-cf0-781-f208-three-way-review.json`。完整分类：`ssmcp-cf0-781-f208-three-way-inventory.json`。固定 API 差异证据：`ssmcp-cf0-781-f208-focused-patches.json`。

