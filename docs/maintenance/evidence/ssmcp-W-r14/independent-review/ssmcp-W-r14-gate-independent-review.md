# SSMCP W／r14：门禁原件独立复核

固定 W／r14 的 35 阶段门禁已通过，本次只读复核未发现阻断或实质证据不一致。结论仅覆盖这一轮 Gate35；新的 runtime、UI、P1 与最终 44 仓图仍需各自的实际回执。

## 固定身份

- Commit：`4de17310ce2ecdbc8b6c6ab86ee365653f753ee8`；tree：`5be29af415b915ef3307bfed08c6cefec2798898`。
- 唯一父提交：`f42baae1d5227bd6db8315aef778160b80b57274`。
- Run：`3e89242560e0a243bde3d8442ce7e1db`；InvocationID：`96256392e87944e2a00cb78d6c8aff9b`。
- 实际门禁：2026-11-21T05:42:51.112874+00:00 至 2026-11-21T05:56:01.212636+00:00。
- 独立审阅完成：2026-11-21T06:09:54.033330+00:00。

相对 r13 仅修改 scripts/e2e_composer.py 的一个标题字符串：next caller → Next caller。固定 GitHub compare、两个导出文件的逐字节替换，以及独立递归 tree 审查一致；其余 1113 个叶子和四个 gitlink 保持。该 native UI 用例没有在 Gate35 中运行，因此本报告不提前判定原 composer 失败已通过复验。

## 实际计数

| 范围 | 本轮原件 |
|---|---|
| Gate | 35 阶段全部退出 0 |
| Rust 父结果 | 26 个，逐项匹配原日志与选择集合 |
| Library private | 2057 通过，23 ignored |
| Library HOST | 6 通过，与 private 互斥 |
| 普通 integration | 19 目标，101 通过 |
| Worker ignored-exact | 1 通过 |
| 另外 mandatory ignored | 4 阶段，14 通过 |

V2 的 7 个回归和原 17 个目标，在 r14 日志中各自有明确的 ok 行；都是 2057 的子集。没有累加旧运行或嵌套子进程结果。与 r13 比较仅用于确认覆盖集合，35 阶段顺序及各选择集合均保持。

## 证据核验

本轮读取并计算了 213 份文本输入的 SHA，核对 35 份阶段日志、55 个 probe 输出及四份 Cargo JSON 编译记录。导出源码的 1849 项清单（1545 文件、304 目录）在字节、mode 和路径集合上匹配，九项输入在门禁前后及本次读取时一致。

26 个选定产物均为 fresh=false；37 条原 wrapper 记录的 PID、阶段目录和时间对应本轮 Gate。compiler 的 cwd／source／profile，经 link output、Cargo executable 到 owned copy 的记录一致。五份受控副本已重新读取实际字节：library-test SHA 为 `57fb20efb29b2eefabf9dfe0f3b88b0fb58db6e35efce2fb6feec4b3d625fab3`；另外四份与 r13 相同，但各自的新编译记录和新路径字节均已独立验证。

外层控制器、launcher 和 driver 在明确替换源码／路径／输入哈希后与 r13 原文相同。两层仍分别持 source-author 和 target 的 NONBLOCK 锁；原退出记录、run、InvocationID、最终 Gate SHA 相互绑定。exit 文件先落盘、再关闭描述符，因此不单凭文件存在或布尔字段推断锁的实际释放时刻，也不声称全程内核锁轨迹或全局锁空闲。

两个 Clippy 阶段退出 0，保留 unused qrcodegen／manifest warning 的事实。没有重跑产品、测试或 Cargo，没有读取共享 target 当前 ELF，也没有修改旧 r13 证据或源码。

## 交付

- [本轮精简独立审计](ssmcp-W-r14-gate-independent-review.json)
- [源码差异、覆盖和控制器证明](source-controls-coverage.json)
- [213 份文本输入索引](original-text-index.json)
- [固定源码变更](https://github.com/LIghtJUNction/ssmcp/compare/f42baae1d5227bd6db8315aef778160b80b57274...4de17310ce2ecdbc8b6c6ab86ee365653f753ee8)
