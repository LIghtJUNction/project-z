# Project Z：共享库、应用与安装套件协同维护

更新时间：2026-11-20T02:19:12.741729+00:00。本报告对应固定源码快照，仓库与提交清单见文末；发布制品、应用运行验收和用户机器上的安装状态分别记录。

## 已完成的协调层

Project Z 当前统一固定 **42 个仓库、60 个 Cargo package**。相对先前 29 仓库协调快照，本批新增登记 zgpui、zinput、ztype、zrc、zfetch、zdistro、zmcl、zpty、zgraphics、zterm、OniMods、zcall-omarchy、mechrevo-drivers，共 13 个仓库。相对 PR #3 的 main 基线 `9d72d19`，本 PR 净增加 15 个仓库（另包含先前接入的 lmm-api-source、zcall-gui），并将旧 ztui 名称迁移到 ztuio；两种计数使用不同的比较基线。

统一清单记录真实工作区、包名、版本、来源提交、Cargo 依赖，以及运行时、安装和源码分发关系。生成文件包括 `catalog.json`、`.cargo/project-z.toml`、`docs/PROJECTS.md`，政策入口为 `project-z.toml`。各仓库继续独立开发和发布，聚合仓库固定一次可以一起检查的源码组合。

已经完成的协调器检查包括版本约束、Cargo 依赖环、退役名称、工作区包归属、来源等价性、生成文件一致性以及实际 Cargo 解析。`ztty-ui` 与 `ztui-core` 是禁止重新引入的旧名称；替代职责分别由 zgpui 与 ztuio 承接。运行时和源码打包关系可以互相引用，这不等于 Cargo 包之间存在依赖环。

### 修复同名同版本的两份路径来源

全量解析实际发现：SSMCP 的 `crates/zplugin` 与聚合根目录 `zplugin` 虽然固定在相同提交，仍被 Cargo 视为两个路径身份，不能无歧义地写入同一个锁文件。协调器现在按每个工作区选择唯一来源：显式路径指定的副本必须与 canonical 源码的 Git 提交、仓库内相对包路径和干净状态一致；选择后，同仓库全部可发布包及过程宏一起切换，并继续协调传递的普通和构建路径依赖。

当前工作区的开发依赖参与检查，传递依赖自身的开发依赖不会传给调用者，遵循 [Cargo 的开发依赖语义](https://doc.rust-lang.org/cargo/reference/specifying-dependencies.html#development-dependencies)。不同工作区可以各自使用已验证的副本；同一工作区显式要求两个不同物理来源时会报告冲突。解析和真正执行 Cargo 命令使用同一套临时配置，结束后恢复锁文件内容、权限和存在性，不覆盖预先存在的其他配置。

修复与 80 项本地回归已推送：[01ba817](https://github.com/LIghtJUNction/project-z/commit/01ba8176c3ad9a63b384889f90c016a10ceecf6e)。真实离线 Cargo 夹具先重现旧冲突，再验证新配置只解析出一份 runtime 和 macros，并验证传递开发依赖不会污染消费者。提交前只移除了两个 Python 文件末尾各一个空行；源码散列和 AST 一致证明与测试收据一起保存。

## 改动如何传播到消费者

一次基础库变更需要同步三个不同事实：manifest 允许什么版本、Cargo.lock 固定什么包、子模块固定什么源码。应用还需要适配真实调用方式和运行行为；安装套件则需要接入已经发布的实际应用制品。只通知下游或只提高版本号不构成完成。

`impact --repositories` 把 Cargo 普通、构建、开发依赖与政策清单中的运行时、安装及源码分发关系合并。下面列出本次固定快照的实际传递范围，均包含变更的库自身。

| 变更仓库 | 传递影响范围（包含自身） |
| --- | --- |
| zsys | oh-my-ztty, ssmcp, zcall-gui, zcall-omarchy, zcalld, zcalld-compat, zharness, zinput, zplugin, zrc, zsys, zterm, ztty, ztype, zuse |
| zuse | oh-my-ztty, ssmcp, zrc, ztype, zuse |
| zui | zcall-gui, zcall-omarchy, zcalld, zcalld-compat, zmcl, ztype, zui |
| zgpui | oh-my-ztty, zgpui, zterm, ztty |
| zpty | oh-my-ztty, zpty, ztty |
| zgraphics | oh-my-ztty, zgraphics, zterm, ztty |
| zterm | oh-my-ztty, zterm, ztty |
| zplugin | oh-my-ztty, ssmcp, zcall-gui, zcall-omarchy, zcalld, zcalld-compat, zharness, zinput, zplugin, zrc, zterm, ztty, ztype |

完整逐仓库传播矩阵保存在 `docs/evidence/2026-11-20/repository-impact.json`。zcalld 的 GUI、Omarchy 前端和兼容扩展既是消费者，也参与其源码分发，因此分别登记了实际关系；三处嵌套 Gitlink 已与根目录固定来源逐一比较。

### 公共能力的边界

| 组件 | 当前职责与边界 |
| --- | --- |
| zsys | 共享操作系统能力入口；当前实际直接消费者由清单给出。zpty 的 PTY/ConPTY 底层尚不能宣称已经全部统一到 zsys。 |
| zgpui | 无标准库场景中的场景、布局等共享 UI 能力；通过 zterm 进入当前终端消费链。与 Zed GPUI 的公平性能对照另行记录。 |
| zui / zui-native | 独立的原生窗口和 GL 路径，服务 GUI 应用；不能仅凭名字视为 zgpui 的同一实现。 |
| zinput | 共享输入与插件边界，由实际 manifest 跟踪消费者。 |
| zpty | PTY/ConPTY 与底层终端进程能力；Linux 本库当前没有非零的独立 unit 集合，实际 PTY 行为由消费者验收覆盖。 |
| zgraphics | Kitty/Sixel 图形协议、RGBA 图像与放置状态；不承担操作系统窗口和最终渲染后端。 |
| zterm | 终端解析、屏幕、历史和共享场景连接；当前普通 Cargo 依赖包含 zgpui。 |
| ztty / oh-my-ztty | ztty 是终端应用；oh-my-ztty 是组合终端、SSMCP、shell 与配置的发行和安装套件。两者需要分别跟踪源码与安装版本。 |

## 验证结果与证据范围

| 验证 | 实际结果 | 证据与范围 |
| --- | --- | --- |
| 协调器本地回归 | 80/80，通过，无跳过 | 真实 Git/Cargo fixture、版本规则、来源、工作区隔离和锁恢复 |
| 版本、图和生成文件 | 42 仓库、60 包通过 | 固定快照；Cargo 依赖无环，约束一致 |
| 全量实际 Cargo 解析 | 36 个 Rust 仓库通过 | 包含应用；确认 canonical 源码或同提交干净等价副本 |
| 锁文件与配置恢复 | 前后散列、权限、存在性一致 | 解析后静态检查再次通过 |
| 既有核心库检查 | 20 个库仓库检查退出码为 0 | 不是 20 个单测，也不是全部应用验收 |
| 新终端库发布来源 | 3/3 下载与源码核验一致 | API、索引、crate checksum、VCS、载荷 |
| ztty 消费者功能 | 原全套 300 项；Wayland 另次 65/65 | 原 20/21 阶段状态与夹具失败保留 |
| ztype 消费正式 zuse 0.2.1 | 构建/Clippy及 11 项原生验收通过 | 固定 037de997，实际 GTK 接收 |
| zcalld 正式候选 | 五平台构建通过；未确认正式发布 | 固定 c72a1cb9，publish/aur skipped |
| SSMCP 新应用组合 | c44 的 73 项发布脚本测试、格式与 GTK C 语法通过；Clippy 资源中止 | 聚合仍固定 ecc450f；新组合尚未完成应用构建、原生验收和套件接入 |
| zgpui/GPUI 性能对照 | 无性能结果 | 构建曾因资源守护停止，后续准入未通过 |

所有根聚合 Cargo 操作均在独立验证副本中执行。最终全图解析使用受限 systemd 单元、单 Cargo job、低优先级和零任务 swap；持续记录全机可用内存，低于保留余量则停止任务。它验证依赖解析和来源，不代替每个大型应用的数据库、设备、桌面或跨平台运行验收。

### zuse 0.2.1 与 ztype

zuse 0.2.1 的正式发布源码为 `d930769005d307c42639e8abedc81ab039427e40`，注册表实际下载校验和为 `8da9a00ef8468d196234a99cb4d7f47991d9fb1ef704f67da2ce63d46395ea04`。正式五平台发布及 Linux 发布包的 17 项 GTK、12 项 MCP、5 项 PTY、11 项 USB C ABI 验收有独立回执。

ztype 已固定 `zuse-computer = "=0.2.1"` 与真实 registry lock，功能和证据提交为 [037de997](https://github.com/LIghtJUNction/ztype/commit/037de9972e169942ca6258d6aee6ba53711204f6)。Clippy、应用和 kana 动态库构建，以及 11 项真实 GTK 接收验收通过。输入界面继续保持两行紧凑候选条；当前是基于小型起步词表及多种引擎的组合输入应用，包含假名、Unicode/原文、自定义表、原生插件与显式目标送达。完整整句预测和系统级 IME 前端仍待实现。

zuse [正式发布](https://github.com/LIghtJUNction/zuse/releases/tag/v0.2.1)；[发布回执](https://github.com/LIghtJUNction/zuse/blob/889e4c4c17c903159fb4616dd6ee565001919767/docs/evidence/release-0.2.1.json)；[ztype 中文验收报告](https://github.com/LIghtJUNction/ztype/blob/91edc97aab1bea18f15f56e1ee2ec0651cc85916/docs/delivery-2026-11-20.zh-CN.md)。

### 三个新增终端库与 ztty

| 库 | 已核验发布版本 | 源码提交 | 实际 crate SHA-256 |
| --- | --- | --- | --- |
| zpty | 0.2.2 | `66919bc6dcb7757e0437fe955bfa809fb1282b68` | `1d46215c9aaad115aa3637217dcd3d7752d4f511f05ca29729c83ae58c0dd955` |
| zgraphics | 0.2.0 | `fe6357f98cf80fb6cc74739e45e8866ee17706ad` | `cc775cfedeae7a0563bb11e51e25b32e9d4a72757fb2935221ab7bc6f2c88e54` |
| zterm | 0.5.0 | `13d5e2c74571d35cccd920b1204798211b70c79f` | `5cad31f851ec516590643444f339eb6e0a2b7b034b68d190172233e9392364b1` |

注册表 API、索引、真实下载包、VCS 信息和源码载荷逐一匹配。ztty 固定为 `1a2f165983d7abff507c69b54c0c4ed225f49a45`；产品 ELF 来自 `6053a97920c29c852cd92d8b96e35f62cff92ecb`，两次提交的产品源码、Cargo 输入、assets 和五个库 Gitlink 的 Git 对象逐字一致。

既有 `make check` 的原始日志记录 466 项 Rust 检查通过、6 项忽略，其中包含 zgraphics 的 50 项 unit / 1 项 doctest、zterm 的 158 项 unit / 3 项 doctest。原始 GUI/CLI 全套运行是 20/21 阶段、300 项检查通过；Wayland 阶段曾在夹具初始化时超时，执行断言为 0，该失败保留。修正夹具使用的 Python 路径后，用同一组产品 ELF 单独复验 Wayland，65/65 通过且包含全部 19 项必需断言。

这些证据来自 Linux 私有 Xvfb、headless Sway 和 Mesa 软件 EGL。独立审计重算了三份 ELF 和 76 个受 Git 管理的测试/辅助文件的散列，支持复用现有功能验收；不据此声称原生 Windows/macOS、物理 GPU 或性能门禁通过。本轮另备的 canonical-patch 三库 unit gate 两次在资源准入阶段停止，没有进入 Cargo；该状态仍记录为 `resource_not_started`，不与已完成的消费者验收混算。

另有已完成的 registry 发布：`ztty-plugin-api 0.1.0` 的正式来源为 `36b367ffda4cea9b3b3dfbf38dc6375567912323`，下载包为 3,482 B，SHA-256 为 `e00adc5df1eefa237ea1ccd8d837ceecabef1976141b78918901d95cb8e9d4a6`。本轮直接回读 API 和实际 crate 均成功、版本未撤回，包内 `src/lib.rs` 及原始 Cargo 清单与固定 ztty `1a2f165` 逐字一致。原负责人还完成了六个独立 registry 消费者和一个组合消费者，共 21 条 Cargo 命令通过，包含真实 PTY；这不等于动态插件加载或应用正式发布。详见[发布与消费回执](https://github.com/LIghtJUNction/ztty/blob/00d3d418c11f632789dfbb4034db8cefb5e3fd20/docs/reports/plugin-api-registry-20261120/README.md)，本轮来源复核保存于 `docs/evidence/2026-11-20/plugin-api-publication.json`。

ztty 0.5.0 仍是开发候选。既有同条件测量发现性能回退：Unicode 吞吐中位数由约 104.584 降至 21.906 MiB/s，ASCII 由约 305.179 降至 252.769 MiB/s。功能通过不能消除这项性能结果，后续优化仍由原维护方推进并传播给套件。

### SSMCP 应用传播

当前聚合固定的 SSMCP 源码升级为 [ecc450f](https://github.com/LIghtJUNction/ssmcp/commit/ecc450f17012f8120d7d49470ce9599ada65456f)，清单、锁文件与内置 zuse Gitlink 已更新到正式 0.2.1，实际 registry 来源和本地 metadata/release-script 检查有回执。旧 0.2.0 应用构建证据不能充作新的 0.2.1 应用验收。

继续复核发现应用层仍逐 Unicode scalar 调用输入接口，可能先写入 ASCII 前缀，再对后续不可表示字符返回拒绝，从而绕过共享库的整段文本保证。独立候选 [c44c2cf](https://github.com/LIghtJUNction/ssmcp/commit/c44c2cfecb6ba5dae3a63d67a3af08c77eb7b2cc) 已合并 Wayland 修正、高位私有显示分配器和 E0509 修复，改为 X11 一次全文调用，并清除会串用宿主辅助功能总线的继承环境变量；全文拒绝、同一 Computer 恢复和发送后取消的真实夹具已准备。

该候选的 73 项发布脚本测试、格式与 GTK C 语法检查实际通过。2026-11-20 02:04:57 UTC，Clippy 阶段的全机可用内存降至 3,207,434,240 B，低于保留的 3 GiB，守护程序正常停止了自有构建单元；单元峰值约 592 MiB，swap 与 OOM 均为 0。Clippy、应用构建和原生行为验收仍未完成，现有缓存保留。公开回执见 `docs/evidence/2026-11-20/ssmcp-c44-partial-gates.json`，原仓库[同一回执](https://github.com/LIghtJUNction/ssmcp/blob/2e1fee53fde40bac7fc6ace71415eca35e1a3638/docs/reports/shared-cohort-20261120/local-preflight.json)。后续使用独立云工作区构建可行性检查；只有新的实际结果才能推进聚合 Gitlink。协调层的版本、图和解析通过，不代表这个应用组合已经通过运行验收。

发行和安装链仍需继续：SSMCP 新正式应用制品 → oh-my-ztty 的双架构依赖锁与 bundle 验收 → zrc 的真实命令解析和连接行为。当前已安装 suite 的旧 SSMCP 版本不会因为源码 Gitlink 更新而自动改变。zrc 没有直接 Rust ABI 依赖；如果 CLI 契约未改变，不为形式传播强制改版号，但必须验证其实际调用的新 bundle 二进制。

### zcalld 与 GUI/Omarchy/兼容扩展

聚合固定 [c72a1cb9](https://github.com/LIghtJUNction/zcalld/commit/c72a1cb9c6ae5af638ad1100c6ec31ff8ee6f265)，版本为 0.2.0 候选，满足 Omarchy 前端声明的版本下限。旧候选在 Windows 上存在提前 HTTP 拒绝响应被 TCP reset 丢失，以及关闭流程未记录运行中工具取消的问题；原负责人已分别修复 Windows IPC 控制台信号和有界分阶段连接关闭。

新正式候选 [run 44652099557](https://github.com/LIghtJUNction/zcalld/actions/runs/44652099557) 在 Linux x86_64/aarch64、Windows x86_64、macOS x86_64/aarch64 五个平台通过。原失败的两项 Windows 用例明确恢复为 `ok`，MCP 为 13/13。已实际下载 Windows/Linux x86_64 Actions 制品，验证整体摘要、包内二进制和递归源码归档。

三处嵌套来源保持：GUI `5dbc423eedd4d529a38b3e8e3adc3e6355a56b2b`、Omarchy `78282c3c3cfa6e9e65e2cbd654f38a96398c6e03`、compat `008910901a3ef8ac5dd57b748a3210faa463c2b9`。正式发布状态以当前收据为准：候选工作流的 publish/aur 为 skipped，尚未确认 0.2.0 tag/release，原发布方仍在完成其应用验收。未在用户主机安装这些候选下载文件。

### 其他实际纳入的消费者与交付

- **zdistro 0.1.0：**[已正式发布](https://github.com/LIghtJUNction/zdistro/releases/tag/v0.1.0)，四个平台、17 种格式、25 份收据和 9 个附件已核验。wheel/pyz 在新环境中完成从初始化到构建、验证、矩阵生成的实际流程；Deb/Arch 做了解包执行，sdist 做了重建。未据此声称 PyPI、应用商店或用户系统安装已经完成。
- **zmcl：**固定 `3659cf144c69356268f9a185d9ea80eecb50cc7c`，[Linux 开发预览 v0.1.0](https://github.com/LIghtJUNction/zmcl/releases/tag/v0.1.0) 已发布。现有 77 项 Rust、62 项 Python 与 GUI/WM_CLASS/退出后 Java 存活证据按各自真实源码身份保留；不将早先 GUI 二进制验收倒填到后续代码版本。
- **OniMods：**登记的是实际消费 zhex 的 Rust `onim` 工作区；完整游戏模组、游戏内运行及 Workshop 上传属于另外的验收范围。
- **mechrevo-drivers：**登记真实 console 工作区对 zhex/zclap 的依赖。已有硬件和 GUI 证据按实际机型记录，未扩称全部机型、Windows 或用户系统驱动安装成功。
- **LMM / Extore：**当前稳定清单保持已经固定的 LMM core/CLI。Extore 扩展宿主与新的权限/会话绑定仍是独立候选，未把尚未完成的端到端验收写成稳定聚合完成。

## 尚未完成的性能和发行工作

zgpui 与 Zed GPUI 的基准代码、双方固定提交、CPU 锁文件、等价布局/命中任务、release 参数及样本格式已保存。一次实际增量构建被全机可用内存余量保护停止；最近一次启动预检在 2026-11-20 01:32:36 UTC 测得 5.112 GiB，可用门槛是 5.25 GiB，因此未启动新的编译。保留了缓存和原始资源收据，没有输出可比较的性能数字，也没有声称 zgpui 已全面领先。

接续工作按已经发现的真实问题推进：完成 SSMCP 新源码组合和输入行为验收，接入正式应用制品后验证套件及 zrc；由 zcalld 原发布方完成其正式发布；修正 ztty 的实测性能差距；资源允许时恢复同一固定 GPUI 基准。每项都保留实际负责人、固定源码、已有证据、阻碍和下一步，避免重复构建或并行改写同一工作树。

## 日常迭代命令

```sh
python3 scripts/project_z.py sync
python3 scripts/project_z.py check
python3 scripts/project_z.py impact --repositories zuse
python3 scripts/project_z.py resolve --all
python3 scripts/project_z.py run --affected zuse -- test --lib
```

`impact` 返回需要协调的范围；它不会自动替代非 Rust 安装、GUI、设备和业务行为验收。消费者完成必要版本、锁文件、源码和适配后，应及时提交推送，再更新聚合 Gitlink 与清单。日常开发以本机检查验收，不触发或等待例行 CI、CodeQL、远程审查；正式构建、签名、制品发布与部署流程继续保留。

## 本次固定仓库清单

| 仓库 | 角色 | 固定提交 |
| --- | --- | --- |
| OniMods | application | [f0819fa207c5](https://github.com/LIghtJUNction/OniMods/commit/f0819fa207c52e98aa7dff8084620557669af7ea) |
| lmm-api-source | application | [4571b477d490](https://github.com/TokenNotIncluded/lmm-api-source/commit/4571b477d490b86d477f44f1c6768cc5f3b409d1) |
| mechrevo-drivers | application | [4599a3825dac](https://github.com/LIghtJUNction/mechrevo-drivers/commit/4599a3825dac3c85efeeb490cb4eebe1c1b6dff0) |
| oh-my-ztty | suite | [7b69b751772a](https://github.com/LIghtJUNction/oh-my-ztty/commit/7b69b751772a839f090e408228d94f810fd96d1e) |
| ssmcp | application | [ecc450f17012](https://github.com/LIghtJUNction/ssmcp/commit/ecc450f17012f8120d7d49470ce9599ada65456f) |
| z58 | library | [c70d50eafb3f](https://github.com/LIghtJUNction/z58/commit/c70d50eafb3f50eb9a709861f9e1ed2c2fa48dc3) |
| z64 | library | [7e9cff67beae](https://github.com/LIghtJUNction/z64/commit/7e9cff67beae2c484f8b9749b83ae24a1d0e1bbd) |
| zcall | library | [8fb84b812b80](https://github.com/LIghtJUNction/zcall/commit/8fb84b812b8025e34399b28e27242605d68ea345) |
| zcall-gui | application | [5dbc423eedd4](https://github.com/LIghtJUNction/zcall-gui/commit/5dbc423eedd4d529a38b3e8e3adc3e6355a56b2b) |
| zcall-omarchy | application | [78282c3c3cfa](https://github.com/LIghtJUNction/zcall-omarchy/commit/78282c3c3cfa6e9e65e2cbd654f38a96398c6e03) |
| zcalld | application | [c72a1cb9c6ae](https://github.com/LIghtJUNction/zcalld/commit/c72a1cb9c6ae5af638ad1100c6ec31ff8ee6f265) |
| zcalld-compat | extension | [008910901a3e](https://github.com/LIghtJUNction/zcalld-compat/commit/008910901a3ef8ac5dd57b748a3210faa463c2b9) |
| zclap | library | [4d87f3ae3743](https://github.com/LIghtJUNction/zclap/commit/4d87f3ae3743e81509d5ac5500909955667c860f) |
| zclick | bindings | [530e2f347d29](https://github.com/LIghtJUNction/zclick/commit/530e2f347d2950605ee579a396d5760ebad034bd) |
| zconv | library | [0af1f7eb0766](https://github.com/LIghtJUNction/zconv/commit/0af1f7eb0766ff0ce9db5cee7c6184eff511a8c1) |
| zdistro | application | [6a54a137fc69](https://github.com/LIghtJUNction/zdistro/commit/6a54a137fc697d372b54ef85105315f2ce522b3d) |
| zdot | application | [e6b5feb98b05](https://github.com/LIghtJUNction/zdot/commit/e6b5feb98b05c59e0986624c0742dfe4a9187a2a) |
| zdwire | library | [c046e3182b0a](https://github.com/LIghtJUNction/zdwire/commit/c046e3182b0adf15d43500400a427b7dd7389525) |
| zfetch | application | [f19b27867620](https://github.com/LIghtJUNction/zfetch/commit/f19b278676206d76626dd01e4b89f7ad9ce9318f) |
| zgpui | library | [1d796d1fc638](https://github.com/LIghtJUNction/zgpui/commit/1d796d1fc63808dc099ed7b10c92e75835ae2814) |
| zgraphics | library | [fe6357f98cf8](https://github.com/LIghtJUNction/zgraphics/commit/fe6357f98cf80fb6cc74739e45e8866ee17706ad) |
| zharness | library | [e3580c01c725](https://github.com/LIghtJUNction/zharness/commit/e3580c01c7252da090d04e59b59762bc561777d1) |
| zhex | library | [09dfaa0adee6](https://github.com/LIghtJUNction/zhex/commit/09dfaa0adee628d0714e2f9e96921555e619b2f6) |
| zinput | library | [37617313dd7a](https://github.com/LIghtJUNction/zinput/commit/37617313dd7aaabcca9dd567344a76c4cbe03907) |
| zldap | library | [d90e02d2ed10](https://github.com/LIghtJUNction/zldap/commit/d90e02d2ed107c6ede7ad4a56bfe329c82eb4fe8) |
| zmcl | application | [3659cf144c69](https://github.com/LIghtJUNction/zmcl/commit/3659cf144c69356268f9a185d9ea80eecb50cc7c) |
| zmcpio | library | [bc89d7fa3b02](https://github.com/LIghtJUNction/zmcpio/commit/bc89d7fa3b0249b3a9037748e2113b31615e8c89) |
| zmime | library | [2d5930955ed8](https://github.com/LIghtJUNction/zmime/commit/2d5930955ed8086e12a6ab6cd3dd5caa837e1a42) |
| zplugin | library | [00d566eedcff](https://github.com/LIghtJUNction/zplugin/commit/00d566eedcff7b2932e90b9dfeb44910c783d305) |
| zpty | library | [66919bc6dcb7](https://github.com/LIghtJUNction/zpty/commit/66919bc6dcb7757e0437fe955bfa809fb1282b68) |
| zrc | configuration | [ef8bd9571e20](https://github.com/LIghtJUNction/zrc/commit/ef8bd9571e206c8086e38b9dcbdc760a466b5133) |
| zscan | library | [c000a84c748d](https://github.com/LIghtJUNction/zscan/commit/c000a84c748d8e090ff662b2aef3858aa4880b09) |
| zshard | shell | [1cfa1a1eb761](https://github.com/LIghtJUNction/zshard/commit/1cfa1a1eb761d14e2ccfd5381282b6ccd1491cff) |
| zsyn | library | [b1cb68fd6110](https://github.com/LIghtJUNction/zsyn/commit/b1cb68fd61101e98c504a90e47b74e2bccdd0165) |
| zsys | library | [808fcfdb7358](https://github.com/LIghtJUNction/zsys/commit/808fcfdb73584ca7ca122e20b76f0209f56ab0f7) |
| zterm | library | [13d5e2c74571](https://github.com/LIghtJUNction/zterm/commit/13d5e2c74571d35cccd920b1204798211b70c79f) |
| ztty | application | [1a2f165983d7](https://github.com/LIghtJUNction/ztty/commit/1a2f165983d7abff507c69b54c0c4ed225f49a45) |
| ztuio | library | [9c632b30f7e2](https://github.com/LIghtJUNction/ztuio/commit/9c632b30f7e2c2fd51a19b4bc5d90d529041ae7e) |
| ztype | application | [037de9972e16](https://github.com/LIghtJUNction/ztype/commit/037de9972e169942ca6258d6aee6ba53711204f6) |
| zui | library | [5e37fcfb791e](https://github.com/LIghtJUNction/zui/commit/5e37fcfb791eec9ac523fc19373e95d0a513112f) |
| zuse | application | [d930769005d3](https://github.com/LIghtJUNction/zuse/commit/d930769005d307c42639e8abedc81ab039427e40) |
| zvte | library | [b4e50a5cde47](https://github.com/LIghtJUNction/zvte/commit/b4e50a5cde476fb5303060f3ecbc9200ccea5cc0) |

生成清单与上述固定来源绑定；后续应用补丁、正式发行和性能结果应以新增提交更新记录，不能覆盖本轮失败原始证据或将未执行项改成成功。
