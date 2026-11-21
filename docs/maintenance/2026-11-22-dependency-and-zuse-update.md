# 2026-11-22 依赖同步与 Zuse 更新

本记录列出本轮已完成的源码推送、正式发行与验证。提交号用于定位实际源码；测试夹具、已忽略测试及未完成的聚合工作分别说明。

## 已推送和纳入快照的源码

| 仓库 | 提交 |
| --- | --- |
| zuse | `b5ebbd3679af215706cbd73b17045e014f5e0524` |
| ssmcp | `dde2938e050e1d9f8186a600f57dbb67e12de211` |
| ztype | `bb2c1dc71a0f1dc77b56b0bc1bc7fd3cdb2501f8` |
| zuse-skills | `fce48d78dcbedbecaaa56a09fdf11b12b9a6b09a` |
| OniMods | `1b93643d3ec683aa2e512c7a5b42ae1177db5b33` |
| mechrevo-drivers | `e522bf8c612865043fdf766726b93066249fb6f8` |
| zclick | `732f958299e0e7b3522e4e85264083f8a0acafdc` |
| zharness | `5f9a9f58f090326bf2d43f4df2cc90c1bc674c21` |
| zterm | `15174fecfb441011e4ae35d0e361b88eec29bd7a` |
| zrc | `c127bd2965525adc05c46c6fba492aa1e45460f1` |
| zcalld | `61df8ac1c4e135f07313e6984dc389f49acc5afe` |
| ztty | `404864fa7f32ea485090cf331f3e96788a49cc8f` |
| oh-my-ztty | `2fa1b47d41fbc441b482d7c4c23beac0c1e903e4` |

本轮 ztty 依赖同步提交为 `094085e90eda4df1e696bbc16283527445ee5a8d`。同步期间，上游先发布 0.6.0 的 SSH/mux 改动，又完成 0.6.1 的发行准备及验收记录。后续提交只调整版本、发行文档和 CI 验证配置，运行代码及 zterm、zgpui 来源保持一致。

## Zuse 0.5.0 发行与安装

Zuse 0.5.0 已由上述源码正式发行。[GitHub 正式发行运行 44924731136](https://github.com/LIghtJUNction/zuse/actions/runs/44924731136) 的 5 个平台构建及 publish 均成功。

开发机的 `~/.cargo/bin/zuse` 已从 0.4 系列升级到 0.5.0。`zuse update --check` 返回 `up_to_date`，通道为 `github-stable`，`can_update=true`。14 个原生模块函数的预检通过。

## 已完成验证

| 范围 | 结果与证据范围 |
| --- | --- |
| Zuse 常规 Rust 测试 | 397 passed、19 ignored；ignored 项未计为通过。 |
| 浏览器长按 | 独立浏览器长按测试 1 项显式通过。 |
| GTK 草稿与取消 | 私有 GTK 测试 2 项显式通过，包括 800 ms 回复延迟下的快速取消。 |
| X11 长按 | 4 种情形通过；观测时长为 179/181 ms，取消 70 ms，失焦 84 ms。 |
| Wayland 长按 | 5 种情形通过。 |
| Zuse 其它门禁 | all-targets Clippy、no_std 检查及 updater 12 项测试通过。 |
| ssmcp | native 摘要记录 30 项通过；zuse_backend 28 项通过、4 项 ignored；不重播测试 1 项通过。 |
| ztype | 原生 `cargo test` 通过。 |
| ztty | 在 `c63dbd5` 上运行原生 `cargo test`，255 passed、8 ignored；当前锁定的 `404864f` 与其运行代码一致。 |
| zuse-skills | 代码提供 14 个函数，native 验证 34 项通过。 |
| oh-my-ztty | 套件检查 181 项全部通过；采用 ztty 0.6.1 后，37 项来源契约复测通过，六个组件的递归源码与来源锁一致。 |
| Project Z | 115 项测试通过。 |

ssmcp 的 `exec.read` 已支持展开有界、脱敏的详细结果。生产渲染器生成的两帧夹具图已由 reviewer 看图验收；证据范围是 fixture 输出，未作为 live 桌面截图验收。开发机 CLI 已安装本轮修复提交，版本号仍为 0.10.25；当前运行会话保持运行，新启动的 CLI 使用该修复。

GTK 验证覆盖自有夹具中的编辑与取消，不代表真实 ChatGPT 桌面会话或消息发送已验收。Zuse 的细节和边界见对应源码中的 [0.5.0 验证记录](https://github.com/LIghtJUNction/zuse/blob/b5ebbd3679af215706cbd73b17045e014f5e0524/docs/validation-0.5.0.md)。

Project Z 首次初始化时先获取各仓库当前默认分支，避免被不可获取的历史子模块提交阻塞，再记录实际提交。正式 CI 测试命令移除 `--lib`，适配 3 个不包含库目标的 fuzz manifest；库单元测试和集成测试仍由 `--tests` 执行。

发行工作流显式选择本轮聚合验证使用的 Rust 1.100.0，并在并行解析前安装 rustfmt、Clippy，避免多个 Cargo 进程同时首次初始化工具链时争抢下载临时文件。

Project Z 聚合 `check` 通过：45 个仓库、72 个包的 Git 来源、锁文件及当前默认分支一致。`resolve --all` 在 39 个仓库通过锁定依赖解析。聚合源码快照通过 `release.yml` 的正式发行流程发布，流水线会再次验证来源、解析依赖，并执行 Linux、Windows、macOS 的核心库测试；发行状态和产物见 [Project Z Releases](https://github.com/LIghtJUNction/project-z/releases)。
