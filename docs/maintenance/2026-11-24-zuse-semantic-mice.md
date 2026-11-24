# Zuse Wayland 语义鼠标传播

Zuse `1df2ab46fa39349627fafa52120d9d0bb9fa1454` 增加独立的穿透光标与 AT-SPI 控件动作。动画在同一输出内逐帧提交位置，复用既有 Wayland 图层。脚本的五只鼠标在同一 `parallel` 组运行，每条移动计划为 600 毫秒。

现场 Hyprland 的五个 GTK 按钮各收到一次 AT-SPI 回调，该轮手动计数均为 0。私有 Hyprland 复测确认五条轨迹重叠、五个控件各触发一次、错误控件名未触发操作、系统鼠标保持在 `(400, 300)` 且键盘焦点不变。验收二进制 SHA-256 为 `57a8a2139d2c524d3d21573eaf231178872703d7b8501eea9fe76e78391f452e`。Zuse 本地测试 498 通过、22 忽略，all-features Clippy 和 wasm32 无标准库检查通过。

| 消费者 | 精确来源与回执 |
| --- | --- |
| ztype | `e237997a5a26b6f9e33b817ada4ddb9bac6e2465` 的 Cargo.lock 只更新 Zuse 来源。锁定解析通过，all-targets 测试 73 通过、1 忽略。 |
| zuse-skills | `201a7508d3ed2928295ebaf0853ea4528212b980` 的 14 个原生函数通过导入、描述和预检。 |
| zuse-std | `d79f43f8f3c2a1bff05962420f014b6c16403c5c` 的 22 个函数可导入，43 步 API 示例预检通过。 |
| SSMCP | 本机 SSMCP 0.10.31 在隔离状态目录识别新构建的独立 CLI，版本为 0.6.0。 |
| zrc | `6947a092eed4d0b989551970f6178d4cca59326b` 的配置和组合检查通过，Python 测试 11 通过、12 项无原生 CLI 夹具而跳过。 |
| oh-my-ztty | `b766c4bd9984b20c22bdacf10df973683fb97f4a` 使用锁定的 zshard，33 项隔离 shell 补全测试通过。 |

Project Z 记录 Zuse 和 ztype 的已验证源码。图、版本声明和 Git 策略测试 27 项通过。整图的 `check` 和 `resolve --all` 需要初始化其余子模块并处理其他上游来源的更新，交由 Project Z 维护者 [LIghtJUNction](https://github.com/LIghtJUNction) 接续。正式下载仍使用原有 `v0.6.0`，SSMCP 托管下载、zrc 集成和 oh-my-ztty 整包交付等待新资产后由各仓库维护者 [LIghtJUNction](https://github.com/LIghtJUNction) 验收。
