# zuse PR #2：固定候选只读审查

**结论：建议在进入下一组合前修复 1 项 P2 问题。** 合法的 scoped script 可以执行完成，却生成 CLI/MCP 无法正确处理的完成回执。所有权、并行资源隔离、touchpad 预检和所审 Num Lock 路径未发现第二项已证实阻塞。本审查没有构建、执行产品、运行测试或 GUI，也没有修改源码、锁文件及当前 SSMCP 冻结组合。

## 固定来源与方法

| 项目 | 身份 |
| --- | --- |
| PR | [LIghtJUNction/zuse #2](https://github.com/LIghtJUNction/zuse/pull/2)；读取时为 open / draft |
| base | `a1bb8fd2cbce0a9d85134999883c578358065242` |
| 实现提交 | `81b5225644e971019d1e8e61e89ffe6694c45a8d` |
| 审查 head | `bb838b3573d36ff559c4c901ae7a64a0dd30a2bd` |
| 审查 tree | `285dcbe660ee410338a3bbeaf2153bd43862b77b` |
| diff | 40 文件、2 提交；第二个提交只补下游交接文档；Cargo 清单和锁文件未变 |
| 方法 | 固定源码、控制流、协议编码实现及字面量算术；执行次数为 0 |

审查覆盖 scoped compiler/scheduler、Mouse/X11 清理、cursor 边界、Runtime/MCP 入口、touchpad 能力与预检，以及新增 Wayland Num Lock 路径。两项只读子审查收到实质结果后停止，释放团队槽位；下面的回执问题由本审查者进一步逐段核对到实际锁定的 `zmcpio@84fc4978a248c2a3e2dd110f4f26fa52dd8b6890`，没有把子审查建议直接写成测试通过。

## P2：回执预算没有覆盖 JSON token 和 MCP 转义开销

新增 scheduler 只限制事件原始字节数为 **768 KiB**，完成运行及清理后才把事件拼成结果。CLI 随后重新解析结果判定退出码，MCP 则先解析，再同时输出文本形式与 `structuredContent`。这几层使用的上限不一致。[事件预算](https://github.com/LIghtJUNction/zuse/blob/bb838b3573d36ff559c4c901ae7a64a0dd30a2bd/src/script/scheduler.rs#L89-L107)、[完成与清理](https://github.com/LIghtJUNction/zuse/blob/bb838b3573d36ff559c4c901ae7a64a0dd30a2bd/src/script/scheduler.rs#L492-L530)、[MCP 结果编码](https://github.com/LIghtJUNction/zuse/blob/bb838b3573d36ff559c4c901ae7a64a0dd30a2bd/src/mcp.rs#L560-L588)。

下面两个输入都只查询能力，不打开显示器、不创建输入设备，也不需要失败的后端。需要显式把 `max_steps` 从默认 **256** 提高到相应值；这是现有受支持配置，并非默认配置下 256 步必然出错。

| 合法输入 | 静态预算证明 | 推导结果 |
| --- | --- | --- |
| `repeat 2500 { touchpad.capabilities(); }`，`max_steps=2500` | 每事件 27 tokens，仅事件已需 **67,500**；parser 最多 **65,536**。即使时间戳取 u128 的 39 位，事件及逗号最多 **775,000 B < 786,432 B**；5002 个展开节点也低于 16384 上限。 | scheduler 可返回 `completed`，但 CLI 把重新解析失败当执行失败，打印完成 JSON 后退出 1；MCP 解析错误直接向外传播，没有完成结果帧。 |
| `repeat 2200 { touchpad.capabilities(); }`，`max_steps=2200` | 完整结果约束为 **59,423 tokens**，仍在 parser 限内；每事件有 30 个引号，文本编码仅这些引号就增加 **66,000 B**，超过 `2*result.len()+65,536` 为转义和外层结构预留的额外空间。 | 原始结果可解析，但双份 MCP 编码返回 `Buffer` 错误；stdio 循环同样在写完成响应之前退出。 |

这些数字来自固定 capability JSON 和 scheduler 格式串，以及锁定 parser 对容器、key、value 各分配 token 的实现；不是运行结果。[固定能力数据](https://github.com/LIghtJUNction/zuse/blob/bb838b3573d36ff559c4c901ae7a64a0dd30a2bd/src/touchpad.rs#L252-L273)、[parser 上限](https://github.com/LIghtJUNction/zuse/blob/bb838b3573d36ff559c4c901ae7a64a0dd30a2bd/src/json.rs#L32-L48)、[锁定 parser token 计数](https://github.com/LIghtJUNction/zmcpio/blob/84fc4978a248c2a3e2dd110f4f26fa52dd8b6890/src/json.rs#L400-L449)、[双份结果序列化](https://github.com/LIghtJUNction/zmcpio/blob/84fc4978a248c2a3e2dd110f4f26fa52dd8b6890/src/tools.rs#L169-L237)、[字符串转义与 Buffer 判定](https://github.com/LIghtJUNction/zmcpio/blob/84fc4978a248c2a3e2dd110f4f26fa52dd8b6890/src/writer.rs#L18-L70)。

错误发生在动作和清理之后。`runtime::failed` 对解析错误返回 true；CLI 按该值选择退出码，MCP 的 `serve_lines` 则通过 `?` 直接传播错误。若此前存在合法输入动作，调用方失去回执后不能据此判断可以安全重放。本审查没有声称客户端实际自动重试、发生重复输入或能回滚外部效果。[失败判定](https://github.com/LIghtJUNction/zuse/blob/bb838b3573d36ff559c4c901ae7a64a0dd30a2bd/src/runtime.rs#L1646-L1652)、[CLI 输出](https://github.com/LIghtJUNction/zuse/blob/bb838b3573d36ff559c4c901ae7a64a0dd30a2bd/src/main.rs#L89-L94)、[stdio 传播](https://github.com/LIghtJUNction/zuse/blob/bb838b3573d36ff559c4c901ae7a64a0dd30a2bd/src/mcp.rs#L614-L645)。

**最小修复方向：** 让可接受的回执同时满足 token 数和实际编码字节上限；或者返回明确的有界摘要，仍保留完成/部分提交状态和清理结果。MCP 缓冲区需要按转义后长度计费或使用有界的精确容量重试，不能只将 parser 上限调大而留下第二个容量问题。作者可用上述两个纯脚本补 CLI/MCP 回归，并在同一 stdio 会话继续发第二个请求，确认服务仍可用。若采取摘要策略，用已有 MockHost 验证动作前缀及清理信息即可，无需新增 GUI 门禁。**本审查未运行这些建议用例。**

## 其他重点路径与边界

- **所有权与取消：** 构造前记录唯一 XInput master 名称；操作在 server grab 内校验名称，避免 ID 重用后误投设备。尝试按下的按钮会先登记，正常错误和 cooperative cancel 最终逐个释放 live handles。alias 和函数参数保留相同 MouseId，局部 owned 列表只记录实际构造者；parallel 按 MouseId/共享 User 资源判冲突。没有把静态审查写成 native 清理通过。[X11 close](https://github.com/LIghtJUNction/zuse/blob/bb838b3573d36ff559c4c901ae7a64a0dd30a2bd/src/platform/pointer_x11.rs#L806-L905)、[parallel 资源](https://github.com/LIghtJUNction/zuse/blob/bb838b3573d36ff559c4c901ae7a64a0dd30a2bd/src/script/compile.rs#L490-L521)。
- **取消入口不同：** CLI 使用 InterruptGuard，Rust 可传 cancellation token；当前 MCP `zuse.script` 调用 `execute`，其回调始终为 false。因此不能把 CLI/Rust 取消证据宣传成 MCP cancellation notification 已接通。这是实现边界，未另立缺陷。[入口](https://github.com/LIghtJUNction/zuse/blob/bb838b3573d36ff559c4c901ae7a64a0dd30a2bd/src/script/mod.rs#L40-L59)。
- **touchpad：** 所有 native 标志为 false；完整展开程序的 gesture/cancel 能力检查发生在 scheduler 前，因而不会先执行较早鼠标动作再发现不支持。纯规划和能力查询可用，未发现 wheel fallback。[预检](https://github.com/LIghtJUNction/zuse/blob/bb838b3573d36ff559c4c901ae7a64a0dd30a2bd/src/script/plan.rs#L95-L112)。
- **字符串与键盘：** 前台文本先验证完整字符串；后台文本先完成整串 keymap 解析，再开始 dispatch。Num-on 路径限定普通前台 chord，保留 no-held、Caps-off、group-0、同一可恢复主键盘及 map 稳定性门控；文本和后台路径仍拒绝 Num-on。错误可能发生在部分提交之后，不应盲重放；本审查没有进行原生故障注入。[固定路径](https://github.com/LIghtJUNction/zuse/blob/bb838b3573d36ff559c4c901ae7a64a0dd30a2bd/src/platform/wayland.rs#L338-L422)。
- **兼容性：** `platform::Desktop` 现有公开签名没有变化。Runtime 默认独立指针、fresh `mouse.position()` 需要既有 handle 是明确行为变更；保留有意控制用户指针的调用应显式选择 user/system。SSMCP、ztype 的 Desktop façade 不会仅因升级依赖就暴露新 scoped API；下游适配属于后续独立组合。

## 作者门禁与本次独立证据的区别

已读取固定 [validation 文档](https://github.com/LIghtJUNction/zuse/blob/bb838b3573d36ff559c4c901ae7a64a0dd30a2bd/docs/validation-scoped-mice.md) 和 [sanitized evidence JSON](https://github.com/LIghtJUNction/zuse/blob/bb838b3573d36ff559c4c901ae7a64a0dd30a2bd/docs/evidence/scoped-mice-native-2026-11-21.json)。它们报告 Rust **286 passed / 0 failed / 5 ignored**、no-default-features **20 passed**、格式/Clippy，以及 compile-only 跨平台检查、私有 Xvfb MPX、GTK/AT-SPI 和 Hyprland 0.57.2 验收；原生二进制 SHA 为 `17d0a6867ee3dc9d176b5d8c3921069e51f06648c29459083cee16084f326c0b`。

这些仍是**作者已有报告**。本次未读取原始逐命令回执、compiler-artifact 与完整 source-to-binary 绑定及原始 native 报告，也未重跑；不把其数量加入本审查通过数，不外推 Windows/macOS 实机或当前 SSMCP 新组合。若需要独立验收身份核对，下一步仅索取这些现成原件。

当前 SSMCP **441 + a1** 冻结组合保持原样。作者列出的 `83e632...` impact 是历史图观察，下游 SSMCP/ztype façade、锁及 aggregate 更新仍由各自现有 owner 在后续组合交接，不报告为已完成传播。

## 报告自检

本结论只阻塞已证明的回执预算契约；没有将未复现的原生清理故障扩成第二项问题。推荐回归与作者旧门禁均标明来源，固定 candidate/tree 未替换为未来 main，执行、构建、GUI 和源码修改计数均为 0。

