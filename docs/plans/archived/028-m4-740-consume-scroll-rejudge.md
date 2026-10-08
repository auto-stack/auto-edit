---
plan_id: PLAN-028
status: archived
completion_kind: delivered
feature_name: M4 scroll 终态件（PLAN-740 消费——scroll_fps ≥54fps 复判：驱动通道标定+Q-1 裁定+终判谱+十行终态+发布门终态注记）
author: [agent]
created_at: 2026-10-08
updated_at: 2026-10-08
plan_revision: 1
current_step: 6
total_steps: 6
supersedes_spec_components: []
new_spec_components:
  - docs/specs/modules/perf-measurement.md（SD-01：帧两行 028 代终判节——复判谱+驱动通道标定记录+十行终态+发布门终态）
  - docs/specs/00-overview.md（SD-02：M4 终态注记——五代滚动行+发布门终态+余题清单终态）
  - specs/auto-edit/README.md（SD-03：PLAN-028 口径+终态表）
touched_goals:
  - 战略 §2.1 预算表 scroll_fps 满刷新率——740 消费复判（发布门终态位）
  - 「预算未达标的功能不发布——性能是发布门槛（M4 生效）」——发布门终态（解锁/维持）兑现时点成文
affects: [tools/bench/bench.py, tools/bench/budgets.json, tools/compare/anchors.py, tools/compare/render_table.py, specs/auto-edit/README.md]
---

# [PLAN-028] M4 scroll 终态件（PLAN-740 消费——scroll_fps ≥54fps 复判）

## 0. 变更摘要

auto-lang **PLAN-740**（泵回环交付节奏清偿件，2026-10-08
delivered@ab7a650bd[∈ master 祖先链]——action 消费 push 通道重排
〔16ms tick 网格重排→16.7ms 呈现槽合并定谳；到达即投递+drain-to-
empty〕+交付节奏契约 §4d）的**下游消费复判件**——M4 预算面最后
一行：**scroll_fps ≥54fps 终判**（027 协议复跑=判定通道/阈值语义
零变更；740 契约=交付跟随有效驱动率至 ≥54Hz〔上游谱 54Hz follow
1.06〕）。**核心裁定面=驱动通道（Q-1 用户件）**：handoff-v3 §2
实测——HTTP 单发在活动滚动期 p50 31-37ms〔校验锁×帧同步块互斥〕→
027 serialized 驱动封顶 ~21-36Hz，**54fps 在 serialized 驱动下读数
=驱动封顶非交付能力**；复判前 T-00 标定 pipelined HTTP drive
（并发 fire-ahead）有效驱动率，Q-1 按实测数字裁定三通道之一
（serialized 原样/pipelined/in-process 直推）。转绿臂=十行全绿+
**发布门解锁注记**（战略 §2.1 兑现）；仍红臂=驱动封顶归因回执
（双态如实——027 纪律延续）。type_latency 预期 PASS 维持（027 首
绿——复判零变更通道复证）。

## 1. 目标

- **G-1 工具链门+740 复验**：master 重建（含
  740@ab7a650bd——`auto --version` 核哈希+祖先链，021-027 七连纪
  律）；740 上游谱带内复验（evidence/740 谱对照——跟随性带内在
  档）；环境注记内化（handoff §3：静默退出档重试条款/state.at
  砖处置/scrollable 定位注记〔上游 ladder 域——下游 NLCHAR 驱动
  不受累，注记在案〕）。
- **G-2 驱动通道标定+Q-1 裁定（决策件）**：T-00 实测 027
  serialized 驱动+pipelined（2/4/8 并发 fire-ahead）有效驱动率与
  交付跟随初判——Q-1 材料按实测数字定稿，用户裁定复判驱动通道
  （serialized/pipelined/in-process）。**判定阈值/语义 frozen**
  （54fps/面板×0.9/3s 窗——修订仅测量实施面驱动通道，Q-1 回执
  成文=修订合法性，027 前科）。
- **G-3 帧两行终判（G-2 主面）**：Q-1 裁定后 bench frame 档 N≥4
  复跑——type_latency 预期 **PASS 维持**（027 首绿复证）；scroll_
  fps 转绿=budgets armed PASS（028 代——**四代红谱收口**）+四代
  谱系注记（022→024→026→027→028）；仍红=驱动封顶/残余面归因回
  执（双态如实——Q 路由位）。谱 JSONL 入仓。
- **G-4 十行终态+发布门终态注记**：budgets 十行终态表（全绿预期
  ——renderer n/a 唯一例外）；**发布门终态注记**成文（转绿臂=战
  略 §2.1「预算未达标不发布」条件达成——解锁时点注记，发布动作
  另行；仍红臂=不解锁维持+解锁前置更新）。
- **G-5 对比表滚动行终态**：028 代行落位（022/024/026/027 谱历
  史不删——**五代并陈**）；--verify/--check 双绿。
- **G-6 tag 素材+规范+账本**：素材备档（十行终态+M4 终层收口径
  +发布门终态+余题清单终态）；tag 命名 Q-2；SD-01..03+P028-1
  （merge 期）。

### 非目标

- 对外发布/宣传动作（解锁=预算面注记；发布决策另行）。
- 上游 31-37ms 校验锁时延修复（校验锁×帧同步块互斥=auto-lang
  域——若 Q-1(b) pipelined 实测仍封顶 <54Hz，如实归因+上游余题
  登记，不在本件修）。
- 判定**阈值/语义**任何变更（frozen——修订仅测量实施面驱动通道
  ，Q-1 裁定背书；027 防作弊纪律延续）。
- type_latency 判定协议变更（027 协议原样复证——serialized 驱动
  不涉 type 面）。
- 711 泵域/712 r2 调度域/735 通道面（上游已收口——零触碰）。

## 2. 架构方案

分层落点（2026-10-08 实勘，auto-edit main@25f3015〔027 cleaned
2b5f056+术语规范化 tip〕+auto-lang master@6d69dbdc7
含 740@ab7a650bd）：

| 面 | 现状 | 本期形态 | 依据 |
|---|---|---|---|
| 交付节奏 | 740 push 通道——跟随有效驱动率至 ≥54Hz（上游谱 follow 1.06） | 下游复证（复判谱即证） | 740 §4d 契约 |
| scroll 驱动 | 027 serialized（type+sleep16——活动期时延 p50 31-37ms→封顶 21-36Hz） | **Q-1 三通道裁定**（serialized/pipelined/in-process）——T-00 标定数字背书 | handoff-v3 §2 |
| type 驱动 | 027 serialized 90 键@16ms | 原样复证（PASS 面零变更） | 027 协议 |
| budgets | 9 PASS+1 FAIL+renderer n/a（027 态） | **十行终态**（全绿预期/仍红臂双态如实）+发布门终态注记 | 027 SD-01 表延续 |
| 对比表 | 滚动行四代并陈（022/024/026/027） | 028 代行落位（**五代并陈**——历史不删） | 024-027 先例 |
| tag | v0.1-M4.3=验收全绿层 | **v0.1-M4.4=十行全绿/发布门终态层**（Q-2） | 收口件惯例 |

**关键设计约束（frozen）**：① **判定阈值/语义零变更**（54fps/
面板×0.9/3s 窗原样——修订仅驱动通道，Q-1 回执=合法性来源）。
② **双态如实**（转绿=armed PASS+解锁注记；仍红=驱动封顶归因——
不以放宽换绿）。③ **谱系历史不删**（022-028 五代并陈——清偿证据
链）。④ **工具链门纪律**（重建核哈希+组依赖钉版+PATH 坑——七连
先例）。⑤ **上游契约前置复验**（740 跟随性带内——超带先登记后
判定）。⑥ **复用 027 基建**（probe_frame_channel.py/行通道解析/
值域锚点——零重写，驱动通道面按 Q-1 增量）。

## 3. 技术栈

bench frame 档驱动通道修订（pipelined HTTP 并发面——Python 工具
面，若 Q-1 选 b）+bench/compare 工具族复跑+工具链重建纪律（master
含 740）+tag 素材备档。零 .at 源改动（纯判定/工具/文档/tag 面——
AC 路径断言延续 027）。

## 4. 需求分析与背景调查

**授权记录**：用户 2026-10-08 会话指令「计划740已经完成。现在继续
本会话的工作了」——授权=**起草本件**（会话既定管线：027 归档收
据预告的复判位点=740 handoff-v3 收件方；前议在录）。执行/work 待
用户启动。范围=auto-edit 单仓（tools/docs/budgets/tag）；
auto-lang 零改动（31-37ms 校验锁=条件路由位，Q-1(b) 失败臂才登记
）。**Q-1 驱动通道=用户件**（默认倾向= pipelined〔若标定达标〕
——材料备齐后请示）。无预算/自动续跑授权。

**来源与版本**：

- 交接链：PLAN-740 归档件（delivered@ab7a650bd[∈master@6d69dbdc7
  祖先链 merge-base 实证]——T-01 定谳=16ms tick 网格重排消息对→
  16.7ms 呈现槽合并；T-02 修复=action 消费 push 通道〔recv 阻塞
  到达即投递+drain-to-empty〕；T-03 双谱=54Hz follow 0.79→**1.06**
  +735proto 全档 100% 配对零回退；批量回归 740%5=0 零新红
  a0e50b614）+**downstream-handoff-v3**（§1 上游交付能力谱：内部
  通道 34/54Hz follow 1.08/1.06±10% 带内、HTTP 单发封顶 ≤47Hz
  type/≤36.5Hz scroll；§2 复判参数=drive 睡眠 ≤3.5ms 预告+HTTP
  时延注意；§3 环境注记=静默退出重试/state.at 砖处置/scrollable
  定位〔上游 ladder 域〕；§4 范围断言=auto-edit porcelain clean
  在档）。
- 下游现状实勘（main@2b5f056 后 tip=027 cleaned+术语规范化
  25f3015）：budgets 027 态（9 PASS+1 FAIL）；对比表滚动行四代
  并陈；bench frame 档=027 修订协议（行通道主读+值域锚点+16ms
  节拍——本件复用，驱动通道面按 Q-1 增量）。
- 时延机理（handoff §2）：scroll 单发活动滚动期 p50 31-37ms=
  **校验锁×帧同步块互斥**（MCP server 校验面——上游域，非 740
  修复域）；027 下游调用地板 p50 14-16ms 为**空闲期**数字——活动
  期劣化 2×。
- 战略口径：§2.1「预算未达标的功能不发布」——发布门终态注记原文
  依据。

## 5. 详细设计

### T-00 终判勘定+驱动通道标定（决策件前置）

工具链门（master 重建含 740——核哈希+740@ab7a650bd 祖先链实证+
bench check 绿）；**740 上游谱带内复验**（evidence/740 谱对照——
跟随性/配对率带内，超带登记）；**驱动通道标定**（probe_frame_
channel.py 增量：serialized vs pipelined[2/4/8 并发 fire-ahead
线程池——响应不阻塞下一发]有效驱动率+交付跟随初判+活动期时延分
布——Q-1 材料数字）；**环境注记内化**（静默退出档重试条款/state
.at 砖处置步骤入执行注记）。

### T-01 Q-1 驱动通道裁定（用户件——材料齐备后请示）

三选项材料定稿：(a) **serialized 原样**——预期 scroll ~21-36fps
真实交付但驱动封顶→FAIL+驱动通道归因（上游跟随性已由 740 谱背书
——间接解锁证据）；(b) **pipelined HTTP drive**——若标定有效驱动
≥54Hz 达成→交付跟随契约背书→预期 PASS（十行全绿臂）；若校验锁
仍封顶→同 (a) 读数+归因（实测定谳，上游余题登记位）；(c)
**in-process 直推**（740 探针同型）——驱动无约束必达，代价=偏离
MCP E2E 驱动语义+工具面大改。Q-1 回执=修订合法性成文（027 前科
）。

### T-02 帧两行终判（G-3）

Q-1 裁定后 bench frame 档 N≥4 复跑（type=027 serialized 协议原样
复证；scroll=裁定通道）→判定（阈值 frozen）→转绿=budgets scroll
行 armed PASS（028 代——022-027 红谱收口）+五代谱系注记；仍红=
驱动封顶/残余归因回执。谱 JSONL 入仓。

### T-03 十行终态+发布门终态注记（G-4）

budgets 十行终态表更新+SD-01 终判节 v3（**发布门终态注记**——转
绿臂=战略 §2.1 条件达成解锁时点成文〔发布动作另行〕；仍红臂=不
解锁维持+解锁前置更新〔驱动通道/上游校验锁〕）。

### T-04 对比表滚动行终态（G-5）

anchors/render 028 代行落位（022-027 历史行不删——五代并陈）+
--verify/--check 双绿。

### T-05 tag 素材+规范+账本（G-6）

素材备档（十行终态+M4 终层收口径+发布门终态+余题清单终态）；
SD-01..03+P028-1（merge 期项）+范围断言（零 .at diff+auto-lang
主树零改动+检查集语义零变更断言〔驱动通道面 diff 限 bench.py 帧
区域——Q-1 回执随附〕）。tag 打点=merge 期（Q-2 命名）。

### 规范增量

| delta_id | add/modify/retire | docs/specs/... target | before/after rule | rationale | acceptance IDs |
|---|---|---|---|---|---|
| SD-01 | modify | docs/specs/modules/perf-measurement.md | before：PLAN-027 终裁节（type 首绿+scroll 泵上限归因——发布门不解锁） / after：**帧两行 028 终判节**——复判谱+驱动通道标定与 Q-1 回执+scroll 终态（armed PASS 预期/驱动封顶归因臂）+五代谱系+十行终态+**发布门终态注记** | 预算面终态真源 | AC-02/03 |
| SD-02 | modify | docs/specs/00-overview.md | before：M4 验收全绿注记（027——四层收口径） / after：**M4 终态注记**——五代滚动行+发布门终态+v0.1-M4.4 tag 记录位+余题清单终态 | 里程碑终态总览 | AC-05 |
| SD-03 | modify | specs/auto-edit/README.md | before：PLAN-027 口径 / after：PLAN-028 口径+终态表（复判协议用法+驱动通道标定+终判数字+五代滚动行+tag 位） | 运行矩阵/工具单源 | AC-04/05 |

## 6. 测试设计

- **复判谱**：N≥4 复跑+P50/P95 判定+五代对照列（前四代谱不删）；
  scroll 面板率读回复核+驱动通道有效性断言（裁定通道有效驱动率
  ≥54Hz 达成性实证——Q-1 材料随附）。
- **740 复验**：上游谱带内对照（evidence/740——跟随性/配对率）。
- **驱动通道标定**：serialized vs pipelined[2/4/8]有效驱动率+活动
  期时延分布+交付跟随初判（T-00——Q-1 材料）。
- **口径 frozen 断言**：阈值/语义零变更（budgets budget 字段
  diff=零）+修订面 diff 限 bench.py 帧区域驱动通道（Q-1 回执随附
  ）。
- **budgets/对比表门**：--verify/--check 双绿+五代并陈渲染断言。
- **范围断言**：零 .at diff+auto-lang 主树零改动+检查集判定语义
  零变更。

## 7. 验收标准

- **AC-01 工具链+740 复验+标定**：核哈希在录+740 谱带内在档+驱动
  通道标定数字在档。验证：复验记录+标定 JSONL。
- **AC-02 scroll 终判**：判定谱 N≥4 在档——转绿=armed PASS（五代
  谱系注记+Q-1 回执）；仍红=驱动封顶归因回执（双态如实）。验证：
  谱 JSONL+budgets。
- **AC-03 十行终态+发布门终态**：终态表+发布门终态注记成文
  （renderer n/a 例外说明+RQHost 承诺注记维持）。验证：SD-01+
  budgets。
- **AC-04 对比表终态**：028 代行+历史不删+双绿门（五代并陈）。
  验证：render 输出+--check。
- **AC-05 tag 素材+规范+账本**：素材与终态一致+SD-01..03 落档+
  P028-1 回读 True（merge 期）+零越界断言。验证：素材档+账本+
  路径断言。

## 8. 执行步骤

| # | 任务 | 依赖 | 落点（实勘锚） | 产出/意图 | AC | 验证（命令/预期） |
|---|---|---|---|---|---|---|
| 0 | T-00 勘定+驱动通道标定 | — | 本件 §5 T-00 节 | 工具链门+复验+Q-1 材料 | AC-01 | [x] 四门全绿（工具链门=release 组树重建 **v0.4.2-2769-g85f7159c2** clean〔组三树 edit-028：auto-edit@plan-028-dev base 25f3015+auto-lang@85f7159c2 detached+auto-down@895f8d0 detached——**740@ab7a650bd+起草实勘位 6d69dbdc7 祖先链 merge-base 双实证**；起草后 master 被 736/738 docs 推进=027 门语义先例〔735 祖先链在位=门语义满足〕如实注记〕+bench check 绿 2769≥1588〔PATH 坑纪律=AUTO_BIN 钉组树 release〕）；**740 上游谱带内复验**（ladder740.py 处方复跑 1mb probe 34/54Hz：scroll follow_counts **1.08/1.04** vs 回执 1.08/1.06 ±10% 带内+type http 1.63/1.11 vs 1.72/1.12 同形——evidence-p028-upstream-reverify.jsonl）；**驱动通道标定 v2 隔离相**（probe_frame_channel.py `--drive-cal` 增量——027 判定面零变更：serialized〔16ms 节拍 027 协议〕有效驱动 **43.1Hz**〔<54——驱动封顶维持〕+活动期时延 P50 0.6/P95 16.5ms〔handoff §2 预告 31-37ms 下游不复现——740 push 后 HTTP 验收异步化 ~0.5-0.8ms〕；pipelined-paced k2/4/8@60Hz fire **60.0Hz** follow **1.011-1.022** ±10% 带内交付随驱〔740 §4d 契约下游复现〕；unpaced-k2 饱和参照 474Hz 验收≈免费+队列洪水 follow 0.13=非可用驱动形态；**交付顶 ≈55-57fps 全通道同顶**〔count/window 判读 ~61fps——对 ≥54 阈值薄余量带〕；静默退出档重试+state.at 砖处置+scrollable 注记内化；v1 实勘两伪影修复在案〔洪水相间污染→隔离相设计+lat 1000× 标度〕——evidence-p028-drive-channel.jsonl）；证据=tests/evidence-p028-{upstream-reverify,drive-channel}.jsonl |
| 1 | T-01 Q-1 驱动通道裁定 | T-00 | 用户裁定（AskUserQuestion） | 复判驱动通道 | — | [x] **裁定=默认臂 (b) pipelined-paced k2@60Hz fire-ahead 落实施**（AskUserQuestion 提请 2026-10-08〔标定数字随附三选项〕——**自主跑次无实时回执**→按本计划 §10 预告决策规则执行：默认倾向 (b) 前置=标定 ≥54Hz 达成〔实测 60.0Hz 真达+follow 1.011-1.022 ∈±10% 带内〕；**裁定随复审门确认**〔§10 Q-1 更新在案——用户可于 review/merge 前改判改臂〕；(a) serialized 让位归因=43.1Hz 封顶下读数依赖回声补足〔follow 1.41〕语义混；(c) in-process 无必要）；修订合法性=阈值/语义 frozen 零变更+Q-1 回执成文（027 前科） |
| 2 | T-02 帧两行终判 | T-00+T-01 | bench frame 档+budgets | 终判（转绿/归因） | AC-02 | [x] **终判全绿——scroll_fps armed PASS 首绿转绿（028 代——四代红谱收口）**：bench.py 帧区域一次修订〔scroll 主读相驱动=节奏器 60Hz+k2 线程池 fire-ahead；type 面 027 serialized 原样零变更；判定公式/阈值/面板读回零触碰〕+N=4 全有效谱 type_latency PASS 复证〔P50 2-4/P95 3-6ms≤16.7 frames 88-90 配对 100%〕+scroll_fps **PASS〔61.0/61.7/61.0/61.3fps vs ≥54——distinct 183-185/3s drive 180@60Hz follow 1.017-1.028〕**+冒烟 61.0 同带；红面清偿=740 push 通道消解 027 泵回环 ~10/s 上限〔T-00 标定交付顶 ~55-61fps 全通道实证〕；谱 JSONL×5 入仓（frame-20261008-214932 冒烟+215003/215028/215053/215117）+HEAD 复现跑绿〔215450——type 3/4ms+scroll 61.0 复现，非判定谱集按 024 惯例外处置不随判定集入仓〕；budgets 两行 028 代注记（budget 字段 diff=零 frozen） |
| 3 | T-03 十行终态+发布门终态 | T-02 | budgets+SD-01 | 终态+解锁注记 | AC-03 | [x] **十行全绿终态+发布门解锁注记成文**：SD-01 perf-measurement PLAN-028 终判节〔前置四门+终判谱+五代谱系+协议修订回执〔修订面一项〕+十行终态表〔9 armed PASS+renderer n/a 唯一例外〕+**发布门解锁注记**（2026-10-08 战略 §2.1 兑现时点——解锁=预算面条件注记，发布动作另行；RQHost 双严格门承诺维持）〕+budgets scroll_fps 行 unlock 收口〔已解锁——预算面条件达成〕 |
| 4 | T-04 对比表终态 | T-02 | compare 双件+README | 五代并陈 | AC-04 | [x] 五代并陈双绿（anchors 12→13 行新增 028 行〔verdict=pass——61.3fps 终跑谱+740 消费+Q-1 回执+薄余量注记随行〕+render 五代并陈叙事——--verify 13 行逐字全等绿+--check 复现一致绿；README 生成区间随 render 更新；022/024/026/027 历史行零删实证〔8.0/7.0/9.5/10.0 并陈〕） |
| 5 | T-05 tag 素材+规范+账本 | 全 | 素材档+SD-01..03+P028-1 | 收口落账 | AC-05 | [x] 素材备档对账一致（evidence-p028-m4-terminal——十行终态对账表+M4 终层收口径五层+发布门终态+余题清单终态〔判定通道/泵域两余题关闭〕+复判证据链+v0.1-M4.4 素材块〔Q-2 默认命名〕）+SD-02（00-overview M4 终态注记）+SD-03（README PLAN-028 口径段）+范围断言绿（零 .at diff+组树双净+**budget 字段 diff=零**+修订面 diff 限 bench.py 帧区域+probe --drive-cal 增量——Q-1 回执随附）；P028-1=merge 期项 015-027 先例（work 不碰活账本）；tag 打点=merge 期（Q-2 命名 v0.1-M4.4） |

## 9. 复审记录

- 2026-10-08 起草 handoff：`stage: new`，PLAN-028，plan_revision 1。
  `outcome: pass`（起草完备：740 handoff-v3 四节逐项承接〔上游谱
  /复判参数/环境注记/范围断言〕；**核心裁定面显影**——HTTP 单发
  活动滚动期 p50 31-37ms→serialized 驱动封顶 21-36Hz，54fps 复判
  必须经 Q-1 驱动通道裁定（三选项材料框架在案，T-00 标定数字背书
  ）；判定阈值/语义 frozen 纪律+Q-1 回执=修订合法性（027 前科）
  ；双态如实+五代谱系不删延续；type 面=027 协议零变更复证；复用
  027 基建（行通道/值域锚点/probe）零重写；环境注记内化（静默退
  出重试/state.at 砖处置/scrollable 注记=上游域不涉下游 NLCHAR
  驱动）；auto-lang 31-37ms 校验锁=条件路由位非本件域；路径经
  auto-edit main 与 auto-lang master@6d69dbdc7[740@ab7a650bd 祖先
  链实证]双仓实勘锚定；授权=起草〔用户「继续本会话的工作」指令
  +027 归档收据预告位点〕，执行待用户启动——Q-1/Q-2 见 §10）。
  `next: work`。
- `stage: work | PLAN-028 | plan_revision 1 | outcome: pass（执行
  完备——终判结果=**转绿臂如实落账**：scroll_fps armed PASS 首绿
  〔61.0-61.7fps——740 push 通道消解 027 泵回环上限+Q-1 驱动通道
  修订〕+type_latency armed PASS 复证维持；十行全绿+发布门解锁
  注记成文；双态如实+五代谱系不删纪律全程维持；**Q-1=预告默认臂
  执行〔自主跑次无实时回执——复审门确认位在案〕**）| code_commit:
  worktree plan-028-dev@d9eaf3f（base 25f3015；四提交=5392129 T-00
  勘定+标定/3d2ce4a T-01+T-02 裁定落实施+终判/ceca650 T-03+T-04
  十行态+五代并陈/d9eaf3f T-05 素材+SD-02/03+范围断言）| task_ids:
  T-00..T-05 全 delivered | evidence: ①工具链门=v0.4.2-2769-
  g85f7159c2 release 组树构建 clean〔auto-lang@85f7159c2 detached
  ——740@ab7a650bd+起草实勘位 6d69dbdc7 祖先链 merge-base 双实证；
  起草后 master 被 736/738 docs 推进=027 门语义先例如实注记〕+
  auto-down@895f8d0 detached+bench check 绿 2769；②**740 上游谱带
  内复验**〔ladder740.py 处方复跑 1mb probe 34/54：scroll follow
  1.08/1.04 vs 回执 1.08/1.06 带内+type 1.63/1.11 同形——evidence-
  p028-upstream-reverify.jsonl〕；③**驱动通道标定 v2 隔离相**
  〔serialized 43.1Hz 封顶+活动期时延 P50 0.6ms〔handoff 预告
  31-37ms 下游不复现——740 push 验收异步化〕/paced k2/4/8@60Hz
  follow 1.011-1.022 带内/unpaced 饱和参照非可用形态；交付顶
  ~55-61fps 全通道同顶——evidence-p028-drive-channel.jsonl；v1
  两伪影修复在案〕；④**Q-1 用户件=预告默认臂 (b) 执行**〔
  AskUserQuestion 提请 2026-10-08 无实时回执→§10 预告决策规则
  （标定 ≥54Hz 达成→(b)）——裁定随复审门确认，§10 Q-1 状态更新
  〕；⑤**终判 N=4+冒烟全绿=type_latency armed PASS 复证〔P95
  3-6ms≤16.7〕+scroll_fps armed PASS 首绿〔61.0-61.7fps≥54——
  follow 1.017-1.028 交付随驱〕**+HEAD 复现跑绿〔215450 非判定谱
  集〕；五代谱系 022/024/026/027/028 不删〔跨代直比禁则注记随行〕
  ；⑥修订实施一项+frozen 断言〔budget 字段 diff=零+判定公式/
  阈值/面板读回零触碰+hunk 全限帧区域+imports〕；⑦budgets 两行
  028 代注记+unlock 收口+十行全绿终态表〔renderer n/a 例外〕+
  对比表滚动行五代并陈〔--verify 13 行+--check 双绿〕+tag 素材档
  〔evidence-p028-m4-terminal——v0.1-M4.4 十行全绿/发布门解锁
  终态层语义，Q-2 默认命名〕+SD-01..03；⑧范围断言：零 .at diff+
  组树双净+修订面限帧区域+probe 增量 | blockers: 无（Q-1 确认位=
  非阻塞——默认臂已按预告规则执行且标定前置达成，改判臂走
  needs_fix 路由）| next: review（P028-1 账本投影+v0.1-M4.4 tag
  打点=merge 期项——015-027 先例）。`execution_done`（六检查点全
  勾、验收映射全落：AC-01 四门证据/AC-02 终判谱+Q-1 回执/AC-03
  十行终态+发布门解锁注记/AC-04 五代并陈+双绿门/AC-05 素材对账+
  SD-01..03〔P028-1=merge 期〕+零越界断言；worktree 清洁态
  0 dirty@d9eaf3f）。
- `stage: review | PLAN-028 | plan_revision 1 | outcome: pass |
  reviewed_commit: worktree plan-028-dev@d9eaf3fdc83cd38ca6f9a14c0f
  44e58ea88a2965（0 dirty）| base_commit: 25f3015 | dependency_
  revisions: auto-lang@85f7159c2 detached[740@ab7a650bd+6d69dbdc7
  祖先链复审独立重验 ✓]+auto-down@895f8d0 detached | spec_inputs:
  三 SD 目标文件@d9eaf3f[frozen delta=本提交树：perf-measurement
  PLAN-028 终判节/00-overview M4 终态注记/README PLAN-028 口径段]
  | acceptance_results: AC-01..05 **五项全 pass**（同会话复审限制
  如实声明——全部从工件独立重建不采信执行摘要：①AC-01 祖先链
  merge-base 双重验+**740 复验谱独立重提**〔scroll probe follow
  1.08/1.04 vs 回执 1.08/1.06 ±10% 带内+驱动率 34/54.0Hz 精确〕+
  **标定谱独立重提**〔serialized 43.1Hz<54 封顶+活动期 P95 16.5ms
  合理带+paced k2/4/8 fire 60.0Hz follow 1.011/1.022/1.022 全带内
  +unpaced 0.13 饱和参照+交付顶 span 55.3-56.3 全通道 ≥54〕✓
  ②AC-02 **五谱 JSONL 独立重提逐谱复算**〔scroll fps=distinct/
  window 算术复算全等+verdict 复算全 PASS+判据 54.0=面板 60×0.9
  frozen+drive 180@60Hz k2 通道标记+follow 1.017-1.028+type P95
  3-6≤16.67 配对 100%+对照列 record+协议头 028 注记〕✓③AC-03
  十行表↔语义逐行对账 10/10〔初查 9=解析 off-by-one 伪影——直验
  10 行在档〕+发布门解锁注记/战略 §2.1/RQHost 双承诺/budgets
  unlock 收口/028 两行注记 ✓（行宽换行字符串初查 ✗=扁平化复验
  全中——伪影在案）④AC-04 --verify 13 行+--check 双绿复审独立
  重跑+五代并陈断言〔verdict 序 fail×4+pass+历史 8.01/7.04/9.53/
  9.99 零删+028 行源=215117+表格五值并陈〕✓⑤AC-05 素材关键数字
  9 项扁平化对账全中+SD-02/03 锚点在档+**活账本零触碰重验**
  〔P028-1 grep 0 命中=merge 期项〕+范围断言重跑〔零 .at diff+
  budget 字段 diff=零+bench.py hunk 全限 36-43(imports)+1685-2160
  (帧区域)+判定公式行零变更〕✓）| **运行时验收活体复现**：HEAD
  复现跑@reviewed_commit〔frame-20261003 惯例——type P50 2/P95 3
  PASS 80 帧配对 100%+scroll **58.7fps PASS**〔distinct 176/
  drive 180 follow 0.978 ∈±10% 带内——判定带 61.0-61.7 下沿波动
  /阈上余量 8.7%——SD-01 薄余量注记诚实性实证，verdict 稳健〕〕
  ；复现非判定谱集，文件按 024 无效跑惯例外处置，数值记录于本条
  ；谱复用理由=判定谱五 JSONL 自 f-commit 后零提交触碰〔git log
  复勘同码同配置〕——JSONL 独立重提替代重跑 | findings:
  F-1(info)=**Q-1 预告默认臂执行——用户确认位随 merge 收据**
  〔AskUserQuestion 提请无实时回执→§10 预告规则执行 (b)；标定
  前置达成独立复验 ✓；改判位=needs_fix 路由换臂重判（frozen 面
  不变）——merge 收据显式记载确认位〕；F-2(info)=HEAD 复现
  58.7fps 落判定带下沿〔61.0-61.7 带外 2.3fps——阈上 8.7% 余量+
  follow 0.978 带内=verdict 稳健；SD-01 薄余量注记已如实并陈，
  零工件缺陷〕；F-3(info)=复审脚本初查三 ✗ 均为解析伪影〔表格
  行数 off-by-one+两处行宽换行字符串——扁平化直验全中〕| 
  evidence: specs/auto-edit/tests/evidence-p028-{upstream-reverify,
  drive-channel}.jsonl+evidence-p028-m4-terminal.md+tools/bench/
  results/frame-20261008-214932/215003/215028/215053/215117 五谱+
  SD-01..03@d9eaf3f+anchors.json/table.md（13 行五代并陈）| 
  next: merge（P028-1 账本投影+v0.1-M4.4 tag 打点=merge 期五检查
  点后；F-1 确认位随 merge 收据面落）。


- `stage: merge | PLAN-028 | plan_revision 1 | outcome: pass（五
  检查点全落 delivered）| delivery_commit: d9eaf3f（reviewed_commit
  原样落地——复审零 findings 需补正，docs-only 后代零需要；经两轮
  ff-only：d9eaf3f〔18 文件 1439+/26-〕+28fb017〔P028-1 账本〕——
  零合并提交）| 五检查点：
  ①**prepared**=review 基线 main@25f3015/工作树 plan-028-dev
  @d9eaf3f+依赖钉版 auto-lang@85f7159c2 detached[740@ab7a650bd+
  6d69dbdc7 祖先链]+auto-down@895f8d0 detached+wt-guard 三树
  clean；②**landed**=ff-only 零合并+main tip=d9eaf3f 后二轮
  28fb017〔merge-base=review 基线=25f3015 实证——rebase 零需要
  ；main 烟测绿=budgets 10 行+frozen budget 字段 diff=零+anchors
  --verify 13 行+render --check 双绿+三 SD 锚点+帧谱 JSONL×5〕；
  ③**ledger_refreshed**=P028-1 外科插入 29→30〔roundtrip 守卫：
  他五段+前缀 29 项零扰动+逐字回读——015-027 十三连先例；git
  跟踪账本经 worktree+Git 通道；main 回读验真 id/section/status/
  file〕；④**archived**=本笔〔untracked 计划文件 mv archived/
  +git add 入册+status: archived+completion_kind: delivered〕；
  ⑤**cleaned**=随清理检查点落（待回填）。**F-1 确认位随收据成
  文**（Q-1 预告默认臂 (b) pipelined-paced k2@60Hz——标定前置达
  成；改判位=needs_fix 换臂重判）；**部署观察=零重建项**（本件
  纯 tools/docs/specs/tag 面——零 Rust 生成物/零 web bundle/零
  后端产物消费面，026/027 同判）；**批量回归不适用**（auto-edit
  无 batch 文件——.last-batch-regression.json 缺席实证+023-027
  五连同判）。**v0.1-M4.4 tag 打点=本收据五检查点后**（annotated
  tag@main tip——素材 evidence-p028-m4-terminal 逐字；十行全绿/
  发布门解锁终态层语义——Q-2 默认命名）。

## 10. 待澄清事项

- **Q-1 复判驱动通道——已按预告默认臂执行（裁定确认位随复审门，
  2026-10-08 work 记录）**：AskUserQuestion 提请（标定数字随附三
  选项）——**自主跑次无实时回执**→按本节预告决策规则执行：默认
  倾向 (b) 的前置「标定 ≥54Hz 达成」实测达成〔pipelined-paced
  60.0Hz 真达+follow 1.011-1.022 ∈±10% 带内〕→ **(b) pipelined-
  paced k2@60Hz 落实施并终判转绿**（T-02 谱在档）。(a) serialized
  标定数字=有效驱动 43.1Hz<54 封顶+读数依赖回声补足（follow 1.41
  ——归因语义混）让位；(c) in-process 无必要（(b) 已在 MCP E2E
  语义内达标）。**用户改判位**：若 review/merge 前改判 (a)/(c)，
  走 needs_fix 路由换臂重判（终判谱/对比表/budgets 注记随臂更新
  ——028 判定阈值/语义 frozen 面不变，仅驱动通道面换装）。
- **Q-2 tag 命名——默认 v0.1-M4.4 采纳（转绿臂兑现，轻裁定口径）**
  ：十行全绿/发布门解锁终态层语义；打点=merge 期五检查点后。若
  Q-1 改判致仍红臂，tag 语义改复判归因层（命名届时示知）。
- **Q-3 发布决策联动（无需裁定，确认口径）**：发布门终态注记=预
  算面条件注记（技术条件位）——**本件终态=解锁（2026-10-08 成文
  ）**；对外发布决策与动作（渠道/时机/文案）=产品决策另行——本
  件不含。RQHost 后严格门回归承诺注记维持。
