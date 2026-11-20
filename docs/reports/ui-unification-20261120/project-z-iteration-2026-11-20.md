# Project Z 本轮迭代报告：主线验收、套件安装与项目页更新已完成

> **本轮稳定组合已完成交付验收。** 日期：2026-11-20；人类可读时间统一为 **Asia/Taipei（UTC+8）**。组件发行、开发机套件安装、聚合主线验收和项目页更新均有实际回执；线上文件复核于18:57:45通过。精确源码提交、文件摘要与证据归属见[脱敏JSON](project-z-iteration-2026-11-20.json)，其中机器时间保留UTC。后续新版本另按各自批次推进。

## 1. 主线已经合入并通过最终依赖验收

**本轮主线验收提交为 `78fc357f778a0dbff12f9320da82f324cb427410`，已通过GitHub独立读回。** 实际接受测试的源码提交为 `522bc7c9da008f05e9f715c1c1eda91b13ca89ec`；后续78fc357只更新三份文档，没有改变被测源码及依赖。提交编号唯一标识一份代码，以下结果均按这一关系归属；后续站点与报告文档合流产生的新编号不替代这个验收来源。[最终回执][final-validation]

| 最终验证 | 结果 | 耗时 |
|---|---|---:|
| 清单、版本和源码一致性检查 | 退出0；43个仓库、62个Cargo包通过 | 0.997秒 |
| 全部本地依赖解析 | 退出0；38个Rust仓库通过 | 8.639秒 |
| 工作树与固定提交 | 103个递归子模块加根仓库，共104个检出，前后均干净且匹配 | — |
| 文件与配置保全 | 内容、权限及存在性未变，差异清单为空 | — |

验证于18:46:55至18:47:04执行，覆盖233个Cargo.lock候选路径中的142个既有文件，以及209个仓库内配置候选路径中的3个既有文件；外部Cargo配置也保持不变。依赖解析证明所选源码能够组成一致的依赖图，运行能力仍以各组件的实际测试为依据。[最终回执][final-validation]

在此前b54f083已接入ztty 0.5.2、zmcl的zi18n消费改动和zguard 0.1.0的基础上，最后一批只把套件更新到0.2.6源码1e3ce8d及相应清单、文档。其它已接受来源保持不变：界面库仍为zgpui 0.1.2，zmcl提交2b1218f实际使用zi18n 0.1.0读取九个既有标题。这不代表后来zmcl 0.1.2及新界面库组合已整合。[先前组件回执][aggregate]

本轮还将旧zui实现统一到zgpui，并补上关联源码校验：zcalld内嵌的 `apps/zcall-gui` 必须与总仓库选定的GUI指向同一提交，`check`、`resolve`、`run`都会验证，避免外层程序带着旧界面通过总仓库检查。91项相关单元测试以退出码0通过，耗时37.139秒；回执记录了基线b84f610及实现文件摘要。另有真实负例证明旧GUI指针被拒绝，ab2/e6对齐的正例通过。[源码关联回执][source-links]

历史提交 `046bb4b0b73f82e0943c92d7c81facb9968b8520` 的独立JSON记录的是检查、36个Rust仓库的依赖解析和保全。91项测试属于上述关联源码验收，不绑定046，也不充当本次最终依赖解析的替代证据。[旧解析回执][old-validation]

## 2. 已完成发布与安装

| 组件 | 已确认结果 | 适用范围 |
|---|---|---|
| zi18n 0.1.0 | 正式发布，跨平台及实际注册表消费通过 | 已登记到聚合，并由zmcl提交2b1218f实际消费。[报告][zi18n] |
| ztty 0.5.2 | 正式六平台发布、Cargo/AUR发布及交互式Zsh安装通过 | 其它命令搜索路径可能仍使用系统包；现有会话未被强制重载。[报告][ztty] |
| SSMCP 0.10.20 | 正式发布；无参数启动后的真实工具命令退出0 | 最新三种命令环境均成功返回0.10.20；服务器部署未触发。[客户端报告][ssmcp20] · [最终入口验收][suite-install] |
| oh-my-ztty 0.2.6 | 正式发行、官方文件下载核验、实际安装及重复安装通过 | 三种命令环境均回报套件0.2.6，保护范围内文件不变。[正式记录][suite-report] |
| zguard 0.1.0、zharness 0.6.0 | 两库已正式发布，公开归档及来源已核实 | zguard已登记；zharness 0.6.0仍等待后续依赖整合。[集成报告][guard] |
| zmcl 0.1.2 | GitHub与AUR 0.1.2-1发布、开发机升级完成 | 19项已装文件无改动，4组已装GUI创建检查通过；聚合仍采用较早的相容界面组合。[最终报告][zmcl-final] |

ztty的Cargo入口从官方注册表在本机构建，套件入口从官方预编译归档提取；两者均为0.5.2，各自按其构建来源验收，不能混用二进制摘要。

发布表示已有可获取的固定制品；安装表示某个入口实际运行对应程序；聚合通过则要求整套源码与依赖相容。一个环节完成，不会自动证明其它环节也完成。SSMCP 0.10.20的安装只替换已验收的交互式入口，原进程继续使用其已加载的程序，不能据此宣布所有在线会话或服务器已升级。[安装报告][ssmcp20]

## 3. 套件0.2.6：发行与开发机安装均已完成

正式源码为 `1e3ce8d3e5a141d09e450fd3f635f987a5732be4`，附注标签对象为 `5a5f45dcc37c443876aee5d29ed280bcf6c6058d`。正式运行44719594477于18:31:12成功结束，双架构构建与发布共三项作业通过；Release452554850于18:31:09公开。[流程][suite-ci] · [发布页][suite-release]

两个架构都完整递归检出仓库并构建套件，验证真实终端窗口、键盘、补全和清理。套件中的ztty与SSMCP使用官方预编译制品；这些结果不表述为重新编译全部组件。

| 官方归档 | 字节数 | SHA-256 |
|---|---:|---|
| Linux x86_64 | 7,273,546 | `94a22ce1300a337e741ef0c2a336e29e90696b621fbdfa05c0b66673ce10dc20` |
| Linux aarch64 | 7,011,427 | `b035c460e3444e7b33dda4e5dd25bceecf0757af40b095950adb8d0ad001637b` |

本地已有90项测试、双架构套件、x86_64基本运行检查、0.2.5↔0.2.6真实升级回退及个人配置保留、493条站点链接的回执。本地Codex环境的AF_UNIX权限错误曾阻断本地GUI验收；正式CI中的原有GUI步骤通过，补充的是正式环境证据，不能把本地失败改成“本地全部通过”。[正式发行与安装证据包][suite-drive]

最新安装回执确认，6个文件从精确官方URL实际下载，用时9.836秒，API摘要及三份伴随校验文件全部匹配。实际安装1.173秒、重复安装0.624秒，均退出0；新版本126项与旧版本119项文件清单分别核对通过，受保护的个人配置、链接和Cargo安装指纹不变。真实登录式Zsh加载原有配置，用时0.376秒、退出0。[最终安装回执][suite-install]

| 实际命令环境 | 套件 | ztty | SSMCP |
|---|---|---|---|
| 登录式Zsh | 0.2.6 | 0.5.2 | 0.10.20 |
| 开发机命令环境快照回放 | 0.2.6 | 0.5.2 | 0.10.20 |
| 用户服务命令环境快照回放 | 0.2.6 | 0.5.0 | 0.10.20 |

用户服务环境的两个裸版本命令均成功退出；受追踪权限限制，最终委托文件及摘要未知，不能把此前路径查询失败推断为命令失败。独立系统包记录仍为 `oh-my-ztty-bin 0.2.5-1`，外部ztty链接仍指向系统0.5.0。此次升级未停止现有连接或服务，但没有另测全部进程的存活连续性。[最终安装回执][suite-install]

## 4. 后续版本的能力与依赖边界

**SSMCP 0.10.21尚未正式发行。** 唯一负责人已冻结新候选 `8c354a0e0ef8ad5d4586776e645953d0d35b7d8d`，正在执行完整验收。本次交接尚未收到全部门禁通过证据，正式Release查询仍未建立发行；该后续批次继续独立推进，不影响本轮稳定组合交付。

**zharness 0.6.0已经发布，但应用接入仍需单独验收。** 正式源码db4206d精确依赖zguard 0.1.0、zcall 0.4.0、zplugin 0.3.1；133项运行测试包含17项授权保护集成测试，另有15项文档测试。检查只作用于显式启用保护的调用入口；直接 `call_text` 不会自动受到保护，不能因依赖升级就宣布SSMCP现有路径已完成运行期接入。[集成报告][guard] · [云盘副本][guard-drive]

Project Z为每个已知包选择统一源码，精确版本约束和嵌套依赖都须与之相符，可选依赖也参与检查。SSMCP 0.10.20源码使用的部分精确版本与当前聚合不同，因此可作为独立已验客户端安装，却不能只凭版本更新就替换当前聚合源码。套件锁定的二进制与聚合锁定的源码，应分别记录来源。

界面库目前涉及zgpui 0.1.2、0.1.4、0.1.5三组精确约束；已发布的zcall-gui 0.1.2依赖0.1.4，使用0.1.5的下一批应用尚未收齐。zcalld 0.4.0与兼容扩展0.2.0由原zcalld负责人最终发布，原衔接负责人继续协作。扩展候选 `4d19a421b45010a1ac5e52d8bcc93a5c006e8f4b` 已提交PR #2且构建阶段完成，仍不是正式发行版本。[候选PR][compat]

SSMCP原生监听功能还需要支持 `listen` 的zcalld。当前聚合中的旧版本没有该命令；D722与SSMCP ed2开发组合已有绑定构建清单的94项通过证据，但不覆盖最终0.10.21或当前旧组合。zcall 0.4.0与zharness 0.6.0的后续整合，应同时收齐受影响应用的固定源码和实际运行证据。

生产服务的不中断要求保持。最后只读预检因活跃会话及缺少已验证的切换保护机制而拒绝升级；发布客户端和恢复开发机连接，都不能证明服务端无感升级完成。取得新的安全切换证据前，不重启现有会话。[预检说明][ssmcp20]

## 5. 中断恢复与证据保留

本轮曾遇到空间不足和执行连接中断，18:38:24恢复；空间恢复原因未证实。协调者核实原作业后顺序继续同一任务，最终正常完成，没有把失联当作后台已经停止，也没有用旧验收充当新通过。恢复过程未重启旧客户端或生产服务。机器交接保留必要的角色、阶段和回执关系，正文不公开进程或私有会话标识。

## 6. 项目页已更新，线上文件逐项匹配

站点修复 `17c3819cee0a0dc9bd057dd529d2a48437b749e2` 恢复了既有规则：同名crate的仓库归属不匹配时，保留已核实的源码项目，记录 `repository_mismatch`，不展示无关crate链接，不使全部刷新失败。8项测试与静态检查通过，原37项目、27个crate快照的构建摘要不变；新的39个公开仓库、29个crate数据随后通过验证。[修复][site]

**公开页已上线：<https://lightjunction.github.io/project-z-site/>。** 公开仓库提交为 `5bdd99dc749de86482f1bafb525693c2acc66b85`，只更新 `index.html` 与 `projects.json`。Pages运行44723433069于18:57:10成功；18:57:45的首页及六个静态文件共7次请求均返回HTTP 200，大小和SHA-256全部匹配121,945字节的构建。[发布流程][site-run] · [线上核验回执][site-publication]

公开仓库只保留白名单中的七个文件，含未改变的README，私有总目录没有发布。页面以39个已核公开仓库、29个已核crate展示各自发行状态；例如zgpui 0.1.5、zharness 0.6.0的公开版本可被展示，而本轮聚合仍使用已验相容的源码组合。公开版本目录不是自动升级整个依赖图的指令。[页面云盘记录][page-drive]

本轮引用的套件、ztty、SSMCP、zi18n及授权库证据均有固定GitHub来源和对应云盘资料。报告把实际测试、安装入口、发布制品与线上文件分别记录；未将候选版本、单项测试或文件替换扩写为全部运行状态的保证。

## 7. 后续批次与负责人职责

| 下一批范围 | 现有负责人应交付的结果 |
|---|---|
| SSMCP 0.10.21 | 唯一整合负责人完成冻结候选的完整跨平台门禁与正式发行，保留历史失败回执 |
| zgpui 0.1.5及应用 | 界面库与zmcl负责人协调ztty、ztype、GUI维护者，收齐精确依赖、嵌套源码及实际窗口验收 |
| zcalld 0.4.0／兼容扩展0.2.0 | 原zcalld发布负责人与衔接负责人完成PR #2配对、正式发行和真实协议验收 |
| zcall 0.4.0／zharness 0.6.0消费 | 共享库与应用维护者更新受影响的精确依赖链，实际接入授权保护入口，避免只改版本即宣称运行功能完成 |
| 后续聚合 | 协调者收齐同批固定来源后独立检查、解析与保全；保留本轮稳定组合，不追逐未经验收的各仓库主线 |

后续验收继续遵守三个边界：测试绑定具体源码；不同构建产物保留各自来源；生产升级必须证明不会中断活跃用户。当前稳定组合无需等待这些新批次即可使用。

[aggregate]: https://github.com/LIghtJUNction/project-z/blob/b54f083e2b7900c2f5c93ec93e26366526645095/docs/reports/ui-unification-20261120/accepted-component-pins.md
[old-validation]: https://github.com/LIghtJUNction/project-z/blob/b54f083e2b7900c2f5c93ec93e26366526645095/docs/reports/ui-unification-20261120/independent-validation-046bb4b.json
[zi18n]: https://github.com/LIghtJUNction/zi18n/blob/cdff8dea19e97268d296afa827767ea689420591/docs/releases/0.1.0.md
[ztty]: https://github.com/LIghtJUNction/ztty/blob/76fa2cfd13b776c027d5a86fadafde8e035f88f2/docs/releases/0.5.2/report.zh-CN.md
[ssmcp20]: https://github.com/LIghtJUNction/ssmcp/blob/f8a40bb741fc5921c9ae5a1d447eac7dba2fd251/docs/reports/client-install-0.10.20-20261120/README.md
[suite-ci]: https://github.com/LIghtJUNction/oh-my-ztty/actions/runs/44719594477
[suite-release]: https://github.com/LIghtJUNction/oh-my-ztty/releases/tag/v0.2.6
[guard]: https://github.com/LIghtJUNction/zguard/blob/6772b932a65e18f64e13591dee6edb2f6b099406/docs/INTEGRATION-2026-11-20.md
[zmcl]: https://github.com/LIghtJUNction/zmcl/releases/tag/v0.1.2
[site]: https://github.com/LIghtJUNction/project-z/commit/17c3819cee0a0dc9bd057dd529d2a48437b749e2
[suite-drive]: https://drive.google.com/file/d/15c79p02J6VqnXF2qnSYacMJOj7hp4-6E/view
[guard-drive]: https://drive.google.com/file/d/1hFQ6Xwzz9UXpuHY0WTYCOI9a-J8ZSfhp/view
[ssmcp-drive]: https://drive.google.com/file/d/1hoScdqhU49-odsmwvWuBFJ1nmrIKCgLL/view
[zi18n-drive]: https://drive.google.com/file/d/17JnwPZtiGOS4IxP9MJOwU14oIiHWK4cT/view
[ztty-drive]: https://drive.google.com/file/d/1f8AvfqWjI3OLNdVXdn2v7lC8JZs6hVmI/view
[compat]: https://github.com/LIghtJUNction/zcalld-compat/pull/2
[final-validation]: https://github.com/LIghtJUNction/project-z/blob/78fc357f778a0dbff12f9320da82f324cb427410/docs/reports/ui-unification-20261120/final-validation.json
[source-links]: https://github.com/LIghtJUNction/project-z/blob/78fc357f778a0dbff12f9320da82f324cb427410/docs/reports/ui-unification-20261120/source-links-validation.json
[suite-report]: https://github.com/LIghtJUNction/oh-my-ztty/blob/0b60eb7d6e35d06a137278ffe0b3f1139c722fe6/docs/reports/0.2.6/release.zh-CN.md
[suite-install]: https://github.com/LIghtJUNction/oh-my-ztty/blob/0b60eb7d6e35d06a137278ffe0b3f1139c722fe6/docs/reports/0.2.6/actual-install.json
[site-run]: https://github.com/LIghtJUNction/project-z-site/actions/runs/44723433069
[site-publication]: https://github.com/LIghtJUNction/project-z/blob/3ca312cad4e8866caccb034e52a47596ce3441bd/site/evidence/publication-20261120.json
[page-drive]: https://drive.google.com/file/d/1zXlCIfplSFiBxLHOpqNy31Fbn2e2HgDX/view
[zmcl-final]: https://github.com/LIghtJUNction/zmcl/blob/2287ca81de9ec5ba200ba0d1792dcda7d2742488/docs/reports/2026-11-20-gui-iteration.md

