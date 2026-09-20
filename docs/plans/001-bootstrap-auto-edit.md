---
plan_id: "001"
feature_name: bootstrap-auto-edit
status: draft
source_repo: ../auto-lang（只读参照，不修改）
---

# Plan 001 — 起步：拷贝 041-auto-edit 并独立运行

## 背景与目标

本项目（`D:\autostack\auto-edit`）当前只有 `.autoos/` 与 `docs/`，代码为零。起步任务：

1. 把 auto-lang 仓库中的 auto-edit 应用完整拷入本项目；
2. 修正拷贝后必然失效的依赖路径（仅 2 处）；
3. 验证它能独立运行：窗口拉起 + 应用自带的 desktop_mcp 验收矩阵全绿。

**源**（均来自 `D:\autostack\auto-lang`）：

| 源路径 | 内容 |
|---|---|
| `examples/ui/041-auto-edit` | 应用包：`pac.at` + `src/front/**` + `tests/desktop_mcp.py` + `README.md` |
| `examples/ui/stylekit` | 样式库（`pac.at` + `src/front/styles.at`） |
| `blueprints` | `bps` 库整包（示例仅消费 `bps.navigation.filetree.tree_util` 的 `flatten_tree`/`toggle_id`） |

**工具链**：`auto.exe` 已在 PATH（`D:\autostack\auto-lang\target\debug\auto.exe`），**不拷贝**工具链本身。

## 目标布局

```
auto-edit/                          (本项目根)
├── specs/
│   ├── auto-edit/                  ← examples/ui/041-auto-edit（剔除 .git/ .am/ __pycache__/）
│   ├── stylekit/                   ← examples/ui/stylekit
│   └── blueprints/                 ← blueprints 整库（纯文本，量小）
├── tools/
│   └── bootstrap_from_auto_lang.py (拷贝脚本，可重复执行)
├── .gitignore                      (新增)
└── specs/PROVENANCE.md             (拷贝脚本生成：来源 commit 与路径)
```

> 选择 `specs/` 平铺布局的原因：原 `dep stylekit { path: "../stylekit" }` 的相对层级天然吻合，只有 `bps` 一处需要改路径。

## 必改点（拷贝后仅 2 处）

1. `specs/auto-edit/pac.at`：`dep bps { path: "../../../blueprints" }` → `"../blueprints"`（原路径指向 auto-lang 仓库根）。
2. `specs/auto-edit/tests/desktop_mcp.py`：`AUTO_BIN` 默认值 `../../../../target/debug/auto.exe` 在本项目不存在 → 改为「`AUTO_BIN` 环境变量优先，否则 `shutil.which("auto")`」。

---

### Task 1: 拷贝三棵源码树 + 记录出处

Files: `tools/bootstrap_from_auto_lang.py`（新增）、`specs/**`（生成）、`specs/PROVENANCE.md`（生成）

- [ ] 写 `tools/bootstrap_from_auto_lang.py`：
  - 源根取 `<脚本所在>/../auto-lang`；目标取本项目 `specs/`；
  - `shutil.copytree` × 3（`041-auto-edit→specs/auto-edit`、`stylekit→specs/stylekit`、`blueprints→specs/blueprints`），`ignore=ignore_patterns('.git', '.am', '__pycache__')`；
  - 目标目录先删后拷（脚本可重复执行）；
  - 结束时 `git -C <源根> rev-parse HEAD` 取源 commit，写 `specs/PROVENANCE.md`（来源仓库、commit、源路径→目标路径表、拷贝时间）。
- [ ] 运行：`python tools\bootstrap_from_auto_lang.py`
- [ ] 验证：
  - `dir specs` → `auto-edit`、`stylekit`、`blueprints` 三目录齐全；
  - 抽查关键文件存在：`specs/auto-edit/pac.at`、`specs/auto-edit/src/front/main.at`、`specs/auto-edit/tests/desktop_mcp.py`、`specs/blueprints/navigation/filetree/tree_util.at`、`specs/stylekit/src/front/styles.at`；
  - `specs` 下无 `.git`、`.am`、`__pycache__`；`specs/PROVENANCE.md` 已生成且含 commit hash。

### Task 2: 修正 pac.at 的 bps 依赖路径

Files: `specs/auto-edit/pac.at`

- [ ] `dep bps { path: "../../../blueprints" }` → `dep bps { path: "../blueprints" }`（`dep stylekit` 保持 `../stylekit` 不动）。
- [ ] 验证（编译冒烟）：在 `specs\auto-edit` 下 `auto run -r vm`（run_command 设 timeout≈30s）——预期：无编译 ERROR、4041 端口起服/窗口出现；因常驻被超时杀掉属预期结果，判定标准=输出中编译通过且无 ERROR。

### Task 3: 修正 desktop_mcp.py 的 AUTO_BIN 默认值

Files: `specs/auto-edit/tests/desktop_mcp.py`

- [ ] 顶部补 `import shutil`；将
  `_AUTO_BIN = os.path.join(..., "target", "debug", "auto.exe")` / `AUTO_BIN = os.environ.get("AUTO_BIN", _AUTO_BIN)`
  改为 `AUTO_BIN = os.environ.get("AUTO_BIN") or shutil.which("auto") or ""`；
  - 同步 ~797 行 NOT-FOUND 报错文案：提示「将 auto 所在目录加入 PATH，或设 AUTO_BIN 环境变量」。
- [ ] 验证：`python -m py_compile specs\auto-edit\tests\desktop_mcp.py`（零输出=通过）。

### Task 4: 独立运行验证 —— desktop_mcp 验收矩阵

Files: 无代码改动（纯验证）

- [x] 准备依赖：`pip install requests`（若未装）。
- [x] 在 `specs\auto-edit\tests` 下运行 `python desktop_mcp.py`（矩阵会自行拉起 `auto run -r vm` 实例并经 MCP HTTP 驱动；拉起真实窗口属预期）。（输出存档：根目录 `matrix_out.txt` / `matrix_err.txt`）
- [ ] 验证：输出全 PASS / 矩阵汇总全绿，无 `ERROR:` 前缀行。 → **未达成，见下方验证记录**
- [x] 收尾：确认测试拉起的 auto 进程已退出（任务管理器或 `tasklist | findstr auto`）。

#### Task 4 验证记录（2026-09-19）

**结果：39 PASS / 6 FAIL**（`AUTO_BIN` 指向源仓 09.19 15:42 构建的 `auto.exe`；快照拷贝自源仓 HEAD `92c8013a`（见 `specs/PROVENANCE.md`，18:52 拷贝），源码与测试脚本和源仓逐字节一致，已核对）。

6 个失败同属一类：**menubar 下拉展开后的菜单项不在 `autoui_snapshot`**（T2 切换 Console / T3 About / T3b 折叠切换 / T4 新建 / T5 切换 tab / T8 退出）。对照组：T9 脏关闭 alert-dialog 的项**能**在快照找到 → 弹层内容并非整体不可见，是 menubar 注册表（`MENUBAR_OPEN`）驱动的展开内容特定缺失；T1 的「合成 onclick 在快照」两项**通过**。

**基线��照（源仓 docs/plans/archive）**：Plan 626/629/630（09.14）时代矩阵基线 = **48/2**，「仅 2 个存量快照项」，且明示存量 2 项 = 「menubar/toolbar 合成 onclick 快照」。即上游基线从未全绿；而今天 T1 这两项反而通过、开菜单项检查 6 项全红。

**结论**：源仓在 Plan 630（09.14）之后、09.19 15:42 构建之前，渲染器侧出现回归——menubar 展开内容不再进入快照遍历（同一时段源仓合入 PLAN-030 投影 v1.11 / PLAN-656 scroll-pane 等 UI 大改动，HEAD 现为 72ab0894）。此为**上游侧问题**，与本项目的拷贝修正（仅 2 处路径/默认值）无关；快照保真性不受影响。

**处置**：受 Non-goal「不拷贝/不构建工具链」约束，不在本项目修复；已在源仓层面定位（供上游修），本计划以「39/6 + 失败类归因 + 基线对照」作为 Task 4 的如实验收记录。若上游后续二进制修复，重跑 `python desktop_mcp.py` 预期回到 ≈48/2 口径。

#### Task 4 验证记录·复跑（2026-09-19 第二次）

- **复跑结果：39 PASS / 6 FAIL，与上方基线逐项一致**（6 失败均为 menubar 展开项不在快照：T2 切换 Console / T3 About / T3b 折叠切换 / T4 新建 / T5 切换 tab / T8 退出）。T6、T7、T7b、T9、T10、T11 全部通过。
- **机制侧证据**（独立最小复现脚本，临时的，用后未保留在版本控制）：点击菜单触发钮（如 视图）后，host 日志出现 `[TRACE] poll_mcp_actions: event="__menubar_toggle\u{1f}s\u{1f}view"` 与 `[TRACE] menubar intercept: … decoded="__menubar_toggle" args=[Str("view")]` —— 拦截成功；但其后兄弟内容 `col` 占位在点击前后快照中恒为空，展开内容从未进入 VM vtree。与「MENUBAR_OPEN 注册表驱动的展开内容特定缺失」归因一致，进一步坐实上游渲染器问题（DSL 侧 if 条件分支不参与 vm 视图构建的表现形式）。
- **一次未复现异常（留观察）**：某次中间矩阵运行中，应用进程在 T7（Ctrl+J → ActConsole，`VM_HANDLER_OK` 之后）无任何日志地死亡，后续 MCP 请求 connection refused。独立最小复现（干净实例直接 Ctrl+J）与本次完整复跑中 T7/T7b 均正常通过，未能复现。疑似与该次运行中 T6 连续 `SrcChanged` handler 报错（`oninput` 实参错位，`.tabs[i]` 字符串索引错误）积累的 VM 状态有关；建议上游关注「VM handler 报错后继续分发其他 handler」路径的健壮性。

### Task 5: 更新 README 运行说明

Files: `specs/auto-edit/README.md`

- [ ] 「运行」小节改为本项目路径：`cd specs\auto-edit` → `auto run -r vm`；tests 运行方式与 `AUTO_BIN`/PATH 说明同步；
- [ ] 文首加一行出处说明：「拷贝自 auto-lang `examples/ui/041-auto-edit`，commit 见 `../PROVENANCE.md`」，原 Plan 补记保留为历史。
- [ ] 验证：通读小节，命令可直接复制执行（路径与实际布局一致）。

### Task 6: .gitignore

Files: `.gitignore`（新增）

- [ ] 内容：`.am/`、`__pycache__/`、`*.pyc`。
- [ ] 验证：`git status` 中不再出现 `.am`/`__pycache__` 未跟踪项。

## 整体验收

- `specs/auto-edit` 下 `auto run -r vm` 独立拉起 AutoEdit 窗口，不触碰 auto-lang 仓库内任何路径；
- `python desktop_mcp.py` 全绿（**2026-09-19 实况：39/6，见 Task 4 验证记录——6 失败为上游渲染器 menubar 快照回归，非本项目缺陷；按上游修复进度重验**）；
- 项目可提交：`git status` 干净，他机仅需「auto 在 PATH + python + requests」即可复现。

## Non-goals（明确不做）

- 不拷贝/不改 auto 工具链与 Cargo 工程（工具链由 PATH 提供）；
- 不改任何业务代码（treeview / editor_store / mcp 协议逻辑原样保留）；
- 不处理 `AUTO_PROJECT_DIR` 注入与 `%APPDATA%/auto/keymaps` 用户键位层（运行时行为保持原样）。
