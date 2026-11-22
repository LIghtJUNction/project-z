# AI integration

Use the AI commands to inspect local shell context, connect a client to your workspace or place a proposed command in the editing buffer. Start by inspecting the context below, then choose an ssmcp connection or a provider CLI for requests.

## Inspect context

From any shell:

```sh
omztty ai context
```

Inside the preset shell:

```zsh
zai context
```

The result is one `zshard.context.v1` JSON object:

| Field | Meaning |
| --- | --- |
| `cwd` | Current working directory |
| `shell`, `shell_version` | The active zsh runtime |
| `last_exit` | Recorded prior status in the interactive shell |
| `capabilities` | Available context, command staging and ssmcp interfaces |
| `history_included` | `false` |
| `environment_included` | `false` |

It does not read file contents or emit the previous command. A fresh standalone process starts with `last_exit` set to 0. The directory path is included when you send a request to a provider.

## Connect a workspace

```sh
omztty ai connect
```

This starts the bundled ssmcp in the current directory. Inside the preset shell, `zai connect` provides the same handoff and forwards supplied arguments to ssmcp.

Use the [ssmcp 0.10.20 connection instructions](https://github.com/LIghtJUNction/ssmcp/tree/v0.10.20) when connecting an AI client. Model selection and account setup stay with that client.

## Use a provider

Set `ZSHARD_AI_COMMAND` to a zsh argv array in [local.zsh](configuration.md#configuration-files). Each array element becomes one argument. The provider receives the context and request on standard input.

You can inspect that transport locally with the standard `cat` command:

```zsh
ZSHARD_AI_COMMAND=(cat)
zai ask 'Show the request envelope'
```

This diagnostic echoes the request; it does not call a model. For regular use, replace the array with your installed provider CLI and its documented stdin arguments.

After configuring a provider, use `zai ask` inside the preset or `omztty ai ask` from another shell:

```sh
omztty ai ask 'Explain this directory context'
```

The launcher reads the persistent provider configuration. Returned text is displayed without automatic shell evaluation. A provider's authentication, pricing and own context behavior remain part of that provider.

## Stage a command

In an interactive preset shell:

```zsh
zai propose 'git status --short'
```

The command is put into the editing buffer. Review, edit or cancel it; pressing Enter executes it. Staging requires an interactive TTY and a single printable command line.

## Runtime boundaries

Opening a shell performs no provider request or MCP connection. The included ssmcp has its existing Rust standard-library and networking dependencies and runs when requested. A live AI session has a different memory footprint from the idle terminal measurements.

The [AI contract](https://github.com/LIghtJUNction/zshard/blob/v0.2.0/docs/plugins.md#ai-contracts) defines argument handling and context fields. The `cat` example above checks the local request format; a real provider requires its own setup.
