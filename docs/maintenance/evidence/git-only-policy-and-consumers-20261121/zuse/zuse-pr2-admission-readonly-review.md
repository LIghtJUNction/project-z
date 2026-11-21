# zuse PR2 只读准入复核

截至 2026-11-21T06:53:30Z，**PR2 已实际合入；最新主线是 `830fcefd`，不能继续把 `fe47` 当作当前主线。** 本轮没有修改远端、运行产品或触发 CI。

## 源码与 CI

PR2 的 `fe47f963e604c13a2646baf5d391df5a7c69fc36`、已完整审阅 CI 的 `67e2d6a4cee0d106f46bdf064013e163c0aa3337`、CI 实际检出的 `cf9d3973db10a8639cdfbc3460af8b9230cf1e5c`，整棵树都为 `af46f28f9db1b4cd9f1103dc0f97687669b770d5`。本轮重新读取三份完整原日志并核对 SHA，结果如下；这是各平台汇总，不能相加成为独立测试数量。

| 平台 | 通过 | 失败 | ignored | 汇总行 |
|---|---:|---:|---:|---:|
| Ubuntu | 289 | 0 | 5 | 22 |
| macOS | 267 | 0 | 3 | 22 |
| Windows | 263 | 0 | 2 | 22 |

实际日志包含 fmt、locked tests、原生及 Wasm no-default-features check、严格 Clippy。该 CI 未执行需要显式 opt-in 的原生 MPX/图形验收，也未执行历史上单独的 20 项 no_std 测试套件。[原日志核对](ci-original-log-readback.json)

## 本次捕获的主线变化

收尾 API 读取显示 PR2 于 **06:46:06 UTC** 合入，账户为 LIghtJUNction；不能据账户推断是人工还是 agent。API 的 draft 字段仍为 true，但 state=closed、merged=true，因此不再列 Draft 为当前阻断。

主线现在为 `830fcefd2277cbba46536c67d206f29058ba7fb3`，树 `3c110034f10ba5f35b0e18ac6b890d533121a473`。从 fe47 向前两个提交，159 个叶子中 154 个原样，仅 Cargo.toml、Cargo.lock、CHANGELOG、README、release workflow 五处变化：

- 包版本 0.2.2 → 0.3.0；zcall 锁从 564ede15 → 317c52f1。
- 四个直接 Git 依赖移除 version 选择器，原 feature 设置保留。
- GitHub 发行流程移除 Cargo registry 发布步骤。

全部 Rust 源码保持。这属于依赖、版本及发行流程变化，不能当成纯文档或套用旧锁的运行证明。830 当前 10 个 Checks API 条目均 success（3 平台 CI、identity、5 构建、publish）；本轮未重新审阅其完整日志或发行制品。

## 准入结论与下游边界

对固定 fe47/af46，未发现源码或 CI 阻断；也不需要仅因合并提交身份改变而重复相同源码树的三平台 CI。公开 reviews/comments 为空，已读主线保护与 rulesets 没有额外必需检查；这不是对后续消费者正确性的证明。

仓库 AGENTS 和 PR 正文要求完成消费者传播。对于新的 Runtime 默认独立指针行为，各 owner 需要逐个评估 SSMCP、ztype 的兼容性，仅对实际不兼容的入口修改代码，并验证新的依赖组合；用户这次要求更新 zuse，必须按最新主线及新锁推进。SSMCP 的 W/r14 仍是旧 a1 依赖，不能移用到新的 0.3.0 组合。消费者实际运行、UI/P1 与最终 44 仓图仍按既有 owner 的窗口收口。

[完整固定身份与来源](zuse-pr2-admission-readonly-review.json) · [PR2](https://github.com/LIghtJUNction/zuse/pull/2) · [已封存 CI](https://github.com/LIghtJUNction/zuse/actions/runs/44860554142) · [新增主线差异](https://github.com/LIghtJUNction/zuse/compare/fe47f963e604c13a2646baf5d391df5a7c69fc36...830fcefd2277cbba46536c67d206f29058ba7fb3)
