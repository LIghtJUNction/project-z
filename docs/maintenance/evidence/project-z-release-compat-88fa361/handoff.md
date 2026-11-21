# Project Z 发行投影兼容性修复

固定基底 `ba666696e38c350c7bf3cdcc01fd940fcfa69145`；已验证暂存树 `ad123c0aeda12ff63b3b1c1efb7804ff4a9282f4`。本地修复完成，尚未创建提交或修改远端引用。源码目录：`/home/lightjunction/Documents/GITHUB/pr-core-release-projection-ba6666-20261121/source`。

## 修复

原工具把内部 Git 依赖中的 `version` 一律当作冲突来源，违反当前允许 `version + git` 的源码规则。现在复用仓库已有、未修改的 `cargo_versions.satisfies`：声明的版本约束必须合法且包含锁定版本，之后仍投影为锁中的 `=exact`。非法约束或不匹配会明确失败，不会用版本要求选择另一个 Git 提交。

`rev/branch/tag/path/registry/registry-index/workspace` 混用仍拒绝。别名、features、optional、default-features、target 和 workspace 继承保留。receipts 沿用同一入口，并继续核对确切提交与归档哈希。现有离线 Cargo metadata 断言未隐藏、删除或跳过。

依据：[Cargo multiple locations](https://doc.rust-lang.org/cargo/reference/specifying-dependencies.html#multiple-locations)。

## 实际验证

- RED：两个方法运行后实际退出 1；六个合法版本子例及 receipts 的准备阶段均被旧版拒绝。原件保留，未运行 Cargo。
- GREEN：三个模块合计 **18 项通过、0 失败、0 错误、0 跳过**。其中 release 4、projection 8、receipts 6；unittest 耗时 1.790 秒。原生作业 `26c4545eae1eab8d27485f4a48077d3c-bc6` 实际退出 0，两路输出均 EOF。
- 真实 Cargo 仅一次：`cargo metadata --offline --no-deps --format-version=1`，在私有临时夹具执行并退出 0，stdout 3,901 字节已保留。没有 Rust 编译、真实聚合图命令、产品、CI、安装或发布。
- 父进程一次非阻塞取得共享外锁，持锁前后均有内核记录；结束后解除。独立 postflight 观察到本作业两个 PID 均已退出、该锁的内核记录为空、临时夹具已清理。该观察不保证后续全局空闲。
- 源码 HEAD、暂存树、状态前后完全相同。未改其他工作树，也未清理共享 target。

## 文件

| 路径 | 字节 | Git blob |
|---|---:|---|
| docs/release-projection.md | 5658 | `4461f954fe94defb8055e4e3deb434fcb38b7a6f` |
| scripts/release_projection.py | 14539 | `ee12250feb7c0cd12c7350ca5574c5b974a89318` |
| tests/test_release_projection.py | 11080 | `44f0a71b44ce4ce1a7e7823943aab752be815d74` |
| tests/test_release_receipts.py | 7563 | `b06534747913b6239809fa07388abcba8d6eaca2` |

完整修改文本、diff、SHA-256、实际命令与原件索引在同目录 `handoff.json` 及 `evidence/publication-files.json`。Root 负责后续 GitHub 插件提交与精确树读回；无需重跑本批测试。
