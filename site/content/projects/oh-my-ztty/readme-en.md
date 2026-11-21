# oh-my-ztty

A lean Linux terminal setup built on Project Z: **ztty + zsh + zshard + zrc + zdot + zfetch + ssmcp + zmem**.

[Website](https://lightjunction.github.io/oh-my-ztty/) · [中文](README.zh-CN.md) · [Install guide](docs/installation.md) · [Performance](docs/performance.md) · [0.2.1 workstation report](docs/reports/workspace-0.2.1.md)

## Install

### Per-user release

Download and inspect the installer, then run it:

```sh
curl -fLO https://github.com/LIghtJUNction/oh-my-ztty/releases/latest/download/install.sh
sh install.sh
~/.local/bin/omztty shell
```

Linux x86_64 and ARM64. Requires system zsh; the graphical terminal uses X11/fontconfig. The bundle includes the Project Z components and a native application configuration profile. The terminal suite installs per user. By default, the installer also uses sudo to set up zmem as the system memory manager; use `--no-memory-manager` for a per-user-only install. Installation is repeatable. Your login shell and existing tools remain available. Runtime and configuration commands need no Rust or Python.

### Arch Linux (AUR)

Install the [oh-my-ztty-bin package](https://aur.archlinux.org/packages/oh-my-ztty-bin) with an AUR helper:

```sh
yay -S oh-my-ztty-bin
omztty doctor
```

Use your AUR helper to upgrade the system package. Configuration adoption remains explicit through the commands below. Before removing the package, run `omztty config remove` to restore adopted configurations, then remove it with your package manager. [Installation guide](docs/installation.md#arch-linux-aur) includes the `makepkg` route.

## The suite

| Component | Job |
| --- | --- |
| [ztty](https://github.com/LIghtJUNction/ztty) | Native terminal |
| [zshard](https://github.com/LIghtJUNction/zshard) | Original zsh framework: completion, suggestions, highlighting and lazy plugins |
| [zrc](https://github.com/LIghtJUNction/zrc) | Native Neovim and terminal-tool configuration with one warm Ink palette |
| [zdot](https://github.com/LIghtJUNction/zdot) | `no_std` dotfiles manager with plans, reversible links and explicit Git sync |
| [zfetch](https://github.com/LIghtJUNction/zfetch) | On-demand native system overview, zero crate dependencies |
| [ssmcp](https://github.com/LIghtJUNction/ssmcp) | On-demand MCP workspace connection for AI |
| [zmem](https://github.com/LIghtJUNction/zmem) | System memory pressure, managed background jobs and adaptive Swap |

Development follows each component's latest default branch. Git submodules and `dependencies.lock.json` record the exact sources selected for a build. The [0.2.6 release record](docs/reports/0.2.6/release.zh-CN.md) describes the already published combination. Your Linux distribution supplies zsh. See the [completion reference](docs/completions.md) for command and version coverage.

## System memory

zmem is the default memory and Swap manager. The installer adopts existing Swap, enables its system service and keeps local policy in `/etc/zmem/zmem.conf`. Subsequent installs preserve that configuration.

```sh
omztty memory status --json --processes
omztty memory plan --json
omztty memory run --class background -- cargo build
omztty memory rollback
```

Use `omztty memory setup` to enable the bundled manager later. System setup copies zmem to root-owned `/usr/local/bin/zmem`; the service continues independently of the terminal suite. [Memory policy and recovery](site/content/memory.md) explain defaults, workload classes and skipped setup.

## Ink preset

A warm graphite, linen and copper palette, generous spacing and a two-line prompt with the path, cached Git branch and command status. The prompt uses zsh builtins; installed fonts fall back through Fontconfig. [Customize the preset](docs/installation.md#ink-appearance).

The [workstation report](docs/reports/workspace-0.2.1.md) records the deployed Ink configuration, desktop launch chain, broker reuse, recovery steps and acceptance scope.

## Make it your default workspace

### Shell settings and private sync

`omztty setup` guides local initialization, an optional zsh startup hook and a private dotfiles repository under your own GitHub account. Start locally with:

```sh
omztty setup --local --install-rc
omztty env set EDITOR nvim --shared
omztty env set PROJECT_ENDPOINT https://example.invalid
omztty env list
omztty path add ~/.local/bin
omztty path add ~/tools/bin --append
omztty rc add 10-aliases
omztty rc edit 10-aliases
omztty rc check
omztty rc status
```

Shared data and zsh snippets live in `~/.config/oh-my-ztty/profile/shell/`; machine-only environment values default to `~/.config/oh-my-ztty/local/env.tsv`. Values are hidden in lists. The `env file`, `path file` and `rc file NAME` commands print their locations, and the corresponding `edit` commands validate manual changes. PATH rules keep their order and expand `~/` for each machine.

Before Git is enabled, `rc backups` and `rc restore ID` manage local file versions. An independent profile Git repository switches shared shell changes to local commits and stops new snapshots. Use `sync history`, `sync restore REV [PATH]` and an explicit `sync push`; machine-only values stay outside Git. Synchronization accepts allowed text configuration and rejects binary files.

```sh
omztty setup --repo dotfiles
omztty sync status
omztty sync push
omztty update --config-only
omztty update --with-config
```

GitHub setup needs `gh auth login --hostname github.com`; commits need your Git `user.name` and `user.email`. Read the [shell guide](site/content/shell.md) and [private sync guide](site/content/dotfiles.md) for command examples, file formats and recovery.

### Application configuration

~~~sh
omztty config init
omztty config plan --json
omztty config apply --backup
~~~

One editable profile manages zsh, ztty, Neovim, Kitty, Foot, Ghostty, tmux, fzf, bat, ripgrep and Git display settings. Existing configurations are backed up by zdot. After upgrading, run `omztty config refresh` to update defaults you have not changed; your edits and deliberately removed files are preserved. [Configuration and recovery](docs/configuration.md) explains the native editor, application coverage and file locations.

## Everyday commands

```sh
omztty terminal        # Open ztty with the suite's zsh configuration
omztty shell           # Try the shell in your current terminal
omztty info            # Native system overview
omztty doctor          # Check binaries, system dependencies and zmem service
omztty memory          # Inspect memory pressure and Swap
omztty ai context      # Emit explicit shell context
omztty ai connect      # Start ssmcp in your workspace
omztty dot plan --root ~/dotfiles --target "$HOME"  # Preview dotfile changes
omztty update          # Update a per-user installation
omztty uninstall       # Restore configs and remove a per-user installation
```

AI-generated commands are reviewed in the shell input line before execution. The suite does not start an AI model or resident agent at shell startup.

Current source builds also expose startup inspection through zfetch:

```sh
omztty info --boot         # Inspect startup services and configuration paths
omztty info --boot --json  # Read the same startup chain as JSON
```

## Develop together

```sh
git clone --recurse-submodules https://github.com/LIghtJUNction/oh-my-ztty.git
cd oh-my-ztty
python3 scripts/workspace.py status
python3 scripts/workspace.py sync
python3 scripts/workspace.py check
python3 scripts/build_bundle.py
```

`sync` fetches all seven default branches and records their commits and observation times in the schema 2 source lock. After the first full synchronization, `sync zshard` updates one component. The bundle compiles all five native programs from those sources with Cargo's `--locked` option and respects the configured shared target directory.

[Development and release guide](CONTRIBUTING.md) covers local checks, source updates and explicit version publication. [Architecture](docs/architecture.md) describes the runtime boundaries and extension interfaces.

MIT license. Performance claims and their measurement conditions belong together; see [the benchmark record](docs/performance.md).
