# U/r12 第二次 UI 失败：限定原件核对

**结论：两份固定原件在本次核对范围内一致；该批 UI 验收仍然失败。** 实际完成 9 个套件，第 10 个 session_groups 在收件人选择器断言失败；其余 14 个计划套件未运行。没有完成全部 UI 或 P1。

源码为 784370b5fe1b817c788273a5f7b1ab826c743965，版本元数据 0.10.25。原回执时间为 2026-11-21 03:53:48—03:56:39 UTC，记录 171.074 秒。本次只读取 acceptance.json 和已脱敏的 session_groups/run.log，不运行产品或测试。

## 套件与 alias 计数

24 个计划执行包含 10 个已启动：9 passed、1 failed、14 not_run。逻辑清单另含 human_finish alias，共 25 项。该 alias 由已经通过的 interactions 覆盖一次，没有独立执行，也不额外增加独立通过数。

| 前九个通过的套件 | 回执检查数 |
| --- | ---: |
| message_references | 53 |
| force_send | 137 |
| listener_transports | 74 |
| zuse_worker | 31 |
| interactions | 172 |
| private_desktop | 35 |
| account_compat | 69 |
| input_history | 150 |
| reload_state | 37 |

以上是各套件原有检查数，不相加成新的唯一测试总数，也不并入 Gate35、runtime18 或前次 UI 结果。

## checks 0 与 21 条 PASS 的区别

失败行在 acceptance.json 中**没有 checks 键**。root 读取的 b37 wrapper 输出为 checks 0；这不能解释成零断言。原日志包含 **21 条 setup PASS 记录**，末尾原 JSON 也明确记载 status failed、checks 21、frames 0。

这些 PASS 覆盖私有账号／OAuth 建立、一个 source PTY 和两个收件进程启动，以及认证目录身份检查。随后失败的是 the explicit native recipient picker，终端文本显示没有匹配的已验证收件人，并保留草稿。21 条记录不是 session_groups 全套通过；frames 0 只保留日志自身口径。

原件未记录当时目录缓存的完整现场。本核对没有扩大到产品源码或驱动语义审查，不据此认定最终根因。

## 回收与输入身份

回执中 10 个已启动 child 均记录 owned_child_reaped=true，包含 exit 1 的失败 child。失败行没有内部 cleanup 汇总，不能补称其全部内部孙进程清理已经独立核实。本次也没有读取当前进程表。

10 组完整 inputs_before 与 inputs_after 逐结构相等；顶层记录的输入集合摘要前后同为 19e4cefb584e1ec5fc0d01274f517e4794c21c18dad74879656dad9ffc320907，changed 为空。本次没有重新读取这些输入文件或大 ELF，也没有独立重算未审查的顶层 hash 公式。

## 后续范围

按协调者转交的 seq887/889 决定，保留原 session_groups 夹具，由原作者修复 cold query 异步刷新后的匹配行为；七行预热夹具未采用、未执行。这是后续工作安排，不是已验证的修复。U 的九组通过及本次失败都不能转记为后继源码的结果。

完整逐项状态、原件路径／字节数／SHA、21 条原始 PASS 行号和读取边界见[结构化核对](ui-second-failure-independent-read.json)。两份原件前后字节、inode、大小与 mtime 保持不变。没有修改主报告、源码、Git refs、Drive、锁或最终 44 仓依赖图。
