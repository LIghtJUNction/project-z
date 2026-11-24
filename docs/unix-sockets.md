# Project Z Unix socket 规范

适用于 Project Z 新增的本机 Unix domain socket 服务。每个服务公开自己的端点、传输协议和版本。调用方直接连接 socket，可以在同一个进程内提交多次请求。

## 路径与生命周期

| 约定 | 要求 |
| --- | --- |
| 默认路径 | 用户服务使用 `$XDG_RUNTIME_DIR/<服务名>/<端点名>.sock`。MCP 端点命名为 `mcp.sock`。 |
| 显式路径 | 服务支持为测试、多个实例及系统服务指定路径。服务输出实际路径，客户端允许显式选择端点。 |
| 文件权限 | 用户服务的 socket 目录由运行用户持有，权限为 `0700`。Linux socket 文件权限为 `0600`。 |
| 启停 | 已被占用的路径应报告错误。正常退出只清除本实例创建的 socket。管理员可在确认旧服务已经退出后清理残留文件。 |
| 访问 | 默认服务同一系统账号。跨账号或跨主机的接口需要独立的认证和授权配置。更换传输方式时保留服务本身的准入规则。 |

默认运行目录必须是绝对路径。没有可用的 `XDG_RUNTIME_DIR` 时，调用方可传入自己的私有运行目录中的路径。客户端应报告连接失败与实际路径，以便排查服务未启动、权限错误和路径长度超限。参见 [XDG Base Directory Specification](https://specifications.freedesktop.org/basedir/latest/)。

## 请求与响应

MCP 服务在 Unix stream socket 上使用 HTTP，端点路径为 `/mcp`。客户端按 MCP 规范发送 `initialize` 和 `notifications/initialized`，后续 HTTP 请求携带协商后的 `MCP-Protocol-Version`。服务文档列出允许的 HTTP Host、认证方式、可选的事件流、请求上限以及过载或超时时的返回行为。HTTP 连接可由服务关闭，客户端应支持重连。连接断开时，调用方需要确定原请求的结果或确认操作可安全重复，才能自动重试。参见 [MCP 生命周期](https://modelcontextprotocol.io/specification/2025-11-25/basic/lifecycle)和[MCP 传输规范](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports)。

其他 API 沿用该服务已经公开的协议并记录版本。发布新接口时，记录消息边界、并发语义、请求和响应大小上限，以及超时、取消和错误格式。相同的服务从不同传输接入时，使用同一套结果和错误语义。

## 已有入口

- zrun 命令服务使用 `$XDG_RUNTIME_DIR/zrun/mcp.sock` 和 MCP Streamable HTTP。原生 HTTP 客户端、CLI 和 stdio 转发器可接入同一命令队列并共享缓存。zmcpio 已直连默认 socket，完成 MCP 2025-11-25 初始化、工具发现和命令调用。[zrun 命令服务](https://github.com/LIghtJUNction/zrun/blob/main/docs/agent-shell.md)
- zcalld 的用户网关支持 `$XDG_RUNTIME_DIR/zcalld/gateway.sock`，继续提供 OpenAI 兼容 HTTP API。[zcalld 配置和服务管理](https://github.com/LIghtJUNction/zcalld)
- zuse 接受 `zuse mcp --socket PATH`，当前由调用方指定路径。[zuse MCP 用法](https://github.com/LIghtJUNction/zuse#mcp)

新接入的本地验收覆盖默认路径、显式路径、权限、重复启动、正常退出清理、协议初始化及一次实际调用。服务若提供并发或结果复用，再用多个独立客户端确认它们访问的是同一实例。
