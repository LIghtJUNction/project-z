# SSMCP V2／r13：原始门禁证据独立复核

固定源码的 35 阶段门禁已通过；本次独立只读复核未发现阻断或实质证据不一致。结论仅覆盖这一轮 Gate35，不代表后续 runtime、UI、P1、正式发布或最终 44 仓图已经通过。

## 固定身份

- Commit：`f42baae1d5227bd6db8315aef778160b80b57274`；tree：`64b40eb8a3e0188076cf376229d3d87074d27dcc`。
- 唯一父提交：`18f43d69715538582ddc2806434009170f188e3c`；源码版本 0.10.25。
- Run：`f6121dd70d3f8c4fb3d747a9bf2697bf`；unit：`ssmcp-release25-gate35-r13-20261121.service`。
- 实际门禁：2026-11-21T04:59:22.538104+00:00 至 2026-11-21T05:09:54.138883+00:00，持续 631.600780 秒。
- 本次审阅完成：2026-11-21T05:27:55.992049+00:00。

## 实际执行与计数

| 范围 | 本轮原始结果 |
|---|---|
| Gate 阶段 | 35 个阶段均退出 0 |
| Rust 父结果 | 26 个，与原日志最后一个父汇总及选中清单逐项一致 |
| Library private | 2057 通过，23 ignored；6 个 HOST 不在此组执行 |
| Library HOST | 6 通过，与 private 集合互斥 |
| 普通 integration | 19 个目标，101 通过 |
| zuse worker | 1 个 ignored-exact 用例独立执行并通过 |
| 额外 mandatory ignored | 4 个阶段，14 通过 |
| Python policy | release-policy 100 通过；deployment-policy 35 通过，均包含在 35 个阶段内 |

新增 7 个 V1/V2 回归和原需求的 17 个目标均在本轮 private 日志中各有唯一明确的 ok 行，属于 2057 的子集。没有把它们、嵌套子进程汇总或历史 r12 成绩重复相加。与 r12 比较时只核覆盖集合：35 阶段顺序、20 个 integration 清单、HOST6 和 ignored 选择保持；private 仅新增这 7 个用例，没有删除测试。

## 源码和产物身份

本次读取并校验 213 份文本输入，核对全部 35 份阶段日志、55 个 probe 的 stdout/stderr，以及四份 Cargo JSON 编译记录。当前导出源码的 1849 项清单，包括 1545 个文件与 304 个目录，字节、mode 和路径集合全部匹配；主源码与四个子模块 archive 的提交头也相符。九项固定输入的门禁前后 SHA 与本次只读实测一致。

26 个选定产物均记录 fresh=false。实际 workspace wrapper 的 cwd、源码路径和编译参数，与 Cargo package、manifest、target/profile 一致；从保存的编译参数推导的 link output，和 Cargo 可执行文件、owned copy 的原始大小／SHA 逐项一致。本次再独立读取五份受控副本的实际字节：一个 debug library-test、三个 release binary、一个 release example；不是“五个 release ELF”。

| 受控副本 | 字节 | SHA-256 |
|---|---:|---|
| library-compile/library-test-fixture | 166677776 | `c69dee8ced668ac1bbe39da83b19c9c419d1acb9c1c2b006b8cbc115aa499e0d` |
| release/ssmcp | 15750352 | `d654703a12f9479e97b9807ac8d61f370bd5c413963bf6e5b6e45dfbd8434f41` |
| release/ssmcp-frontend | 1386584 | `2e19f8ad2fea673f899bbfc44449161e072381571946b85e3c6a5dc7e8325a06` |
| release/ssmcpd | 8176168 | `c1991fac3c0c6aa0a229781c87fe67ef24c028fd5ffc88b0c50dc413baaa5527` |
| decoder/vt_snapshot | 440984 | `efdbeb3f200fcf4404b2612d836433047ecc90eb0744f345fc971ee7441db97f` |

依赖元数据为 277 个包：264 个 registry、12 个 Git、1 个 root path；12 个 Git 包来自 11 个 checkout。此处核验元数据和原依赖审计记录，没有重新遍历所有外部依赖源码。

## 退出与边界

原始 unit invocation、外层控制器、launcher、最终 Gate SHA 和 run/source 相互绑定；外层及 launcher 均退出 0，时间顺序一致。另有独立静态审查核对 source-author 外锁与 Cargo target 锁的唯一持有层级及关闭路径。只读审阅没有取得锁、发送信号、运行产品或 Cargo，也未读取共享 target 当前 ELF。

两个 Clippy 阶段退出 0，但均有 unused qrcodegen／manifest warning，因此不声称零警告。原 wrapper 保存关键参数与完整 argv 的摘要，未保存完整 argv；本次没有重算缺失的完整 argv 摘要。记录支持这一轮退出链，不等同于全期内核锁轨迹，也不说明当前全局锁空闲。

后续 runtime、UI、P1、发布与最终 44 仓图须以各自新回执单独评估。旧 U/r12 的成功和失败记录保持原身份；本次没有把相同哈希视为继承旧验收的依据。

## 证据

- [完整独立复核](ssmcp-V2-r13-gate-independent-review.json)
- [简明机器可读摘要](ssmcp-V2-r13-gate-review-summary.json)
- [213 份文本输入索引](original-text-index.json)
- [覆盖集合比较](contract-comparison.json)
- [独立锁与退出链复核](lock-exit-independent-review.json)
- [固定 GitHub commit](https://github.com/LIghtJUNction/ssmcp/commit/f42baae1d5227bd6db8315aef778160b80b57274)
