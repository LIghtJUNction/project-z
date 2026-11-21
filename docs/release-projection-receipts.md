# 注册表投影的发布回执

Schema 2 回执验证一条具体关系：**固定的源码提交，经固定版本的投影工具转换，并使用固定的注册表锁文件重新打包后，产生与指定 crate 完全相同的字节。** 验证由 [`release_projection_receipts.py`](../scripts/release_projection_receipts.py) 执行，成功状态为 `PROJECTED_RELEASE_REBUILT_AND_VERIFIED`。

这一关系适用于开发源码使用 Project Z Git 依赖、发布包使用注册表精确版本的场景。[投影工具](../scripts/release_projection.py) 从提交中的 `Cargo.lock` 取得内部依赖版本，将允许列表中的 Git 声明转换为对应的 `=VERSION`，并保留可审查的转换记录。

## 受信输入

回执文件顶层仅包含整数 `schema_version: 2` 和 `receipts` 数组。每条记录仅包含下列七个字符串字段；重复 JSON 键、重复的包名与版本组合、额外字段及不合格式的摘要都会被拒绝。

| 字段 | 绑定的内容 |
| --- | --- |
| `package` | Cargo 包名 |
| `version` | 包版本 |
| `github` | 源码的 GitHub 仓库，与源码及归档中的包元数据核对 |
| `source_git_sha` | 完整、固定的源码提交 ID |
| `projection_tool_sha` | 完整、固定的 Project Z 投影工具提交 ID |
| `registry_lock_sha256` | 发布用注册表 `Cargo.lock` 的完整 SHA-256 |
| `archive_sha256` | 待验证 `.crate` 文件的完整 SHA-256 |

**回执文件自身的 SHA-256 必须来自独立的受信来源。** 调用者通过 `--trusted-receipts-sha256` 传入发布流程已经固定并审核的值。直接对任意收到的回执计算摘要，再把该值当作信任依据，会失去这层来源约束。摘要采用 64 位小写十六进制；Git 提交 ID 采用仓库对应的完整 40 或 64 位小写十六进制。

工具检出的 HEAD 必须等于 `projection_tool_sha`。`.gitmodules`、`scripts/release_projection.py` 和 `scripts/cargo_versions.py` 还须逐字节匹配该提交，且不能是符号链接。加载器直接编译已经验证的 Python 源字节，避免执行未跟踪的 `__pycache__` 内容。调用者使用的校验器、Python、Git、Cargo 及其执行环境继续属于信任根。

## 验证步骤

1. 核对独立固定的回执摘要、记录格式、源码提交、工具提交及包的仓库身份。
2. 核对候选 crate 摘要和包元数据，拒绝归档中人为提供的 `.cargo_vcs_info.json`。
3. 核对注册表锁文件摘要。外部来源必须是带校验和的 crates.io 条目；内部 Project Z 包名和版本须与源码 Git 锁文件一致，禁止残留 Git 来源。
4. 通过 Git archive 和固定投影工具建立独立源码目录。源码工作区中的未提交内容不进入该快照；投影后仍含 Git 依赖、含伪造 VCS 元数据或位于另一 Git 工作区内的目录都会被拒绝。
5. 写入已验证的注册表锁文件，运行 `cargo package --locked --registry crates-io`。打包必须保持该锁文件字节不变，重新生成的 crate SHA-256 必须等于候选归档摘要。

成功后，工作目录中的 `verification.json` 记录回执的七个字段、源码锁文件摘要、投影 manifest 摘要和归档字节数。该命令执行本地重建，不上传或发布制品；候选归档的下载地址及注册表返回的摘要由调用它的发布流程记录。

## 执行命令

先准备源码仓库、检出固定提交的 Project Z 工具仓库、受信回执以及两类按包名命名的文件：

- `ARCHIVES_DIR/PACKAGE-VERSION.crate`
- `REGISTRY_LOCKS_DIR/PACKAGE-VERSION.Cargo.lock`

以下变量由调用方的发布环境提供。`SOURCE_COMMIT` 和 `TRUSTED_RECEIPTS_SHA256` 使用审核后固定的值；`VERIFY_DIR` 必须尚不存在，并位于所有 Git 工作区之外。为本次验证分配独立的 `TARGET_DIR`，避免其他 Cargo 作业覆盖同名打包产物。

```sh
python3 scripts/release_projection_receipts.py \
  --repo "$SOURCE_REPO" \
  --commit "$SOURCE_COMMIT" \
  --project-z-tools "$PROJECT_Z_TOOLS" \
  --receipts "$RECEIPTS_FILE" \
  --trusted-receipts-sha256 "$TRUSTED_RECEIPTS_SHA256" \
  --archives "$ARCHIVES_DIR" \
  --registry-locks "$REGISTRY_LOCKS_DIR" \
  --work-dir "$VERIFY_DIR" \
  --manifest Cargo.toml \
  --workspace-manifest Cargo.toml \
  --target-dir "$TARGET_DIR"
```

`--manifest` 和 `--workspace-manifest` 都相对于源码仓库根目录，默认均为 `Cargo.toml`。验证工作区成员时，将前者设为成员 manifest，后者保留工作区根 manifest；注册表锁文件对应整个工作区。省略 `--target-dir` 时，脚本使用 `CARGO_TARGET_DIR`，未设置该变量则使用工作目录下的 `build`。

## 与现有严格验证的关系

原 [`release_receipts.py`](../scripts/release_receipts.py) 的 schema 1 路径保持不变：它要求依赖 crate 的原生 `.cargo_vcs_info.json` 标识源码锁文件中的精确、干净 Git 提交。Schema 2 使用独立命令、独立格式和独立成功状态验证经过 manifest 转换的制品。缺少或不匹配的 schema 1 证据仍按原规则失败；不要补写 VCS 元数据或将两种回执互换。

Schema 2 按包执行验证。单包成功记录不自动覆盖它的依赖集合：需要发布整个依赖快照时，发布流程应逐包收集相应证据，并核对依赖关系。内部包名与版本一致本身只描述依赖选择；各注册表包与其原始 Git 提交的来源关系由对应包的回执承担。

## 证据范围

这个门禁证明声明的转换可以重建出同一份 Cargo 源码归档。原生可执行文件的可复现性、平台运行行为、性能、签名和发布权限仍由各自的验收与发布步骤负责。Cargo 版本、系统构建库或依赖可用性变化可能使重新打包失败；验证按失败处理，发布流程应保留实际使用的工具链和命令记录。

[`test_release_projection_receipts.py`](../scripts/test_release_projection_receipts.py) 覆盖信任摘要、固定提交、工具字节、伪造 Python 缓存、锁文件、VCS 元数据与重建结果的拒绝路径。测试使用真实 Git 仓库和正式投影函数，仅替换 Cargo 重建入口，因此正式发行还需执行上面的真实 Cargo 验证命令。
