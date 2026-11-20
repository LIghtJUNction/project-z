# zuse 0.2.2：消费者与 Project Z 源码传播回执

日期：2026-11-20（UTC）

本次已完成 zuse 0.2.2、ztype 正式 registry 消费、SSMCP 已验收候选之间的源码对齐，并通过 Project Z 全量版本、依赖图和本地依赖解析检查。SSMCP 的应用主线合并、正式发布、安装部署，以及安装套件使用新资产，仍由各自现有维护会话继续完成。

## 固定的源码与依赖

| 位置 | 本快照固定提交 | 含义 |
| --- | --- | --- |
| `zuse` | `94c837551a7a2fd8ec9f577a3e2f57309bd5ce5a` | 正式 `zuse-computer 0.2.2` 源码 |
| `ztype` | `12e8a458d69b222a001a9e479823b65da840db6b` | 已进入 ztype main 的 registry 消费提交 |
| `ssmcp` | `bfe5f25ffab718f100b11d2ce55c8dc839cbad71` | 已验收的独立候选分支 `deps/zuse-0.2.2-20261120` |
| `ssmcp/crates/zuse` | `94c837551a7a2fd8ec9f577a3e2f57309bd5ce5a` | 与顶层 zuse 相同的源码 |
| `oh-my-ztty` | `0fdc87873c53e7c87d18952f83a7b94fc4149de5` | 保留原快照；安装资产尚待传播 |
| `zrc` | `ef8bd9571e206c8086e38b9dcbdc760a466b5133` | 保留原快照；实际 PATH 调用验收尚待维护 owner |

ztype 的 manifest 精确要求 `=0.2.2`，真实 Cargo.lock 来自 crates.io；其余 15 个 lock 包条目保持不变。实际使用的 registry 归档为 387,761 bytes，SHA-256 为 `16d3bf8c73bf64721672bf0483899b796967c8d3b53fa0ea934b3e705d6e2fde`。官方 API、下载归档、Cargo 缓存归档以及归档内的 VCS 提交相互一致；归档和实际解包缓存的全部 32 个 `src` 文件与正式源码逐字节一致。详见 [ztype registry 证据](https://github.com/LIghtJUNction/ztype/blob/12e8a458d69b222a001a9e479823b65da840db6b/docs/evidence/zuse-0.2.2-registry.json)。

SSMCP 候选基于原已验收源码 `785e6b00440b048d00d9da626a33defa99108afe`，只改 manifest 的精确版本、真实 Cargo.lock 和 `crates/zuse` gitlink，合计 3 行增加、3 行删除。其 Cargo 使用 path 依赖，因此 lock 的该包条目没有 registry checksum；可复现性由精确 manifest、lock 版本和 gitlink 共同确定。详见 [SSMCP 候选提交](https://github.com/LIghtJUNction/ssmcp/commit/bfe5f25ffab718f100b11d2ce55c8dc839cbad71) 和本库保存的 [消费者验收证据](../evidence/2026-11-20/ssmcp-zuse-0.2.2-consumer.json)。

## 消费者实际验收

| 范围 | 结果 | 解释 |
| --- | --- | --- |
| ztype 严格 Clippy、app 与 kana 插件构建 | 通过 | 使用正式 registry 包 |
| ztype Rust 测试 | 13 通过、0 失败 | composition 10 项、plugin 3 项 |
| ztype CLI 与插件验收 | 14 / 14 通过 | 实际应用和插件执行 |
| ztype Linux GTK 验收 | 11 / 11 通过 | 私有 X11 环境，最终精确接收 96 UTF-8 bytes |
| ztype macOS arm64 的 desktop、plugins 类型检查 | 通过 | `--no-default-features --features desktop,plugins`，仅编译检查 |
| ztype 完整 macOS GUI | 未验证 | Linux 交叉环境缺少 Objective-C `cc1obj`，既有 zui-native 构建受阻；未替换 build script 或制作假库 |
| SSMCP Linux 应用构建 | 通过 | `cargo build --offline --locked --bin ssmcp` |
| SSMCP zuse 后端契约 | 12 通过、0 失败、2 忽略 | 过滤器 `computer::zuse_backend`；两个被忽略项是专用 fixture 入口；不代表全部 SSMCP 测试 |
| SSMCP 原生 worker | 6 个 GTK 场景通过 | 自有 Xvfb、私有 accessibility bus、进程清理均通过 |

ztype 完整命令和环境限制见 [消费报告](https://github.com/LIghtJUNction/ztype/blob/12e8a458d69b222a001a9e479823b65da840db6b/docs/zuse-0.2.2-consumer.zh-CN.md)。SSMCP worker 另记录了 28 条运行断言，其中包含轮询、清理观察和外层 GTK 验收；这不是 28 个独立场景，不能再与 6 个 GTK 场景相加。SSMCP 验收二进制 SHA-256 为 `5a34bdd5ec623a676ea4a378213b015488b70078e7cb0be8d5ea9c271e95fe9a`。

## Project Z 一致性检查

在隔离的聚合工作树中固定上述源码后，依次执行：

```sh
python3 scripts/project_z.py sync
python3 scripts/project_z.py check
python3 scripts/project_z.py resolve --all
```

执行环境设置 `CARGO_NET_OFFLINE=true`、`CARGO_BUILD_JOBS=1`、`RUST_TEST_THREADS=1`，命令以 `nice -n 19` 运行。原始退出码、输出、时间和生成文件 SHA-256 收入 [聚合验收 JSON](../evidence/2026-11-20/zuse-0.2.2-propagation.json)。

| 命令 | 退出码 | 实际结果 |
| --- | --- | --- |
| `sync` | 0 | 更新 42 个仓库、60 个包的目录 |
| `check` | 0 | 42 个仓库、60 个包的版本与依赖图一致 |
| `resolve --all` | 0 | 36 个仓库的本地依赖解析成功 |

验收前后，99 个递归源码工作树均干净且 HEAD 未变化；139 个 Cargo.lock / Cargo 配置对象的字节、文件模式与存在性保持不变。该 139 项计数包含聚合根的 `.cargo/project-z.toml`，只是本轮枚举范围，不是测试用例数量。`catalog.json` 和 `docs/PROJECTS.md` 由协调脚本生成；`.cargo/project-z.toml` 无需变更。源码提交改动范围为 zuse、ztype、ssmcp 三个顶层 gitlink，依赖图结构保持一致。

实际执行检查时的协调器基线为 `b9de9241bf4cb9e95fdc079a727bf947da782652`。发布前保留了并发进入 main 的文档提交，将父提交快进到 `79607a87d08937724aad371510bfe9b508ff1d85`；两者之间只改变 7 个 `docs/evidence` / `docs/reports` 文件，没有改变协调器、manifest、gitlink 或生成输入。快进后的生成文件 hash 与已验收内容相同，详见 JSON 中的 `parent_update_after_validation`。

## 尚待完成的应用与安装传播

源码依赖已能一致解析，但实际安装程序选择的是已发布资产。当前聚合所固定的 [oh-my-ztty dependencies.lock.json](https://github.com/LIghtJUNction/oh-my-ztty/blob/0fdc87873c53e7c87d18952f83a7b94fc4149de5/dependencies.lock.json) 仍固定 SSMCP `v0.10.10`。因此下一步必须沿实际交付顺序完成：

1. SSMCP 现有维护 owner 将候选变更与正在进行的应用改动组合，验收最终组合提交，再推进应用 main、正式版本和安装。候选提交在 Project Z 中固定，不等于 SSMCP main 已推进。
2. oh-my-ztty 现有维护 owner 取得该正式 SSMCP 资产后，同步 asset tag、下载 URL、实际 SHA-256 与源码 gitlink，完成真实安装验收，再推进套件版本。
3. zrc / 套件维护 owner 使用最终安装后的 PATH 完成实际 SSMCP 调用验收，记录实际可执行文件版本、来源和结果。
4. 将这些已验收提交纳入后续聚合快照，再执行 `sync`、`check` 与 `resolve --all`。

以上主线、发布和安装步骤是明确保留的后续工作；本回执只证明所列不可变源码及其实际验证结果。

## 证据自检

| 检查点 | 结论 |
| --- | --- |
| 主张与证据 | 提交、版本、checksum、命令和退出码均可追溯 |
| 数量口径 | Rust 测试、CLI 检查、GTK 场景与运行断言分别表述 |
| 范围边界 | macOS GUI、SSMCP main / release / installation 和套件传播明确保留 |
| 工作区保护 | 使用独立工作树，保留并发上游文档和所有原有 consumer lock/config |
| 后续责任 | 由既有 SSMCP、套件及 zrc 维护 owner 继续实际交付传播 |
