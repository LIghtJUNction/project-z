# zuse PR2 原始证据溯源

**结论：已恢复部分原始验收证据，完整来源链仍未闭合。** 本次只有读取、哈希计算和文本原件复制，没有构建、测试、GUI、源码或 ref 修改；当前 a1 发布组合不变。

## 已核实

原始工作树位于 `/home/lightjunction/Documents/GITHUB/project_z/dist/worktrees/zuse-scoped-mice-20261121`。读取时 HEAD 为 `bb838b3573d36ff559c4c901ae7a64a0dd30a2bd`，tree 为 `285dcbe660ee410338a3bbeaf2153bd43862b77b`，工作区干净。实现提交 `81b5225644e971019d1e8e61e89ffe6694c45a8d` 到该 HEAD 仅变更两份文档；这能证明两个提交的实现相同，但不能替代验收当时的源码快照。

下表路径均相对于该工作树的 `target/`。

| 原件 | 本次独立读取结果 | 尚缺的来源字段 |
| --- | --- | --- |
| `scoped-validation-final/wayland-final.json` | Hyprland 0.57.2 的 7 组均为 ok；记录 ELF SHA 为 `17d0a686…`，隔离与恢复字段完整。移除 4 个私有运行身份字段后，与已提交 JSON 的 wayland 部分完全一致。 | 外层 argv/exit、原始 ELF、源码到产物清单 |
| `scoped-validation-final/cli-native.log` | 与已提交 CLI 摘要完全一致；基线 6 设备，SIGINT/SIGTERM 清理分别 5/3 ms，子进程预期退出码 1。固定 helper 仅在检查及清理完成后输出 pass。 | 原始 --binary 路径和外层退出记录；该 stdout 没有源码或 ELF 哈希 |
| `scoped-validation-final/accessibility-native.log` | Cargo 原始输出明确 1 passed / 0 failed / 0 ignored，1.17 s；含实际测试二进制路径。该文件仍存在，当前哈希为 `e2399efb…`。 | 运行时的产物哈希与源码清单；现在存在并不能证明历史上未被替换 |
| `native-fixtures/cage-v6/receipt.json` | Cage 源码包与实际 Cage ELF 仍在；本次哈希分别与原 receipt 的 `6dc16196…`、`5fd303a5…` 完全相符。 | 这证明测试环境组件的保留状态，不补足 zuse 本身的源码到产物链 |

两次此前 Wayland 失败保持原样：Weston 的协议版本阻断，以及 Cage 环境尚无唯一 main keyboard 导致输入被拒绝。没有把这些失败覆盖为最终通过。

## 未闭合的部分

在上述精确目录、既有 cloud 报告及已知产物路径中，未找到 **286 Rust / 20 no_std / 2 项 MPX** 的原始 Cargo 输出，也未找到 fmt、Clippy 和五个交叉目标的逐命令原件。这些数值仍只能按作者已发布摘要引用。CLI 和 AT-SPI 是另外的夹具，不能补作那两项 MPX Rust 测试。

共享路径 `/var/tmp/project-z-cargo-target/debug/zuse` 当前实际 SHA 为 `04deac62ad725723f36d99baafa95591778d3b1742fccbbfc9ced2dd269003b0`，不等于原验收的 `17d0a6867ee3dc9d176b5d8c3921069e51f06648c29459083cee16084f326c0b`。`zuse.d` 仍写着原 PR2 工作树；这一陈旧依赖文件不能证明当前 ELF 就是原产物。

对现有 zuse client 的一次只读 recent-jobs 查询在 5 秒后超时，没有取得记录，未重复查询。没有全盘搜索或读取无关会话。Root 已确认原作者不在当前 roster。

## 原作者仍需交付

1. 286/20/MPX2 及格式、Clippy、跨平台检查的原始 stdout/stderr、argv、cwd、环境与退出记录。
2. 将当时源码树、Cargo.lock 与 `17d0` ELF/测试可执行文件关联起来的原始构建清单；若在提交前验收，应提供可与 `81b5225` 比较的源码快照。
3. 原始 `17d0` 产物或已有不可变归档位置；若已丢失，应明确历史产物校验的缺口。新构建不能补写成历史原件。
4. CLI/Hyprland 原作业的完整命令与退出记录，以及任何既有外部归档 ID/哈希。

本次恢复的 12 份文本原件已复制至同目录 `zuse-pr2-original-evidence/`，逐字节长度和 SHA-256 全部与开发机原件一致；完整路径和哈希见该目录 `manifest.json`。完整审计见 `zuse-pr2-original-evidence-provenance.json`。PR3 的测试与产物没有混入本次 PR2 来源证明。

固定来源：[PR2](https://github.com/LIghtJUNction/zuse/pull/2)、[验收文档](https://github.com/LIghtJUNction/zuse/blob/bb838b3573d36ff559c4c901ae7a64a0dd30a2bd/docs/validation-scoped-mice.md)、[已提交摘要](https://github.com/LIghtJUNction/zuse/blob/bb838b3573d36ff559c4c901ae7a64a0dd30a2bd/docs/evidence/scoped-mice-native-2026-11-21.json)。
