# PR #10 在当前 main 上的依赖验证

2026-11-21 UTC，云端 Linux，Python 3.12.14，Cargo 1.100.0。GitHub API 显示 #10 为打开的草稿，基底 `coord/git-source-policy-20261120` 为 `b5ac5b7c5bdfafbe5562e9f9820288bea752f58f`，提交 `5983a7f297baba6a8ea00b2182e528baa80bb400` 有 0 个 Actions 运行、0 个 check run 和 0 条 commit status。[原 PR](https://github.com/LIghtJUNction/project-z/pull/10)

候选从 `main` 的 `6e786250812849079c870804ce4141b74f88f7d3` 建立。该基线已经登记 zuse-skills，并已采用 Zuse 0.5.0。本次补上 bilibilive 的 GitHub 默认分支 gitlink、application 角色和生成的索引，沿用原 PR 的三份历史证据。清单从 45 个仓库、72 个包变为 46 个仓库、73 个包。

| 递归检出的快照 | `python3 scripts/project_z.py check` | `python3 scripts/project_z.py resolve --all` |
| --- | --- | --- |
| 原 PR head | 退出 1。5 个嵌套 gitlink 不一致，4 处内部 Git 开发依赖指定了版本，18 条锁记录过期 | 退出 1。前 9 条结构和声明错误阻断 Cargo 全图解析 |
| 当前 main | 退出 1。仅 SSMCP 默认分支前进 | 退出 0。39 个 Rust 仓库通过锁定解析 |
| main 加 bilibilive | 退出 1。仅报告 bilibilive 的 Zuse 锁记录 | 退出 1。同一条锁记录在全图 Cargo 解析前拦截 |

原 PR 的首条诊断是 `ssmcp/crates/zuse` 固定了 `8d37a7df6fd94df1d0939eb6800c238e71f5835d`。本轮重现的 27 条诊断与该提交保存的集合完全一致。[原始诊断和目标 SHA](2026-11-21-zuse-050-source-update.json)

候选运行 `python3 scripts/project_z.py sync --record` 成功，重新比较生成文件一致。`python3 -m unittest discover -s tests -v` 通过 120 项。首次在沙箱的临时目录运行时，空的 `.git` 保护目录触发 10 项隔离夹具错误；完整重跑使用云机独立的临时目录。`impact --repositories zuse` 返回 bilibilive、oh-my-ztty、ssmcp、zrc、ztype、zuse、zuse-skills。

## 组件仓库待办

- **LIghtJUNction/bilibilive** 的 `main` 为 `6a6801492e0d70ca6cc8103f92fe76ac7f2da2df`。`Cargo.toml` 中的包别名和 Git 开发声明已正确。`Cargo.lock` 的 `zuse-computer` 仍为 0.4.2 / `d67e47c5dcd443ad9121a908ca57059160249051`。组件维护者需要更新到 Zuse 0.5.0 / `b5ebbd3679af215706cbd73b17045e014f5e0524`，验证兼容性，并提交开发锁和本轮来源记录。正式发布仍由独立 staging 按锁投影。[开发声明](https://github.com/LIghtJUNction/bilibilive/blob/6a6801492e0d70ca6cc8103f92fe76ac7f2da2df/Cargo.toml#L24) · [锁记录](https://github.com/LIghtJUNction/bilibilive/blob/6a6801492e0d70ca6cc8103f92fe76ac7f2da2df/Cargo.lock#L3066)
- **LIghtJUNction/oh-my-ztty** 的 `main` 为 `2fa1b47d41fbc441b482d7c4c23beac0c1e903e4`。其 `components/ssmcp` gitlink 和 `dependencies.lock.json` 都固定 `dde2938e050e1d9f8186a600f57dbb67e12de211`。在另一份 main 检出中运行完整 `sync`，选中 SSMCP 的公开 `main` `3730c039ec15a33af7bb3b56a9811e5649a99f85` 后，正是在这个嵌套 gitlink 上退出 1。套件维护者需要一起更新 gitlink、来源锁并验证安装。随后 Project Z 可以连同套件一起登记 SSMCP，并显式记录它对独立 Zuse CLI 的运行时依赖。[套件来源锁](https://github.com/LIghtJUNction/oh-my-ztty/blob/2fa1b47d41fbc441b482d7c4c23beac0c1e903e4/dependencies.lock.json#L11) · [SSMCP 运行时依赖](https://github.com/LIghtJUNction/ssmcp/blob/3730c039ec15a33af7bb3b56a9811e5649a99f85/docs/dependencies.md)

候选的 `check` 在消费者锁阶段退出。独立比较 46 个已登记仓库的公开默认分支，只有 SSMCP 与候选快照有差异。两处组件变更进入各自默认分支后，需要重新执行 `sync`、`check` 和 `resolve --all`。
