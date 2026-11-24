# Zuse Wayland 窗口、截图与消费者传播

Zuse 主分支的 `9c66eec42e6768d6c790437d3cdcf288daaff265` 增加 Sway 和 niri 原生窗口 IPC，限制 Wayland 截图辅助进程的执行时间和输出，并在 PNG 完整且窗口几何稳定后替换文件。Linux 文本观察直接读取所需的无障碍字段，密码保护依据 AT-SPI 角色编号。运行时版本仍为 0.6.0，现有 `v0.6.0` 发行标签指向 `328117e3cd714bebab3ce45951bdaa1bdf52dda1`。

本体通过 `cargo test --offline --locked --all-features`、all-targets Clippy 和 wasm32 无标准库检查。隔离 GTK、Sway 1.12、niri 26.04 和 Hyprland 0.57.2 验收均通过。Sway 的区域 PNG 为 400 × 574，niri 的桌面 PNG 为 1280 × 800。使用私有 Cage 的 Hyprland 验收读取了 640 × 720 窗口截图的中心像素，并核对了实际前台和后台文本。该批次调试 CLI 的 SHA-256 为 `63a54a768ea8cea2b2692b5bb291605ecd2cbed53eb3c978a5c026f53c9775ae`。

| 消费者 | 验证来源 | 结果 |
| --- | --- | --- |
| ztype 0.4.2 | `85f55836d36dc292900d5c6ff50cb9627021a4b8` | 提交和推送 Cargo.lock，唯一变更为 Zuse Git SHA。离线锁定解析和 `cargo test --locked --offline --all-targets` 通过，73 通过，1 项需要独立词库而忽略。 |
| zuse-skills | `201a7508d3ed2928295ebaf0853ea4528212b980` | 以新 Zuse 验证 14 个函数的原生导入、描述和预检。将既有源码扩展登记到 Project Z。 |
| zuse-std 0.1.0 | `d79f43f8f3c2a1bff05962420f014b6c16403c5c` | 以 `v0.1.0` 添加并锁定安装，核对锁中 SHA，22 个函数可导入。完整 API 示例的 43 个步骤通过预检。 |
| SSMCP | `5daf52547c0402e78aa0a6a277d855b399e3308a` | 通过独立 CLI 消费 Zuse。当前源码的 `cargo test --offline --locked --lib computer::` 为 26 通过，1 个内部子进程夹具按设计忽略。开发机 SSMCP 0.10.27 在隔离状态目录通过 PATH 识别候选 CLI。 |
| zrc 0.1.2 | `6947a092eed4d0b989551970f6178d4cca59326b` | `scripts/check.py` 通过配置、组合和终端检查。Python 单元测试 11 通过，12 项需要设置 `ZRC_TEST_BINARY` 而跳过。它通过 SSMCP 间接使用 Zuse。 |
| oh-my-ztty | `b766c4bd9984b20c22bdacf10df973683fb97f4a` | 使用锁定的 zshard 源码，33 项隔离 shell 补全测试通过。图中补登套件随包分发的 Zuse 补全关系。套件的 SSMCP gitlink 为 `4c8b05c46c01cc9796edc443eb18deb5b6d99b8d`。 |

Project Z 的 catalog、gitlink 和生成页记录 Zuse、ztype 和 zuse-skills 的上述提交。核对三个更新的 gitlink 及其递归来源、两个 Rust 锁、Cargo 元数据和生成页。协调器的图、版本声明和 Git 策略测试共 27 项通过。聚合的 `check` 和 `resolve --all` 在本次隔离检出中停于未初始化的 `z58`。另外，远端新鲜度检查发现基线的 SSMCP、zdot、zgpui、zrun 和 zsys 已落后公开主分支。这些变化各自需要消费者同步，完整聚合验收由 Project Z 维护者 [LIghtJUNction](https://github.com/LIghtJUNction) 继续协调。

托管安装仍使用现有 Zuse 发行资产。SSMCP 管理的下载、依赖它的 zrc 运行时和 oh-my-ztty 安装包，需要新的正式 Zuse 资产后再做发行级验收，交由各仓库维护者 [LIghtJUNction](https://github.com/LIghtJUNction) 接续。
