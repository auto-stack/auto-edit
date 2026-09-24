---
plan_id: PLAN-013
status: archived
completion_kind: delivered
feature_name: m2-largefile-mode-v1（M2-04：大文件模式 v1——50MB 档探测/关折行/平文本/全文本命令护栏）
author: [agent]
created_at: 2026-09-23T23:06:15+08:00
updated_at: 2026-09-24T12:20:00+08:00
plan_revision: 1
current_step: 6
total_steps: 6
supersedes_spec_components: []
new_spec_components:
  - "docs/specs/modules/editor-store.md#SD-01（大文件模式节追加：big 标量/探测协议/命令护栏/显示）"
  - "docs/specs/modules/back-api.md#SD-02（file_size 端点节——T-00② 裁 pre-load 形则启用，条件性）"
  - "docs/specs/00-overview.md#SD-03（M2 注记补第四件行——M2 四件全落叙事）"
touched_goals: []
---

# [PLAN-013] M2-04：大文件模式 v1（50MB 档）

## 0. 变更摘要

M2（Notepad++ 对位，战略 §2.2）第四件=**补注十一压后件的收口**（011/012
已交付 M3 v1 两件，M3 未承接件均被上游引擎门控——大文件模式的"随后
收口"时机已到）。战略 §2.2 原文：「大文件：> 50 MB 进入大文件模式
（关折行/懒语法/分块解码）」。核心实勘（**模式机制的内核面全现成，
零内核改动**）：①关折行=`code_editor` DSL `wrap` prop（view.rs:2379
现役，默认 false——大文件即默认值回归）；②懒语法=`lang:"plain"`
**原生旁路 syntect**（highlight.rs:64 白名单 `"none"|"plain"|
"plaintext"|"" → None`——高亮跳过、零 warm_language）；③探测窗兼容=
ProbeByteMeta 现行 64KB 采样窗本就是">64KB 按窗判定（显示语义）"。
真正的新增面两件：**探测链**（per-tab `big` 标量；pre-load back
`file_size` 新端点 vs post-load `loaded_bytes`——T-00② 裁定，倾向
pre-load 以免首帧 wrap 渲染一拍）与**全文本命令护栏**（ReplaceAll/
EolConvert/WriteFidelity 的 VM 字符串路径在大文件的墙——011 实勘
10M steps VM 墙+工具链漂移在案；big 态拦截+提示+上游件指向：save
直写端点 §10-2、真分块 IO §10-2 观察 B）。分块解码（1GB 线）=
上游阻塞非目标，v1=50MB 档（50MB–超大拒绝位之间）。会话恢复天然
兼容（会话只存 path，重装载即重探）。
前置：PLAN-012 执行中（worktree plan-012-dev T-04 已落，剩 T-05/T-06）
——**本计划执行前置=012 merge 归档**。

## 1. 目标

- **G-1 探测与模式态**：per-tab `big: bool` 标量（阈值 50MB，T-00④
  定参）；探测时点=T-00② 裁（pre-load `file_size` 端点 或 post-load
  `loaded_bytes`）；`SyncByteMeta` 族挂点重算；状态栏「大文件」标注。
- **G-2 模式切换链**：big tab 的编辑器 `wrap: false` + `lang: "plain"`
  （视图 props 按 `t.big` 走——VM view 模板只读惯例）；tab 间切换
  props 联动正确（big↔normal 往返无残留）。
- **G-3 全文本命令护栏**：ReplaceAllRequest / EolConvertRequest /
  WriteFidelity（save）在 big 态**拦截 + 显式提示**（console+状态栏，
  绝不静默）；readonly **不设**（大文件仍可小步精修——战略 §1.2 保留
  清单②）；拦截语义=命令级（编辑/查找/导航不受限）。
- **G-4 超大拒绝位**：>超大阈值（T-00④ 定参，预判 512MB）装载拒绝+
  架构阻塞注记（真分块 IO §10-2 指涉）——1GB 线非目标如实标注。
- **G-5 测量与矩阵**：bench 大文件档（50MB/100MB fixture open 载入
  +模式 on/off 代理指标对照——阶段标记/loaded_bytes/RSS 记账）；矩阵
  扩 T17 检查组（探测/切换/护栏/拒绝/显示/恢复兼容）。
- **G-6 规范与上游**：editor-store.md 大文件模式节 + overview M2 第四
  件行（M2 收口叙事）；upstream §16（save 直写端点消费时点注记[护栏
  解除件]+VM 大字符串墙归档注记）；vue 复验。

### 非目标

- **分块解码/1GB 可打开**（真分块 IO=上游阻塞，§10-2 观察 B 在案——
  预算行 rope 前架构性不可达纪律不变，本件只记账）。
- 大文件 save 的**可用路径**（护栏只是拦截；正解=上游 `code_editor_
  save` 直写端点[§10-2 want 在册]——落地后 big 态 save 解禁，零 front
  改动预期）。
- 大文件下 diff（011 上限门 10k 行/1MB 已拒+注记——本件只对齐消息面）、
  find-in-files（009 10MB 跳过门已有）。
- 大文件折叠/语法高亮任何形态（M4 tree-sitter 时代重评——designs/001
  在档）；懒语法=「跳过」非「延迟」。
- 行内查找（内核 search prop）在大文件的行为变更（内核逐行快照隔离
  现役——非本件面）。
- auto-lang 侧任何改动（上游 want 走 docs/upstream 登记）。

## 2. 架构方案

分层落点（2026-09-23 实勘：auto-edit main@31b3b16 + 012 在途 ee60ce9 /
auto-lang 543eccdc4）：

| 面 | 现状 | 本期形态 | 依据 |
|---|---|---|---|
| 关折行 | `wrap` DSL prop 现役（view.rs:2379；默认 false） | big tab → `wrap: false` 显式绑定（防默认值漂移）；normal tab 维持现状（现视图未绑 wrap=默认 false？——**T-00① 勘**：若现状恒 false 则「关折行」项=零动作，护栏重心移至命令面） | prop 面现成 |
| 懒语法 | `lang_to_extension` 白名单：plain/none/""→None（highlight.rs:64）——高亮跳过 | big tab → `lang: "plain"`（旁路 syntect+warm_language） | 内核原生旁路，零改动 |
| 探测链 | `loaded_bytes`（post-load envelope total）；`file_size` 无独立端点（back fs.size 内用于 diff_dirs/search） | T-00② 裁：**pre-load**（back 新端点 `file_size(path) i64`——OpenPath 时探，big 置位先于装载与首帧渲染）或 **post-load**（loaded_bytes 驱动——零端点，代价=wrap-on 首拍渲染成本，实测定） | 首帧成本 vs 新端点取舍 |
| 命令护栏 | ReplaceAll/EolConvert/WriteFidelity=检测器白名单登记件（显式全文操作） | big 态入口拦截：handler 前置门（`tabs[i].big` → console+状态栏提示+零动作）；编辑/查找/导航/fif 不受限 | 011 实勘 VM 墙（10M steps）+工具链漂移——大字符串过 VM 堆的结构性风险 |
| 超大拒绝 | load_file 无上限（100MB→219MB RSS，687 实测；>1GB 风险未探） | RunPendingLoad 装载前门：>超大阈值 → 错误形 tab（readonly+标题后缀「超大文件-只读」？——**readonly 与 G-3「不设只读」冲突→裁定：拒绝装载**（空 tab+console 注记+架构阻塞指向），不进半装载态） | 1GB 线=上游件，半装载=模糊态不做 |
| 会话恢复 | 会话只存 path/光标位（010）——重装载即重探 | 天然兼容零改动（big 探测随装载链重走）；T17 断言恢复后 big 态正确 | 装载链复用 |
| bench | open 载入档现役（阶段标记+loaded_bytes+RSS 记账）；1/10/100MB fixtures M1 在册 | 大文件档对照：同 fixture mode on/off（plain vs auto 高亮载入计时差+RSS 差）——代理指标记账（L0 无预算效力口径） | §5 阶梯纪律 |
| 检测器 | 白名单五件封闭集 | 零变更（护栏=前置门，不动读出位） | — |
| vue 轨 | 012 build-green（预期） | 新增面=file_size 端点（若裁 pre）+props 绑定+状态栏——基础面 | — |

**与 011/012 边界的对齐**：diff 上限门（10k 行/1MB）与 fif 大小门
（10MB）的消息面统一提及 big 模式注记（可选，不扩门）；核心边界=
**本件管「编辑器内」**，011/012 管各自面。

## 3. 技术栈

.at（editor_store.at 探测链/big 标量/护栏前置门、app.at props 绑定+
状态栏、back/{api,fsys}.at file_size[条件]）、desktop_mcp 矩阵（T17
组+50MB 级生成式 fixture——临时生成不入库）、python 探针
（probe_bigfile.py，T-00 决策件）、tools/bench（大文件档对照）。无新
依赖；内核零改动。

## 4. 需求分析与背景调查

- **授权记录**：用户 2026-09-23 指令——「计划021正在执行中，现在可以
  提前给下一个计划立项了吗？」。**口径勘定**：本仓最高在途=PLAN-012
  （worktree plan-012-dev，T-00..T-04 已落）；仓内无 021（docs/.wt/
  兄弟仓均无痕）——按「在途计划的下一件预立项」处理=本件（013），
  若用户另有所指（他仓 021）请纠正，本件编号不受影响（013 为本仓
  max+1）。授权=预起草；**执行前置=012 merge 归档**。范围=auto-edit
  仓源码与 docs；auto-lang 零改动。
- **战略依据**：§2.2 大文件行原文（>50MB 进入大文件模式——关折行/
  懒语法/分块解码）；补注十一（大文件模式压后，与 M3 并行或随后收口
  ——011/012 已落 M3 v1 未承接件均引擎门控，收口时机到）；§2.1 预算
  表（1GB 行解锁条件=真分块——本件非目标纪律）。
- **上游状态实勘**（2026-09-23）：auto-lang 543eccdc4（最新 PLAN-698
  债册清偿批）——**diff 引擎供料包与 tree-sitter 供料件均未承接**
  （Cargo 无 tree-sitter/similar；698 四轨均非 diff/tree-sitter）。
- **内核面证据**（实勘）：view.rs:2379（CodeEditor 全 prop 面：wrap/
  lang/line_numbers/readonly 等现役）；highlight.rs:44-64
  （lang_to_extension 白名单——plain/none/"" 原生旁路）；ProbeByteMeta
  64KB 采样窗（editor-store.md 字节保真节——显示语义按窗，天然兼容）。
- **代码锚**：`specs/auto-edit/src/front/editor_store.at`（012 终态增
  目录状态族——本件 big 标量/护栏门挂点；OpenPath/RunPendingLoad
  装载链；SyncByteMeta 挂点族；ReplaceAllRequest/EolConvertRequest/
  WriteFidelity 三护栏位）、`src/front/app.at`（code_editor props
  绑定位：lang: "auto" 现值——big 态条件绑定；状态栏 StatusBar）、
  `src/back/api.at`（012 终态 13 端点——file_size 条件第 14 件）、
  `tests/desktop_mcp.py`（T16 在途——T17 追加位）、`tools/bench/`
  （budgets.json+results/ 惯例；diff-20260923 JSONL 先例）。
- **风险登记（011 实勘传承）**：VM 大字符串墙（10M steps 档）+工具链
  漂移（1914→2046 split 49×/dp 2.7×）——护栏与 bench 判读均须钉版
  纪律（README 2046 钉版实证在案）。
- **矩阵口径**：012 终态 N/0（README 口径）；T17 后 → ≥N+M/0（M=
  T-04 实落）。

## 5. 详细设计

### T-00 探针勘定（决策件，先行）

`tests/probe_bigfile.py`（probe 族形态：Phase A back + Phase B merged
UI），五项：

1. **wrap 现状勘**：现视图未绑 wrap（默认 false？）——若恒 false 则
   「关折行」项=零动作（登记注记）；wrap prop 绑定态切换的运行时
   生效性（视图重建后应用）。
2. **探测时点裁定**（核心决策）：pre-load `file_size` 端点（新）vs
   post-load `loaded_bytes`（零端点）——50MB fixture 首帧渲染成本
   实测对照（wrap-on 一拍 vs plain 全程）；**倾向 pre-load**（首帧
   即模式态+超大拒绝可在装载前发生）。
3. **全文本命令大文件风险实测**：50MB/100MB fixture 上 EolConvert/
   ReplaceAll/WriteFidelity 行为（预期墙/超时/RSS 观察——护栏的
   实证依据；100MB 既有锚=219MB RSS[687]）。
4. **阈值与超大拒绝位**：50MB 门（战略原文）；超大拒绝预判 512MB
   （实测 200MB 档 RSS/时长城后定参——1GB 不可达即可证）。
5. **plain 旁路验证**：lang:"plain" 高亮跳过（渲染输出对比）+
   warm_language 不触发；50MB plain vs auto 载入计时差（bench 档
   预演）。

**产出=§10 T-00 决策记录**：探测时点定案+阈值双参+wrap 现状注记+
护栏实证。

- AC 关联：AC-01..AC-04 前置。验证：`python tests/probe_bigfile.py`
  退出码 0 + 报告落档。

### T-01 探测链与 big 标量

（T-00② 裁 pre）back 增 `file_size(path) i64`（GET；fs.size 直通）
——第 14 端点；front `tabs[i].big` 标量（OpenPath 探测置位；阈值
常量）；SyncByteMeta 挂点族+状态栏「大文件」标注位；超大拒绝门
（OpenPath 或 RunPendingLoad 前置：>超大位 → 错误形 tab+console
注记+架构阻塞指向，不装载）。（裁 post 则零端点：loaded_bytes 驱动
置位+超大门在装载 total 回读位——半装载已发生，拒绝语义降级为
「不再渲染」注记，T-00② 权衡明记。）

- AC 关联：AC-01/AC-04。验证：Phase B 烟测（50MB fixture 开→big
  state+状态栏；>超大位→拒绝形）。

### T-02 模式切换链（视图 props）

app.at code_editor props 按 `t.big` 条件：`lang: t.big ? "plain" :
"auto"`、`wrap: false` 显式（T-00① 定形态）；big↔normal tab 切换
联动（props 随激活 tab 重绑——视图重建机制现役）；对折（fold）等
他 prop 不动。

- AC 关联：AC-02。验证：矩阵 T17（切换后高亮旁路断言[快照纯色]/
  props state）。

### T-03 全文本命令护栏

三 handler 前置门：`tabs[i].big` → console+状态栏提示（「大文件：
全文命令已拦截（save 待上游直写端点）」族）+ 零动作；readonly 不设
（小步编辑不受限——SrcChanged/dirty 正常）；提示文案含上游件指向
（§10-2）。

- AC 关联：AC-03。验证：矩阵 T17（big 态三命令拦截断言+normal 态
  不受扰[011/008 既有检查复绿]）。

### T-04 矩阵 T17 + bench 大文件档 + 口径

`tests/desktop_mcp.py` 增 T17 组（预估 8 检查，独立进程+生成式 50MB
fixture[临时构造不入库]）：探测置位/状态栏标注/plain 旁路渲染/切换
联动往返/三命令拦截/超大拒绝/normal 回归/会话恢复重探。bench 增
大文件档（50/100MB mode on/off 对照 JSONL——载入阶段标记+RSS；L0
代理指标口径注记）。README 口径：N/0 → ≥N+M/0。

- AC 关联：AC-05。验证：矩阵完成态 ≥N+M/0 + bench JSONL 在档。

### T-05 规范落账 + upstream §16 + vue 复验

SD-01..03 落 docs/specs（追加节+来源注记——SD-02 按 T-00② 裁定落
或撤）；upstream m1-supply 增 §16（PLAN-013 件：**save 直写端点消费
时点注记**（big 护栏解除件——§10-2 want 在册，落地后解禁零 front
改动预期）；VM 大字符串命令墙归档注记（10M steps 族——大文件命令
护栏的实证归档）；T-00 勘出新件随落）；vue regen --build exit 0。

- AC 关联：AC-06。验证：grep 两/三册 + §16 在档 + 构建退出码。

### 规范增量

| delta_id | add/modify/retire | docs/specs/... target | before/after rule | rationale | acceptance IDs |
|---|---|---|---|---|---|
| SD-01 | add | modules/editor-store.md（追加「大文件模式」节） | before：无模式面契约。after：big 标量语义（阈值/探测时点协议[pre/post 裁定形]）、模式切换链（wrap/lang plain 绑定语义）、**命令护栏清单**（三 handler 前置门+readonly 不设裁定+上游解除件指向）、超大拒绝位（阈值+错误形 tab+架构阻塞指向）、会话恢复兼容性注记（重装载重探） | 模式态+护栏=行为契约，防后续计划误拆 | AC-01..AC-04 |
| SD-02 | add（条件） | modules/back-api.md（file_size 端点节+计数勘正 13→14） | before：13 端点。after：14（file_size GET，i64，fs.size 直通）——**仅 T-00② 裁 pre-load 形则落**；裁 post 则本 SD 撤销并以 editor-store 节内注记替代 | 探测时点两形的规范落点不同 | AC-01 |
| SD-03 | add | 00-overview.md（M2 注记补第四件行） | before：M2 注记三件。after：补第四件（大文件模式 v1）——M2 四件全落叙事（大文件模式=50MB 档；1GB 线上游阻塞注记） | 总览阶段进度面+M2 收口 | AC-06 |

## 6. 测试设计

- **T-00 探针**（probe_bigfile.py）：五项勘定；退出码门。
- **矩阵 T17**（快照+autoui_state 双面）：八件如 §T-04；生成式 fixture
  （50MB 临时构造——纯文本重复模式，划词断言用锚点行注入）。
- **bench**：大文件档 mode on/off 对照 JSONL（载入标记+loaded_bytes+
  RSS；L0 代理口径注记——无预算效力）。
- **回归面**：normal 态三命令（011 T13 ReplaceAll/008 T12 EOL 转换/
  save E2E）复绿——护栏零误伤断言。
- **vue 轨**：regen_vue --build exit 0。

## 7. 验收标准

- **AC-01 探测与显示**：≥50MB 文件打开 → `big=true`（state 断言）+
  状态栏「大文件」标注；<50MB 零扰动；会话恢复后重探正确。验证：
  矩阵 T17。
- **AC-02 模式切换**：big tab `lang:"plain"`（高亮旁路——渲染纯色
  断言）+ `wrap:false`（T-00① 定形态）；big↔normal 切换往返无残留。
  验证：矩阵 T17。
- **AC-03 命令护栏**：big 态 ReplaceAll/EolConvert/save 三命令拦截
  （console+状态栏提示，零动作，文件零变）；小步编辑/查找/导航不受
  限；normal 态三命令复绿（零误伤）。验证：矩阵 T17+回归组。
- **AC-04 超大拒绝**：>超大阈值文件 → 拒绝装载（错误形 tab+console
  注记+架构阻塞指向），不进半装载态；1GB 线=非目标注记在档。验证：
  矩阵 T17（阈值边界 fixture）。
- **AC-05 矩阵与测量**：T17 组入矩阵，完成态 012 终态 N/0 → ≥N+M/0
  判绿（M 实落为准，README 同步）；bench 大文件档 JSONL 在档（mode
  on/off 对照+L0 口径注记）。验证：矩阵退出码+README grep+JSONL。
- **AC-06 规范与上游**：SD-01..03 在册（SD-02 按 T-00② 裁定形）；
  upstream §16 在档；vue regen --build exit 0。验证：grep+构建
  退出码。

## 8. 执行步骤

| 步 | 任务 | 依赖 | 产出/验证 |
|---|---|---|---|
| 1 | T-00 探针勘定（wrap 现状/时点裁定/风险实测/双阈值/plain 验证） | **012 merge** | §10 决策记录；exit 0 |
| 2 | T-01 探测链+big 标量（条件端点） | T-00② | 烟测 big state |
| 3 | T-02 模式切换链（props 绑定） | T-01 | 烟测 plain 旁路 |
| 4 | T-03 命令护栏（三前置门） | T-01 | 烟测拦截+回归 |
| 5 | T-04 矩阵 T17+bench 大文件档+README | T-02/T-03 | ≥N+M/0+JSONL |
| 6 | T-05 规范 SD+upstream §16+vue | T-04 | grep+build exit 0 |

（T-02/T-03 可并行；worktree 纪律照旧——专用组 worktree，主检出零
落盘；**钉版纪律**（011 教训）——bench/判读前核 auto --version。）

## 9. 复审记录

- **2026-09-24 stage: merge | plan_id: PLAN-013 | plan_revision: r1 |
  outcome: pass | 收据键 PLAN-013:r1 五检查点 | prepared：reviewed 基线
  f45da264[pass@r1]+delta 冻结三册+§16（均 docs/ 规范层既证靶，无
  README-as-spec 类未证靶） | landed：rebase main（a7b833c）3/3 重放
  +range-diff 全等 `=`（eb451ca→fc317f4/9741d1e→8007f25/
  **f45da26→027346e=delivery**）+`git merge --ff-only` TIP-MATCH
  027346e 零合并提交+落位烟测 bench check 绿（检测器红证 PASS+构建
  2046） | ledger_refreshed：.autoos/specs.json reviews 段 **P013-1**
  外科插入（13 items；整文件解析+roundtrip 字节等价先证+回读断言前
  12 项零扰动+他五段零扰动；file 指归档路径本件）commit 6678954 |
  archived：git mv docs/plans/archived/013-m2-largefile-mode-v1.md+
  status: archived+completion_kind: delivered | cleaned：随后行
  （wt-guard clean 493 链接级摘除[deps×2+pnpm 晶格 491]目标完好复核
  在案）。

- **2026-09-24 stage: review | plan_id: PLAN-013 | plan_revision: 1 |
  outcome: pass | reviewed_commit: f45da264（worktree plan-013-dev tip，
  树全净） | base_commit: 84c2ef6 | dependency_revisions: auto-lang
  主检出 b41e9aa31（698 报告件[docs-only]， drafting 基线 543eccdc4
  之后前移——零运行面影响）/工具链钉版 p012_pin_auto.exe 2046-dirty
  同版未变 | spec_inputs: editor-store.md 大文件模式节/back-api.md
  file_size 端点节+计数 14/00-overview.md M2 第四件行/upstream §16
  （均 tip f45da264 冻结副本） | acceptance_results: AC-01 pass（
  T17.1 big_active/loaded_bytes=50MB/lang_active=plain+T17.8 恢复重
  探+17.5/17.6 边界双件）/AC-02 pass（T17.1 plain 绑定+T17.4 往返无
  残留+wrap:false 显式绑定[内核 prop 流静态证据 view.rs:1921 builder
  默认+apply_config 逐字段 diff 热应用]）/AC-03 pass（T17.2 ReplaceAll
  拦截+big_hint+T17.3 save 拦截磁盘零变 E2E+T17.7 normal 零误伤写通
  E2E+T12/T13 组复绿[复审轮 T12.6 唯一败=已知缺]；EolConvert 双门源
  检在册[Request+本体]、菜单入口 menubar-sub MCP 失明=T12.6 同源如
  实注记）/AC-04 pass（T17.5 513MB 错误形+readonly_label=只读(超大
  拒绝)+loaded_bytes=0+console load rejected；1GB 非目标注记在档）/
  AC-05 pass（完成态 117 检查，复审轮 **116/1**[唯一败=T12.6 不计]
  ≥判绿线 115/0 达成[与执行期 run4 同谱复现]；README 口径段 grep ✓；
  bench JSONL 在仓 tools/bench/results/bigfile-20260924-120827.jsonl；
  bench check 绿=检测器白名单零变更[源检 code_editor_text 恰三读出
  位=EolConvert/ReplaceAll/WriteFidelity 既有件]）/AC-06 pass-with-
  noted-deviation（SD-01..03 grep 在册+§16 line 440 在册；vue 复审轮
  lenient gen exit 0 [34 组件]+pnpm build 红=12 错全在 src/App.vue
  [§14 helper 预存 TS7006]+strict 红=695 menubar-sub 预存——**本件
  零新增错面双轮复现**[执行期+复审轮]） | findings: **F-1（非阻断，
  blocked-on-upstream）**：AC-06 字面「pnpm build exit 0」不可达——
  阻断面全在上游（menubar-sub 三元素 vue schema 缺登记[695 引入预
  存主干断层]+helper 族 TS7006[§14]），本件可控面（gen 可过+零新增
  错面）达成且 012 同形 delivered 在案；残留已 §16 登记解锁动作三
  项，清偿后无需回改本件 front。**F-2（观察）**：deps auto-lang
  543eccdc4→b41e9aa31 前移（docs-only）不涉运行面。**F-3（观察）**
  ：复审轮矩阵 116/1 与执行期 run4 完全同谱（T17 8/8 两轮稳定） |
  evidence: 复审轮矩阵 RESULT=116 passed/1 failed[唯一 FAIL=T12.6
  mixed→LF=已知上游缺]（session 内复审独立性声明：判定自工件重建
  ——提交内容静态核[code_editor_text 三位/阈值常量 536870912>
  /52428800>=/SD 计数勘正/§16/T17 八检查+失败臂 13 处 result.check
  /探针报告 8/8]+复跑[矩阵复审轮+vue 复审轮]；仓内耐久工件=探针
  报告 probe_bigfile_report.{json,txt} 8/8+bench JSONL+README 口径
  段；复审轮 RESULT 行摘录于本记录——复跑日志在组目录随 merge 清理
  不入仓） | next: merge |

- **2026-09-24 stage: work | plan_id: PLAN-013 | plan_revision: 1 |
  outcome: pass | code_commit: f45da26（plan-013-dev tip；基 84c2ef6，
  三提交 eb451ca[实施]/9741d1e[矩阵+bench]/f45da26[规范]） |
  task_ids: T-00..T-05 全落（current_step 6/6） |
  evidence: ①矩阵完成态 **117 检查**（109+8），run3 114/3→run4
  **116/1**（唯一败=T12.6 menubar-sub 已知上游缺不计）——判绿口径
  ≥115/0 达成，T17 全组 8/8（run3 起 T17 全绿）；②探针
  probe_bigfile **8/8 exit 0**（终修订绑定：fsys 零-try 形+front
  try 门后）——Phase A 端点三形 ✓/B2 ReplaceAll 拦截 0.44s/B3 save
  拦截+磁盘零变/50·100·200MB 装载 loaded_bytes 全对；③bench
  bigfile 档 exit 0（JSONL results/bigfile-20260924-120827.jsonl：
  49MB auto 臂 179ms/579MB·50MB plain 204ms/655MB·100MB 382ms/
  941MB——尺寸杠杆代理对照，L0 无预算效力口径在档）；④bench check
  exit 0（检测器白名单零变更+红证自检 PASS）；⑤vue 臂：strict gen
  红=695 menubar-sub 预存断层 / lenient gen ✓ exit 0（34 组件）/
  pnpm build 红=**12×TS7006 全在 §14 helper 行（012 预存面）**
  +fsys.rs 转译警告=009 期 search_files try 形（预存）——**本件
  零新增错面**；print 遮蔽缓解（globalThis 改写）已清 TS2339×4 |
  blockers: 无（vue AC-06「build exit 0」未达=预存上游断层继承
  ——strict gen 挡在 menubar-sub schema[695]/helper 族 TS7006
  [§14]，012 同款 blocked-on-upstream 定性+零新增错面即本件域绿
  ——复审独立裁定面） | next: review |

  执行要点（对 §10 决策的落地核对）：Q-1 pre-load 形落 RunPendingLoad
  装载前门（file_size envelope→json.to_value 内联+try 门→big 置位
  先于 load_file）；Q-2 wrap 恒 false 勘定+显式绑定防漂移；Q-3 拒绝
  位 512MB（拒绝形 readonly+ro_reason:"big"+标题后缀+loaded=true 终
  结装载链——**拒绝形 readonly 保留=空 rope 无栏清写盘防线**[008
  同根]；readonly_label 派生两形态分立）；Q-4 护栏=结构性/战略线定
  位（50MB 活体可完成[2.5s]+200MB 峰 RSS ~1.55GB+漂移在案）。工程
  实录：①矩阵 run1 与 vue pnpm build 并发致 T15 整组 7 败+T17 驱动
  竞态（负载噪声非代码）——run2 起零并发重跑；②T17.7 初版缺
  AUTO_BENCH=1（ConsumeOpen env 种子仅门控下生效——T13 +按钮同源
  根因）即修；③T17.8 初版误设 tab_count==3——恢复链 `.tabs=[]`
  替换种子形，正确期望 1，即修；④file_size 裸 int 返回过 HTTP=
  serialize null（T-00 Phase A 勘出）→envelope JSON 形仓内既证形
  落地+§16 观察登记；⑤a2r rust 转译器 try 体不支持 Asn/Return（两
  形实测）→fsys 零-try 形+防御上移 front try 门（VM 面任意形可用）
  ——fsys.rs 转译恢复至仅余 009 期预存警告；⑥探针 B2 首拍派发竞态
  （typed/clicked 全空）→开栏 state 校验重试+effective 回读验证
  （T13 卫生同源）即愈。

- **2026-09-24 stage: work（executing 进入，T-00 起）**：用户指令「计划
  013: 实施它」；前置核实=012 merge 归档闭环（84c2ef6 五检查点
  delivered，执行前置解除）。worktree=`D:/autostack/.wt/plan-013/auto-edit`
  （branch `plan-013-dev`，base=main tip **84c2ef6**，零提交起步）；组级
  auto-lang junction（bps 相对路径 ../../../ 三级解析面）+deps junction ×2
  （bps→auto-lang/blueprints、stylekit→**pristine 导出** git archive
  HEAD——主检出 stylekit 两删除 WIP 挂账在案[008 起]，012 同款预防）；
  工具链钉版=`/d/tmp/p012_pin_auto.exe`（**v0.4.2-2046-g02ae0ac1c-dirty**
  实测复核同版——011 Q-7 纪律）。主检出预检：stylekit 两删除=并行会话
  WIP 挂账（不涉本件路径）；本计划文件=主检出未跟踪件（记账单源，随
  本提交入库）。矩阵基线=012 终态 **109 检查**（判绿 ≥107/0，README
  口径）。outcome: pass（进入执行）。next: T-00 探针勘定。

- **2026-09-23 stage: new（r1，drafting → 预备交接）**：用户指令预
  起草在途计划的下一件（口径勘定：仓内在途=012 非 021——按下一件
  =013 处理，编号不受影响）；战略定位=M2-04 大文件模式（补注十一
  压后件收口；M3 v1 未承接件均引擎门控[auto-lang 最新 698 无 diff/
  tree-sitter 承接]）。背景调查实勘：模式机制内核面全现成（wrap
  prop+lang plain 原生旁路——零内核改动）；新增面=探测链（T-00②
  pre/post 裁定）+全文本命令护栏（VM 墙实证传承）；1GB 线上游阻塞
  非目标。六步六 AC 三规范增量（条件 SD-02）+upstream §16+bench 档。
  **执行前置=012 merge 归档**。outcome: pass（授权=预起草；执行待
  012 收口后用户启动 auto-plan-work）。next: work（前置=012 归档）。

## 10. 待澄清事项

（T-00 决策记录落档处——起草时预登记三项）

- **Q-1 探测时点**（T-00②，核心）：**裁定=pre-load 形，落点细化**——
  back 新端点 `file_size(path) int`（fs.metadata 直通=fs.size 映射，T-01
  落），探测位=**RunPendingLoad 装载前门**（非 OpenPath——OpenPath/恢复
  链统一单点：两链的 tab 均为 loaded=false 建 tab→编辑器空实化（零内容
  渲染成本）→Tick 装载；big 置位先于 load_file 完成 → 装载后首帧即模式
  态，同 handler 原子性保证）。首帧正确性另两根静态支柱：apply_config
  逐字段 diff 热应用（mod.rs apply_config_locked：lang_changed=同 buffer
  重建 SyntaxEditor[plain→无语法=旁路]/wrap_changed=set_wrap）+ 渲染侧
  get-or-create 每重建 diffed-in（iced/renderer.rs build_code_editor_
  generic→CodeEditor::new「config is diffed in」）。pre 相对 post 的
  实质优势=**超大拒绝先于 rope 分配**（post 拒绝=装载后「不再渲染」
  降级形——600MB 级 rope RSS 已发生）；SD-02 落档。
- **Q-2 wrap 现状**（T-00①）：**裁定=现状恒 false**——内核 builder
  默认 wrap:false（view.rs:1921）+现视图未绑 wrap（app.at code_editor
  仅 lang/style/search/on* 面）。「关折行」项=**零动作注记**（模式
  语义已是关）；显式绑定 `wrap: false` 仍落（防默认漂移，T-02）。
- **Q-3 超大拒绝位**（T-00④）：**定参=512MB（536870912B）**。依据：
  687 锚 100MB→219MB RSS（≈2.2×）外推 512MB→~1.1GB rope 峰（VM 池
  驻留另计）——装载本身可行但资源峰进入不可控域；1GB 线（战略 §2.1
  预算行）在其上=「拒绝位之内 50MB+ 可开（模式态），之外拒绝（真分块
  IO=上游阻塞）」两段式。探针 b5 活体：200MB 装载 loaded_bytes 全对
  （2046 钉版）——200MB<512MB 拒绝位内，门槛不扰现存域。与 1GB 预算
  行关系注记成文（§16 架构阻塞指向）。
- **Q-4 全文本命令风险实测（T-00③，执行期增记）**：50MB fixture
  （2046 钉版）ReplaceAll 全管线（code_editor_text 读出→back
  regex_replace→edit 全文回写）**2.53s 完成、计数 1691/1691 精确**；
  save（WriteFidelity 读出+包装+write_text）1.26s——50MB 域无硬步墙。
  护栏依据据此**勘定为结构性/战略线**（非紧急墙）：①全文往返把
  50–100MB 字符串两次过 VM 池（687 反例 729–1356MB 池滞留形态；RSS
  峰未测域）；②工具链漂移在案（011 实勘 split 49×/dp 2.7×——同代码
  跨版时间不保）；③save 唯一路径=全文 VM 往返（直写端点 §10-2 want
  清偿前无正解）；④战略 §2.2 大文件模式语义=约束域（50MB+ 不做无界
  全文操作）。护栏维持三件全拦截（G-3 原授权不变）。
