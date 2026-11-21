# HOST6／r11 consumer 静态复核

复核时间：2026-11-21 02:14:50 UTC。结论：**固定 UNBOUND consumer 改动未发现阻断问题；没有实际 consumer、Gate11 或 P1 通过结论。**

## 包与来源

[现有 Drive 原包](https://drive.google.com/file/d/1Hi_udwmvBThG6DuQfGrhkgLLTKu-y7lR/view)已完整下载：105,590 B，SHA-256 `a113a1dc557230452b1607f9036b3c13ce0ac5a9b146ba0d7f745e3f3fcd55c6`。实际为 **18 份载荷＋1 份 MANIFEST，共 19 成员**；逐成员 CRC32、大小、SHA-256、UTF-8 与唯一安全路径均核对通过。没有重复上传。

本次相对于包内固定 baseline 审查，不导入或执行其中的 Python 模块。完整输入描述符、静态推导及范围记录见[独立审查 JSON](ssmcp-HOST6-r11-consumer-independent-static-review.json)。

## 改动确实限定在准备身份与 HOST6

| 部分 | 独立确认的变化 |
|---|---|
| `gate10_binding.py` | 恰 8 个顶层赋值：准备版 driver／launcher、r11 目录与两份输入路径、inventory hash、launcher AST hash。其余整棵 AST 相同，33 个顶层定义（30 函数、3 类）保持原样。 |
| `gate_inventory_gate10.py` | 保留原四项 HOST 测试及顺序，追加两项 socket 测试；`validate_inventory` 只将诊断中的 four 改为 six。其余规则与算法相同。 |
| 相邻 source／dependency helper | 两份文件均匹配 baseline 与 candidate 中相同的固定哈希。 |
| launcher 身份 | 独立重新计算规范化 AST 为 `650ee1a742e423988a068936190c088c6b47b5b2c96b201eb00b3f94c63ea09b`；只规范化三项最终绑定赋值，没有抹去路径或控制流程差异。 |

两份完整 diff 均从实际文件逐字节重建一致。六个 HOST 名称与包内 producer `c878638a…` 顺序相同；35 个总阶段、26 个 Rust 选择阶段、20 个 integration target、14 个强制 ignored 最低集合保持原值与顺序。`zuse_worker_entry` 的单独 ignored-exact 检查也保留，不混入上述 14 项。

## 六项 HOST 仍须实际执行

完整库清单必须恰好包含这六项 HOST 测试；HOST 与 private 必须互斥并覆盖全部清单，HOST 不能进入 ignored 集合。private 命令只跳过这六项，host 命令则按原顺序串行执行六个精确名称。

选择规则从完整清单推导通过数和过滤数，并要求实际原始父级汇总一致。因此未来 host 回执需要六项通过、零失败、零 ignored、零 measured，不能用缺项、空选择或声明计数替代。外层还比较完整 argv、真实 `--list` 记录与原日志；成功行后出现诊断、重复父级汇总或错误的原始计数都会被现有规则拒绝。这些结论来自静态控制流阅读，本轮没有执行负例合同。

14 个 mandatory ignored 是最低要求；实际 code_mode ignored 清单及三个既定 integration 分组中的全部 ignored 成员仍须在相应阶段执行。

## 仍然未绑定

`EXECUTION_ALLOWED=False`、`FINAL_BINDING=None`、`DRIVER_SHA256=None`、inventory 的 driver pin 仍为 `None`。公开入口在读取结果之前拒绝未绑定状态；私有解析器也要求最终 driver pin。准备版哈希不会自动开放执行。

当前包没有 Q 的完整成功 Gate11、源码／锁／依赖清单及五个受控验证产物的最终绑定。后续必须单独冻结并复核实际成功回执与产物身份；本审查不能替代它们，也不采信包外正在运行的任务已完成。原始 C 失败、旧报告及最终 44 仓图均未改变。

本轮只使用下载、原字节读取、散列和 AST 解析。未调用开发机、Cargo、产品或候选验证器，未访问共享锁与 target，未写源码、Git 引用、Drive 或旧报告。
