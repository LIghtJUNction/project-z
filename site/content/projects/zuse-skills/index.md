# zuse-skills

把 GUI 能力封装成可原生导入、带简短说明的 `.zuse` 函数。Zuse 负责解析、导入、参数替换和执行；本仓库提供 ChatGPT 桌面版的观察、条件草稿准备和独立动作声明，微信、QQ 的只读模块，以及自有 Chromium 的操作验收模块。

桌面模块不请求焦点，不调用系统键鼠。它们要求调用者先确认应用窗口范围；应用不提供后台访问能力时返回错误。**ChatGPT 的空草稿与进程守卫机制已接入，真实 ChatGPT Desktop 的读写和发送仍处于 blocked，尚未验收。** 最近记录的目标没有可用 AT-SPI 应用入口；模块声明和预检不能证明目标应用开放了后台控制接口。

## 原生入口

完整目录预检和条件草稿准备需要 [Zuse 0.5](https://github.com/LIghtJUNction/zuse) 或具备相同守卫接口的运行时。原有 `chatgpt_controls(scope)`、`chatgpt_find(scope, window, label)` 的定义与签名保持不变。可从上游正式发行安装；开发时使用最新公开源码：

```sh
cargo install --locked --git https://github.com/LIghtJUNction/zuse.git zuse-computer
zuse --version
git clone https://github.com/LIghtJUNction/zuse-skills.git
cd zuse-skills
```

先查看一个模块的函数与说明。导入只注册声明；不会执行函数体，也不会启动浏览器：

```sh
zuse eval 'import(path="skills/chatgpt-desktop/module.zuse",as="chatgpt"); functions(namespace="chatgpt")' --read-only
```

`functions()` 原生返回名称、参数顺序、`///` 说明及源码位置。查看全部 14 个函数，其中 ChatGPT 模块导出 8 个：

```sh
zuse run examples/catalog.zuse --read-only
```

执行自有浏览器验收，填字段、点击 Preview，再读回本地页面结果：

```sh
zuse run examples/chromium-preview.zuse
```

它新建私有无头 Chromium 会话，只访问模块内的 `data:` 页面，不连接现有浏览器或账号；完成后关闭会话。需要已安装的 Chromium/Chrome。可用 `ZUSE_BROWSER` 指定其可执行文件，保留浏览器沙箱。

### 检查具体调用，不启动浏览器

原生 Zuse 可以直接预检含引号的参数：

```sh
zuse eval 'import(path="skills/chromium/module.zuse",as="fixture"); fixture.chromium_fixture(text="他说 \"hello\"；本地预览")' --dry-run
```

可选 Python 适配器也提供具体调用的预检入口：

```sh
python3 zskills.py plan chromium_fixture '"他说 \"hello\"；路径 C:\\tmp\\demo"'
python3 zskills.py run chromium_fixture '"仅检查"' --dry-run
```

原生 `--dry-run` 返回步骤计划；适配器另附实际参数和 `function_executed:false`。两种方式都不会启动浏览器或执行应用操作。预检通过只说明该程序满足语法和策略，不证明应用存在或目标正确。正常 `run` 会重新检查当前模块，不使用旧预检结果跳过检查。

### 一次导入，多次查询

`zuse shell --read-only` 会保留模块定义，直到退出。以下两行输入到同一 shell：

```zuse
import(path="skills/chatgpt-desktop/module.zuse", as="chatgpt")
functions(namespace="chatgpt")
```

脚本中的相对导入从脚本所在目录解析；`eval` 和交互 shell 的相对路径从启动目录解析。独立的 CLI 进程不共享定义或浏览器会话。

## 桌面模块

| 模块 | 原生函数 | 已实现的行为 |
| --- | --- | --- |
| ChatGPT 桌面版 | `chatgpt_controls(scope)`、`chatgpt_find(scope, window, label)` | 保留原有只读接口：读取指定 AT-SPI 子树；查找唯一精确标签 |
| ChatGPT 原生观察 | `windows()`、`inspect_window(scope)`、`read_conversation(scope)`、`read_draft(editor)` | 列出窗口供识别，或观察已经确认的窗口、会话、编辑器子树 |
| ChatGPT 草稿机制 | `prepare_draft(editor, pid, message)` | 要求进程匹配、编辑器精确为空，再对同一对象写入并读回；不发送 |
| ChatGPT 独立动作 | `send_prepared(send_button, action_index)` | 显式授权后调用一个新观察到的原生动作；发送结果仍需观察确认 |
| 微信 | `wechat_controls(scope)`、`wechat_find(scope, window, label)` | 同上，范围由调用者确认属于微信 |
| QQ | `qq_controls(scope)`、`qq_find(scope, window, label)` | 同上，范围由调用者确认属于 QQ |
| Chromium | `chromium_fixture(text)` | 在自有无头浏览器中填写、点击并读取本地验收页面 |
| 编写工具 | `zuse_capabilities()` | 读取当前运行时和后端能力 |

先使用宿主已授权的只读电脑工具，确认进程、窗口 ID 和 AT-SPI 窗口路径。`scope` 必须属于目标应用的明确窗口或更小子树，`window` 必须是同一个窗口的原生 ID，`label` 使用刚观察到的完整标签。不要用全桌面范围，也不要把 `active` 当作窗口身份。缺少这组证据时停止调用该桌面函数。

例如，**仅在已验证 `0/12/0` 和 `0x123456` 确为目标窗口后**：

```zuse
import(path="skills/chatgpt-desktop/module.zuse", as="chatgpt")
chatgpt.chatgpt_controls(scope="0/12/0")
chatgpt.chatgpt_find(scope="0/12/0", window="0x123456", label="New chat")
```

这些路径与 ID 只是语法示例，不能直接用于真实会话。应用重启、窗口或无障碍树变化后需要重新确认。原生 `*_controls` 通过有界 `watch` 取得所选窗口子树的观察结果，然后立即 `watch.close`；快照位于返回的 `watch` 结果中的 `receipt.observation`，不会留下持续订阅。该快照可能含该子树内的文本；`*_find` 返回目标描述，不点击它。查不到、匹配不唯一、后端不可用或范围不满足条件时不进行输入。

最近一次真实应用记录确认 ChatGPT 窗口和进程稳定存在。正常 AT-SPI 短时监听前和监听期间的完整根枚举分别记录 10、15 个应用，均无错误或截断，但没有 ChatGPT 目标进程。监听结束后服务状态恢复，观察进程退出；全程没有桌面输入、读取应用文本字段或主动修改设置。该记录仍未提供可信 `scope`；本次模块同步没有重新探测目标。微信、QQ 尚未完成真实应用验收。Windows/macOS 的原生无障碍支持不能由 Linux AT-SPI 测试推断。

### 条件草稿与单独发送

六个新增函数与[上游原生模块](https://github.com/LIghtJUNction/zuse/blob/main/skills/zuse/assets/chatgpt-desktop.zuse)同名、同参数、同函数体。先确认原生进程、窗口、唯一的目标会话和编辑器，再读草稿；缺少 Text 接口、空值之外的现有文字、空白草稿或不完整观察都不能作为可覆盖依据。

`prepare_draft` 将 `expected_text=""` 和调用者观察到的正整数 `pid` 交给 Zuse。Linux AT-SPI 在同一个原生对象上检查条件、写入并读回；这些应用调用不是原子事务，调用者仍需确认会话身份并响应用户接管。适配器保留 `edit` 的完整守卫回执和 `observation`，并返回 `send_performed:false`。写入后观察不完整时，错误明确提示已经提交写入，需要先检查当前编辑器再决定下一步。

条件编辑当前仅支持 Linux AT-SPI；Windows/macOS 在输入前拒绝带条件的编辑。运行时预检只验证调用契约，不能证明当地无障碍后端可用。

以下仅预检语法和策略；示例路径与 PID 不代表真实目标：

```sh
python3 zskills.py plan prepare_draft '"0/1/0/0"' 42 '"待核验的草稿"'
python3 zskills.py plan send_prepared '"0/1/0/1"' 0
```

`pid`、`action_index` 使用 JSON 整数，其余参数仍为最多 4096 UTF-8 字节的 JSON 字符串。预检写入或发送不访问应用；两者在 `--read-only` 下均被原生运行时拒绝。

发送需要对具体目标和消息的明确授权。适配器的实际 `run send_prepared` 还要求 `--authorize-send`，Python 调用要求 `authorize_send=True`；计划和导入不授予发送权限。该参数记录调用者已经取得授权，不替代宿主输入权限，也不会自动核验会话或草稿。调用前重新检查目标、草稿、发送节点和其提供的动作索引，调用后观察同一会话确认结果。单次原生动作回执始终标注 `delivery_confirmed:false`，不会据此宣称消息送达或自动重试。

## 机器可读的能力与阻断原因

```sh
python3 zskills.py capabilities chatgpt-desktop
python3 zskills.py capabilities wechat
python3 zskills.py capabilities qq
```

这个入口只执行原生导入和条件草稿的全程序预检，不枚举真实应用、不访问聊天内容。`runtime.native_import` 表示导入能力；`runtime.guarded_prepare` 单独报告守卫调用能否通过预检，导入成功不会被当作新接口可用。缺少兼容运行时时返回具体阻断原因。

ChatGPT 的 `prepare`、`send` 返回 `implemented:true` 表示已有函数机制，同时保持 `state:blocked`、`application_accepted:false` 和 `target_checked:false`。`last_target_assessment` 引用最近 AT-SPI 入口缺失的历史证据；它不是本次实时探测。只读操作仍要求 `requires_verified_target`。微信、QQ 的写入与发送继续返回 `implemented:false`、`background_adapter_not_implemented`。

[完整应用验收条件与当前差距](docs/acceptance.md) 分别记录模块可导入、后端可访问、草稿写入、显式发送及结果确认。**真实 ChatGPT 的后台写入与发送尚未验收；微信、QQ 尚未实现写入和发送适配。**

## 紧凑输出与并行调用

`zskills.py` 是可选的 Python 3.10+ 适配器。它把导入和执行交给 Zuse，不再自行解释 `.zuse`。无需第三方 Python 依赖。

```sh
python3 zskills.py list
python3 zskills.py list --json
python3 zskills.py run zuse_capabilities
python3 zskills.py run chromium_fixture '"本地预览"'
python3 zskills.py parallel '[["zuse_capabilities"],["zuse_capabilities"]]'
```

原有桌面 `*_controls` 继续要求 `scope`，`*_find` 继续要求 `scope, window, label`。新增的 `pid` 和 `action_index` 按 JSON 整数传入，其他参数使用 JSON 字符串。选择特定运行时：`python3 zskills.py --zuse /path/to/zuse check`。

适配器负责：

- 从原生 `functions()` 读取名称与说明，核对 `catalog.json` 的参数和后端声明，省去反复读取完整模块。
- 对 `*_controls` 只保留最多 40 个控件的角色与标签，每个标签最多 100 字符，不输出 `text`/值字段或坐标。可访问名称由目标应用提供，仍可能含用户内容；此投影不承诺任意文本脱敏。后端返回不完整子树时明确报错。
- 新的观察函数返回有界完整子树，可能包含会话或草稿文字；请求前确认范围。条件草稿保留编辑回执和观察结果，单独发送保留动作回执并明确尚未确认送达。
- 一批最多 8 个独立调用、最多 4 个工作进程。先为每一项执行真实 Zuse 全程序预检，全部通过后才执行第一项；结果保持输入顺序，每项失败单独返回。每个执行进程有 30 秒期限，取消后最多等待 18 秒退出。

并行使用独立运行时，适合只读查询或分别拥有的浏览器实例。适配器在执行第一项前拒绝任何包含原生桌面写入或发送的并行批次；这些动作需要独立执行。预检检查语法、参数、只读权限和允许的操作类别；被导入的模块仍是需要审阅的程序源码。

## 验证

```sh
python3 zskills.py check
ZUSE_BIN=/path/to/zuse python3 -m unittest discover -s tests -v
```

2026-11-22 01:51（Asia/Taipei），使用实际从 crates.io 安装的 **zuse-computer 0.5.0** 对模块源码 `fce48d78dcbedbecaaa56a09fdf11b12b9a6b09a` 完成发布后复验：14 个函数检查通过，**34 项测试全部通过，0 跳过，耗时 2.122 秒**。两项私有 Chromium 测试均实际执行。二进制、公开归档及测试日志摘要见[发布版验收收据](docs/validation-zuse-0.5.0.json)。真实 ChatGPT 的草稿和发送仍未验收，微信、QQ 的写入适配仍未实现。

本次六函数同步在 Zuse 0.5 候选源码的 dev 构建上完成。沙箱的 14 个函数原生 check 通过，32 项测试通过，2 项自有浏览器测试默认跳过；随后开发机启用私有 Chromium 验收，**34 项全部通过，耗时 2.650 秒**。验证时该候选构建的版本字符串仍为 `0.4.2`，守卫接口通过实际预检确认，没有把它记为已发布的 0.5 二进制。测试没有访问真实账号、操作用户桌面或发送消息，也未重跑旧 Zuse 0.4.0 发行二进制。新增覆盖包括整数参数、输入只读拒绝、独立发送授权、写入批次拒绝、完整编辑回执和诚实能力元数据。

以下是原版本的历史验证，不能用来证明新增草稿或发送能力已通过真实应用验收。2026-11-21 对源码 `dbe3533684e39f90e7a7a05d55638629c242bb91` 完成：

| 环境 | 运行时来源 | 结果 |
| --- | --- | --- |
| 沙箱 | Zuse 0.4.0 Git `0016f96067d1e4672c62be9d8008d210edcdae2d`，dev 构建 | 22 项测试通过，2 项浏览器测试默认跳过；该沙箱 Chromium 启动曾收到 SIGABRT |
| 原生 Linux 开发机 | 已发表 `zuse-computer 0.4.0` 包的原生发布验证阶段已有 dev 构建 | 原生 check 通过；**24/24 项测试通过，耗时 2.245 秒**，包含两个自有浏览器测试 |

原生浏览器验收实际完成单会话的字段填写、Preview 点击和结果读回，以及两个私有会话并行时的结果隔离。运行时所用包源码与已发表归档的全部 200 个文件逐字节匹配；本轮没有重新编译、从沙箱传入二进制或全局安装。测试没有连接真实账号，也没有操作用户桌面。

历史测试覆盖原生导入与说明、相对路径、持久 shell、导入无顶层副作用、参数注入、只读预检、子树边界、输出预算、并行预检顺序、具体调用计划及能力目录。当时的 8 个导出函数通过原生预检；真实 ChatGPT、微信、QQ 的读写支持按上文边界单独记录。

在具备正常 Chromium 运行条件的隔离环境复验：

```sh
ZUSE_BIN=/path/to/zuse ZUSE_SKILLS_BROWSER_TESTS=1 python3 -m unittest discover -s tests -v
```

运行时与归档 SHA256、测试日志 SHA256、AT-SPI 观察结果见 [验收收据](docs/validation-2026-11-21.json)。本地网页验收不替代真实应用的草稿或发送验收。

[编写技能](skills/zuse-skill-creator/SKILL.md) · [zgpui 原生后端提案](docs/zgpui-native.md) · [上游原生模块实现](https://github.com/LIghtJUNction/zuse/blob/main/src/script/modules.rs)
