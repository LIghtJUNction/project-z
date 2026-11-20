# Project Z：共享库、应用与安装套件协同维护

更新时间：2026-11-20T04:19:43.438027+00:00。本报告对应固定源码快照，仓库与提交清单见文末；发布制品、应用运行验收和用户机器上的安装状态分别记录。

协调层已通过 80 项真实回归，并完成 36 个 Rust 仓库的全图依赖解析。首轮统一入口已由 [PR #3](https://github.com/LIghtJUNction/project-z/pull/3) 合入 main。后续消费者增量按精确提交分段验证；旧失败和旧来源的验收保留原始身份。ztty 0.5.0 已正式发布，SSMCP 新输入、私有桌面和账户 relay 修复已完成实际原生门禁，套件已验收消费正式 ztty 的候选，zgpui/GPUI 首轮 CPU 对照已公开。zcalld 的真实生成请求仍存在接管阻断，套件中的新 SSMCP 正式制品传播也须另行验收。

## 已完成的协调层

Project Z 当前统一固定 **42 个仓库、60 个 Cargo package**。首轮相对先前 29 仓库协调快照，新增登记 zgpui、zinput、ztype、zrc、zfetch、zdistro、zmcl、zpty、zgraphics、zterm、OniMods、zcall-omarchy、mechrevo-drivers，共 13 个仓库。首轮 PR #3 相对其 main 基线 `9d72d19` 净增加 15 个仓库（另包含先前接入的 lmm-api-source、zcall-gui），并将旧 ztui 名称迁移到 ztuio；两种计数使用不同的比较基线。接续 PR #4 保持 42 仓库、60 包，更新已验收的消费者来源并补充实际发行和应用证据。

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
| 协调器本地回归 | 80/80，通过，无跳过 | 真实 Git/Cargo fixture、版本规则、来源、工作区隔离和锁恢复；协调器源码未再次改动，没有为文档更新重复运行 |
| 统一清单 | 42 仓库、60 包 | Cargo 包关系与额外运行时、安装、分发关系分别记录 |
| 三仓增量全量 Cargo 解析 | 36 个 Rust 仓库、37 个 workspace manifest 全部通过 | OniMods 14d、zterm a207、ztty 9f 的真实解析；94 个源码工作树干净 |
| 原三仓全量解析的锁与配置恢复 | 125 个对象的字节、权限、存在性均恢复 | 初次 256 MiB 资源保护停止留下的临时文件也已按原始 Git 对象恢复；512 MiB 预算的完整解析随后通过 |
| ztty 最终正式源增量 | c4 的 sync/check 实际通过 | Cargo、lock、配置、5 个依赖 gitlink 不变；没有把 9f 的全图解析改称 c4 的新运行 |
| 既有核心库检查 | 20 个库仓库检查退出码为 0 | 不是 20 个单测，也不是全部应用验收 |
| ztty 新功能门禁 | 9855 来源的 472 项 Rust 通过、6 项忽略，32 项真实像素专项通过 | 后续 c4 只增加文档证据；旧 9f 的 365 项 GUI 另存历史回执 |
| ztype 消费 zuse 0.2.1 | 构建、Clippy 与 11 项原生验收通过 | 固定 037de997，实际 GTK 接收 |
| SSMCP 新生产源 | 785 的 fmt、Clippy、test-artifacts、产品与插件构建、私有环境用例通过；原机 2 个 lib 用例、35 项私有桌面 MCP 以及 47 项账户 relay 专项目通过 | 同源实际 ELF，默认生产子进程环境，完整退出清理；此前 c44 的 125 项 MCP、12 项 GTK 证据保持来源不变 |
| zcalld / compat 正式发布 | core 0.2.1、compat 0.1.4 已发布；已做完整成对源码范围审计 | core 五个平台有原生 gate；compat 自身工作流的跨编译与 Linux 原生执行分别标注；真实服务接管尚未完成 |
| 套件终端消费 | 42 项既有本地测试、双架构各 84 文件核验、x86_64 临时安装与 4 项 GUI 通过；隔离 sync/check 通过 | 0fdc 候选，最终 99 个干净源码、138 个锁/配置保持；仍含旧 SSMCP，没有用户安装升级 |
| zgpui / GPUI CPU 对照 | 7 轮配对、112 万逐操作样本，原始数据已公开 | 新建和调整尺寸较快，较大保留布局仍有差距；不是完整桌面框架或 GPU 胜负 |

全量解析、临时来源覆盖和协调器执行夹具使用独立验证副本。根目录的 inventory、sync 与 check 会使用 `cargo metadata --no-deps` 生成和核对清单，因此不能把它们统称为“所有 Cargo 操作都在副本中”。原机 gate 使用有界 systemd/cgroup；云端解析和构建使用进程组资源采样守护，不能把后者写成内核 cgroup 限额。

三仓增量的完整解析实际用时 101.543 秒，受控进程组峰值 278,413,312 B，全机可用内存最低 8,618,934,272 B。初次 256 MiB 限额停止属于资源准入/守护结果，没有 OOM，也不是依赖解析错误。完整回执见[三仓解析](../evidence/2026-11-20/three-source-delta-resolution.json)；最终 ztty 的独立来源与生成检查见[正式源增量](../evidence/2026-11-20/ztty-v050-final-source.json)。

三仓更新前后整张依赖图的节点和边保持一致：226 条全部直接包边、84 条内部包边、包含声明关系的 56 条仓库边，新增和删除均为 0。因此既有影响范围可复用；这一等价性只覆盖依赖图，不覆盖应用行为、正式发行或性能。zcalld/compat 成对更新后已实际完成 sync/check 与 `resolve zcalld`，随后 SSMCP 更新后已完成 sync/check 与 `resolve ssmcp`；两次各解析 1 个受影响工作区，没有重复 36 仓库全量解析。两次均恢复全部 128 个锁/配置对象，94 个源码工作树保持干净；比原三仓阶段多出的 3 项是 ztty 已跟踪的历史文档 Cargo.lock，没有新增工作区。最终图仍为 226/84/56，规范化 SHA-256 为 `b467cda8ef50f8d6ac9555d00ac5ca69d14eb9b28953201fb9f27527efa4446f`。详见[zcalld 成对解析](../evidence/2026-11-20/zcalld-paired-source-validation.json)和[SSMCP 独立增量](../evidence/2026-11-20/ssmcp-785-source-validation.json)。

### zuse 0.2.1 与 ztype

zuse 0.2.1 的正式发布源码为 `d930769005d307c42639e8abedc81ab039427e40`，注册表实际下载校验和为 `8da9a00ef8468d196234a99cb4d7f47991d9fb1ef704f67da2ce63d46395ea04`。正式五平台发布及 Linux 发布包的 17 项 GTK、12 项 MCP、5 项 PTY、11 项 USB C ABI 验收有独立回执。

ztype 已固定 `zuse-computer = "=0.2.1"` 与真实 registry lock，功能和证据提交为 [037de997](https://github.com/LIghtJUNction/ztype/commit/037de9972e169942ca6258d6aee6ba53711204f6)。Clippy、应用和 kana 动态库构建，以及 11 项真实 GTK 接收验收通过。输入界面继续保持两行紧凑候选条；当前是基于小型起步词表及多种引擎的组合输入应用，包含假名、Unicode/原文、自定义表、原生插件与显式目标送达。完整整句预测和系统级 IME 前端仍待实现。

zuse [正式发布](https://github.com/LIghtJUNction/zuse/releases/tag/v0.2.1)；[发布回执](https://github.com/LIghtJUNction/zuse/blob/889e4c4c17c903159fb4616dd6ee565001919767/docs/evidence/release-0.2.1.json)；[ztype 中文验收报告](https://github.com/LIghtJUNction/ztype/blob/91edc97aab1bea18f15f56e1ee2ec0651cc85916/docs/delivery-2026-11-20.zh-CN.md)。

### 三个新增终端库与 ztty

| 库 | 已核验发布版本 | 源码提交 | 实际 crate SHA-256 |
| --- | --- | --- | --- |
| zpty | 0.2.2 | `66919bc6dcb7757e0437fe955bfa809fb1282b68` | `1d46215c9aaad115aa3637217dcd3d7752d4f511f05ca29729c83ae58c0dd955` |
| zgraphics | 0.2.0 | `fe6357f98cf80fb6cc74739e45e8866ee17706ad` | `cc775cfedeae7a0563bb11e51e25b32e9d4a72757fb2935221ab7bc6f2c88e54` |
| zterm | 0.5.1 | `a2074bac4c030cfd7c0b2514c852a89dcf54648f` | `fc48bcaf9892a77d17ab235316448c3e235b0dccd00e5963b542586585c26c91` |

注册表 API、索引、真实下载包、VCS 信息和源码载荷逐一匹配。zterm 0.5.1 的 37 个包文件与发布来源匹配，三个操作系统的正式检查分别有 164 项 unit 和 3 项 doc 结果；不把另外的实验分支算入该发布。详见[zterm 传播审计](../evidence/2026-11-20/zterm-0.5.1-propagation-audit.json)。

ztty [v0.5.0 正式发行](https://github.com/LIghtJUNction/ztty/releases/tag/v0.5.0)已于 2026-11-20 03:41:44 UTC 公开，固定源码为 `c4f8f48c9598284a589e609f25242b49ceabfea8`。正式工作流 [44668398577](https://github.com/LIghtJUNction/ztty/actions/runs/44668398577) 的六个平台原生构建和 verify 全部成功，发行包含 47 个附件。聚合固定正式 tag 的源码，后续只添加验收文档的 main 提交不会被误当作新的产品版本。根协调者还实际下载了 Linux x86_64/aarch64 两个正式压缩包、各自校验文件与构建 JSON 共 8 个资产，确认 GitHub digest、配套 SHA-256、构建记录的 c4 来源/架构/run 和真实包内容一致。x86_64 压缩包为 584,351 B，aarch64 为 552,407 B；这一步是下载与来源核对，没有执行或安装二进制，详见[Linux 正式资产核验](../evidence/2026-11-20/ztty-v050-linux-assets.json)。

9f 到 c4 的完整范围有 8 个提交、321 个文件；GitHub compare 的文件列表不完整，因此审计使用完整树和真实 Git 差异。唯一生产变化在 `src/x11/gpu.rs`：当 Auto 模式且用户显式设置 `LIBGL_ALWAYS_SOFTWARE=1` 时，在初始化 EGL/llvmpipe 前选择软件路径；明确选择 GPU 时仍走 GPU。Cargo 输入、lock、配置和五个依赖 gitlink 逐字不变。

新生产提交 `9855da563f3038adee2fa88e1e24e20eafb77010` 已有 472 项 Rust 通过、6 项忽略，32 项新像素检查通过，其中 Auto/software 24 项、显式 GPU/llvmpipe 8 项，并完成三阶段整机测试。原外层 Python `KeyError` 失败保留；已通过的 Auto 未重跑，续跑的是此前未启动的 GPU 部分。9855 到 c4 只有文档/证据变化，因此新产品证据按这个可审计范围复用。旧 9f 的 21 阶段、365 项 GUI 仍是旧来源的独立验收，不倒填为 c4 重新执行。

新结果仍保留性能限制：10 窗口场景相对既有基线存在约 21.82% 回退，不能由功能通过或正式发布推断全部性能问题消失。新来源的完整[主机验收与性能报告](https://github.com/LIghtJUNction/ztty/blob/db3f49ae77cfa14e6c91145a5bffe306a528a57c/docs/reports/host-9855da5-20261120/README.md)与本仓的[来源增量审计](../evidence/2026-11-20/ztty-v050-final-source.json)记录了这些边界。

`ztty-plugin-api 0.1.0` 的 registry 来源保持 `36b367ffda4cea9b3b3dfbf38dc6375567912323`，包大小 3,482 B，SHA-256 为 `e00adc5df1eefa237ea1ccd8d837ceecabef1976141b78918901d95cb8e9d4a6`。新 ztty 应用 tag 不会改变已经发布的 API crate 的 VCS 身份。此前六个独立 registry 消费者与一个组合消费者共 21 条 Cargo 命令的结果保留在[原始报告](https://github.com/LIghtJUNction/ztty/blob/00d3d418c11f632789dfbb4034db8cefb5e3fd20/docs/reports/plugin-api-registry-20261120/README.md)。

### SSMCP 应用传播

共享库修复只有被应用以正确方式调用才有效。原聚合源码 ecc450f 已固定正式 zuse 0.2.1，但应用仍逐个 Unicode scalar 调用输入接口，可能先写入 ASCII 前缀，再对后续字符拒绝。候选 c44 改为 X11 一次提交全文，并整合 Wayland 修正、高位私有显示分配器和所有权修复；它还清除了可能串用宿主辅助功能总线的继承地址。完整 ecc→785 范围也包含 `src/client.rs` 的修复：Account transport 结束时保留最终授权拒绝，包括显式 `--allow` 但没有 token 的路径；不能把全部生产变化概括成只有显示和文本输入。

c44 的云端 Clippy、测试产物、产品和插件构建实际完成。云端的 44 项 computer 用例、4 项 PTY 通过；两个 Unix socket 用例受沙箱权限阻挡，随后用同一冻结 ELF 在开发机分别通过。原机另已完成 125 项 MCP、客户端与 daemon 各 6 项 GTK，以及私有桌面的部分检查。这些数字各自保留固定来源和执行范围，不合并成一个不存在的“全套重跑”。[c44 云端回执](../evidence/2026-11-20/ssmcp-c44-cloud-validation.json)仍保留原本的部分环境限制。

实际私有桌面测试又暴露两个生命周期问题：隔离会话中的 AT-SPI Registry 无法通过默认 broker 激活，以及退出后残留的 GVFS FUSE 挂载阻止临时状态目录删除。最终生产源码 [785e6b0](https://github.com/LIghtJUNction/ssmcp/commit/785e6b00440b048d00d9da626a33defa99108afe)只在私有子进程的 `Command` 环境设置 `ATSPI_DBUS_IMPLEMENTATION=dbus-daemon` 与 `GVFS_DISABLE_FUSE=1`。它保留 GIO VFS 功能和既有显示/鉴权边界，没有修改父进程环境或宿主服务；[GIO 官方说明](https://docs.gtk.org/gio/overview.html)解释了关闭 FUSE 与关闭整个 VFS 的区别。

新 785 源码的 fmt、Clippy、test-artifacts、产品/插件和精确私有环境测试均通过。2026-11-20 03:54:58–03:55:05 UTC，实际原机运行 2 个受影响 lib 用例和 35 项私有桌面 MCP 检查，全数通过，覆盖同一 Computer 的两种身份错误零输入拒绝、Unicode 恢复、截图、宿主不变和最终应用/Xserver/状态目录完整清理。测试入口未注入诊断用 daemon 偏好，反而让外层使用 broker 与 GVFS；通过来自生产子进程自身设置。

此外，完整源码审查确认已有 125 项 MCP 并未精确覆盖 `src/client.rs` 的无 token `--allow` 最终授权拒绝路径。因此用同一冻结 785 ELF 在两个本地合成网关和隔离凭据目录运行必要的账户 relay 专项目，2026-11-20 04:08:02–04:08:22 UTC 的 47 项检查全部通过，包括活动撤销、Ready 后立即撤销不重试、401/403 停止 watchdog、真实 PTY 和清理。该测试没有使用真实用户凭据、远程模型或 SSH。最初 768 MiB 预算未满足入场门槛，未启动测试；根据该专项目不含 GUI/Xvfb/libtest router 的实际范围，把任务上限收紧为 512 MiB、高水位 384 MiB，保留 3 GiB 全机底线和 256 MiB 缓冲后才另行准入。实际峰值 92,499,968 B，swap/OOM/high/max 为 0，首次未启动记录保留。详见[785 应用与原生增量回执](../evidence/2026-11-20/ssmcp-785-application-validation.json)。

此前私有桌面 gate 的 cgroup 峰值为 494,096,384 B，全机可用内存最低 4,313,755,648 B，swap/OOM/high/max 事件为 0；`sock_throttled` 为 15，原值保留。退出码 0，cgroup 为空、unit inactive，源码与全部资产未变。旧环境诊断、原始清理失败和资源未启动回执均保留。

剩余传播链为：唯一正式发行者产出与该源码一致的新 SSMCP 制品，oh-my-ztty 更新双架构依赖锁并实际验证 bundle，再验证 zrc 的真实命令解析路径和连接行为。旧发行候选与新组合曾同标 0.10.14，但依赖/源码不同，不能覆盖已存在 tag 或借用旧资产。现有唯一发布者的 [v0.10.15 草稿 PR #109](https://github.com/LIghtJUNction/ssmcp/pull/109) 在 04:13:56 UTC 的 head e30a149 仍缺少本轮五个文件的最终环境/GTK 增量；已为该候选建立独立的 [draft PR #110](https://github.com/LIghtJUNction/ssmcp/pull/110)，固定补丁 `bc0ef8e0b24f7e0e58271046743c89334041ec51`，五个文件的 Git blob 已逐一回读；三份 Python 的 AST/编译和 TOML 等价检查通过，保留其 0.10.15、锁、四个 gitlink、交互接线和有效平台修正。该组合源尚未编译或实际运行，785 的 ELF 验收不能改写为它已经通过。原唯一发布者的交接尚未确认送达，具体补丁与验收条件已经公开。套件和用户安装状态必须由新制品的实测回执决定；zrc 没有直接 Rust ABI 依赖，在 CLI 契约不变时不为形式传播强制改版号。

### oh-my-ztty 的终端消费候选

套件来源从 `7b69b751772a839f090e408228d94f810fd96d1e` 更新为 `0fdc87873c53e7c87d18952f83a7b94fc4149de5`，完整范围为 4 个提交、34 个变化文件。启动器唯一生产代码变化是让 `--backend` 与 `--text-plugin` 各消费一个参数值；同时把 ztty gitlink 和双架构发行锁固定到正式 c4。真实产品验收来源为 `5a99afc170dc51455beb1491e04ab76cf18f4564`，其后到 0fdc 只增加文档证据。

14 份公开证据（含截图）的声明 SHA-256、Git blob 和真实检出文件逐字匹配。原负责人完成 42 项本地测试、双架构候选包各 84 个清单文件校验、x86_64 临时安装生命周期和 4 项真实图形检查。实际 `--backend x11` 路径在私有 `SHELL=/bin/sh` 下仍启动预设 zsh；软件渲染窗口、输入、组件版本和最终清理有原始回执。ARM64 只验证组装、ELF 和清单，没有执行验收；`--text-plugin` 只验证 argv，未执行插件；未测试 Wayland GUI。详见[上游候选报告](https://github.com/LIghtJUNction/oh-my-ztty/blob/0fdc87873c53e7c87d18952f83a7b94fc4149de5/docs/reports/ztty-0.5.0-consumer-20261120.md)和[独立源码/制品/聚合审计](../evidence/2026-11-20/suite-ztty-050-consumer-validation.json)。

这仍是未正式发行的套件候选，VERSION 保持 0.2.1，没有覆盖已有正式附件、用户安装或默认终端。SSMCP 仍固定 v0.10.10 / `52a531a59e9ec9236a76eafc0f4f068799e44b15`，图形回执实际读取的也是这个旧版本。AI 测试使用假 provider 和打印 argv 的假 SSMCP；真实 smoke/GUI 仅覆盖本地 context、help 和 version，明确没有真实 AI 连接。zrc 根据 PATH 启动 `ssmcp`，套件 shell 优先 bundled bin，因此新 SSMCP 的正式资产、路径和真实连接仍需独立闭环。

套件增量实际 sync/check 通过，没有重复全图解析或构建。嵌套 ztty 新增五个库源码后，最终递归源码为 **99 个干净工作树**，验收阶段的 **138 个锁/配置对象**在字节、权限、存在性上均保持一致，92 个原有无关来源 HEAD 未改变。此前三仓、c4、zcalld/SSMCP 的 94/125/128 数字仍按各自历史范围保留。最终 package、版本及依赖边不变，仅更新 suite 的来源提交；catalog SHA-256 为 `812933e1fb929cbaf1fd7684fcf61c7f53c2ed4c62edcbf9d20f21a5b15f2f75`。

源码准备第一次遇到 Git 隐式获取对象的线程创建失败，原失败保留。将单线程选项应用到每个 Git 调用后，仅续接未完成的嵌套检出；没有提高资源预算或重建已完成源码。最终生成检查的采样峰值低于 50 MB，全机可用内存最低仍超过 9.3 GB。

### zcalld 与 GUI/Omarchy/兼容扩展

core [v0.2.1](https://github.com/LIghtJUNction/zcalld/releases/tag/v0.2.1) 固定 `b853e264eced9fbd25120d261eb188a3a8e3b1df`；compat [v0.1.4](https://github.com/LIghtJUNction/zcalld-compat/releases/tag/v0.1.4) 固定 `7c782e9a6f431c7112112c04940c015adf2d76df`。完整审计覆盖 core 的 c72→b853 四个提交、23 个文件，以及 compat 的 008→7c 四个提交、24 个文件。外部 Rust/Go 依赖没有改变，core 八个工作区包同步到 0.2.1，typed plugin 的六个接口仍为版本 1；core 内嵌 compat 与独立扩展必须成对更新。

正式 core 工作流 [44662882884](https://github.com/LIghtJUNction/zcalld/actions/runs/44662882884) 包含 Linux x86_64/aarch64、Windows x86_64、macOS x86_64/aarch64 的原生检查，均包含已固定兼容扩展的隐私/MCP helper 验收。compat 自身的五目标构建都由 Ubuntu 执行，只有 Linux x86_64 的 `make check` 属于该工作流内的原生执行，不能把它写成五个平台的原生运行。

根协调者实际下载并校验正式源码归档、Linux x86_64 和 Windows x86_64 制品以及校验表；递归比较源码包的 819 个 Git blob、可执行/符号链接模式和 8 个 gitlink，与 9 棵精确 GitHub 树一致，没有缺失或不匹配。二进制只做下载、包内散列和来源核对，本次下载没有被执行或安装，详见[正式资产与递归源码核验](../evidence/2026-11-20/zcalld-021-formal-assets.json)及[完整成对源审计](../evidence/2026-11-20/zcalld-021-compat-014-audit.json)。GUI、Omarchy 前端固定提交保持不变。

用户主机的安装由原负责人完成；根协调者在 03:32 UTC 读到 `zcalld 0.2.1-1` 和 `zcalld-compat 0.1.4-1` 已安装，但 zcalld 服务 inactive/dead，Magpie 仍在运行。原负责人的第二次切换曾在 03:04 激活并通过模型列表、TCP/Unix、MCP、配置身份和隐私保留验收；随后两条真实 Responses 请求均以 `502 invalid provider response metadata` 失败，因此 03:09 已按冻结恢复脚本回滚。现有 17 项 cutover 测试是事务/故障夹具，不能代替真实主机的生成成功。

因此，正式发布与成对源码采纳已经有依据，日常服务替换仍被真实生成失败阻断。后续定位和修复由唯一原负责人接续，必须通过新的正式补丁和实际生成验收才能重新接管。账号、请求历史和配置原文不会进入公共报告。

### 其他实际纳入的消费者与交付

- **zdistro 0.1.0：**[已正式发布](https://github.com/LIghtJUNction/zdistro/releases/tag/v0.1.0)，四个平台、17 种格式、25 份收据和 9 个附件已核验。wheel/pyz 在新环境中完成从初始化到构建、验证、矩阵生成的实际流程；Deb/Arch 做了解包执行，sdist 做了重建。未据此声称 PyPI、应用商店或用户系统安装已经完成。
- **zmcl：**固定 `3659cf144c69356268f9a185d9ea80eecb50cc7c`，[Linux 开发预览 v0.1.0](https://github.com/LIghtJUNction/zmcl/releases/tag/v0.1.0) 已发布。现有 77 项 Rust、62 项 Python 与 GUI/WM_CLASS/退出后 Java 存活证据按各自真实源码身份保留；不将早先 GUI 二进制验收倒填到后续代码版本。
- **OniMods：**从 f081 升级到 `14dba75a5752c3142039a8660ce37cdf57d7082a` 的完整来源审计已通过。71 项 Rust、2,391 项 JLib 断言（含 36 项新增）、两组 Python 3/13 项及四个 release 构建有实际回执；57 个清单不变。游戏内项目仍有 5 项部分验证、6 项未运行，不能写成全游戏或 Workshop 上传成功。聚合跟踪的是实际消费 zhex 的 Rust `onim` 工作区，详见[增量审计](../evidence/2026-11-20/onimods-f081-to-14d-acceptance.json)。
- **mechrevo-drivers：**登记真实 console 工作区对 zhex/zclap 的依赖。已有硬件和 GUI 证据按实际机型记录，未扩称全部机型、Windows 或用户系统驱动安装成功。
- **LMM / Extore：**当前稳定清单保持已经固定的 LMM core/CLI。Extore 扩展宿主与新的权限/会话绑定仍是独立候选，未把尚未完成的端到端验收写成稳定聚合完成。

## zgpui 与 GPUI 的实际对照

首轮 CPU 基准已完成，尚未达到“全面超越”。固定 zgpui `1d796d1fc63808dc099ed7b10c92e75835ae2814` 和 GPUI/Zed `a246423a3b24a08e0d0c8574eab3a9de422747e0`，统一 Rust 1.100、opt-level 3、thin LTO、一个 codegen unit。GPUI 的唯一上游补丁只是导出已有布局引擎，没有改变算法。两份可执行程序各通过 20 组独立几何预期与每组 2,048 次命中查询；夹具最初的根宽和 DPI 失败保持原件，修正没有改预期结果或两库算法。

2026-11-20 03:35:50–03:36:16 UTC，在同一云端 CPU 0、nice 19、预先固定随机种子下完成 7 轮配对、224 个计时进程和 1,120,000 个逐操作样本；另用 32 个进程测量分配。预热、顺序和样本数在测量前固定，没有删除长尾或为结果重新选核。

下表先计算每轮 GPUI/zgpui 的操作均值之比，再取 7 轮比值的几何平均；95% 区间按进程轮次 bootstrap。大于 1 表示该工作负载上 zgpui 更快；它不是综合评分，也不是 p50 比值。

| 总节点数 | 新建布局 | 调整尺寸 | 保留布局 | 几何查询 |
| ---: | ---: | ---: | ---: | ---: |
| 3 | 14.00 | 10.63 | 1.68 | 0.89，区间跨 1 |
| 21 | 8.66 | 6.31 | 1.10，区间跨 1 | 0.78 |
| 73 | 13.20 | 5.71 | 0.79 | 0.78，区间跨 1 |
| 241 | 8.41 | 4.97 | 0.81 | 0.89 |

241 节点场景的新建布局 p50 为 zgpui 19.341 µs、GPUI 170.802 µs；调整尺寸分别为 13.076 µs 和 62.770 µs；保留布局分别为 13.088 µs 和 10.866 µs。最后一项方向相反，配对均值比为 0.805，95% 区间 0.760–0.854。GPUI 每次仍清除和重建 absolute bounds，但保留 Taffy 求解缓存；zgpui 当前创建新布局快照。这不是 GPUI 零成本返回全部矩形，而是现有缓存与重复工作量的差别。

分配也不能只看一个数字。最大场景新建布局，zgpui 每次 243 次分配、申请 23,293 B，GPUI 每次 161 次、申请 1,022,700 B；zgpui 的申请字节较少，但次数较多。保留布局中分别为 1 次/5,784 B 与 16 次/1,920 B。分配流量不等于常驻内存。

测量有明确限制：69/224 个批次线程 CPU 计数差为 0，表示本轮该计数未分辨出增量，不能称作零 CPU；进程 RSS 从 11,904 到 124,296 KiB，各组中位数虽同为 67,304 KiB，原始值随轮次上升；父收集器保留样本，采集和进程启动效应尚未隔离，不能代表两库独占内存相同。整个 CPU 观察区间有 13.80% steal ticks，区间结果不能证明无云端干扰。完整[中文报告](https://github.com/LIghtJUNction/zgpui/blob/4b6d628452f62dcbdb955b98183dfe134d173ad1/benchmarks/gpui-comparison/reports/20261120-cloud-cpu/FINDINGS.zh-CN.md)、[全部表格](https://github.com/LIghtJUNction/zgpui/blob/4b6d628452f62dcbdb955b98183dfe134d173ad1/benchmarks/gpui-comparison/reports/20261120-cloud-cpu/report.md)和原始数据包已公开。

几何查询使用 GPUI Bounds 的线性宿主适配器，不是 GPUI 的完整事件分发。当前 canonical 图中，zgpui 唯一直接 Cargo 消费者是 zterm；zterm 重导出类型和 Scene，并未调用这里测量的 `layout`/`button_at`。ztty 生产路径有自己的场景与几何缓存、命中适配，因此这些微基准差距不能直接写成 ztty 每帧或输入延迟差距。下一轮优化应先剖析真实保留布局的重复工作，再在独立提交上复用相同预期、场景和参数。当前没有可传播的新 zgpui 性能补丁。双方冻结源码的具体函数、ztty 的刷新/命中路径和有界优化方案见[生产路径后续分析](https://github.com/LIghtJUNction/zgpui/blob/ea157f96583bc3cd1e005524093327dc9e6d67e2/benchmarks/gpui-comparison/reports/20261120-cloud-cpu/FOLLOWUP.zh-CN.md)。

原生应用启动、实际 GPU 帧、文本塑形、字形像素、完整可访问性和 Windows/macOS 性能尚不在本次测量范围。原始包有 519 个原始输出与记录文件，压缩包 SHA-256 为 `400abff1703dd370a8479af47a4a696fe1c797437a5ac9fe38575c9849b2db53`；[Drive 原始数据](https://drive.google.com/file/d/1FUn4bqoe7bk1w0YjawIjxMPrWhW5Ln8i/view)和[中文报告副本](https://docs.google.com/document/d/1H0aEi0_vhQ4RM9jcWDEyG7fLga7nQx7I/edit)已经回读核验。

## 继续维护的明确边界

| 工作 | 已完成部分 | 仍需完成的实际结果 |
| --- | --- | --- |
| SSMCP → suite → zrc | 新生产源构建、原生输入与完整私有桌面清理 | 同源正式应用资产、双架构 bundle、新安装二进制路径与真实连接 |
| zcalld 真实接管 | 正式发布、安装、配置/身份保留和 metadata 检查 | 修复 Responses 502，实际生成通过后按事务流程接管 |
| ztty 性能 | 正式 0.5.0、32 项新像素与三阶段实测 | 针对仍回退的场景优化，并用相同基线验证 |
| zgpui 性能 | 可复查的首轮 CPU 对照与消费者路径审计 | 保留布局/查询剖析、独立生产优化、同任务对照；GPU/应用层另设可比任务 |
| LMM / Extore | 已固定稳定 core/CLI | 独立扩展宿主候选完成业务端到端后再纳入 |

每项保留唯一现有负责人、精确来源、原始失败和下一项必要验收。健康的现有任务继续执行，避免重复构建、并行改写同一工作树或用一次通知代替下游集成。

定时维护的最新已知状态为暂停：任务接口返回 `is_enabled=false`，最近结果为空且 `requires_user_action=true`，没有提供暂停者或原因。因此当前会话的实际工程进展不能表述为“24 小时无人值守已经持续运行”。已有任务此前恢复过一次，未通过重复启用、重复创建或 run_now 形成循环。04:03 UTC 前后的再次读取仍是同一暂停记录；最后一次完成结果为空、要求用户操作，且未给出原因。需要用户处理的任务状态单独说明。

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
| OniMods | application | [14dba75a5752](https://github.com/LIghtJUNction/OniMods/commit/14dba75a5752c3142039a8660ce37cdf57d7082a) |
| lmm-api-source | application | [4571b477d490](https://github.com/TokenNotIncluded/lmm-api-source/commit/4571b477d490b86d477f44f1c6768cc5f3b409d1) |
| mechrevo-drivers | application | [4599a3825dac](https://github.com/LIghtJUNction/mechrevo-drivers/commit/4599a3825dac3c85efeeb490cb4eebe1c1b6dff0) |
| oh-my-ztty | suite | [0fdc87873c53](https://github.com/LIghtJUNction/oh-my-ztty/commit/0fdc87873c53e7c87d18952f83a7b94fc4149de5) |
| ssmcp | application | [785e6b00440b](https://github.com/LIghtJUNction/ssmcp/commit/785e6b00440b048d00d9da626a33defa99108afe) |
| z58 | library | [c70d50eafb3f](https://github.com/LIghtJUNction/z58/commit/c70d50eafb3f50eb9a709861f9e1ed2c2fa48dc3) |
| z64 | library | [7e9cff67beae](https://github.com/LIghtJUNction/z64/commit/7e9cff67beae2c484f8b9749b83ae24a1d0e1bbd) |
| zcall | library | [8fb84b812b80](https://github.com/LIghtJUNction/zcall/commit/8fb84b812b8025e34399b28e27242605d68ea345) |
| zcall-gui | application | [5dbc423eedd4](https://github.com/LIghtJUNction/zcall-gui/commit/5dbc423eedd4d529a38b3e8e3adc3e6355a56b2b) |
| zcall-omarchy | application | [78282c3c3cfa](https://github.com/LIghtJUNction/zcall-omarchy/commit/78282c3c3cfa6e9e65e2cbd654f38a96398c6e03) |
| zcalld | application | [b853e264eced](https://github.com/LIghtJUNction/zcalld/commit/b853e264eced9fbd25120d261eb188a3a8e3b1df) |
| zcalld-compat | extension | [7c782e9a6f43](https://github.com/LIghtJUNction/zcalld-compat/commit/7c782e9a6f431c7112112c04940c015adf2d76df) |
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
| zterm | library | [a2074bac4c03](https://github.com/LIghtJUNction/zterm/commit/a2074bac4c030cfd7c0b2514c852a89dcf54648f) |
| ztty | application | [c4f8f48c9598](https://github.com/LIghtJUNction/ztty/commit/c4f8f48c9598284a589e609f25242b49ceabfea8) |
| ztuio | library | [9c632b30f7e2](https://github.com/LIghtJUNction/ztuio/commit/9c632b30f7e2c2fd51a19b4bc5d90d529041ae7e) |
| ztype | application | [037de9972e16](https://github.com/LIghtJUNction/ztype/commit/037de9972e169942ca6258d6aee6ba53711204f6) |
| zui | library | [5e37fcfb791e](https://github.com/LIghtJUNction/zui/commit/5e37fcfb791eec9ac523fc19373e95d0a513112f) |
| zuse | application | [d930769005d3](https://github.com/LIghtJUNction/zuse/commit/d930769005d307c42639e8abedc81ab039427e40) |
| zvte | library | [b4e50a5cde47](https://github.com/LIghtJUNction/zvte/commit/b4e50a5cde476fb5303060f3ecbc9200ccea5cc0) |

生成清单与上述固定来源绑定；后续应用补丁、正式发行和性能结果应以新增提交更新记录，不能覆盖失败原始证据或将未执行项改成成功。
