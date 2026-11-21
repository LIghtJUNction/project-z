# U/r12 Gate35 独立原件复核

**结论：0 项阻断、0 项实质证据不一致。** 本次独立读取U自己的回执、日志与产物，确认固定Gate35全部退出0。范围是已经完成的构建与测试门禁；UI/runtime、最终消费者验收、P1及最终44仓图仍需各自实际结果。

- 源码：[784370b5fe1b817c788273a5f7b1ab826c743965](https://github.com/LIghtJUNction/ssmcp/commit/784370b5fe1b817c788273a5f7b1ab826c743965)。
- tree：2c60d011da8c2b31aefd80367bf7f19e28f10b62；唯一父提交为Q647bce2ec9cf74beab43adea831c2e0712d28ea8。
- 运行编号：f38d16ea5cc34c21c5a56313245625a1；版本元数据0.10.25。
- 完整Gate原件：1,282,781字节，SHA256 cf17822a03c045fff67b2015e196fee0e1edaf45df55b0761331080eac496000。
- 独立复核时间：2026-11-21T03:22:29.783853+00:00。未执行产品、Cargo、候选验证器或取得锁。

## 实际计数

| 范围 | 本轮结果 | 计数边界 |
|---|---|---|
| 全部门禁 | 35个阶段退出0 | 26个阶段有Rust父测试汇总 |
| library-private | 2050 passed、23 ignored、6 filtered | HOST6不在该组执行 |
| library-host | 6 passed、0 ignored、2073 filtered | 两组互斥，合计2079个名字 |
| 普通集成测试 | 19个target、101 passed | 不包括下一行worker |
| 独立worker | 1个ignored-exact测试passed | 20个集成target合计102 |
| 额外强制ignored | 4个阶段、14 passed | 分别2、7、3、2 |
| 原需求17例 | 均有唯一原始ok行 | 已包含于2050，不另加 |

35份日志和55组probe的stdout/stderr均已读取。26份父汇总与原日志最后一条汇总、选定名字及原list结果一致。嵌套子测试汇总按原行号核对，未重复加总。与Q仅比较覆盖合同；U的执行结果、耗时和编译证据全部来自U本轮。

## 源码与实际编译

212份独立文本原件已经读取并核对SHA。导出源码的1849项清单包括1545个文件和304个目录，当前字节及mode与清单完全一致。五份源码archive的摘要和PAX commit标识与固定主仓及四个gitlink一致。

Cargo metadata前后原字节相同：277个包包含264个registry、12个Git、1个root path。12个Git包来自11个checkout，因为zplugin及macros共用仓库。9个launcher输入前后摘要相同，本复核又读取其实际文件核对摘要。未重新审计所有外部registry/Git依赖树。

四个真实构建阶段的Cargo JSON归档逐项等于原构建日志JSON。26个选定产物均记录fresh=false；workspace wrapper的实际cwd、源文件、package、manifest、metadata target和profile对应本轮U。**release使用源码声明的opt-level=z**。保存的关键编译参数能够推导link路径，原件中link输出、Cargo executable和受控副本的字节数/SHA一致。

两个Clippy命令均退出0，原日志仍有Cargo的unused dependency qrcodegen及manifest warning，本报告不称零warning。原wrapper保存关键参数、数量和完整argv摘要，但没有保存完整argv；未声称独立重算未保存的完整argv摘要。

## 五个受控产物复哈希

五个现有副本均完整读取，前后inode、大小、mtime未变，并匹配U自身编译/复制记录。未读取当前共享target二进制，也未因与Q同hash就复用Q编译证明。

| 产物 | 字节数 | 本次读取SHA256 |
|---|---:|---|
| library-test-fixture | 166657104 | da95c523626a6de2fdeeb7372992b8a3678e7348ce84c42f367fe7fc4dec2be0 |
| ssmcp | 15738696 | 2dbab2aa293ae411de20f9839d574bf62ef79a644710884a81f6fe6239717e35 |
| ssmcp-frontend | 1386584 | 2e19f8ad2fea673f899bbfc44449161e072381571946b85e3c6a5dc7e8325a06 |
| ssmcpd | 8176168 | e2e63fcfc63c05ca81907c976f8f3dda2aee65db9efa6d0d242fba69b95271b0 |
| vt_snapshot | 440984 | efdbeb3f200fcf4404b2612d836433047ecc90eb0744f345fc971ee7441db97f |

它们是一个debug库测试可执行文件、三个release binary和一个release example。供三组集成测试使用的另一个debug client helper已包含于26个编译记录，其本轮三个前后摘要检查一致；没有重复读取当前共享helper。

## 退出与锁的边界

原unit启动、outer及launcher对应同一invocation da41b3070b844d3fb69af4bd8b3b8c24。launcher退出0并绑定最终Gate摘要、运行编号，outer也退出0，开始/结束顺序一致。实际读取的controller仅取得source-author锁；launcher才以NONBLOCK取得共享Cargo锁，两处finally均关闭各自fd。

03:17:20.877110 UTC的独立单点观察显示unit已经collected/not-found、inactive/dead、MainPID0、ControlGroup空，原PID1184034与1184045均不存在。该观察不替代历史systemd退出事件，不证明全期内核锁记录或当前全局锁空闲。历史完成结论来自原退出回执及完整Gate，不来自collected unit的Result字段。

## 原件入口

- [结构化复核](ssmcp-U-r12-gate-independent-review.json)
- [212份文本索引](original-text-index.json)
- [详细只读提取](raw-audit-r2.json)
- [覆盖合同对照](contract-comparison.json)
- [当前unit/PID观察](current-unit-observation.json)
- [固定GitHub commit原件](github-U-commit-original.json)
- [源码archive提交标识](archive-commit-headers.json)

封存Q22报告、C失败记录、Q通过记录及活动源码均未修改。
