---
plan_id: PLAN-018
status: executing
feature_name: M4-01 性能预算门开篇——M4 解阻供料包落档（a2r 映射残余/帧时间戳插桩/大文件卡死回归/tree-sitter 首批）+预算全表重定+可达行首批锚点
author: [agent]
created_at: 2026-09-29T09:54:28+08:00
updated_at: 2026-09-29T09:54:28+08:00
plan_revision: 1
current_step: 0
total_steps: 7
supersedes_spec_components: []
new_spec_components:
  - docs/upstream/2026-09-m4-perf-unblock-supply.md（SD-01：M4 解阻供料包——四件，上游承接排队位）
  - docs/specs/modules/perf-measurement.md（SD-02：预算门 M4 语义+budgets 全表重定节）
  - docs/specs/00-overview.md（SD-03：M4 面开篇注记）
  - specs/auto-edit/README.md（SD-04：PLAN-018 口径——bench 扩档/锚点数字回填位）
touched_goals:
  - 战略 §6 路线图 M4「速度王座与发布」开篇（关键产出四件：预算全绿/installer/公开对比表/语法高亮首批——本件=解阻+盘点+可达行锚点）
  - 战略 §2.1 性能预算表（M4 生效「预算未达标不发布」——本件=门机制全表重定与首批数字）
affects: [tools/bench/bench.py, tools/bench/budgets.json, specs/auto-edit/README.md, docs/upstream/, docs/specs/modules/perf-measurement.md]
---

# [PLAN-018] M4-01 性能预算门开篇（解阻供料包+全表重定+可达行锚点）

## 0. 变更摘要

PLAN-017 交付后 **M3 本仓面收口**（overview M3 第五件注记尾行），按
路线图 §6 进入 **M4「速度王座与发布」**（关键产出：预算全绿/
installer/portable/公开对比表 NP++·Zed·BC/语法高亮首批 tree-sitter）。
M4 四产出**全部门控于上游解阻或用户裁定**——本件=M1「供料先行+本仓
并行」开篇模式复用：①**M4 解阻供料包落档**（四件：a2r 映射残余清偿
[L2 主形态解阻——read_text_range/code_editor_delta 缺席实证、
code_editor_edit 已映射实勘]/内核帧时间戳插桩[type_latency+scroll_fps
测量解锁]/大文件实例 UI 硬卡死回归清偿[043/552/700/702 期——T17
blocked 族+大文件交互面]/tree-sitter 首批[内核现 syntect/two-face
实勘、零 tree-sitter 依赖——最大件先勘定后供]）；②**budgets.json
全表重定**（validity 纠偏——open_100mb/open_1gb 解锁条件[内核 rope 化
+分块读]上游均已交付，"架构性不可达禁调优"文本过期；diff_100mb 已
达标对齐；a2r 缺口注记）；③**可达行首批锚点**（open_100mb/open_1gb
装载墙钟档+steady_start 启动链分解归因+warm_start/idle_mem 锚点——
release 工具链全链形态[016 diff_100mb 判定先例]；断言化待上游解阻后
切正主 L2 形态）。本件后 M4 主线=上游承接件逐件清偿→L2 断言全表→
Q3 裁定→installer→公开对比表。

## 1. 目标

- **G-1 M4 解阻供料包落档（四件，docs/upstream/）**：
  **供① a2r 映射残余清偿**——`File.read_text_range`/`code_editor_delta`
  无 trans/ui_gen a2r 臂（2026-09-29 实勘：ui_gen/rust.rs 零命中；
  code_editor_edit 已映射[L9716 实锚]）→ PLAN-007 装载链新内建缺口
  残余，L2 主形态（a2r release 直拉）跑不了现代装载链——perf README
  在册 blocked 项的清偿件；**供② 内核帧时间戳插桩**——type_latency
  （≤1 帧）与 scroll_fps（满刷新率）测量面（战略 §2.1 已登记上游小
  供料；.at 层无帧时间戳观测通道，PLAN-005 T-03 实勘）；**供③ 大文件
  实例 UI 硬卡死回归清偿**——2046→83c4621b5 窗（043/552/700/702 期
  业主，m1-supply §17 在册）——T17.2/17.3/17.8 blocked 族+大文件交互
  面（017 谱仍 4 败含此族）；**供④ tree-sitter 首批勘定+实施**——
  内核语法面现 syntect/two-face（Cargo.toml code-editor feature 实勘）
  、零 tree-sitter 依赖；§4.2 内核路线 tree-sitter 化（学 Zed 三课）
  ——语法高亮首批（常见 20 语言起步）的上游大件。
- **G-2 budgets.json 全表重定**：validity 文本纠偏（open_100mb/
  open_1gb：解锁条件已满足→「解锁待测」；renderer_cold_start：
  683 pending 维持；type_latency/scroll_fps：供② 排队注记；diff_
  100mb 达标谱对齐[016 修复轮 1906/1971ms 在档]）；tier 阶梯复核
  （steady_start=hard 语义[Q2 单 iced 补注九已裁定行]；M4 收口行
  [warm_start/idle_mem]的断言化路径注记）；五态断言面（stage_proxy
  budget_assert 行序）一致性回归。
- **G-3 open_100mb/open_1gb 解锁基线档**：bench 扩档——100MB 文本
  装载墙钟（≤1s 预算行**首次实测锚点**；大文件模式 50MB 阈值交互
  [013]：100MB 必经 big 态——装载墙钟与 big 态注记同档成文）+1GB 可
  打开档（512MB 拒绝位边界注记——013 超大拒绝 512MB 在册，1GB 行=
  战略 ledger 态记录）；生成式 fixture（013/016 先例不入库）；滚动
  不掉帧面=供② 解阻后（本件注记不冒领）。
- **G-4 steady_start 启动链分解归因**：阶段时间戳插桩面盘点（BENCH
  标记族——进程起/逻辑 init/首帧请求代理指标，PLAN-004/005 在册）
  → release 工具链形态下**分解数字表**+与 ≤80ms 预算差距归因（达标
  即绿注记；未达标=归因清单，瘦身实施=后续件——「预算未达标不发布」
  是 M4 发布门槛，本件先立门再逐行清偿）。
- **G-5 warm_start/idle_mem 锚点档**：warm_start（≤120ms——会话恢复
  20 tab 懒装载墙钟；bench_ws_loaded 标记[editor_store.at:442 实锚]
  扩档）+idle_mem（≤60MB——L0 空闲内存采样档；「记账不阻塞」语义
  维持，数字入 budgets 注记）。

### 非目标

- 上游四件的**实施**（auto-lang 侧承接计划——本件只落供料档+勘定
  证据；669 模式：上游走自己的 plan 流程）。
- installer/portable 件与 Q3 裁定（材料备齐[exe 现尺寸 37.8MB vs
  ≤15MB 差距表]待用户裁定——§10 Q-1；裁定后另立件）。
- 公开对比表（NP++/VSCode/Zed/BC 同机对比——L2 数字齐后件，依赖
  上游解阻+本件锚点升级）。
- type_latency/scroll_fps 断言（供② 解阻后）；renderer_cold_start
  （上游 683 重设计 pending——n/a 形态维持）。
- 预算瘦身的**实施**（本件=分解归因+清单；open_100mb/steady_start
  未达标行的瘦身=后续件——禁调优纪律仅在解锁条件已满足的行放开
  测量，优化实施仍走计划）。
- auto-lang 侧任何改动；specs/auto-edit 应用代码（本件=tools/docs
  面——bench 扩档是工具链非产品面；若锚点测量需 app 侧 BENCH 标记
  补点，按最小 diff 落并在 §8 任务内注明）。

## 2. 架构方案

分层落点（2026-09-29 实勘，auto-edit main@f4e34c1 + auto-lang
master@9b5a10e51）：

| 面 | 现状 | 本期形态 | 依据 |
|---|---|---|---|
| 供料包 | m1-supply（M1）+diff-engine-supply（M3）两包在册；M4 无 | **2026-09-m4-perf-unblock-supply.md 四件落档**（证据基=本件 T-00 勘定；回执方式同前两包——上游承接后下游零/最小改动复验） | M1「供料包立即发、本仓并行干别的」成功模式（战略补注三(c)）；669 模式 |
| budgets.json | 十行三态（hard 1/ledger 8/blocked 于 validity 文本）；open_100mb/open_1gb 行 validity=「rope 前架构性不可达」（**文本过期**——rope 单写者[673]+分块读[687]上游已交付）；diff_100mb 已含达标谱 | 全表重定：过期 validity 纠偏+解锁注记+供料排队注记+M4 断言化路径；bench stage_proxy budget_assert 五态行序一致性回归 | budgets.json:27-41 实勘；stage_assert mode 行序逻辑（bench.py:794-820） |
| open_100mb 档 | stage_bigfile 既有（013：mode on/off 尺寸杠杆代理对照）；无 100MB 装载墙钟档 | **stage 扩档**：100MB 生成式文本装载墙钟（BENCH 标记读点）+big 态注记+1GB 可打开档（512MB 拒绝位边界）；release 工具链全链形态 | 013 大文件模式；016 release 全链判定先例；stage_bigfile（bench.py:1030） |
| steady_start 分解 | 阶段时间戳代理指标在册（PLAN-004/005：进程起/init/首帧请求）；无 ≤80ms 对表归因 | 分解数字表+差距归因（达标绿注记/未达标清单化）；BENCH 标记族盘点（缺口=最小补点） | 战略 §5 代理指标节；budgets steady_start 行（Q2 单 iced 语义） |
| warm_start/idle_mem | bench_ws_loaded 标记在册（editor_store.at:442）；idle_mem L0 采样未成档 | 两锚点档（20tab 恢复墙钟+空闲内存采样）→budgets 注记回填 | budgets warm_start/idle_mem 行 |
| 上游四阻塞 | 分散在册（perf README blocked 表/m1-supply §17/战略 §2.1 unlock 列） | 供料包四件归口集中（证据+期望形态+验收建议——供料档格式复用前两包） | 各在册位实锚 |

**关键设计约束（frozen）**：
① **断言形态分层**——本件锚点=「记账不阻塞」（L0/release 全链形态
数字入档）；**硬判定维持 L2 唯一预算效力**（战略补注二）——016 的
release 全链判定先例仅限 diff（server 侧计算主导）；steady_start/
open_100mb 等交互面预算的**正式判定**待供① 解阻后的 a2r release
直拉形态，本件不冒领。② 供料档只登记不实施（auto-lang 零改动）。
③ 禁调优纪律的放开仅限解锁条件已满足的行（open_100mb/open_1gb——
解锁条件上游已交付）；未解阻行维持 ledger/blocked 语义。④ Q2 单
iced 裁定（补注九）语义不重开——steady_start 行文本已对齐，本件
只补数字。

## 3. 技术栈

python bench/perf 工具链（tools/ 既有三 stage 族扩展）+生成式 fixture
（013/016 先例：50/100MB/1GB 生成式临时构造不入库）+release 工具链
构建纪律（判据前核 `auto --version`；016 修复轮 v0.4.2-2183-
gc8f86ef92 形态先例——含 703/704）+docs/upstream 供料档格式。无
app 产品代码改动（bench 标记补点除外——最小 diff 注记制）。

## 4. 需求分析与背景调查

**授权记录**：用户 2026-09-29 会话指令「现在 M3 已经完成；按照之前
的设计，还有后续的 M4 吗？如果有，请继续规划下一个计划文件」——
确认 M4 存在（路线图 §6 在册）并授权=**起草本件**（M4 开篇件）；
执行/work 待用户另行启动。范围=auto-edit 单仓（tools/docs/upstream/
specs 文档面）；auto-lang 零改动。无预算/自动续跑授权。

**来源与版本**：

- 交接链：PLAN-017 归档件（delivered@f4e34c1）——M3 本仓面收口
  （overview M3 第五件注记）；执行谱 T17.2/17.3/17.8 blocked 族=
  大文件卡死回归仍在（供③ 依据）。
- 战略口径：§6 路线图 M4 行（预算全绿/installer/公开对比表/语法
  高亮首批 tree-sitter）；§2.1 预算表+「预算未达标的功能不发布——
  性能是发布门槛（M4 生效）」；§9 Q2（中期裁定=单 iced，补注九——
  budgets steady_start 行已对齐）/Q3（安装器，M4 前议——§10 Q-1
  材料位）。
- 现状实勘（auto-edit main@f4e34c1）：budgets.json 十行全读（过期
  validity 两行实锚）；bench.py stage 族（check:587/proxy:717/
  assert:794/diff:881/bigfile:1030——budget_assert 五态行序机制
  :805-820）；perf README（L2 主形态 blocked 表：a2r 映射缺口+RQ
  覆盖缺口+F-R1 三阻塞在册；exe 37.8MB 实锚）；editor_store.at:442
  bench_ws_loaded 标记。
- 上游实勘（auto-lang master@9b5a10e51）：ui_gen/rust.rs——
  code_editor_edit 臂在（L9716）、read_text_range/code_editor_delta
  零命中（缺口残余实证）；Cargo.toml——syntect 5/two-face 现役
  （code-editor feature）、零 tree-sitter 依赖；plan046（memo/keyed
  渲染域）在途无冲突。
- 历史关联：PLAN-004/005/006（perf/bench/预算断言体系+首份 L2 基线
  [rqhost 形态]）、007（单 iced 化+装载链缺口登记）、013（大文件
  模式+bigfile 档）、016（release 全链判定先例+diff_100mb 达标）、
  017（M3 收口+T17 blocked 谱）。

## 5. 详细设计

### T-00 M4 勘定决策件（有界调查，决策产物）

1. **L2 形态复核**：a2r 映射残余清单实勘（本仓 rust-workspace 生成
   物 grep+上游 rust.rs 对照——read_text_range/delta 缺席面定界，
   含 trans 面与 ui_gen 面两半）；RQ 覆盖缺口/F-R1 现状注记（不
   入本供料包——前者随 rqhost 退役档案化、后者 L 线）。
2. **BENCH 标记族盘点**：现有标记全列（装载/会话/ws_loaded/big
   等）→ steady_start 分解缺口清单（进程起/init/首帧——补点落位
   与最小 diff 注记）。
3. **open_100mb 可测形态勘定**：release 全链形态装载墙钟读点
   （BENCH 标记 vs MCP 轮询——016 计时卫生学[沉降窗]先例）；big
   态阈值交互确认（100MB>50MB 必经 big 态——档位语义）。
4. **Q2/Q3 材料汇总**：exe 尺寸差距表（37.8MB→≤15MB——a2r 原生化
   vs 执行打包两路径成本注记）+Q3 裁定问题清单（§10 Q-1 位）。

### T-01 供料包落档（G-1）

`docs/upstream/2026-09-m4-perf-unblock-supply.md`：四件（供①a2r
映射残余/供②帧时间戳插桩/供③大文件卡死回归/供④tree-sitter 首批）
——每件=诉求/动机/期望形态/验收形态建议/证据基（T-00 实勘）；优先
级建议（供① 最先[L2 主形态解阻——全预算行的判定前提]→供③[交互面
blocked 族]→供②[两行测量解锁]→供④[最大件，勘定+实施两段]）；回执
方式同前两包。**格式对齐 diff-engine-supply（标题/证据基/优先级/
回执节预留）**。

### T-02 budgets.json 全表重定（G-2）

十行逐行处置：纠偏两行（open_100mb/open_1gb validity→「解锁待测
——上游 rope[673]+分块读[687]已交付；本件 T-03 首批锚点」）+达标
对齐一行（diff_100mb——016 谱已在，格式统一）+排队注记三行
（type_latency/scroll_fps→供②；renderer_cold_start→683 pending
维持）+M4 收口路径注记两行（warm_start/idle_mem——断言化=供① 后
L2 形态）+steady_start（T-04 分解数字回填位）。stage_proxy/
stage_assert 五态行序回归（重定后 check 全绿——不破 014 的 l2 行序
机制）。

### T-03 open_100mb/open_1gb 基线档（G-3）

bench 扩档 `stage_open`（或并入 bigfile 档扩展——T-00③ 定）：100MB
生成式文本（重复行+散点差异——滚动/高亮真实负载形）装载墙钟×N 跑
谱+big 态注记同档；1GB 可打开档（512MB 拒绝位对照——「可打开」=
装载成功+首屏标记，墙钟 ledger 记录）；计时卫生（沉降窗——016
fixture writeback 教训复用）。产出=JSONL+budgets 注记回填（open_
100mb 行 unlock→「锚点在档，L2 正式判定待供①」）。

### T-04 steady_start 分解归因（G-4）

BENCH 标记补点（T-00② 清单的最小 diff——app 侧若需动，任务内注记
路径）→release 全链形态分解数字表（进程起→init→首帧请求→可输入
代理）×N 跑谱+≤80ms 对表（达标=绿注记入 budgets validity；未达标
=分项归因清单[瘦身候选+量级估计]——后续件排队位）。**不实施瘦身**
（frozen 约束④）。

### T-05 warm_start/idle_mem 锚点档（G-5）

warm_start：会话文件 20 tab 构造（生成式）→恢复墙钟（bench_ws_
loaded 标记读点+「不读盘」断言面[懒装载语义——010]）；idle_mem：
空窗口+20tab 恢复两形态空闲内存采样（L0 采样纪律——进程内存读点
形态 T-00③ 勘定）。数字→budgets 注记。

### T-06 规范增量+账本（G-1..5 收口）

perf-measurement.md 增「预算门 M4 语义与全表重定」节（SD-02——
断言形态分层[锚点 vs L2 正式判定]/四供料排队位/重定前后对照表）；
00-overview M4 面开篇注记（SD-03）；README PLAN-018 口径（SD-04——
bench 扩档用法+锚点数字回填位）；specs.json reviews 段 P018-1 投影
（015/016/017 外科插入先例）。

### 规范增量

| delta_id | add/modify/retire | docs/specs/... target | before/after rule | rationale | acceptance IDs |
|---|---|---|---|---|---|
| SD-01 | add | docs/upstream/2026-09-m4-perf-unblock-supply.md | before：M4 四产出门控分散在册（perf README blocked 表/m1-supply §17/战略 §2.1 unlock 列） / after：四件供料包归口（a2r 映射残余/帧插桩/卡死回归/tree-sitter——每件证据+期望形态+验收建议+优先级[①最先]；回执节预留） | 上游承接排队位；M1 供料先行模式复用 | AC-01 |
| SD-02 | modify | docs/specs/modules/perf-measurement.md | before：预算断言五态机制在册（004/005/014）；budgets validity 部分过期 / after：增「预算门 M4 语义与全表重定」节——断言形态分层（锚点记账 vs L2 正式判定[release 全链先例的适用边界=server 侧计算主导]/四供料排队/重定对照表/禁调优放开的行清单） | M4 门机制的规范锚 | AC-02/06 |
| SD-03 | modify | docs/specs/00-overview.md | before：面注记止于 M3 第五件（M3 本仓面收口） / after：M4 面开篇注记（供料包四件+全表重定+可达行锚点；M4 主线预告=承接清偿→L2 断言→Q3→installer→对比表） | 面进度总览承接 | AC-06 |
| SD-04 | modify | specs/auto-edit/README.md | before：PLAN-017 口径（137/≥125/0） / after：PLAN-018 口径（bench 扩档用法[stage_open/分解档/锚点档]+数字回填位+工具链形态注记） | 运行矩阵/工具单源 | AC-06 |

## 6. 测试设计

- **bench 回归**：stage_check（环境指纹+工具链门）/stage_proxy
  （budget_assert 五态行序——重定后全绿）/stage_assert（L0 缺省序
  与 l2 序两形回放）——**既有档零回退**为硬门。
- **新档验证**：stage_open（100MB×N 跑谱离散度[016 四跑谱先例——
  离散注记]+1GB 可打开+512MB 拒绝位对照）/steady 分解档（标记序
  单调+N 跑谱）/warm_start（20tab 恢复+懒装载不读盘断言）/idle_mem
  （两形态采样）。
- **供料档审校**：四件证据锚逐一可复现（上游 grep 命中/在册行号/
  blocked 谱引用）——审校即验（无运行时面）。
- **矩阵零扰动**：本件零 app 产品代码改动（bench 标记补点除外——
  若动则 desktop_mcp 抽查 T1/T15.1 主链）；判绿口径不变（承 017
  ≥125/0——本件不动矩阵检查集）。

## 7. 验收标准

- **AC-01 供料包四件落档**：文件在档+四件全（证据基可复现——上游
  实勘锚在册）+优先级与回执节预留。验证：文件在档+grep 锚+节结构
  对齐前两包。
- **AC-02 budgets 全表重定**：十行处置全落（纠偏 2/对齐 1/排队 3/
  收口路径 2/steady_start 数字位 1/Q2 已裁行 1）+五态断言面回归
  绿。验证：`python tools/bench/bench.py check`+`assert`（既有
  results 回放）双绿。
- **AC-03 open_100mb/1GB 锚点档**：100MB 装载墙钟 N 跑谱+big 态
  注记在档；1GB 可打开+512MB 拒绝位对照在档；budgets 回填。验证：
  新档 JSONL 在 results/+数字入 budgets validity。
- **AC-04 steady_start 分解归因**：分解数字表+≤80ms 对表结论（绿
  注记或归因清单）在档。验证：报告文件+bench 新档跑谱。
- **AC-05 warm_start/idle_mem 锚点**：20tab 恢复墙钟+不读盘断言+
  两形态内存采样数字在档。验证：同上。
- **AC-06 规范+账本**：SD-01..04 落档+specs.json P018-1 回读 True。
  验证：文件在档+账本断言+grep 锚。
- **AC-07 消费零越界**：auto-lang 主树零改动；app 产品代码零 diff
  （或仅 BENCH 标记最小 diff 且注记在 §8）。验证：双仓 porcelain+
  diff --stat 路径断言。

## 8. 执行步骤

| # | 任务 | 依赖 | 落点（实勘锚） | 产出/意图 | AC | 验证（命令/预期） |
|---|---|---|---|---|---|---|
| 0 | T-00 M4 勘定决策件 | — | 本件 §5 T-00 节+勘定报告（evidence-p018-*） | 四勘定案+供料证据基 | AC-01 | [ ] 勘定报告在档（L2 缺口定界/标记族盘点/读点形态/Q2Q3 材料） |
| 1 | T-01 供料包落档 | T-00 | docs/upstream/2026-09-m4-perf-unblock-supply.md | 四件+优先级+回执预留 | AC-01 | [ ] 文件在档+证据锚复现 |
| 2 | T-02 budgets 全表重定 | T-00 | tools/bench/budgets.json+bench.py 注记面 | 十行处置+五态回归 | AC-02 | [ ] check+assert 双绿 |
| 3 | T-03 open_100mb/1GB 档 | T-00 | bench.py stage 扩档+results/ | 锚点跑谱+回填 | AC-03 | [ ] 新档 JSONL+数字入 budgets |
| 4 | T-04 steady_start 分解 | T-00 | bench.py+（最小 diff）BENCH 标记补点 | 分解表+归因结论 | AC-04 | [ ] 报告在档（绿注记或清单） |
| 5 | T-05 warm/idle 锚点档 | T-00 | bench.py 扩档 | 两锚点数字 | AC-05 | [ ] JSONL+budgets 注记 |
| 6 | T-06 规范+账本 | T-01..05 | SD-01..04+specs.json | M4 开篇收口 | AC-06 | [ ] 文件在档+P018-1 回读 True |

## 9. 复审记录

- 2026-09-29 起草 handoff：`stage: new`，PLAN-018，plan_revision 1。
  `outcome: pass`（起草完备：M4 四产出门控结构实勘成立[a2r 缺口
  残余/帧插桩/卡死回归/tree-sitter 零依赖四锚]；供料先行+本仓并行
  的开篇模式有 M1 先例；budgets 过期 validity 两行纠偏有据；断言
  形态分层[锚点 vs L2 正式判定]防止冒领；路径/符号经
  auto-edit@f4e34c1 与 auto-lang@9b5a10e51 双仓实勘锚定；授权=起草
  ，执行待用户启动）。`next: work`。

## 10. 待澄清事项

- **Q-1 Q3 安装器与自动更新裁定（M4 前议——战略 §9 原文）**：本件
  T-00④ 备齐材料（exe 37.8MB→≤15MB 差距表+两路径[执行打包 vs a2r
  原生化]成本注记+winget 加分项口径）；**裁定=用户件**——裁定后
  installer 件立项，本件不含。若用户愿在执行前预裁定，请在启动 work
  时示知。
- **Q-2 open_100mb/steady_start 首批锚点未达标时的处置确认（无需
  裁定，确认口径）**：默认=记录差距+归因清单（瘦身实施=后续件按
  计划走——「预算未达标不发布」是 M4 发布门槛而非本件门）；若用户
  希望本件内即实施瘦身（扩任务），需追加授权——否则按默认。
- **Q-3 供④ tree-sitter 供料粒度（无需裁定，确认口径）**：默认=
  供料包内四件之末（勘定+实施两段式——先勘定件定界[语言集/管线
  选型/syntect 共存策略]，实施件上游另立）；若用户希望 tree-sitter
  独立成包（不与三解阻件混包），执行期供料档可拆——不影响本件
  AC。
