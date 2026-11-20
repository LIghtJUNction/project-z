# Project Z

Project Z 统一维护内部库及其消费者。**内部依赖直接使用 GitHub 默认分支的最新源码；Cargo 注册表用于外部发布。**

本仓库记录每次更新实际采用的提交，检查消费者是否使用同一份源码，并计算变更影响。实现、许可证、正式发行和应用验收仍由各子仓库维护。

## 更新与验证

在独立工作区中运行：

```sh
git clone --recurse-submodules https://github.com/LIghtJUNction/project-z.git
cd project-z
python3 scripts/project_z.py sync
python3 scripts/project_z.py check
python3 scripts/project_z.py resolve --all
```

需要 Git、Python 3.11 或更新版本，以及仓库指定的 Rust 工具链。应用需要的系统库、桌面会话和设备见各自说明。

| 命令 | 作用 |
| --- | --- |
| `sync` | 查询 GitHub 默认分支，更新干净且处于 detached 状态的子仓检出，记录确切提交并生成索引 |
| `check` | 核对 Git 来源、版本约束、锁文件、嵌套 gitlink、远端新鲜性和生成文件 |
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

需要发布的 crate 在声明中保留与上游 Cargo.toml 实际版本相符的 `version` 元数据；它校验 Git 源码版本，发布时成为外部使用的注册表依赖。同仓库内的 workspace/path 依赖继续保留。

Cargo.lock 保存本轮解析的具体 Git 提交。维护者通过 `cargo update -p <包名>` 更新内部依赖，验证后提交锁文件；日常构建使用 `--locked`。这样既能在每次同步时使用最新源码，也能复现某次验证。版本号相同但 Git 提交不同，仍会被视为不同源码。

协调器不生成 crates.io 到本地 path 的覆盖，也不临时改写再还原锁文件。声明和实际解析都会检查；同名旧包、未发布的内部 package 和可选依赖不能绕过来源约束。所有指向已登记 Project Z 仓库的子模块自动参与 gitlink 检查，Cargo 排除的应用也包括在内。

规则依据：[Cargo 的 Git 与多来源依赖](https://doc.rust-lang.org/cargo/reference/specifying-dependencies.html)、[cargo update 与锁文件](https://doc.rust-lang.org/cargo/commands/cargo-update.html)。

## 项目与传播

[项目索引](docs/PROJECTS.md) 列出仓库、实际 package、版本、关联与提交。`.gitmodules` 定义仓库 URL，`project-z.toml` 定义角色、特殊 manifest 和运行时关系。一个仓库可以含多个 package；独立子模块属于自己的仓库，不按目录位置误归给应用。

底层库的负责人负责推进所有受影响的消费者，包括兼容适配、声明、锁文件、源码指针和对应行为的验证。按依赖顺序先推送子仓，再同步聚合图。新增库使用 `git submodule add <GitHub URL> <目录>` 登记；不要凭名称前缀推断包归属。

```sh
python3 scripts/project_z.py impact --repositories zsys
python3 scripts/project_z.py run --repo zcall -- test --lib --tests
python3 scripts/project_z.py order
```

默认的 `run` 和 `resolve` 选择公共库；`resolve --all` 包含应用。非 Rust、桌面、服务、设备及发行包仍执行自己的验收，不能用 Cargo 解析成功代替。

## 记录与发布

日常开发以本地验证为准；正式发行保留必要的构建、签名、制品与部署流程。报告记录实际源码、命令、结果和未覆盖范围，历史记录中的旧 SHA 保持原样。

生成截图、APK、压缩包和编译物放到云盘或指定制品位置，Git 保存文字证据和链接。必要图标、字体、测试夹具及构建引导文件按用途保留。开发机使用共享 Cargo target，相关命令由外层批次持有共享锁，见 [AGENTS.md](AGENTS.md)。

`scripts/maintenance.py` 审计上游默认分支和外部发布状态；显式 `--apply` 在独立工作树准备更新，通过全图检查后才形成候选提交。注册表尚未发布不阻止内部采用最新 Git 源码。

`scripts/release.py` 和正式工作流打包已验证、干净的递归源码，并保存提交清单。正式标签与发布制品不会由日常同步自动更新。协作细节见 [CONTRIBUTING.md](CONTRIBUTING.md)。
