# Architecture

The suite packages seven independently maintained tools around system zsh. This page explains which process does each job, where configuration lives and how a release records the versions it uses.

## Process boundaries

| Component | Responsibility | When it runs |
| --- | --- | --- |
| ztty | Terminal rendering, windows and PTY | While its broker is running |
| System zsh | Parse and execute commands | While the shell is open |
| zshard | Prompt, completion, editing and plugin loading | Inside the existing zsh process |
| zrc | Native editor and terminal-tool profiles | Read by the corresponding application |
| zdot | Dotfile planning, links and explicit Git sync | For a requested command |
| zfetch | Native system overview | Only for `omztty info` or `omztty zfetch` |
| ssmcp | Authenticated MCP workspace connection | After an explicit connection command |
| zmem | Memory pressure policy, managed background scopes and Swap lifecycle | As the system service enabled by default during installation |

The ztty broker supports detached sessions that can outlive a window. Opening `omztty shell` alone does not start that broker or an AI process.

Shell startup does not download plugins, run zfetch, call a provider or connect to MCP. Optional work is requested through commands or declared plugin loading modes.

## Native code

The zdot library and Linux executable use Rust `no_std`. Their Project Z zclap dependency is configured without its default standard-library feature. The executable uses direct system calls with no allocator, libc or dynamic ELF interpreter.

zshard is written in zsh and adds no compiled helper. The pinned ztty core and executable also use Rust `no_std`; the graphical front end still depends on the [listed graphics libraries](installation.md#requirements).

The bundled ssmcp retains its existing Rust standard-library and networking dependencies. These boundaries describe separate programs. They do not make the whole bundle free of all standard libraries or system libraries.

zrc supplies Lua for Neovim 0.11+ and each application's native configuration files. Applications load those files directly; no separate configuration process runs. zfetch is a native Rust `no_std` utility without crate dependencies and runs only when requested.

Development scripts and build tools are outside the installed native dependency graph. Installing a release and using its configuration commands require neither Rust nor Python.

## Source and artifact pins

The [component gitlinks](https://github.com/LIghtJUNction/oh-my-ztty/tree/main/components) record exact source commits for ztty, zshard, zrc, zdot, zfetch, ssmcp and zmem. The `.gitmodules` file records their repository locations.

[dependencies.lock.json](https://github.com/LIghtJUNction/oh-my-ztty/blob/main/dependencies.lock.json) records the canonical repository, default branch, exact commit and observation time for every component. Source gitlinks and this source lock must agree before building the bundle.

A release includes a build record and `MANIFEST.sha256`. The installer checks both the downloaded archive and its contents before activation. Versioned archives and their checksums are listed on the [release page](https://github.com/LIghtJUNction/oh-my-ztty/releases).

zmem has a zero-dependency Rust `no_std` policy library and a Linux adapter using the standard library and system tools. Its state and policy are exposed as JSON for AI clients.

## Installation state

The per-user installer keeps releases below the user's XDG data directory and selects one with a `current` link. The AUR package owns `/usr/lib/oh-my-ztty` and exposes `/usr/bin/omztty`; its runtime is updated and removed through the package manager.

In both layouts, the launcher addresses bundled executables explicitly, even when another tool with the same name exists elsewhere.

The launcher supplies a separate `ZDOTDIR` for trying the shell, a suite history path and a cache path tied to the release directory. Adopting `omztty config` creates an editable profile and deploys it through zdot; the managed default `.zshrc` reads the same suite entry point.

Personal `options.zsh`, `local.zsh` and completion files live under `${XDG_CONFIG_HOME:-$HOME/.config}/oh-my-ztty`. Personal completions use its `completions/` directory, outside the runtime. HOME adoption requires an absolute `XDG_CONFIG_HOME` within HOME. Its journal and backups live under `${XDG_STATE_HOME:-$HOME/.local/state}/zdot/oh-my-ztty`.

For a per-user installation, uninstallation restores the adopted profile first. A restoration failure or inconsistent deployment record preserves the runtime for recovery. For the AUR package, restore the profile with `omztty config remove` before removing the package. Independent `omztty dot` deployments remain separate. See [configuration](configuration.md).

Before activation, the per-user installer prepares the audited completion cache. Native zsh auditing and input validation remain part of reuse; it is not a bypass of completion security checks.

The default installer also enables the independent zmem system service. It copies the executable to `/usr/local/bin/zmem`, preserves existing `/etc/zmem/zmem.conf` policy, and records a recovery path for earlier managers. `--no-memory-manager` skips this setup. Removing the user suite keeps the system service installed; `sudo /usr/local/bin/zmem rollback` remains available.

## Extension boundaries

Shell plugins use ordinary zsh files, hooks, standard completion functions and prompt callbacks. A pinned plugin installation and its explicit integrity verification are separate from loading it into a shell.

AI providers receive a bounded, explicit context through the [provider contract](ai.md). Proposed commands enter the editing buffer for review.

zrc profiles share the Ink palette through native application files. Neovim supports native packages and explicit local extensions; application and language-server installation remain separate.

Dotfile profiles describe repository-relative sources and target-relative destinations. zdot computes the plan before applying it and records ownership for recovery and removal.

Terminal and MCP extensions remain the responsibility of their upstream Project Z projects. The suite pins those implementations and links to their documentation rather than defining a second incompatible interface.

## Versioned combinations

The suite and its components have independent semantic versions. A suite release is a validated combination, identified by its commit and seven gitlinks.

Publish a component change first, then advance the suite pin and validate the assembled result. Normal shell startup uses the installed versions. [Development and release workflow](development.md)
