# Plugins

Add shell commands, completions and prompt behavior by loading ordinary zsh files. Start with the included example, then add the plugins you want to `local.zsh` so they load in future sessions.

## Load a local plugin

Inside the preset shell, try the included example:

```zsh
zshard load "$ZSHARD_HOME/examples/hello.plugin.zsh"
hello world
```

To load it in future shells, put the first line in [local.zsh](configuration.md#configuration-files). A canonical file path is loaded once in a shell.

## Choose a loading mode

| Interface | When the file is sourced |
| --- | --- |
| `zshard load FILE` | Immediately |
| `zshard defer FILE` | At the next ZLE editing line |
| `zshard lazy COMMAND FILE` | When that command is first used |

Each deferred batch attempts every queued plugin once. A failure does not discard the later plugins; the batch returns its first nonzero status. Plugins queued during a batch wait for the next editing line. Failed plugins are not retried automatically.

A lazy plugin must define its command or make the external executable available. The wrapper preserves the original argument boundaries.

Installing a plugin does not make startup load every installed plugin. Loading remains a separate configuration choice.

## Pin a remote plugin

A remote plugin needs a full 40-character Git commit and an entry file inside that checkout. This example installs the published zshard hello sample:

```zsh
zshard plugin add hello \
  https://github.com/LIghtJUNction/zshard.git \
  a55c2d08b4299b25ec007b45641df87e8c0d0bbb \
  examples/hello.plugin.zsh
zshard plugin verify hello
zshard use hello
```

Add `zshard use hello` to `local.zsh` if you want it in each shell.

The checkout and its lock file record the pin. Installation does not source the downloaded file. Loading it runs that code inside your shell. `verify` explicitly checks Git HEAD and uncommitted changes; ordinary shell loading is separate from that integrity check.

Git file transports and repository hooks are disabled during plugin installation. The entry must resolve inside the checkout.

## Export and restore pins

Keep an exported lock file with your chosen configuration:

```zsh
zshard plugin export > plugins.lock
zshard plugin restore plugins.lock
```

Restore verifies matching installed checkouts, installs missing pins and refuses a different existing pin. It does not load code. A failed batch retains successfully installed entries so a retry can continue.

Use `zshard plugin remove hello` to remove that installed checkout. Changing a pin means explicitly removing it and installing the reviewed replacement.

## Hooks and cleanup

Plugins register hooks through `zshard hook EVENT FUNCTION` and remove them through `zshard unhook EVENT FUNCTION`. Supported events include `chpwd`, `precmd`, `preexec`, `periodic`, `zshaddhistory`, `zshexit` and `zsh_directory_name`.

A plugin owns its functions, variables, hooks and widgets. The hello example exposes cleanup as `zshard_plugin_hello_unload`, which is called by:

```zsh
zshard unload hello
```

Removing an installed checkout does not undo code already loaded in the current shell. Use cleanup or open a new shell. Unload refuses to claim success when the plugin supplies no cleanup function.

## Completions and themes

Register a directory of standard zsh `_command` completion files with `zshard completions DIRECTORY` before completion initializes. With the default lazy setting, that means before the first Tab. With eager loading, initialization has already happened by the time `local.zsh` runs. Registration after initialization returns an error.

Register a prompt callback with `zshard theme FUNCTION`. It receives the last exit status and elapsed whole seconds and assigns `PROMPT` and `RPROMPT`. Keep external commands out of the callback to retain the default prompt's process behavior.

See the [complete extension reference](https://github.com/LIghtJUNction/zshard/blob/v0.2.0/docs/plugins.md) and the [working hello plugin](https://github.com/LIghtJUNction/zshard/blob/v0.2.0/examples/hello.plugin.zsh).
