# 2026-11-21 Project Z 公开源码快照核验

截至 **16:35:56 UTC**，46 个登记仓库均为公开仓库，默认分支均为 `main`。独立云端检出与逐仓读取的远端 HEAD 全部一致。当前组合被 4 个消费者阻断，本分支从聚合 main `be64e5ab` 建立，只提交诊断目录。登记快照、上游 gitlink 和消费者锁的更新仍待全图验收。[生成的 catalog](catalog.json) · [项目与依赖索引](PROJECTS.md) · [完整 SHA、诊断和锁文件摘要](audit.json)

## 门禁结果

| 项目 | 实际结果 |
| --- | --- |
| `sync --record` | 退出 0。按已检出的 SHA 生成 46 仓、73 个 Cargo 包的 catalog 与索引。63 个递归子模块检出完整，45 份工作区 Cargo.lock 与各自提交中的 Git blob 相同。 |
| `check` | 退出 1。6 个嵌套 gitlink 与所选上游不一致，另有 12 条内部 Cargo.lock 记录过期。协调器在进入远端新鲜性检查前报错，本次另行核验全部远端 HEAD。 |
| `resolve --all` | 退出 1。6 个 gitlink 在全图 `cargo metadata --locked` 开始前阻断。 |
| 按仓运行协调器的 `resolved_paths` | 37 个 Rust 仓、42 个登记 manifest 完成真实 `cargo metadata --locked` 和内部来源 SHA 比对。bilibilive、SSMCP、ztype 因各自的 gitlink 或锁文件冲突留待修复；其余 6 仓没有登记 Cargo manifest。 |

首轮普通 `sync` 也在同样的 6 个 gitlink 处停止。75 个登记工作区及成员 manifest 中，72 项直接跨仓声明的 GitHub URL、默认分支写法和开发依赖字段均通过核对。登记范围包括配置中的 fuzz 与插件工作区。外部发行继续使用单独的投影工具，回归中覆盖了注册表来源回执校验。

## 待配合的消费者

| 源码负责人 | 必须随自身提交同步的内容 |
| --- | --- |
| SSMCP `02aa4dcd` | `crates/zharness`、`crates/zuse` 应分别对应 `5f9a9f58`、`b5ebbd36`。Cargo.lock 涉及 zcall、zconv、zharness、zmcpio、zuse-computer 共 5 条。Zuse 自身在 `b5ebbd36` 上的锁定元数据解析已通过。 |
| bilibilive `6a680149` | Cargo.lock 仍固定 zuse-computer 0.4.2 `d67e47c5`。16:19 的取样中这项解析通过；16:35 取样的 Zuse main 为 0.5.0 `b5ebbd36`，需要验证新版本并刷新该锁。 |
| ztype `4d784aa2` | `vendor/zgpui` 应对应 `174a8b73`。Cargo.lock 涉及 zcall、zconv、zgpui、zgpui-raster、zmcpio、zuse-computer 共 6 条。 |
| oh-my-ztty `ab904f09` | 更新 `components/ztty`、`components/ssmcp`、`components/zrc`，分别对接验收后的上游提交。当前采样为 `c63dbd52`、`02aa4dcd`、`c127bd29`。安装套件分发的旧 SSMCP 与 ztty 内又带有 4 个过期副本，递归路径已列入 JSON。 |

负责人提交兼容改动后，聚合维护者可重新获取公开 main、生成目录并运行两道门禁，再决定可登记的 gitlink。上述逐仓通过只覆盖依赖解析，各项目的原生产品验收由其维护者负责。

## 历史身份与传播范围

- `0783fdf6` 属于 **project-z**。该树中的 zi18n gitlink 是 `cdff8dea19e97268d296afa827767ea689420591`，与采样时的公开 main 和 `zmcl/vendor/zi18n` 相同。用 `0783fdf` 查询 zi18n 自身得到 HTTP 422。影响范围为 zi18n、zmcl。[历史树](https://github.com/LIghtJUNction/project-z/tree/0783fdf6f70e07bf873bbebb97aea868e0e06002)
- 同一历史树记录的 `lmm-api-source` 提交 `ec0dac93ab7386567ebf51e26bcc264d8921e6be` 在 GitHub 提交接口返回 HTTP 422。公开 main `fa57cd2049ccd9138cdc0b4104db36b5b6c53ae5` 可正常检出，其 `apps/cli` 对齐 lmm main `260a1eff2400aa64fc697028a406a8017ed6259c`。两者各自完成真实锁定解析。单查 `impact lmm` 的仓库模式仅返回 lmm，核对分发树后还应计入 lmm-api-source。[LMM 源码树](https://github.com/TokenNotIncluded/lmm-api-source/tree/fa57cd2049ccd9138cdc0b4104db36b5b6c53ae5)
- 聚合 main 有 43 个登记仓库。草稿 #7 `b5ac5b7c` 提供 Git-only 协调器；叠加草稿 #10 在核验期间从 `6c76ef89` 前进至 `df34cc65`，更新了 bilibilive、Zuse 及登记文件。两次 #10 的脚本、测试和政策文件相同。与后一个 #10 相比，最终采样有 **11 个 gitlink 差异，涉及 17 仓**；相对 main 为 29 个新增或变动源，涉及 30 仓。全部集合见 `audit.json` 的 `impact`。最后一次取样中 ztty 为 `c63dbd52`、Zuse 为 `b5ebbd36`、zuse-skills 为 `fce48d78`。[PR #7](https://github.com/LIghtJUNction/project-z/pull/7) · [PR #10 的固定提交](https://github.com/LIghtJUNction/project-z/commit/df34cc651b7b72a00fe437da49d911e876cdc9ca)

## 复核

在新目录检出上述 #10 的协调器版本，按 `audit.json` 的 `heads[].url` 与 `heads[].remote_head` 获取各仓的精确提交。递归子模块使用每个父提交的 gitlink。LMM 引用的外部 Extore 提交 `cf3469db` 可从其公开 `review/extore-zplugin-catalog` 分支取得。使用仓库固定的 Cargo 1.100.0 依次运行以下命令，预期退出状态分别为 0、1、1。

```sh
python3 scripts/project_z.py sync --record
python3 scripts/project_z.py check
python3 scripts/project_z.py resolve --all
```

zi18n 的 `cargo test --locked --all-features` 通过 26 项，包含一个文档测试。zmcl 的 `gui::titles::tests::titles_preserve_existing_english_bytes` 定点测试通过 1 项，覆盖实际使用 zi18n 的 GUI 标题。协调器完整回归在独立云容器的离线 Git/Cargo 夹具中通过 **112/112** 项。首次使用沙箱默认临时目录时，`.git` 占位符使 10 项工作树夹具失败；最终复跑使用普通临时目录、仅允许 Git 文件协议并清空进程继承环境。原始门禁输出、工具版本与生成物散列均在随附 JSON 中。
