# Project Z

把 Project Z 的 19 个项目放在同一个检出目录里，方便同时修改上下游、做联调，以及给一组兼容的提交打版本。每个子模块保留自己的仓库、测试和发布流程。

## 协同迭代

从聚合仓库根目录执行：

```sh
git submodule update --init --recursive
git submodule status --recursive
```

子模块检出聚合仓库记录的提交。要更新某个项目到上游 `main`，先确认它的工作区干净，再执行 `git submodule update --remote --checkout -- zcall`。要在子模块中提交改动，先用 `git -C zcall switch main` 切到开发分支，并核对分支与待联调快照的位置。

例如，同时改 `zconv` 和依赖它的 `zcall`，以及下游的 `zharness`，可以从聚合仓库根目录运行：

```sh
ln -s project-z.toml .cargo/config.toml
cargo test --manifest-path zcall/Cargo.toml
cargo test --manifest-path zharness/Cargo.toml
```

这个本地软链接让测试启动的子 Cargo 进程也读取同一份配置。联调结束后可用 `unlink .cargo/config.toml` 关闭。配置会用本地子模块替代匹配版本的 crates.io 依赖。目前覆盖 `zcall`、`zclap`、`zconv`、`zplugin`、`zvte`。Cargo 仍检查依赖的版本约束，联调时也可能改写下游的 `Cargo.lock`，提交前请检查差异。各项目所需工具链和专项测试见其自己的 README。

联调通过后，先在各子模块提交并推送，再从聚合仓库记录这组提交：

```sh
git add zconv zcall zharness
git diff --cached --submodule=log
git commit -m "Update the Project Z snapshot"
git push --recurse-submodules=check
```

## 统一发布

在 GitHub Actions 的 **Release Project Z** 中选择 `main`，按需选择 `patch`、`minor` 或 `major`。版本按仓库中最大的 `vMAJOR.MINOR.PATCH` 标签递增，首次选 `patch` 会生成 `v0.0.1`。

默认把完整源码包和 `commits.txt` 上传为工作流产物。开启 `publish` 后，同一份产物会附在 GitHub Release 上，标签指向本次运行检出的聚合提交。子仓库的标签和 crates.io、PyPI 上的包仍由各项目发布。下载完整源码请使用 Release 附件中的 `project-z-v*.tar.gz`。

本地预览打包可用 `python3 scripts/release.py patch dist`。
