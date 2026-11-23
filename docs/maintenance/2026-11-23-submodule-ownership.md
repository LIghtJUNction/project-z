# 未初始化子模块的元数据归属检查

日期：2026-11-23。原始验证基线：`573a7070dbeb0101920fbe1bf137e7dcca80619d`。公共主线集成基线：`5b6ed98b630197fa7ef0f2bf7851d5c31aec9650`。

`sync_sources` 现在会在放行空目录或缺失目录前，检查 Git 保留的子模块元数据。若 `core.worktree` 指向另一个 checkout，预检会拒绝同步，并给出元数据目录、实际目标和请求目标。另一个目标是否仍然存在，不影响这个判断。该检查不修改配置，也不接管其他 checkout 的元数据。实现见 [`verify_retained_submodule` 和 `verify_source_checkout`](../../scripts/project_z.py)。

## 原因与行为

工作目录为空，只说明源码文件没有放在这里；Git 仍可能在父仓库的模块目录中保存对象、引用和配置。原来的 `allow_uninitialized` 分支只检查工作目录，满足“缺失或为空”后立即返回，因此没有判断保留的元数据属于哪个工作目录。

本次回归在临时仓库中构造这一状态：把第三层子模块移到另一个位置，保留模块 gitdir，并将 `core.worktree` 指向那个位置。随后分别让请求目录为空或缺失、原归属目标存在或缺失。四种组合在旧实现上均被预检接受，新增的拒绝断言因此失败。这证明了预检缺口；它不能证明共享开发机上既有 zrc 配置异常的历史写入者，也不能据此把异常归因于普通 linked worktree 初始化。[回归实现](../../tests/test_recursive_sources.py)

新检查沿用已有预检顺序，发生在 `latest_heads`、clone、fetch、checkout、递归 submodule sync/update 之前：

1. 由 Git 读取父仓库 `.gitmodules`，根据路径找到真实模块名。模块名不由目录 basename 推导。
2. 在该父仓库中调用 `git rev-parse --path-format=absolute --git-path modules/<name>`，让 Git 选择当前 checkout 的模块命名空间。linked worktree 的私有目录因此得到保留。
3. 如果对应模块配置存在，直接读取配置中的 `core.worktree`，按 Git 的 pathname 语法展开，并以模块 gitdir 为基准解析相对路径。
4. 将解析结果与请求 checkout 的规范路径比较。任一记录指向其他位置即拒绝；不存在模块配置或没有 `core.worktree` 时，继续原来的初始化流程。

递归检查显式传递直接父仓库，顶层检查使用传入的协调根目录。读取配置文件不会先进入一个可能已经失效的 worktree，因此目标目录缺失时仍能完成归属判断。[调用顺序与实现](../../scripts/project_z.py)

## 本地验证

测试扩展了现有 `tests/test_recursive_sources.py`，复用 A → B → C → D 的真实 Git fixture。注册名统一使用 `registered.source`，工作目录仍为 `nested`，以覆盖名称与路径不同的情况。所有 clone/fetch 来源都是临时本地仓库，Git 协议限制为 `file`；没有网络请求或 Cargo 调用。

| 场景 | 实际断言 |
| --- | --- |
| 请求目录为空，归属目标存在 | 拒绝；没有 clone/fetch/checkout/submodule init/sync/update；配置及另一个 checkout 的 HEAD、toplevel、status、源码内容不变 |
| 请求目录为空，归属目标缺失 | 拒绝；配置不变，不创建目标 |
| 请求目录缺失，归属目标存在 | 拒绝；请求目录保持缺失，另一个 checkout 不变 |
| 请求目录缺失，归属目标缺失 | 拒绝；两个位置保持缺失，配置不变 |
| 保留元数据属于请求位置，但请求目录缺失 | 直接 checkout 预检允许继续；配置不被改写 |
| 正常 deinit/reinit | 实际递归同步成功，原有各层 HEAD 与跟踪源码内容保持 |
| 新本地 clone | 实际递归初始化成功，模块 gitdir 与原 checkout 分离，原深层配置不变 |
| 新 linked worktree | 实际递归初始化成功，使用 Git 返回的私有模块目录，原深层配置不变 |

冲突用例同时经过顶层 `checkout_errors` 入口和递归 `sync_sources` 入口。测试在生产 command 边界拦截会修改来源的命令，并比较前后状态；Git 仓库、配置和路径解析本身是真实执行的。[测试代码](../../tests/test_recursive_sources.py)

### 旧实现的反例

仅加入新测试、尚未修改生产实现时，在隔离 checkout 的 `tests/` 下运行：

```sh
python3 -m unittest -v \
  test_recursive_sources.RecursiveSourceCheckoutTests.test_sync_rejects_retained_metadata_for_existing_foreign_checkout \
  test_recursive_sources.RecursiveSourceCheckoutTests.test_sync_rejects_retained_metadata_for_missing_foreign_checkout \
  test_recursive_sources.RecursiveSourceCheckoutTests.test_sync_rejects_foreign_metadata_when_checkout_path_is_missing \
  test_recursive_sources.RecursiveSourceCheckoutTests.test_sync_rejects_missing_foreign_target_when_checkout_path_is_missing
```

实际结果：4 项均在“预检接受了属于另一个 checkout 的元数据”断言处失败；`Ran 4 tests in 1.257s`，退出码 1。测试在该断言处停止，没有执行旧实现后续的来源更新。

### 修复后的相关测试

环境为 Linux x86_64，Python 3.14.10、Git 2.56.1。在隔离 checkout 的 `tests/` 下运行：

```sh
PYTHONDONTWRITEBYTECODE=1 \
GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null \
GIT_ALLOW_PROTOCOL=file GIT_TERMINAL_PROMPT=0 LC_ALL=C \
python3 -m unittest -v \
  test_recursive_sources \
  test_project_z.PathBoundaryTests \
  test_project_z.SourceLinkTests \
  test_maintenance.IsolatedApply
```

实际结果：

```text
Ran 39 tests in 11.241s

OK
```

退出码 0。其中递归来源与归属测试 15 项，路径边界 3 项，来源链接 9 项，隔离快照 12 项。最后还执行了 `git diff --check`，退出码 0。维护测试只选择不运行 Cargo 的 `IsolatedApply` 类，未执行该文件中的 Cargo 解析测试。[既有来源测试](../../tests/test_project_z.py) · [既有隔离测试](../../tests/test_maintenance.py)

### 公共主线上的复验

协调端将原始补丁 `680773d664be3effc6b5d4ba69ea060a371e628e` 应用到公开主线 `5b6ed98b630197fa7ef0f2bf7851d5c31aec9650` 的独立 clone，使用相同的 39 项测试重新验证。环境为 Linux x86_64、Python 3.12.14、Git 2.56.1；结果为 `Ran 39 tests in 21.637s`、`OK`，退出码 0。测试仍只使用临时本地 Git fixture，没有网络请求、Cargo 或远端 CI。

这次集成只包含协调脚本、测试和说明文档。没有接收开发机主 checkout 中未验收的子模块指针或 catalog 变化，也没有把局部测试结果记为全图 `check`、`resolve --all` 通过。

## 范围与局限

本次检查解决的是允许未初始化目录时遗漏的元数据归属判断，已有的 HEAD、脏文件、路径边界和活动分支规则继续生效。例如，手动删除嵌套 gitlink 的整个目录，仍可能被父仓库的“source checkout is not clean”检查拒绝；直接归属检查允许同一目标，并不代表完整同步必定接受父仓库的其他状态。

校验读取当时可见的配置，不提供跨进程事务或锁。其他进程在预检完成后改写元数据，仍需要维护者通过 checkout 归属与工作协调来避免。这个补丁不修复已经损坏的共享配置，不删除或重写其他 checkout，也不追溯历史写入原因。

验证范围限于以上临时 Python/Git fixture 与列出的测试环境。没有运行生产仓库的 `sync`、全图 `check`、`resolve --all`、Cargo、其他平台或远端 CI。生产主 checkout 和子模块没有被本任务修改；修复在独立本地 clone 中准备，由协调端审阅整合。
