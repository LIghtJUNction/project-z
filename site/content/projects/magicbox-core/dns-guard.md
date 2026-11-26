# Scoped DNS guard

Use `magicbox-dns-guard` when launching a workload in a dedicated cgroup v2. The Linux kernel rejects new TCP and UDP connections to destination ports 53 and 853 for that cgroup and its descendants. It also checks the destination of unconnected UDP sends. The workload can resolve names through a proxy that accepts hostnames, such as MagicBox's SOCKS5 listener.

The foreground process needs privileges to load cgroup socket-address eBPF programs. Select an existing, empty child cgroup. Start the guard and wait for the line `ready` before the supervisor places workloads in the group. The command checks the mount identity, refuses symlinks and leaves process placement to the supervisor.

```sh
cargo build --release --locked --bin magicbox-dns-guard
sudo ./target/release/magicbox-dns-guard attach /sys/fs/cgroup/my-proxy-workload
```

Four eBPF links cover IPv4 and IPv6 connect and UDP send-message operations. All links share one activation flag. The process switches that flag only after the kernel accepts all four links. A failed attach closes the links created during that attempt. SIGTERM or SIGKILL releases this guard's links. A supervisor that requires continuous protection should tie the workload lifetime to the guard lifetime.

Traffic on other ports keeps its original policy, including HTTPS on port 443. Resolver requests delegated to a separate system service follow that service's cgroup. Hotspot forwarding, traffic outside the selected hierarchy, inherited already-connected descriptors and application DNS on arbitrary ports require separate coverage. Android availability depends on its kernel configuration, cgroup layout and SELinux policy.

## Reproduce the kernel test

Use a disposable Linux VM with cgroup v2 mounted and `CONFIG_CGROUP_BPF=y`. The harness creates a unique empty cgroup, checks actual socket results on loopback, and removes its cgroup at exit.

```sh
cargo build --release --locked --bin magicbox-dns-guard
cc -O2 -Wall -Wextra -Werror tests/dns_guard_probe.c -o /tmp/magicbox-guard-probe
sudo unshare --net --mount --propagation private sh tests/dns_guard.sh \
  "$PWD/target/release/magicbox-dns-guard" /tmp/magicbox-guard-probe
```

A QEMU TCG guest running Debian Linux `6.12.117+deb13-cloud-amd64` passed 144 socket checks. Each phase exercised IPv4 and IPv6, TCP connect, UDP connect and unconnected UDP sendmsg on ports 53, 853, 443 and 5353. The harness exercised a selected group, its child, an outside process, two concurrent guards, signal cleanup, and a deliberately failed second link. It also verified refusal of the cgroup mount root, an ordinary directory, a symlink, a relative path, and an occupied cgroup.
