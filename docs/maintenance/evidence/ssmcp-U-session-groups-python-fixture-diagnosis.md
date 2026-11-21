# 冻结 U：session_groups Python 夹具窄诊断

**最终处置：原作者修产品首次冷态查询，保留原 session_groups 夹具回归。** 本只读调查确认了两组夹具的前台目录就绪时序不同，但没有记录 b37 失败瞬间的缓存内容，不能宣称运行根因已证实。此前提出的夹具预热候选已明确**未采用、未执行**；相同 `mode=shell` 也不能作为已确认原因。本次没有修改或运行任何夹具。

完整来源身份与位置见 [诊断 JSON](ssmcp-U-session-groups-python-fixture-diagnosis.json)。冻结源码根目录为：

`/home/lightjunction/.local/state/work-maintainer/ssmcp-release21-recovery-20261121/release25-final12/source`

## 1. 原始失败确实执行了 21 项 setup 检查

已读取唯一指定原日志：

`/home/lightjunction/.local/state/work-maintainer/ssmcp-acceptance-recovery-20261121/u-ui24-acceptance-mesa-v1/suites/session_groups/run.log`

字节数 **10,563 B**，SHA-256 **18f2fed2e00bff5823288f6a2d089ef37b85a048f7c48400c3f4a68fe2c41fe4**，与提供值一致。日志前 21 行均为 PASS：17 项账号／连接 setup、1 项三个独立受控进程存活、3 项精确服务端目录描述符。最后一行记录 `failed / checks=21 / frames=0 / 9.768s`。外层 wrapper 的 checks=0 不能解读为没有执行断言，这 21 项也不能改称 21 个 Rust 单元测试。

失败链为 `e2e_session_groups.py:179 → select:90 → e2e_interactions.py:115 → e2e_input_history.py:151`。第一次查询的是 process A 的 `client:<id>`。UI 留在原视图，提示 **No verified native recipient matches this name · draft retained**；原分组选中、投递和回执断言尚未到达。

## 2. 实际差异在 UI 就绪时序

| 位置 | 已核实行为 |
|---|---|
| `scripts/e2e_session_groups.py:150–179` | 启动前台和 A、B 两个普通 peer，创建 A 的一个受控 collab member；独立 `messages.list` 确认三个精确身份 online/sendable，随后直接进行首次精确 ID picker 查询。没有先观察前台目录已经收到这些身份。 |
| `scripts/e2e_interactions.py:472–490` | 先用空查询打开 picker，再启动同类 peer；通过 `quiet_until` 等该 peer 的名称真实出现在源 PTY，期间不注入键盘输入，随后才做选择与发送。 |
| `scripts/e2e_interactions.py:537–548` | 查询精确 agent ID 前，同样先打开空 picker、创建成员并等待该成员名称出现在 UI。 |
| `scripts/e2e_input_history.py:139–151` | 8 秒 `wait_state` 只 pump 和读取前台状态，不再次发送 `/message`，也不确认目录刷新已完成。 |

服务端目录检查成功，证明服务端知道这些身份；它没有证明前台接收者快照已完成加载。当前缺少失败瞬间的前台目录内容及刷新完成时序，因此只能把首次查询与目录刷新顺序列为有根据的候选。

Core 的独立固定 U Rust 检查另报告：身份过滤没有 `mode=shell` 条件；空／非空查询均先发起刷新再读取快照，非空无匹配时在切换 Agents 视图之前返回。这些是 Core 的独立代码核对，本 Python 审阅没有重复审计 Rust 或把静态路径说成运行复现。

## 3. peer 参数与角色没有发现差异

两组均沿 `SessionGroups → Interactions → InputHistory → Composer → Dashboard → Harness` 使用 `scripts/e2e.py:558–576` 的同一个 `start_client`。调用只给 label、name、cwd，没有显式 harness、model fixture 或不同的 extra_env。

`e2e.py:452–453` 转发至 `e2e_account_gateway.py:159–164`，两者采用相同参数结构：

`ssmcp --server <owned-origin> --name <fixture-name> --shell /bin/sh --no-setup --reconnect-delay 1`

`start_client` 只等连接凭据记录（最长 10 秒），不等待源前台的接收者缓存。两组也使用同一受控环境 helper；本次只读 helper 源码，没有打开实际生成的账号、认证或配置文件。

## 4. 已提出但未采用的候选，以及最终处置

Root 后续转交原 native source／acceptance 负责人 seq887／889：**原作者正在修产品冷态查询，保留原 session_groups，不采用 7 行夹具预热。** 原作者指出，全空目录下空 `/message` 也可能早退，因此预热既不能保证建立所需前置状态，也不能掩盖首次精确查询的产品问题。最终建议是由该唯一负责人完成产品修复，沿用原用例获得固定源码的回归证据。本审不增加实现、诊断或复现。

以下仅保留先前提出的候选及其适用前提，**不是当前采用的修复方案**：

若当前 group 用例的前提是“接收者已在 UI 就绪”，可在首次 `select(front, recipients)` 前使用已有空查询 `open_picker(front)`，再沿用已有 `quiet_until` 等 **Group process A、Group process B、Exact group thread** 三个唯一 fixture 名称出现在受控源 PTY。之后继续原 `select`，保留精确 ID、选中身份、空 inbox、无隐式发送及所有后续收据断言。

不要用固定 sleep、放宽原 8 秒／9 秒时限、宽泛重试或改变 peer 模式来取得通过结果。应保留本次冷态精确查询的失败日志和真实 checks=21。

这项候选仅补夹具前置同步。**若产品契约要求第一次冷态 `/message <id>` 自动等待目录并成功，则需要原负责人单独依据契约与回归测试处理；等待预热后的夹具通过，不能证明冷态产品路径已正确。** 本次未应用补丁、启动新复现、运行 Cargo／GUI／模型或触碰任何已有进程、锁和认证目录。
