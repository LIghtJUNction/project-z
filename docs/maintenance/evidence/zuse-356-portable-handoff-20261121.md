# zuse 356：portable 验收

固定候选 `35664746549c482c99082e6180419b2c0f5ff532`（树 `0d1d19006dfcf4da8e804f1f27d13d284eb96299`）已完成这轮 portable 验收。原作业 `26c4545eae1eab8d27485f4a48077d3c-6dc` 实际退出 0，用时 61.129 秒。PR3 保持草稿，PR2、主线和冻结的下游来源未变。

## 实际结果

| 门禁 | 本轮结果 | 范围 |
|---|---|---|
| 默认 `cargo test --offline --locked` | 289 passed，0 failed，5 ignored | 含 doc-test 阶段；两个 private_x11 条目因未开启私有 X11 环境而提前返回，不能作为 MPX 通过证据 |
| `cargo test --offline --locked --no-default-features` | 20 passed，0 failed，0 ignored | 包含 `tests/core.rs` 的 17 项；未用 `--lib` 截断 |
| 无默认特性编译检查 | 本机、wasm32 均退出 0 | 仅库编译 |
| 四个平台 `check --all-targets` | Windows GNU、macOS x86/ARM、Linux ARM 均退出 0 | 编译检查；Linux ARM Rust target 本轮安装成功 |
| `clippy --all-targets -- -D warnings` | 退出 0 | 25 个候选根目标实际重新 lint，compiler-artifact 均 `fresh=false` |

既有 16 项窄回归已被默认测试覆盖，不与 289 累加；no_std 是第二种特性配置，也不作为独立新增总数。原作者历史 286/20 摘要及旧 17d0 二进制不用于证明本次候选。

## 源码、产物与资源

整个批次只取得一次非阻塞共享外锁。驱动在运行时读到父 `flock` PID 2585341 与 `/proc/locks` 中 inode 63537699 的实际所有权。源码运行前后均为同一干净提交，`Cargo.lock` SHA256 始终为 `cffb29f3aa454c065523c6fc62ebf33721694df88af94e0aff2feea5d17855e0`。本轮原始命令、cwd、日志哈希和 compiler-artifact 路径均在 JSON 回执内。

CLI、库测试和 AT-SPI 测试产物均由本轮 `fresh=false` 记录定位，并在持锁期间复制到本任务证据目录。CLI 为 17,454,624 字节，SHA256 `7a6a6d995b3a1b77e2cd5d4ea585e72e5c170e338e333d85684ec2dbca9b864b`。副本权限 0500，读回哈希一致；这些二进制没有写入 Git。

23:40:47 UTC 的回收检查确认 scope 为 inactive/dead，Result=success，ControlGroup 为空；原 supervisor 与 flock 已退出，外锁没有 holder/waiter。2 GiB RAM、2 GiB swap、单 CPU 配额和单 Cargo job 是设置上限；瞬态 scope 已回收，未取得峰值内存，不能把上限当峰值。

## 尚未执行

私有 MPX、scoped-mice CLI、AT-SPI、Cage/Hyprland、PTY 和合成 libusb 六组原生验收仍待独立窗口。本轮未向宿主桌面发送输入，也未运行 SSMCP 门禁。

本文件依据同目录 `zuse-356-portable-handoff.json` 和 `zuse-356-evidence/portable/result.json`；启动、退出、锁、源码及产物均有原始回执，不把新验证记到历史候选上。
