---
plan_id: PLAN-017
status: executing
feature_name: M3-05 差异侧编辑回路——差异侧直接编辑 v1（diff 视图双侧跳转编辑+保存自动重比+净形即时预览+B 侧跳转补全）
author: [agent]
created_at: 2026-09-28T17:31:25+08:00
updated_at: 2026-09-28T18:05:00+08:00
plan_revision: 1
current_step: 0
total_steps: 7
supersedes_spec_components: []
new_spec_components:
  - docs/specs/modules/diff-view.md（SD-01：差异侧编辑回路节——跳转/保存自动重比/live 预览/一致刷新）
  - docs/specs/00-overview.md（SD-02：M3 第五件注记——M3 本仓面收口）
  - specs/auto-edit/README.md（SD-03：PLAN-017 口径——判绿重定/工具链门）
  - docs/upstream/2026-09-diff-engine-supply.md（SD-04：§6.3 增补——in-place 混源 rows 供料 want 登记）
touched_goals:
  - 战略 §2.3 M3 验收面「文件 diff 完本体：差异侧直接编辑（编辑后即时重比）」——v1 形态（编辑回路闭环；BC 同款 in-place=上游供料后续件）
affects: [specs/auto-edit/src/front/editor_store.at, specs/auto-edit/src/front/app.at, specs/auto-edit/tests/desktop_mcp.py, specs/auto-edit/tests/probe_bufdiff.py]
---

# [PLAN-017] M3-05 差异侧编辑回路（差异侧直接编辑 v1）

## 0. 变更摘要

PLAN-016 交付后的 M3 剩余本仓件（overview M3 第四件注记尾行「M3 剩余
=差异侧直接编辑重比+语法高亮联动」——后者=M4 tree-sitter 门控非本仓
现时可做）。战略 §2.3 原文「差异侧直接编辑（编辑后即时重比）」的
**v1 形态=编辑回路闭环**：diff 视图（并排/内联两态）任一侧**跳转编辑**
（对应文件成 tab+hunk 首行落点）→ 编辑器内修改 → **保存自动重比**
（WriteFidelity 保存完成位挂钩——diff 视图原地刷新零手动）→（保存前）
**净形即时预览**（SrcChanged→防抖→diff_snapshots——016 缓冲区面板
天然净形面 live 更新）。附带清偿 016 尾注后续件：**DiffBufJump B 侧
跳转**（现有 A 侧对称臂）。**边界如实成文**：BC 同款「diff 视图内
直接键入」=上游混源（file↔buffer）rows envelope 缺位——本件登记供料
want（SD-04），in-place 形态属后续件。本件后 **M3 本仓面收口**（剩
语法高亮联动=M4 首批 tree-sitter，供料驱动）。

## 1. 目标

- **G-1 双侧跳转编辑**：diff 视图增编辑入口（hunk 行动作+工具栏
  「编辑 A/B 侧」钮）→ 目标文件以 tab 打开（已开则激活——OpenPath
  既有去重语义）→ **装载等待**（load_key 单槽协议——016 旁路 B→A
  轮转先例的 handler 化复用：pend 旗标+`tabs[].loaded` 双真门）→
  `code_editor_set_cursor(key, line, 0)` 落 hunk 首行（DiffBufJump
  同款 1 基→0 基换算）。A/B 双侧对称；下钻态（dir_from_dirs）同权。
- **G-2 保存自动重比（磁盘态即时重比）**：WriteFidelity 两臂（normal
  write_text/big 直写——013/014 双形态）保存完成位（`dirty=false`
  后）挂 diff 感知钩子：`diff_open && tabs[i].path ∈ {diff_a,
  diff_b}` → 自动 `DiffCompute`（envelope 原地刷新/vmode 保持[015
  生命周期不变式——重算尾段投影重建]/导航位既有复位语义）；**下钻态
  双刷新**（dir_from_dirs 门→DiffCompute+DirDiffRefresh——012 同步
  动作后刷新协议复用，过滤态保持）；**缓冲区面板刷新**（diff_buf_
  open 且键匹配→DiffBufRun）。保存失败/无关文件保存=零动作（console
  零重比记录——矩阵断言面）。
- **G-3 净形即时预览（保存前 live）**：`SrcChanged(i)` → diff_buf
  面板开态且 i 键匹配 → **Tick 防抖**（单拍合并——SrcChanged 置
  pending 旗标，Tick 消费单次 DiffBufRun）→ 面板计数/hunk 列表
  live 更新（diff_snapshots 净形与面板渲染面天然同形——rows 缺位
  零障碍）。文件 diff 视图侧保存前预览（脏计数 badge）=probe 装载
  轨形（016 §10 Q-1 候选 (b) 遗项）——**T-00 勘定**：成立则随件
  落（badge 计数），不成立则降级「未保存」dirty 提示（tab dirty 面
  现役）+want 登记，不硬做。
- **G-4 B 侧跳转补全（016 尾注清偿）**：`DiffBufJump` 增 B 侧对称
  臂（切 kb 对应 tab+`set_cursor(kb, b1, 0)`——A 侧先例同构；净形
  行双臂动作=按侧选定的双钮或行内双击侧判定，T-00 定 UI 形）。
- **G-5 矩阵/探针/口径**：desktop_mcp.py T15 组增 **15.20-15.24
  编辑回路子组**（双侧跳转/保存自动重比[envelope 派生面变化断言]/
  无关保存零扰动/面板 live 预览/B 侧跳转）；probe_bufdiff 扩 live
  预览段（SrcChanged 模拟=code_editor_set_text 驱动→净形计数变化）；
  判绿口径重定（完成态 129→N，承 016 口径 ≥118/0 基线抬升）。

### 非目标

- **diff 视图内直接键入（BC 同款 in-place）**——上游缺混源（file↔
  buffer）rows envelope：diff_snapshots 净形（rows:[]）喂不了 rows
  渲染的并排/内联视图；本件登记供料 want（SD-04：diff_snapshots
  rows 形+混源或等价面），后续供料→消费件另立。
- 语法高亮联动（M4 首批 tree-sitter——供料驱动）；3-way merge/双向
  同步向导（战略 §9-Q5）；十六进制比对。
- diff 视图滚动模型重构（双独立窗格联动——011 已裁撤的 want 不复
  活；编辑回路=tab 编辑器与 diff 视图并存同屏，跳转切换已有先例）。
- A/B 之外的任意文件保存触发重比（钩子域=diff_a/diff_b 精确匹配）；
  会话恢复态的 diff 视图跨会话持久（diff_open 不入会话——010 域，
  维持现状）。
- auto-lang 侧任何改动（发现上游缺陷回 upstream 登记）。

## 2. 架构方案

分层落点（2026-09-28 实勘，auto-edit main@f20882e + auto-lang
master@9b5a10e51）：

| 面 | 现状 | 本期形态 | 依据 |
|---|---|---|---|
| 跳转编辑 | diff 视图纯只读（行=text 节点）；016 DiffBufJump 仅缓冲区面板 A 侧（切 tab+set_cursor 先例在册） | diff 视图编辑入口（hunk 行动作+工具栏双侧钮）→OpenPath/TabActivate+装载等待+set_cursor 落 hunk 首行——DiffBufJump 模式向 diff 视图迁移+双侧化 | 016 DiffBufJump；016 旁路装载轮转（B→A 单槽协议）handler 化 |
| 保存钩子 | WriteFidelity 两臂保存完成位=dirty=false+console（editor_store.at:2604-2641 实勘——big 直写/normal write_text 双臂同点） | 保存尾部增 diff 感知钩子（三域分派：diff 视图 DiffCompute/下钻态+DirDiffRefresh/面板 DiffBufRun）——单一挂钩点三消费域 | 012 DirDiffRefresh 协议；015 vmode 生命周期不变式；016 DiffBufRun |
| live 预览 | SrcChanged(i)=dirty 置位+计数（editor_store.at:613-618 实勘）；diff_buf 面板=净形渲染（rows 缺位零依赖） | SrcChanged→pending 旗标→Tick 消费→diff_snapshots 重比→面板净形刷新（保存前）；文件视图 badge=probe 装载轨形 T-00 勘定 | 9916 净形契约（SD-03 册）；016 面板渲染面 |
| B 侧跳转 | DiffBufJump 单臂（A 侧） | 对称臂（kb 侧 b1 锚点）——净形行双臂动作 UI 形 T-00 定 | 016 尾注「B 侧跳转=后续件」原文 |
| 矩阵 | T15 组 20 检查（016 后 15.16-15.19 在册）；完成态 129/判绿 ≥118/0 | 15.20-15.24 子组（五检查）+probe 扩段；口径重定 | desktop_mcp.py T15 组结构；README 016 口径 |

**关键设计约束（frozen）**：
① **零 back 改动**（本件纯 front 件——消费既有 15 端点与 natives；
api.at/fsys.at 零 diff；015「纯视图件」先例同款）。② 钩子域精确匹配
（path ∈ {diff_a, diff_b}）+零动作可断言（无关保存 console 零重比行）
——防误重比（大目录 dirdiff 不涉）。③ 自动重比**不重置用户态面**：
vmode 保持（015 不变式）、过滤态保持（012 协议）、irows 重建（重算
尾段语义）；导航位=DiffCompute 既有复位语义（不新增 clamp 面）。
④ 装载等待复用 load_key 单槽协议轮转序——不自造并行装载（016 首轮
烟测死锁教训在册）。⑤ live 预览域=净形面板（rows 缺位天然匹配）；
文件视图 badge 仅在 probe 轨形成立时随件落，否则 want 登记不硬做。

## 3. 技术栈

纯 front（.at store/handler/视图）+既有端点（diff_files 9915/
diff_snapshots 9916/diff_dirs 9917+第 15 端点）+python 矩阵/探针。
工具链纪律承 016：判据前核 `auto --version` 含 704 修复 b2f8761e0
（现役 v0.4.2-2183-gc8f86ef92 已含——若期间上游 master 漂移按组依赖
worktree `.wt/edit-017/auto-lang` 钉版惯例）。

## 4. 需求分析与背景调查

**授权记录**：用户 2026-09-28 会话指令「计划 16 已完成；请规划下一个
计划」——授权=**起草本件**（M3 剩余本仓件的下一件——overview M3
第四件注记尾行两候选中，语法高亮联动=M4 tree-sitter 门控，差异侧
直接编辑=本仓现时可做且被 016 基建解锁）。**【执行授权 2026-09-28】
用户指令「计划017: 实施它」=执行/work 授权落地**——status
drafting→executing，自 worktree `.wt/edit-017/auto-edit`（分支
plan-017-dev，base f20882e）执行。范围=auto-edit 单仓（front/tests/
docs）；**back 零改动**；auto-lang 零改动。无预算/自动续跑授权。

**来源与版本**：

- 交接链：PLAN-016 归档件（docs/plans/archived/
  016-m3-diff-engine-consume.md，delivered@f20882e）——缓冲区面板/
  DiffBufJump A 侧/装载轮转协议/净形契约消费实证；overview M3 第四
  件注记（L206「M3 剩余=差异侧直接编辑重比+语法高亮联动」）。
- 现状实勘（auto-edit main@f20882e）：editor_store.at:2604
  WriteFidelity（两臂保存完成位）、:613 SrcChanged/:621 CursorMoved
  （事件面）、:2300+ DiffBufBypassTick（装载轮转门实现——handler
  化蓝本）、016 缓冲区面板状态族（diff-view.md 缓冲区比较节在册）；
  desktop_mcp.py T15 组 20 检查结构；README 016 口径（完成态 129/
  判绿 ≥118/0）。上游：diff-endpoints.md 净形契约（rows:[]）+704
  修复后 rows 面规范锚（diff-view.md 引擎时代节在册）。
- 历史关联：PLAN-011（diff 视图只读形态+双栏同步裁撤注记——本件
  不动滚动模型）、012（DirDiffRefresh/过滤态保持协议）、015（vmode
  生命周期/纯视图件先例）、016（面板/跳转/轮转先例+B 侧后续件尾注）。
- 战略口径：§2.3 完全体清单「差异侧直接编辑（编辑后即时重比）」
  原文——v1 编辑回路形态的边界注记随 SD-02 落 overview（BC in-place
  =供料后续件）；§6 路线图 M4 行（语法高亮首批 tree-sitter——非
  本件面）。

## 5. 详细设计

### T-00 编辑回路勘定决策件（有界调查，决策产物）

1. **probe 装载轨形（016 §10 Q-1(b) 遗项）**：文件 diff 视图保存前
   badge（A 侧磁盘文件→隐藏 probe 编辑器键装载[code_editor_
   load_file 非 UI 键]→diff_snapshots(probeA, tabB) 净形计数）——
   探针定轨形（merged 实例：registry 键生命周期/disposal/事件噪声）；
   成立→随件落 badge；不成立→降级 dirty 提示+want 登记（§10 Q-2）。
2. **编辑入口 UI 形**：候选 (a) 工具栏双侧「编辑 A/B」钮+hunk 位次
   联动（跳当前 hunk 首行）；(b) 行级动作（hunk 行双击/行内钮——
   行归属侧判定）。默认 (a)+(b) 的 hunk 行归属侧双击（矩阵可断言面
   优先）；T-00 探针定夺（快照形态断言约束——for 动态行动作面在
   2044 的既有实证边界）。
3. **B 侧跳转动作形**：净形行双臂（A 钮/B 钮双钮）vs 单臂+侧切换
   ——默认双钮（矩阵 find 唯一性优先）。

### T-01 双侧跳转编辑链（G-1）

handler 族：`DiffEditJump(side)`（工具栏钮：side ∈ {a,b}→目标
=当前 hunk 首行[diff_hunks[hunk_idx] 的 a1/b1]）+`DiffRowEdit(vi,
side)`（行级动作：行归属判定→该行 lo/ro 锚点）——公共核：目标
路径=diff_a/diff_b→tab 集查径（path 匹配→TabActivate；未开→
OpenPath+pend 登记）→装载等待（pend 旗标+tabs[].loaded 双真门，
load_key 单槽轮转序复用）→`code_editor_set_cursor(key, line-1, 0)`
+console 记录。下钻态（dir_from_dirs）同权（diff_a/diff_b 即下钻
对）。

### T-02 保存自动重比钩子（G-2）

WriteFidelity 保存完成位（两臂 dirty=false 后、console 记录前）增
`store.DiffSaveHook(i)`：①diff_open 且 path 精确匹配→DiffCompute
（+console「diff: 已重比（保存触发）」）；②dir_from_dirs 门→
追加 DirDiffRefresh；③diff_buf_open 且 tabs[i].key ∈ {ka,kb}→
DiffBufRun；④无命中→零动作零 console（矩阵断言：无关保存后 console
 无重比行）。保存失败臂零动作（既有错误面不动）。

### T-03 净形 live 预览（G-3）

SrcChanged 增面板感知：diff_buf_open 且键匹配→`diff_buf_live_pend
=true`；Tick 尾消费（pend 且面板开→清 pend+DiffBufRun——单拍合并
防抖）。文件视图 badge 视 T-00①：成立→`diff_dirty_badge`（净形
adds/dels 预览串，diff 视图头显示；probe 键随 diff 视图开/关生命
周期建/弃）；不成立→「未保存」提示位（tab dirty 现役面引用，零新
端点）+want 登记。

### T-04 B 侧跳转补全（G-4）

DiffBufJump 增 side 参数（A 臂现有+a1 锚点；B 臂新增+kb 激活+b1
锚点——0 基换算同款）；净形行双钮（「→A」「→B」）。016 尾注清偿。

### T-05 矩阵/探针/smoke（G-5）

- desktop_mcp.py T15 组 **15.20-15.24**：双侧跳转（tab 激活+
  set_cursor 读回[TabActivate SyncCursor 面，15.18 同款]）/保存
  自动重比（旁路开 diff→编辑 B 侧 tab→保存→envelope 派生面计数
  变化+vmode 保持）/无关保存零扰动（console 增量无重比行）/面板
  live 预览（set_text 驱动 SrcChanged→净形计数变化，保存前）/B
  侧跳转（kb 激活+光标读回）。
- probe_bufdiff.py 扩段：live 预览链（merged 臂：set_text→SrcChanged
  模拟→净形刷新）+probe 装载轨形勘定报告（T-00① 决策证据）。
- smoke_t234 扩 P17 断言族（开发期烟测，不入矩阵计数——015 惯例）。

### T-06 规范增量+账本

diff-view.md 追加「差异侧编辑回路（PLAN-017 SD-01，M3-05）」节
（入口/跳转协议/保存钩子三域/live 预览/B 侧补全/矩阵断言口径）；
00-overview M3 第五件注记（**M3 本仓面收口**——剩余语法高亮联动
=M4）；README PLAN-017 口径（判绿重定数字真值回填）；供料档 §6.3
增补 in-place 混源 rows want（若 T-00① 不成立并附 badge want）。
specs.json reviews 段 P017-1 投影（015/016 外科插入先例）。

### 规范增量

| delta_id | add/modify/retire | docs/specs/... target | before/after rule | rationale | acceptance IDs |
|---|---|---|---|---|---|
| SD-01 | modify | docs/specs/modules/diff-view.md | before：diff 视图只读；缓冲区面板仅 A 侧跳转；保存与 diff 态无联动 / after：新增差异侧编辑回路节（双侧跳转协议[装载轮转复用]/保存钩子三域分派/vmode·过滤态保持/live 预览净形域/B 侧对称臂/矩阵断言口径 15.20-15.24） | M3-05 主册落账 | AC-01..05 |
| SD-02 | modify | docs/specs/00-overview.md | before：M3 第四件注记尾行「M3 剩余=差异侧直接编辑重比+语法高亮联动」 / after：M3 第五件注记（编辑回路 v1 形态+BC in-place=供料后续件边界；**M3 本仓面收口**，剩语法高亮联动=M4） | 面进度与边界总览 | AC-06 |
| SD-03 | modify | specs/auto-edit/README.md | before：PLAN-016 口径（129/≥118/0） / after：PLAN-017 口径（完成态/判绿数字=执行后真值回填；back 零改动注记） | 运行矩阵/判绿单源 | AC-06 |
| SD-04 | modify | docs/upstream/2026-09-diff-engine-supply.md | before：§6.3 残留 want 三件（体量/尾行/bench 已清偿） / after：§6.3 增补 in-place 混源 rows want（diff_snapshots rows 形或混源端点——BC 同款编辑的解锁件；视 T-00① 结果并附 badge want） | 上下游收据链延续；后续供料排队位 | AC-07 |

## 6. 测试设计

- **矩阵（desktop_mcp.py）**：15.20 双侧跳转（A/B 各一：tab 激活+
  装载完成+set_cursor 读回）；15.21 保存自动重比（旁路 AUTO_DIFF_A/B
  开 diff→DiffEditJump(b)→set_text 改一行→保存[WriteFidelity normal
  臂]→diff 视图计数变化[+N/−M 断言]+vmode 保持+console 重比行）；
  15.22 无关保存零扰动（开 diff 态保存第三文件→console 增量无重比
  行+envelope 派生面不变）；15.23 面板 live 预览（AUTO_DIFFBUF 双
  tab→set_text→净形计数变化[保存前]→保存→DiffSaveHook 刷新一致）；
  15.24 B 侧跳转（DiffBufJump B 臂：kb tab 激活+光标 b1 读回）。
- **big 臂钩子**：15.21 加 big 变体（>50MB fixture 保存走直写臂→
  同钩触发）——生成式临时构造（013/016 先例，fixtures pristine）；
  工具链大文件 UI 卡死回归 blocked 集若未清偿则此变体注记 blocked
  承接（不新增硬红）。
- **探针（前置决策门，不入矩阵）**：probe_bufdiff 扩 live 链段+
  T-00① probe 装载轨形报告（成立/不成立证据在档）。
- **golden**：零 golden 面（编辑回路=纯编排，envelope 契约零改动
  ——15.21 计数断言走推导期望，非 golden 重定）。
- **双轨**：merged 直调链主验；split HTTP 复跑 15.20-15.22（端点
  零新增——既有面回归）；vue 臂 build-green 复验（新面=既有
  for/if/button 族已证面）。
- **判绿口径**：完成态 129→134（+5）；判绿下限随升（承 016 blocked
  集口径，执行后真值回填——修复轮若有已知族漂移按 016「已知族全中
  零新失败」对账法）。

## 7. 验收标准

- **AC-01 双侧跳转编辑**：diff 视图任一侧跳转→tab 激活（已开/新开
  两路径）+装载完成+光标落 hunk 首行（读回断言）；下钻态同权。
  验证：矩阵 15.20 绿。
- **AC-02 保存自动重比**：保存 diff_a/diff_b 后视图自动刷新（计数
  变化+vmode 保持）；big 直写臂同钩；下钻态双刷新（视图+目录面板）；
  无关保存零动作（console 断言）。验证：矩阵 15.21/15.22 绿。
- **AC-03 面板 live 预览**：SrcChanged→防抖单拍→净形计数保存前刷新；
  保存后 DiffSaveHook 刷新一致。验证：矩阵 15.23 绿。
- **AC-04 B 侧跳转**：DiffBufJump 双臂（A 既有回归+B 新增）；净形
  行双钮。验证：矩阵 15.24 绿+15.18 回归绿。
- **AC-05 back 零改动**：api.at/fsys.at 零 diff（git diff 路径断言）
  ——纯 front 件承诺。验证：worktree diff --stat 路径面=空。
- **AC-06 规范+口径**：SD-01..04 落档；判绿新口径数字=实测真值回填
  README。验证：文件在档+矩阵全量 ≥新下限/0 failed。
- **AC-07 want 登记+账本**：供料档 §6.3 增补在档（in-place 混源
  rows——附 T-00① 结果）；specs.json P017-1 投影回读 True。验证：
  grep 锚+账本断言。

## 8. 执行步骤

| # | 任务 | 依赖 | 落点（实勘锚） | 产出/意图 | AC | 验证（命令/预期） |
|---|---|---|---|---|---|---|
| 0 | T-00 勘定决策件（probe 轨形/入口 UI 形/B 侧动作形） | — | 本件 §5 T-00 节+probe_bufdiff 扩段 | 三勘定案+报告在档 | AC-03/07 | [ ] 探针 exit 0+决策补记 §5 |
| 1 | T-01 双侧跳转编辑链 | T-00 | editor_store.at（DiffEditJump/DiffRowEdit+装载轮转 handler 化）+app.at（工具栏钮/行动作） | 跳转协议双侧化 | AC-01 | [ ] 矩阵 15.20 绿 |
| 2 | T-02 保存自动重比钩子 | — | editor_store.at:2604 WriteFidelity 尾+DiffSaveHook | 三域分派+零动作可断言 | AC-02 | [ ] 矩阵 15.21/15.22 绿 |
| 3 | T-03 净形 live 预览 | T-00 | editor_store.at（SrcChanged/Tick）+（视勘定）badge | 面板 live+badge/want 二选一 | AC-03 | [ ] 矩阵 15.23 绿 |
| 4 | T-04 B 侧跳转补全 | — | editor_store.at（DiffBufJump）+app.at（双钮） | 016 尾注清偿 | AC-04 | [ ] 矩阵 15.24 绿 |
| 5 | T-05 矩阵/探针/smoke | T-01..04 | desktop_mcp.py+probe_bufdiff.py+smoke_t234 | 15.20-15.24+判绿重定 | AC-06 | [ ] 全量 ≥新下限/0 failed |
| 6 | T-06 规范+账本+want | T-05 | SD-01..04+specs.json | 收口注记+供料 want 排队 | AC-06/07 | [ ] 文件在档+P017-1 回读 True |

## 9. 复审记录

- 2026-09-28 起草 handoff：`stage: new`，PLAN-017，plan_revision 1。
  `outcome: pass`（起草完备：M3 剩余本仓件定位有据[overview 尾行+
  路线图 M4 边界]；编辑回路四件全挂既有先例[DiffBufJump/装载轮转/
  DirDiffRefresh/vmode 不变式]；back 零改动承诺+AC-05 路径断言；
  BC in-place 缺口如实登记供料 want 而非硬做；路径/符号经
  auto-edit@f20882e 实勘锚定[WriteFidelity 两臂/SrcChanged/旁路
  Tick]；授权=起草，执行待用户启动）。`next: work`。

## 10. 待澄清事项

- **Q-1 编辑入口 UI 形预裁定（可选）**：T-00 默认=工具栏双侧钮
  （hunk 位次联动）+hunk 行归属侧动作双形态并行（矩阵可断言优先）；
  若用户预裁定只取其一（极简/极全两极），请在执行前示知——否则按
  T-00 探针证据定案。
- **Q-2 文件视图保存前预览（badge）轨形（无需裁定，确认口径）**：
  默认按 T-00① 探针证据二选一——probe 装载轨形成立→随件落 badge；
  不成立→降级 dirty 提示+badge 随 in-place want 一并登记（SD-04
  附注）。两形均不阻塞主链（G-1/G-2/G-4 与此独立）。
