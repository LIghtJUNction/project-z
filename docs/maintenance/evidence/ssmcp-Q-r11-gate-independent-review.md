# SSMCP Q / r11：完整 Gate 原件独立复核

## 结论和适用范围

没有发现阻断这份历史 Gate 证据的矛盾。固定源码 **Q `647bce2ec9cf74beab43adea831c2e0712d28ea8`**、tree `5143f90c05066c95b2df58a9eab1831e05888a62` 的原始运行 `ecfe8f69dcb362096018be9a632ff96c` 已完成 **35 个阶段，全部退出 0**。本次仅读取并核对已有证据，没有运行候选、原验证器、Cargo、产品测试或锁获取。

这份结论只属于 Q / r11。原负责人已报告 Python UI 夹具仍有旧 None 预期，正在准备最小后继；本审查未固定后继 SHA，也不把 Q 的结果用于后继、UI、运行时 A/B 或最终 P1。旧 C 的失败原件保留。

## 测试计数

| 范围 | 原始结果 | 计数边界 |
|---|---:|---|
| 完整 Gate | 35 阶段退出 0 | 其中 26 阶段产生 Rust 父测试结果 |
| library private | 2050 passed，23 ignored，6 filtered | private 清单 2073 项 |
| library host | 6 passed，0 ignored，2073 filtered | 六个精确名字与 private 互斥；二者覆盖 2079 项总清单 |
| ordinary integration | 19 个 target 阶段，101 passed | 两个 target 普通选择为零，保留各自 ignored 边界 |
| zuse worker integration | 1 passed | 单独 `--ignored --exact`，不是 ordinary |
| 额外 mandatory ignored | 4 阶段，14 passed | code_mode 2、two_tools 7、workspace_bridge 3、context_helpers 2 |
| 原 17 项目标用例 | 17 条原始 `... ok` 均存在 | 属于 private 2050 的子集，不另加计数 |

20 个 integration 阶段合计 102 passed，必须表述为 **101 ordinary + 1 ignored-exact worker**。原负责人初始 review 的 ordinary 标签偏宽，已用独立的 count-clarification 原件修正，未改测试或原始日志。嵌套子进程的 `test result` 已逐行对应，未加入父结果合计。

两个 Clippy 命令及其实际 `--offline --locked --workspace --all-targets -- -D warnings` 参数均已核对，其中一条另含 Windows GNU target。它们成功退出，日志仍包含 Cargo 清单层的 `unused dependency qrcodegen` 警告；本审查不称“零警告”。

## 源码、依赖和编译产物

三个证据包共 **202 份文本** 已逐份核对字节数和 SHA-256，涵盖 35 日志、55 probe 的 stdout/stderr、四个 Cargo JSON 记录及实际 wrapper 记录。26 个 selected compiler artifacts 全部 `fresh=false`；原 Cargo JSON 和原日志解析出的对象逐项相等，wrapper 的 cwd、源码参数与 metadata target 相符。原 wrapper 仅保存关键编译参数及完整 argv 的摘要/长度，本审查不声称重算了未保存的完整 argv 字节。

前后两份实际 locked metadata 完全同字节：277 包 = 264 registry + 12 Git packages + 1 根 path package。11 是 Git checkout 数；`zplugin` 和 `zplugin-macros` 共用同一 checkout。源码 manifest 的 1849 entries 包括 **1545 文件和 304 目录**，不是 1849 个文件。Cargo.lock、九个启动输入、原工作树 Q 身份及干净状态、runtime tools 和 code-mode runner 前后保持一致。依赖清单本体已读取并核 hash；完整依赖源目录的前后逐文件复核是原 Gate 的记录，本审查没有再执行一次依赖审计。

五个受控产物是一个 debug 测试可执行文件、三个 release 二进制和一个 release 示例。本次额外只读散列了这五份自有副本，均与原 Gate 的 link-output → Cargo executable → owned copy 记录相符，读取期间文件状态稳定：

| 产物 | profile | 字节 | SHA-256 |
|---|---|---:|---|
| `library-test-fixture` | debug test | 166,657,104 | `2b2771c074ffbd8c4a73b9ea8805df162ba86190bebe52a4e69b66d2653fc7b8` |
| `ssmcp` | release bin | 15,738,696 | `2dbab2aa293ae411de20f9839d574bf62ef79a644710884a81f6fe6239717e35` |
| `ssmcpd` | release bin | 8,176,168 | `e2e63fcfc63c05ca81907c976f8f3dda2aee65db9efa6d0d242fba69b95271b0` |
| `ssmcp-frontend` | release bin | 1,386,584 | `2e19f8ad2fea673f899bbfc44449161e072381571946b85e3c6a5dc7e8325a06` |
| `vt_snapshot` | release example | 440,984 | `efdbeb3f200fcf4404b2612d836433047ecc90eb0744f345fc971ee7441db97f` |

额外 debug `CARGO_BIN_EXE_ssmcp` 有独立编译链，属于 integration-compile 的 21 个记录，不算上述第五个或第六个受控产物。本次没有重读可能被其他作业覆盖的共享 target ELF；原 link-output 字节等值来自原 Gate 的持锁观测，保留副本的 hash 则由本次独立读取复核。

## 启动和锁的证据边界

原 `start-unit.json`（742 B，SHA `4202e558a03ca3a22d420ded41440ee5e57e3828f962dcaec42fe78199b1ad4f`）记录实际 systemd 提交。它与 outer controller、launcher 和 Gate 均绑定 invocation `880bd12873874a43a7f0a1eb9dc28c91`。原 outer exit（1167 B，SHA `37e9a0929b8b6ea71bf158c5d758a4ebad0f056d63c781f4de7828be0d01885d`）为 0，launcher exit 为 0，并指向 G 的完整 passed receipt。96f 是异步 unit 启动任务，其 exit0/bothEOF 只证明提交完成。

实际代码显示：outer 只获取 source-author lock；bound launcher 单次非阻塞获取共享 Cargo target lock，等待 Gate 和前后身份检查完成后，在 `finally` 关闭自己的 fd。outer 等子进程返回后关闭自己的 source lock，没有第二层 target lock。`held_for_entire_batch=True` 本身是代码写出的声明，不是独立内核取样。

本次 02:34:55.449139 UTC 的只读观察显示该 unit 已 collect：`LoadState=not-found`、inactive/dead、MainPID 0、空 ControlGroup；两个原 PID 723736、723754 均不存在。这是当前观察，不能代替原 systemd 退出事件或全期 `/proc/locks` 记录。没有声称全局锁现在空闲，也没有操作其他作业。

## 可追溯原件

- G：`/home/lightjunction/.local/state/work-maintainer/ssmcp-release21-recovery-20261121/release25-final11`；原完整 receipt 1,282,803 B，SHA `645dd18969232888cbb393e4193542b421706161eaf6ef2af0af6acca553d7ec`。
- Q 源码/tree、HOST6 六项、35/26/20/14 合同均固定。相对已审 c878 producer，bound driver 仅两条源码 SHA/tree 赋值变化，其余字节相同；launcher 仅三处允许绑定的 AST 值变化。
- 控制原件包：`ssmcp-Q-r11-actual-receipts-original.json`，1,446,007 B，SHA `be3ffc6bbaafbc9e8de9a9e6cb39fe860889fbc76d3456d6ce13bb7f805f54c6`。
- 完整日志原件包：`ssmcp-Q-r11-raw-evidence-original.json`，7,113,590 B，SHA `e105a47e90f01791f719cda356449c089c48be30e2aa98cad10098a04a5e78f1`。
- 启动/outer 原件包：`ssmcp-Q-r11-outer-evidence-original.json`，18,399 B，SHA `8767704717fe8d37cc19cf7e33b600702db922ebc4cb961fae31d6fb59ea8c1b`。
- 配套 JSON 保存逐阶段 argv、日志描述符、五产物详细链和其他输入 hash。没有改写旧 C、旧 Q 静态审查或主报告。
