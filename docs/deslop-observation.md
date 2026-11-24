# Rust 架构观测

**Observe Project Z Rust architecture** 每天运行一次，也可在默认分支手动触发。它独立于发布和既有 CI，不会因为架构发现阻止合并或发布，不自动修复，也不写允许列表来隐藏历史问题。

范围来自 `catalog.json` 的已登记 Cargo 入口，包含不在仓库根目录的工作区。脚本核对 `.gitmodules` 和当前提交的 gitlink，在无检出凭据的 GitHub 托管 runner 上获取该固定提交。只尝试 `LIghtJUNction` 名下的仓库，不读取组织的私有源码或没有 Cargo 清单的组件。源码无法匿名获取、入口缺失、锁解析失败、超时及工具异常都不会计为通过；扫描不会递归初始化未纳入清单的嵌套子模块。

- `clean`：本次配置没有发现。
- `findings`：发现模块循环、接口泄漏等结构问题；不阻塞既有 CI。
- `tool_error`：该工作区未完成有效扫描；查看工件日志修复扫描条件后重试。出错会标红这个独立观测任务，不把结果当作干净基线。

Actions 摘要列出每个工作区的源码提交和状态，工件提供机器可读的 `report.json` 与诊断日志，留存 14 天。同一时间至多一个工作流，最多并行扫描三个仓库。报告只代表 Linux 默认功能配置和记录的快照，不代表其他平台、功能组合或子仓库最新分支。

在独立检出中试跑单个仓库（不用于有未提交修改的工作区）：

```sh
rustup component add rust-analyzer rust-src
cargo install deslop-please --locked --version '=0.1.3'
python3 scripts/deslop_observation.py --repo zrun --output /tmp/project-z-deslop-report
```

规则和诊断解释见 [deslop-please](https://github.com/deterministic-machines/deslop-please/tree/v0.1.3)。诊断是审查线索，不等同于缺陷。先看模块职责和调用边界，不为了消掉提示而机械搬代码。
