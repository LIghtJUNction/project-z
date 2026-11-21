# zuse 356：私有原生验收

固定候选 `35664746549c482c99082e6180419b2c0f5ff532`、树 `0d1d19006dfcf4da8e804f1f27d13d284eb96299` 的六组私有原生验收全部通过。唯一执行批次为 `26c4545eae1eab8d27485f4a48077d3c-7c9`，退出 0，墙钟 13.107 秒。这是功能验收耗时，不是性能基准。

源码运行前后干净且身份一致。PR3 仍为独立修复分支；本次验收没有合并 PR2/PR3，也没有更新 SSMCP 或 ztype 的冻结来源。

## 实际执行结果

| 范围 | 本轮结果 | 证据边界 |
|---|---:|---|
| MPX | 2 项真实测试通过 | `ZUSE_TEST_PRIVATE_X11=1`，认证私有 Xvfb，Xauthority 权限 0600，精确选中原两项测试 |
| 私有 X11 CLI | 全部场景通过 | 独立鼠标、显式 user opt-in、正常退出，以及 SIGINT/SIGTERM 取消与资源回收 |
| AT-SPI | 1 项显式启用测试通过 | 私有 DBus/Xvfb/GTK；原 helper 的嵌套 Cargo 没有 `--locked`，实际 argv 和前后未变的锁文件均已保留 |
| Wayland | 7 组通过 | 自有 headless Cage 0.3.1 和私有 Hyprland 0.57.2；文本、后台不改焦点、截图、键盘状态拒绝与允许的 Num-on 前台快捷键 |
| 串口 | 5 组通过 | 自有内核 PTY；256 字节双向传输、超时、部分写入停止、termios 恢复及输入前预检 |
| USB | 11 组通过 | 合成 libusb C ABI；设备选择、传输、部分效果、超时、失败清理和预检，没有打开物理 USB 设备 |

MPX 两项在此前 portable 289 条通过记录中只是无 opt-in 的提前返回。本轮补齐了它们的真实执行，不能把总数写成 291 项独立测试。AT-SPI 原先属于五条 ignored 记录之一；本轮只补齐这一项。其余夹具的分组数量不与 Rust 测试条目相加。

## 源码与产物

运行使用此前 portable 批次实际重新编译并在持锁期间复制的 CLI `7a6a6d995b3a1b77e2cd5d4ea585e72e5c170e338e333d85684ec2dbca9b864b` 和库测试产物 `e36daa4146c197cdbf7822d06220561543dd8d168c4f8810e5966c202568e4fb`。本轮在运行前后核对了独立副本及共享输出的全部哈希。AT-SPI 的实际运行路径同样与保留的编译产物记录相符，运行后字节哈希不变。

`Cargo.lock` 的 SHA256 始终为 `cffb29f3aa454c065523c6fc62ebf33721694df88af94e0aff2feea5d17855e0`。没有重跑 portable 批次，也没有用这次结果补写原 PR2 缺失的 286/20 或旧 `17d0` 产物来源链。

## 隔离与回收

整个批次只取得一次非阻塞外锁。驱动实际观察到父 `flock` PID 3188303 对共享锁 inode 63537699 的内核所有权。独立 postflight 确认 scope 为 inactive/dead、Result=success、ControlGroup 为空，记录中的自有进程均已退出，内核外锁记录为空。MPX 的 Xauthority 和显示号 lease 均已移除。

Wayland 原始回执直接证明没有连接或查询宿主桌面的焦点与指针，physical-input/KMS 文件描述符为 0。回执没有保留 GL renderer 名，因此不声称本轮重新观测到了 llvmpipe/swrast，也不推广为物理 GPU 或真实硬件输入验收。2 GiB RAM、2 GiB swap、单 CPU 配额和单 Cargo job 是配置上限；本轮没有取得峰值内存。

## 原始记录

[文本证据包](https://drive.google.com/file/d/1_4o5_1MuigO8fMdlw7hOd67TZvW6yP6l)包含 73 份文本载荷和 1 份清单，共 74 个 ZIP 成员。包大小 50,905 字节，SHA256 `6e2822aabf6f730d60582eb22feff4d025d607fcc0bb81d0be3a4fd31beda3c5`；上传后已下载并逐字节核验。包内含六组命令与日志、实际启动/结束快照、编译产物来源、测试选择、源码夹具哈希及清理回执，不含二进制或截图。

来源：[固定源码](https://github.com/LIghtJUNction/zuse/commit/35664746549c482c99082e6180419b2c0f5ff532)、[独立修复 PR3](https://github.com/LIghtJUNction/zuse/pull/3)。逐命令退出状态和全部原件路径见同名 JSON 交接记录。
