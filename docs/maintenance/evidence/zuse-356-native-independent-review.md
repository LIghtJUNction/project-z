# zuse 356 私有原生验收独立复核

**结论：未发现实质不一致，0 项阻断。** 本复核只读取既有原件与源码夹具，没有启动构建、输入、GUI 或运行时，也未更改源码、refs 或 main/a1 下游组合。

## 来源与执行

固定源码 `35664746549c482c99082e6180419b2c0f5ff532`，tree `0d1d19006dfcf4da8e804f1f27d13d284eb96299`。原始 ZIP **50,905 B**，SHA256 `6e2822aabf6f730d60582eb22feff4d025d607fcc0bb81d0be3a4fd31beda3c5`；**73 份 payload＋1 份 manifest＝74 members**，CRC、全部文件大小/哈希及解出原件一致。

唯一原生作业 `26c4545eae1eab8d27485f4a48077d3c-7c9` 实际 exit 0、running false、双 EOF；supervisor 13.107 秒，结果回执起止 13.039921 秒，六条命令记录用时合计 12.812 秒。这些是不同计时边界，并非三次运行。[原始结果](zuse-356-native-evidence/native/result.json) · [最终状态](zuse-356-native-evidence/execution-native-status.json)

| 实际命令 | 原件中的结果 | 范围 |
|---|---|---|
| private-mpx | 2 passed，0 failed/ignored，133 filtered | 恰好两项 MPX 测试；env1、私有认证 Xvfb |
| private-cli | 工作流通过 | 默认独立指针、显式释放、正常退出、SIGINT/SIGTERM 取消 |
| private-accessibility | 1 passed，0 failed/ignored | 私有 D-Bus、认证 Xvfb、GTK/AT-SPI |
| private-wayland | 7 组全部 ok | 私有 headless Cage 0.3.1＋Hyprland 0.57.2 |
| private-serial | 5 组 passed | 自有内核 PTY、合成字节、termios 恢复 |
| private-usb | 11 组 passed | CLI 子进程选择合成 C libusb ABI |

## 关键核对

- MPX 实际调用使用 `ZUSE_TEST_PRIVATE_X11=1`、DISPLAY `:18292` 与 0600 Xauthority，WAYLAND_DISPLAY 已移除；选中清单与测试日志都只有两个指定函数。固定辅助脚本先认证 `xdpyinfo`，并要求两项实际完成。[MPX 原件](zuse-356-native-evidence/native/mpx/result.json)
- CLI `7a6a6d995b3a1b77…`、lib-test `e36daa4146c197cd…`、AT-SPI `d6e9f46a49db84ce…` 与 portable 的实际 `fresh=false` compiler-artifact、哈希及自有副本对应。原生前置回执核了六个自有/共享位置，门禁在结束前再次检查其哈希；本次独立复核没有读取 ELF 本体。
- AT-SPI 的真实嵌套命令为 `cargo test --offline --manifest-path … --test accessibility_native -- --ignored --nocapture`，**没有 `--locked`**。Cargo.lock 前后同为 `cffb29f3…`，源码前后 clean；原日志还有三个根 crate 的实际 rustc 调用。不能把空的 JSON compiler-artifact 列表误读成未编译。[实际 Cargo argv](zuse-356-native-evidence/native/cargo-invocations.jsonl)
- Wayland 回执证明私有 socket、renderD129、0 physical input/KMS FDs，以及无 host display 连接或指针/焦点查询。**本轮未保留成功路径的 private.log，也没有 GL renderer 名，不能称重新观测到 llvmpipe/swrast 或软件渲染身份，更不能推广到物理 GPU。** 这项表述收窄已与执行者确认。[Wayland 原件](zuse-356-native-evidence/native/wayland.json)
- USB 有 38 份 trace：16 份非空均以合成库 load 开始、unload 结束，22 份前置拒绝路径为空；这与 11 个验证组不同。串口和 USB 均声明没有打开物理设备。
- `00:18:00.868464 UTC` 的后置记录为 scope inactive/dead、Result success、ControlGroup 空；9 个记录的自有 PID 均已消失，MPX lease/auth 已清理，原外锁 inode 63537699 无持有者或等待者。MemoryPeak 未记录；本复核未重新探测当前锁。[清理原件](zuse-356-native-evidence/native-postflight.json)

## 计数与合入边界

portable 的 **289 passed / 5 ignored** 保持原始口径；两项 MPX 已包含在其中的受保护早返回条目里，本轮补上真实私有环境覆盖，**不能写成 291 unique**。AT-SPI 本轮显式执行了一项原 ignored 测试，也不改写旧回执。Wayland/PTY/USB 组数、此前重叠的 16 项定向测试和 no_std 20 均不合并成唯一单元测试总数。

这些原件与已有 portable、P2 RED/GREEN 和静态复核共同支持对固定 356 修复作合入决定；不等于已验证后续 merge、main/a1 下游、正式发布或 final44。

[机器可读复核](zuse-356-native-independent-review.json) · [原件哈希索引](zuse-356-native-independent-review-original-hashes.json)
