# Installation

Choose a per-user release installation or the Arch Linux package. Both provide the same suite commands; use the matching update and removal instructions below.

The bundle includes the terminal, shell framework and configuration tools. You need system zsh and the libraries listed below. Installing a release and managing its configuration require neither Rust nor Python.

## Requirements

| Requirement | Supported configuration |
| --- | --- |
| Operating system | Linux x86_64 or ARM64 |
| Shell | System zsh 5.9 or newer |
| Default memory manager | Linux cgroup v2, systemd, util-linux and administrator access; Btrfs also uses btrfs-progs |
| Optional editor profile | Neovim 0.11 or newer, installed separately |
| Private GitHub profile sync | Git and the optional GitHub CLI (`gh`) |
| Graphical terminal session | X11 or XWayland |
| Graphics libraries | X11, Xrender, Xft, Fontconfig, Wayland, xkbcommon, FreeType, HarfBuzz, EGL and GLES |
| Binary ABI | glibc 2.34 or newer and libgcc for ztty and ssmcp |

The ztty 0.5.2 binary needs the listed graphics libraries even when you select the X11 backend. The release workflow targets Ubuntu 24.04 for both architectures. Other distributions also need compatible libraries.

Install Neovim, other applications and language servers separately when you want to use their profiles.

On Ubuntu 24.04, install the basic dependencies with:

```sh
sudo apt-get install zsh git curl libx11-6 libxrender1 libxft2 libfontconfig1 \
  libwayland-client0 libwayland-egl1 libwayland-cursor0 libxkbcommon0 \
  libfreetype6 libharfbuzz0b libegl1 libgles2 libgcc-s1
```

## Arch Linux (AUR)

Install the [oh-my-ztty-bin package](https://aur.archlinux.org/packages/oh-my-ztty-bin) with an AUR helper:

```sh
yay -S oh-my-ztty-bin
omztty doctor
omztty shell
```

With Git and Arch's `base-devel` tools installed, the package can also be built directly:

```sh
git clone https://aur.archlinux.org/oh-my-ztty-bin.git
cd oh-my-ztty-bin
makepkg -si
```

The package installs prebuilt release binaries under `/usr/lib/oh-my-ztty` and provides `/usr/bin/omztty`. Update it through your AUR helper:

```sh
yay -Syu oh-my-ztty-bin
```

If you adopted the application profile, run `omztty config refresh` after upgrading. This updates defaults you have not changed. Use the package manager to remove the runtime; `omztty update` and `omztty uninstall` are for per-user installations.

If an older per-user installation is also on your PATH, use `/usr/bin/omztty` to select the package explicitly.

Restore adopted configurations before removing the package:

```sh
omztty config remove
sudo pacman -R oh-my-ztty-bin
```

## Install a release

Use the installer to keep the suite under your own account. Download it as a file, then run it:

```sh
curl -fLO https://github.com/LIghtJUNction/oh-my-ztty/releases/latest/download/install.sh
sh install.sh
~/.local/bin/omztty doctor
```

The installer downloads the archive for your architecture, verifies its SHA-256 and file manifest, then installs under `${XDG_DATA_HOME:-$HOME/.local/share}/oh-my-ztty`.

Commands go into `~/.local/bin` by default. You can use the absolute launcher path to initialize configuration and save its PATH entry:

```sh
~/.local/bin/omztty setup --local
~/.local/bin/omztty path add "$HOME/.local/bin"
~/.local/bin/omztty rc install
```

Open a new zsh session to load it. For the current shell, add the directory once:

```sh
export PATH="$HOME/.local/bin:$PATH"
```

An unrelated existing `omztty` executable stops installation. Existing tools with other names are preserved; the `omztty` launcher selects its bundled components explicitly.

## System memory manager

The release installer enables zmem by default using sudo. zmem adopts existing Swap, installs a root-owned executable at `/usr/local/bin/zmem`, and keeps the system policy in `/etc/zmem/zmem.conf`. Existing configuration is preserved during upgrades.

```sh
omztty memory status --json --processes
omztty memory plan --json
omztty memory run --class background -- cargo build
```

For a per-user-only install or a machine without systemd, run `sh install.sh --no-memory-manager`. This skips system setup and remembers the choice on subsequent updates. It leaves an existing manager running. `omztty memory setup` enables the bundled zmem immediately; `omztty update --memory-manager` also records the choice for future updates.

Use `omztty memory rollback` to restore the previous managers and configuration. The system service remains installed when the per-user terminal suite is removed; its independent recovery command is `sudo /usr/local/bin/zmem rollback`.

See [memory policy and recovery](memory.md) for defaults, workload classes and AI output.

## Start the environment

Open a configured zsh session in your current terminal:

```sh
omztty shell
```

Type `exit` to return to your previous shell. To open the same setup in a new ztty window:

```sh
omztty terminal
```

Both commands use the suite's configuration for that session. Adopt the application profile below to link its settings into your home directory. Your account's login shell is unchanged.

## Set up your own shell settings

Run the setup wizard after installation:

```sh
omztty setup
```

It prepares the standard profile, offers to connect your ordinary zsh startup file and can create a private GitHub dotfiles repository under your signed-in account. The remote step is optional; `omztty setup --local` prepares local configuration without it.

Manage settings directly from the command line:

```sh
omztty env set EDITOR nvim --shared
omztty path add "$HOME/.local/bin"
omztty rc add aliases
omztty rc edit aliases
omztty rc check
```

The [shell guide](shell.md) explains the values, file paths, manual editing and version history. The [dotfiles guide](dotfiles.md#synchronize-the-suite-profile) covers private synchronization and restoring configuration on another machine.

Once the profile has its own Git repository, shared shell changes made by these commands become local commits. Run `omztty sync history` to inspect them and `omztty sync push` when you want to upload them. Git mode stops new file snapshots; machine-specific values and the home rc startup block remain local.

## Adopt the default workspace

The optional profile adds the suite's zsh, terminal and editor defaults to your home configuration. Create it, inspect the planned changes, then apply it:

```sh
omztty config init
omztty config plan --json
omztty config apply --backup
omztty config status
```

`--backup` saves existing files before replacing them with managed links. `omztty config remove` restores those originals. The [configuration guide](configuration.md) explains each profile, personal settings and the optional Git display include.

Open a new zsh session after adoption. Editable files live under `${XDG_CONFIG_HOME:-$HOME/.config}/oh-my-ztty/profile`. The journal and backups live under `${XDG_STATE_HOME:-$HOME/.local/state}/zdot/oh-my-ztty`. HOME adoption requires an absolute `XDG_CONFIG_HOME` within HOME; roots outside HOME are rejected.

Suite upgrades preserve the editable profile. Run `omztty config refresh` after upgrading to update files that still match their shipped defaults. Custom edits, added files and deliberately removed files are preserved.

Personal completion files belong in `${XDG_CONFIG_HOME:-$HOME/.config}/oh-my-ztty/completions/`. The preset registers that directory for on-demand loading. It stays outside the runtime and survives updates and uninstallation.

## System overview

Run `omztty info` to display system information through the bundled zfetch utility. `omztty zfetch` invokes the same tool directly. The shell does not run it automatically.

## Install options

Choose another absolute command directory or omit the desktop entry:

```sh
sh install.sh --bin-dir "$HOME/bin" --no-desktop
```

A new installation creates a desktop entry by default. `--no-desktop` disables it; `--desktop` enables it again. When neither option is supplied, repeat installations and updates preserve the last successful choice.

Disabling an existing installation removes only desktop links that still point to this suite. Replacement files and foreign links are preserved. Enabling the entry stops if an unrelated file or link already occupies its path.

Personal shell configuration belongs outside the release directory. See [configuration](configuration.md) before adding aliases, themes or plugins.

## Offline installation

Download an archive and its matching `.sha256` file from the same published release. The following example uses the x86_64 archive for [v0.2.6](https://github.com/LIghtJUNction/oh-my-ztty/releases/tag/v0.2.7) once that release is published.

```sh
sh install.sh --from ./oh-my-ztty-0.2.7-linux-x86_64.tar.gz
```

Use the aarch64 archive on ARM64. If you have already obtained the digest from the release record, the installer's `--sha256` option can supply it instead of a sidecar file.

## Update or reinstall

For a per-user installation:

```sh
omztty update
```

To update the profile from your own configured Git repository, select a configuration update explicitly:

```sh
omztty update --config-only
omztty update --with-config
```

`--config-only` pulls the profile without changing the runtime. `--with-config` updates a per-user suite and pulls its profile. The profile must have a clean Git working tree and a fast-forward update available. Use `omztty sync status` to inspect local edits first.

If you adopted a home profile, run `omztty config refresh` after updating to receive changes to unmodified shipped defaults. Upgrade the AUR runtime through your AUR helper; its profile can still be updated with `omztty update --config-only`.

To change the desktop entry choice during an update, select one option:

```sh
omztty update --no-desktop
omztty update --desktop
```

Updates retain the desktop-entry choice saved by your last successful installation. Either option above changes that choice after the update succeeds.

Each version has its own directory. A `current` link selects the active version, and completion caches are separated by release.

Before activation, the installer prepares an audited completion cache. A failed preparation leaves the previous version active. Reinstalling the same archive verifies the existing files; it preserves and reports an installed version that has been modified.

## Uninstall

For a per-user installation:

```sh
omztty uninstall
```

Uninstallation restores the adopted `omztty config` home profile before removing the runtime. Failed restoration or inconsistent deployment records preserve the installation for recovery. After restoration, suite-owned installation files and links are removed; personal profiles, additions, completion files and history are retained.

Independent repositories deployed through `omztty dot` have a separate lifecycle. Use [zdot remove](dotfiles.md#remove-a-deployment) first if you also want to restore those deployments.
