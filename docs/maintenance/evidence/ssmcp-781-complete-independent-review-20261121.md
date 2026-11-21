# SSMCP 781 完整 baseline：独立回执核对

## 结论

现有原始文件能够支持：**固定 `781b87df1d364137b6885f17f631a3e9e991bd58` / tree `6bf7beb143cfdce3878df856c27785164695430f` 的这一轮六样本和 Ctrl+V baseline 已按记录通过。** 本次独立复核未发现归档、来源身份、检查项数量或时间计算不一致。

复核只读取 JSON／ZIP 和既有构建、产物读回记录，没有重新运行程序、构建、GUI 或测试。它不证明后续优化、最终 P1、runtime-18、完整单元套件、发行门禁或新 main 的验收。

## 原件与来源绑定

ZIP `original-receipts.zip` 为 **13,644 B**，SHA256：

`2bd9cbcd765399c4f782e97cc9b47351f03fbe3f650685e16b0e8e29b92998f2`

归档恰有 3 个原始 JSON 和 1 个 manifest；无重复/额外成员，CRC 完整。3 个 payload 与 cloud 原件逐字节一致，长度和 SHA256 均符合 manifest。内嵌 manifest 也逐字节一致。

| 原件 | Bytes | SHA256 |
| --- | ---: | --- |
| execution-receipt.json | 29,263 | `aefc6b8a20c8bec808057acae758c60fb44630c5912cb1851cced2a7dc2eef63` |
| six-cases-report.json | 19,660 | `7b7c9081616aca563d74efe883cd716e6be8da594e2671e283c904a7b096c64c` |
| ctrlv-report.json | 13,333 | `df1d570ed1bbcf8e47d6a4e99c94d06357319ebc0ca22a9c5e9d3d82b05498d4` |

两份运行报告绑定到 79,446 B 的构建回执 `d2204375614807af510f6c7fd08ec657d212a98f18f504cb21376c63f47ea7c0`。其 source/tree、锁文件、gitlinks 与既有独立构建审查一致。运行报告中的 revision 字段自述为 caller-declared；此处依据完整构建回执和匹配的实际产物链闭合来源，未单凭该字段认定版本。

5 个构建产物均记录 `fresh=false`，实际 source argument、link output、Cargo target、保存副本及此前原生 SHA 读回一致。其中 **4 个运行使用项**——ssmcp、ssmcpd、library-test-fixture、vt_snapshot——在两份运行报告中均有相同的前后哈希。第 5 个 ssmcp-frontend 的身份来自构建与此前读回，不能声称本轮夹具执行了它。

输入快照前后均为 360,244 B、SHA `c651e2462799aceb4945cc13664896034e62fb8fc045e059131410c805c29321`。运行 product 指纹覆盖 800 个文件，SHA `974ec9c112928f0e42a414e4dc4a65569760391d3ba7f9a37801c1aa22a094e2`；两运行报告一致，9 个 frozen helper 也与执行 cohort 一致。完整输入快照原件未包含在这个小 ZIP 中，前后不变属于原生 producer 记录，本审查核验其跨文件一致性。

## 检查项与样本

six-cases 与 ctrlv 两步骤均为 exit 0、stderr 0 B。原始 `passed_checks` 列表分别确有 **80** 与 **31** 项，包含初始化、权限、重复路由和样本断言；**不能写成 111 个 Rust 单元测试**。

下表由每个样本的原始 monotonic_ns 时间戳独立重算，全部与报告浮点值相符。每行是一次记录，不是均值、分位数或优化比较。

| 样本 | 预期结果 | PTY 首字节写入至可见完成 ms | PTY 最后字节接收至可见完成 ms |
| --- | --- | ---: | ---: |
| 多行 2,738 B | 私有引用文件 | 67.904495 | 67.896572 |
| 多行 64 KiB | 私有引用文件 | 34.839222 | 31.049540 |
| 多行恰好 4 MiB | 私有引用文件 | 370.222459 | 39.763628 |
| 多行 4 MiB + 1 B | 拒绝且不建文件 | 337.795869 | 9.789428 |
| 普通非 bracketed 16 KiB | 完整 inline | **2439.160607** | **2439.137164** |
| 后台输出中多行 2,738 B | 私有引用文件 | 43.186361 | 43.178628 |
| Ctrl+V 导入 2,738 B | 私有引用文件 | 50.066292 | 50.059631 |

`ready` 指完成引用／inline／拒绝的物理 VT 解码帧，出现在后续正确性 RPC 之前；计入 VT 解码成本。PTY 最后字节被接收不代表客户端已经读完，也不是磁盘 fsync 完成时间。测试只断言有界活性及正确性；**普通 16 KiB 约 2.439 秒是 baseline 观测，不是优化结果或性能达标结论**。来源：[六样本原件](ssmcp-781-complete-baseline/six-cases-report.json)、[Ctrl+V 原件](ssmcp-781-complete-baseline/ctrlv-report.json)。

## Busy、剪贴板与锁边界

Busy 样本记录 producer 输入前后均在运行，字段 `busy_output_ticks_during_input=20`，并记录输入前与 ready 后真实输出。首个 post-ready 输出在 ready 后 **0.584604 ms**，后观察窗口持续至 ready 后 **748.808433 ms**。保留 20 这一 producer 计数，但未把它换算成“43 ms 内 20 次”速率，也未声称拥有逐 tick 的时间证据。

Ctrl+V 只写一个真实 PTY 字节 `0x16`，production adapter 调用私有 PATH 中受控的假 `wl-paste`，导入合成 UTF-8 数据；记录了 MIME 一次读取、原始字节/私有权限、草稿引用与未自动发送等检查。**没有读取 OS clipboard，50.066292 ms 不能推广为真实 Wayland/X11 系统剪贴板性能。**

执行回执记录共享 quiet/outer 锁 device 34 / inode 63537699，自 **2026-11-20 23:34:02.929762 UTC** 持有至 **23:34:30.313629 UTC**，覆盖两步骤和最终输入检查；释放发生在 execution finished 之后。本次未探测当前锁持有者，不能由旧释放时间断言现在锁空闲。隔离记录为 synthetic payload、无真实用户凭据、无外部模型、未触及既有服务；回执中的“production account router”指隔离环境运行的产品实现，不代表线上服务。来源：[执行回执](ssmcp-781-complete-baseline/execution-receipt.json)。

## 保存范围

先前失败尝试与 build-only 回执保留原样；这份成功记录只为同一固定来源补足此 baseline 的运行证据。原始 VT 流、图像、完整输入清单和五个二进制均不在这个只含 JSON 的小归档中；相关 native 路径与哈希保留在原件和独立 JSON 内。

独立 JSON：`ssmcp-781-complete-baseline-independent-review.json`。已有构建证明：`ssmcp-781-baseline-build-receipt.json`、`ssmcp-781-baseline-build-independent-review.json`、`ssmcp-781-preserved-artifact-readback.json`。

