# Memory and Swap

zmem is the suite's default system memory manager. The release installer sets it up with administrator privileges, enables `zmem.service`, and hands management of existing Swap to zmem. The terminal, shell and AI tools use the same system policy.

## See what the system is doing

```sh
omztty memory
omztty memory status --json --processes
omztty memory plan --json
omztty memory doctor --json
```

Status reports available RAM, Swap, pressure and process usage. The plan explains the current policy decision. JSON output gives AI tools the same measurements and decisions as the command line. `omztty doctor` also shows whether the system memory service is active.

zmem observes how long tasks wait for memory, alongside available RAM and Swap. Under pressure it can prepare more disk Swap and lower the memory high-water mark of managed background jobs. It protects session memory and avoids repeatedly changing policy when pressure fluctuates.

## Keep background jobs manageable

Start a build or other background job through the managed scope:

```sh
omztty memory run --class background -- cargo build
```

Interactive work can use `--class interactive`. The `disposable` class is for work you explicitly allow to encounter a hard memory limit. Use the class before starting the process so the kernel accounts for its memory in the intended group.

The default policy preserves processes. It does not discard application data, clear the entire page cache or provide application checkpoints. Applications remain responsible for saving their documents and progress.

## Default policy

The suite ships `config/zmem/zmem.conf`. On first setup, zmem copies this policy to `/etc/zmem/zmem.conf`. Later installs preserve the existing system configuration.

| Setting | Default |
| --- | --- |
| Observation interval | 2 seconds |
| Disk Swap growth step | 2 GiB |
| Maximum managed disk Swap | 32 GiB |
| Disk space kept available | 8 GiB |
| Target free Swap | 4 GiB |
| RAM reserve | Scaled to installed RAM |
| New zram capacity | 50% of RAM |
| Session protection | Enabled |
| Swappiness management | Enabled |
| Profile | Balanced |

Edit `/etc/zmem/zmem.conf` with administrator privileges, then restart `zmem.service`. Existing occupied Swap stays active during adoption; the configured zram layout applies when zmem initializes a device at boot. The [zmem documentation](https://github.com/LIghtJUNction/zmem) defines the configuration keys, policy limits and recovery behavior.

## Setup, updates and recovery

The normal release installation includes system memory setup. For a container, a non-systemd environment or a per-user-only installation, use:

```sh
sh install.sh --no-memory-manager
```

This skips system setup and records the choice for future updates. It does not stop an existing system manager. Enable zmem later with:

```sh
omztty memory setup
omztty update --memory-manager
```

`memory setup` installs the bundled version immediately. `update --memory-manager` also records that system memory management should be included in future suite updates. The setup command copies the executable to root-owned `/usr/local/bin/zmem`; the system service runs that copy, independently of the user-writable suite directory.

To restore the memory managers and configuration recorded before zmem took over:

```sh
omztty memory rollback
```

The system memory service has its own lifetime. Removing the per-user terminal suite keeps it available, along with `/etc/zmem/zmem.conf`. If the suite has already been removed, its recovery command is:

```sh
sudo /usr/local/bin/zmem rollback
```

Package-managed installations can use `omztty memory setup` when their bundle includes zmem. Their ordinary runtime updates continue through the distribution's package manager.
