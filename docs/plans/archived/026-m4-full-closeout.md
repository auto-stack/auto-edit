---
plan_id: PLAN-026
status: archived
completion_kind: delivered
feature_name: M4 完全体收口件（PLAN-731 消费——帧两行重判转绿+预算十行全绿快照+发布门解锁注记+v0.1-M4.2 tag 打点）
author: [agent]
created_at: 2026-10-03T00:23:01+08:00
updated_at: 2026-10-03T01:00:00+08:00
plan_revision: 1
current_step: 6
total_steps: 6
supersedes_spec_components: []
new_spec_components:
  - docs/specs/modules/perf-measurement.md（SD-01：预算十行全绿终态快照+发布门解锁注记）
  - docs/specs/00-overview.md（SD-02：M4 完全体注记——tag 记录位+余题清单终态）
  - specs/auto-edit/README.md（SD-03：PLAN-026 口径+终态表）
touched_goals:
  - 战略 §2.1 预算表 type_latency ≤1 帧/scroll_fps 满刷新率——731 消费重判（最后两行红）
  - 「预算未达标的功能不发布——性能是发布门槛（M4 生效）」——发布门解锁注记 + v0.1-M4.2/M4 完全体 tag
affects: [tools/bench/bench.py, tools/bench/budgets.json, tools/compare/anchors.py, tools/compare/render_table.py, specs/auto-edit/README.md]
---

# [PLAN-026] M4 完全体收口件（帧两行重判+十行全绿+tag）

## 0. 变更摘要

auto-lang **PLAN-731**（S5 帧尾段增量化，2026-10-02 delivered@
30bda6831——子段插桩/shaping 缓存+视口增量/layout 增量/组件缓存/
掉泵治理；R1 复审含基线谱全档+segsum 零回退实算+对照报告 JSONL
在案）的**下游消费件**——M4 完全体最后一环：**①帧两行重判**（
工具链重建含 731→bench frame 档复跑——**022 判定口径 frozen 原样**
[帧内 P95 ≤16.7ms/scroll ≥面板×0.9]——转绿预期[S5 三子段压降+
掉泵治理直对两行根因]；仍红=S5 子段谱归因回 upstream[双态如实]）
→ **②预算十行全绿快照**（8 行既有绿+两行新绿+renderer n/a 唯一
例外——**发布门解锁注记**：「预算未达标的功能不发布」战略原文
的兑现时点成文）→ **③v0.1-M4.2 tag**（命名 Q-1——M4 完全体标记
；打点=本件 merge 收据[惯例]；消息=十行终态+余题清单终态[供⑭/
RQHost 门/NP++ 全为条件件注记]）→ **④对比表滚动行终态**（022/
024/026 三代并陈刷新——024 先例口径）+上游谱带内复验。**本件
delivered=M4 名副其实的完全体**（管理收口[M4]+能力补全[M4.1]+
验收全绿[M4.2]三层齐）。

## 1. 目标

- **G-1 工具链门+上游谱复验**：master 重建（含 731 delivery
  30bda6831+733——`auto --version` 核哈希，021-025 五连纪律）；
  **731 回执谱同机复验**（S5 子段压降/泵率/键入谱三线带内对照
  ——超带=环境/回归疑点登记 upstream）。
- **G-2 帧两行重判（731 消费主面）**：bench frame 档 N≥4 复跑
  （release 全链——022/024 判定形态原样）；**判定口径 frozen**
  （帧内 P95 ≤16.7ms；scroll_fps ≥面板率×0.9——面板率读回法
  022 口径）；**转绿**=budgets 两行 armed PASS+判定谱注记（三代
  谱系：022 首判 110/8.0→024 重判 95-112/6.7-8.8→026 终判）；
  **仍红**=S5 子段谱对照归因（731 JSONL 为基）+回 upstream 余题
  回执（双态如实——tag 口径随 Q-2）。
- **G-3 十行全绿快照+发布门解锁**：budgets 十行终态表（8 行既有
  绿+两行新绿+renderer n/a）——SD-01 收口节；**发布门解锁注记**
  成文（战略 §2.1「预算未达标的功能不发布[发布门槛 M4 生效]」
  ——自本件起预算面不再阻塞对外发布决策；发布动作本身仍另行）。
- **G-4 对比表滚动行终态**：022/024/026 三代并陈（024 先例——
  FAIL 谱历史不删）+我方滚动行终态数字；--verify/--check 双绿。
- **G-5 v0.1-M4.2 tag**：素材备档（十行终态+三层收口径注记+
  余题清单终态[供⑭ 插件化/RQHost 回归门 20MB/10MB/NP++ 列——
  全条件件]）；**打点=本件 merge 收据**（v0.1-M1..M4.1 惯例）；
  命名 Q-1（默认 v0.1-M4.2）。
- **G-6 规范+账本**：SD-01..03+P026-1。

### 非目标

- **对外发布/宣传动作**（发布门解锁=预算面条件达成注记；发布
  决策与动作=另行——tag≠发布口径维持）。
- S5 续作（重判仍红时的上游循环——本件只出归因回执）；RQHost/
  供⑭/20MB-10MB 回归门（条件触发件——tag 消息注记位）；NP++ 列
  （用户面）。L1 开篇（下一里程碑——tag 后另议）。
- 判定口径变更（frozen——022 原样复跑；口径变=作弊）；725/731
  已落段任何重构；矩阵检查集变更（判绿口径承 025 的 141/0——
  本件零检查集改动，帧档=bench 域非矩阵域）。

## 2. 架构方案

分层落点（2026-10-03 实勘，auto-edit main@08685d6 + auto-lang
master@cb2da5fba）：

| 面 | 现状 | 本期形态 | 依据 |
|---|---|---|---|
| 帧两行 | armed FAIL（024 重判谱：P95 95-112ms/6.7-8.8fps） | 731 工具链重判——转绿预期（S5 压降+掉泵直对根因）；双态如实 | 731 交付谱（对照报告 JSONL 在案） |
| budgets | 8 行绿+renderer n/a+两行 FAIL（M4.1 态） | **十行全绿快照**（两行 armed PASS）+发布门解锁注记 | 024 SD-01 十行表延续 |
| 对比表 | 滚动行 022/024 并陈（024 先例） | 三代并陈+终态数字 | 024 口径 |
| tag | v0.1-M1..M4.1 在册 | **v0.1-M4.2**（打点=本件 merge 收据；命名 Q-1） | 收口件 merge 收据惯例 |
| 判定口径 | 022 帧内口径+面板×0.9 | **frozen 原样复跑**（零改动） | 防冒领纪律 |

**关键设计约束（frozen）**：
① **判定口径零改动**（022 原样——P95 分位/驱动协议/面板读回法；
口径变更=作弊）。② **双态如实**（转绿=armed PASS；仍红=归因回
执——不以放宽换绿；tag 语义随 Q-2）。③ 三代谱系历史不删（022
首判/024 重判 FAIL 谱保留对照——清偿证据链）。④ 工具链门三验
（构建源核哈希+组依赖钉版+PATH 坑纪律——五连先例）。⑤ 上游谱
带内复验为重判前置（超带先登记后判定——防环境噪声误判）。

## 3. 技术栈

bench/compare 工具族复跑（022 帧档+三代并陈机制）+工具链重建纪律
（master 含 731/733）+tag 素材备档。零 .at 源改动（纯判定/文档/
tag 面——AC-05 路径断言）。

## 4. 需求分析与背景调查

**授权记录**：用户 2026-10-03 会话指令「731 已经完毕并合并；请
继续本会话的工作」——授权=**起草本件**（会话既定路线的最后一环
：731 交付→帧两行重判收口→M4 完全体 tag——前议三段在录[731
handoff/上轮答问]）；执行/work 待用户另行启动。范围=auto-edit
单仓（tools/docs/budgets/tag）；auto-lang 零改动。Q-1 tag 命名=
轻裁定（默认 v0.1-M4.2）。无预算/自动续跑授权。

**来源与版本**：

- 交接链：PLAN-731 归档件（auto-lang delivered@30bda6831+cleaned@
  cd12f580b——五改+R1 复审[F-1 基线谱全档/F-2 segsum 零回退实算
  {1MB +3.8%/5KB -4.2% 同带,100KB -36% 改善向}/F-3 ce_text_runs
  实计]+对照报告/勘定/回执 JSONL 在案）。
- 谱系（三代）：022 首判（P50 110/P95 115ms、8.0fps——armed FAIL
  基线）→024 重判（P95 95-112ms、6.7-8.8fps——725 后 FAIL 维持
  +S5 归因）→本件终判（731 后——转绿预期）。
- 现状实勘（main@08685d6=v0.1-M4.1 tag 位）：budgets M4.1 态
  （8 绿+n/a+两 FAIL）；compare 三态列+滚动行并陈机制；bench
  frame 档（022 T-03 落位——驱动协议 autoui_type 直达+cursor-
  follow）；tag 惯例（v0.1-M1..M4.1——收口件 merge 收据打点）。
- 战略口径：§2.1「预算未达标的功能不发布——性能是发布门槛（M4
  生效）」——发布门解锁注记的原文依据；§5「全部为 L2 数字」。

## 5. 详细设计

### T-00 重判勘定

工具链门（master 重建含 731/733——构建源核哈希）；**上游谱带内
复验**（S5 子段/泵率/键入三线——731 JSONL 对照；超带=登记
upstream 后再判）；帧档驱动协议复核（022 口径原样——frozen ①
断言：bench.py 帧档零改动 diff）。

### T-01 帧两行重判（G-2）

bench frame 档 N≥4 复跑（release 全链）→判定（P95 ≤16.7ms/
≥面板×0.9）→转绿=budgets 两行 armed PASS+三代谱系注记；仍红=
S5 子段谱对照归因+upstream 回执草案（Q-2 路由位）。谱 JSONL
入仓。

### T-02 十行快照+发布门注记（G-3）

budgets 十行终态表更新+SD-01 收口节（发布门解锁注记——战略原文
兑现时点；renderer n/a 例外说明[上游 683 pending 维持]）。

### T-03 对比表滚动行终态（G-4）

anchors/render 三代并陈刷新+--verify/--check 双绿。

### T-04 M4.2 tag 素材（G-5）

素材备档（十行终态+三层收口径[M4 管理收口/M4.1 能力补全/M4.2
验收全绿]+余题清单终态[全条件件]）；打点位注记（merge 阶段执行
——五检查点后，惯例）。

### T-05 规范+账本（G-6）

SD-01..03+P026-1（015-025 外科插入先例）+范围断言（零 .at diff）。

### 规范增量

| delta_id | add/modify/retire | docs/specs/... target | before/after rule | rationale | acceptance IDs |
|---|---|---|---|---|---|
| SD-01 | modify | docs/specs/modules/perf-measurement.md | before：M4 判定收口节（十行表——两行 FAIL+S5 归因在案，024 态） / after：**十行全绿终态快照**（三代帧谱系+两行转绿判定谱）+**发布门解锁注记**（战略 §2.1 发布门槛条款兑现时点——发布动作另行） | 预算面终态真源 | AC-02/03 |
| SD-02 | modify | docs/specs/00-overview.md | before：M4 后续件注记（open_1gb 收口——025 态；余题含 S5） / after：M4 完全体注记（三层收口径+tag 记录位+余题清单终态[供⑭/RQHost 门/NP++ 全条件件]；L1 开篇指针） | 里程碑三层齐的总览 | AC-05 |
| SD-03 | modify | specs/auto-edit/README.md | before：PLAN-025 口径 / after：PLAN-026 口径+终态表（十行+三代滚动行+tag 位） | 运行矩阵/工具单源 | AC-04/05 |

## 6. 测试设计

- **帧重判谱**：N≥4 复跑+P50/P95 判定+三代对照列（022/024 谱不
  删）；scroll 面板率读回复核（022 口径）。
- **口径 frozen 断言**：bench.py 帧档 diff=零（复跑不改判定面
  ——grep/路径断言）。
- **上游谱复验**：三线带内对照表（超带=upstream 登记件随附）。
- **budgets/对比表门**：断言面一致+--verify/--check 双绿+三代
  并陈渲染断言。
- **tag 素材校验**：与 SD-01 终态逐字对账。
- **范围断言**：零 .at diff+auto-lang 主树零改动+检查集零变更
  （判绿口径承 025）。

## 7. 验收标准

- **AC-01 工具链+上游复验**：核哈希在录+三线带内对照表在档。
  验证：复验记录。
- **AC-02 帧两行重判**：判定谱 N≥4 在档——转绿=两行 armed PASS
  （三代谱系注记）；仍红=归因回执（双态如实——Q-2 口径随裁）。
  验证：谱 JSONL+budgets。
- **AC-03 十行快照+发布门**：终态表+解锁注记成文（renderer n/a
  例外说明）。验证：SD-01+budgets。
- **AC-04 对比表终态**：三代并陈+终态数字+双绿门。验证：render
  输出+--check。
- **AC-05 tag 素材+规范+账本**：素材与终态一致+SD-01..03 落档+
  P026-1 回读 True+零越界断言。验证：素材档+账本+路径断言。

## 8. 执行步骤

| # | 任务 | 依赖 | 落点（实勘锚） | 产出/意图 | AC | 验证（命令/预期） |
|---|---|---|---|---|---|---|
| 0 | T-00 重判勘定 | — | 本件 §5 T-00 节 | 工具链门+复验+口径断言 | AC-01 | [x] 四门全绿（工具链门=组三树 edit-026〔auto-edit@plan-026-dev base 08685d6/auto-lang@cb2da5fba detached/auto-down@895f8d0 detached——autodown-core 组 sibling 解析 load-bearing 实勘 Cargo.toml:172〕release 重建 `auto --version`=**v0.4.2-2640-gcb2da5fba clean**+731@30bda6831/733@550895b68 祖先链 merge-base 双实证+bench check 绿〔2640≥1588〕；**731 上游谱带内复验**=组树 ladder.py 处方复跑三线全带内〔1mb s5 P50 0.37/0.35/0.33ms vs 回执 0.36/0.42/0.34+泵率 1.95/0.41/2.14 同带——环境噪声排除重判放行，复验谱 evidence-p026-upstream-reverify.jsonl；100kb/typenl 相位 MCP 中途拒连瞬态异常如实注记〕；**帧档 frozen 断言**=stage_frame 区域〔_FRAME_MCP_PORT_BASE→main〕f183f53→08685d6 逐字节全等〔023/025 改动均在 installer/open 区域〕+面板读回 60Hz） |
| 1 | T-01 帧两行重判 | T-00 | bench frame 档+budgets | 终判（转绿/归因） | AC-02 | [x] 终判 FAIL 维持+归因换代回执（**双态如实——Q-2 默认臂触发**：N=4 全有效谱 P50 71-78ms/**P95 156-160ms**>16.7+scroll 8.1-9.5fps<54——三代谱系 022 110/115→024 95-112/6.7-8.8→026 156-160/8.1-9.5；**归因换代**〔731 插桩下沉后 S5 子段下游首度可见〕=①S5 增量化生效实证〔024 段外 ~108ms 消散→s5 三子段 0.1-0.2ms+突发重建退位单帧单建 segsum ~2ms 帧工作面全绿余量 ~8×〕②唯一慢帧=第 0 帧首建 s4_element 91-92ms〔024 同款一次形非判定域〕③红面换代=**帧泵呈现交付通道**〔__frame_pump 消费滞后/合并 paired ~11% vs 024 突发形 17-24%→fprobe_present 读回=泵消费时刻陈旧度非帧工作时长——判定通道语义随泵治理漂移；scroll 交付率 8-9.5fps 实测双读法 FAIL 稳健〕——**呈现交付节奏+判定通道语义适配=上游域余题第二段**回执 upstream；budgets 两行 026 代注记+谱 JSONL×4 入仓@worktree 0b74750；tag 语义降「重判收口」+发布门不解锁随 Q-2 落账） |
| 2 | T-02 十行快照 | T-01 | budgets+SD-01 | 全绿+发布门注记 | AC-03 | [x] as-is 态落账（**Q-2 改制如实**：十行终态快照=8 PASS+2 FAIL+renderer n/a——十行全绿未达；SD-01 收口节=PLAN-026 终判节〔终判谱 N=4+归因换代+十行 026 态表+发布门**不解锁**注记——战略 §2.1 如实执行+复判前置=上游两余题清偿〕@worktree 185f206） |
| 3 | T-03 对比表终态 | T-01 | compare 双件+README | 三代并陈 | AC-04 | [x] 三代并陈双绿（022 8.0/024 7.0/026 9.5fps 三行 FAIL 谱历史不删〔024 先例〕——anchors.py SRC_FRAME_026 行+render_table 三代脚注；**anchors --verify 11 行全等+render --check 复现一致双绿**@worktree 185f206） |
| 4 | T-04 tag 素材 | T-01..03 | 素材档 | M4.2 备档 | AC-05 | [x] 素材对账一致（evidence-p026-m4-closeout=十行 026 态表+三层收口径〔M4 024/M4.1 025/M4.2 026 重判收口〕+余题清单终态〔泵交付节奏+通道语义适配=上游域第二段+供⑭/RQHost 门条件件+NP++ 用户面〕+v0.1-M4.2 tag 素材全文〔Q-1 默认命名——语义降「重判收口」+发布门不解锁注记〕+731 消费回执——与 SD-01 十行表逐字对账@worktree 185f206） |
| 5 | T-05 规范+账本 | 全 | SD-01..03+P026-1 | 收口落账 | AC-05 | [x] SD 全落档+范围断言绿（SD-01..03 全落@worktree〔perf-measurement 终判节/00-overview M4 完全体收口件注记/README 026 口径〕+范围断言：**零 .at diff**+auto-lang/auto-down 组树双净+检查集零变更〔bench.py 零 diff=frozen 断言实际保持〕；P026-1=merge 期项 015-025 先例——work 不碰活账本） |

## 9. 复审记录

- 2026-10-03 起草 handoff：`stage: new`，PLAN-026，plan_revision 1。
  `outcome: pass`（起草完备：731 消费面承接清晰[重判=唯一主面+
  上游复验前置]；口径 frozen 零改动+双态如实+三代谱系不删三纪律
  防冒领；十行全绿快照与发布门解锁注记有战略原文依据；tag 打点
  惯例+素材先行；零 .at/零检查集变更=纯判定面；路径/符号经
  auto-edit@08685d6 与 auto-lang@cb2da5fba 双仓实勘锚定；授权=
  起草[用户「继续本会话的工作」指令+三段前议在录]，执行待用户
  启动——Q-1 tag 命名默认 v0.1-M4.2）。`next: work`。
- `stage: work | PLAN-026 | plan_revision 1 | outcome: pass（执行
  完备——判定结果=Q-2 默认臂如实红，非执行缺陷；双态如实纪律
  全程维持）| code_commit: worktree plan-026-dev@185f206（base
  08685d6；两提交=0b74750 T-00+T-01 终判+归因回执/185f206
  T-02..T-05 十行态+三代并陈+素材+规范账本）| task_ids:
  T-00..T-05 全 delivered | evidence: ①工具链门=v0.4.2-2640-
  gcb2da5fba release 组树构建 clean〔auto-lang@cb2da5fba detached
  ——731@30bda6831+733@550895b68 祖先链 merge-base 双实证；
  auto-down@895f8d0 detached——autodown-core 组 sibling 解析
  load-bearing 实勘 Cargo.toml:172〕+bench check 绿；②**731 上游
  谱带内复验三线全带内**〔组树 ladder.py 处方复跑：1mb s5 P50
  0.37/0.35/0.33ms vs 回执 0.36/0.42/0.34+泵率同带——环境噪声
  排除重判放行；evidence-p026-upstream-reverify.jsonl；100kb/
  typenl 相位瞬态异常如实注记〕；③帧档 frozen 断言=stage_frame
  区域 f183f53→08685d6 逐字节全等〔bench.py 全程零 diff〕；④终判
  N=4 全有效谱=type P50 71-78/P95 156-160ms>16.7+scroll
  8.1-9.5fps<54 → **FAIL 维持（026 代——三代谱系 022/024/026 不
  删）**；**归因换代**〔731 插桩下沉后 S5 子段下游首度可见〕=
  S5 增量化生效实证〔024 段外 ~108ms 消散→s5 三子段 0.1-0.2ms+
  突发重建退位单帧单建 segsum ~2ms——帧工作面全绿余量 ~8×；024
  慢帧归因面零复现；唯一慢帧=第 0 帧首建 s4_element 91-92ms 一
  次形非判定域〕+红面换代=**帧泵呈现交付通道**〔__frame_pump 消
  费滞后/合并 paired ~11% vs 024 突发形 17-24%→fprobe_present 读
  回=泵消费时刻陈旧度非帧工作时长——判定通道语义随泵治理漂移；
  scroll 交付率 8-9.5fps 实测双读法 FAIL 稳健〕——**呈现交付节奏
  +判定通道语义适配=上游域余题第二段**（消费回执 evidence-p026-
  frame-rejudge §结论与回执）；⑤budgets 两行 026 代注记+十行终态
  as-is 快照（8 PASS+2 FAIL+renderer n/a）+**发布门不解锁注记**
  〔Q-2 默认臂——战略 §2.1 如实执行；复判前置=上游两余题清偿〕+
  SD-01 终判节+对比表滚动行三代并陈〔--verify 11 行+--check 双绿
  〕+tag 素材档〔evidence-p026-m4-closeout——v0.1-M4.2 语义降
  「重判收口」，Q-1 默认命名，与十行表逐字对账〕+SD-02/SD-03；
  ⑥范围断言：零 .at diff+auto-lang/auto-down 组树双净+检查集零
  变更〔本件纯判定/文档/tag 面〕| blockers: 无 | next: review
  （P026-1 账本投影=merge 期项——015-025 先例彩排位随 review/
  merge；v0.1-M4.2 tag 打点=merge 期五检查点后）。`execution_done`
  （六检查点全勾、验收映射全落：AC-01 四门证据/AC-02 终判谱+归因
  回执〔Q-2 口径——双态如实〕/AC-03 十行 as-is 态+不解锁注记/
  AC-04 三代并陈+双绿门/AC-05 素材对账+SD-01..03〔P026-1=merge
  期〕；worktree 清洁态 0 dirty@185f206；**授权适配注记**：T-02
  「十行全绿快照」与「发布门解锁注记」以 Q-2 默认臂改制执行〔计划
  §10 预授权——十行全绿未达则 as-is 如实+不解锁〕，不属验收弱化
  ——转绿臂判据原样保留为复判件目标）。
- `stage: review | PLAN-026 | plan_revision 1 | outcome: pass |
  reviewed_commit: worktree plan-026-dev@185f206230076d31260c189f005502b45e839925
  （0 dirty）| base_commit: 08685d6 | dependency_revisions:
  auto-lang@cb2da5fba detached[731@30bda6831+733@550895b68 祖先链
  复审独立重验 ✓]+auto-down@895f8d0 detached | spec_inputs: 三 SD
  目标文件@185f206[frozen delta=本提交树：perf-measurement
  PLAN-026 终判节/00-overview M4 完全体收口件注记/README 026 口径]
  | acceptance_results: AC-01..05 **五项全 pass**（复审同会话限制
  如实声明——全部从工件独立重建不采信执行摘要：①AC-01 工具链
  v0.4.2-2640-gcb2da5fba 复验+祖先链 merge-base 重验+**带内对照
  独立重算**〔复验谱↔回执谱逐值：s5 P50 0.37/0.35/0.33 vs
  0.36/0.42/0.34+泵率 1.95/0.41/2.14 vs 1.46/0.41/1.69——带内判
  据显式化 |Δs5|≤0.1ms∧泵率 0.3×..3×〕+stage_frame 区域
  f183f53→HEAD 逐字节全等重跑✓②AC-02 四谱 JSONL 独立重提〔P95
  156-160>16.7∧fps<54 判定复算四跑全 FAIL 维持✓+focus_ok/
  valid≥10 有效性复核✓〕③AC-03 十行表↔budgets.json 十行交叉
  对账程序化全一致+发布门不解锁注记在档+renderer n/a 例外在表✓
  ④AC-04 --verify 11 行+--check 双绿复审独立重跑✓⑤AC-05 素材
  关键数字/语义十项 grep 对账+范围断言〔零 .at diff+组树双净+
  检查集零变更〕重跑✓+**P026-1 彩排 True**〔副本插入 27→28：
  他五段深等+前缀 27 项零扰动+回读 P026-1 三守卫——活账本零
  触碰〕）| findings: F-1(info)=ladder 复验 100kb/typenl 相位
  MCP 中途拒连一次〔evidence-p026-upstream-reverify 注记在档；
  1mb 门槛基面完整带内不受累+下游四跑同窗零复现——观察位非
  阻塞〕；F-2(info)=render fps 格「armed FAIL（首基线锚点）」
  措辞对 024/026 非首判行略欠精确〔024 既有渲染器行为——最小
  diff 纪律维持不改，记录在案〕；F-3(info)=frontmatter
  total_steps 起草值 7→执行期校正 6〔可执行任务实数——计数
  语义〕；F-4(info)=Q-2 改制执行经计划 §10 预授权核验〔十行
  as-is+不解锁=授权适配非范围缩减——转绿臂判据保留为复判件
  目标〕| evidence: 运行时证据复用理由=四谱 JSONL/ladder 复验
  谱/双绿门均执行于复审提交树内容〔185f206=0b74750 树+SD/素材
  /compare 产物；判定面代码/依赖零变化〕+工具链 2640 复审重验
  同版——静态面〔JSONL 重提/交叉对账/grep 对账/彩排/范围断言〕
  全部复审独立重跑 | next: merge（用户已授权全链——review 通过
  移交 auto-plan-merge；P026-1 正式落账+v0.1-M4.2 tag 打点随
  merge 五检查点）。
- `stage: merge | PLAN-026:r1 | outcome: pass（archived 已落——cleaned
  待清理检查点补记）| delivery_commit: 185f206〔ff-only 零合并 main
  tip=185f206——15 文件 597+/8-，base=main@08685d6 零 rebase 重写〕|
  canonical_spec_paths: docs/specs/modules/perf-measurement.md+
  docs/specs/00-overview.md+specs/auto-edit/README.md〔越界先例=024
  SD-03/025 SD-04 在档〕| ledger_targets: .autoos/specs.json reviews
  段 P026-1〔外科插入 27→28 四守卫——git 跟踪文件经 worktree+Git
  通道 commit fc6870e；main 回读 P026-1 present/28 items/schema OK〕|
  main 烟测: budgets 十行 026 纪元在录+anchors --verify 11 行+render
  --check 双绿+三 SD 锚点+帧谱 JSONL×4 在档 | 批量回归到期判定:
  不适用〔auto-edit 无 batch 文件——.last-batch-regression.json
  缺失+023/024/025 同判〕| archived: docs/plans/archived/
  026-m4-full-closeout.md〔status=archived+completion_kind=delivered〕|
  cleaned: ✓〔wt-guard 三树 fresh clean+三 worktree 注销〔auto-edit/
  auto-lang/auto-down 各归属主仓——注销前占用预检=零 auto.exe/
  auto-edit.exe 进程+三树零 reparse point〕+branch 删 plan-026-dev
  was fc6870e 全落祖先链+组目录 edit-026 清——.wt 无残留+三仓
  registry 零〕| 部署观察: 零重建项维持〔auto-edit=按需构建应用仓
  ——无常驻服务消费本仓代码；dist/portable 产物=发布期按需构建；
  组工具链=构建期依赖随计划重建，随组目录清理退场〕。**v0.1-M4.2
  tag=本收据打点（五检查点后——v0.1-M1..M4.1 惯例；素材=
  specs/auto-edit/tests/evidence-p026-m4-closeout.md 逐字对账；
  语义=重判收口〔Q-2〕非十行全绿——发布门不解锁如实注记）。**

## 10. 待澄清事项

- **Q-1 tag 命名（轻裁定，默认即可）**：默认 **v0.1-M4.2**（点
  版本序列延续——M4 管理收口/M4.1 能力补全/M4.2 验收全绿三层
  齐）；若用户偏好独立语义名（如 v0.1-M4-full），执行期示知——
  素材与打点位不变。**→ 素材已按默认 v0.1-M4.2 备档；语义随 Q-2
  降「重判收口」——打点=merge 期。**
- **Q-2 重判仍红处置（条件活——仅 T-01 不达时）**：默认=S5 子段
  谱归因+upstream 余题回执（tag 语义降为「重判收口」——十行
  全绿未达，发布门不解锁，如实注记）；731 对照 JSONL 为归因基。
  731 谱与 024→026 预期间带已核——预期低概率。
  **→ 2026-10-03 T-01 触发：默认臂已落账**（终判 FAIL 维持
  P95 156-160ms/8.1-9.5fps——归因换代：S5 增量化生效实证+红面
  =帧泵呈现交付节奏+判定通道语义适配，均上游域余题第二段；
  tag 语义降「重判收口」+发布门不解锁+十行快照=as-is 态如实）。
  **归因细节超出计划预期形态注记**：计划预期「仍红=S5 子段谱归
  因」——实际 S5 域已清偿（帧工作面绿），红面换代为帧泵呈现交付
  通道（上游 711 泵域）+判定通道语义适配——归因回执如实升级，
  upstream 余题清单随之更新（非 Q-2 预设的 S5 残差路径，处置语义
  同臂：回执 upstream+不解锁）。
- **Q-3 发布决策联动（无需裁定，确认口径）**：发布门解锁=预算面
  条件达成**注记**（技术条件位）；对外发布决策与动作（渠道/
  时机/文案）=产品决策另行——本件不含。**→ 发布门维持不解锁
  （本件落账）。**
