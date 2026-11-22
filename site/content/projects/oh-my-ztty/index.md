# oh-my-ztty

基于 Project Z 的 Linux 工作环境：**ztty + zshard + zrc + zdot + zfetch + ssmcp + zmem**。系统 zsh 负责执行命令，套件统一终端、编辑器和常用工具的配置。

[官网](https://lightjunction.github.io/oh-my-ztty/) · [English](README.md) · [安装说明](docs/installation.md) · [配置与恢复](docs/configuration.md) · [性能记录](docs/performance.md) · [0.2.1 实机报告](docs/reports/workspace-0.2.1.md)

原生 Tab 补全覆盖套件组件、Codex／Claude／Gemini／OpenCode／pi／Amp、Go／Rust／Node 开发命令，以及 Project Z 等自研 CLI；Git、uv、Cargo 等复用已安装的系统补全。支持多级命令、参数取值与中文路径，个人补全规则优先。详见[补全说明](docs/configuration.md#native-completion)与[覆盖清单](docs/completions.md)。

## 安装

### 用户级发行包

先下载并查看安装脚本，再执行：

```sh
curl -fLO https://github.com/LIghtJUNction/oh-my-ztty/releases/latest/download/install.sh
sh install.sh
~/.local/bin/omztty shell
```

支持 Linux x86_64、ARM64。系统需提供 zsh 5.9+；图形终端使用 X11/XWayland，正式构建在 Ubuntu 24.04 验证。安装包包含七个 Project Z 组件的运行程序或原生配置，终端套件按用户安装，默认通过 sudo 将 zmem 安装为系统内存管理器。使用 `--no-memory-manager` 可跳过系统设置；重复安装会记住该选择，无需在安装时配置 Rust 或 Python。使用编辑器配置需要另行安装 Neovim 0.11+；日常运行和配置部署也不需要 Rust 或 Python。

### Arch Linux（AUR）

通过 AUR 助手安装 [oh-my-ztty-bin](https://aur.archlinux.org/packages/oh-my-ztty-bin)：

```sh
yay -S oh-my-ztty-bin
omztty doctor
```

系统软件包通过 AUR 助手更新，配置采用仍需执行下方命令。卸载软件包前，先运行 `omztty config remove` 恢复原配置，再通过包管理器移除软件包。未使用 AUR 助手时，可按[安装说明](docs/installation.md#arch-linux-aur)使用 `makepkg` 安装。

## 七个独立项目

| 项目 | 作用 |
| --- | --- |
| [ztty](https://github.com/LIghtJUNction/ztty) | 原生终端 |
| [zshard](https://github.com/LIghtJUNction/zshard) | zsh 框架，提供补全、历史建议、命令高亮和延迟加载插件 |
| [zrc](https://github.com/LIghtJUNction/zrc) | Neovim 与常用终端工具的原生配置，共用暖色 Ink 外观 |
| [zdot](https://github.com/LIghtJUNction/zdot) | `no_std` 配置管理工具，预览、部署链接、备份和恢复，并显式执行 Git 同步 |
| [zfetch](https://github.com/LIghtJUNction/zfetch) | 零 crate 依赖的原生 `no_std` 系统概况工具，按需运行 |
| [ssmcp](https://github.com/LIghtJUNction/ssmcp) | 按需把工作区接入 AI 的 MCP 工具 |
| [zmem](https://github.com/LIghtJUNction/zmem) | 默认系统内存与 Swap 管理器，提供压力观测、后台任务约束和自适应交换空间 |

开发时同步各组件默认分支的最新源码，Git 子模块与 `dependencies.lock.json` 共同记录本次构建选用的提交。[0.2.6 发布记录](docs/reports/0.2.6/release.zh-CN.md)保留该已发布版本的组件组合与验收结果。zsh、Neovim 等系统应用需单独安装。进入 shell 后，可按需查看系统概况或启动 AI 连接。zfetch 的 Arch Linux 包名为 `zfetch-project-z` 与 `zfetch-project-z-bin`，发布状态见其仓库说明。

## 默认内存管理

安装器默认启用 zmem 系统服务，接管现有 Swap，把初始方案保存到 `/etc/zmem/zmem.conf`，后续升级保留本机配置。查看状态和策略，或把编译任务纳入后台管理：

```sh
omztty memory status --json --processes
omztty memory plan --json
omztty memory run --class background -- cargo build
```

`omztty memory setup` 可在跳过初次设置后启用 zmem；`omztty memory rollback` 恢复接管前记录的管理器与配置。系统服务运行 root 所有的 `/usr/local/bin/zmem`，独立于用户目录中的套件。卸载终端套件会保留系统内存服务；已卸载后仍可用 `sudo /usr/local/bin/zmem rollback` 恢复。默认参数和命令见[内存管理说明](site/content/memory.md)。

## Ink 默认外观

暖石墨背景、亚麻白文字、铜色重点、28 px 内边距与两行提示符，把路径、Git 分支和输入区分开。Neovim 与终端工具沿用同一套配色。提示符使用 zsh 内置能力；字体通过 Fontconfig 回退，不强制安装图标字体。[自定义预设](docs/installation.md#ink-appearance)。

[实机报告](docs/reports/workspace-0.2.1.md)记录了 Ink 配置、桌面启动链、broker 复用、恢复步骤与验收范围。

## 设为默认工作环境

### Shell、环境变量与 PATH

`omztty setup` 引导初始化、接入现有 zsh rc，并按选择在本人 GitHub 账号下创建私有 dotfiles 仓库。也可以先只在本机使用：

```sh
omztty setup --local --install-rc
omztty env set EDITOR nvim --shared
omztty env set PROJECT_ENDPOINT https://example.invalid
omztty env list                         # 默认隐藏值
omztty path add ~/.local/bin
omztty path add ~/tools/bin --append
omztty path move ~/tools/bin first
omztty path list --effective
omztty rc add 10-aliases
omztty rc edit 10-aliases
omztty rc check
omztty rc status                       # 打印位置和当前 zsh 的重载命令
```

共享配置集中在 `~/.config/oh-my-ztty/profile/shell/`，机器专用变量默认保存在 `~/.config/oh-my-ztty/local/env.tsv`。`env file`、`path file`、`rc file NAME` 显示准确路径；可以使用对应的 `edit` 命令或直接编辑文本文件。PATH 保存的是有序规则，`~/` 在各台机器上按自己的 HOME 展开。

未启用 Git 时，修改前保存本地文件版本，可用 `rc backups` 和 `rc restore ID` 恢复。Profile 启用独立 Git 后停止生成这些快照，共享 shell 修改自动形成**本地提交**；用 `sync history` 和 `sync restore REV [PATH]` 查看、恢复，用 `sync push` 明确上传。机器专用变量留在 Git 外。同步会检查文本类型和允许路径，拒绝二进制文件。

```sh
omztty setup --repo dotfiles            # 确认后创建本人的私有仓库
omztty sync status
omztty sync push
omztty update --config-only            # 只拉取个人配置
omztty update --with-config            # 拉取个人配置，再更新套件
```

GitHub 引导需要 `gh auth login --hostname github.com`，Git 提交需要已配置的 `user.name`、`user.email`。完整教程见 [Shell 与环境变量](site/content/shell.md)和[私有配置同步](site/content/dotfiles.md)。

### 应用配置

先准备可编辑配置并查看部署计划，再备份已有文件、应用链接：

```sh
omztty config init
omztty config plan --json
omztty config apply --backup
omztty config status
```

统一配置覆盖 zsh、ztty、Neovim、Kitty、Foot、Ghostty、tmux、fzf、bat、ripgrep 和 Git 显示设置；应用程序本身单独安装。Git 配色通过配置说明中的显式 include 启用。采用配置后重新打开终端，账户的登录 shell 记录保持原值。

编辑源文件位于 `~/.config/oh-my-ztty/profile/`，个人 shell 片段放在 `profile/shell/rc.d/`，个人补全放在 `~/.config/oh-my-ztty/completions/`；已有的 `local.zsh` 仍会加载。对应 XDG 配置可改变这些位置；HOME 配置部署要求 `XDG_CONFIG_HOME` 位于 HOME 内。

升级后运行 `omztty config refresh`，即可更新尚未自行修改的默认文件；个人编辑、新增文件和主动删除的文件会保留。`omztty config remove` 恢复采用配置前保存的文件。用户级安装的 `omztty uninstall` 会先恢复这个受管理的 profile；恢复失败时保留运行程序供修复。通过 `omztty dot` 部署的其他仓库独立管理。完整位置与恢复步骤见[配置说明](docs/configuration.md)。

## 常用命令

```sh
omztty terminal        # 用 ztty 打开预设 shell
omztty shell           # 在当前终端体验
omztty info            # 按需运行 zfetch，显示系统概况
omztty zfetch          # 直接运行套件中的 zfetch
omztty doctor          # 检查组件、系统依赖和 zmem 服务
omztty memory          # 查看内存压力和 Swap
omztty config audit    # 检查统一配置及已知旧 shell 框架位置
omztty ai context      # 输出明确选择的 shell 上下文
omztty ai connect      # 在当前工作区启动 ssmcp
omztty update          # 更新用户级安装
omztty uninstall       # 先恢复配置，再卸载用户级安装
```

AI 建议的命令先进入输入行，由人确认执行。个人配置、补全与历史位于发行版目录之外，更新或卸载时保留。

当前源码构建还可通过 zfetch 查看启动链中的服务与配置路径：

```sh
omztty info --boot         # 查看启动服务和配置文件位置
omztty info --boot --json  # 以 JSON 输出同一启动链
```

## 一起迭代

```sh
git clone --recurse-submodules https://github.com/LIghtJUNction/oh-my-ztty.git
cd oh-my-ztty
python3 scripts/workspace.py status
python3 scripts/workspace.py sync
python3 scripts/workspace.py check
python3 scripts/build_bundle.py
```

`sync` 默认获取七个组件的最新默认分支，并在 schema 2 源码锁中记录提交与观测时间。旧锁首次升级需要完整同步；此后可用 `sync zshard` 单独更新一个组件。打包时通过 Cargo `--locked` 从记录的源码编译五个原生程序，沿用已有的共享构建目录配置。

开发、测试和显式发布步骤见 [CONTRIBUTING.md](CONTRIBUTING.md)。性能数字与测量范围见[性能记录](docs/performance.md)。项目采用 MIT 许可证。
