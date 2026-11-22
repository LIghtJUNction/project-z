# Shell, PATH and environment

Use `omztty` to keep your zsh settings in a predictable directory and change them from the command line. Shared settings live in your profile. Once you enable Git for that profile, shared shell changes are recorded as local commits and you choose when to push them.

## Start with setup

```sh
omztty setup
```

The wizard prepares your profile, offers to connect it to your existing zsh startup file, and can help create a private dotfiles repository under your own GitHub account. It shows the configuration location and asks before the optional steps. GitHub synchronization uses the optional `gh` command and its existing login.

For a local setup without a GitHub repository:

```sh
omztty setup --local
omztty shell
```

`omztty shell` loads the settings in a new preset zsh session. To load the same settings when your ordinary zsh starts, preview and install its startup block:

```sh
omztty rc install --dry-run
omztty rc install
```

The block goes into `$ZDOTDIR/.zshrc` when `ZDOTDIR` is set, otherwise `~/.zshrc`. Existing startup code remains in place. Repeating installation keeps one block. This integration manages zsh; it does not change your account's login shell.

## Manage environment variables

An environment variable is a named value that a shell passes to programs it starts. For example, tools use `EDITOR` to choose an editor. Setting a value in the profile makes it available to future shell sessions.

```sh
omztty env set EDITOR nvim --shared
omztty env set API_BASE_URL https://api.example.invalid
omztty env list
omztty env get EDITOR
```

`set` saves a variable locally by default. Add `--shared` when the value belongs on your other machines and may be committed to your private profile repository. A local value overrides a shared value with the same name. `list` shows names and their sources; `get NAME` or `list --show` displays values explicitly.

```sh
omztty env list --show
omztty env unset API_BASE_URL
omztty env unset EDITOR --shared
```

`unset` removes the saved definition from the selected scope. A shared value or a value inherited from the parent session can still exist. Start a fresh shell to check the resulting environment.

Shell quoting still applies when you enter a command. Quote spaces and use single quotes when dollar signs or command-looking text must remain literal:

```sh
omztty env set PROJECT_LABEL 'work laptop'
omztty env set EXAMPLE_TEXT 'literal $HOME, not an expansion'
```

The stored value is data. The loader does not execute it as shell code. Use the dedicated PATH commands below to manage command-search directories.

## Manage PATH

`PATH` is an ordered list of directories. When you type a command name, the shell looks through that list from left to right. A directory placed first takes priority over later directories containing the same command.

```sh
omztty path add "$HOME/.local/bin"
omztty path add "$HOME/dev tools/bin" --append
omztty path list
```

The default placement is at the front. `--append` places a directory after the inherited PATH. Only your chosen directory rules are saved: temporary virtual-environment and toolchain entries from the current process are not copied into the profile.

Change a saved directory's priority or remove its rule:

```sh
omztty path move "$HOME/dev tools/bin" first
omztty path move "$HOME/.local/bin" last
omztty path remove "$HOME/dev tools/bin"
```

The same directory is not added repeatedly when a shell loads the settings again. Paths under your home directory are stored in portable form so another machine can expand them under its own home directory. Quote directories that contain spaces. A colon separates PATH entries and cannot be part of one saved directory.

Compare the saved rules with the PATH inherited by the command:

```sh
omztty path list
omztty path list --effective
```

Removing a rule stops oh-my-ztty from adding it. A directory supplied by the operating system, another startup file or a virtual environment can remain in PATH.

## Manage rc snippets

An rc snippet is an ordinary zsh file containing commands to run during startup. Use snippets for aliases, functions and shell settings that need code rather than a named environment value.

```sh
omztty rc add aliases
omztty rc edit aliases
omztty rc check
omztty rc list
omztty rc status
```

For example, the `aliases` snippet can contain:

```zsh
alias ll='ls -alF'
```

Import an existing file, inspect a snippet and switch it on or off from the command line:

```sh
omztty rc add tools --from "$HOME/tools.zsh"
omztty rc show tools
omztty rc disable tools
omztty rc enable tools
omztty rc remove tools
```

`rc check` validates environment and PATH records and checks snippet syntax without running the snippets. Enabled snippets are normal executable zsh code, and run when the settings load. `rc add` creates an enabled snippet, including when importing a file; review the source before importing it. With Git enabled, changing a shared snippet records a local commit. Before Git is enabled, the shell manager keeps local file snapshots.

Enabled files end in `.zsh` and load in filename order. Disabling a snippet retains its contents in a `.zsh.disabled` file.

## Find and edit the files

Every command group can print its actual location, including XDG overrides:

```sh
omztty config path
omztty env file
omztty env file --shared
omztty path file
omztty rc file aliases
```

With the default XDG locations, the layout is:

| File or directory | Contents | Included in profile sync |
| --- | --- | --- |
| `~/.config/oh-my-ztty/profile/` | Profile repository and application files | Yes |
| `~/.config/oh-my-ztty/profile/shell/env.tsv` | Shared environment variables | Yes |
| `~/.config/oh-my-ztty/profile/shell/path.tsv` | Ordered PATH rules | Yes |
| `~/.config/oh-my-ztty/profile/shell/rc.d/` | zsh snippets | Yes |
| `~/.config/oh-my-ztty/profile/.baseline/` | Local copy of shipped defaults for refresh | No |
| `~/.config/oh-my-ztty/local/env.tsv` | Machine-specific environment values | No |
| `~/.local/state/oh-my-ztty/backups/` | Local file snapshots made before Git is enabled | No |
| `~/.local/state/zdot/oh-my-ztty/` | Application deployment journal and originals | No |

`XDG_CONFIG_HOME` changes the configuration root, and `XDG_STATE_HOME` changes the state root. Home application deployment requires an absolute configuration root inside HOME.

You can edit the files with any text editor. The CLI also opens them using your editor:

```sh
omztty env edit
omztty env edit --shared
omztty path edit
omztty rc edit aliases
omztty rc check
```

Use `env set`, `path add` and the other commands for routine changes; they choose the correct file and validate the input. Manual editing is useful when reviewing several settings together. The `edit` commands validate a temporary copy before saving it, so invalid edits leave the existing configuration in place.

Each environment record has a variable name, one actual tab character, then the literal value. For example, an `env.tsv` file can contain:

```text
# Shared environment values
EDITOR	nvim
PROJECT_LABEL	development workstation
```

Each PATH record has `prepend` or `append`, one actual tab, then an absolute directory or a home-relative directory:

```text
# Ordered PATH rules
prepend	~/.local/bin
append	/opt/toolchain/bin
```

Both formats accept empty lines and comments beginning with `#`. Use tabs between fields, not spaces. A value cannot contain a tab, carriage return or newline; a PATH directory also cannot contain a colon. Each variable name and directory appears once per file.

Values are literal text: do not add shell quotes or an `export` prefix to a data record. An environment value containing `$HOME` stays exactly that text. PATH entries expand only a leading `~` or `~/` to the current machine's home directory. Rc snippets use ordinary zsh syntax. Run `omztty rc check` after editing files directly.

Existing `options.zsh` and `local.zsh` files continue to work in the preset shell. `options.zsh` holds options needed before zshard initializes; `local.zsh` holds existing personal additions. They remain local unless you deliberately move the relevant settings into the shared profile.

## Load a change

A new `omztty shell` session reads the updated settings. An ordinary new zsh session also reads them after `rc install`.

To reload from an already running suite shell:

```zsh
source "$OMZTTY_ROOT/config/zsh/settings.zsh"
```

Reloading also runs enabled rc snippets again. `omztty rc status` prints a reload command with the actual installation path, which is useful from an ordinary zsh session.

A command cannot change the environment of the parent shell that launched it, so merely running `env set` or `path add` does not change that shell's current variables. A fresh session is the clearest way to check removals.

## Review and restore changes

Git becomes the history for shared shell settings when the standard profile has its own Git repository. `omztty setup --repo NAME` and `omztty sync init` record the initial local configuration, using your configured Git name and email. The shell manager stops making new file snapshots. PATH changes, shared environment changes and snippet changes create local commits; they are uploaded only when you run `omztty sync push`.

```sh
omztty sync history
omztty sync restore COMMIT
omztty sync restore COMMIT shell/path.tsv
```

Choose `COMMIT` from the recent local history. With no file argument, restore selects the shared shell configuration. Supply a path relative to the profile to restore one allowed file, such as `shell/path.tsv` or `shell/env.tsv`.

Restore requires a clean working tree, checks the selected configuration and records the result as a new local commit. It creates no file snapshot and uploads nothing. Use a new shell to load the restored settings, then `omztty sync push` when you want to synchronize that version.

Git needs your commit name and email before recording a shared change. If they are missing, the command stops before writing the change. Set them for this profile if needed:

```sh
git -C "$(omztty config path)" config user.name "Your Name"
git -C "$(omztty config path)" config user.email "you@example.com"
```

Machine-specific environment values and the ordinary home rc startup block stay outside Git. In Git mode, changes to those local files also create no snapshots. Existing snapshots from before Git was enabled stay on disk; new changes use Git history. `rc backups` and `rc restore` point you to the Git history commands in this mode.

### Before enabling Git

For a profile without its own Git repository, the shell manager saves local file snapshots:

```sh
omztty rc backups
omztty rc restore BACKUP_ID
```

Each ID describes one file's previous contents and permissions, or records that the file was previously absent. Restoring an absence record removes the newly created file. The current version is saved before restoring a record.

### Remove the startup block

To stop an ordinary zsh from loading the managed settings while retaining the configuration:

```sh
omztty rc uninstall --dry-run
omztty rc uninstall
```

Use `omztty config remove` separately when restoring an application profile that was deployed with `config apply`.

## Synchronize between machines

The [dotfiles guide](dotfiles.md#synchronize-the-suite-profile) explains private GitHub setup, explicit push and pull, and restoring a profile on another machine. The update commands have separate scopes:

| Command | What it updates |
| --- | --- |
| `omztty update` | The installed per-user suite |
| `omztty update --config-only` | Your configured profile repository |
| `omztty update --with-config` | The per-user suite and your configured profile repository |
| `omztty config refresh` | Shipped application defaults that you have not changed |

Keep machine-specific values in the local scope. A private Git repository still has history: removing a value from the latest file does not remove it from earlier commits.
