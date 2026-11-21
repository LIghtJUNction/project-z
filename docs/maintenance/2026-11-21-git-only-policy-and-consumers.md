# Git-only 规则与消费者进展

**截至 2026-11-21 07:30:11 UTC（台北时间 15:30:11）。** Project Z 的 Git-only 开发规则已发布到维护分支；zuse 0.3.0 已进入主线。ztype 和 SSMCP 的新依赖组合仍需各自验收，最终 44 仓库检查继续暂停。本记录独立追加，保留此前的失败、验证身份和历史报告。[来源快照](evidence/git-only-policy-and-consumers-20261121/github-reference-observation.json)

## 本轮结果

| 范围 | 实际结果 | 验证边界 |
| --- | --- | --- |
| Project Z | [892b9d1](https://github.com/LIghtJUNction/project-z/commit/892b9d1eecbc8a7ac2bee724749e9bf8f07322c0) 已发布；6 文件，另外 447 个叶节点不变 | 24 个 Python 测试方法通过；没有运行消费者或最终 44 仓库检查 |
| zuse | [PR #2](https://github.com/LIghtJUNction/zuse/pull/2) 已合并；当前 main 为 [830fcef](https://github.com/LIghtJUNction/zuse/commit/830fcefd2277cbba46536c67d206f29058ba7fb3)，包版本 0.3.0 | 已完整复核的三平台 CI 对应 67e 的 af46 树；830 的 10 个检查仅核状态成功 |
| ztype | [PR #4](https://github.com/LIghtJUNction/ztype/pull/4) 为 draft，头部 bd26b5b；只改 Cargo.toml、Cargo.lock | 已核 TOML 和源码树；锁补丁由源码推导，尚未经过 Cargo 解析、产品或 UI 验收 |
| SSMCP | [PR #164](https://github.com/LIghtJUNction/ssmcp/pull/164) 已合并；C2 与 P2 的树相同。后继工作分支为 [9e1a06c](https://github.com/LIghtJUNction/ssmcp/commit/9e1a06c4c6a04fe6a7ac7919c9cee9ab497ac95b) | 后继仅记录源码进度；截至快照没有新的 Gate35、runtime、UI 或 P1 通过结果 |

### 开发规则已经改变

跨 Project Z 仓库的 Cargo 开发依赖使用规范 GitHub 默认分支 URL，移除显式 `version`，包括 `"*"`；同仓库路径、外部依赖和包自身版本保持各自语义。同步时更新并记录 Git 提交与锁文件，使一次构建仍有确定输入。对外发布另行生成 registry 版本映射。既有 88fa 发布投影对兼容历史 `version + git` 的校验未被删除。[发布读回](evidence/git-only-policy-and-consumers-20261121/policy/publication-readback.json) · [独立代码审阅](evidence/git-only-policy-and-consumers-20261121/policy/project-z-git-only-independent-review.md)

原 RED 在旧生产实现上运行 5 个方法：3 个父方法失败，包含 38 个子测试失败。原 GREEN 运行 24 个方法：15 个策略方法、4 个声明提取方法、5 个未改的发布投影方法，失败、错误、跳过均为 0。两轮使用同一测试文件；这里没有把子测试数当成独立缺陷数，也没有重跑门禁。本轮未执行真实 Cargo 集成、离线 metadata、完整测试集或消费者验收。[RED](evidence/git-only-policy-and-consumers-20261121/policy/red.json) · [GREEN](evidence/git-only-policy-and-consumers-20261121/policy/green.json)

### 新依赖需要验证新组合

zuse 的 fe47、67e 和实际 CI checkout cf9 整树均为 af46。已封存的完整日志分别记录 Ubuntu 289 通过／5 忽略、macOS 267／3、Windows 263／2；三者均无失败，数量不跨平台相加。830 在此之后修改了版本、锁、发布流程及文档共 5 个路径，Rust 源码未变，但依赖图发生变化，因此不直接继承旧 CI 的产品结论。[修订后的准入复核](evidence/git-only-policy-and-consumers-20261121/zuse/zuse-pr2-admission-readonly-review.md)

ztype 候选删除 7 个内部 Git 依赖的版本选择条件，并把锁中的 zuse 更新至 830／0.3.0、zcall 更新至 317。其余锁项保持，20 个 Rust 文件和 2 个 gitlink 未改。各消费者应逐个评估兼容性，只修改实际不兼容的入口，再验收新组合；不能预设所有调用入口都必须重写。[静态准备](evidence/git-only-policy-and-consumers-20261121/ztype/readback-proof-public.json) · [PR 发布读回](evidence/git-only-policy-and-consumers-20261121/ztype/publication-readback.json)

SSMCP 的已合并 C2/P2 包含可协商的每会话 OpenAI 元数据、相关斜杠命令和保存的 ChatGPT URL 操作。后继 9e1 工作范围还包括账户夹具退出屏障、本地初始化错误、WebAction 回退、线程元数据隔离以及 Git-only 依赖更新。源码发布不代表这些后继行为已经通过运行验收。[限定状态记录](evidence/git-only-policy-and-consumers-20261121/coordination-status-observation.json)

## 已完成的有限验证

**当前安装入口的单次 socket 测试通过。** 入口实际报告 `ssmcp 0.10.25`，15,751,344 字节，SHA-256 前后均为 `54651b3fd9611210a838ffa5ddc1e032dc40d7b71ea2cf163487e4b32085c7b9`。一次启动、一次发送、一次 Python 夹具调用保留完整输入；缺失文件和 skill 各产生 warning，返回 completed JSON 与 EOF。客户端和外层进程退出 0 并被回收，私有 endpoint 已消失。未使用模型或宿主默认 socket，也未安装、重载或部署。这只验证该安装入口的隔离调用，不证明已消失的历史会话成功，也不替代后继源码的 UI/P1。[实际执行](evidence/git-only-policy-and-consumers-20261121/current-entry-smoke/root-actual-execution.json) · [结果](evidence/git-only-policy-and-consumers-20261121/current-entry-smoke/report.json)

**W 账户诊断的一次运行未复现原失败。** 旧服务 36 项、W 服务 33 项，共 69 项通过。空列表及严格 404 谓词保持；原始数值 404 未另行记录。审阅核对了脚本差异、实际 job 和固定文本输入，没有重新读取 ELF。这不建立原失败根因，也不改写 W 的 UI 失败或旧 503 项历史记录。[独立复核](evidence/git-only-policy-and-consumers-20261121/account-diagnostic/account-diagnostic-independent-readback.json)

**Linux 多用户问题仍缺实际入口身份。** 只读材料支持原工作目录的本地权限限制，以及一个与包数据库摘要一致的旧系统 ELF；尚未证明已退出的 x shell 实际选中了它。没有切换用户、放宽权限、安装软件或运行产品来补认这个结论。[事实与边界](evidence/git-only-policy-and-consumers-20261121/linux-multiuser/facts-and-boundaries.json)

## 待完成与保留范围

- 新需求已纳入：`--version --all` 显示依赖版本树；逐入口检查 Ctrl-Super-C 关闭接管后直接 zuse CLI 的绕过报告；统一 Computer Use On/Off 语义。这些是待实现、待验证事项。
- 原始 85 项队列仍为 **56 合并、14 关闭、9 归档、5 阻塞、1 待集成**。最后一项仍是 [zcalld PR #1](https://github.com/LIghtJUNction/zcalld/pull/1)，当前 draft，头部 bd7。后续新 PR 不加入这 85 项。
- 原有原生验证窗口未归还，最终 44 仓库图尚未启动；本次整理没有执行 Cargo、产品、CI 或获取共享 target 锁。[状态及来源](evidence/git-only-policy-and-consumers-20261121/coordination-status-observation.json)

07:24:03 UTC 的只读观察为内存可用约 **5.29 GiB**、工作盘可用约 **362 GiB**、共享 target 所在盘可用约 **687 GiB**。这些是当时读数，不表示全机空闲或锁已释放。

[c9de 历史报告](https://github.com/LIghtJUNction/project-z/commit/c9de7a60351b277a4903c9f40781cbae69cd6e5c) 与 [Google Doc v8](https://docs.google.com/document/d/1X7wuVkub_mHe93NTofh-VmB7a32_RWFJBY8E3ddDEgw) 继续保留 **06:23:03 UTC** 的截止时间；本批不改写它们。[Doc 交付边界](evidence/git-only-policy-and-consumers-20261121/doc8/delivery-v8.json) · [本批结构化记录](2026-11-21-git-only-policy-and-consumers.json)

公开证据只包含必要文本。含私有路由或会话标识的少数收据发布明确标注的脱敏副本，并记录原件摘要和删改字段；原件保留。未读取或公开含隔离 OAuth 值的 raw client.stderr。
