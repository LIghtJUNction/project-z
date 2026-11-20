# zuse PR #3：固定实现独立静态审查

**结论：未发现新的静态阻塞；原 P2 的 token 与编码容量问题在这份固定实现中得到处理。** 本结论绑定实现 `35664746549c482c99082e6180419b2c0f5ff532`、树 `0d1d19006dfcf4da8e804f1f27d13d284eb96299`；父提交是测试提交 `44ffb599e96c412c216f395ed8b7286f585b5474`，PR 基于 scoped-mice 分支 `bb838b3573d36ff559c4c901ae7a64a0dd30a2bd`。GitHub commit/tree 已独立读取。审查没有构建、运行测试、操作 GUI 或修改源码。

## 关键判断

详细事件现在采用有界前缀。超过 768 KiB 或实际 JSON token 预算时，调度器增加 `events_omitted` 并继续执行；后续详情也保持省略。动作与等待预算、所有权、真实后端调用和取消检查没有移入省略分支。[record 与 close](https://github.com/LIghtJUNction/zuse/blob/35664746549c482c99082e6180419b2c0f5ff532/src/script/scheduler.rs#L100-L151)

错误与清理结果独立保留。`cleanup.attempted` 在调用 close 前计数，`cleanup.failed` 在取得结果后计数；即使 close 详情省略，计数仍存在。最终结果继续合并执行和清理错误，双失败时两段原因都保留；任何一个失败或取消都不会被改写为 completed。完整事件列表不再可得时，省略标记明确暴露这一限制，没有宣称回滚或允许盲目重放。[最终结果](https://github.com/LIghtJUNction/zuse/blob/35664746549c482c99082e6180419b2c0f5ff532/src/script/scheduler.rs#L487-L550)

Token 数使用实际锁定 parser 的 `tokens_used()`，没有用字节数猜测。事件上限为 **65,280 tokens**。按当前源码逐项计数，完整回执在 events 之外增加 **31** 个 token，modern 的纯文本 MCP 外层再增加 **27** 个；最大 **65,338 < 65,536**，仍留 **198** 个。这个计算只适用于当前字段布局，未来增加字段需要重新核对。[解析器入口](https://github.com/LIghtJUNction/zuse/blob/35664746549c482c99082e6180419b2c0f5ff532/src/json.rs#L34-L61)、[固定 envelope](https://github.com/LIghtJUNction/zmcpio/blob/84fc4978a248c2a3e2dd110f4f26fa52dd8b6890/src/mcp.rs#L555-L573)

MCP 重试只发生在已生成结果的编码阶段。闭包仅再次调用 `protocol.tool_result`；不调用 Runtime、script 执行入口或外层 handle。只有 Buffer 且 needed 大于现有空间时才扩大一次并重编码一次，初始容量和 needed 都保留 **32 MiB** 上限。锁定 Writer 会在容量不足时继续累计转义、结构化副本、request ID 和 framing 的总长度，因此 needed 是完整编码长度。[MCP 修复](https://github.com/LIghtJUNction/zuse/blob/35664746549c482c99082e6180419b2c0f5ff532/src/mcp.rs#L561-L606)、[Writer](https://github.com/LIghtJUNction/zmcpio/blob/84fc4978a248c2a3e2dd110f4f26fa52dd8b6890/src/writer.rs#L11-L73)

## 测试与证据边界

已审测试源码覆盖 CLI 2,500 次能力查询，以及同一真实 stdio 子进程中的 2,200、2,500、随后 1 次查询；断言后续响应、ID、text/structured 一致及进程成功退出。MockHost 覆盖字节超限后仍执行后续 click，以及成功、输入失败、清理失败、双失败和取消五种结果。新增测试能够检查原问题和修复的主要行为。[入口测试](https://github.com/LIghtJUNction/zuse/blob/35664746549c482c99082e6180419b2c0f5ff532/tests/script_entrypoints.rs)、[调度器测试](https://github.com/LIghtJUNction/zuse/blob/35664746549c482c99082e6180419b2c0f5ff532/src/script/scheduler.rs#L825-L928)

Core 已报告原 RED 3 项失败，以及固定实现的 green 作业 611：6 项入口、10 项 scheduler、fmt、locked metadata 和相关 Clippy 全过。**这些是原执行者的回执信息；本审查未重新打开原始 gate 日志，也未把它们计作自己的测试通过。** 原执行者正在补齐 compiler-artifact 与 fresh=false 来源证明。PR #2 的原 native、跨平台或 286 项结果保持原身份，不计入本次审查。

当前没有额外修改建议。后续可按原负责人已完成的窄门禁与产物身份交付继续处理此独立 PR；本审查不代表 main、SSMCP 冻结组合或下游依赖已经更新。

