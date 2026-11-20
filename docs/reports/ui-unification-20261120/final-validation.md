# oh-my-ztty 0.2.6 聚合候选验证

源码快照 `522bc7c9da008f05e9f715c1c1eda91b13ca89ec`（tree `eb2dfc60e3ab31f96c6fb29c458573f8500a2ac6`）通过最终 `check` 与 `resolve --all`，待主分支审阅。[固定候选](https://github.com/LIghtJUNction/project-z/commit/522bc7c9da008f05e9f715c1c1eda91b13ca89ec) · [验证回执](final-validation.json)

## 套件来源

oh-my-ztty 从 `0fdc87873c53e7c87d18952f83a7b94fc4149de5` 更新到 `1e3ce8d3e5a141d09e450fd3f635f987a5732be4`。附注标签 `v0.2.6` 对象为 `5a5f45dcc37c443876aee5d29ed280bcf6c6058d`。正式运行 `44719594477` 的三个作业全部成功。Linux x86-64 和 AArch64 原生作业均完成完整递归检出、安装生命周期、锁定 bundle、实际 GUI、键盘、补全与清理，再由发布作业交付。Release `452554850` 于 `2026-11-20T18:31:09+08:00` 发布，含六个附件。[正式运行](https://github.com/LIghtJUNction/oh-my-ztty/actions/runs/44719594477) · [正式制品](https://github.com/LIghtJUNction/oh-my-ztty/releases/tag/v0.2.6)

| 官方归档架构 | 字节数 | SHA-256 |
| --- | ---: | --- |
| Linux x86-64 | 7,273,546 | `94a22ce1300a337e741ef0c2a336e29e90696b621fbdfa05c0b66673ce10dc20` |
| Linux AArch64 | 7,011,427 | `b035c460e3444e7b33dda4e5dd25bceecf0757af40b095950adb8d0ad001637b` |

套件固定 ztty `6e2ce246b0b50e6b82da99756832feae6e966f21` 和 SSMCP `4f4dd88275c205e0e61a7601b4e0d11f56038769`，其 SSMCP 官方制品版本为 0.10.20。顶层 SSMCP 的兼容 Cargo 源码仍为 `bfe5f25ffab718f100b11d2ce55c8dc839cbad71`。现有 `requires` 关系保留套件与顶层组件的传播边界，套件制品的来源由它自己的标签和锁文件记录。

## 聚合验证

验证时段为 `2026-11-20T18:46:55+08:00` 至 `2026-11-20T18:47:04+08:00`（Asia/Taipei）。两条命令各在已提交的候选上执行一次。

| 命令 | 退出码 | 耗时 | 结果 |
| --- | ---: | ---: | --- |
| `python3 scripts/project_z.py check` | 0 | 0.997 s | 43 个仓库、62 个 Cargo package，版本与依赖图一致 |
| `python3 scripts/project_z.py resolve --all` | 0 | 8.639 s | 38 个 Rust 仓库完成本地依赖解析 |

验证前后，103 个递归子模块和根仓库均保持干净，HEAD 与记录的固定提交一致。核对了 233 个 Cargo.lock 候选路径（142 个原有文件）和 209 个仓库内配置候选路径（3 个原有文件）。文件内容、权限、存在性及外部 Cargo 配置均一致，差异为 `[]`。

回执提交仅补记验证结果，使用同一依赖图和源码固定点。先前的独立验证继续对应 `046bb4b0b73f82e0943c92d7c81facb9968b8520`。实际套件安装与主分支审阅由各自负责人跟进。[先前独立验证](independent-validation-046bb4b.json)
