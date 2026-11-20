# 已验收的组件源码快照

本阶段接续已独立审查的聚合提交 `8c789ef69297ca344f667cbe1bcdf223d79babf2`，更新下列 gitlink。[第一阶段提交](https://github.com/LIghtJUNction/project-z/commit/8c789ef69297ca344f667cbe1bcdf223d79babf2)

| 仓库 | 原 gitlink | 本阶段 gitlink |
| --- | --- | --- |
| `ztty` | `1631db8a02e8627d5d35ac0e1d4bef93475f45dc` | `6e2ce246b0b50e6b82da99756832feae6e966f21` |
| `zmcl` | `35eb8a3242a6ba637266ba1480354138389c9cb0` | `2b1218f70cf89fb042fd725d4ef92dcb4e67dfe9` |
| `zguard` | 首次登记 | `5cdd637edbb075f6611f88f8566e15de4b360cca` |

## 组件验收依据

- **ztty 0.5.2** 的 `v0.5.2` 标签指向 `6e2ce246b0b50e6b82da99756832feae6e966f21`，tree 为 `57c38b1e962578a29dae65c4e54adab65fd6b1bf`。正式运行 `44712216777` 第一次执行成功。GitHub Release `452506520` 于 `2026-11-20T09:45:17Z` 发布，包含 47 个附件。[正式运行](https://github.com/LIghtJUNction/ztty/actions/runs/44712216777) · [GitHub Release](https://github.com/LIghtJUNction/ztty/releases/tag/v0.5.2)
- ztty 的 Cargo 包于 `2026-11-20T09:45:34Z` 发布。独立实际下载及安装回执记录归档为 7,791,804 字节，SHA-256 为 `75e3c82bbd2ca39334f554169027ae9a16c12f326af225faec7907d8cb664025`，包内 VCS 元数据指向干净的 `6e2ce24`。源码与归档的 22 节点依赖图及 features 一致，六个原由本地源码提供的包在归档中均使用精确注册表版本 `zgpui 0.1.2`、`zgraphics 0.2.0`、`zinput 0.1.3`、`zpty 0.2.3`、`zterm 0.5.2` 和 `ztty-plugin-api 0.1.0`。既有独立回执确认 Linux x86-64 的交互式 Zsh 入口使用已安装的 registry 0.5.2，启用 `wayland`。[固定版本发布报告](https://github.com/LIghtJUNction/ztty/blob/76fa2cfd13b776c027d5a86fadafde8e035f88f2/docs/releases/0.5.2/report.zh-CN.md) · [发布证据](https://github.com/LIghtJUNction/ztty/blob/76fa2cfd13b776c027d5a86fadafde8e035f88f2/docs/releases/0.5.2/publication-evidence.json) · [归档验证摘要](https://github.com/LIghtJUNction/ztty/blob/76fa2cfd13b776c027d5a86fadafde8e035f88f2/docs/releases/0.5.2/package-verification-summary.json) · [官方归档](https://static.crates.io/crates/ztty/ztty-0.5.2.crate)
- **zmcl 0.1.1** 的 `Cargo.toml` 和 `Cargo.lock` 确认 `zi18n =0.1.0` 由 `gui` feature 启用，新增的 `vendor/zi18n` 固定到 `b90984b48465a764bcb699ad2bb3251fa7020024`，与聚合源码一致。`vendor/zgpui` 仍为 `5b268da910639abd2fb8e581acb4f6eed50b7516` (`0.1.2`)，`vendor/zclap` 和 `vendor/zconv` 保持第一阶段的固定源码。界面初始化通过 `Catalogs.lookup(...).text()` 读取九个既有英文标题，绘制路径使用返回的文本，测试逐字节核对原文。维护者报告 78 项应用测试、19 项核心测试、严格 Clippy 和从空构建目录执行的 `--no-default-features` 构建均通过。聚合清单据此登记 `zmcl → zi18n`。[消费源码](https://github.com/LIghtJUNction/zmcl/commit/2b1218f70cf89fb042fd725d4ef92dcb4e67dfe9) · [标题与断言](https://github.com/LIghtJUNction/zmcl/blob/2b1218f70cf89fb042fd725d4ef92dcb4e67dfe9/src/gui/titles.rs) · [绘制入口](https://github.com/LIghtJUNction/zmcl/blob/2b1218f70cf89fb042fd725d4ef92dcb4e67dfe9/src/gui.rs)
- **zguard 0.1.0** 的 `v0.1.0` 标签指向 `5cdd637edbb075f6611f88f8566e15de4b360cca`。发布源码的库为零依赖 `no_std`。实测 crates.io 归档为 20,455 字节，SHA-256 为 `641d20929078aba7e9eb6ae9c33ae89d9b23d3a0f12f0eebb8fd05dacc93eb40`，包内 VCS 元数据指向干净的同一提交。索引校验值一致，正式 GitHub 附件与 registry 归档逐字节一致。[正式发布](https://github.com/LIghtJUNction/zguard/releases/tag/v0.1.0) · [索引](https://index.crates.io/zg/ua/zguard) · [官方归档](https://static.crates.io/crates/zguard/zguard-0.1.0.crate)
- zguard 正式运行 `44713799452` 的三平台原生验证、裸机库编译和包验证通过。发布作业完成 Cargo 发布后，在 GitHub Release 附件步骤失败。维护者随后以同一标签和归档完成 GitHub 发布。后续发布工具修复 `24890a70ba2a5e4f283f3c31eb30721143ffd9b5` 的变更范围为工作流、脚本、文档及发布测试。[正式运行](https://github.com/LIghtJUNction/zguard/actions/runs/44713799452) · [发布工具修复](https://github.com/LIghtJUNction/zguard/commit/24890a70ba2a5e4f283f3c31eb30721143ffd9b5)

## 聚合核对

`python3 scripts/project_z.py sync` 生成 43 个仓库和 62 个 Cargo package 的清单。`python3 scripts/project_z.py check` 退出 `0`，版本、依赖图、源码路径和生成文件通过检查。101 个递归子模块检出全部匹配记录的 gitlink。`impact --repositories zi18n` 返回 `zi18n` 和 `zmcl`，`impact --repositories zguard` 返回 `zguard`。本阶段组件发布与安装结论引用上述既有证据。聚合 `resolve --all` 的独立通过记录对应 `046bb4b0b73f82e0943c92d7c81facb9968b8520`。[独立验证回执](independent-validation-046bb4b.json)

## 待验收范围

- oh-my-ztty 继续固定 `0fdc87873c53e7c87d18952f83a7b94fc4149de5`。等待唯一的 0.2.6 发布负责人交付已核实的不可变套件源码、组件制品和锁文件。在验收套件的最终 pins 后运行一次完整 `resolve --all`。
- SSMCP 继续固定 `bfe5f25ffab718f100b11d2ce55c8dc839cbad71`。完整功能版本 21 由单一负责人完成源码及正式发行验收。
- zgpui 0.1.4/0.1.5 消费者、zmcl 后续原生 GUI 版本、zcall 0.4 与 zharness 0.6.0 由各自负责人验收固定源码和精确依赖约束。zharness 对 zguard 的消费关系随该后续批次核验。
