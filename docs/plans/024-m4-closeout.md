---
plan_id: PLAN-024
status: executing
feature_name: M4-07 收口件（PLAN-725 帧两行重判转绿+open_1gb 裁定落账+NP++ 列条件补齐+M4 四面终检表+v0.1-M4 tag 打点）
author: [agent]
created_at: 2026-10-02T14:03:15+08:00
updated_at: 2026-10-02T14:09:15+08:00
plan_revision: 1
current_step: 0
total_steps: 6
supersedes_spec_components: []
new_spec_components:
  - docs/specs/modules/perf-measurement.md（SD-01：预算十行终态表+M4 判定收口节）
  - docs/specs/00-overview.md（SD-02：M4 第七件注记——M4 收口与 tag 记录位）
  - specs/auto-edit/README.md（SD-03：PLAN-024 口径+M4 终态表）
  - docs/strategy/002-north-star-v2.md（SD-04：条件——open_1gb 裁 (a) 时 §2.1 行降范围注记；裁 (b) 时改挂供料档登记节）
touched_goals:
  - 战略 §6 路线图 M4「速度王座与发布」四面验收收口 + §2.1 预算表终态（type_latency/scroll_fps 重判+open_1gb 落账）
  - v0.1-M4 里程碑 tag（v0.1-M1/M2/M3 惯例——打点=本件 merge 收据）
affects: [tools/bench/bench.py, tools/bench/budgets.json, tools/compare/anchors.py, tools/compare/render_table.py, tools/compare/compare.py, docs/strategy/002-north-star-v2.md, specs/auto-edit/README.md]
---

# [PLAN-024] M4-07 收口件（帧两行重判+裁定落账+终检+tag）

## 0. 变更摘要

M4「速度王座与发布」的**收口件**。前置全齐：PLAN-725（键入帧增量
更新管线——帧两行 FAIL 清偿本体）已 delivered 归档（SD-01 帧管线
增量契约+改前/改后阶梯谱双谱在档）；PLAN-023 已 delivered
（installer **armed PASS**〔50MB 独立渲染期过渡门+RQHost 后 20MB
回归承诺——用户重基线裁定落账〕+panic=unwind 保 catch_unwind 兜底
+供⑭ 插件化 want 登记）；021/022 已落 steady/warm/open/idle/diff
五行 PASS 与对比表 L2 列。本件四步收口：**①帧两行重判**（工具链
重建含 725→bench frame 档复跑——type_latency P50 110/P95 115ms
vs ≤16.7ms、scroll_fps 8.0fps vs ≥54 的转绿判定；725 分段优化
[单帧单建/载荷增量/脏域重建]效果的同机下游验证）→ **②open_1gb
裁定落账**（用户件——designs/002 材料+023 双复证在案；(a) 降范围
=战略行注记 or (b) 登记上游流式装载 want）→ **③NP++ 列条件补齐**
（已装→harness 补跑三指标；未装→pending 终态注记——tag 不阻塞
〔Q-3〕）→ **④M4 四面终检表+v0.1-M4 tag**（预算十行终态汇总+
四验收面逐项核销清单[含语法高亮首批核销注记]；**tag 打点=本件
merge 收据**——v0.1-M1/M2/M3 惯例同款 annotated tag）。**本件
delivered=M4 完全收口**。

## 1. 目标

- **G-1 帧两行重判（725 下游验证）**：master 重建（含 725 delivery
  ——`auto --version` 核哈希，021-023 纪律）→ bench frame 档复跑
  （022 驱动协议修正版[autoui_type 直达+cursor-follow 滚动]）——
  **type_latency ≤16.7ms（帧内口径 P95）+scroll_fps ≥面板×0.9**
  判定；N≥4 谱+725 改前谱对照（110ms/8fps→改后）。转绿=budgets
  两行 armed PASS+对比表滚动行刷新；**仍红**=新谱分段归因+回
  auto-lang 余题（Q-2 双态如实——tag 口径随裁）。
- **G-2 open_1gb 裁定落账（用户件——Q-1）**：两案执行——**(a)
  降范围**：战略 §2.1 行注记「1GB=远期流式域，512MB 拒绝位=独立
  渲染期形态」（013 非目标注记的正式化）+budgets 行终态注记；
  **(b) 登记供料**：上游流式装载 want 入 m4-perf-unblock-supply
  （工期在上游——M4 以 ledger-blocked-with-plan 注记收口）。
- **G-3 NP++ 列条件补齐**：已装→compare harness 补跑（打开
  100MB/小文件启动/diff 计时三指标——020 通道即用）→表格列转正；
  未装→pending 终态注记（**tag 不等待**——Q-3 默认口径：竞品列
  完整性=对比表后续补列域，非里程碑判定门）。
- **G-4 M4 四面终检表**：预算十行终态汇总表（八行判定+renderer
  n/a+open_1gb 裁定态）+四验收面逐项核销清单——①预算全绿（含
  过渡门口径注记）②installer/portable（armed PASS+RQHost 回归
  承诺指针）③公开对比表（我方列全实数+竞品态注记）④语法高亮
  首批（716 组A+022 语法面+供⑭ 插件化演进指针）——入 SD-01/02/03
  三册与 README 终态表。
- **G-5 v0.1-M4 tag**：打点=本件 merge 收据（五检查点落定后）
  ——annotated tag、message 含四面核销摘要（v0.1-M3 先例形态）。
- **G-6 规范+账本**：SD-01..03（+条件 SD-04）+P024-1。

### 非目标

- 供⑭ 语法插件化实施（RQHost 期触发件——want 在册）；RQHost/
  渲染拓扑（上游域——20MB 回归门随其落地另件）。
- open_1gb 实施（裁定 (b) 路径下=上游件）；NP++ 安装动作（用户
  面——本件只消费安装结果）。
- 帧两行仍红时的上游优化续作（auto-lang 域——本件只出归因谱与
  回执）；L1/L2 线开篇（M4 tag 后另议——战略 §6 顺序）。
- 对外发布/宣传动作（tag=里程碑标记非发布——023 Q-2 裁定口径：
  对外发布前必须全绿含 20MB 回归门）。

## 2. 架构方案

分层落点（2026-10-02 实勘，auto-edit main@957686f + auto-lang
master@b385534d7）：

| 面 | 现状 | 本期形态 | 依据 |
|---|---|---|---|
| 帧两行 | armed FAIL 首基线（022：110/115ms、8.0fps） | 725 工具链复跑重判——转绿 PASS 预期（725 分段优化+阶梯谱改前/改后双谱在档） | 725 SD-01；022 判定谱 |
| open_1gb | 拒绝位双复证（023 T-04 旁证）+designs/002 材料在案 | 用户裁定落账（a/b 两路执行形） | 021 §10 Q-1 遗留+023 复证 |
| installer/idle | armed PASS（50MB/150MB 过渡门——023 重基线裁定+战略追记） | 终检表收录（回归承诺指针——20MB/10MB 随 RQHost） | 023 bda49de/3e505da |
| 对比表 | 我方列全实数（滚动 8.0fps FAIL 行）+NP++ 列缺 | 滚动行重判刷新+NP++ 条件补齐 | 020/022 通道 |
| tag | v0.1-M1/M2/M3 在册（收口件 merge 收据打点惯例） | v0.1-M4=本件 merge 收据 | git tag 实锚 |
| auto-lang | 725 归档+726 归档（吞吐治理批）+727 稿（HTTP 域） | 无依赖动作（725 谱引用即止） | git log 实勘 |

**关键设计约束（frozen）**：
① **重判不冒领**——帧两行判定=022 判定口径原样（帧内 P95/面板×
0.9——口径变更即作弊）；725 改前谱=对照基线不删。② open_1gb
两路均**落账即收口**（(a) 注记/(b) ledger-blocked-with-plan——
不以「已登记」冒充「已达标」）。③ tag 打点=merge 收据位（五检查
点完备后）——**tag 动作在 merge 阶段执行**，本件 work 面只备
message 素材（四面核销摘要）。④ NP++ 缺席不阻 tag（Q-3 默认——
对比表列完整性≠里程碑判定门）。⑤ 帧两行仍红=双态如实（Q-2——
归因回执+tag 口径随用户裁）。

## 3. 技术栈

bench/compare 工具族复跑（022 帧档+020 compare 通道）+工具链重建
纪律（021-023 三连先例）+战略/规范文档面。无 .at 源改动（纯
工具/文档/判定面——AC-06 路径断言）。

## 4. 需求分析与背景调查

**授权记录**：用户 2026-10-02 会话确认「计划 024 还没有起草」
（对上轮误报的更正）——本件按前议设计补立（M4 收口件——帧重判+
裁定落账+终检+tag）；起草授权=用户既定排期（上轮「要我现在就把
PLAN-024 起草出来」之议的延续）；执行/work 待用户另行启动。范围
=auto-edit 单仓（tools/docs/budgets/tag）；auto-lang 零改动。
**Q-1 open_1gb 裁定=用户件**（材料齐后请示）。无预算/自动续跑
授权。

**来源与版本**：

- 交接链：PLAN-725 归档件（帧两行清偿本体——五段成本链分段优化
  +SD-01 帧管线增量契约+阶梯谱双谱）；PLAN-023 归档件（installer
  armed PASS+重基线裁定链+冲突面表+供⑭）；PLAN-021/022（五行
  PASS+帧首判谱+对比表通道）。
- 判定谱系：type_latency/scroll_fps=armed FAIL 110/115ms、8.0fps
  （budgets 现读）→ 725 改后预期（其阶梯谱在档——本件同机下游
  验证）；steady 17.8/warm 2.6/open 865.8/idle 9.1/diff 635.0
  （023 T-04 五行复跑谱——终检表基）。
- open_1gb 材料：docs/designs/002-open-1gb-adjudication.md+023
  双复证（512MB/1GB 拒绝位=装载探测兜底链活体旁证）。
- tag 惯例：v0.1-M1（b497db7）/M2（ff892dc→ed8c107=014 收口件
  收据）/M3（f4e34c1=017 收口件收据）——annotated tag+里程碑
  收口件 merge 收据打点。
- auto-lang 现势（master@b385534d7）：725/726 归档、727 稿
  （HTTP file transfer 域）——本件无上游依赖动作。

## 5. 详细设计

### T-00 重判勘定

725 交付谱复核（改后阶梯谱数字——重判预期校准+分段归因对照表
预置）；工具链门（master 重建含 725——构建源核哈希）；022 帧档
驱动协议复核（autoui_type 直达+cursor-follow——判定口径原样
frozen ①）；NP++ 在位探测（决定 G-3 路径）。

### T-01 帧两行重判（G-1）

bench frame 档 N≥4 复跑（release 全链——022 判定形态）→判定
（≤16.7ms P95/≥面板×0.9）→转绿=budgets 两行 armed PASS+对比表
滚动行刷新（anchors/render+--check）；仍红=新谱分段归因+上游
余题回执草案（Q-2 路由位）。谱 JSONL 入仓（改前对照列保留）。

### T-02 open_1gb 裁定落账（G-2——用户件 Q-1）

请示（designs/002+023 复证为材料）→依裁定执行：(a) 战略 §2.1
行注记+budgets 行终态（SD-04 落档）；(b) 供料档 §10 增补流式
装载 want+budgets 行 ledger-blocked-with-plan 注记。

### T-03 NP++ 列条件补齐（G-3）

已装：compare harness 补跑三指标→列转正（--check 复现）；未装：
pending 终态注记（README 对比表节+Q-3 口径注记）。

### T-04 M4 终检表+tag 素材（G-4/G-5）

四面核销清单+预算十行终态表（SD-01/02/03+README）；tag message
素材（四面摘要+关键数字）备档——**tag 动作=merge 阶段**（五检查
点后按惯例执行）。

### T-05 规范+账本（G-6）

SD-01..03（+条件 SD-04）落档+specs.json P024-1（015-023 外科
插入先例）。

### 规范增量

| delta_id | add/modify/retire | docs/specs/... target | before/after rule | rationale | acceptance IDs |
|---|---|---|---|---|---|
| SD-01 | modify | docs/specs/modules/perf-measurement.md | before：installer 判定终态节（023）+帧两行 armed FAIL 首判在册 / after：**预算十行终态表**（M4 收口快照——八行判定谱系+renderer n-a+open_1gb 裁定态+过渡门口径与 RQHost 回归指针）+M4 判定收口节 | M4 判定面真源快照 | AC-01/02/04 |
| SD-02 | modify | docs/specs/00-overview.md | before：M4 第六件注记（剩余=帧两行+open_1gb 裁定） / after：M4 第七件注记——**M4 收口**（四面核销清单+tag 记录位；L1/L2 后续指针） | 里程碑收口总览 | AC-04 |
| SD-03 | modify | specs/auto-edit/README.md | before：PLAN-023 口径 / after：PLAN-024 口径+M4 终态表（tag 位注记） | 运行矩阵/工具单源 | AC-04 |
| SD-04 | modify（条件） | docs/strategy/002-north-star-v2.md 或 docs/upstream/2026-09-m4-perf-unblock-supply.md | before：§2.1 open_1gb 行无裁定态 / after：裁 (a)=战略行降范围注记〔+变更记录行〕；裁 (b)=供料档 §10 流式装载 want 登记 | 用户裁定落账（Q-1 两路） | AC-02 |

## 6. 测试设计

- **帧重判谱**：N≥4 复跑+P50/P95 判定+725 改前对照列（110/8.0
  基线不删）；scroll_fps 面板率读回法复核（022 口径原样）。
- **对比表门**：--verify/--check 双绿（滚动行刷新+NP++ 条件态）；
  NP++ 补跑形=三指标 N=4 谱+版本钉版（020 三要素）。
- **终检表核验**：十行终态逐行与 budgets/判定谱对账（grep 锚——
  每行数字溯源到 JSONL）；四面清单逐项核销注记（语法高亮首批=
  716+022 链指）。
- **tag 素材校验**：message 素材与终检表一致（数字逐字对照）；
  tag 动作留 merge 阶段实录（§9 收据位）。
- **范围断言**：.at 源零 diff+auto-lang 主树零改动。

## 7. 验收标准

- **AC-01 帧两行重判**：判定谱在档——转绿=budgets 两行 armed
  PASS+对比表滚动行刷新；仍红=分段归因+上游回执草案（双态如实
  ——Q-2 口径随裁）。验证：frame 档 JSONL+budgets 注记+--check。
- **AC-02 open_1gb 落账**：裁定回执在录+两路之一执行形落档
  （SD-04）。验证：战略/供料档增改在档+budgets 行终态。
- **AC-03 NP++ 列**：已装=三指标谱+列转正；未装=pending 终态注记
  +Q-3 口径注记。验证：compare 输出+README 节。
- **AC-04 M4 终检表**：十行终态+四面核销清单在档（三册+README
  ——数字逐行溯源）。验证：grep 锚+对账表。
- **AC-05 tag 素材**：v0.1-M4 message 素材备档（与终检表一致）
  ——tag 动作=merge 阶段（收据实录位预留）。验证：素材文件+
  §9 预留位。
- **AC-06 规范+账本+范围**：SD 落档+P024-1 回读 True+零越界断言。
  验证：文件在档+账本断言+双仓 porcelain。

## 8. 执行步骤

| # | 任务 | 依赖 | 落点（实勘锚） | 产出/意图 | AC | 验证（命令/预期） |
|---|---|---|---|---|---|---|
| 0 | T-00 重判勘定 | — | 本件 §5 T-00 节 | 预期校准+协议复核+NP++ 探测 | AC-01/03 | [ ] 勘定记录在档 |
| 1 | T-01 帧两行重判 | T-00 | bench frame 档+budgets+compare | 转绿判定（或归因回执） | AC-01 | [ ] 谱+判定+--check 绿 |
| 2 | T-02 open_1gb 落账 | — | §10 Q-1 请示+SD-04 | 裁定两路执行 | AC-02 | [ ] 回执+落档在案 |
| 3 | T-03 NP++ 列 | T-00 | compare harness（条件） | 列转正或终态注记 | AC-03 | [ ] 输出在档 |
| 4 | T-04 终检表+tag 素材 | T-01..03 | SD-01..03+README+素材档 | M4 收口快照 | AC-04/05 | [ ] 十行对账+素材一致 |
| 5 | T-05 规范+账本 | 全 | SD 落档+specs.json | 收口落账 | AC-06 | [ ] P024-1 True+范围断言 |

## 9. 复审记录

- 2026-10-02 起草 handoff：`stage: new`，PLAN-024，plan_revision 1。
  `outcome: pass`（起草完备：四步收口各有判定谱/材料/通道在位
  [725 阶梯谱/designs-002/020 compare/023 五行谱]；重判口径 frozen
  防冒领；open_1gb 两路均落账即收口不虚标；tag 打点=merge 收据
  惯例+素材先行；NP++ 缺席不阻 tag 的默认口径成文；帧两行仍红的
  双态处置预留；路径/符号经 auto-edit@957686f 与 auto-lang@
  b385534d7 双仓实勘锚定；授权=补立起草[用户更正指令在录]，执行
  待用户启动——Q-1 裁定为用户件）。`next: work`。

## 10. 待澄清事项

- **Q-1 open_1gb 裁定（用户件——T-02 请示）**：(a) 降范围〔战略
  行注记——512MB 拒绝位=独立渲染期形态，1GB=远期流式域〕或 (b)
  登记上游供料〔流式装载 want——M4 以 ledger-blocked-with-plan
  收口〕。材料=designs/002+023 双复证。默认无预裁定——请示后执行。
- **Q-2 帧两行仍红处置（条件活——仅 T-01 复跑不达时）**：默认=
  新谱分段归因+回 auto-lang 余题（tag 口径随裁：等清偿 or 携注记
  打——023 Q-2 裁定先例[里程碑标记≠发布]可援引）；725 阶梯谱若
  预示优化幅度不足，T-00 即预警。
- **Q-3 NP++ 缺席时 tag 口径（确认默认）**：默认=tag 不等待 NP++
  （对比表列完整性=后续补列域非里程碑判定门——竞品三家实数已足
  表位成立）；若用户坚持四家齐再 tag，执行期示知——T-03 改阻塞
  位。
