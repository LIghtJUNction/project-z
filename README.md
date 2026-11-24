# Project Z

[统一文档站](https://lightjunction.github.io/project-z-site/) · [文档构建与更新](site/README.md)

Project Z 统一维护内部库及其消费者。**内部依赖直接使用 GitHub 默认分支的最新源码；Cargo 注册表用于外部发布。**

本仓库记录每次更新实际采用的提交，检查消费者是否使用同一份源码，并计算变更影响。实现、许可证、正式发行和应用验收仍由各子仓库维护。

## 更新与验证

在独立工作区中运行：

```sh
git clone https://github.com/LIghtJUNction/project-z.git
cd project-z
python3 scripts/project_z.py sync
python3 scripts/project_z.py check
python3 scripts/project_z.py resolve --all
```

`sync` 会从远端默认分支初始化缺失或空目录中的子模块，再记录本轮提交。未初始化目录中的已有文件、未提交改动和需要移动的活动分支会阻止同步。

需要 Git、Python 3.11 或更新版本，以及仓库指定的 Rust 工具链。应用需要的系统库、桌面会话和设备见各自说明。

| 命令 | 作用 |
| --- | --- |
| `sync` | 查询 GitHub 默认分支，初始化缺失的子仓并更新干净的 detached 检出，记录确切提交并生成索引 |
| `check` | 核对内部 Git 声明、锁文件、嵌套 gitlink、远端新鲜性和生成文件 |
| `resolve --all` | 用 Cargo `--locked` 解析全部 Rust 工作区，逐包核对 Git URL、提交与版本 |
| `impact --repositories <名称>` | 列出直接、间接和明确登记的运行时、安装消费者 |
| `run --affected <名称> -- <Cargo 参数>` | 在记录的源码上运行选定的 Rust 消费者验证 |

同步发现不兼容的版本、旧锁或旧 gitlink 时，需要先在所属仓库修复、验证并提交。聚合工具不会替换成旧注册表包，也不会覆盖正在使用的分支。维护程序已选定来源时可用 `sync --record` 只生成清单；后续 `check` 仍要求来源是最新默认分支。

## Cargo 依赖规则

跨 Project Z 仓库使用统一 URL，省略 `branch`、`tag` 和 `rev`：

```toml
[dependencies]
zconv = { git = "https://github.com/LIghtJUNction/zconv.git" }
```

跨仓依赖的开发声明不写 `version`；可发布 crate、构建/开发依赖和 workspace 继承也遵循此规则。包自身版本及 Cargo.lock 中的版本继续保留，同仓 workspace/path 和外部依赖保持原有规则。对外发布时，在独立 staging 中按已提交锁文件生成精确版本依赖，见[发布投影](docs/release-projection.md)。

Cargo.lock 保存本轮解析的具体 Git 提交。维护者通过 `cargo update -p <包名>` 更新内部依赖，验证后提交锁文件；日常构建使用 `--locked`。这样既能在每次同步时使用最新源码，也能复现某次验证。版本号相同但 Git 提交不同，仍会被视为不同源码。

协调器不生成 crates.io 到本地 path 的覆盖，也不临时改写再还原锁文件。声明和实际解析都会检查；同名旧包、未发布的内部 package 和可选依赖不能绕过来源约束。所有指向已登记 Project Z 仓库的子模块自动参与 gitlink 检查，Cargo 排除的应用也包括在内。

规则依据：[Cargo 的 Git 与多来源依赖](https://doc.rust-lang.org/cargo/reference/specifying-dependencies.html)、[cargo update 与锁文件](https://doc.rust-lang.org/cargo/commands/cargo-update.html)。

## 项目与传播

Project Z 本地服务共用 [Unix socket 规范](docs/unix-sockets.md)，定义默认路径、权限、生命周期和 MCP 接入方式。

[项目索引](docs/PROJECTS.md) 列出仓库、实际 package、版本、关联与提交。`.gitmodules` 定义仓库 URL，`project-z.toml` 定义角色、特殊 manifest 和运行时关系。一个仓库可以含多个 package；独立子模块属于自己的仓库，不按目录位置误归给应用。

[底层 z 库依赖替换计划](docs/maintenance/2026-11-23-dependency-replacement.md) 按实际调用边界安排通用能力复用、消费者代码删除与传播验收，并记录 zrun 接入 zharness、ssmcp 前仍需补齐的能力。

底层库的负责人负责推进所有受影响的消费者，包括兼容适配、声明、锁文件、源码指针和对应行为的验证。按依赖顺序先推送子仓，再同步聚合图。新增库使用 `git submodule add <GitHub URL> <目录>` 登记；不要凭名称前缀推断包归属。

```sh
python3 scripts/project_z.py impact --repositories zsys
python3 scripts/project_z.py run --repo zcall -- test --lib --tests
python3 scripts/project_z.py order
```

默认的 `run` 和 `resolve` 选择公共库；`resolve --all` 包含应用。非 Rust、桌面、服务、设备及发行包仍执行自己的验收，不能用 Cargo 解析成功代替。

`project_z.py run` 启动 Cargo 构建、检查、测试、基准、Clippy、文档和编译任务时，会在 Linux 上优先使用已验证的 zmem 0.2 或更新版本，把新任务放入后台资源组。内存从任务启动时就记入该组，zmem 因而能够按实际使用量和系统余量调整预算。系统未提供可用的 systemd 管理器或可信的活动 zmem 服务时，入口会说明原因并照常执行。设置 `ZMEM_BUILD_BACKGROUND=0` 可让本批任务沿用调用者的分组；已有任务保持原分组，共享 Cargo 构建锁仍由外层批次持有。

使用 zmem 0.4 或更新版本时，这些后台任务还会在启动前检查可用内存和内存 PSI。压力高时默认等待最多 60 秒，超时返回 75，命令不会启动；显式运行可用 `--wait-timeout` 调整等待。交互任务绕过准入，Cargo metadata 查询不加入等待。该入口只纳管它启动的任务，不拦截任意终端命令。参见 [zmem 启动准入说明](https://github.com/LIghtJUNction/zmem/blob/main/docs/background-admission.md)。

## 记录与发布

日常开发以本地验证为准；正式发行保留必要的构建、签名、制品与部署流程。报告记录实际源码、命令、结果和未覆盖范围，历史记录中的旧 SHA 保持原样。

生成截图、APK、压缩包和编译物放到云盘或指定制品位置，Git 保存文字证据和链接。必要图标、字体、测试夹具及构建引导文件按用途保留。开发机使用共享 Cargo target，相关命令由外层批次持有共享锁，见 [AGENTS.md](AGENTS.md)。

`scripts/maintenance.py` 审计上游默认分支和外部发布状态；显式 `--apply` 在独立工作树准备更新，通过全图检查后才形成候选提交。注册表尚未发布不阻止内部采用最新 Git 源码。

`scripts/release.py` 和正式工作流打包已验证、干净的递归源码，并保存提交清单。[每六小时的同步工作流](docs/scheduled-snapshots.md)默认仅验证。维护者显式启用写入后，完整 CI 通过且存在未发布的新版本时才创建聚合补丁发行。协作细节见 [CONTRIBUTING.md](CONTRIBUTING.md)。
