# Project Z 共享实现与发行快照

本轮更新内部依赖来源，并把已确认的重复生产逻辑接入现有提供者。2026-11-23 开发批次的本地门禁于台北时间 2026-11-24 00:06 完成：**49 个仓库、82 个包通过来源检查，43 个 Rust 仓库完成真实 locked 解析，150 项协调测试通过。** 113 个递归源码引用均匹配记录提交。[前置门禁证据](evidence/release-cohort-20261123/preflight.json)

该提交随后进入正式发行工作流。三平台库测试与五组 Linux 消费者验证全部成功后，才允许打包和发布；此文记录源码提交前的证据，不预先宣称尚未执行的发行结果。

## 迁移范围与行为边界

初筛检查了 1,633 个 Rust 生产文件，排除同源嵌套、vendor、生成文件及测试夹具，再人工核对下列调用契约。这是有界审查，不代表所有语言或全部实现已完成去重。[逐消费者源码与验证范围](evidence/release-cohort-20261123/dedup-proof.json)

| 应用与可审查来源 | 接入的提供者与范围 |
| --- | --- |
| [ssmcp](https://github.com/LIghtJUNction/ssmcp/commit/b799d0c5fe03c5b19ed4441f200de715c6c7d512) | Hex → `zhex`；保留接口与错误映射 |
| [zmem](https://github.com/LIghtJUNction/zmem/commit/5997b9581f5b6962c9d9cd12774a2ce119e46ca7) | 备份路径 Hex → `zhex`；保留字节路径与 NUL 拒绝 |
| [ztty](https://github.com/LIghtJUNction/ztty/commit/963afbd7f9463f6de61a96e1968fdf26d3bc8990) | Hex 编解码 → `zhex`；PTY Base64 → `z64`；保留小写解码规则、游标与容量 |
| [zmcl](https://github.com/LIghtJUNction/zmcl/commit/61c3655806fee9f4a20fc8bea2e881ce0531fc48) | Hex → `zhex`；SHA-1/256 → `sha1`/`sha2` |
| [zterm](https://github.com/LIghtJUNction/zterm/commit/55e24949c3cf5773535215d81fed71e3364c4802) | OSC52 Base64 → `z64`；保留 framing、policy 与长度上限 |
| [zmcpio](https://github.com/LIghtJUNction/zmcpio/commit/aba5ee5e775142f67a2cb0b181fc1fecdc286e98) | HTTP sentinel Base64 → `z64`；保留协议封装与错误契约 |
| [mechrevo-drivers](https://github.com/LIghtJUNction/mechrevo-drivers/commit/2874af81c0cf59bdbe6b6e79e969ea17204e50c3) | 亮度后端编码 → `z64`；保留 UTF-16LE 输入与平台行为 |
| [zcall-gui](https://github.com/LIghtJUNction/zcall-gui/commit/3b9a0f4673c08a9aa259b52e02858c0a88f43f6b) | 更新器 SHA-256/Hex → `sha2`/`zhex` |
| [zcalld](https://github.com/LIghtJUNction/zcalld/commit/6eab1150e8d58d330583c1b3206bf91e7862dc9a) | SHA-256/Hex → `sha2`/`zhex`；兼容通道编码 → `z64`，解码 → `base64` |
| [zuse](https://github.com/LIghtJUNction/zuse/commit/13be18166f9f1bdfb219da851c28b3319fdb7653) | Base64 → `z64`；WebSocket SHA-1 → `sha1`；保留 20 字节摘要与 accept 语义 |

迁移保留各调用者的 alphabet、padding、尾位、输入上限及错误优先级。zcalld 兼容 worker 原本接受非规范尾位，因此使用 `base64` 的相应配置，未强加严格解码规则。zuse 的 `MAX_MESSAGE`、zmem/zuse 的 `std` 特性边界与 zmcl-core 的 `no_std` 边界继续保留。适配层负责领域规则，不再复制完整算法。终审发现 ztty 残留手写解码后，已补接 `zhex::decode`；原 3 项 broker 协议测试、Clippy 和格式检查通过，清单、锁与测试源码未改。

禁止重复生产实现的要求已写入 `AGENTS.md`、`CONTRIBUTING.md` 和 `docs/shared-implementations.md`：先核对契约、复用提供者，再完成消费者传播。Windows permissions、JSON parser 候选尚缺完整契约证明，保留审查，不据此宣布必须新增库。

## 来源传播与发行入口

内部开发声明继续使用默认分支 Git URL；实际 Cargo 更新产生锁定 SHA，随后同步嵌套 gitlink。zconv fuzz 与 zhex comparison 的辅助依赖锁得到刷新；生产源码等价的传播复用既有行为证据，同时执行真实 locked metadata。例见 [lmm](https://github.com/TokenNotIncluded/lmm/commit/e04695efe394b8d8bc4bb7eff5c6f9a9f29463d0)、[OniMods](https://github.com/LIghtJUNction/OniMods/commit/9ee0d1df7473e570b494b89d99902e6de6c7fb05) 及服务端 [apps/cli 与 core 锁更新](https://github.com/TokenNotIncluded/lmm-api-source/commit/b6179424adf622416c6ff8340f99ccb8658acef4)。zuse 和 [ztype](https://github.com/LIghtJUNction/ztype/commit/d61eb478e665fbf862fc2f58a37cb91fb9aa0162) 已公开，[套件最终来源](https://github.com/LIghtJUNction/oh-my-ztty/commit/b34de32ed007015872fbaf92ee55185dfd8e031d)也已公开。SSMCP 随后合入上游 PR #193（`b5fdceea9af1b14f6f178bbc1677969fd3ff73c9`）；本轮 Hex 源码与两份依赖锁保持不变，聚合采用该真实新主线。

zmem 将 registry 上传从 GitHub 资产发行分离，固定复用[总仓 dbeecf0](https://github.com/LIghtJUNction/project-z/tree/dbeecf0c038d9184825e6fb2a25dfdc5eb951e40) 的 `scripts/release_projection.py`、`scripts/release_receipts.py`。独立 receipt 哈希、精确来源与 dry-run 全部通过后，仍须显式选择上传；token 只注入上传步骤。现有离线 fixture 不构成真实 registry 发布证据。

ztype 把 Linux 环境准备集中到 `ztype/.github/actions/setup-linux/action.yml`，保留依赖、构建与六分钟时限，并加三十秒强制终止宽限；尚未实际运行远端 CI。新增 zbridge、zrun、zaccel 的聚合登记，由 `.gitmodules`、`project-z.toml` 和生成 catalog 共同核对。

## 已有验证及未覆盖项

Rust 1.100 上的五核心库既有基线测试通过；后续行为变化须使用各自专项记录，不能以旧基线代替。已读记录包括 zterm 库测试 195 通过、1 项旧 ignored；zuse 浏览器 12 项、mechrevo 亮度 14 项、zcall-gui 单元 44 项、zcalld installer 15 项及 compat-client 10 项通过。zmem 默认测试共 245 项通过，3 项既有 root/硬件相关 ignored；另有 8 项 registry fixture 通过。为满足新增 zhex 依赖的工具链要求，其最低 Rust 版本改为 1.99.1，并实际验证该工具链的默认 CLI、无默认特性与路径编码检查；相关无默认特性检查、标准摘要向量与分块边界也有通过记录。以上不构成全仓 MSRV 或跨平台验收。

仍有真实未通过项：zcalld 的 5 项 Unix socket 测试受 IPC 权限限制；ztty 的 1 项临时目录测试在未修改基线上同样失败，另有 8 项旧 ignored；ztype 的 3 项 Unix datagram 测试和 zrc 特殊文件检查受权限限制；zfetch 缺少所需 sysfs 节点。它们须在正式 Linux 环境补验，不能删除、跳过后计为全量通过。GUI、设备及安装行为仅按实际记录认定。

[zrun v0.1.0-p0.1](https://github.com/LIghtJUNction/zrun/releases/tag/v0.1.0-p0.1) 已发布 P0 预览。首次性能测量尚未达到目标；预览验收范围以该组件的源码说明和正式运行记录为准，本轮不声明性能改善。

## 完整快照的本地门禁与正式发行

下列结果来自同一完整来源快照；源码文件与 catalog 哈希保存在[前置证据](evidence/release-cohort-20261123/preflight.json)。共享能力专项测试按原提交和特性组合复用，未将复核记录计作新运行。

| 门禁 | 实际结果 |
| --- | --- |
| `python3 -B scripts/project_z.py sync --record` | 退出 0；记录 49 仓库、82 包 |
| `python3 -B scripts/project_z.py check` | 退出 0；来源声明、锁、嵌套引用、生成文件及远端最新默认分支一致 |
| `python3 -B scripts/project_z.py resolve --all` | 退出 0；43 个 Rust 仓库通过实际 `Cargo --locked` 解析 |
| `python3 -B -m unittest discover -s tests -v` | 150 项通过，退出 0；约 180 秒 |
| 递归源码身份 | 113 项全部匹配记录提交，嵌套工作区干净 |

正式发行调用[统一协调工作流](../../.github/workflows/ci.yml)，在 Linux、Windows、macOS 上运行库测试，并在原生 Linux 上补验 ztty、ztype、zcalld、zrc 和 zfetch。Linux 输入环境使用已复审的 ztype action，额外显式安装 ztty 所需 HarfBuzz 开发包；失败仍会阻止后续 package/publish。源码包与 `commits.txt` 由[发行工作流](../../.github/workflows/release.yml)从同一提交生成，最终平台结果和资产以对应正式运行记录为准。
