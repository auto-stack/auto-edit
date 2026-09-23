---
plan_id: PLAN-011
status: reviewed
feature_name: m3-file-diff-v1（M3-01：文件 diff v1——并排只读视图 + 过渡计算层 + hunk 导航）
author: [agent]
created_at: 2026-09-23T13:39:10+08:00
updated_at: 2026-09-23T18:50:00+08:00
plan_revision: 1
current_step: 7
total_steps: 7
supersedes_spec_components: []
new_spec_components:
  - "docs/specs/modules/diff-view.md#SD-01（新建册：diff 视图状态面与过渡计算层契约）"
  - "docs/specs/modules/back-api.md#SD-02（diff_files 端点节 + #[api] 计数勘正 9→10）"
  - "docs/specs/00-overview.md#SD-03（M3 面开篇注记）"
touched_goals: []
---

# [PLAN-011] M3-01：文件 diff v1（并排只读 + 过渡计算 + hunk 导航）

## 0. 变更摘要

M3（diff 对打 Beyond Compare，战略 §2.3）首件，按补注十一提前开工（010
已 delivered，矩阵 86/0）。核心判断（背景调查实勘）：**diff 引擎供料包
（docs/upstream/2026-09-diff-engine-supply.md，2026-09-23 五件）尚无上游
立项**（auto-lang 最新计划 693/694/696/697/088 均非 diff）——本件=**引擎
无关的编排层先行**：并排视图、hunk 导航、行内三段高亮、矩阵与 bench
计时框架全建；计算层落 **back 新端点 `diff_files` 的过渡形态「朴素分层
diff」**（公共前后缀裁剪 → ≤400 行中间区 DP-LCS → 大中段降级整块
replace hunk → 配对行公共前后缀三段标记），envelope 契约即**替换缝**——
内核引擎（histogram+分块并行）落地后仅换计算层，视图/测试零改动。
约束实勘定形：.at 语言无 sort/index_of/hash 原语（native_catalog 实勘）
→ 算法选型朴素化（真 patience/histogram 属内核件）；AutoVM 解释吞吐
未定标 → T-00 微基准定上限参数。v1 边界如实成文：**双文件磁盘态比较**
（与「编辑中缓冲区」比较需全文读出，撞零全文 tab 铁律——引擎
diff_snapshots 端点[供料 §5]直读 rope 才是正解）；100MB ≤2s 预算=
blocked-on-upstream 记账（bench 框架就位+基线+blocked 标注，perf.py
exit 3 先例）；差异侧直接编辑=完全体件（引擎+增量重比时代）。
前置：PLAN-010 delivered（e780d93），矩阵完成态 86/0（判绿 ≥85）。

## 1. 目标

- **G-1 diff 入口**：「工具→比较文件…」菜单（静态 menubar item——010
  menubar-content 四边界勘定：动态子节点不可用）+ `dialog_open` ×2 选
  双文件（rfd 阻塞式，ActOpen 同款）；矩阵旁路=env `AUTO_DIFF_A`/
  `AUTO_DIFF_B`（AUTO_OPEN_PATH 先例）。
- **G-2 计算服务**：back 端点 `diff_files(path_a, path_b, ctx)` 返回
  envelope（hunks+行对 rows+计数+截断/错误形）；朴素分层算法（T-00
  定参）；上限语义（>10k 行或 >1MB 拒绝并注明架构阻塞——T-00 保守
  定参，见 §10）。
- **G-3 并排视图**：根视图全幅 diff 态（diff_open 条件面，console_open
  同款形态）——左右两栏行渲染：行号×2+行种类着色（增/删/上下文）+
  **行内三段高亮**（配对行公共前后缀裁剪→pre/mid/post 三 text 元素，
  mid 着重色——VM 普通元素达成，无新内核面）；顶部状态栏（±计数、
  hunk 位次 i/N、截断/超限注记）。
- **G-4 hunk 导航**：下一处/上一处（F7/Shift+F7+按钮）——hunk_idx
  推进/回绕 + 当前 hunk 高亮 + scroll controller `scroll_to` 偏移跳转
  （PLAN-656 绑定面在册；行高/偏移定标 T-00）。
- **G-5 矩阵与测量**：矩阵扩 T15 检查组（golden 对照：hunk 结构/行对/
  三段标记/计数/导航回绕/错误形/超限拒绝）；bench 增 diff 计时档
  （1/10/100MB——1MB 档记基线，超限档 blocked-on-upstream）。
- **G-6 规范与上游**：新模块册 diff-view.md（视图状态面+row 契约+过渡
  计算定位+替换缝）+ back-api 计数勘正 + overview M3 开篇注记；upstream
  §14 登记（新 want：双栏同步滚动联动面[若 T-00 证实无事件面] 等）；
  vue 轨 build-green 复验。

### 非目标

- **与「编辑中缓冲区」比较**（active tab vs 工作文本）：需
  `code_editor_text` 全文读出——撞零全文 tab 铁律与检测器白名单封闭集；
  正解=引擎 `diff_snapshots(key_a, key_b)` 端点直读 rope（供料 §5），
  落地后零 front 改动启用。
- 差异侧直接编辑+编辑后即时重比（完全体件——依赖引擎+rope 子树哈希
  增量重比[供料 §2]）。
- 100MB ≤2s 预算达标（引擎前架构性不可达，记账不调优——战略 §2.1
  解锁条件列；bench 只记基线+blocked 标注）。
- 双栏平滑同步滚动（v1=导航跳转；同步联动面=T-00④ 勘定，无事件面则
  登记 upstream want）。
- 目录 diff v1（M3 第二件候选）、3-way merge/双向同步（§9-Q5 开放
  问题）、十六进制比对（非目标）。
- 语法高亮联动（M4 tree-sitter 时代——docs/designs/001 接口在案）。
- auto-lang 侧任何改动（上游 want 走 docs/upstream 登记）。

## 2. 架构方案

分层落点（2026-09-23 实勘，auto-edit main@e780d93 / auto-lang fe785d185）：

| 面 | 现状 | 本期形态 | 依据 |
|---|---|---|---|
| 计算 | 无（auto-lang 零 diff 引擎实勘；供料包五件无上游立项） | **back 新端点 `diff_files`**：朴素分层——①公共前后缀行裁剪 ②中间区 ≤400 行（T-00 定参）DP-LCS（O(N·M) 行级）③大中段降级单 replace hunk（注记降级）④replace 区配对行（索引对齐）公共前后缀裁剪→三段标记 ⑤上下文窗 ctx（默认 3 行）切 hunk。envelope JSON：`{hunks:[{a1,a2,b1,b2}],rows:[{lo,ro,ln,rn,lk,rk,lpre,lmid,lpost,rpre,rmid,rpost}],adds,dels,truncated,err}`（rows=hunk 展开后的渲染就绪行，模板只读惯例） | .at 无 sort/index_of/hash（native_catalog 100-118 实勘：list 原语止于 get/set/insert/remove/drop）→ O(n²) 排序/hash 类算法出局；朴素分层在原语面内自洽 |
| 入口 | 无 | 静态 menubar item（「工具」菜单组——menubar-content 四边界[010 §13]：动态子节点/带参 onclick 实参归零均不可用，静态+无参 handler 安全）+ `dialog_open` ×2（2927 在册；rfd 阻塞式——矩阵不可驱动，旁路=env `AUTO_DIFF_A/B`，AUTO_OPEN_PATH 先例[editor_store.at:1099-1106]） | dialog_open 现役（ActOpen） |
| 视图 | 无 | **根视图全幅 diff 态**（Plan 449：快照定位交互留根）：`if .store.diff_open` 替换编辑区（console_open 条件面同款[app.at:297]）；rows `for` 渲染：每行 row 内左右两 col（lo/ro=行号，lk/rk=种类），三段 text（pre/mid/post，mid=着重色）——**全览渲染 ≤600 行 cap**（超限 truncated 注记+hunk 导航仍全量）；顶部状态条（文件名×2、±计数、hunk i/N） | VM view 不能调函数（Plan 402）→ rows 由 handler 预计算为渲染就绪形 |
| 导航 | scroll controller 绑定面在册（PLAN-656：DSL `scroll_controller()` 句柄 + scroll widget `controller` prop，view.rs:813） | `scroll` 包裹 rows 区 + controller 句柄；F7/Shift+F7+按钮 → hunk_idx 推进/回绕 → scroll_to(handle, hunk_row_index × 行高)（行高定标 T-00③）+ 当前 hunk 行左侧标记 | auto.scroll.to(9904) 偏移语义在册 |
| bench | 无 diff 档 | `tools/bench` 增 diff 计时（1/10/100MB fixture 对）：1MB 档跑通记基线；超 v1 上限档 → blocked-on-upstream 标注（perf.py exit 3 先例，upstream §6） | 战略 §5 diff 计时行；§2.1 预算行记账口径 |
| 检测器 | 白名单五件（bench.py:95） | **零变更**——diff 链零 `code_editor_text`（双文件=纯 back 读盘） | v1 边界（编辑版比较=非目标）正是为此 |
| vue 轨 | 010 build-green | 新增面=back 端点（HTTP 同形）+ 根视图基础 kind（row/col/text/scroll/button）——预期 build-green；`scroll_controller`/`scroll_to` 若 vue 映射缺 → 死分支口径注记（不补件，生成器件登记） | 跨轨禁补件裁定 |
| 替换缝 | — | envelope 契约=计算层与视图层的唯一接口：内核引擎落地后 back 实现体换 Rust 直调（或端点转发内核），envelope/视图/矩阵零改动；T-06 在 diff-view.md 成文 | 669 供料模式 |

**算法边界如实成文**：朴素分层≠histogram/patience——大重排（中段超大）
降级为整块 replace（视觉=一大段红绿，无细粒度）；此为过渡形态已知
局限，内核引擎清偿后消失。中间区上限/文件上限/行高三参数=T-00 定标。

## 3. 技术栈

.at（editor_store.at diff 状态/handler/rows 预计算、app.at 根视图 diff
态+scroll controller、back/{api,fsys}.at diff_files+朴素分层实现）、
actions DSL（工具菜单+F7/Shift+F7）、desktop_mcp 矩阵（T15 组+golden
fixtures）、python 探针（probe_diff.py，T-00 决策件：微基准+原型对拍）、
tools/bench（diff 计时档）。无新依赖；back 净增一端点；内核零改动。

## 4. 需求分析与背景调查

- **授权记录**：用户 2026-09-23 指令——「计划010已经完工；请按战略规划
  下一个计划」。授权=起草（本件）；执行/work 待用户另行启动。范围=
  auto-edit 仓源码与 docs；auto-lang 零改动（上游 want 登记）。无预算/
  自动续跑授权。战略依据：补注十一（M2/M3 交错——010 收口后 diff
  提前开工、大文件模式压后）；§2.3 M3 验收面；§2.1 diff 预算行。
- **上游状态实勘**（2026-09-23）：auto-lang fe785d185——最新计划
  693/694/696/697/088 均非 diff；`similar`/`imara-diff` 不在
  Cargo.toml；diff 引擎供料包（本仓 docs/upstream/2026-09-diff-engine-
  supply.md）尚无承接立项。set-cursor/goto 仍无（§12 want 在案）。
- **语言原语实勘**（native_catalog）：list 原语=new/push/pop/len/
  is_empty/clear/get/set/insert/remove/drop/reserve（100-118）——
  **无 sort/index_of/hash**；str 原语含 split/find/substr/replace（
  009 已证双轨映射集）；`dialog_open`（2927）/`dialog_save`（2928）
  在册（ActOpen 现役 rfd 形态）；scroll 控制器族（9900-9904，
  PLAN-656：DSL `scroll_controller()` 句柄 + scroll widget
  `controller` prop 绑定）。
- **代码锚**（main@e780d93）：`specs/auto-edit/src/front/editor_store.at`
  （1318 行；ActOpen env 旁路先例 :1099-1106；console_log 反馈惯例；
  handler/收口 helper 惯例）、`src/front/app.at`（467 行；actions 块
  :39；编辑区 code_element :278；console_open 条件面 :297——diff 全幅
  态同款插入位；静态 menubar 先例）、`src/back/api.at`（九 #[api]——
  diff_files 为第十件；#[api] 契约+fsys 错名惯例）、
  `src/front/console_panel.at`（scroll 容器先例）、
  `tests/desktop_mcp.py`（T14 组在册，T15 追加位）、
  `tools/bench/bench.py`（ALLOWED_HANDLERS 五件封闭集——本件零涉）。
- **规范基线**：docs/specs/modules/editor-store.md（零全文 tab/save
  白名单/装载协议——diff 链不得破）、back-api.md（九端点+标量返回
  铁律+pac 不写 api:）、00-overview.md（M2 注记三件在案，M3 面无
  开篇——SD-03 补）、010 §13 upstream（menubar 四边界+scroll want——
  本件消费/对照）。
- **矩阵口径**：完成态 86/0（判绿 ≥85）；T15 后 N/0 随 T-05 落定，
  README 单源同步。
- **并行警示**：主检出未提交项=战略补注十一+diff 供料包+designs/001
  （本会话产物，随 M3 首计划 work/merge 周期入库）+ stylekit 两删除
  （并行 WIP，不涉本件路径）。

## 5. 详细设计

### T-00 探针勘定（决策件，先行）

`tests/probe_diff.py`（probe_find/probe_session 形态：Phase A back
HTTP + Phase B merged UI），五项：

1. **AutoVM 算力微基准**：.at 侧 list 读写/str 比较/循环吞吐定标
   （10⁵/10⁶ ops 三档计时）→ DP-LCS 中间区上限（预判 400 行，O(N·M)
   ≈1.6×10⁵ 单元）与全览渲染行数 cap（预判 600）定参。
2. **朴素分层原型对拍**：python 参考实现（同算法）× fixtures 五形态
   （纯增/纯删/改/散点改/大重排降级）golden 对照——hunk 结构+行对+
   三段标记逐字段断言；行号边界（a1/a2/b1/b2 半开区间约定）。
3. **scroll 定标**：scroll widget controller 绑定 + `scroll_to(handle,
   offset)` 语义（像素偏移 vs 行）+ 行高实测（固定行高样式下量取）→
   hunk 跳转偏移公式。
4. **双栏同步可行性**：scroll 位置变化事件面有无（onscroll 类）——
   有则 v1 附带同步；无则登记 upstream want（§14），v1=导航跳转。
5. **入口链预演**：`dialog_open` ×2 顺序流（手动路径）；env 旁路
   `AUTO_DIFF_A/B` 消费形态（merged 实例 E2E）。

**产出=§10 T-00 决策记录**：三参数（中间区/渲染 cap/行高公式）+
④裁定+golden 基准五件入 `tests/fixtures/diff/`。

- AC 关联：AC-01..AC-05 前置。验证：`python tests/probe_diff.py`
  退出码 0 + 报告落档。

### T-01 back diff_files 端点（朴素分层）

`api.at` 增 `diff_files(path_a, path_b, ctx) str`（GET；envelope JSON
直通——标量返回铁律）+ `fsys.at` 实现体 `diff_files_json`：读双文件
（exists 前置；缺失→envelope err 形）→ 行 split → 朴素分层四步（裁剪/
DP-LCS/降级/三段标记）→ 上下文窗切 hunk → rows 预计算（渲染就绪形，
含行号推进）→ 上限门（>10k 行或 >1MB→envelope err「文件超限，等待
内核引擎」+ 架构阻塞注记位——T-00 定参 §10）。json 拼装走
json.from_value（009 search_files_json 同款——record 序列化+转义吸收；
010 Str 链选型不采——009 已证原生面）。

- AC 关联：AC-02。验证：探针 Phase A golden 五形态对照 + 上限门/
  错误形（HTTP 形实测）。

### T-02 front diff 状态与计算接线

`EditorStore` 增：`diff_open/diff_a/diff_b`（路径与开态）、`diff_rows/
diff_hunks/diff_hunk_idx`（渲染就绪行+hunk 表+导航位）、`diff_adds/
diff_dels/diff_truncated/diff_err`（计数与边界态）、`diff_title_a/
diff_title_b`（状态栏派生）。msg 增：DiffOpen, DiffCompute, DiffNext,
DiffPrev, DiffClose。DiffOpen（env 旁路优先→dialog_open×2）→
DiffCompute（back 调用+json.to_value 解包+rows 赋值+hunk_idx 归零）→
错误形分支（err 态+console 记录，不静默）。

- AC 关联：AC-01/AC-02。验证：vm merged 烟测（env 旁路开+counts/
  rows state 断言）。

### T-03 并排视图（根视图全幅态）

app.at：`if .store.diff_open` 替换编辑区块——顶部状态条（文件名×2/
±计数/hunk i/N/截断注记）+ scroll（controller 绑定）内 rows `for`
渲染：row=左右 col（lo/ro 行号+种类底色）×三段 text（pre/mid/post，
mid 着重色；上下文行单段）。关闭按钮/Esc（DiffClose→diff_open=false，
tabs 编辑区复原——tab 集零扰动）。菜单「工具→比较文件…」（静态
menubar-item+无参 handler）+ actions 声明（shortcut 预留 Ctrl+Alt+D）。

- AC 关联：AC-03。验证：矩阵 T15 快照（行文本/行号/计数栏定位）+
  autoui_state。

### T-04 hunk 导航

F7/Shift+F7（actions shortcut）+「下一处/上一处」按钮 → DiffNext/
DiffPrev（hunk_idx 推进/回绕+当前 hunk 行标记位更新+`scroll_to`
偏移跳转[行高公式 T-00③]）；空 hunk（无差异文件）时按钮 disabled
（enabled_if 表达式）。

- AC 关联：AC-04。验证：矩阵 T15（hunk_idx 序列+回绕+scroll 副作用
  state 断言）。

### T-05 矩阵 T15 检查组 + fixtures + bench 档 + 口径

`tests/desktop_mcp.py` 增 T15 组（预估 10 检查，独立进程+env 旁路）：
双开（旁路）/golden 三形态对照（散点改/纯增/大重排降级——rows 与
counts state 断言）/行内三段标记断言/hunk 导航推进+回绕/当前 hunk
标记/错误形（缺文件）/超限拒绝（构造 >上限 fixture）/关闭复原
（tab 集零扰动）/truncated 注记/计数栏快照。`tools/bench` 增 diff
计时档（fixtures 1/10/100MB 对生成脚本+结果 JSONL；超限档
blocked-on-upstream 标注）。README 口径：86/0 → N/0（判绿下限同步）。

- AC 关联：AC-05/AC-06。验证：`python tests/desktop_mcp.py` 完成态
  ≥N/0 + bench diff 档 JSONL 在档。

### T-06 规范落账 + upstream §14 + vue 复验

SD-01..03 落 docs/specs（新册 diff-view.md+追加节）；upstream
m1-supply 增 §14（PLAN-011 件：双栏同步滚动联动面 want[若 T-00④ 证
无事件面]/大 diff 行渲染虚拟化观察件[VM view 全渲染的行数天花板]/
§5 diff_snapshots 消费时点注记[「与编辑版比较」延后理由]；T-00 勘出
新件随落）；vue 轨 `python scripts/regen_vue.py --build` exit 0 复验
（scroll_controller/scroll_to 映射缺→死分支注记，登记生成器件）。

- AC 关联：AC-07。验证：grep 三册 + upstream §14 在档 + regen
  --build exit 0。

### 规范增量

| delta_id | add/modify/retire | docs/specs/... target | before/after rule | rationale | acceptance IDs |
|---|---|---|---|---|---|
| SD-01 | add | modules/diff-view.md（**新建册**） | before：无 diff 面规范。after：diff 状态字段清单（diff_open/rows/hunks/导航位/边界态）、rows 渲染契约（行号/种类/三段标记语义）、envelope 契约（=计算层↔视图层唯一接口、替换缝——内核引擎落地仅换 back 实现体；degraded 降级注记/err="" 无错形）、过渡计算定位（朴素分层四步+三参数 200/600/10k 行·1MB[T-00 定参]+降级语义）、上限门语义（pre-read 尺寸门+post-split 行数门+架构阻塞注记）、入口契约（dialog×2+env 旁路） | M3 首件开新面需成册；替换缝契约化防止引擎落地时视图层返工 | AC-01..AC-05 |
| SD-02 | add+modify | modules/back-api.md（追加 diff_files 端点节 + 计数勘正） | before：九 #[api]。after：十 #[api]（增 diff_files GET）；契约（参数/envelope 形/上限与错误形/rows 预计算归 back 的理由——VM view 不能调函数） | 端点+envelope=跨轨一致性落点 | AC-02 |
| SD-03 | add | 00-overview.md（M3 面开篇注记） | before：M2 注记三件、无 M3 注记。after：M3 开篇行（首件=文件 diff v1，补注十一提前开工口径+供料包指引） | 总览的阶段进度面 | AC-07 |

## 6. 测试设计

- **T-00 探针**（probe_diff.py）：五项勘定+golden 基准；退出码门。
- **golden 对照**（T-01/T-05 共用）：python 参考实现产 golden JSON ×
  fixtures 五形态（纯增/纯删/改/散点改/大重排）；back envelope 逐字段
  对拍（hunk 区间/行对种类/三段标记/计数）。
- **矩阵 T15**（快照+autoui_state 双面）：开栏/渲染/导航/错误/超限/
  复原十件。
- **bench**：diff 计时档（1MB 基线+超限 blocked 标注）JSONL 在档；
  检测器零涉断言（白名单封闭集不变）。
- **vue 轨**：regen_vue --build exit 0。

## 7. 验收标准

- **AC-01 入口与旁路**：「工具→比较文件…」可开（静态菜单项）；env
  `AUTO_DIFF_A/B` 旁路生效（矩阵可驱动）；取消 dialog 零动作。
  验证：矩阵 T15 + 手动 dialog 路径注记。
- **AC-02 计算正确性**：五形态 golden 逐字段对照通过（hunk 半开区间/
  行对种类/配对行三段标记/±计数）；上限门（>10k 行或 >1MB）拒绝+
  架构阻塞注记；缺文件错误形不静默。验证：探针 Phase A + 矩阵 T15。
- **AC-03 并排渲染**：diff 态左右两栏行对齐渲染（行号×2/种类着色/
  行内三段 mid 着重）；顶部状态条（±计数/hunk i/N/截断注记）；
  ≤600 行全览（超限 truncated）；关闭复原 tab 集零扰动。验证：矩阵
  T15 快照+state。
- **AC-04 hunk 导航**：F7/Shift+F7/按钮推进回绕；当前 hunk 标记+
  scroll 跳转到位（行高公式）；无差异时导航 disabled。验证：矩阵 T15
  state 序列断言。
- **AC-05 矩阵基线**：T15 组入矩阵，完成态 86/0 → ≥95/0 判绿（N 以
  T-05 实落为准，README 同步）。验证：矩阵退出码+README grep。
- **AC-06 bench 计时框架**：diff 档在仓（1/10/100MB fixture 对+生成
  脚本）；1MB 档基线数字入 JSONL；超限档 blocked-on-upstream 标注。
  验证：bench 产物在档+口径行。
- **AC-07 规范与上游**：SD-01..03 在册（新册+追加+来源注记）；
  upstream §14 在档；vue regen --build exit 0。验证：grep+构建退出码。

## 8. 执行步骤

| 步 | 任务 | 依赖 | 产出/验证 |
|---|---|---|---|
| 1 | [x] T-00 探针勘定（probe_diff.py 五项+golden 基准） [✅ 已完成 2026-09-23]：五轮探针（r1-r5），末轮 **26/0 绿 exit 0**；§10 决策记录+golden 六形态（degraded 契约件）+五项勘定全落——证据：specs/auto-edit/tests/probe_diff_report.{txt,json}，载具 probe_diff_app/ | — | §10 决策记录；exit 0 |
| 2 | [x] T-01 back diff_files（朴素分层+envelope+上限门） [✅ 已完成 2026-09-23]：fsys.diff_files_json 全内联+api 第十件；探针①′golden×六形态逐字段+错误形×3 全绿 35/0 exit 0（提交 aa3b1ae） | T-00 | Phase A golden 对照绿 |
| 3 | [x] T-02 front 状态+计算接线 [✅ 已完成 2026-09-23]：17 状态字段+五 msg+env 旁路 Tick 自开臂（提交 1b4fc75） | T-01 | merged 烟测 state 断言 |
| 4 | [x] T-03 并排视图（根视图全幅态） [✅ 已完成 2026-09-23]：工具菜单+四 action+全幅视图+scroll controller（同上提交） | T-02 | 烟测+快照 |
| 5 | [x] T-04 hunk 导航 [✅ 已完成 2026-09-23]：推进回绕序列 [1,2,0,1,0]+scroll_to 24px/行+单 hunk 回绕实证（同上提交） | T-03 | 导航烟测 |
| 6 | [x] T-05 矩阵 T15+fixtures+bench 档+README [✅ 已完成 2026-09-23]：T15 组 11 检查全绿；终跑 **97/0 EXIT 0**（86+11，判绿 ≥96 README 落账）；bench `diff` 档基线 543/1184ms+门拒 19/198ms JSONL 在档；钉版纪律实证（提交 0d2d6ac/407b2fc） | T-04 | ≥N/0+JSONL |
| 7 | [x] T-06 规范 SD-01..03+upstream §14+vue [✅ 已完成 2026-09-23，vue 臂 blocked-on-upstream 在案 §10 Q-6]：新册 diff-view.md+back-api 端点节勘正十件+overview M3 开篇+§14 十件；vue gen ✓（33 组件+scroll 映射在档=预设「映射缺」反转）full build blocked（生成器 helper 族 TS 类型 want 登记）；grep 四锚在档（提交 0d2d6ac/407b2fc） | T-05 | grep+build exit 0 |

（worktree 纪律照 008/009/010——专用组 worktree，主检出零落盘。）

## 9. 复审记录

- **2026-09-23 stage: new（r1，drafting → 交接 work）**：用户指令按
  战略起草下一计划；补注十一定位=M3-01（010 已 delivered e780d93/
  矩阵 86/0）。背景调查实勘：上游 diff 引擎零承接（供料包刚发）→
  本件=引擎无关编排层先行（envelope=替换缝）；.at 无 sort/hash 原语
  → 计算层朴素分层（真 histogram 属内核件）；v1 边界如实成文（磁盘
  态双文件/预算 blocked 记账/无差异侧编辑）。七步七 AC 三规范增量
  （新册 diff-view+勘正+开篇注记）+upstream §14+bench 档。outcome:
  pass（授权=起草；执行待用户启动 auto-plan-work）。next: work。

- **2026-09-23 stage: work（executing 进入，续跑对账）**：用户指令
  「继续实施（已实施一部分）」。worktree=plan-011-dev@e780d93（零
  提交；未跟踪=T-00 探针脚本/载具 app/fixtures+golden/报告×2——
  T-00 跑过一轮 13 过 11 败，源码零改动）。四类败因本会话实勘定根：
  ①⑤=探针未按标量返回铁律 JSON 解码（env_str 带引号串——端点本身
  正常，契约确认）；②①1e6 档=VM per-handler 步数预算墙实证
  （auto-lang engine.rs:2145 `budget=10_000_000` steps，WARN[budget]
  四连发、app 存活后续基准正常——T-01 实现硬约束入 §10）；③①
  file_cap=真发现（split 实测 ~0.5ms/行，50k 外推 ~25s——预判不
  成立，Q-1 预授权降参）；④③scroll=探针顺序缺陷（未滚动先读
  viewport_h 未 populated=0；content_h=4800 读回正确=24px×200）。
  探针已修四处+envelope 增 degraded 降级注记字段（SD-01 契约件，
  golden 重生成），重跑中。worktree 的 docs/plans 拷贝=冗余（计划
  记账主检出单源），本会话清除；docs/upstream 供料包双份同文，
  worktree 副本保留为 T-06 §14 追加载体（merge 时吸收主检出未跟踪
  副本）。outcome: **pass——T-00 收口**：探针修四处+双会话隔离+快轮询
  后 r5 26/0 绿 exit 0；三参数保守定值 200/600/10k 行·1MB（§10）+
  Q-2/Q-3/Q-4 全决+Q-5 步数预算新立（10M steps）+upstream 观察件四条
  （2044 返回值丢失疑回归/dp400 挂死崩/onscroll 回声漂移/性能漂移）。
  next: T-01 back diff_files。

- **2026-09-23 stage: work（T-01..T-04 收口，executing 续）**：T-01
  fsys.diff_files_json 全内联单函数（规避 2044 文件局部 fn 返回值丢失
  疑回归）+api 第十件 #[api] GET /api/diff_files——探针①′golden×六
  形态逐字段+错误形×3 全绿 **35/0 exit 0**（提交 aa3b1ae）。工程实录：
  record 字面量/调用实参严格单行（.at 解析器不收跨行——合并脚本事故
  一次，git checkout 恢复重写）；`go` 系保留字（token Go）；流切片
  尾翼 +1 差一修；标量返回 HTTP 双重编码（探针深解码；front merged
  直调单次 to_value 不涉）。T-02..T-04：editor_store 17 字段+五 msg+
  env 旁路 Tick 自开臂（menubar 展开项 2044 不进 vtree 复认+键盘
  AltGr 疑虑→Tick 自开=矩阵确定性驱动面）；app.at 工具菜单+四
  action+全幅视图（四独立 for 单 bool 旗标循环）+DiffScrollToHunk
  （24px/行 float 累加）——烟测 **19/0 ALL PASS**+unbalanced 形态
  （dbg 计数 4ctx/1pair/2del+NEW/L8/L9 节点全渲染+单 hunk 回绕）
  （提交 1b4fc75）。**假阳性教训入档**：视图分支三度重构期间探针串
  两度错位（L5-changed 非本 fixture 串；三段=分离 text 节点非拼接
  串）——pair 行可能从未坏过；最终形（四 for 单旗标+typed 局部归一
  化+分离节点断言）为实证绿面，SD-01 按 final form 成文。deps
  junction ×2 建（010 先例，merge 清理时摘）。outcome: pass。
  next: T-05 矩阵 T15+bench+README。

- **2026-09-23 stage: work（T-05/T-06 收口，execution_done）**：矩阵
  扩 T15 组 11 检查（env 旁路自开/计数 state/形状 dbg/三段分离节点/
  导航序列/位次/关闭复原/unbalanced/错误形/超限/截断）——**终跑
  97/0 EXIT 0**（86+11，判绿 ≥96 README 落账；钉版 2046 实证）。bench
  `diff` 档（AC-06 校准重定形 §10 Q-8）：基线 543/1184ms+门拒 19/
  198ms JSONL 在档。规范三册：SD-01 新册 diff-view.md+SD-02 端点节
  勘正十件+SD-03 M3 开篇；upstream §14 十件（含 vue 生成器 helper 族
  TS 类型 want）。**vue 臂 blocked-on-upstream 在案（§10 Q-6）**：
  gen ✓ 33 组件+scroll 映射在档（预设「映射缺」反转），pnpm build
  红于生成器 helper 族 TS7006（本件首用 controller 族触发；跨轨禁
  补件适用）——精确解锁动作=上游 helper 类型件落地后重跑
  `regen_vue --build` exit 0。工程实录：工具链钉版纪律（并行会话
  换血期判据前必核 --version+AUTO_BIN 钉副本）+矩阵运行期禁全局
  taskkill（run3 误杀实录）+视图分支假阳性教训（探针串错位两度，
  §9 T-02..04 条）。worktree=plan-011-dev@407b2fc（六提交
  a55aa07/aa3b1ae/1b4fc75/0d2d6ac/407b2fc+基线）；组目录 junction
  ×3（deps bps/stylekit+组级 auto-lang——merge 清理摘除）。outcome:
  **pass**（附 vue 臂 blocked-on-upstream——上游件在档，非本仓阻断
  项）。next: review（/auto-plan:review）。

- **2026-09-23 stage: review | PLAN-011 | r1 | outcome: pass（附
  finding R-2）| reviewed_commit: f19fa47（worktree plan-011-dev；
  实施基线 407b2fc+复审证据两提交 a731ddd/1f577e2/f19fa47）|
  base_commit: e780d93 | dependency_revisions: auto
  v0.4.2-2046-g02ae0ac1c-dirty（钉版副本
  /d/tmp/p011_pin_auto.exe，并行会话换血期防换杀）| spec_inputs:
  docs/specs/modules/diff-view.md（新册）+back-api.md（端点节+勘正
  十件）+00-overview.md（M3 开篇）——三册锚点 grep 4/4 在档，内容与
  实现核对一致（四 for 单旗标/1MB+10k 门/替换缝/degraded/分离节点
  口径）| acceptance_results: **AC-01..AC-06 全 PASS**（AC-01 矩阵
  T15.1+烟测自开+人工 dialog 步骤成文[probe ⑤ 注记=计划验收口径]；
  AC-02 探针 ①′golden×六形态逐字段+错误形×3 35/0；AC-03 T15.3/3b/
  15.10/15.6——着色归人工视觉门[快照不带动态行 style，SD-01 口径]；
  AC-04 T15.4/15.5+烟测序列+单 hunk 回绕；AC-05 **矩阵 97/0 EXIT 0**
  ≥96+README；AC-06 bench diff 档两轮 JSONL 在仓+blocked 注记——
  档位校准重定形=§10 Q-8 计划内定参路径非未授权缩水）；**AC-07
  PARTIAL**（前两子句绿：三册在档+§14 十件；第三子句 vue
  regen --build exit 0 未达成——blocked-on-upstream）| findings:
  **R-1（已解）**bench diff JSONL 实施期未入库——复审补记 a731ddd；
  **R-2（开放，非阻断，上游件）**AC-07 第三子句：TS7006 全部位于
  生成器自发射 scroll_* helper（App.vue 23-28 归因 grep——本件转译
  产物零错，gen 33 组件 ✓），gen tsconfig strict 所致，跨轨禁补件
  适用的本仓无修面——**按任务行内预写分支路径处置**（T-06 原文
  「映射缺→死分支口径注记，登记生成器件」：§14 want 已登记+SD-01/
  §14 注记已成文），精确解锁=上游 helper 类型件落地后重跑
  `regen_vue --build`；**R-3（观察，非阻断）**DiffBypassTick 在
  env 未设时每 tick 重读 env（bypass_done 不置位）——卫生改进候
  选件，97/0 三轮含此路径无功能影响实证，留后续件顺手清偿 |
  evidence: 复审独立重跑全部门禁@钉版 2046（probe **35/0** exit 0
  [报告刷新在仓 f19fa47]；smoke **19/0** ALL PASS；矩阵三轮
  96/1→96/1→**97/0 EXIT 0**——前两轮唯一败点=ActAbout console 行
  [86 基线既有件，非 diff 检查]，第三跑同码同二进制通过=随机 flake
  定性非回归；bench diff exit 0 两轮[基线 543/131ms·358ms 负载漂移
  口径注记+门拒 19-21/42ms]；vue 归因 grep=TS 错误 12/12 在生成器
  helper 行）| limitations: 复审与实施同会话——按规程以工件重建
  裁决（全部门禁在受审树重跑取新证据，未采信执行期摘要）；AC-07
  处置（任务行预写分支路径）曾提请用户裁定未获应答，自主判断记
  录在案且可逆（上游清偿后 re-review 即闭合）| next: **merge**
  （/auto-plan:merge）。

## 10. 待澄清事项

（T-00 决策记录——2026-09-23 五轮探针收口，probe_diff_report.json/.txt 在档，
载具 probe_diff_app/）

**Q-1 三参数定值（保守跨工具链）**：

| 参数 | 定值 | 依据 |
|---|---|---|
| DP 中间区上限 | **200** | dp200 档双工具链存活（1914 ≤0.5s / 2044 248ms）；2044 规则输出 216-258（dp300=1.075-1.537s 随负载波动），200 留余量；dp400 在 2044 挂死/硬崩双态（upstream 观察件②） |
| 全览渲染 cap | **600** | 2044 rows600 构建 53ms ≪ 0.2s 预算（快轮询实值）；600 行≈fif 面板 500 按钮先例量级；超限 front 截断+truncated 注记（T-02 store 侧 cap） |
| 文件上限 | **10k 行 / 1MB** | 2044 split5k=53ms（0.01ms/行）→ 50k/2MB 预判在该工具链成立；但 1914 实测 0.52ms/行（50k=26s UI 冻结）——漂移取保守，最坏档 10k 行 ≤5s；尺寸门 pre-read（fs.metadata）即时拒；引擎时代作废 |

- **Q-2 scroll_to 语义（已决）**：绝对像素 `scroll_to(handle,"y",px)`；
  行高=content_h÷行数=24.0px（h-6 整）；跳转公式 offset=行号(0基)×24；
  viewport_h 滚动后 populated（256px 实测），行高公式不依赖 vh；控制器
  绑定+读回 B2 会话四检查全绿。
- **Q-3 双栏同步（已决）**：onscroll 事件面在册且程序化滚动**会**回声
  （2044 obs_n=1/oy=48 实测；1914 曾 obs_n=0——回声行为随工具链漂移）
  → v1 附带双栏同步（左 onscroll→右 scroll_to），矩阵仅状态断言+
  人工视觉复验。
- **Q-4 配对策略（已决）**：索引对齐配对+不成对行整行 mid 染色——
  可接受（ASCII 判据面在档），三段数据保留 envelope 供引擎时代 refine。
- **Q-5 步数预算（新立，T-01 硬约束）**：VM per-handler **10M steps**
  （engine.rs:2145 源码读+首轮 WARN[budget]×4 实证双锚）；diff_files
  全链估算 ~2.2M steps ✓（split 1 调+trim 2.8k 迭代+DP 40k 单元+
  rows/stream 构建+逐 hunk 扫描）。
- **envelope 契约补件**：`degraded` 降级注记 bool（大中段降级语义入
  契约，SD-01）；`err` 无错时=""（.at 侧 nil 语义绕行）。
- **upstream 观察件（T-06 §14 登记）**：①2044 疑似函数返回值丢失
  回归（dp_sim return acc+sc→0，1914 同码=32160200——T-01 缓解：
  逻辑收口模块级 fn+端点链烟测）；②dp400 嵌套大表（401²）挂死/
  硬崩双态（无 panic 无 budget 告警=原生层静默死）；③程序化 scroll
  onscroll 回声行为漂移（1914 无/2044 有）；④1914→2044 性能漂移
  （str.split 49×/dp ~2.7×）。

**探针五轮实录**：r1(1914) 13/11 败因四类定根（⑤未解码标量 JSON/①1e6
预算墙/①file_cap 真发现/③未滚动先读）；r2(1914) push1e6 崩；r3(2044)
dp400 崩；r4(2044) 25/1（轮询地板发现——0.5s 量子掩盖亚 0.5s 真值）；
r5(2044, 0.05s 轮询) **26/0 绿（exit 0）**。工具链漂移实录：1914→2044
（auto-lang 主检出并行会话施工中，二进制 mtime 15:36——跨会话共享
target/debug 是测量噪声源，判据前必核 --version）。

- **Q-6 vue 臂 blocked-on-upstream（T-06 实勘定性，2026-09-23）**：
  `regen_vue --build` 的 gen 阶段 ✓（33 组件；**scroll controller 族
  映射在档**——计划预设「映射缺→死分支注记」反转为正案：
  scroll_to(k,"y",px) 轴语义直映 scrollTop），但生成的 scroll_* helper
  族无 TS 类型注解，gen tsconfig `"strict": true` 下 vue-tsc TS7006
  build 红——本件 diff 导航**首次使用** controller 族触发（主检出
  010 旧生成物零 helper 实证）。跨轨禁补件裁定适用（禁改生成物）→
  upstream §14 登记生成器件 want（helper 族补类型/strict 豁免位），
  vue 臂 full build blocked-on-upstream，清偿后复验 exit 0。
  另：S001 schema 漂移 INFO×N 全部来自 bps 蓝图组件（MasterDetail/
  NoteList 等 label/skeleton prop——pac --lenient 豁免面旧账，非本件）。
- **Q-7 工具链钉版作业纪律（矩阵四轮实录新立）**：并行会话施工中
  target/debug 换血（2044→2046）致矩阵死亡点逐跑漂移假象+二进制中途
  127 消失——**矩阵/bench/构建一律 AUTO_BIN 钉版副本执行**（2046 钉
  版 /d/tmp/p011_pin_auto.exe 实证：钉后首轮即出 RESULT 96/1——败因
  为本矩阵 T15.5 断言算错[序列终态位次]，非产品）；矩阵运行期禁全局
  taskkill（run3 被本会话 bench 前置 kill 误杀实录）。
- **Q-8 bench diff 档位校准重定形（AC-06 修订）**：file_cap 10k 行/
  1MB 下原计划 1/10/100MB 档全落上限外——重铸为档内基线两档
  （small 1000 行 543ms/mid 2500 行 1184ms）+门拒两档（尺寸 19ms/
  行数 198ms，即时性实证）+blocked-on-upstream 注记（全文大文件 diff
  待引擎 diff_snapshots）。AC-06 本质（框架+基线 JSONL+blocked 标注）
  保持达成。
