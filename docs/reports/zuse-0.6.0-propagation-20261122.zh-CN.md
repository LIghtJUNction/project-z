# Zuse 0.6.0 已完成证据与总仓集成阻断

**Zuse 0.6.0、标准库及下列消费者验证已经完成；Project Z全图候选未通过验收，总仓集成尚未完成。** 本次只提交本报告和机器可读证据，不合入未通过的候选gitlink、目录索引或注册配置。

本报告固定实际受测来源和观察时间。并行维护后来推进的公开HEAD另列，不继承较早来源的通过结论。稳定标签v0.6.0及五平台发行资产保持原样。

## 本轮受测与公开来源

| 本轮来源 | 公开提交 |
|---|---|
| 稳定Zuse v0.6.0 | [`328117e3cd714bebab3ce45951bdaa1bdf52dda1`](https://github.com/LIghtJUNction/zuse/commit/328117e3cd714bebab3ce45951bdaa1bdf52dda1) |
| 5f阶段Git安装短验 | [`5f3742790247407fce7a79629282c35db118fc36`](https://github.com/LIghtJUNction/zuse/commit/5f3742790247407fce7a79629282c35db118fc36) |
| 最后安装短验 | [`6e88dd885eb73545a1ab6a9cd50097ef63fba423`](https://github.com/LIghtJUNction/zuse/commit/6e88dd885eb73545a1ab6a9cd50097ef63fba423) |
| std v0.1.0 | [`d79f43f8f3c2a1bff05962420f014b6c16403c5c`](https://github.com/LIghtJUNction/zuse-std/commit/d79f43f8f3c2a1bff05962420f014b6c16403c5c) |
| ztype受测提交 | [`c89dd36dc7dea1fcbded743c03500a7544d3201e`](https://github.com/LIghtJUNction/ztype/commit/c89dd36dc7dea1fcbded743c03500a7544d3201e) |
| SSMCP兼容修复 | [`add39e18ff92680ff3ac0c3e911407956e20b228`](https://github.com/LIghtJUNction/ssmcp/commit/add39e18ff92680ff3ac0c3e911407956e20b228) |
| skills导入/预检 | [`201a7508d3ed2928295ebaf0853ea4528212b980`](https://github.com/LIghtJUNction/zuse-skills/commit/201a7508d3ed2928295ebaf0853ea4528212b980) |
| zrc CLI验证 | [`31f37e9bb8f5c5adcf195f68692c47ec7ea26705`](https://github.com/LIghtJUNction/zrc/commit/31f37e9bb8f5c5adcf195f68692c47ec7ea26705) |
| zmcl受测同步 | [`67f227e13f47a7e93545be494ce6b19b867d2ee9`](https://github.com/LIghtJUNction/zmcl/commit/67f227e13f47a7e93545be494ce6b19b867d2ee9) |
| suite公开等价来源 | [`34563be624b45ad4d931f05f7c3c9bda94ecac2e`](https://github.com/LIghtJUNction/oh-my-ztty/commit/34563be624b45ad4d931f05f7c3c9bda94ecac2e) |

这张表不是“所有最新HEAD均已验收”的声明。suite实际检查/构建来源为本地9ae64496b2055830b174c4e2012163cc81c09a1e；公开34563be6与它仅有观察时间戳差异。

已公开的zuse-std是源码包。隔离聚合准备树将其登记为extension、manifests=[]、requires=["zuse"]，并补充SSMCP对独立Zuse CLI的运行时关系。上述总仓注册仍保留在准备分支，未由本次文档提交合入。SSMCP没有嵌入zuse-computer Cargo依赖。

## 实际发现和修复

对旧 SSMCP `ffb7f32f` 的真实验证确认：官方下载、SHA256 和大小检查通过，但安装阶段拒绝了新资料成员 `examples/session_client.py`。这不是 Zuse 已安装 Git 版本的运行故障。

公开修复 `add39e18ff92680ff3ac0c3e911407956e20b228` 接受发行脚本定义的顶层、普通、无执行权限 `examples/*.py` 和十五个精确技能资料路径。安装器仍只提取预期的主程序；资料文件不安装、不执行，已有路径、链接、重复成员、权限、大小和摘要检查继续生效。该源码还包含机器可读的 JSON 操作错误回执改进。

该提交的树 `c184077be2ae416bbf2ca88cfb9da82e974471f8` 与固定验收输入一致。实际测试覆盖官方下载、安装、版本、外部 PATH 优先、卸载、外部 Cargo 安装前后不变，以及固定输入前后不变；本地回环/PTY 的用户等待流程也通过。

## 已完成的消费者验证

源码和运行时分别绑定。5f/9caf表示源码提交/二进制摘要；它是已验证阶段，不再称当前安装。

| 检查范围 | 实际结果 | 来源与边界 |
|---|---|---|
| 公开标准库精确锁 | 22函数、API43步、深度5分形243步，清单/锁未变 | std d79f43f8；稳定标签、5f阶段及最后6e88安装分别短验 |
| 公开会话客户端 | 标量7步、跨任务函数复用4步、close/socket清理通过 | 5f与6e88各自独立私有会话，仅timer/functions |
| zuse-skills | 14项原生导入/描述/预检通过；新GTK默认1跳过、0通过 | 201a源+5f/9caf；未外推到6e88，未执行应用函数体 |
| ztype | all-targets --locked --offline：73通过、1忽略，10.131秒 | c89dd36d，真实锁Zuse5f/Zmcpio97f |
| SSMCP | computer24通过/1忽略；JSON错误契约1通过；Clippy、release及真实管理生命周期通过 | add39e18，完整树c184077b |
| zrc | Rust1、原生CLI12、投影边界2全部通过，零跳过；fmt/Clippy通过 | 31f37e9b，冻结同源程序和锁 |
| zmcl | 114通过、零失败/忽略；Clippy通过 | 67f227e1，集成树与受测树均145b3403 |
| suite | 181通过、零跳过；语法/编译检查及真实归档安装通过 | 受测9ae；公开345的时间戳差异另证 |

最后一次已验安装为6e88dd885eb73545a1ab6a9cd50097ef63fba423，版本0.6.0，SHA256为a138cfc152502a03b6ce13cbbc12d06374d14440dc733f2257ad3d874c9302e8、2651440字节。短验时间为 2026-11-21T20:41:56.710688+00:00 至 2026-11-21T20:41:57.030126+00:00，覆盖表中的stdlib22/API43/分形243和会话7/4；安装身份前后不变、host input为0。该短验不等于审阅其Zmcpio0.5.3依赖全部源码，也不等于全图验收。

zuse-skills的216→201a仅新增194行私有GTK/AT-SPI fixture，其余23个既有文件blob/模式相同。新增项仅完成语法和默认skip门禁，没有启用。以下历史结果保持原来源：


- 标准库使用已公开的 `v0.1.0` 精确锁，稳定标签安装和所列默认分支安装阶段各自复验得到 22 个函数；API 预检为 43 步，深度 5 的 Sierpinski 预检为 243 个三角形步骤。安装清单和锁的摘要前后相同，没有重新下载或发布。
- zuse-skills 在稳定标签运行时完成 14 个原生导入、描述和预检；通用批次为 32 通过、2 个浏览器项跳过，随后使用同一运行时单独启用私有无头 Chromium fixture，两项均通过。5f/9caf 运行时的201a源只补验14项目录和预检，没有重复执行上述完整批次或浏览器项。
- ztype 的 1 个忽略项需要外部完整词典 `ZTYPE_TEST_DICTIONARY`；本轮没有把它计作通过。
- SSMCP 归档/管理测试的 1 个忽略项是由另一个通过的测试显式启动的隔离子进程 fixture，仍保留测试器报告的原始 24/1 计数。Clippy 退出 0，同时保留原有 Cargo manifest 的 `qrcodegen` 未使用依赖警告。
- Zuse 的早期完整 Rust 基线为 473 通过、19 忽略；最后改动路径的门禁为 192 通过、4 忽略，并通过 fmt、Clippy 和构建。两个来源及范围分开记录，不把 473 宣称为最后候选的重新全量执行。

## Suite新归档与真实安装

公开34563be624b45ad4d931f05f7c3c9bda94ecac2e与受测9ae64496只相差dependencies.lock.json的updated_at和六个observed_at。六个组件SHA/gitlink以及所有其他文件内容和模式相同，因此复用既有公开提交。构建回执记录受测9ae；归档BUILD保留六个实际组件SHA及sources_updated_at=2026-11-21T19:49:22+00:00，没有改标为从345构建。

归档oh-my-ztty-0.2.6-linux-x86_64.tar.gz为7,997,724字节，SHA256为：

`7d3c464495b1920de7e54879eb8b28aaccaeb2a5d26cce133e9489a0ceb83a3e`

实际build233.461秒、smoke1.518秒、临时HOME首次安装0.615秒、重复安装0.415秒、卸载0.064秒，均退出0；已有文件保留、工作树clean。它是本轮源码快照验证归档，没有覆盖既有0.2.6正式发行资产。

包内SSMCP来自add39e18，SHA256为56b73a7615e94affea1637fe8fc1caceccdc0124e64255f2eaa8e51fc265a742；实际Zuse管理安装、版本/timer、卸载阶段2.068秒，退出0。官方归档含74个成员，安装只落receipt.json和zuse；受管理Zuse摘要b5b0941bb98016880cd248159626d5aafd7ccbbb9057d928f535700cd13728bd。执行时外部安装仍为5f/9caf，其摘要、dev/inode/size前后不变。

## 聚合官方命令：未接受候选

命令作用于保留的隔离候选，父提交6e786250812849079c870804ce4141b74f88f7d3。sync301结束于2026-11-21T20:28:48.668643+00:00；31c记录于2026-11-21T20:34:15.664014+00:00至2026-11-21T20:34:21.775148+00:00。这不是对后来全部公开HEAD的重新验收。

| 官方命令 | 退出码 | 秒 |
|---|---:|---:|
| `python3 scripts/project_z.py sync` | 1 | 51.415 |
| `python3 scripts/project_z.py check` | 1 | 2.816 |
| `python3 scripts/project_z.py resolve --all` | 1 | 1.969 |
| `python3 scripts/project_z.py impact --repositories zuse` | 0 | 0.766 |

sync在嵌套源码指针校验退出。check列出来源、锁、检出和生成索引差异；resolve在前置校验被拒绝，不能称全工作区解析成功。impact实际成功，得到oh-my-ztty、ssmcp、zrc、ztype、zuse、zuse-skills、zuse-std。相关Cargo元数据操作由同一外层共享锁串行执行。

### 301时的六条差异及后续进展

| 候选关系 | 当时记录 → canonical目标 | 后续一次公开观察 |
|---|---|---|
| ztty/crates/zgpui | 174a8b73 → eeb909e9 | ztty c0f195d9已对齐 |
| ztty/crates/zterm | 15174fec → c0860ae4 | 同一ztty c0f195d9已对齐 |
| zcalld/apps/zcall-gui | 95cbe443 → a97c3bfe | 20:32:28Z所见父d22ccce7仍旧pin |
| lmm-api-source/apps/cli | 260a1eff → b97b5c26 | 20:32:28Z所见父ddfe1d14仍旧pin |
| ztype/vendor/zgpui | 174a8b73 → eeb909e9 | ztype c545d587已对齐 |
| zmcl/vendor/zgpui | 174a8b73 → eeb909e9 | zmcl6a83e621已对齐 |

可复用公开提交为 [`c0f195d9b93065040b4efef35f3615831db11b38`](https://github.com/LIghtJUNction/ztty/commit/c0f195d9b93065040b4efef35f3615831db11b38)、[`c545d587dc1a43496b323149df79aaa45debb85e`](https://github.com/LIghtJUNction/ztype/commit/c545d587dc1a43496b323149df79aaa45debb85e)、[`6a83e6215d583a4e03c02a3e07df576cc599081d`](https://github.com/LIghtJUNction/zmcl/commit/6a83e6215d583a4e03c02a3e07df576cc599081d)，观察于2026-11-21T20:33:36Z。这些后续推进不是本轮GUI实跑，不能说六条仍全部未修，也不能改写301通过状态。

### 责任维护流与未完成事项

| 责任仓库/维护流 | 事实边界与下一步 |
|---|---|
| zgpui/zterm及GUI消费者 | eeb引入25文件、约4365行的真实材质/透视/字体/emoji变化；zterm锁跟随新实现。需绑定新GUI行为/包装回执、完成消费者及suite传播，再验全图；不能按纯锁等价处理 |
| zcalld/zcall-gui | 父侧这一关系是被exclude的应用gitlink，但目标a97引入新GUI行为。需对应GUI cohort验收后正常更新父指针 |
| lmm-api-source/lmm CLI | CLI b97只更新zhex09df→9fc；该固定zhex差异仅新增14行测试、生产源码/manifest相同。但31c另报services/core/Cargo.lock也仍锁09df。需分别更新CLI指针和Core锁，记录对应来源；整个父仓不只是一个gitlink缺口 |
| Zuse/Zmcpio/ztype依赖维护流 | 31c报告Zuse5f/ztypec89锁97f、canonical为222d6ed3。97f→222的50个Rust/Cargo文件blob和模式相同，但六个发行工具/workflow/docs/test文件改变；这是Zuse自身来源一致性缺口，不能归入GUI阻断 |

最后一次公开查询又观察到Zuse6e88锁Zmcpio0.5.3@89a247ac274bcd96b760dd9e7dcb0d4d924a901e，ztype c545仍锁97f。89a源码不在本次诊断范围；97f→222的等价证据不能套到89a。6e88安装仅完成前述有界短验，不代表该依赖传播已经全图闭合。随后停止追逐新HEAD。

### 自有检出残留已清理

31c中的suite/SSMCP、zcall-gui/zgpui、zmcl/zclap等递归checkout差异，是sync在递归更新前退出留下的自有准备状态，不能归责于外部owner。已使用已有canonical本地对象，将它们和随后发现的zharness/zdot/zrc/zi18n正常detached到各父记录。零网络下载、零Cargo/GUI；最终46仓checkout_errors=[]。

原失败回执没有覆盖。清理后只复验纯Git检出，不将check/resolve改标成功。catalog、生成索引、注册和候选gitlinks仍保留在隔离准备分支，尚未接受。原Project Z活动检出的既有改动没有被覆盖。

## 稳定发行资产

Zuse 发布工作流 [44937714591](https://github.com/LIghtJUNction/zuse/actions/runs/44937714591) 的五个目标成功。独立沙箱实际下载全部五个归档并核对 GitHub 的摘要和大小；各归档中的 `session_client.py` 与三个 `SKILL.md` 内容一致，Windows 文本按 CRLF 归一化比较。

| 归档 | 字节数 | SHA256 |
|---|---:|---|
| [zuse-v0.6.0-x86_64-unknown-linux-gnu.tar.gz](https://github.com/LIghtJUNction/zuse/releases/download/v0.6.0/zuse-v0.6.0-x86_64-unknown-linux-gnu.tar.gz) | 1399658 | `6a38b67eddc26a5671658d4ea4b767922e7be78f44e5af480fa3ba14dd3bac15` |
| [zuse-v0.6.0-aarch64-unknown-linux-gnu.tar.gz](https://github.com/LIghtJUNction/zuse/releases/download/v0.6.0/zuse-v0.6.0-aarch64-unknown-linux-gnu.tar.gz) | 1299785 | `ca52cfbf33904db0d0aac7bd9ead1a8f5de5ed3f41b49b468a28304e5a676852` |
| [zuse-v0.6.0-x86_64-apple-darwin.tar.gz](https://github.com/LIghtJUNction/zuse/releases/download/v0.6.0/zuse-v0.6.0-x86_64-apple-darwin.tar.gz) | 1229675 | `cbabbd88484e1faa6ae4069009599aab94fdac3f111ee898cb19bd8c435a6609` |
| [zuse-v0.6.0-aarch64-apple-darwin.tar.gz](https://github.com/LIghtJUNction/zuse/releases/download/v0.6.0/zuse-v0.6.0-aarch64-apple-darwin.tar.gz) | 1124933 | `6fc4d131e6789227a8eb70e11ec3bd778859e020ca0d95bfc445a870101b4dff` |
| [zuse-v0.6.0-x86_64-pc-windows-msvc.zip](https://github.com/LIghtJUNction/zuse/releases/download/v0.6.0/zuse-v0.6.0-x86_64-pc-windows-msvc.zip) | 1183326 | `3ff72598c7ed4bba23acafbb2e9f6df5538af4c361f4672e719f42cd35a22106` |

Linux x86_64 的发行二进制实际运行 `--version`，返回 `zuse 0.6.0`、退出 0，二进制 SHA256 为 `b5b0941bb98016880cd248159626d5aafd7ccbbb9057d928f535700cd13728bd`。其余平台本轮只验证构建和归档内容，没有执行对应二进制。

## 验收边界

本轮消费者检查未向用户桌面发送输入。私有浏览器、临时HOME、合成回环/PTY、静态预检及私有会话只证明各自覆盖的接口。

主机native-evdev路径通过过真实只读预检，input_events=0。用户离开后没有执行物理按键、最终绘画或实机对战验收；这部分仍待用户回来，不能由软件测试、发行构建或包管理验证代替。

仓库为[LIghtJUNction/project-z](https://github.com/LIghtJUNction/project-z)。本提交仅发布本报告和[机器可读证据](../evidence/2026-11-22/zuse-0.6.0-propagation.json)，包含来源、命令、原始失败、回执摘要、后续公开观察和检出修复。它不宣称总仓集成完成，也不在文内自嵌尚未生成的提交SHA。
