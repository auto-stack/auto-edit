---
plan_id: PLAN-019
status: execution_done
feature_name: M4-02 portable 单 exe 瘦身件（a2r 原生化路径——Q3 裁定 2026-09-29：治本瘦身+纯 portable，winget/自动更新不入）
author: [agent]
created_at: 2026-09-29T16:43:17+08:00
updated_at: 2026-09-29T19:45:00+08:00
plan_revision: 1
current_step: 6
total_steps: 6
supersedes_spec_components: []
new_spec_components:
  - docs/specs/modules/perf-measurement.md（SD-01：installer 行/portable 形态节+Q3 裁定记录）
  - docs/specs/00-overview.md（SD-02：M4 第二件注记）
  - specs/auto-edit/README.md（SD-03：PLAN-019 口径+portable 构建用法）
  - docs/strategy/002-north-star-v2.md（SD-04：§9 Q3 裁定注记——打包路径=a2r 原生化+纯 portable；变更记录行）
  - docs/upstream/2026-09-m4-perf-unblock-supply.md（SD-05：增补位——two-face 语法集子集 want，条件触发）
touched_goals:
  - 战略 §2.1 预算行「安装包 ≤15 MB 单 exe，无运行时依赖」——本件实施与判定
  - 战略 §9 Q3 裁定落地（2026-09-29 用户裁定：a2r 原生化瘦身路径+纯 portable 形态）
affects: [tools/perf/perf.py, tools/bench/budgets.json, tools/, specs/auto-edit/README.md]
---

# [PLAN-019] M4-02 portable 单 exe 瘦身件（a2r 原生化路径）

## 0. 变更摘要

PLAN-018 备齐 Q3 裁定材料（evidence-p018-survey.md §4——exe 37.8MB →
≤15MB 需 -60%+两路径成本注记）后的 **installer 件立项**，路径按用户
2026-09-29 裁定（本件 §4 授权记录）：**a2r 原生化瘦身**（治本——
保持「单 exe 无运行时依赖」战略语义；与供④ tree-sitter[syntect/
two-face 退役面]协同）+**纯 portable 形态**（winget/自动更新均不入
——战略 §9 加分项口径，后续件再议）。核心链：**体积精测**（构成
占比表——018 勘定注记「后续件实施时精测」的兑现）→ **portable
构建脚本**（regen→profile 补丁注入→release build→strip→尺寸断言
——生成物 Cargo.toml 无 [profile] 节且 gitignored[每次 regen 重生成]
，注入走 regen 后补丁通道=**纯下游零上游依赖**）→ **瘦身手段迭代**
（LTO/codegen-units/strip/opt-level 取舍+生成物 deps 面 feature
审计）→ **性能回归护栏**（018 锚点档复跑对照——瘦体积不得肥延迟，
M4 速度王座语义）→（条件触发）**two-face 子集上游 want 登记**。
分阶段达标已获裁定接受：首件未压进 15MB=剩余差距归因+want 排队，
第二段随上游清偿收口。

## 1. 目标

- **G-1 体积精测报告**：现势 exe（工具链 v2205+ 重测——37.8MB 为
  PLAN-007 era 旧锚）+**构成占比表**（iced/tiny-skia 渲染栈/two-face
  全量语法集/cosmic-text/std/其他——cargo-bloat 或 cargo tree 分解
  形态 T-00 定）+各手段收益预估表。018 勘定「体积构成勘定面（后续
  件实施时精测）」注记的兑现面。
- **G-2 portable 构建脚本**：`tools/` 新增（或 perf.py 扩段）
  `build_portable` 一键链——`auto build -r rust` regen→**[profile.
  release] 补丁注入**（追加节形——生成物 gitignored/regen 覆盖，补丁
  后置于 regen=幂等通道）→`cargo build --release`→strip→产物
  `dist/portable/auto-edit.exe`→**尺寸断言**（≤15MB 硬判定超限红+
  差距数字入报告；perf.py release 直调构建链先例复用）。
- **G-3 瘦身手段落位（本仓通道全量）**：profile 族（lto/codegen-
  units/strip/opt-level——**取舍受 G-4 护栏约束**，默认保守=保
  opt-level 3 先行 LTO+cgu+strip，收益不足再评估 "s"/"z" 与代价）+
  生成物 deps 面 feature 审计（iced features=["tokio","advanced"]
  子集可行性/ureq/tokio/axum default-features 面——经同一补丁通道
  改生成物 Cargo.toml deps 行，regen 幂等）。每手段一档收益数字
  （对照表在档）。
- **G-4 性能回归护栏**：018 锚点档复跑对照——**瘦身不得破预算行**
  （open_100mb ≤1s/warm 净段 ≤120ms/idle ≤60MB 达标维持；steady_
  start 现状 232.6ms 未达标——**不劣化**判据[±10% 运行方差容差注记
  ，018 离散谱先例]）。手段×锚点对照数据入报告——防「瘦体积肥
  延迟」（M4=速度王座，尺寸是发布门槛之一而非唯一）。
- **G-5 尺寸判定与分阶段收口**：达标→budgets installer 行 armed/
  达标注记+烟测（G-5）；未达标→剩余差距归因表+**two-face 语法集
  子集/lazy 装载 want** 登记 m4-perf-unblock-supply（内核 code-editor
  feature 粒度——`two_face::syntax::extra_no_newlines()` 全量内嵌
  实勘锚 highlight.rs:135；与供④ tree-sitter 退役面协同注记）+
  第二段收口件预告。
- **G-6 portable 烟测**：单 exe 干净目录直跑（无安装器/无解压/无
  运行时依赖）——BENCH 标记到位+最小 E2E（release 直拉既有形态+
  矩阵抽查 T1/T15.1 主链——全矩阵不强制[产物形态非源码变更]）。

### 非目标

- **winget 上架与自动更新**（用户裁定不入——战略 §9 加分项口径；
  后续件再议）。
- **执行打包路径**（自解压/压缩容器——用户裁定否决；「单 exe 无
  运行时依赖」语义维持原解）。
- 内核侧实施（two-face 子集 feature 粒度/生成器 profile 原生支持/
  供④ tree-sitter——**上游承接件**，本件只经补丁通道绕行+want
  登记；auto-lang 零改动）。
- steady_start 瘦身实施（VM boot 224.5ms 主导=工具链/形态面——
  018 归因清单在档，上游与 L2 形态件收口）。
- 公开对比表（L2 数字齐后件）；L2 断言全表（供① 解阻后件）。
- 应用产品代码改动（.at 源零 diff——本件=构建通道/工具/文档面；
  矩阵检查集零变更[判绿口径承 018]）。

## 2. 架构方案

分层落点（2026-09-29 实勘，auto-edit main@0698641）：

| 面 | 现状 | 本期形态 | 依据 |
|---|---|---|---|
| 生成物 profile | rust-workspace/Cargo.toml 无 [profile] 节（workspace 仅 members+deps 实读）；gitignored+regen 覆盖 | **regen 后补丁注入**（tools 脚本追加 [profile.release] 节——幂等：重复注入检测跳过；018 perf.py release 直调先例的通道延伸） | rust-workspace/Cargo.toml 实读；perf README（工具链默认 debug profile，release 由 perf.py 直调补足） |
| 体积构成 | 37.8MB 旧锚（PLAN-007 era build）；构成=勘定面未精测（018 §④ 注记） | 精测报告：现值重测+占比表+手段收益对照 | evidence-p018-survey.md §4 |
| deps feature 面 | iced {tokio,advanced}/ureq json/tokio rt/axum 默认面（生成物 deps 行实读） | feature 审计+子集化（同补丁通道改 deps 行）；收益数据驱动取舍 | rust-workspace/Cargo.toml 实读 |
| 性能护栏 | 018 锚点档在档（open 841ms/warm 1.3ms/idle 51.4MB/steady 232.6ms+离散谱） | 手段×锚点复跑对照表；预算行零回退门 | 018 budgets 注记+JSONL |
| two-face 粒度 | `extra_no_newlines()` 全量内嵌（highlight.rs:135 实锚）；无 feature 粒度 | 条件触发 want 登记（供料档增补——与供④ 协同注记） | auto-lang Cargo.toml:257+highlight.rs 实勘 |
| 判定面 | budgets installer 行=ledger「Q2 前无打包件」 | 路径已裁注记+达标 armed/未达标差距注记（数字回填） | budgets.json:75-81 |

**关键设计约束（frozen）**：
① **性能优先序**（战略 viewing-first+§2.1 前三行预算优先级最高的
口径传导）：手段取舍以 G-4 护栏为门——opt-level 降级类手段仅在
护栏全绿时采用，任一锚点回退超容差即回滚该手段并记录。② 补丁通道
幂等（regen→patch 可重复；patch 脚本对已注入态零重复写入）。③ 分
阶段语义如实成文（未达标≠失败——差距归因+want 排队即本件交付；
裁定已接受）。④ 上游零改动（生成器/内核不碰——want 只登记）。⑤
纯 portable 判定口径=**单 exe 直跑**（无安装壳/无解压步骤/无外部
运行时依赖——烟测即证）。

## 3. 技术栈

python tools 脚本（perf.py 先例形态）+cargo release profile 族
（lto/codegen-units/strip/opt-level/panic——取舍数据驱动）+cargo
tree/bloat 分解+018 bench 锚点档复跑（工具链纪律承 018：`auto
--version` 核；判据前重建组依赖钉版惯例）。无 .at 源改动。

## 4. 需求分析与背景调查

**授权记录**：用户 2026-09-29 会话指令「计划 018 已经完成；请规划
下一个计划」+**AskUserQuestion 裁定两问**（Q3 路径=「a2r 原生化瘦身
（推荐）」；周边 scope=「都不入，纯 portable（推荐）」）——授权=
**起草本件**（018 §10 Q-1「裁定后 installer 件立项」的兑现）；执行
/work 待用户另行启动。范围=auto-edit 单仓（tools/docs/budgets——
.at 源与矩阵检查集零改动）；auto-lang 零改动。无预算/自动续跑授权。

**来源与版本**：

- 交接链：PLAN-018 归档件（delivered@0698641）——Q3 裁定材料
  （evidence-p018-survey.md §4：37.8MB 实锚/差距表/两路径成本/体积
  构成勘定面）+锚点谱（open/steady/warm/idle JSONL）+budgets 全表
  重定态；M4 开篇注记「主线预告=承接清偿→L2 断言→Q3→installer→
  对比表」——Q3 位兑现。
- 战略口径：§2.1 installer 行（≤15MB 单 exe 无运行时依赖）；§9 Q2
  残余（打包路径）+Q3（安装器与自动更新——M4 前议）；本件裁定落地
  后两行注记收口（SD-04）。
- 现状实勘（auto-edit main@0698641）：rust-workspace/Cargo.toml
  实读（无 [profile] 节/deps 行全列/gitignored 确认）；perf README
  （release 直调构建链+产物路径 `specs/auto-edit/rust-workspace/
  target/release/auto-edit.exe`+exe 名=pac `exe_name`）；budgets.
  json installer 行；018 锚点 JSONL 在 results/。
- 上游实勘（auto-lang master@e2deb4f87）：two-face 0.4 optional 无
  粒度面（Cargo.toml:257）+`extra_no_newlines()` 全量内嵌
  （highlight.rs:135）——子集/lazy want 的定界证据；M4 供料包四件
  无承接（705/706/plan046-047 为他域——want 排队位维持）。
- 历史关联：PLAN-006（release 构建链+exe 产物路径锚）/007（单 iced
  化+37.8MB 锚）/018（Q3 材料+锚点档+预算门重定）。

## 5. 详细设计

### T-00 体积勘定决策件（有界调查，决策产物）

1. **现势精测**：v2205+ 工具链 regen→release build→现值（37.8MB
   旧锚对照）+**构成分解**（cargo-bloom/cargo tree --duplicates/
   symbols 面——工具可得性 T-00 内定，Windows 生态备选：cargo
   bloat/手粒度 .text/.rodata 分解）。
2. **手段收益预估与序**：LTO（thin/fat）、codegen-units=1、strip
   （symbols）、opt-level（3 保底/"s"/"z" 评估）、panic=abort（VM
   错误语义面——保守默认不启用，收益显著才评估）、deps feature
   子集（iced advanced 必要性/ureq json 面等）——按「预估收益/风险
   （G-4 护栏面）」排序成表。
3. **补丁通道定形**：注入脚本形态（追加节+幂等检测）、deps 行改写
   边界（仅 feature 子集面，不动版本/path）。

### T-01 portable 构建脚本（G-2）

`tools/` 落位（`build_portable.py` 或 perf.py 子命令——T-00③ 定）：
regen（auto build -r rust）→patch（profile+deps 子集）→cargo
build --release→strip→`dist/portable/auto-edit.exe`→**断言**（尺寸
≤15MB 硬判定；超限=exit 红+差距数字+JSONL 记录）+产物 sha256/版本
注记（portable 分发面最小账）。复用 perf.py 构建链与环境指纹纪律。

### T-02 瘦身手段迭代（G-3/G-4 联动）

按 T-00 序逐手段落位：每手段一档（注入→build→尺寸收益+**锚点档
复跑**[open/warm/idle 必跑，steady 抽档]）——对照表累计在档；护栏
红即回滚该手段并记录（frozen ①）。产出=手段×{尺寸,锚点} 终表+
最终 profile/deps 注入内容定稿。

### T-03 尺寸判定与分阶段收口（G-5）

达标：budgets installer 行 armed+数字；未达标：剩余差距归因表
（构成面剩余占比——预期大头=two-face 语法集+iced 栈）+want 登记
（m4-perf-unblock-supply 增补节：**two-face 语法集子集/lazy 装载
feature 粒度**——期望形态[子集 feature 或运行时按需装载]/验收建议
[尺寸差值+矩阵语法面回归]/与供④ 协同注记[tree-sitter 化后 syntect/
two-face 整体退役——want 生命周期可能止于供④]）+第二段收口件预告
（overview 注记）。

### T-04 portable 烟测（G-6）

干净目录直跑：`dist/portable/auto-edit.exe`（独立 env——APPDATA
隔离 018 纪律）→BENCH 标记到位（启动/装载链）+最小 E2E（open 文件
+diff 主链抽查——矩阵 T1/T15.1 抽档[产物形态非源码变更，全矩阵不
强制]）+「无运行时依赖」面（无 DLL 侧车/无解压残留——proc 探测）。

### T-05 规范增量+账本

perf-measurement.md 增「installer/portable 形态」节（SD-01——Q3
裁定记录[2026-09-29 用户：原生化+纯 portable]/构建通道[regen→patch
→release→strip]/判定口径[单 exe 直跑+≤15MB]/分阶段语义）；budgets
installer 行更新；00-overview M4 第二件注记（SD-02）；README
PLAN-019 口径+portable 构建用法（SD-03）；战略 §9 Q2 残余+Q3 裁定
注记（SD-04——变更记录行）；（条件触发）供料档增补（SD-05）。
specs.json reviews 段 P019-1 投影（015-018 外科插入先例）。

### 规范增量

| delta_id | add/modify/retire | docs/specs/... target | before/after rule | rationale | acceptance IDs |
|---|---|---|---|---|---|
| SD-01 | modify | docs/specs/modules/perf-measurement.md | before：installer 行=ledger「Q2 前无打包件」；无 portable 形态节 / after：增「installer/portable 形态」节——Q3 裁定记录[用户 2026-09-29：a2r 原生化+纯 portable，winget/自动更新后续件]/构建通道[regen→补丁注入→release→strip——生成物 gitignored 的幂等通道]/判定口径[单 exe 直跑+≤15MB+无运行时依赖]/分阶段达标语义 | 预算行实施面落账 | AC-03/05 |
| SD-02 | modify | docs/specs/00-overview.md | before：M4 开篇注记（主线预告含 Q3→installer 位） / after：M4 第二件注记（portable 瘦身件——路径裁定+手段表+判定结果[达标/差距归因+want 排队]；对比表=下一 blocker 位注记） | 面进度总览承接 | AC-06 |
| SD-03 | modify | specs/auto-edit/README.md | before：PLAN-018 口径 / after：PLAN-019 口径（portable 构建用法+产物位+数字回填位；判绿口径不变注记） | 运行矩阵/工具单源 | AC-06 |
| SD-04 | modify | docs/strategy/002-north-star-v2.md | before：§9 Q2/Q3 待裁定（打包路径开放/安装器 M4 前议） / after：裁定注记——打包路径=**a2r 原生化**（治本+语义维持）、形态=**纯 portable**（winget/自动更新后续件）；变更记录追加行 | 用户裁定落账（§9 Q3「M4 前议」的议决） | AC-06 |
| SD-05 | modify（条件） | docs/upstream/2026-09-m4-perf-unblock-supply.md | before：四件供料无 two-face 面 / after：增补 two-face 语法集子集/lazy 装载 want（T-03 未达标时触发——证据[构成占比]+期望形态+与供④ 协同[退役面重叠→want 生命周期注记]） | 分阶段收口的上游排队位 | AC-03/06 |

## 6. 测试设计

- **构建链验证**：build_portable 一键链 exit 0+产物在位+幂等复跑
  （regen→patch 重复执行零重复注入——diff 对照）；断言面（尺寸
  门：达标绿/超限红+差距数字）。
- **手段对照表**：每手段{尺寸收益,锚点复跑}数据行——护栏门（预算
  行零回退+steady ±10% 容差）逐手段判红绿；回滚记录在案。
- **烟测**：干净目录单 exe 直跑——BENCH 标记+最小 E2E（open+diff
  主链）+无依赖面探测（无 DLL 侧车/无解压残留/进程树单进程）。
- **矩阵零扰动**：.at 源零 diff（AC-07 路径断言）；判绿口径承 018
  （本件不动检查集——抽查档不计入）。
- **budgets 回归**：stage_check/assert 双绿（installer 行更新后五态
  面一致性——018 机制复用）。

## 7. 验收标准

- **AC-01 体积精测报告**：现值重测+构成占比表+手段预估序表在档。
  验证：报告文件（evidence-p019-*）+数字可复现（重跑对照）。
- **AC-02 portable 构建脚本**：一键链 exit 0+产物 dist/portable/
  auto-edit.exe+幂等复跑验证+断言门（≤15MB 绿/超限红+数字）。
  验证：脚本执行记录+产物在位。
- **AC-03 尺寸判定**：达标=budgets installer 行 armed+数字回填；
  未达标=差距归因表+two-face want 登记（SD-05 触发）+分阶段注记。
  验证：budgets 注记+（条件）供料档增补节在档。
- **AC-04 性能护栏**：手段×锚点对照表在档；终态手段集下 open ≤1s/
  warm 净段 ≤120ms/idle ≤60MB 维持+steady 不劣化（±10% 容差）。
  验证：锚点档 JSONL（终态手段集复跑谱）。
- **AC-05 portable 烟测**：单 exe 干净目录直跑绿（BENCH 标记+最小
  E2E+无依赖面探测）。验证：烟测记录+探测输出。
- **AC-06 规范+账本**：SD-01..04 落档（SD-05 条件触发）+specs.json
  P019-1 回读 True。验证：文件在档+账本断言+grep 锚。
- **AC-07 范围零越界**：.at 源与矩阵检查集零 diff；auto-lang 主树
  零改动。验证：双仓 porcelain+diff --stat 路径断言。

## 8. 执行步骤

| # | 任务 | 依赖 | 落点（实勘锚） | 产出/意图 | AC | 验证（命令/预期） |
|---|---|---|---|---|---|---|
| 0 | T-00 体积勘定决策件 | — | 本件 §5 T-00 节+evidence-p019-survey | 精测+手段序+通道定形 | AC-01 | [x] ✅ 报告在档（§① regen 探针 133 错实录/§② 基面裁定+基线 39,411,200B/§④ 构成占比表[.rdata 12.4MB=two-face 主项域]/§⑤ 手段序表） |
| 1 | T-01 portable 构建脚本 | T-00 | tools/portable/（三脚本） | 一键链+断言门 | AC-02 | [x] ✅ build_portable.py 链通+产物 dist/portable/（29,844,480B+sha256）+幂等自证 pass（第二遍哈希等价）——链 exit 1=尺寸门红为设计语义（超限差距数字入档） |
| 2 | T-02 手段迭代+护栏 | T-01 | 注入内容迭代+锚点档复跑 | 手段×{尺寸,锚点}终表 | AC-04 | [x] ✅ 终表六变体（V2=29.8MB -24.3% 终态/V3 abort -7.11MB/V4 z -7.65MB/V5 组合 16.46MB 距门 714KB）+护栏双轨全绿（工具链轨锚点 018 对照全容差内+产物面 probe_surface 三行大余量） |
| 3 | T-03 尺寸判定+收口 | T-02 | budgets.json+（条件）供料档增补 | 达标注记或差距+want | AC-03 | [x] ✅ 未达标=分阶段语义兑现：budgets installer 行数字回填（差距归因+门控测量位）+SD-05 two-face want 登记供料档 §5（条件触发成立） |
| 4 | T-04 portable 烟测 | T-02 | dist/portable/ 产物 | 单 exe 直跑证 | AC-05 | [x] ✅ 四段全绿（直跑 BENCH 标记对+单进程+零残留+back fsys 链；diff HTTP 面归矩阵域注记） |
| 5 | T-05 规范+账本 | T-01..04 | SD-01..05+specs.json | 裁定与形态落账 | AC-06 | [x] ✅ SD-01..05 全落档；P019-1 账本投影=merge 期项（016/017/018 先例——随 review/merge 轮，work 不碰活账本） |

## 9. 复审记录

- 2026-09-29 起草 handoff：`stage: new`，PLAN-019，plan_revision 1。
  `outcome: pass`（起草完备：Q3 用户裁定在案[§4 授权记录——两问
  答卷原文]；构建通道纯下游可行性实勘成立[生成物无 profile 节+
  gitignored→regen 后补丁注入]；性能护栏先于瘦身手段成门[M4 速度
  王座语义]；分阶段达标语义与条件触发 want 均有裁定依据；路径/符号
  经 auto-edit@0698641 与 auto-lang@e2deb4f87 双仓实勘锚定；授权=
  起草，执行待用户启动）。`next: work`。


- **2026-09-29 work handoff**：`stage: work` | PLAN-019 |
  plan_revision 1 | `outcome: pass` | code_commit: worktree
  plan-019-dev@**c41cf66**（base 0698641；单笔全落 T-00..T-05；
  worktree 清洁态）| task_ids: T-00..T-05 全落（current_step 6/6）|
  evidence: 勘定报告 specs/auto-edit/tests/evidence-p019-survey.md
  （regen 探针 133 错实录[供① 阻塞维持]+last-good 基面裁定+两漂移
  适配补丁[ui-gpui 声明/ClientOpts.remote——后者为记录性偏差：source
  面一行，边界注记在档]+cargo-bloat 构成表+手段×{尺寸,锚点}终表）+
  tools/portable/ 三脚本（build_portable/probe_surface/smoke_portable）
  + portable-*/surface-*/smoke-* JSONL 入仓+锚点三档 JSONL+SD-01..05
  落档+budgets installer 行回填 | blockers: 无 |
  next: review。
  执行期要点：①regen 上游阻塞=核心链按裁定回退 last-good 基面
  （2026-09-22 PLAN-007 era 生成物+依赖钉版 auto-lang@5bb3f53be——
  与 018 锚点谱同代；基线 39,411,200B vs 旧锚差 -243KB=依赖代差
  注记）；②终态手段集=lto=fat+codegen-units=1+strip+tokio 子集
  =29,844,480B（-24.3%）——**≤15MB 未达标=分阶段语义兑现**（差距
  归因=上游域[wgpu 4.1MB .text/two-face 全量语法集 .rdata 主项/image/
  HTTP/字体栈]+two-face want 已登记供料档 §5）；③门控手段测量位
  （Q-1/Q-2 裁定面数字在案）：panic=abort -7.11MB（**back_proxy.rs
  catch_unwind 隔离语义实勘**——生成码零处/back_proxy 一处生产用点）、
  opt-level=z -7.65MB、组合 16,459,264B **距门仅 714KB**；④G-4 护栏
  双轨全绿：工具链轨锚点三档复跑 018 对照全容差内（steady 230.3ms
  [-1.0%]/open 844.5ms/warm 1.5ms/idle≈48.5MB）+产物面探针
  （steady 21.2ms/open 38.2ms/idle 10.2MB 大余量）；⑤构建稳定性
  配方实录（本机编译高峰 rustc 0xc0000409 随机崩+dwm 连崩旁证——
  sccache 旁路+16MB 栈+-j2+瞬态崩限次重试，脚本固化）；⑥烟测 diff
  HTTP 面归矩阵域注记（生成 back=fys 契约路由实勘）；⑦工具链钉版
  二重性注记：组 auto-lang 树@5bb3f53be（源=依赖角色）+其 target/
  下预建 v2205 release 二进制（工具链角色——判据前 `auto --version`
  核纪律保持；树内不再 cargo build，出处收据在此）。

## 10. 待澄清事项

- **Q-1 panic=abort 手段授权（执行期数字已备，待裁定）**：默认保守
  不启用（已维持——终态集不含）；T-02 实测收益 **-7.11MB**（远超
  1MB 阈；组合 opt-level=z 后 16,459,264B 距 15MB 门仅 714KB）。
  语义面实勘：生成码 catch_unwind 零处，但 auto-lang back_proxy.rs
  一处生产用点（FFI 边界 panic 隔离）——启用即破该隔离。裁定问题：
  是否接受 panic=abort（进程遇 panic 直接终止，back_proxy 隔离失效）
  换 -7.11MB？（opt-level=z 另有 -7.65MB 但属 G-4 性能护栏面，需
  护栏复跑后裁决。）
- **Q-2 steady_start 护栏容差确认（无需裁定，确认口径）**：默认
  ±10% 运行方差容差（018 离散谱先例）——steady 现状未达标（232.6ms
  vs ≤80ms），「不劣化」判据以容差带为界；若用户希望严格逐跑不劣化
  （零容差），执行期示知——否则按默认。
