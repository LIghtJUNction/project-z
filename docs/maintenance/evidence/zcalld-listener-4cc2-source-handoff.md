# zcalld listener：合入 v0.4.4 主线的源码候选

PR1 已更新为 `4cc2fd1cfb6eb49dacc022af6c15cc0f7825e409`，树为 `262cb876bcf4f83ef2c66912863629f0401db89d`。它以原候选 d531 和主线 `0a0a62cdca25bbdf289a17f03dfeed1acc945595` 为双父，正常快进原分支。PR 保持草稿；主线和发行标签未移动。

## 已完成的源码核对

| 项目 | 结果 |
|---|---|
| 新主线 | 216 个文件或 gitlink 叶节点 |
| 整合候选 | 219 个叶节点 |
| 主线保留 | 除两个被 listener 整合替换的文件外，其余 214 个主线叶的 SHA、模式和类型全部相同 |
| listener 改动 | 恰好五个 Rust 路径：两个原文件加三个新文件，全部与 d531 的对应 blob 相同 |
| 删除 | 无主线文件删除 |
| 本机与 GitHub | 本机暂存树与 GitHub 创建的树均为 262cb876 |
| 独立复核 | 第二位审阅者逐叶检查通过；仅静态审查，没有运行测试 |

保留主线的版本 0.4.4、Cargo 清单和锁、全部安装器修复，以及 GUI `ca35a306`、compat `c521d1fb` 和 zcall `317c52f1`。其中 GUI 新源码与安装器的 Windows 目录权限修复相配套，未回退到旧候选的 d357。

五个 listener 文件继续使用原 Linux 限定、显式私有 Unix socket/no-proxy 路径和 `STOPPING` 取消检查。主线在相关 system/transport 文件中的新增差异属于 Windows 断连检测，原 Linux listener 前置接口未变。这个结论来自源码对比，不能替代新组合的运行验收。

## 本轮没有运行的新树门禁

本轮只做了新隔离源码准备、Git 逐叶比较、空白检查及独立静态复核，没有运行 Cargo、构建 CLI、原生输入测试或最终 SSMCP P1。候选没有新的已验二进制。

原 d531 的 179 项 Rust 测试和八项 curl 用例继续对应 d531/tree06826；原 97d 的 177 项 Rust 测试和八项 curl 用例继续对应 97d/tree44a49。旧产物和回执保持原身份。

新候选的本机路径为 `/home/lightjunction/Documents/GITHUB/pr-core-zcalld-listen-0a0-20261121/source`，读回已是干净的 4cc2/tree262。原 d531 工作树和证据未改。Root 负责安排新候选验收并最终合并 PR1；当前 SSMCP 性能 A/B 的安静窗口保持优先。

## 证据

- [PR1](https://github.com/LIghtJUNction/zcalld/pull/1)
- [固定候选提交](https://github.com/LIghtJUNction/zcalld/commit/4cc2fd1cfb6eb49dacc022af6c15cc0f7825e409)
- 完整来源、五文件矩阵、所有 gitlink、CAS 与清洁读回：`zcalld-listener-4cc2-source-handoff.json`。
- 独立树复核：`pr-cleanup-zcalld-262-tree-independent-review.json`，SHA256 `84f34a5c129682dc7de70410b3fdc86b59896e17d80b8446ae9b835dc0a32c79`。
