# SSMCP：--input / --agent 只读架构核对

## 结论与范围

两个参数应保持独立：`--input` 选择聊天输入接口，默认 `terminal`；`--agent` 选择聊天消息的处理方，默认 `next-caller`。最新认证补充要求明确：`--input none` 禁用聊天框，现有工具和 control 仍可用。该补充来自 root 转交的用户消息 `fbc265b0131638b26cee28102f5e1288` revision 2；它不改变两个默认值。

本次只读基线为 `90c497007f6d6f16c3dd2da6a4599c48787e5ee1`。读取 canonical 树时，三个子模块 zharness、zplugin、zuse 有既有修改，随后出现未跟踪 artifacts/；均未修改或清理。没有执行 Cargo、运行 agent、发起聊天/finish、启动服务、改源码或创建平行实现。实现仍由 native feaba 与既有 CLI thread 独占。

完整原始需求记录为开发机 `git-policy-root/ssmcp-input-agent-original-history-20-50.json`，SHA256 `0778d361473a6ef692f796091d9c7eb1fea43db17d0a528af5aeecaf4d703997`。其中后续更正把默认 agent 名称统一为 next-caller；旧 --watch、--agent none 和曾误写的 --input 默认 none 均不能作为当前默认值。

## 已存在的实现与复用边界

| 范围 | 已核实的源码事实 | 给现有实现者的最小建议 |
|---|---|---|
| CLI 与会话恢复 | [client.rs](https://github.com/LIghtJUNction/ssmcp/blob/90c497007f6d6f16c3dd2da6a4599c48787e5ee1/src/client.rs) 的 Options、parse_with_policy、parse_saved、session_spec、child_session_spec 管理参数与重连保存；本基线没有 --input / --agent 字段。旧 --backend / --type 被 harness_selection_flags_are_removed 测试明确拒绝。 | 分别解析和验证 InputSpec、AgentSpec；保存/重载保留选择，不能把新参数转发成 SSH、shell 或外部 agent 的任意参数，也不要恢复旧 backend 选择语义。 |
| 终端与管道 | [client/input.rs](https://github.com/LIghtJUNction/ssmcp/blob/90c497007f6d6f16c3dd2da6a4599c48787e5ee1/src/client/input.rs) 的 platform::attach/reopen_tty 在非 TTY 时返回 None，Windows 亦检查 is_terminal；现有 pump 处理 dashboard 键盘、F7、粘贴和所选 PTY。 | 管道目前不会由该 TTY pump 接收。增加独立、有界、可取消的非 TTY 文本入口；规定换行、EOF 和多条消息边界。不要把聊天文本自动写成 shell 命令，也不要改变父进程 stdin 的共享 O_NONBLOCK 状态。 |
| 共同提交点 | [terminal/conversation.rs](https://github.com/LIghtJUNction/ssmcp/blob/90c497007f6d6f16c3dd2da6a4599c48787e5ee1/src/client/terminal/conversation.rs) 的 chat_submit 最终调用 steering::submit/publish_edit；native recipient 和 /send 目前有各自的显式分支。 | 输入适配器应汇合到统一的消息提交/处理选择处，保留用户文本、消息身份及失败草稿。避免各适配器复制一套投递队列或隐式解释不同的 slash command。 |
| next-caller | [client/steering.rs](https://github.com/LIghtJUNction/ssmcp/blob/90c497007f6d6f16c3dd2da6a4599c48787e5ee1/src/client/steering.rs) 内部默认 target 为 "next"；[steering.rs](https://github.com/LIghtJUNction/ssmcp/blob/90c497007f6d6f16c3dd2da6a4599c48787e5ee1/src/steering.rs) 的 finish_response → claim_selected 在锁内检查 Queued、target、reservation、revision 与大小限制，写入 Delivered、run_id、agent_id 后返回 client_user 消息。 | CLI 名称 next-caller 可映射到现有 "next"，不必改 wire target。保持实际授权调用的身份、版本与回执；已交付的消息不能因断连、重载、改 agent 或重试再次执行。 |
| input none | 此项是最新需求，当前基线无该开关。聊天 draft、提交状态、steering 队列与 native Backend 不是同一对象。 | 关闭 composer/聊天入口即可；不要连带停工具/control、撤销整个连接或清空已排队消息。禁用状态下不能让管道或隐藏 UI 继续偷偷提交聊天。 |
| Web / MCP HTTP | [http.rs](https://github.com/LIghtJUNction/ssmcp/blob/90c497007f6d6f16c3dd2da6a4599c48787e5ee1/src/http.rs) 已实现带协议协商的 Streamable HTTP MCP；local_router 只提供 OAuth 与认证 MCP，local_authority 检查 Host/authority。[client/local.rs](https://github.com/LIghtJUNction/ssmcp/blob/90c497007f6d6f16c3dd2da6a4599c48787e5ee1/src/client/local.rs) 的 local 模式默认 127.0.0.1:0，公网 URL 等有独立验证。 | Web 聊天输入页面和 MCP 工具端点需要明确区分。复用身份、协议和请求限制，不要因为提供聊天入口就无意暴露全部 native control。host/port 绑定、端口冲突、Origin/Host 与认证应按实际接入方式验收。 |
| MCP stdio | 本次入口搜索仅发现外部 backend 的 stdio MCP / RPC 连接；[backend/rpc.rs](https://github.com/LIghtJUNction/ssmcp/blob/90c497007f6d6f16c3dd2da6a4599c48787e5ee1/src/backend/rpc.rs) 的 Peer 是启动子进程并持有其管道的调用端。未发现可直接当聊天输入使用的同等入口。 | 入站 MCP stdio 需要明确的服务端协议适配；stdout 只能输出该协议，日志/ANSI/dashboard 不得污染；EOF、取消与 stdin 唯一所有者要单独测试。不能将外连 Peer 的存在当作入站模式已实现。 |
| Unix socket | [client/interface/listener.rs](https://github.com/LIghtJUNction/ssmcp/blob/90c497007f6d6f16c3dd2da6a4599c48787e5ee1/src/client/interface/listener.rs) 和 [listener/transport.rs](https://github.com/LIghtJUNction/ssmcp/blob/90c497007f6d6f16c3dd2da6a4599c48787e5ee1/src/client/interface/listener/transport.rs) 是聊天向接收者交付的 request/read/ack 出口，带 owner/thread、连接 epoch 与 lease。[local_socket.rs](https://github.com/LIghtJUNction/ssmcp/blob/90c497007f6d6f16c3dd2da6a4599c48787e5ee1/src/local_socket.rs) 已提供锁、0600、活跃 socket 检查、同 inode 清理与 peer 校验基础。 | --input sock 是入口，不能直接复用 listener 的业务方向。可复用底层安全路径/生命周期组件；给默认路径与自定义路径明确隔离、长度限制、消息 framing 和回执。现有 listener 的 lease/ack 仍独立保留。 |
| Codex / Claude / 其他 agent | [backend/codex.rs](https://github.com/LIghtJUNction/ssmcp/blob/90c497007f6d6f16c3dd2da6a4599c48787e5ee1/src/backend/codex.rs) 使用 app-server stdio，协商当前 schema；[backend/cc.rs](https://github.com/LIghtJUNction/ssmcp/blob/90c497007f6d6f16c3dd2da6a4599c48787e5ee1/src/backend/cc.rs) 明确 claude mcp serve 暴露工具，不是交互式 Claude terminal。[client/interface/harness.rs](https://github.com/LIghtJUNction/ssmcp/blob/90c497007f6d6f16c3dd2da6a4599c48787e5ee1/src/client/interface/harness.rs) 已有显式 provider 调用与任务槽位。 | 优先复用已协商的 provider 能力、取消和结果通道，但为聊天处理定义清晰的会话/turn 合约。成功启动 Claude MCP 工具进程不等于完成 Claude 聊天；不支持该合约时应准确报错，不假装成功或悄悄退回其他 agent。 |
| 另一个 SSMCP | [broker/messaging.rs](https://github.com/LIghtJUNction/ssmcp/blob/90c497007f6d6f16c3dd2da6a4599c48787e5ee1/src/broker/messaging.rs) 已有 recipient 发现、授权与 liveness proof；[interface/messages.rs](https://github.com/LIghtJUNction/ssmcp/blob/90c497007f6d6f16c3dd2da6a4599c48787e5ee1/src/client/interface/messages.rs) 是带 provenance 与幂等回执的 assistant 输出。 | 另一 SSMCP 的接收者必须绑定实际身份/会话，不能仅用展示名称。不要将外部输入包装成伪造 client_user 或 assistant ui.message；保留角色来源、取消、去重和结果关联。 |

## 建议的窄验收

以下是建议，未在本次审阅中执行；无需为静态调查启动全套构建。

| 验收组 | 足以证明的行为 |
|---|---|
| 参数与恢复 | 无参数得到 terminal + next-caller；显式 input none 关闭聊天框但原工具/control 可调用；分别改变 input、agent 互不覆盖；无效组合明确报错；saved session、child session、reload round-trip 保留选择。 |
| next-caller 回归 | 同一消息只随一个实际工具结果交付；保留 expected revision、agent/thread 身份与全局广播的原权限规则；并发编辑/撤回/取消与响应竞争、断线重载、已交付消息重试不导致重放。复用 steering 现有 exact_agent_targets_and_retries_preserve_fifo_and_do_not_restore_delivered_records、successful_takeback_prevents_old_text_delivery_and_publish_requires_current_revision 等测试夹具。 |
| 终端 / 管道 | 保留既有 Unicode 分片、粘贴与 F7 行为；管道多行/分片 UTF-8、空 EOF、过长输入、取消、消费方关闭有确定结果；普通文本不会进入 shell 执行。明确使用一条 EOF 消息还是流式帧，并让文档与实现一致。 |
| none 隔离 | 无 composer/隐藏聊天提交；不会吞掉现有下一次调用待投递消息；工具列表、只读调用及既有 control 生命周期保持。 |
| Web / MCP | 私有本地 fixture 验证 host/port、错误 Host/Origin、未授权访问、端口占用；MCP initialize、版本与帧错误、stdio stdout 纯净、EOF/cancel；页面输入与协议输入均到同一处理方。 |
| sock | 默认/自定义路径、路径冲突、活跃 socket 拒绝替换、失效自有 socket 恢复、错误 peer、分片/超限帧、退出只删自己 inode；保留既有 listener scope/lease 测试，避免输入入口影响原出口。 |
| 外部 agent | 本地可控 fixture 验证 argv 无 shell 注入、会话复用/新会话、响应/错误/取消、子进程退出、超时和重复提交；对每个实际支持的 agent 再验证真实协议能力。调用被接收和模型已执行必须使用不同回执语义。 |
| SSMCP 对 SSMCP | 明确接收者授权、断连后的未知结果、去重/取消与回复关联；输入不因回送变成无限循环；身份和 user/assistant 来源不得由未验证的 payload 自称。 |

## 本次交接状态

仅给唯一源码实现者提供审阅建议，不增加 writer、不修改 active worktree、不发送测试消息、不运行模型。三项优先合同边界已先行交给 root：复用现有 next 队列、区分 listener 出口与 input sock 入口、区分 Claude MCP 工具服务与会话 agent。正式实现与真实验收结果仍应由现有 owner 在自己的固定候选上记录。
