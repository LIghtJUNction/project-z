# 用底层 z 库替换上层重复实现

日期：2026-11-23。本计划把 Project Z 的协同维护落到依赖替换：通用底层能力由一个 z 库维护，上层项目调用它并删除相同实现。每批都交付可复用的底层提交、消费者适配、删除范围、真实锁文件及行为证据。

## 首轮调查时已经具备的基础

- 子模块归属保护补丁在隔离源码中完成：空目录或缺失目录仍检查保留的 Git 元数据是否属于另一份 checkout。原始协调基线为 `573a7070dbeb0101920fbe1bf137e7dcca80619d`，补丁提交为 `680773d664be3effc6b5d4ba69ea060a371e628e`，原始相关 Python/Git fixture 39 项通过。集成时使用当前公开主线，保留原始验证身份；详见 [归属检查报告](2026-11-23-submodule-ownership.md)。
- zrun 的独立 P0 已有单线程 spawn/block_on/join/yield/timer、取消与关闭实现；设计提交 `b33e0d087102fdf8c33adc12fc2e49fe36a53dfb`，实现提交 `12e6421ddfc898658ab59f97e922979e85d8b597`。43 项常规测试、显式百万任务测试、35 项核心 Miri 检查、400 个独立比较样本通过正确性检查。120 秒短测完成 2,995 万个任务并结束于 active=0。性能普通/挑战门槛尚未达到；Loom、多线程、I/O 和 24 小时稳定性仍未完成。zrun 本轮未部署、未公开发布。
- [zaccel v0.1.1](https://github.com/LIghtJUNction/zaccel/releases/tag/v0.1.1) 已完成 [正式五平台构建](https://github.com/LIghtJUNction/zaccel/actions/runs/45182003421)，提交 `04be97d271c7d0db50b2856bec5cbf225e031f7a`。GPU 功能和计时分别记录；公开发布不代表所有消费者已经接入。它和未公开的 zrun 尚未被写成一个已经全图验收的新聚合快照。

本文件使用公开聚合提交 `5b6ed98b630197fa7ef0f2bf7851d5c31aec9650` 的 catalog 作覆盖清单：46 个仓库、73 个包。代码级接入调查另读取了 zharness `8907262ce6c8494f2849f8e5abd84f7a3da2e405`（0.6.0）和 ssmcp `7bb087582e74e7b75cdb2e6997d61d826d5cebd8`（0.10.28）。这些身份各自记录，不能把静态 catalog 当作本次最新全图 `check` 的结果。

## 替换次序

| 批次 | 底层库 → 消费者 | 要集中维护的能力 | 完成所需证据 |
| --- | --- | --- | --- |
| A：有明确等价边界的纯算法 | z64/zhex/z58 → 编码调用方 | 严格编解码、输出容量、错误位置；优先核对 ssmcp 的标准 Base64 和 URL-safe 无填充调用点 | 空输入、边界长度、错误 padding、非规范尾位、超长输入和现有调用方错误处理；比较热点吞吐/分配，确认剩余外部依赖来自哪里 |
| B：公共任务执行与收尾 | zrun → zharness 的 std 应用适配、ssmcp 的通用收尾层 | 有界任务/结果/定时、后续阻塞池和任务组 | API 能力补齐后删除消费者通用实现；取消、panic、关闭与未启动工作归属必须实测；P0 性能问题有记录且得到处理 |
| C：系统与终端 | zsys/zpty/zvte/zterm → ztty、ssmcp、zuse 等实际消费者 | 已明确的系统调用封装、PTY 和终端解析状态 | 各平台生命周期、进程树、窗口尺寸、终端字节序列、Unicode 和设备行为；不能只凭编译通过替换 |
| D：接口与应用 | zclap/zcall/zmcpio/zplugin/zharness → 应用、运行时服务及安装器 | 参数约束、协议、插件 ABI、工具循环与公共策略 | 保留 feature/no_std/ABI 边界；枚举直接和间接消费者，按依赖次序一起更新并验收 |

上表是排期和核对方向，不声称任何同名库都是其他 crate 的直接替换。已有记录中 zuse 使用 z64，zharness 使用 zguard，ztty 使用 zpty 并通过 zterm 使用 zvte；后续沿同一复用方式推进。[记录清单](2026-11-23-dependency-inventory.json)

## zrun 如何进入 zharness 与 ssmcp

zharness 的 `TaskBoard` 管理的是任务依赖、能力匹配和租约。其核心是 no_std、调用方提供缓冲区和时钟的同步状态机，目前没有内部异步执行器。接入 zrun 的合适位置是可选的 std 运行适配层：应用提交有界工作、等待结果、取消与计时；基础状态机继续保留原有无分配和调用方控制的语义。租约到期不能自动重放已经产生外部副作用的操作。[源码](https://github.com/LIghtJUNction/zharness/tree/8907262ce6c8494f2849f8e5abd84f7a3da2e405)

首轮基线中的 ssmcp `src/backend/opencode/cleanup.rs` 曾是可复用能力的具体候选：`Finalizers`、`Finalizer`、`DeferredWork`、`Shutdown` 管理异步与普通线程两类完成句柄，保证排队归档工作在运行时关闭时仍有归属，并在流完成后关闭事件日志。zrun 需要先提供有界阻塞池、明确的完成句柄及 drain 契约；然后消费者留下归档业务顺序，删除通用队列和等待实现。现有 `queued_archive_survives_runtime_shutdown_exactly_once` 行为必须保留。[源码](https://github.com/LIghtJUNction/ssmcp/blob/7bb087582e74e7b75cdb2e6997d61d826d5cebd8/src/backend/opencode/cleanup.rs)

2026-11-24 复核时，公开主线 `b5fdceea9af1b14f6f178bbc1677969fd3ff73c9` 已删除嵌入式 OpenCode 等后端，上述路径和测试随之退役。后续应从当前 `src/worker/executor.rs` 的阻塞历史写入重新建立接入基线，保留捕获的提交 owner、先记录请求再派发、持久化结果以及派发后 unknown 不自动重放的语义。该候选仍需要有界 blocking 模块与新的行为验收；旧后端的测试记录只作为历史设计依据。[当前 worker 执行边界](https://github.com/LIghtJUNction/ssmcp/blob/b5fdceea9af1b14f6f178bbc1677969fd3ff73c9/src/worker/executor.rs)

ssmcp 的主服务还使用 Tokio 网络、TLS/WebSocket、进程、信号、文件与同步设施。P0 zrun 没有 I/O reactor 或阻塞池，不能承担这些职责。后续适配可以按边界逐段交接，但需要有界消息和明确的运行域，不能直接在 zrun 中 poll 依赖 Tokio reactor 的 Future。`session/service.rs` 的进程组、guardian/Windows Job、认证和 epoch 判断属于业务资源归属，仍由 ssmcp 保管。[服务代码](https://github.com/LIghtJUNction/ssmcp/blob/7bb087582e74e7b75cdb2e6997d61d826d5cebd8/src/session/service.rs)

zaccel 的 `wait_future` 也有通用 Future 驱动和等待，但同时必须调用 `wgpu::Device::poll` 并检测设备错误；它需要外部事件驱动接口和截止时间，不能只换一个 block_on 调用。CLI 的进程看门狗继续处理原生驱动调用可能阻塞的问题。[GPU 等待代码](https://github.com/LIghtJUNction/zaccel/blob/04be97d271c7d0db50b2856bec5cbf225e031f7a/src/gpu.rs)

zrun 的具体接入设计、拟议 blocking API 和验收报告位于本轮 P0 源码交付中的 `docs/adoption.md`、`docs/design.md`、`docs/measurements/p0-linux-20261123.md`。首轮交付时尚未公开，因此当时没有向消费者加入不可解析的 Git 依赖。公开仓库随后在同一 P0 基线上增加了预览提交 `beeea183b7dcbff7fe34ea0add9039d6058c2edb`；本轮通知优化候选仍未整合到该公开主线，也没有加入消费者生产依赖。后续保持默认分支来源规则，不以本地 path/registry patch 代替最终标准解析。

## 2026-11-24 续进展（UTC+8）

总仓最新已记录快照为 `2e32aac`，其 49 个仓库、82 个包、43 个 Rust 仓库 locked 解析及 150 项协调测试的范围见[发行快照记录](2026-11-23-release-cohort.md)。下述增量候选尚不在该快照中，不能把既有全图记录当作这些新提交的验收。

### ssmcp 的剩余 hex 调用

公开 `b799d0c` 已将 `src/hex.rs` 接入 zhex，并随 `b5fdcee` 保留在当前上游。续作基于该上游提交，继续迁移 55 处生产或测试夹具的字节转小写 hex 调用；这包括身份随机值、摘要与有限前缀的编码。随机源、哈希输入、截断长度、命名空间和上层校验规则由原调用者继续负责。提供者是锁文件中实际的 zhex `52515207f9d97a2580182169b611b4763366b328`，开发声明仍为默认分支 Git URL。

首轮候选有 58 处：其中两处随上游旧后端删除，一处 release checksum 测试保留独立的格式化预期。hex 边界检查同样使用独立参考，覆盖所有字节值、非对齐切片和 21 个长度；没有把生产 codec 用来计算这些测试的预期值。未使用的 `qrcodegen` 从真实依赖及根、桌面两份锁文件中移除；Base64 仍有实际传递消费者，本轮未增加另一份实现。

已推送的源码为 `d51f6b44e2a30f12a217d7378af17b934a3bcd10`，含两项取消测试修复：等待整个任务清理完成再检查 socket；让超时与取消分别使用独立请求夹具，并给就绪等待设置上限。它保留了上游的原生后端调整、lint 修复和历史归属契约。相对 `b5fdcee`，这批源码、测试和锁文件共新增 97 行、删除 186 行；Rust 部分净减少 74 行，提供者新增代码为零。行数只用于说明维护范围，未据此宣称性能改善。

该精确提交的严格 Clippy、格式检查、四项已有 codec 测试与桌面工作区完整 locked metadata 已通过；两项取消测试按源码等值复用既有通过记录。完整服务测试编译收到 SIGKILL，四次原生 Cargo 批次因共享锁占用而没有启动；完整服务测试仍未验收。详见 [消费者验证报告](https://github.com/LIghtJUNction/ssmcp/blob/c6c95dafcfeda7eb9bacbeace1658c0b4c317d62/docs/reports/zhex-adoption-20261124/README.md)。随后主线上游已独立合入其他代码至 `b2f7858`，这些新增变更不在本批精确源码检查的覆盖范围。本续进展不推进新的聚合 gitlink。

### zrun 通知优化候选

实现候选 `156188c1a22fa70d50ab89e937ee69425223619d` 让执行器先声明准备休眠，再检查任务与定时器；只有命中该休眠状态的通知才进入线程唤醒路径。任务布局、队列、每轮 64 次任务预算和工作负载保持相同。AcqRel 原子交换保留通知与状态发布顺序，三个 Loom 模型覆盖实际通知握手；43 项常规测试和 14 项执行器 Miri 检查通过。

10 轮、4 个任务规模、5 个场景、2 个修订组成的 400 个独立进程样本全部通过正确性核对，顺序交替，保留全部样本。与原 P0 基线相比，1 千、1 万、100 万任务的自唤醒吞吐中位数分别提高约 14.9%、13.8%、10.9%，各自配对 95% 区间完整高于 1；10 万任务的区间跨过 1，结论仍不确定。spawn 与每任务内存没有明确改善。此次比较的两端都是 zrun，首次相对 Tokio 未达标的结论没有被改写。

完整文档候选为 `0240c304c1ef8428da0268b89cb66f083333604d`，源码和原始证据保留在本轮交付包，开发机隔离源码工作树干净、没有配置远端。这一候选没有推送、发布或部署；已存在的公开 P0 预览与它分别记录。局部 Loom 不覆盖未来多 worker 的全部状态机，24 小时稳定性、I/O/TCP 和跨平台门槛仍待实际完成。

## 每批可审核的交付

1. 固定消费者与底层库的当前源码身份，列出被替换代码、行为契约和反例。
2. 底层先补最小缺失能力，并验证容量、所有权、错误与取消边界。
3. 更新真实调用点并删除重复实现。同时报告“底层新增行、各消费者删除行、净变更、重复实现份数、依赖树变化”，不只报告新依赖数量。
4. 同一工作负载比较变更前后结果、延迟、吞吐、内存与关闭行为。保留失败样本和未覆盖平台。
5. 按依赖次序提交/推送底层与消费者，更新 Cargo.lock 和必要的嵌套 gitlink；跨仓声明使用 GitHub 默认分支 URL，不加 version/rev/tag/branch。
6. 最后执行全图 `check`、`resolve --all` 及实际消费者门禁。未完成前不推进聚合 gitlink，不把一份计划或库发布写为传播完成。

共享开发机上的 Cargo 仍使用统一 target 和一个外层锁；本轮不干预其他会话持有的锁或正在进行的编译。能够在沙箱复现的下载、CPU 测试和统计分析留在沙箱，开发机主要承担必要的设备验收。

## 首轮 catalog 中已登记仓库的传播范围

下表由上述固定 catalog 的跨仓 Cargo 引用与 `requires` 关系计算。包含 normal/build/dev 引用；间接数去掉自身。运行时/安装关系可能形成互相依赖的组件组，需要成组验收，不能把这张图误读为纯 Cargo DAG。表中的零只说明当前记录未发现消费者，不证明没有外部用户。计划开始时仍要运行现有 `impact` 并补齐实际漏记关系。

| 仓库 | 角色 | 记录的内部依赖 | 直接消费者数 | 全部消费者数 |
| --- | --- | --- | ---: | ---: |
| OniMods | application | zhex | 0 | 0 |
| lmm | application | zhex | 0 | 0 |
| lmm-api-source | application | zclap, zconv, zhex | 0 | 0 |
| mechrevo-drivers | application | zclap, zhex | 0 | 0 |
| oh-my-ztty | suite | ssmcp, zdot, zfetch, zmem, zrc, zshard, ztty | 0 | 0 |
| ssmcp | application | zharness, zplugin, ztuio, zuse | 2 | 2 |
| z58 | library | — | 0 | 0 |
| z64 | library | — | 1 | 6 |
| zcall | library | zconv | 3 | 12 |
| zcall-gui | application | zcalld, zgpui | 1 | 3 |
| zcall-omarchy | application | zcalld, zcalld-compat | 1 | 3 |
| zcalld | application | zcall, zcall-gui, zcall-omarchy, zcalld-compat, zconv, zplugin, zsys | 3 | 3 |
| zcalld-compat | extension | zcalld | 2 | 3 |
| zclap | library | — | 6 | 11 |
| zclick | bindings | zclap | 0 | 0 |
| zconv | library | — | 5 | 15 |
| zdistro | application | — | 0 | 0 |
| zdot | application | zclap | 2 | 2 |
| zdwire | library | — | 0 | 0 |
| zfetch | application | — | 1 | 1 |
| zgpui | library | — | 5 | 9 |
| zgraphics | library | — | 2 | 3 |
| zguard | library | — | 1 | 4 |
| zharness | library | zcall, zguard, zplugin | 1 | 3 |
| zhex | library | — | 4 | 4 |
| zi18n | library | — | 1 | 1 |
| zinput | library | zplugin, zsys | 3 | 4 |
| zldap | library | — | 0 | 0 |
| zmcl | application | zclap, zconv, zgpui, zi18n | 0 | 0 |
| zmcpio | library | zcall | 1 | 6 |
| zmem | application | — | 1 | 1 |
| zmime | library | — | 0 | 0 |
| zplugin | library | zsys | 6 | 12 |
| zpty | library | — | 1 | 2 |
| zrc | configuration | ssmcp, zconv, zdot | 1 | 1 |
| zscan | library | — | 0 | 0 |
| zshard | shell | — | 1 | 1 |
| zsyn | library | — | 0 | 0 |
| zsys | library | — | 4 | 15 |
| zterm | library | zgpui, zgraphics, zinput, zvte | 1 | 2 |
| ztty | application | zgpui, zgraphics, zinput, zplugin, zpty, zterm | 1 | 1 |
| ztuio | library | — | 1 | 3 |
| ztype | application | zgpui, zinput, zplugin, zuse | 0 | 0 |
| zuse | application | z64, zclap, zmcpio, zsys | 3 | 5 |
| zuse-std | extension | zuse | 0 | 0 |
| zvte | library | — | 1 | 3 |

完整消费者名称和计算口径保存在 [JSON 清单](2026-11-23-dependency-inventory.json)。上表保留首轮固定快照；最新快照与本次增量分别见前文。catalog、聚合 gitlink 和子仓工作区的未验证变动不随此文档自动接收。
