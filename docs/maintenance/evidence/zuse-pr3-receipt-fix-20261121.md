# zuse PR #3：回执预算修复与验收

**固定实现已通过 16 项针对性测试及格式、锁文件解析和相关 Clippy 检查；独立静态审查未发现新增阻塞。PR #3 保持草稿，等待原 PR #2 作者整合。**

## 固定来源

| 项目 | 身份 |
|---|---|
| PR | https://github.com/LIghtJUNction/zuse/pull/3 |
| 基线 | `bb838b3573d36ff559c4c901ae7a64a0dd30a2bd` |
| 先行回归测试 | `44ffb599e96c412c216f395ed8b7286f585b5474` |
| 已测实现 | `35664746549c482c99082e6180419b2c0f5ff532` |
| 已测 tree | `0d1d19006dfcf4da8e804f1f27d13d284eb96299` |
| 独立源码目录 | `/home/lightjunction/Documents/GITHUB/pr-core-zuse-receipt-20261121/source` |

这次仅改变 `src/json.rs`、`src/mcp.rs`、`src/script/scheduler.rs`、`tests/script_entrypoints.rs` 和 `docs/scoped-mice.md`。Cargo 清单、锁文件及原 PR #2 分支保持原身份。

## 问题与修复

显式提高 `max_steps` 后，合法脚本可以完成执行却丢失回执。2,500 次纯能力查询超过原 65,536-token 解析上限；2,200 次查询虽能解析，其 MCP 文本与结构化双份结果的转义长度仍超过固定缓冲余量。原始 RED 分别复现 CLI 状态错误、MCP Buffer 错误及摘要契约失败。[固定测试](https://github.com/LIghtJUNction/zuse/blob/35664746549c482c99082e6180419b2c0f5ff532/tests/script_entrypoints.rs)

修复将详细事件限制为有界前缀，使用实际 parser token 数并为最终字段保留余量；后续详情通过 `events_omitted` 明确计数。执行仍遵守原步数、等待和资源预算，默认 256 不变。`cleanup.attempted/failed` 独立于可省略详情；操作失败、取消和清理失败继续保留，双失败也不会丢掉其中一项。[调度器](https://github.com/LIghtJUNction/zuse/blob/35664746549c482c99082e6180419b2c0f5ff532/src/script/scheduler.rs)

MCP 只对已经算出的结果重做一次编码，按 Writer 的实际 `needed` 分配，继续受 32 MiB 输出上限约束。重试不会回到执行入口，因此不会重放输入动作。[编码修复](https://github.com/LIghtJUNction/zuse/blob/35664746549c482c99082e6180419b2c0f5ff532/src/mcp.rs)

## 实际验收

| 阶段 | 固定源码 | 实际结果 |
|---|---|---|
| RED，作业 `5dd` | `44ffb599`，原生产源码 | 入口 2 项失败、摘要 1 项失败；两个 Cargo 命令均 exit 101；编译成功 |
| GREEN，作业 `611` | `3566474` | 入口 6 passed，scheduler 10 passed，0 failed / 0 ignored |
| 静态门禁 | `3566474` | locked metadata、rustfmt、diff check、相关 Clippy 全部 exit 0 |
| 独立审查 | `3566474` | 0 新增阻塞；未另运行测试 |

16 是不同测试函数的数量。五种 MockHost 结果属于其中一个测试，不额外累加；RED 原矩阵在首个失败处停止，也没有冒称所有子情形都在 RED 跑完。MCP 用例确实在一个 stdio 子进程中依次发送 2,200、2,500、随后 1 次查询，核对三次响应与正常退出。全部运行都没有 DISPLAY/Wayland 输入会话或真实输入设备操作。

完整 argv、cwd、退出码、时间和日志哈希保存在两份原始 `result.json`，没有改写失败回执。GREEN 的主要命令为：

```sh
cargo test --offline --locked --message-format=json-render-diagnostics --test script_entrypoints -- --test-threads=1
cargo test --offline --locked --message-format=json-render-diagnostics --lib script::scheduler::tests:: -- --test-threads=1
cargo clippy --offline --locked --message-format=json-render-diagnostics -vv --lib --bin zuse --test script_entrypoints -- -D warnings -Cmetadata=zuse_receipt_3566474
```

## 产物与资源证据

真实 compiler-artifact 显示 CLI、库、入口测试、scheduler 测试和 Clippy 三个根目标均 `fresh=false`。Clippy 原始 `-vv` 第 19、21、23 行记录固定源码目录的实际 `clippy-driver` 调用。早期摘要中一个查找字面 `CLIPPY_ARGS` 的字段为 false，仅表示该环境值没有打印在日志中；原始回执保留，解释另存 v2，不重跑已通过的 lint。

验收时实际 CLI 为 17,454,768 B，SHA-256 `04deac62ad725723f36d99baafa95591778d3b1742fccbbfc9ced2dd269003b0`。其路径是共享 target 输出；哈希在外锁内记录，后续路径内容可能被其他合法构建替换，不能将它当作永久不变的已交付二进制。

两个批次均使用共享 target、整批 outer flock、单 job、2 GiB 内存与 2 GiB swap 上限。驱动记录真实父 `flock` 的 argv、PID 与 `/proc/locks` 匹配；完成后的只读 scope 回执均为 inactive/dead、ControlGroup 空。本报告不声称全局锁此后一直空闲。

## 证据位置与边界

- RED 原件：`/home/lightjunction/Documents/GITHUB/pr-core-zuse-receipt-20261121/gate-red/result.json`，5,875 B，SHA-256 `91bc831b300b6de0a2625e721bf12f98ab1b201c72f3ddc868c6025ce54bc46f`。
- GREEN 原件：`/home/lightjunction/Documents/GITHUB/pr-core-zuse-receipt-20261121/gate-green/result.json`，9,510 B，SHA-256 `a3c05be4ab48fe50b18fe459ff23344e5b425f3f33d594c82acec555e6b2c0db`。
- [机器可读交付](zuse-pr3-receipt-fix.json) 包含逐命令、源码、锁定 Git 包、产物与审查来源。
- [独立静态审查](zuse-pr3-independent-static-review.md) 绑定同一固定提交；当前回执与 MCP 外层静态合计最多 65,338 tokens，低于 65,536。未来字段变化需要重新核算。

本次没有复跑原 PR #2 的 286 项 Rust、20 项 no_std、交叉编译或私有原生验收，也没有改动 SSMCP 冻结组合、main、发布 tag 或下游依赖。那些证据仍属于原作者与原固定源码，后续集成由对应负责人处理。
