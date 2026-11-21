# Project Z：报告后的依赖与源码进展

知识截点：2026-11-21T09:28:35.881Z。本记录接续 [14cd62c8 的四仓报告](https://github.com/LIghtJUNction/project-z/blob/14cd62c8a69eca18877d252a2f4f423f48ca8bea/docs/maintenance/2026-11-21-git-only-release-staging.md)，保留其 09:03:55.489 UTC 固定截点和全部原件。

## 两个新增草稿

| 仓库 | 已发布源码 | 本次修改 | 核对范围 |
| --- | --- | --- | --- |
| zdot | [PR2](https://github.com/LIghtJUNction/zdot/pull/2)，f78bd895 | 仅删除 `dependencies.zclap.version`。 | 27 个叶对象中其余 26 个不变；Git URL、default-features=false、Cargo.lock 和包版本保持。 |
| TokenNotIncluded/lmm | [PR5](https://github.com/TokenNotIncluded/lmm/pull/5)，98d667a2 | 仅删除 `dependencies.zhex.version`。 | 65 个叶对象中其余 64 个不变；Git URL、外部依赖、Cargo.lock 和包版本保持。 |

两仓均为 open、draft、unmerged；默认 main 分别保持 a3c6a75b 与 7ba45df9。准备阶段用 Python 标准库解析 TOML 并逐项比较；root 又从 GitHub 读回提交、父提交、完整树、分支、PR 和 Cargo.toml 全文，确认只有上述单字段变化。本次没有刷新锁中的 Git 提交，也没有执行 Cargo、metadata、产品测试、CI、registry 或发行命令；仍需各自实际消费与发行门禁。原始 85 项分类保持，本次新增草稿另列。[zdot 回执](evidence/git-only-followup-20261121/zdot-publication-readback.json) · [lmm 回执](evidence/git-only-followup-20261121/lmm-publication-readback.json)

## SSMCP 后继源码

[PR166](https://github.com/LIghtJUNction/ssmcp/pull/166) 于 09:13:10 UTC 合并；root 核实 main 为 [f69db30c](https://github.com/LIghtJUNction/ssmcp/commit/f69db30c3a9e461c48731c81dbde5a35ea176dc2)，tree 为 98f89ac6。合入的 814c07c 将测试故障注入改为已 flush 的非法 JSON，并澄清两处发行说明；原十秒边界及结果不确定、禁止重放和清理等断言保持。

验收准备随后发现 zuse main 已从 830 前进到 [ac5713c2](https://github.com/LIghtJUNction/zuse/commit/ac5713c2bfc3cc4848e89107cc1a6929ec48e2dc)，新增本地程序与有界观察等功能。原负责人报告十一仓准备检查只有 zuse 与锁定来源不一致，并继续核对依赖；最新消息仍是 Gate16 未绑定、未运行。尚未取得当前 zuse 作者的冻结确认，不能用在线客户端或空协作名单代替确认。旧源码的 Gate、runtime、UI 与平台成绩均不转挂到新来源。[源码观测与边界](evidence/git-only-followup-20261121/ssmcp-source-observation.json)

## 开发机与下一步

09:27:54 UTC 直接读取开发机：可用内存约 4.23 GiB，工作盘可用约 360.44 GiB，共享 target 所在盘可用约 681.89 GiB。本次没有清理用户文件或搬移数据。资源读数是瞬时观测，不表示所有任务空闲或共享锁已经释放。[原始资源记录](evidence/git-only-followup-20261121/dev-machine-health.json)

编译与产品验收窗口继续由原 SSMCP 负责人持有。本组保持无 Cargo、build、metadata、产品执行、target 写入或排队；ztype v2 仍未启动。接下来先固定 SSMCP 的实际依赖输入，再运行其 Gate、runtime、UI／P1；四仓发行脚本与新增消费者草稿各自完成实际门禁后，才进入最终 44 仓组合验收。

14cd 的 13 个文本文件已完整回读，原 489 个叶对象全部保留，提交后共 502 个。[固定报告发布回执](evidence/git-only-followup-20261121/fixed-report-publication.json)。Google 文档沿用原文档 ID；后续阅读副本与截点后补记另行验证。
