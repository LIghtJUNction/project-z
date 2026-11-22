# Dotfiles

Keep your shared shell and application settings in a private GitHub repository through `omztty setup` and `omztty sync`. The standard profile path stays the same across installations, and the CLI prints its actual location with `omztty config path`.

The [shell guide](shell.md) covers PATH, environment variables and rc snippets. The [configuration guide](configuration.md) covers the application profile. You can also manage an independent repository with `omztty dot`, as described below.

## Synchronize the suite profile

Start the interactive setup:

```sh
omztty setup
```

The wizard prepares the local profile, offers to install the zsh startup block and asks whether to configure GitHub synchronization. The remote step is optional. It uses the GitHub CLI's current account and accepts a private repository owned by that account.

Install `gh` through your package manager and sign in when you want GitHub synchronization:

```sh
gh auth login
omztty setup --repo dotfiles
```

This creates a private `dotfiles` repository under your signed-in GitHub account and uploads the selected profile files. The command shows the account and repository before the confirmed remote operation. Your existing Git identity is used for commits.

Local-only setup works without the GitHub CLI:

```sh
omztty setup --local
```

`--local` initializes configuration without connecting an ordinary shell startup file. Add `--install-rc` to install that block explicitly. A script can use `--yes` together with an explicit `--local`, `--repo NAME` or `--from OWNER/NAME` choice; `--yes` alone does not choose a remote operation.

If you already created an empty private GitHub repository under your own account, connect it explicitly:

```sh
omztty setup --local
omztty sync init
git -C "$(omztty config path)" remote add origin git@github.com:YOUR_LOGIN/dotfiles.git
```

`sync init` creates the local Git repository and records the initial configuration. It uses your configured Git name and email, and does not create a remote or push. Replace `YOUR_LOGIN` with the signed-in account name. Use `setup --from` below when that repository already contains a profile you want to restore.

After making changes, inspect and synchronize them explicitly:

```sh
omztty sync status
omztty sync push
```

Shared shell edits made through `omztty` are already recorded as local commits when profile Git is enabled. `push` commits any remaining allowed changes, including manual edits, then pushes to the configured private repository. It checks the repository's ownership and visibility. Staged or tracked files outside the allowed configuration layout stop synchronization for review. Untracked files outside that layout remain local and are reported as `Kept local`. Keep credentials and machine-specific environment values in the local scope described in the [shell guide](shell.md#manage-environment-variables).

Git is the version history once the profile has its own repository. The shell manager stops creating new file snapshots, and its local commits stay on the machine until you push. Machine-specific environment values and the ordinary home rc startup block stay outside Git and receive no new snapshots in this mode. Previously saved snapshots remain local.

Only allowed text configuration is synchronized. Binary files, caches, snapshots and local environment files are excluded. Set your Git commit name and email before enabling history or changing shared files.

## Review and restore a version

```sh
omztty sync history
omztty sync restore COMMIT
omztty sync restore COMMIT shell/env.tsv
```

`history` shows the latest 20 local commits with their short identifiers, dates and subjects. Choose `COMMIT` from that output. With no path, `restore` restores the shared `shell/` configuration: environment values, PATH rules and rc snippets. Supply one path relative to the profile to restore a particular allowed file, including an application configuration under `files/`.

Restore requires a clean working tree. It checks the selected configuration before writing and records the restoration as a new local commit. It creates no file backup and does not push. If the selected version predates a currently tracked file, restoring that file removes it and records the removal. Run `omztty sync push` when you want the restored version on your other machines.

You can still edit configuration files directly. Review them with `omztty sync status`, then use `omztty sync push` to commit and synchronize allowed changes. Open a new shell after restoring shell settings. In Git mode, `rc backups` and `rc restore` direct you to these Git commands.

## Pull configuration changes

`status` reads local Git state. Pull requires a clean working tree and fast-forwards the current branch:

```sh
omztty sync pull
```

If you have local edits, commit and push them first or review them with Git. If branches have diverged, resolve that history with Git before pulling again. The sync commands do not force-push, merge divergent histories or execute downloaded rc files. New shell sessions load the resulting settings through the configured startup entry.

The profile's `shell/` directory and allowed application configuration files are shared. Machine-specific variables, history, caches and existing restoration records are stored outside the synchronized profile. The `.baseline/` copy of shipped defaults stays local and is excluded from Git synchronization. `omztty config sync` is an alias for the same profile-history and synchronization commands.

## Restore on another machine

Install oh-my-ztty and sign in to the same GitHub account, then choose your existing private repository:

```sh
gh auth login
omztty setup --from YOUR_LOGIN/dotfiles
omztty rc check
omztty rc install --dry-run
omztty rc install
omztty shell
```

Replace `YOUR_LOGIN` with your account name. `--from` requires the standard profile location to be absent and preserves an existing profile by refusing to overwrite it. The downloaded profile is not automatically linked over application configuration or sourced during the clone.

New standard profiles adapt application configuration destinations to the current machine's `XDG_CONFIG_HOME`. Review the deployment plan before linking applications on that machine:

```sh
omztty config plan --json
omztty config apply --backup
```

PATH entries under your home directory are portable. Recreate machine-specific environment values with `omztty env set NAME VALUE` on each machine. Review absolute paths in your own snippets and application files before using them on another system.

Restoration does not copy another machine's `.baseline/`. Before using `config refresh`, follow the [default-baseline requirements](configuration.md#refresh-defaults-after-an-upgrade), including availability of the profile's recorded release when no baseline is saved.

## Update configuration with the suite

Use the update scope that matches the change you want:

```sh
omztty update --config-only
omztty update --with-config
```

`--config-only` pulls the configured profile without replacing the suite runtime. `--with-config` updates a per-user runtime and pulls its configured profile. The same clean-tree and fast-forward rules apply. Plain `omztty update` retains the suite-only update behavior; AUR installations update their runtime through the package manager.

Run `omztty config refresh` separately when you want the new suite's unchanged application defaults. It compares against the saved default baseline and preserves your custom files.

## Manage an independent repository

`omztty dot` links selected files from another repository into your home directory, backs up existing files when requested and restores those originals when you remove the deployment. Its lifecycle is separate from the standard suite profile.

## Create a layout

```sh
omztty dot init --root "$HOME/dotfiles"
```

This creates the file layout and a profile. It does not initialize Git or choose a remote.

Copy the files you intend to manage into `files/`. For example, to manage an existing `.zshrc`:

```sh
cp "$HOME/.zshrc" "$HOME/dotfiles/files/zshrc"
printf 'files/zshrc\t.zshrc\n' > "$HOME/dotfiles/profile.zdot"
```

Each profile line has a source path, a tab, then a destination path. The source is relative to the repository; the destination is relative to the target. Blank lines and `#` comments are ignored. Spaces and Unicode names are supported.

## Preview and apply

For the `.zshrc` example, preview the replacement and apply it with a backup of the existing file:

```sh
omztty dot plan --root "$HOME/dotfiles" --target "$HOME" --backup --json
omztty dot apply --root "$HOME/dotfiles" --target "$HOME" --backup
omztty dot status --root "$HOME/dotfiles" --target "$HOME"
```

Plan only reads. Apply creates the managed link and records the saved original. Without `--backup`, an existing destination stops the operation. Repeating apply keeps matching links. Edits made through a managed symlink change the source file in the repository.

## Remove a deployment

```sh
omztty dot remove --root "$HOME/dotfiles" --target "$HOME"
```

Remove uses the saved deployment profile, checks link ownership and restores originals that were backed up. It refuses to remove a destination that you replaced.

To change a deployed profile, remove its previous deployment, edit it, then apply again. Keep the repository at its original path until removal.

For a per-user installation, `omztty uninstall` restores the adopted `omztty config` home profile before removing the runtime. Before removing the AUR package, run `omztty config remove` to restore that profile. Independent repositories deployed through `omztty dot` remain independently managed.

## Synchronize an independent repository

Initialize the repository, commit selected files and configure a remote through normal Git commands. Once that is in place:

```sh
omztty dot sync --root "$HOME/dotfiles" status
omztty dot sync --root "$HOME/dotfiles" pull
omztty dot sync --root "$HOME/dotfiles" push
```

Sync uses the installed Git at `/usr/bin/git` or `/bin/git`. Pull only fast-forwards. Commits, remote selection, credentials and merge resolution stay with Git. A pull does not automatically apply a changed profile.

No synchronization daemon or background network activity is started.

## Limits and recovery

| Boundary | Current behavior |
| --- | --- |
| Profile size | At most 64 KiB |
| Mappings per profile | At most 128 |
| Source and parent symlinks | Rejected |
| Traversal and overlapping destinations | Rejected |
| Ordinary apply failure | New links and moved originals are rolled back |
| Interrupted deployment | Journal is retained for remove recovery |

The suite profile uses `--state-dir` to keep metadata and backups under `~/.local/state/zdot/oh-my-ztty`. Direct zdot invocations without that option retain the target’s `.zdot-state` layout and `.zdot.lock` compatibility. zdot does not upload these files. Concurrent edits by unrelated programs are outside its transaction model.

The native tool requires Linux 4.11 or later and a mounted `/proc`. Its Rust library and CLI use `no_std`, Project Z's zclap and direct system calls, without an allocator or libc.

See [zdot's usage reference](https://github.com/LIghtJUNction/zdot/tree/v0.2.0) and [design and recovery details](https://github.com/LIghtJUNction/zdot/blob/v0.2.0/docs/design.md).
