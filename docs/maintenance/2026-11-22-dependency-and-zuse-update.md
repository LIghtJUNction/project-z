# 2026-11-22 依赖同步与 Zuse 0.6 更新

Zuse 0.6.0 已完成源码验证和开发机安装，SSMCP 最终合并源码验收及套件来源同步已通过并发布；SSMCP CLI 也已安装。Project Z 的最终本地聚合检查及完整锁定解析通过，正式发行由 release.yml 对本记录所在提交单独执行。

本记录按源码提交、源码树和执行批次划分证据。已忽略测试不计为通过，历史结果不替代新生产变更的验收。

## 源码与发行身份

| 对象 | 精确来源 | 本记录状态 |
| --- | --- | --- |
| Zuse 开发源码与 Git 安装 | `6e88dd885eb73545a1ab6a9cd50097ef63fba423` | 已安装 0.6.0；执行源码沿用已验证的 `e733abb` |
| Zuse 官方 `v0.6.0` 标签的提交 | `328117e3cd714bebab3ce45951bdaa1bdf52dda1` | 五平台构建及发布成功 |
| SSMCP 最终发布提交 | `add39e18ff92680ff3ac0c3e911407956e20b228` | 已推送；源码树验收通过，CLI 已安装 |
| ztype | `1b08bedd4ffb1ef68effa5aea32c31775e51d268` | 已推送；新渲染来源的默认功能编译通过，最终锁完整解析通过 |
| zuse-skills 夹具修复发布 | `201a7508d3ed2928295ebaf0853ea4528212b980` | 已正常推送，本地已对齐 |

[Zuse 正式发行运行 44937714591](https://github.com/LIghtJUNction/zuse/actions/runs/44937714591) 的五个平台构建和 publish 均通过，产物见 [v0.6.0](https://github.com/LIghtJUNction/zuse/releases/tag/v0.6.0)。该流水线没有执行测试，不能作为下表测试结果的来源。

标签提交 `328117e`、完整测试提交 `e733abb` 与当前安装提交 `6e88dd8` 的 Zuse 执行源码相同，但依赖锁不同。后续锁提交将 Zmcpio 的版本和来源更新为 0.5.3／`89a247a`，其生产代码也没有变化。官方发行产物、完整测试来源和当前 Git 安装分别记录，未以一个来源替代另一个来源。

## 本轮已落地的修复

- Zuse 的有界按键保持、取消和焦点保护，以及 X11／Wayland 的按键映射修复，已随 `e5cb15a` 集成并保留在 0.6 中。桌面模块通过进程和目标控件守卫操作草稿；0.6 又增加持久控制会话、有界程序控制流和包消费能力。
- SSMCP 的 `exec.read` 详情限制长度并清理终端控制内容；独立 Zuse 管理器使用配置好的 TLS 客户端，覆盖无全局 provider 的独立进程 TLS 客户端构建和不支持目标的明确返回。JSON 模式的操作错误返回单行 MCP 错误收据，并保留失败状态。
- SSMCP 的发行归档校验兼容官方 Zuse 0.6 新增的文本文件，同时保留成员路径、链接、权限和唯一平台二进制约束。
- zuse-skills 的 GTK 夹具改用自有 Xvfb、私有 session、显式 accessibility bus 与 registry，包含有界就绪等待和清理；草稿、PID、焦点、空内容覆盖及不激活窗口的既有断言保持不变。
- Project Z 的初始化从观测到的默认分支建立隔离检出，避免先访问已不可用的历史 gitlink；正式验证预先初始化 Rust 1.100.0，去掉不适用于无库目标 fuzz manifest 的 `--lib`，并统一 Git、Cargo、文件和命令输出的 UTF-8 编码。协调器的 120 项测试已在先前正式运行中通过；新快照仍由最终发行工作流重新验证。

## Zuse 0.6.0 验证与安装

| 检查 | 实际结果 | 来源与边界 |
| --- | --- | --- |
| `cargo test --workspace --locked` | 477 passed、20 ignored | `e733abb` 原生运行；按 45 个测试目标计数，排除嵌套输出重复计数 |
| all-targets Clippy | 通过 | `e733abb` 原生同批次；`cargo clippy --locked --all-targets -- -D warnings` |
| no_std 核心 | 通过 | `e733abb` 原生同批次；`cargo check --locked --no-default-features --lib` |
| zuse-skills 原生预检 | 14 个函数通过 | 已安装的 0.6.0；预检不执行真实应用函数体 |
| Git 安装 | 0.6.0 | 使用官方 canonical Git URL，无 branch、tag 或 rev 固定参数 |
| `zuse update --check` | `up_to_date`、`can_update=true` | 已安装 CLI 的实际结果 |

安装使用 `cargo install --git https://github.com/LIghtJUNction/zuse.git --locked --bin zuse`，保留开发机原有 Cargo 安装目录和可更新来源。最终依赖同步后再次安装，Cargo 安装记录为 `6e88dd88`，更新检查为 `up_to_date` 且 `can_update=true`，SSMCP 实际识别外部 Zuse 0.6.0。477 项测试保留在 `e733abb` 的原始批次；没有将元数据更新表述为一次新的完整测试运行。

## zuse-skills 的 35 项验证

模块目录继续导出 14 个函数。原批次 35 项中有 34 项通过，私有 GTK 项因 `dbus-broker` 在无 systemd 的私有 session 中启动失败，未被记为通过。

修复后的 GTK 单项在原生环境复跑通过，耗时 4.109 秒。该单文件修复的源码树为 `562036b56807819aca371f5413eab92ab856092d`；原 `check_private_draft` 的 AST 和行为断言保持不变。

两次运行合计覆盖 35 个不同测试：原批次 34 项，加上修复后单项 1 项。没有把它表述为一次整批 35 项全通过；修复已随 `201a750` 正常推送，本地已对齐。

GTK 结果只证明私有夹具中的草稿机制。真实 ChatGPT Desktop 的 AT-SPI 入口、目标会话、后台草稿写入和消息发送仍未完成应用验收。

## SSMCP 分阶段证据

| 源码范围 | 检查与结果 | 状态 |
| --- | --- | --- |
| 历史基线 `ffb7f32f527357202194b41be7b7a904153a02ba` | 原生 Rust 2094 passed、30 ignored；Clippy 通过 | 仅适用于该历史基线范围 |
| 同一历史基线范围 | JavaScript 64 项、Python 125 项通过；Python 为原 113 项加上游新增 12 项发行回归 | 保留历史结果，不作为当前完整测试结果 |
| `ffb7f32` 加 0.6 归档及来源补丁；源码树 `5f278cd7b46b9421fcccccb554a9ca58f182b635` | computer 24 passed、1 ignored；all-targets Clippy 通过 | 该源码树已通过 |
| 上述 `5f278cd` 源码树 | 官方 0.6 manager 全链通过；user-wait 192 项检查通过，耗时 26.994 秒 | 已完成的独立原生验收 |
| `834522e` 加归档补丁；源码树 `c184077be2ae416bbf2ca88cfb9da82e974471f8` | computer 24 passed、1 ignored；JSON CLI 新回归 1 项通过，含 6 类分支；Clippy 通过 | 最终合并源码门禁已通过，不替代历史完整测试计数 |

归档补丁兼容实际 15 个 skills 文本路径及 `examples/session_client.py`，保留路径、链接、权限、重复成员和唯一平台二进制校验。相对 `834522e` 仅修改 `src/computer/archive.rs`、`src/computer/tests.rs` 两文件，已随 `add39e18` 正常推送；开发机 CLI 已安装，`ssmcp --version` 为 0.10.25，`computer version --json` 已识别外部 Zuse 0.6.0。

最终 `c184077` 源码树的官方 0.6 manager 下载、安装、版本识别、PATH 优先级、卸载及外部 Cargo 安装保全均通过；user-wait 的 192 项检查通过，耗时 26.945 秒。验收使用私有目录、自有测试账户、回环服务与合成 PTY，不构成真实桌面消息发送验收。

历史完整 Rust 运行首次在默认并发下出现一个 15 秒完成观察窗超时；隔离运行及同源码八并发复跑通过。未修改产品代码或放宽时限，具体根因没有被证明。

## 依赖闭合、ztype 与 zrc

Zclap 当前来源为 `a4c7e6f3e0ff860de701573117248fe8538c71e5`，包版本仍为 0.1.4。相对旧来源 `4d87f3a`，变更只有文档、源码文档注释和单独 `-` 选项值回归，没有执行代码或依赖变化。六个直接消费者 zclick、zdot、zmcl、zuse、lmm-api-source、mechrevo-drivers 的锁均同步该来源；zmcl 的 `vendor/zclap` 也已对齐。

| 生产者 | 版本与最终来源 | 本轮新增变化与验证 |
| --- | --- | --- |
| zgpui | 0.1.8／`eeb909e956ed0cff05e14525d4f29f5a78c553ec` | 可选材质与透视等能力、Linux 固定字号 emoji 缩放；官方精确来源的 13 项发行任务全部成功 |
| zhex | 0.1.3／`9fc8de3901b2726e650537f4a6330355e8a965e7` | 只增加无效字节显示回归；官方精确来源的 11 项 CI 任务全部成功 |
| zi18n | 0.1.0／`755549f82fa513c4e4f2f5aaf6fdeea8da4a6347` | 文档与私用段 locale 回退测试；新增回归 1 项通过 |
| zmcpio | 0.5.3／`89a247ac274bcd96b760dd9e7dcb0d4d924a901e` | 发行验证工具和自身版本更新，Rust 生产代码、API、功能与依赖不变；现有离线发行工具测试 36 项通过 |
| zcall | 0.4.2／`aaac54236f7ce0f4e1559c6e3b78d680d9dabf41` | 已传播至对应消费者，完整锁定解析纳入聚合门禁 |

[zgpui 发行运行 44942576343](https://github.com/LIghtJUNction/zgpui/actions/runs/44942576343) 覆盖 Linux／macOS／Windows 核心与 native、Linux 软件后端、raster、无标准库目标及打包发布；[zhex 运行 44938260851](https://github.com/LIghtJUNction/zhex/actions/runs/44938260851) 覆盖双架构与工具链、标量／SIMD、Miri、无标准库和打包检查。这里复用实际对应提交的公开结果，没有重复启动生产者矩阵。

zhex 来源继续传播到 OniMods、mechrevo-drivers、lmm 与 lmm-api-source；zgpui 来源传播到 zterm、zcall-gui、zmcl、ztty 与 ztype。随后同步 lmm-api-source 的 `apps/cli`、zcalld 的 `apps/zcall-gui`、ztty 的 `crates/zterm` 和套件的 `components/ztty`。相应 Cargo 锁和嵌套 gitlink 一起更新，各候选均核对非目标包不变；最终来源以 `catalog.json` 和发行 `commits.txt` 为准。

ztype 已纳入 `a64866a` 的分解形式 ü 修复。先前沙箱纯逻辑测试 29 passed、1 ignored，覆盖 `u/U + U+0308` 的候选匹配、取消、焦点变化及确认；ignored 项需要额外安装完整词库。采用 zgpui 0.1.8 和同源 zgpui-raster 0.1.0 的 `c545d587` 已在开发机通过默认功能 `cargo check --locked --lib`，耗时 4.273 秒。此前沙箱同一检查因缺少系统开发头文件失败，未计为通过。其后的 Zmcpio 0.5.3／Zuse 来源更新仅影响锁文件，完整 metadata 解析通过，包含 19 个包和 19 个解析节点，沿用已核实不变的执行源码及上述默认功能编译证据。

ztty 新来源 `c0f195d9b93065040b4efef35f3615831db11b38` 已正常推送。开发机 `cargo check --locked --bin ztty --features wayland` 通过，耗时 5.132 秒，实际编译新 zgpui 与 zterm 来源。未据此宣称完成真实窗口或输入交互验收。

zclick 上游 `c437230dcf9467b9d1decaf0142215ea054bcf07` 修复 Python 帮助格式化的缩进及换行。真实 Rust／PyO3 扩展配合固定 Click 8.5.1 执行新增回归，4 passed、22 deselected；依赖审计通过，临时 registry 投影未改动真实 Cargo.lock。

同步期间 zcalld 上游发布 `8e52d791c305a3730d2ea876b8dffb6be2e2c04c`，包含用量采集、Git 技能来源及网关请求缓冲改动，并引用 GUI `daa540307573d86838b108f4a76aa45230fca5f5`。已采用这组来源，本次在其核心上实际执行新增范围的 11 项回归：请求缓冲 3 项、Git 来源边界 2 项、用量采集 6 项，全部通过，使用 Rust 1.100、`--locked --offline`。两个仓库的 Cargo 清单、锁与版本没有变化，GUI 的 zgpui 仍为 `eeb909e`，不引入新的锁传播。

该上游提交附带 core 183、GUI 43、integration 113、UI 状态 28 的验收报告；这些数字不是本次重跑结果。报告精确记录 GUI 提交和二进制哈希，但 core 只有与报告同提交的来源说明，因此本记录以本次实际执行的 11 项回归作为新增核心验证证据。GUI 的新增用量页、记录配置、显式确认重启、provider 搜索与四语言文本已做只读范围审阅，未发现确定阻断；四语言键集合一致，错误读取、历史保留、显式重启确认及成功回执后清除 pending 的边界保持明确。上游 GUI 夹具使用私有 Xvfb 与模拟 CLI；provider 搜索没有独立行为断言。本次没有把这些证据扩大为真实服务或桌面应用验收。

同步期间 zrc 上游推进到 `31f37e9bb8f5c5adcf195f68692c47ec7ea26705`，修复 Unix 附着式 `--output=` 的非 UTF-8 路径保留，并增加隔离发行投影；依赖清单和锁没有变化。沙箱最小现有回归中，Rust 边界 1 项、真实本地 CLI 边界 3 项、发布投影纯配置 2 项均通过；未执行完整 crate 发布验收。

## zuse-std 包消费验收

`zuse-std` 已登记为第 46 个仓库，聚合配置为 `role=extension`、`manifests=[]`、`requires=["zuse"]`。main 与公开 `v0.1.0` 均指向 `d79f43f8f3c2a1bff05962420f014b6c16403c5c`。

原生任务 294 使用已安装的 Zuse 0.6.0 `e733abb`，在全新私有消费者目录完成包初始化、添加公开 v0.1.0、`install --locked` 和列表查询，全部通过且锁中 SHA 正确。收据为原生 Project Z 目录下的 `dist/zuse-std-0.6-acceptance-20261122/report.json`。

只读导入列出 22 个函数，完整 API 预检 43 步通过，深度 5 的递归预检生成 243 个 `draw.triangle` 步骤并通过。该批次没有发送桌面输入；预检结果不代表图形动作已实际执行。

## 聚合状态与正式发行门禁

最终聚合检查已覆盖当前实际登记的 46 个仓库；Git 来源、锁、嵌套 gitlink、默认分支 HEAD 与生成文件一致。新增包的独立验收之外，已完成该新范围的完整 `check` 与锁定解析。

| 项目 | 当前状态或待填结果 |
| --- | --- |
| SSMCP CLI 安装 | 任务 298 已通过；`ssmcp 0.10.25` 来自 `add39e18`，并识别外部 Zuse 0.6.0 |
| oh-my-ztty 最终来源 | `9ef19ba20e8b4ea9f380d08085e417d63eb5a3d6` 已正常发布；六组件采用 ztty `c0f195d`、SSMCP `add39e18`、zdot `645fa9a`、zrc `31f37e9` 以及已锁定的 zshard／zfetch |
| 套件实际来源契约 | 最终沙箱 `build_bundle.verify_sources(lock)` 通过六组件及全部递归子模块检查；锁时间为 `2026-11-21T20:33:08+00:00`。早一批套件来源的原生契约检查也通过；没有将其表述为最终两路径补丁的新原生验收，未重复 181 项套件测试 |
| Project Z 聚合源码身份 | 以本记录所在提交及正式发行的 `commits.txt` 为准，避免在提交内容中自引用该提交 SHA |
| Project Z 最终 `check` | 通过：46 仓库、72 包，耗时 59.267 秒；实际核对当前远端默认分支 |
| Project Z 最终 `resolve --all` | 通过：39 个仓库完成实际 `--locked` 解析，耗时 10.134 秒 |
| Project Z 正式发行 | 由 `release.yml` 对本记录所在提交执行 minor 发行；正式标签、三平台任务结果和产物以 [发行页](https://github.com/LIghtJUNction/project-z/releases) 及对应运行记录为准 |
| 当前自定义 Zuse 技能同步 | 已完成并确认远端；保持 skill_id `6b015bc7f20881918ef80aa56dcdbaec`，作者提交 `2409237b6f9f3539e66ecbc4423dcbd4743200b9`，服务端物化提交 `cee389cad954478b44fb04120b1e44897b3867d0`；4 文件更新的 quick_validate、链接、元数据检查及 reviewer 均通过 |
