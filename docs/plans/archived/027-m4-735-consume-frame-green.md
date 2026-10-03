---
plan_id: PLAN-027
status: archived
completion_kind: delivered
feature_name: M4 验收全绿件（PLAN-735 消费——帧两行终裁重判：呈现面通道重读+驱动节拍适配裁定+十行全绿快照+发布门解锁注记+v0.1-M4.3 tag 打点）
author: [agent]
created_at: 2026-10-03T00:00:00+08:00
updated_at: 2026-10-03T12:40:00+08:00
plan_revision: 1
current_step: 6
total_steps: 6
supersedes_spec_components: []
new_spec_components:
  - docs/specs/modules/perf-measurement.md（SD-01：帧两行终裁节——呈现面判定谱+测量实施修订记录+十行全绿快照+发布门解锁注记）
  - docs/specs/00-overview.md（SD-02：M4 验收全绿注记——四代谱系终态+tag 记录位+余题清单终态）
  - specs/auto-edit/README.md（SD-03：PLAN-027 口径+终态表）
touched_goals:
  - 战略 §2.1 预算表 type_latency/scroll_fps 两行——735 消费终裁（发布门解锁位）
  - 「预算未达标的功能不发布——性能是发布门槛（M4 生效）」——发布门解锁兑现时点成文
affects: [tools/bench/bench.py, tools/bench/budgets.json, tools/compare/anchors.py, tools/compare/render_table.py, specs/auto-edit/README.md]
---

# [PLAN-027] M4 验收全绿件（PLAN-735 消费——帧两行终裁重判）

## 0. 变更摘要

auto-lang **PLAN-735**（帧泵呈现交付节奏清偿件，2026-10-03
delivered@4195f7af9——呈现事实定责+发布点错位配对修复+draw_end
真相通道；R1 复审含分离谱/双谱 100% 配对/R-1 零违例在案）的**下游
消费终裁件**——M4 预算面最后一环：**①帧两行终裁重判**（735 定责
颠覆性事实：026 的 FAIL 读数=**驱动节奏传递+通道伪影**，非呈现能
力上限——呈现随输入更新 +6-10ms、滚动突发送达 2-3ms、事件循环能
力数百 fps；`present` 列已对齐真实呈现时刻〔draw_end 优先，配对
100%/184〕。重判=**测量实施修订裁定后的终裁**——读回通道切呈现面
+驱动节拍适配〔Q-1 用户件，735 回执 §3/§4 建议 16ms 节拍：frozen
判据在 60ms 驱动下物理不可达——驱动器本身是帧率上限〕；判定阈值
与语义零变更=非口径作弊）→ **②十行全绿快照+发布门解锁**（上游
谱 1mb type total P50 ~0.01-0.11ms 余量 ~8×——转绿预期；解锁注记
=战略 §2.1 兑现时点成文）→ **③对比表滚动行终态**（四代并陈或
027 代定责注记）→ **④v0.1-M4.3 tag 素材**（验收全绿层——Q-2
默认命名）。**本件 delivered=发布门解锁的预算面条件达成**（发布
动作仍另行——Q-3 口径）。

## 1. 目标

- **G-1 工具链门+735 回执谱复验**：master 重建（含 735@4195f7af9
  ——`auto --version` 核哈希，021-026 六连纪律）；**735 回执谱同
  机复验**（ladder735.py 复跑——配对率 100% 带+draw_end 通道在
  位+S5/segsum 零回退带；超带=环境疑点登记 upstream）。
- **G-2 帧两行终裁重判（G-2 主面）**：Q-1 裁定后 bench frame 档
  N≥4 复跑——**测量实施修订**（读回通道=呈现面〔探针行 total_ms
  =draw_end-begin 真实帧时——735 回执 §4.2 建议；MCP 快照差分
  退役为对照列〕+滚动驱动节拍适配〔60ms→16ms——§3.3 建议〕）；
  **判定阈值/语义 frozen 原样**（P95 ≤1 帧/distinct ≥面板×0.9
  ——修订=测量实施非口径变更，Q-1 裁定回执落档）；转绿=budgets
  两行 armed PASS+四代谱系注记（022→024→026→027）；仍红=双态
  如实归因回执。
- **G-3 十行全绿快照+发布门解锁**：budgets 十行终态表（10 行全
  PASS+renderer n/a 唯一例外）——SD-01 收口节；**发布门解锁注
  记**成文（战略 §2.1 条款兑现时点；发布动作另行——Q-3）。
- **G-4 对比表滚动行终态**：027 代行落位（022/024/026 谱历史不
  删——三代先例延续）；--verify/--check 双绿。
- **G-5 v0.1-M4.3 tag 素材**：素材备档（十行终态+M4 三层收口径
  +验收全绿层+余题清单终态〔供⑭/RQHost 门/NP++ 条件件〕）；
  打点=本件 merge 收据（惯例）；命名 Q-2。
- **G-6 规范+账本**：SD-01..03+P027-1。

### 非目标

- 对外发布/宣传动作（解锁=预算面技术条件注记；发布决策另行）。
- 上游 9920 接线（auto.frame.draw_end_ms VM 内建——735 回执 §3.2
  建议项：若 T-00 勘定 present_ms 新鲜度带内〔配对修复后消费时刻
  ≈draw_end〕则本件零上游依赖；带外才路由上游微件——条件路由位）。
- a2r/L2 形态帧档通道（735 回执 §4.3 建议——另件域）；S5 续作
  （731 已清偿）；供⑭/RQHost 门/NP++ 列（条件件/用户面）。
- 判定**阈值/语义**任何变更（frozen——修订仅限测量实施面：读回
  机制+驱动节拍，Q-1 裁定背书；阈值变更=作弊纪律原样）。

## 2. 架构方案

分层落点（2026-10-03 实勘，auto-edit main@252028a + auto-lang
master@fecf9a590 含 735@4195f7af9）：

| 面 | 现状 | 本期形态 | 依据 |
|---|---|---|---|
| 帧两行 | armed FAIL 维持（026 代：P95 156-160ms/8.1-9.5fps——驱动节奏传递+通道伪影定责在案） | **呈现面终裁**——读回通道+驱动节拍修订后 N≥4 重判；转绿预期 | 735 回执 v2 §1/§2 |
| present 读回 | fprobe=frame.present_ms（泵消费时刻——配对修复后逐帧新鲜） | 主读=探针行 total_ms（draw_end-begin 真实帧时）；fprobe 快照差分退役为对照列 | 735 §4.2/§3.1 |
| 滚动驱动 | 换行连发 60ms 节拍（022 协议——有效驱动率 ~9-16Hz） | 节拍适配 16ms（Q-1——判据物理可达前提） | 735 §3.3 |
| budgets | 8 PASS+2 FAIL+renderer n/a（026 态） | **十行全绿**（转绿预期）+发布门解锁注记 | 026 SD-01 表延续 |
| 对比表 | 滚动行三代并陈（022/024/026） | 027 代行落位（历史不删） | 024/026 先例 |
| tag | v0.1-M4.2=重判收口 | **v0.1-M4.3=验收全绿层**（Q-2） | 收口件惯例 |

**关键设计约束（frozen）**：
① **阈值/语义零变更**（P95 ≤1 帧+面板×0.9 原样——修订仅测量实
施面：读回机制+驱动节拍；Q-1 裁定回执=修订合法性来源）。② **双
态如实**（转绿=armed PASS；仍红=归因回执——不以放宽换绿）。③
**谱系历史不删**（022 首判/024/026/027 四代并陈——清偿证据链）。
④ **工具链门纪律**（重建核哈希+组依赖钉版+PATH 坑——六连先例）。
⑤ **上游谱带内复验前置**（735 ladder 配对率/draw_end 通道复验
——超带先登记后判定）。

## 3. 技术栈

bench frame 档测量实施修订（读回解析+驱动节拍——Python 工具面）
+bench/compare 工具族复跑+工具链重建纪律（master 含 735）+tag 素
材备档。零 .at 源改动（纯判定/工具/文档/tag 面——AC-05 路径断言
延续 026）。

## 4. 需求分析与背景调查

**授权记录**：用户 2026-10-03 会话指令「计划735已经交付，请继续
本会话的任务」——授权=**起草本件**（会话既定路线：026 归档预告
的第三轮重判位点——735 交付后消费；前议在录）。执行/work 待用户
另行启动。范围=auto-edit 单仓（tools/docs/budgets/tag）；
auto-lang 零改动（9920 接线=条件路由位，默认不触发）。**Q-1 测量
实施修订=用户件**（默认倾向采纳 735 回执建议——材料备齐后请示）。
无预算/自动续跑授权。

**来源与版本**：

- 交接链：PLAN-735 归档件（auto-lang delivered@4195f7af9+cleaned
  @68a6ce919——呈现事实定责+发布点错位配对修复 7b9b2f8f5+插桩
  5da3b4727；R-1 零违例 404 行；iced_winit 0.14.1 钉版注记）+
  downstream-handoff-v2（§1 定责/§2 改后终态/§3 通道语义建议/
  §4 重判件预告四条）。
- 定责核心（735 §1）：026 的 8.1-9.5fps=**驱动节奏读数+通道伪影
  **——呈现随输入 +6-10ms〔unconditional request_redraw 钉版语
  义〕；~105-120ms 恒定节拍=MCP 驱动调用周期传递读数（60ms sleep
  +调用时延 p50 62.5ms）；配对损耗根因=发布点错位（bounds 帧窃
  得配对）——非通知丢失非呈现丢失，无需 fork iced_winit。
- 改后终态（735 §2）：行配对率 100%（184/184）；present 列=
  draw_end 优先真值；draw_end_ms 行通道+frame_draw_end_ms() Rust
  读侧在位（9920 VM 内建未接线=建议项）；上游 1mb type total P50
  ~0.01-0.11ms；S5/segsum 同带+golden 0.00%。
- 下游现状实勘（main@252028a=v0.1-M4.2 tag 位）：budgets 026 态
  （8 PASS+2 FAIL）；compare 三代并陈；bench frame 档 022 协议
  （f183f53→08685d6 零 diff 纪律——本件修订面需显式裁定）；
  editor_store.at fprobe 双门采样臂（frame.begin_ms/present_ms
  ——9918/9919）。
- 战略口径：§2.1「预算未达标的功能不发布——性能是发布门槛（M4
  生效）」——发布门解锁注记的原文依据。

## 5. 详细设计

### T-00 终裁勘定（决策件）

工具链门（master 重建含 735——核哈希）；**735 回执谱同机复验**
（ladder735.py 复跑：配对率 100% 带+draw_end 通道+S5/segsum 零
回退带）；**通道新鲜度勘定**（下游 fprobe present_ms〔9919〕
vs 探针行 draw_end 对照——配对修复后消费时刻≈呈现时刻则零上游
依赖；带外=9920 接线微件路由 upstream）；**Q-1 材料定稿**（测量
实施修订案：读回通道切换+驱动节拍 16ms——含 frozen 断言重锚说
明〔bench.py 帧区域将按裁定修改一次并在新协议位重锚〕）。

### T-01 帧两行终裁重判（G-2）

Q-1 裁定后 bench frame 档 N≥4 复跑（修订协议：读回=呈现面
total_ms 主读+fprobe 对照列；驱动=16ms 节拍裁定案）→判定（阈值
frozen：P95 ≤16.7ms@60Hz 面板读回/distinct ≥54）→转绿=budgets
两行 armed PASS+四代谱系注记；仍红=归因回执（双态如实——Q 路由
位）。谱 JSONL 入仓。

### T-02 十行快照+发布门解锁（G-3）

budgets 十行终态表更新（全绿预期——renderer n/a 唯一例外）+
SD-01 收口节 v2（**发布门解锁注记**——战略 §2.1 兑现时点成文；
发布动作另行 Q-3；RQHost 后严格门回归承诺注记维持）。

### T-03 对比表滚动行终态（G-4）

anchors/render 027 代行落位（022/024/026 历史行不删——四代并
陈）+--verify/--check 双绿。

### T-04 M4.3 tag 素材（G-5）

素材备档（十行终态+M4 三层收口径+**验收全绿层**+余题清单终态
〔供⑭/RQHost 门/NP++ 条件件+泵域钉版注记〕）；打点位注记
（merge 阶段执行——五检查点后，惯例）。

### T-05 规范+账本（G-6）

SD-01..03+P027-1（015-026 先例——merge 期项）+范围断言（零 .at
diff）。

### 规范增量

| delta_id | add/modify/retire | docs/specs/... target | before/after rule | rationale | acceptance IDs |
|---|---|---|---|---|---|
| SD-01 | modify | docs/specs/modules/perf-measurement.md | before：PLAN-026 终判节（两行 FAIL 维持——驱动节奏+通道伪影定责，发布门不解锁） / after：**帧两行终裁节**（测量实施修订记录〔Q-1 回执〕+呈现面判定谱+四代谱系）+**十行全绿终态快照**+**发布门解锁注记**（战略 §2.1 兑现时点） | 预算面终态真源 | AC-02/03 |
| SD-02 | modify | docs/specs/00-overview.md | before：M4 完全体收口件注记（026——重判收口态） / after：**M4 验收全绿注记**（四代谱系终态+发布门解锁+v0.1-M4.3 tag 记录位+余题清单终态〔条件件+泵域钉版注记〕） | 里程碑验收全绿总览 | AC-05 |
| SD-03 | modify | specs/auto-edit/README.md | before：PLAN-026 口径 / after：PLAN-027 口径+终态表（修订协议用法+终裁数字+四代滚动行+tag 位） | 运行矩阵/工具单源 | AC-04/05 |

## 6. 测试设计

- **终裁谱**：N≥4 复跑+P50/P95 判定+四代对照列（前三代谱不删）；
  scroll 面板率读回复核+驱动节拍有效性断言（16ms 节拍下 distinct
  present 频谱 vs 驱动率上限归因注记）。
- **735 复验**：ladder735.py 同机复跑——配对率 100% 带+draw_end
  通道+S5/segsum 零回退带。
- **通道新鲜度**：fprobe present_ms vs 探针行 draw_end 对照表
  （带内=零上游依赖断言）。
- **口径 frozen 断言**：阈值/语义零变更（budgets budget 字段
  diff=零）+测量实施修订面 diff 限 bench.py 帧区域（Q-1 裁定
  回执随附）。
- **budgets/对比表门**：--verify/--check 双绿+四代并陈渲染断言。
- **范围断言**：零 .at diff+auto-lang 主树零改动+检查集零变更。

## 7. 验收标准

- **AC-01 工具链+735 复验**：核哈希在录+配对率/draw_end 通道复验
  带内在档。验证：复验记录。
- **AC-02 帧两行终裁**：判定谱 N≥4 在档——转绿=两行 armed PASS
  （四代谱系注记+Q-1 修订回执）；仍红=归因回执（双态如实）。
  验证：谱 JSONL+budgets。
- **AC-03 十行快照+发布门解锁**：终态表+解锁注记成文（renderer
  n/a 例外说明+RQHost 承诺注记）。验证：SD-01+budgets。
- **AC-04 对比表终态**：027 代行+历史不删+双绿门。验证：render
  输出+--check。
- **AC-05 tag 素材+规范+账本**：素材与终态一致+SD-01..03 落档+
  P027-1 回读 True（merge 期）+零越界断言。验证：素材档+账本+
  路径断言。

## 8. 执行步骤

| # | 任务 | 依赖 | 落点（实勘锚） | 产出/意图 | AC | 验证（命令/预期） |
|---|---|---|---|---|---|---|
| 0 | T-00 终裁勘定 | — | 本件 §5 T-00 节 | 工具链门+复验+Q-1 材料 | AC-01 | [x] 四门全绿（工具链门=release 组树重建 **v0.4.2-2704-gde3a64353** clean〔组三树 edit-027：auto-edit@plan-027-dev base 252028a+auto-lang@de3a64353 detached+auto-down@895f8d0 detached——**735@4195f7af9+737@59ff4e66f+731@30bda6831 祖先链 merge-base 三实证**；plan 起草时 master 实勘位 fecf9a590 已被 737 交付推进，735 祖先链在位=门语义满足，737 增量〔MCP spawn_blocking〕如实注记〕+bench check 绿〔PATH 坑纪律=AUTO_BIN 钉 worktree release〕）；**735 回执谱同机复验带内**（组树 ladder735.py 处方复跑：1mb s5 P50 0.37/0.36/0.36ms vs 回执 0.36/0.33/0.30+泵率 10.28/2.76/10.56 vs 10.07/2.60/10.08 同带+**配对率 100% 全相位**（复验 236 帧零 orphan——F-1 计数补正）+type total P95 0.01ms 全等——零回退环境噪声排除，复验谱 tests/evidence-p027-upstream-reverify.jsonl）；**通道新鲜度勘定带内**（probe_frame_channel.py：fprobe 9919 消费时刻 vs 行通道 draw_end 真值 **Δ P50 1ms/max 19-31ms**+行配对 100%——配对修复后消费≈呈现→**9920 零上游依赖不接线**，条件路由位关闭）；**Q-1 材料定稿**（16ms 节拍校准：MCP 调用地板 p50 14.1-15.8ms→有效驱动 ~30ms 周期 ~34Hz〔调用时延主导，节拍再降无效〕；**关键实证=真实 app 帧泵回环 ~95ms/圈为呈现吞吐上限 ~10/s**——draw_end 间隔 91-95ms 恒定与驱动节拍无关〔30ms 驱动下仍 91-95ms〕，突发内 0-1ms 连建+帧工作面 2-3ms 全绿=735 §4 机制候选 (b)「泵回环自 paced」下游实证→**type 面帧内 P95 预期转绿 ~3ms ≤16.7ms；scroll 面 54fps 物理不可达（泵上限非驱动上限——735 §3.3 预判的下游修正：泵域不在 735 修复范围=上游域余题② 实证落位）**；证据=tests/evidence-p027-frame-channel.jsonl；判定阈值/语义零变更） |
| 1 | T-01 帧两行终裁 | T-00+Q-1 | bench frame 档+budgets | 终判（转绿/归因） | AC-02 | [x] **type_latency armed PASS 首绿**（行通道 P50 2-3/P95 3-4ms ≤16.7——N=4 全有效 24-30 脏帧/跑配对 100%+冒烟谱，frame-20261003-114018/114048/114111/114135/114158.jsonl 入仓）+scroll_fps armed FAIL 维持（9.6-10.0fps<54——红面定责=帧泵回环吞吐上限，fprobe 对照 5.4-8.8fps 并陈）；**Q-1 双修裁定落实施**（bench.py 帧区域一次修订四项：读回主读切行通道+fprobe 退役对照列逐跑并录/16ms 节拍〔对照相 022 原样=A/B 双通道〕/成员过滤勘定 dirty==1∧present>0〔ladder 上游款 s2_us>0 下游不适用——19/22 脏帧 VM 段 0µs 实勘〕/值域锚点窗口切片〔app stdout 块缓冲滞后——中途行数切片不可靠执行期勘定〕）；阈值/语义/面板读回零变更（budget 字段 diff=零 frozen 实证） |
| 2 | T-02 十行快照+解锁 | T-01 | budgets+SD-01 | 全绿+发布门解锁注记 | AC-03 | [x] **十行终态 as-is（Q-1 裁定适配——9 PASS+1 FAIL+renderer n/a，发布门不解锁维持）**：十行表落 SD-01（type 027 首绿/scroll 泵上限归因行）+budgets 两行 027 代注记（unlock 行收口注记随行——type 管线+读数两面清偿收口/scroll 解锁前置换代=上游泵域清偿）；发布门注记成文（战略 §2.1 维持不解锁——scroll 一行未达；Q-1 裁定回执明示此态=授权适配非验收弱化，026 F-4 先例） |
| 3 | T-03 对比表终态 | T-01 | compare 双件+README | 四代并陈 | AC-04 | [x] 四代并陈双绿（anchors 11→12 行新增 027 行〔9.99fps 终跑谱+泵上限归因+fprobe 对照并陈+解锁前置注记〕——--verify 12 行逐字全等绿+render --check 复现一致绿；README 生成区间随 render 更新；022/024/026 历史行零删） |
| 4 | T-04 tag 素材 | T-01..03 | 素材档 | M4.3 备档 | AC-05 | [x] 素材备档对账一致（evidence-p027-m4-accept-green——十行终态逐字对账+M4 四层收口径点位+余题清单终态〔判定通道语义适配 027 关闭〕+v0.1-M4.3 tag 素材块〔Q-2 默认命名用户裁定 2026-10-03〕+735 消费回执六章〔配对确认/真相通道消费/9920 不接线裁定/§3.3 修正回执/§4.1 兑现确认/瞬态零复现〕）+帧终裁归因回执 evidence-p027-frame-final（T-00 四门+泵上限定责+N=4 谱+协议修订四项+frozen 断言）；打点=merge 期五检查点后（惯例） |
| 5 | T-05 规范+账本 | 全 | SD-01..03+P027-1 | 收口落账 | AC-05 | [x] SD 全落档@worktree（SD-01=perf-measurement PLAN-027 终裁节〔四门+校准+终判谱+协议修订回执+十行表+发布门注记〕；SD-02=00-overview M4 验收全绿注记〔四层收口径+tag 记录位+余题清单终态〕；SD-03=README PLAN-027 口径段）+范围断言绿（**零 .at diff**+auto-lang/auto-down 组树双净+**budget 字段 diff=零**+修订面 diff 限 bench.py 帧区域+probe 新件+检查集=修订协议面非判定语义）；P027-1=merge 期项 015-026 先例（work 不碰活账本） |

## 9. 复审记录

- 2026-10-03 起草 handoff：`stage: new`，PLAN-027，plan_revision 1。
  `outcome: pass`（起草完备：735 交付面逐项承接〔定责/配对修复/
  draw_end 通道/重判件预告四条〕；**测量实施修订与口径变更的分界
  明文**〔阈值/语义 frozen 原样——修订=读回机制+驱动节拍，Q-1
  用户裁定背书；防作弊纪律原样〕；双态如实+谱系不删两纪律延续；
  十行全绿+发布门解锁有战略原文依据；上游 9920 接线=条件路由位
  〔通道新鲜度勘定先行——默认零上游依赖〕；路径/符号经
  auto-edit@252028a 与 auto-lang@fecf9a590[735@4195f7af9 祖先链]
  双仓实勘锚定；授权=起草〔用户「请继续本会话的任务」指令+026
  归档预告位点〕，执行待用户启动——Q-1..Q-3 见 §10）。`next:
  work`。
- `stage: work | PLAN-027 | plan_revision 1 | outcome: pass（执行
  完备——终裁结果=Q-1 裁定臂如实落账〔type 首绿+scroll 泵上限归因
  红——裁定回执明示此态〕；双态如实+谱系不删纪律全程维持）|
  code_commit: worktree plan-027-dev@552c789（base 252028a；四提交
  =365a21d T-00 终裁勘定/f76e8e5 T-01 终裁+修订实施/d42af6c T-02+
  T-03 十行态+四代并陈/552c789 T-04+T-05 素材+SD-02/03）| task_ids:
  T-00..T-05 全 delivered | evidence: ①工具链门=v0.4.2-2704-
  gde3a64353 release 组树构建 clean〔auto-lang@de3a64353 detached
  ——735@4195f7af9+737@59ff4e66f+731@30bda6831 祖先链 merge-base
  三实证；737 推进=起草后 master 交付如实注记〕+auto-down@895f8d0
  detached+bench check 绿；②**735 回执谱同机复验带内**〔ladder735.py
  处方复跑：s5 P50 0.37/0.36/0.36 vs 0.36/0.33/0.30+泵率同带+配对
  率 100% 全相位——evidence-p027-upstream-reverify.jsonl〕；③**通道
  新鲜度带内**〔ΔP50 1ms/max 19-31ms+行配对 100%——9920 不接线，
  evidence-p027-frame-channel.jsonl〕；④**Q-1 用户裁定=双修采纳**
  〔AskUserQuestion 回执 2026-10-03〕+T-00 校准实证=帧泵回环 ~95ms/
  圈吞吐上限 ~10/s〔735 §4 候选 (b) 下游定责——735 §3.3 预判下游
  修正〕；⑤**终裁 N=4 全有效谱=type_latency armed PASS 首绿〔P50
  2-3/P95 3-4ms≤16.7——行通道主读 24-30 脏帧配对 100%〕+scroll_fps
  armed FAIL 维持〔9.6-10.0fps<54——泵上限定责；fprobe 对照
  5.4-8.8fps 同带并陈〕**；四代谱系 022/024/026/027 不删〔type 面通
  道换代直比禁则注记〕；⑥修订实施四项+frozen 断言〔budget 字段
  diff=零+阈值/语义/面板读回零变更〕；⑦budgets 两行 027 代注记+十
  行 as-is 快照〔9 PASS+1 FAIL+renderer n/a——发布门不解锁维持，
  Q-1 裁定适配 026 F-4 先例〕+对比表滚动行四代并陈〔--verify 12 行
  +--check 双绿〕+tag 素材档〔evidence-p027-m4-accept-green——
  v0.1-M4.3 验收全绿层语义，Q-2 默认命名裁定〕+SD-01..03；⑧范围
  断言：零 .at diff+auto-lang/auto-down 组树双净+修订面限 bench.py
  帧区域+probe 新件 | blockers: 无 | next: review（P027-1 账本投影
  =merge 期项——015-026 先例彩排位随 review/merge；v0.1-M4.3 tag
  打点=merge 期五检查点后）。`execution_done`（六检查点全勾、验收
  映射全落：AC-01 四门证据/AC-02 终判谱+Q-1 修订回执/AC-03 十行
  as-is 态+不解锁注记〔Q-1 裁定适配〕/AC-04 四代并陈+双绿门/AC-05
  素材对账+SD-01..03〔P027-1=merge 期〕+零越界断言；worktree 清洁
  态 0 dirty@552c789）。
- `stage: review | PLAN-027 | plan_revision 1 | outcome: pass |
  reviewed_commit: worktree plan-027-dev@552c789ec7ff59d0cf3a58ebf988fd46205360dc
  （0 dirty）| base_commit: 252028a | dependency_revisions:
  auto-lang@de3a64353 detached[735@4195f7af9+737@59ff4e66f+731@30bda6831
  祖先链复审独立重验 ✓]+auto-down@895f8d0 detached | spec_inputs:
  三 SD 目标文件@552c789[frozen delta=本提交树：perf-measurement
  PLAN-027 终裁节/00-overview M4 验收全绿注记/README 027 口径]
  | acceptance_results: AC-01..05 **五项全 pass**（同会话复审限制
  如实声明——全部从工件独立重建不采信执行摘要：①AC-01 工具链
  v0.4.2-2704-gde3a64353 复验+祖先链 merge-base 三重验+组树双净
  重跑+**735 复验谱独立重算**〔从复验 JSONL 原始行重提：s5 P50
  0.37/0.36/0.36 vs 回执 0.36/0.33/0.30 带内判据 |Δ|≤0.1ms∧泵率
  0.3×..3× 显式化+**配对 236/236=100.0% 独立重算**+type total P95
  0.01ms〕✓②AC-02 **N=4 谱 JSONL 独立重提五跑全复算**〔type
  P50 2-3/P95 3-4≤16.67+frames 24-30+pairing 100%+focus→PASS 复算
  True×4+冒烟；scroll 9.64-9.99<54→FAIL 复算 True×4〕+**budgets
  frozen 断言独立复验**〔budget/metric/tier 字段 diff=零+rows 10→
  10〕+**bench.py 修订面 diff 复勘**〔hunk 全限 stage_frame 帧区域+
  头注释/常量/助手；tl_pass/sf_pass 判定公式行内容零变更（移位重
  排）；面板读回/budget 计算零触碰〕✓③AC-03 十行表↔budgets 逐行
  对账程序化 10/10〔初查两 ✗=对账脚本伪影：scroll 027 注记窗口
  截断+open_1gb「armed 断言化收口」措辞差——直验数据完整；027 注
  记面=帧两行两行+八行维持前代=计划原样〕+发布门不解锁注记三 SD
  在档+renderer n/a+RQHost 承诺在表✓④AC-04 --verify 12 行+--check
  双绿复审独立重跑+四代并陈断言〔scroll 8.01/7.04/9.53/9.99 历史零
  删+027 行源=114158〕✓⑤AC-05 素材关键数字/语义 16 项 grep 对账
  全中+P027-1 活账本零触碰重验〔grep 0 命中；P026-1=2 命中为 026
  merge 既有〕+范围断言〔零 .at diff+组树双净+修订面限帧区域〕
  重跑✓+**P027-1 彩排留 merge 期**〔015-026 先例〕）| **运行时验收
  活体复现**：HEAD 复现跑〔frame-20261003-115649——type P50 3/P95 6
  PASS〔31 帧配对 100%〕+scroll 13.3fps FAIL〔泵上限带内波动
  9.6-13.3，判定稳健 <54〕→ 复审复现非判定谱集，文件按 024 无效跑
  惯例外处置，数值记录于本条〕；谱复用理由=bench.py 自谱生成
  （f76e8e5）后零提交触碰〔git log 复勘〕——同码同配置，JSONL 独立
  重提替代重跑 | findings: F-1(info)=**「复验 264 帧」计数偏差**——
  实际=配对 236/236〔复验 JSONL 独立重算定责；264=起草时口算误〕
  ，三处出现位：plan T-00 勾选〔复审期已补正 236〕+evidence-p027-
  frame-final.md:29+evidence-p027-m4-accept-green.md:97〔worktree
  已提交档——随 merge 补正或以本记录 236 数值为准；100% 配对判定
  不受累〕；F-2(info)=budgets scroll 行 027 措辞「FAIL 维持（027
  代…）」未冠 armed 前缀〔该行历史代际措辞一致形——022/024/026
  同款，最小 diff 维持不改，记录在案〕；F-3(info)=AC-03 初查脚本
  伪影两 ✗〔窗口截断+措辞字面差——非工件缺陷，直验通过，记录在
  案〕| evidence: specs/auto-edit/tests/evidence-p027-{upstream-
  reverify,frame-channel}.jsonl+evidence-p027-frame-final.md+
  evidence-p027-m4-accept-green.md+tools/bench/results/frame-
  20261003-1140xx 五谱+SD-01..03@552c789 | next: merge（P027-1
  账本投影+v0.1-M4.3 tag 打点=merge 期五检查点后；F-1 evidence
  档计数补正随 merge 收据面落）。
- `stage: merge | PLAN-027 | plan_revision 1 | outcome: pass（五
  检查点全落 delivered）| delivery_commit: d7cccaa（reviewed_commit
  552c789 的 docs-only descendant——F-1 计数补正 2 行 docs，实现/
  依赖零变更核验；经两轮 ff-only：d7cccaa〔19 文件 1283+/45-〕+
  7f9862b〔P027-1 账本〕——零合并提交）| 五检查点：
  ①**prepared**=review 基线 main@252028a/工作树 plan-027-dev
  @552c789+依赖钉版 auto-lang@de3a64353 detached[735+737+731 祖先
  链]+auto-down@895f8d0 detached+wt-guard clean；②**landed**=
  ff-only 零合并+main tip=d7cccaa 后二轮 7f9862b〔merge-base=
  main tip=252028a 实证——rebase 零需要；main 烟测绿=budgets 10 行
  +frozen 字段 diff=零+anchors --verify 12 行+render --check 双绿+
  三 SD 锚点+帧谱 JSONL×5〕；③**ledger_refreshed**=P027-1 外科插
  入 28→29〔roundtrip 守卫：他五段+前缀 28 项零扰动+逐字回读——
  015-026 十二连先例；git 跟踪账本经 worktree+Git 通道；main 回读
  验真 id/section/status/file〕；④**archived**=本笔〔git mv 等
  价：untracked 计划文件 mv archived/+git add 入册+status: archived
  +completion_kind: delivered〕；⑤**cleaned**=三树 fresh clean
  〔wt-guard 三树 clean+占用预检=唯一 auto.exe 进程为主检出 debug
  二进制外来遗留〔PID 7968@main auto-lang——非组树非本会话产物，
  不阻塞〕+零组树进程〕+三 worktree 注销〔edit-027 组目录 rm——
  auto-edit remove 一次性 Permission denied 后 rm -rf 兜底清净，
  auto-lang/auto-down prunable 注册 prune 清〕+branch 删 was
  7f9862b 全落祖先链+组目录清——.wt 无残留+三仓 registry 零
  〔grep/prune 双验〕。**部署观察=零重建项维持**（本件纯
  tools/docs/specs/tag 面——零 Rust 生成物/零 web bundle/零
  后端产物消费面，026 同判）；**批量回归不适用**（auto-edit 无
  batch 文件——.last-batch-regression.json 缺席实证+023/024/025/
  026 四连同判）。**v0.1-M4.3 tag 打点=本收据五检查点后**
  （annotated tag@main tip=612efce——素材 evidence-p027-m4-accept-
  green 逐字；验收全绿层语义——Q-2 裁定命名）。
  F-1 补正随交付提交 d7cccaa 落（evidence 档 264→236 两处）。

## 10. 待澄清事项

- **Q-1 测量实施修订裁定——已裁定（用户 2026-10-03 AskUserQuestion
  回执=双修采纳）**：(a) 读回通道切呈现面（行通道 total_ms 主读+
  fprobe 对照列）+(b) 16ms 节拍——T-01 按此实施。裁定随附 T-00 校
  准实证：**帧泵回环 ~95ms/圈=呈现吞吐上限 ~10/s（与驱动节拍无关）
  ——scroll 54fps 在任何测量实施修订下物理不可达**（735 §3.3「驱动
  器是帧率上限」预判的下游修正——泵域不在 735 修复范围=上游域余题
  ②定责）；type 面帧内口径预期转绿（已兑现 P95 3-4ms）。备选（仅
  修读回/严格 frozen）未采纳。
- **Q-2 tag 命名——已裁定（用户 2026-10-03 回执=默认 v0.1-M4.3）**
  ：验收全绿层语义（type 首绿+验收主面全绿；scroll 泵域余题如实
  注记随行）；打点=merge 期五检查点后。
- **Q-3 发布决策联动（口径确认，无需裁定）**：发布门=预算面条件
  注记位——**本件终态=维持不解锁**（scroll_fps FAIL=泵域余题；
  十行全绿差一行）；对外发布决策与动作（渠道/时机/文案）=产品决策
  另行——本件不含。RQHost 后严格门（installer ≤20MB/idle ≤10MB 级）
  回归承诺注记维持。
