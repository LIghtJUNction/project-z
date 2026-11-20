# Native input dependency cohort — 2026-11-20

**状态：受一个外部源码指针阻塞的候选快照，尚未接受或合入 main。** 本记录覆盖依赖与源码传播；输入服务安装和原生应用验收由对应产品记录给出。

## 固定范围

基于已接受的 Project Z `76dd114c11685d430dd55bb0d78b064a7349af73`，固定 zinput `f5d15e07d7ed233539e1cad87cfc0edb787bf34e`、zgpui `b09f3ded0928df5a35bad32dcd5539560b8617e6` 与 ztype `45a8c3ee30341fb95582838735aeb9dc9f2e2e60`。本候选保留这组不可变输入，供复查本轮工作；各仓库后来推进的 main 应另行选择和验收。

新增登记 zinput-wayland、zinput-x11、zgpui-raster，清单为 **43 个仓库、65 个 Cargo 包**。raster 的 Cargo package 仍为 `publish = false`；清单登记不表示已发布到注册表。

反向范围由实际 Cargo 图和运行依赖展开：zinput 影响 zterm、ztty、ztype、oh-my-ztty；zgpui 另影响 zcall-gui、zmcl，并经源码分发和运行关系影响 zcalld、zcalld-compat、zcall-omarchy。

zinput 的根 src、package、features、dependencies 与原 0.1.3 相同。zgpui 的根 Rust src 和上述配置与 0.1.5 基线 4aba3ba 相同；原生字体实现抽到共享 C 头文件，具体 native 文件存在变化。框架自身的测试证据由各源提交保留。

## 已发布的依赖传播提交

以下五仓均位于 `coord/ztype-native-services-20261120`，只更新依赖、锁文件或嵌套源码；GitHub 插件已独立回读。

| 仓库 | 提交 | 变更 |
| --- | --- | --- |
| zterm | [0c520c3](https://github.com/LIghtJUNction/zterm/commit/0c520c3da70b8ce83259aa0d8420589a79d7e03e) | Cargo.lock 选择 zgpui 0.1.5 |
| zcall-gui | [b1208c6](https://github.com/LIghtJUNction/zcall-gui/commit/b1208c695b6c3d17687f055f4ec52651fd7d3984) | 精确版本、vendor、锁文件一致 |
| ztty | [17238be](https://github.com/LIghtJUNction/ztty/commit/17238bed6484317e014b57389d4c72464f910b5f) | 精确 UI 版本、zgpui/zinput/zterm gitlinks 与锁文件 |
| zcalld | [25fb5c6](https://github.com/LIghtJUNction/zcalld/commit/25fb5c64a34f17bc2378910e2dc12b04f8390329) | 嵌套 GUI 与 canonical 相同 |
| oh-my-ztty | [a16ba86](https://github.com/LIghtJUNction/oh-my-ztty/commit/a16ba860108921b81f5fb4424d648bbd83f11415) | 嵌套终端与 canonical 相同 |

套件的正式二进制资产锁仍指向 v0.5.2，文件摘要保持不变。本分支是源码协调候选；没有创建新的套件发行版。zcalld 的服务实现和根 Cargo.lock 保持原样。

## 实际门禁

| 检查 | 结果 |
| --- | --- |
| 三个直接消费者 cargo check --all-targets --locked | zterm、zcall-gui、ztty 均通过；日志随附 |
| suite 六组件源码状态 | 全部初始化、干净、检出与记录一致 |
| sync | 通过，43 仓库 / 65 包 |
| check | 阻塞：只有下述 zmcl 源码不等价 |
| resolve --all | 同一源码门禁阻塞，未通过 |
| 显式选择其余 37 个 Rust 仓库的 resolve | 协调器的全局源码检查仍返回同一错误，未获得部分解析通过结果 |

保留原始 [check 日志](check-final.log)、[完整解析日志](resolve-all-blocked.log)、[显式选择日志](resolve-available.log) 和 [结构化记录](cohort.json)。协调器实现没有修改。新增 source_links 检查终端归档中的三个库副本及套件的终端副本，确保实际分发的 gitlink 也与 canonical 一致。

## 唯一外部源码阻塞

候选复用已发布 zmcl `7dc09fff213d659d99f98e61ebb2706654c0160b`。其 vendor/zgpui 固定 `4aba3ba83815253fb7e4013baa8bcf894439d32d`，聚合 canonical 则为 `b09f3ded0928df5a35bad32dcd5539560b8617e6`。两个副本的根 API/版本相同，整体仓库提交不同，严格源码等价检查据此拒绝快照。

```text
project-z: zmcl -> zgpui: noncanonical path zmcl/vendor/zgpui (expected zgpui)
```

zmcl 的 [AGENTS.md](https://github.com/LIghtJUNction/zmcl/blob/7dc09fff213d659d99f98e61ebb2706654c0160b/AGENTS.md) 要求单一 main 写入者，已有维护会话和活动工作树。交接给其现有写入者的 [最小补丁](zmcl-vendor-raster-owner.patch) 只更新 vendor/zgpui；版本和锁文件已是 0.1.5。补丁在该已发布源码上通过 `git apply --check --index`，没有新建 zmcl 分支或提交。

接手顺序：原写入者验证并发布该 gitlink 更新；协调者选择其新提交，然后重跑 sync、check、resolve --all。完整门禁通过后，才讨论合入聚合 main。
