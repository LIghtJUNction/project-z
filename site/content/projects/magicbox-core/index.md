# MagicBox

MagicBox 是给应用和网关使用的 Rust 代理。客户端在同一个回环端口接收 SOCKS5 CONNECT 和 HTTP CONNECT。它通过选定上游转发目的地址。服务端提供经过证书验证和用户认证的 HTTPS CONNECT，并用 DNS-over-TLS 解析域名。两个角色共用一个二进制文件。

## 客户端

安装 Rust 1.99.1 或更新版本，在仓库里执行以下命令。

~~~sh
cargo build --locked --release --bin magicbox
~~~

在私有文件 client.toml 中填入你的代理地址、证书域名和凭据。下面使用文档保留地址。

~~~toml
upstream = "https://alice:REPLACE_WITH_PASSWORD@192.0.2.10:8443?server_name=proxy.example"
~~~

~~~sh
chmod 600 client.toml
magicbox check client.toml
magicbox run client.toml
~~~

客户端就绪后在标准错误输出 ready 和实际监听地址。默认监听 127.0.0.1:1080。可通过 listen 字符串选择其他回环 IP 和端口。使用支持远端解析的应用连接这个端口，例如以下 curl 命令。

~~~sh
curl --proxy socks5h://127.0.0.1:1080 https://example.org/
~~~

| 上游方案 | 身份与传输 |
| --- | --- |
| https | TLS 验证公开 CA 和服务端名称。域名节点默认验证原始节点域名，数字 IP 节点默认验证证书的 IP SAN。可选 HTTP Basic 凭据位于 TLS 内 |
| socks5 | 支持无认证和 RFC 1929 用户名密码。远程链路上的凭据与数据使用明文 |
| http | 支持 HTTP CONNECT 和可选 Basic。远程链路上的凭据与数据使用明文 |
| ss | Shadowsocks AEAD TCP 客户端，支持 aes-128-gcm、aes-256-gcm、chacha20-ietf-poly1305；与 Debian shadowsocks-libev 实测互通 |

上游可填写数字 IP 或完整域名。导入订阅和检查配置均在离线状态完成。启动域名节点时，核心向数字地址指定的 DNS-over-TLS 服务发送 A 和 AAAA 查询，两个查询共用一次发送和 5 秒限时。默认解析器为 1.1.1.1，验证 cloudflare-dns.com，可通过 MAGICBOX_RESOLVER 指定其他可信的 tls://IP:PORT?server_name=NAME。解析器能看到被选节点的域名。核心只接受可路由的公网结果，排除本机接口地址，固定结果直到重启。每次连接在原握手限时内尝试其他可用 IP。解析或证书验证失败会终止对应操作。内网和 Tailscale 服务可显式填写数字 IP。

用户名与密码中的 URI 特殊字符可以百分号编码。私有 CA 通过 MAGICBOX_CA_BUNDLE 指定 PEM 文件。配置不含 upstream 时，监听器可以启动，所有转发请求都会被拒绝。上游连接失败时，客户端向本地应用返回失败。

## 运行自己的代理服务器

准备可验证的证书链、对应私钥和一个只允许服务账户读取的凭据文件。下例创建随机密码，凭据保存在单独文件中。客户端配置使用相同的用户名与密码。

~~~sh
umask 077
printf 'alice:%s\n' "$(openssl rand -hex 24)" > credential
~~~

把路径改成服务器上真实的文件位置。显式设置公开监听地址后，能访问该 TCP 端口的客户端都可以发起 TLS 握手。连接目标需要通过用户名与密码验证。

~~~toml
listen = "0.0.0.0:8443"
certificate = "/etc/magicbox/fullchain.pem"
private_key = "/etc/magicbox/privkey.pem"
credential_file = "/etc/magicbox/credential"
~~~

~~~sh
magicbox check-server server.toml
magicbox serve server.toml
~~~

服务端默认通过 1.1.1.1:853 使用 TLS 向 Cloudflare 查询 A 和 AAAA，验证 cloudflare-dns.com。上游 DNS 服务能看到所查询的域名。使用其他解析器时，设置 resolver 为 tls://IP:PORT?server_name=NAME。DNS 响应需要匹配原请求的事务、名称、类型和类别。服务端只使用目标名称及其 CNAME 链的地址，逐个检查并连接数字 IP。请求解析失败会终止这次转发。

服务端限制外连目的地址，拒绝回环、私网、链路本地、运营商共享地址、组播和常用保留网段。认证在 DNS 查询和目标连接之前完成。客户端与服务端各允许 128 个并发会话。握手结束前共用 10 秒截止时间，空闲转发连接的超时时间为 5 分钟。

## Linux 与 Android 的透明 TCP 入口

通过以下命令复用已有客户端配置。管理员在 netfilter 中选择应用 UID 或热点接口后，将该范围的 IPv4、IPv6 公网 TCP 连接 REDIRECT 到指定端口。入口从内核连接跟踪记录读取原始 IP 和端口，转发前检查目标策略。普通连接直接访问监听端口时会被关闭。

~~~sh
magicbox redirect client.toml 19870
~~~

监听成功会输出 ready [::]:19870。端口同时服务 IPv4 和 IPv6。此入口只处理由宿主规则实际送达的 TCP，不安装系统规则。原始 IP 没有域名信息，按域名匹配的规则仅能用于显式提供域名的连接。端口 53、私网、回环和常见保留地址不会从此入口出站。系统解析器代查、独立的 UDP 流和其他应用流量需要各自的宿主策略。独立应用配置 DoH 时，HTTPS 连接可以跟随选定的 TCP 路径。入站流量保持端到端加密语义，MagicBox 不签发代理证书。

## 订阅与规则

尚未选择代理时，可以用 fetch 下载第一个 HTTPS 订阅。URL 可以通过标准输入传给进程，避免令牌出现在命令行参数中。下载在证书验证、完整读取和大小检查通过后才产生标准输出。

~~~sh
umask 077
printf '%s\n' "$SUBSCRIPTION_URL" | magicbox fetch - > feed.txt
~~~

首次下载使用与服务端相同的加密 DNS 默认值，并限制到公网目的地址。可用 MAGICBOX_USER_AGENT 设置自定义 UA，或用 MAGICBOX_RESOLVER 指定自己的 TLS 解析器。下载上限为 2 MiB，总时限为 20 秒。最多跟随三个 HTTPS 重定向，逐跳验证证书和目标地址。自定义 UA 仅发往起始站点。支持定长、分块和以连接关闭划定边界的响应。下载请求指定 identity 内容编码。

~~~sh
magicbox import --list feed.txt
umask 077
magicbox import --select 1 feed.txt > client.toml
magicbox check client.toml
~~~

导入器读取本地文件或标准输入，支持 URI 列表、一次 Base64 或 Base64URL 包装，以及受支持的 Clash/Mihomo、sing-box 格式的 JSON 或 YAML 节点。列表显示编号、协议、可用状态和经过清洗的节点名称。选择节点会输出包含真实凭据的 TOML。无法保留协议或证书语义的节点显示为 unavailable。

MAGICBOX_BLOCKLIST 指向经过排序的精确域名规则文件，首行为 magicbox-exact-v1，随后每行一个小写域名。进程在启动时验证并载入整份规则。内置策略拒绝 localhost、local、home.arpa 及其子域。外部规则按完整域名匹配。

## 作用范围

代理路径内的域名通过 SOCKS5 域名字段或 CONNECT 的目标名称交给上游。应用自行解析后交给代理的 IP 已经失去原域名信息。应用绕过代理的连接由宿主网络策略决定。核心本身无需修改设备路由、系统 DNS 或防火墙。HTTPS 保护到代理服务器的链路；代理服务器能够看见转发目的地。

可选的 Linux cgroup eBPF DNS 守卫按指定 cgroup 生效。操作方式和覆盖边界见 [DNS guard](docs/dns-guard.md)。

SOCKS5 上游还支持 RFC 1928 UDP ASSOCIATE。应用须保留控制连接并使用协商的本地 UDP 中继。核心检查数据报端点、目的地址及域名规则，关闭控制连接时撤销关联。当前没有通用 TUN、透明 UDP 路由或 Shadowsocks UDP。Shadowsocks 插件、AEAD-2022、VMess、VLESS、WireGuard、Hysteria2 和 TUIC 等仍待实现。受支持的主要部署目标为 Linux 和 Android。Android 模块、规则下载与增量更新由 MagicNet 集成仓库提供。

## 验证和测量

~~~sh
cargo fmt --all -- --check
cargo clippy --locked --all-targets -- -D warnings
cargo test --locked
cargo build --release --locked --bin magicbox
python3 tests/tunnels.py target/release/magicbox
python3 tests/dns_path.py target/release/magicbox
python3 tests/udp.py target/release/magicbox
sudo sh tests/netns.sh target/release/magicbox
sudo python3 tests/redirect_kernel.py target/release/magicbox
python3 tests/bench.py target/release/magicbox
python3 tests/compare.py target/release/magicbox /path/to/reference/sing-box
~~~

集成测试需要 Python 3、OpenSSL 和 C 编译器。测试会生成一次性 CA，验证错误证书、认证失败、上游断开、双向数据、半关闭以及使用加密 DNS 的完整客户端与服务端链路。测试将一个指定的公开 IP 映射到本地回显服务，便于普通 Linux 用户运行。

DNS 路径测试优先使用 strace 观察 socket 和 connect 系统调用。在禁用 ptrace 的环境中使用 libc 插桩，并在输出标明观察层次。性能脚本使用本地持续 TCP 连接，记录吞吐量、请求往返延迟及 Linux 进程峰值 RSS；compare.py 在相同的回显负载下轮换运行 MagicBox 和给定的 sing-box 二进制。实际网络、规则规模、并发数和代理协议均会改变测量结果。

## 一次可重复的对照测量

在同一台离线 Debian 虚拟机中，包含透明 TCP 入口、命名上游与独立 DNS 报文库的 MagicBox 构建和参考版本各启动七个独立进程，交替测试。每轮建立一条 SOCKS5 到 SOCKS5 的回环 TCP 隧道，完成 100 次单字节往返与 32 MiB 单向上传。虚拟机采用 QEMU TCG 软件模拟、两个虚拟 CPU 和 360 MiB 内存，未加载外部规则集。表中每项都是七轮中位数。

| 检测项 | MagicBox 0.1.0 | sing-box 1.14.4 |
| --- | ---: | ---: |
| 上传吞吐量 (MiB/s) | 97.11 | 118.09 |
| 单字节往返 p50 (µs) | 421.48 | 955.45 |
| 单字节往返 p95 (µs) | 590.83 | 1355.29 |
| 单进程峰值 RSS (KiB) | 2964 | 55932 |

这组测量中，MagicBox 的单连接内存与往返延迟较低，sing-box 的批量上传吞吐量较高。软件模拟会改变系统调用和 CPU 的相对成本。实机多连接、加密传输、热点转发与加载规则后的性能需要独立测量。逐轮读数、内核、参考发行版和二进制摘要保存在 [原始数据](docs/bench-qemu.json)。

## 独立 DNS 报文库

[magicbox-dns-wire](crates/dns-wire) 提供 A、AAAA 查询编码和响应校验，可单独作路径依赖。该组件只使用 Rust 的 core 和 alloc，在空 Cargo 缓存中也能离线测试。传输层的 TLS 身份校验与超时由调用方负责。
