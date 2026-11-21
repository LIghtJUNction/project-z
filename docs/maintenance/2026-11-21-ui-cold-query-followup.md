# Project Z：UI 首次精确查询后续记录

**状态快照：2026-11-21 04:15:48 UTC。** SSMCP 的冻结 U 已完成 35 个 Gate 阶段和 18 项消息运行检查；第二次完整 UI 验收在第 10 个独立套件 `session_groups` 失败。原作者正在修正首次精确查询时的产品处理路径，原测试用例保留。新补丁和新版本验收尚未完成。

本记录补充 [03:42:51 UTC 主报告](https://github.com/LIghtJUNction/project-z/blob/c08d6e894efd1b8f134ae5abb55f66cb6e2ac178/docs/maintenance/2026-11-20-pr-and-dependencies.md)。该报告已由 `c08d6e8` 发布；随后维护分支通过正常双亲合并 `efe912e` 纳入主线 `be64e5a` 的七个发布工具文件。[PR #7](https://github.com/LIghtJUNction/project-z/pull/7) 仍为草稿。此次补充不重新计算原 85 项 PR 的统计，也不把原 U 的结果转记到后继源码。

## 已完成与仍待完成

| 环节 | 当前证据与边界 |
|---|---|
| U / r12 Gate | 35 阶段通过，原报告包含独立原件审阅。 |
| U 消息运行检查 | 18 项通过；根审阅限定为原始回执与输入身份核对。 |
| 第二次 UI | 24 个独立套件计划，10 个已执行、9 个通过、14 个未执行；另有 1 个别名覆盖，不计为独立执行。 |
| 已通过检查数 | 前 9 个套件的记录数相加为 758 项，不作为去重测试总数；失败套件另有 21 项准备检查通过。 |
| 后续 P1 | 尚未执行。zcalld `bd7a30c` 的窄构建／help／curl 门禁已通过，不能替代 P1。 |
| 最终 44 仓库验证 | 尚未执行。仍等待产品修复、UI／P1 与所需依赖实际集成。 |

SSMCP 的本轮结果固定绑定提交 `784370b5fe1b817c788273a5f7b1ab826c743965`、树 `2c60d011da8c2b31aefd80367bf7f19e28f10b62`。第二次 UI 作业 `…-b37` 已退出 1、双输出流均到 EOF。十个已启动子进程均有已回收记录，十组完整输入记录前后一致。失败条目没有内部 cleanup 汇总，本次不扩大为其全部内部进程已独立核验。详见[第二轮 UI 独立核对](evidence/ssmcp-U-ui24-second-attempt/ui-second-failure-independent-read.md)、[脱敏原始日志](evidence/ssmcp-U-ui24-second-attempt/run.log)及[结构化记录](2026-11-21-ui-cold-query-followup.json)。

## 第 10 个套件实际发生了什么

失败发生于第一次 `/message client:<id>` 查询：界面保留会话视图及草稿，显示没有匹配的已验证接收者。原日志先完成了 17 项账号／连接检查、1 项三个受控进程存活检查，以及 3 项精确服务端目录检查，共 **21 项**。分组选中、投递和回执断言尚未到达。

外层 wrapper 输出 `checks=0`；`acceptance.json` 的失败条目本身没有 `checks` 字段；原 `run.log` 末尾明确记录 `checks=21`、`frames=0`。因此这里的零不能解释为没有执行断言。这些准备检查也不是 21 个 Rust 单元测试。

此前第一轮 UI 在私有 Xvfb 初始化时失败。执行负责人随后只在私有套件环境中明确选择 Mesa 软件渲染；第二轮的 `zuse_worker` 31 项与 `private_desktop` 35 项已实际通过。这个结果证明本次私有显示初始化已越过先前故障，不代表真实物理 GPU 或生产桌面验收。

## 源码核对与当前修复方向

两组夹具创建 peer 的参数相同，均使用普通 shell 客户端。客户端的接收者过滤检查身份和账号字段，并不以 `mode=shell` 排除接收者；完整 `client:<id>` 也是受支持的精确匹配形式。

代码会先排队请求异步目录刷新，再立即查询现有快照。没有匹配时，它在切换到接收者视图之前返回；稍后的目录回复只更新缓存，不会自动重做这次查询。已通过的 interactions 用例先观察接收者出现在前台；失败的 session_groups 只确认服务端目录就绪，就发起首次精确查询。这些源码事实支持刷新顺序的解释。**失败瞬间的前台缓存与回复时序没有被保存，因此本记录不宣称已直接观察到现场缓存为空或陈旧。**

原负责人已决定由原作者修正产品的首次冷态查询行为，并保留原 session_groups 用例作为回归。曾提出的七行夹具预热候选**未采用、未应用、未执行**：完全空目录下，空查询本身也可能提前返回，预热后的通过不能证明首次精确查询正确。参见[Python 夹具独立诊断](evidence/ssmcp-U-session-groups-python-fixture-diagnosis.md)及其[完整来源记录](evidence/ssmcp-U-session-groups-python-fixture-diagnosis.json)。

后续顺序是：审阅原作者最小产品补丁，为新源码重新绑定验证，完成原完整 UI 和 P1，再推进相应合并与最终 44 仓库验证。现有唯一源码写入者和 UI／P1 执行窗口保持协调。

## 报告位置与其他项目状态

- [Project Z 维护 PR #7](https://github.com/LIghtJUNction/project-z/pull/7) 保存已发布主报告、主线发布工具合并和本次增量证据。
- 同一份 [Google 进度文档](https://docs.google.com/document/d/1X7wuVkub_mHe93NTofh-VmB7a32_RWFJBY8E3ddDEgw) 已更新到第五版，快照截至 04:13:20 UTC；全文和父文件夹已重新读取核对。参见[第五版交付证明](evidence/project-z-google-doc-20261121/delivery-v5.json)与[结构回读证明](evidence/project-z-google-doc-20261121/readback-verification-v5.json)。原始 Drive MD／JSON 字节镜像仍为旧 `0d73`，不能写成已同步当前 GitHub 文件。
- zuse PR #4 已合入功能分支 `fe47f96`；PR #2 仍为草稿，zuse 主线及当前 SSMCP 的 zuse 依赖仍是 `a1bb8fd`。没有把功能分支通过误写为下游已适配。
- 04:13:02 UTC 的开发机读取显示，工作区可用约 390.25 GB，内存可用约 6.33 GiB；该观察只是当时资源状态。

本次新增证据保持小型独立文件，既有主报告及历史失败原件保留原身份。完整字节数、SHA-256、作业范围与未验证事项见结构化记录。
