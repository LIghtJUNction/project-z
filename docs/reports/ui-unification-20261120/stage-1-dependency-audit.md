# UI 统一第一阶段依赖审计

审计基于聚合提交 `046bb4b0b73f82e0943c92d7c81facb9968b8520` 的 gitlink、各消费仓库在该提交固定的 Cargo manifest 与 `Cargo.lock`，以及源码分发和运行时声明。[独立验证回执](independent-validation-046bb4b.json)记录该基础提交的 `check` 和 `resolve --all` 结果。

## 新增的仓库关系

箭头从消费者指向依赖。每行的消费包均在该仓库的 `Cargo.lock` 中指向所列版本的本地路径包。所列嵌套 gitlink 均与基础提交的对应聚合 gitlink 一致。

| `requires` 关系 | 消费仓库源码 | 仓库内 manifest 与消费包 | 依赖与嵌套 gitlink |
| --- | --- | --- | --- |
| `zmcl → zconv` | `35eb8a3242a6ba637266ba1480354138389c9cb0` | `crates/zmcl-core/Cargo.toml`，`zmcl-core 0.1.0` | `zconv =0.4.0`，`vendor/zconv` 固定到 `0af1f7eb0766ff0ce9db5cee7c6184eff511a8c1` |
| `zmcl → zclap` | `35eb8a3242a6ba637266ba1480354138389c9cb0` | `Cargo.toml`，`zmcl 0.1.1` | `zclap =0.1.4`，`vendor/zclap` 固定到 `4d87f3ae3743e81509d5ac5500909955667c860f` |
| `zmcl → zgpui` | `35eb8a3242a6ba637266ba1480354138389c9cb0` | `Cargo.toml`，`zmcl 0.1.1` 的 `gui` feature | `zgpui =0.1.2`，`vendor/zgpui` 固定到 `5b268da910639abd2fb8e581acb4f6eed50b7516` |
| `ztype → zgpui` | `9dd67a54ac536b22ab0fe4bd008d6b5cdd95c369` | `Cargo.toml`，`ztype 0.1.0` 的 `gui` feature | `zgpui =0.1.2`，`vendor/zgpui` 固定到 `5b268da910639abd2fb8e581acb4f6eed50b7516` |
| `zcall-gui → zgpui` | `e6ed24bdd5d7d193d76fc03a53d2bc1e10edec74` | `Cargo.toml`，`zcall-gui 0.1.1` | `zgpui =0.1.2`，`vendor/zgpui` 固定到 `5b268da910639abd2fb8e581acb4f6eed50b7516` |

Cargo 图还包括 `ztty → zterm → zgpui`。`ztty` 的 `[patch.crates-io]` 为这条传递依赖选择 `crates/zgpui`，`Cargo.lock` 记录路径包 `zgpui 0.1.2`。运行时和安装链沿现有声明展开，包括 `zcall-gui` 对 `zcalld` CLI 的调用、`zcalld` 分发的前端和兼容组件，以及 `oh-my-ztty/.gitmodules` 中的六个安装组件。`requires` 用于影响分析。现有 `source_links` 规则继续单独校验 `zcalld/apps/zcall-gui` 与聚合 `zcall-gui` 的源码一致性。

## 修改前后的影响范围

`python3 scripts/project_z.py impact --repositories zgpui` 在基础提交运行一次，并在第一阶段 `sync` 后再次运行。两次均退出 `0`，输出逐字节一致，依次为 `oh-my-ztty`、`zcall-gui`、`zcall-omarchy`、`zcalld`、`zcalld-compat`、`zgpui`、`zmcl`、`zterm`、`ztty`、`ztype`。五条关系原已由 Cargo 图覆盖，本阶段将对应的源码依赖显式登记到仓库清单。该结果描述当前固定源码的传播范围。

## zi18n 登记与验证

新增 `zi18n` 库及其唯一新 gitlink，固定到 `b90984b48465a764bcb699ad2bb3251fa7020024`。该提交的 `Cargo.toml` 声明版本 `0.1.0` 和 `default = []`，`src/lib.rs` 在未启用 `std` 时使用 `no_std`。`v0.1.0` 的附注标签对象为 `0443f5d212628dac1fc51a479cfa1e1420dd1a94`。[固定源码](https://github.com/LIghtJUNction/zi18n/tree/b90984b48465a764bcb699ad2bb3251fa7020024)

crates.io 索引、版本 API 和归档均返回 HTTP 200。归档为 17,045 字节，包含 16 个文件，`.cargo_vcs_info.json` 记录上述提交及干净的 VCS 状态。归档、索引和 API 的 SHA-256 一致，为 `eeb0c6eefa7e2dee454cd727e5cacbe89bacf4c461742ca7316a486a32dfaed2`。正式验证 `44711822852` 的七个作业均通过，全部指向同一提交。[索引](https://index.crates.io/zi/18/zi18n) · [版本 API](https://crates.io/api/v1/crates/zi18n/0.1.0) · [归档](https://static.crates.io/crates/zi18n/zi18n-0.1.0.crate) · [正式验证](https://github.com/LIghtJUNction/zi18n/actions/runs/44711822852)

`sync` 生成 42 个仓库和 61 个 Cargo package 的清单。`check` 退出 `0`，报告版本与依赖图一致。`impact --repositories zi18n` 当前只返回 `zi18n`。`zmcl` 对 `zi18n` 的接入由现有 `zmcl` 负责人完成，待实际消费提交验收后登记关系。

## 第二阶段待验收来源

现有组件继续使用基础提交的 pins。`ztty 0.5.2` 的正式发行源码为 `6e2ce246b0b50e6b82da99756832feae6e966f21`，发行制品验收由其负责人完成。`oh-my-ztty 0.2.6` 仍在组装。`zgpui 0.1.4/0.1.5` 的更新版消费者由各自负责人提交验收。SSMCP 21 由单一负责人推进完整功能发行。第二阶段将在各组件提交验收并固定后运行一次 `resolve --all`，并保留适用的原生界面、服务和发行制品验收。
