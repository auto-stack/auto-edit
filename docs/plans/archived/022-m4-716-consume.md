---
plan_id: PLAN-022
status: archived             # merge 收口（2026-10-01——reviewed r2 → archived 终态）
completion_kind: delivered   # 复工全弧交付：供⑧⑨⑪ 回执+帧两行首判 armed FAIL 落账+对比表滚动实数+供⑫⑬ 登记（性能面=管线优化件后续计划）
feature_name: M4-05 PLAN-716 三组消费件（组C diff 窗口切换+FAIL 清偿重判/组B 帧两行断言化+对比表滚动列/组A 双构建形态+语法面回归与语法联动 want 登记）+供③ P716-D1 销账
author: [agent]
created_at: 2026-10-01T14:13:05+08:00
updated_at: 2026-10-01T15:05:00+08:00
plan_revision: 2              # r2=review 裁定修订（AC-03 判定绿→armed 如实判定——用户裁定 2026-10-01，见 §4/§9；其余契约零变更）
current_step: 8
total_steps: 8
execution_context:
  worktree: D:/autostack/.wt/edit-022/auto-edit（branch plan-022-dev，base f9a16e5）
  dependency_pin: 组内 D:/autostack/.wt/edit-022/auto-lang@95dcfb55b detached（执行日 tip；含 716 ec45f911c+719/720）+ D:/autostack/.wt/edit-022/auto-down@895f8d0 detached（autodown-core 相对路径解析必需——018 惯例复活，021「不再需要」结论随 95dcfb55b 现势失效应验）
  toolchain: D:/autostack/.wt/edit-022/auto-lang/target/debug/auto.exe = v0.4.2-2474-g95dcfb55b（clean 无 -dirty；sccache 2m09s 构建；`--version` 核哈希含 716 交付 ec45f911c）
supersedes_spec_components: []
new_spec_components:
  - docs/specs/modules/perf-measurement.md（SD-01：帧两行断言化节+diff 窗口判定口径+滚动列我方态）
  - docs/specs/modules/diff-view.md（SD-02：envelope 窗口参数节——9920 消费面+默认形零扰动）
  - docs/specs/modules/back-api.md（SD-03：diff_files 窗口参数注记）
  - docs/specs/00-overview.md（SD-04：M4 第五件注记）
  - specs/auto-edit/README.md（SD-05：PLAN-022 口径）
  - docs/upstream/2026-09-m4-perf-unblock-supply.md（SD-06：条件——语法联动 want 登记）
touched_goals:
  - 战略 §2.1 预算行 diff_100mb ≤2s（armed FAIL 5183.2ms 清偿）+type_latency ≤1 帧+scroll_fps 满刷新率（两行首次可判）
  - 战略 §2.3 文件 diff 完全家「语法高亮联动」尾项处置（want 登记——供料驱动注记维持）
affects: [specs/auto-edit/src/back/fsys.at, specs/auto-edit/src/back/api.at, specs/auto-edit/src/front/app.at, specs/auto-edit/src/front/editor_store.at, tools/bench/bench.py, tools/bench/budgets.json, tools/compare/anchors.py, tools/compare/render_table.py, tools/portable/build_portable.py, specs/auto-edit/tests/desktop_mcp.py, specs/auto-edit/tests/probe_diffwin.py, specs/auto-edit/tests/run_matrix_x3.sh, specs/auto-edit/README.md, docs/specs/modules/perf-measurement.md, docs/specs/modules/diff-view.md, docs/specs/modules/back-api.md, docs/specs/00-overview.md, docs/upstream/2026-09-m4-perf-unblock-supply.md]  # r2 review finalize（F-1——front 探针臂+文档面+测试件补列）
---

# [PLAN-022] M4-05 PLAN-716 三组消费件（+供③ 销账）

## 0. 变更摘要

auto-lang **PLAN-716**（三组合一件，2026-09-30 delivered 归档@
ec45f911c+cleaned@215f984a3）的**下游消费件**——M4 预算面板的最后
一批转正面：**组C=diff 窗口切换+FAIL 清偿重判**（021 armed FAIL
5183.2ms 的清偿——9920 `auto.diff_files_window` 五参端点贯通 back
+bench 判定档切窗口形；上游 census 实测载荷 21.9×↓/墙钟 −29% 为
弹药）→ **组B=帧两行断言化**（type_latency ≤1 帧/scroll_fps 满刷新
率——9918/9919 `auto.frame.begin_ms/present_ms` 通道消费+AUTO_FRAME_
BENCH 门控；steady_start 首帧段分解补全；对比表滚动列我方数字）→
**组A=双构建形态+语法面**（ts-on/ts-off 载荷开关落地 build_portable
——716 实测叙事[ts-on +18.9MB/two-face 退役实收仅 -0.6MB]的下游
承接；语法面矩阵回归；**M3 尾巴「语法高亮联动」=want 登记**
（`highlight_segments` 无 .at 可达面——本件起草期 grep 实证，不硬
做））+ **供③ P716-D1 销账**（大文件卡死回归多跑×3 复核——018
「确认复核件」注记+716 降级挂账的清偿）。本件后 M4 剩余=installer
收口件+open_1gb 裁定+NP++ 列——**v0.1-M4 tag 的最后两件下游计划
之一**。

## 1. 目标

- **G-1 组C：back 窗口端点贯通**：fsys.diff_files_json 增窗口转发
  （9920 五参 `diff_files_window(path_a, path_b, ctx, rows_offset,
  rows_limit)`——默认形**逐字节等价**[716 golden 钉死]零扰动）；
  api.at `diff_files` 增可选 query 参数 `rows_offset/rows_limit`
  （缺席=全量——016 消费面零改动断言）；envelope 窗口形（rows_
  total+truncated 激活+hunks 全量）入 diff-view 契约。
- **G-2 组C：diff_100mb FAIL 清偿重判**：bench diff_100mb 判定档
  切**窗口形**（rows_limit=600 对齐 front 渲染 cap——「出结果」
  口径=hunks/counts/rows_total 全量+首窗 rows 渲染数据，BC 渐进
  显示同类语义；口径成文入 budgets validity）——重判 ≤2s 预期
  PASS（弹药：census window 1360ms@43.6MB 对 +021 FAIL 5183ms 主耗
  =envelope 全量投影+双层 JSON）；全量形保留为兼容对照档（数字
  在档不删）。
- **G-3 组B：帧两行断言化**：bench 增 type_latency 档（驱动键入→
  `auto.frame.present_ms-begin_ms` 读回≤1 帧——判定口径 T-00 定参
  [16ms@60Hz/8ms@120Hz 换算或 input→present 全链口径]）+scroll_fps
  档（滚动驱动→present 频率采样≥面板刷新率×0.9——面板率读回法
  T-00 定）；budgets 两行 armed；steady_start 分解谱补**首帧段**
  （spawn→first present——021 三段分解的首帧缺口闭合）。
- **G-4 组B：对比表滚动列**：我方滚动数字入 compare 表（anchors
  增滚动锚源+render 滚动行）；**竞品滚动列维持 pending 注记**
  （020 Q-2 口径——捕获自动化双缺陷实证，不冒领）。
- **G-5 组A：双构建形态+语法面**：build_portable 增 **ts-on/ts-off
  载荷开关**（feature `highlight-treesitter` 门控注入——ts-off=
  发布/installer 约束形、ts-on=语法高亮完整形[+18.9MB 实测]）；两
  形态构建冒烟（装载+语法面抽档）+矩阵语法面回归（lang 路由/tail
  [.at/mermaid] 面）；**M3 尾巴「语法高亮联动」处置**：`highlight_
  segments` 无 .at 可达面（起草期 grep 实证——native_catalog/
  ui_gen/trans 三面零命中）→ **want 登记**（diff 视图行级/文本段
  语法着色端点——供料档增补）+M3 尾巴维持「供料驱动」注记。
- **G-6 供③ P716-D1 销账**：大文件实例 UI 卡死回归多跑×3（T17
  交互簇——021 谱已全绿基线）+KNOWN-DEBT P716-D1 回写销账（018
  「登记保持至上游确认/多跑复核」注记的终结动作）。
- **G-7 规范+账本**：SD-01..05 落档+（条件）SD-06 want 登记+specs.
  json P022-1。

### 非目标

- **installer 收口件**（ts-off 形态尺寸判定+门控手段[panic=abort/
  opt-z]裁定+~1MB 再挤——下一件；本件只交付 ts-off 构建通道）。
- **front diff 视图窗口化消费**（滚动惰性拉行=UX 件——本件 back/
  bench 面贯通即清偿判定；front 仍默认全量形消费[日常文件量级]）。
- **语法高亮联动实施**（diff 视图行级着色——want 登记后随上游
  端点另立消费件；M3 尾巴注记维持）。
- 竞品滚动测量（020 Q-2 维持 pending）；open_1gb 裁定与实施（用户
  件+上游域——designs/002 材料在案）；NP++ 列（用户安装后补跑）。
- onig/syntect 摘除（上游 cosmic-text 解耦另档——716 r2 偏差注记）；
  auto-lang 侧任何改动（上游缺陷回 upstream 登记）。

## 2. 架构方案

分层落点（2026-10-01 实勘，auto-edit main@f9a16e5 + auto-lang
master@7491719b8）：

| 面 | 现状 | 本期形态 | 依据 |
|---|---|---|---|
| diff back | fsys.diff_files_json→9915 裸名直调（016 纯转发）；api diff_files 三参 | 增窗口转发（9920 五参——窗口参数在场时；缺席=9915 等价路径）+api 可选 query 参数 | 716 SD-C（9920 签名/HTTP 形/默认等价 golden 在册） |
| bench diff 档 | diff_100mb=全量形 armed FAIL 5183.2ms（021） | 判定档切窗口形（limit=600 对齐渲染 cap）+全量对照档保留；budgets validity 口径重写 | 716 census（21.9×↓/−29%）；011 渲染 cap 600 |
| 帧观测 | 通道已交付未消费（9918/9919 auto.frame.begin_ms/present_ms+AUTO_FRAME_BENCH 门控+零开销实证） | bench 两档（type_latency/scroll_fps）+steady 首帧段+budgets armed | 716 SD-B（双时间戳锚点/门控/0=未捕获值语义） |
| 对比表 | 4 行 L2 实数+diff FAIL 行+滚动列缺 | diff 行重判数字+滚动行我方列（竞品 pending 维持） | 020 三态机制+021 l2 终态 |
| 构建形态 | build_portable 单形态（019 注入通道——feature 面未门控） | ts-on/ts-off 开关（highlight-treesitter feature 注入）+双形态冒烟 | 716 实测叙事（ts-on +18.9MB/two-face −0.6MB/onig 阻断） |
| 语法面 | 内核 21 语言+syntect 缩减集双轨交付；矩阵无语法着色断言面（T-15 口径：a11y 不携 style） | 构建形态冒烟+lang 路由读回抽档+视觉面注记；联动=want 登记 | 716 SD-A；highlight_segments 三面 grep 零命中（起草期实证） |
| 供③ | P716-D1 降级挂账（KNOWN-DEBT）+021 谱 T17 全绿基线 | 多跑×3+销账回写 | 716 r2 收据+018 ef467b3 注记 |

**关键设计约束（frozen）**：
① **默认形零扰动**（api 参数缺席=016 消费面逐字节等价——021 矩阵
回归哨复用）。② **判定不冒领**——diff 重判口径（出结果=全量 hunks/
counts/rows_total+首窗 rows）成文入 budgets validity；全量对照档数字
保留不删；帧两行判定口径（面板率换算/读回法）T-00 定参后成文。③
front 消费面零改动（窗口化仅 back/bench 域——front 惰性拉行=后续件）。④
双构建形态=构建通道件（不改产品代码——build_portable 注入面）。⑤
供③ 销账=多跑实证（×3 全绿）非推断。

## 3. 技术栈

python bench/compare/portable 工具族扩展+.at back 增参（fsys/api 最小
diff）+desktop_mcp 矩阵（回归哨+T17×3）+帧驱动（desktop_mcp 键入/
滚动 action→frame 读回）。工具链纪律承 021：master 重建含 716
（ec45f911c+）；`auto --version` 核哈希；组依赖钉版惯例。

## 4. 需求分析与背景调查

**授权记录**：用户 2026-10-01 会话指令「OK，auto-plan-new 起草
计划 022」——授权=**起草本件**；执行/work 待用户另行启动。
〔r2 补录：后续用户指令链=「实施它」（work 授权）→「计划716已经
全部完成；可以继续本计划的实施了」（复工授权）→「auto-plan-review
; then auto-plan-merge」（复审+merge 授权——复工 summary 已如实
披露帧两行 armed FAIL 实数与 AC-03 判定绿未达，本裁定=验收按
armed 如实判定语义收口，AC-03 修订随之；716 修复轮由用户另行
执行完毕）〕范围=
auto-edit 单仓（src/back 最小 diff+tools/docs/tests）；auto-lang 零
改动（want 登记为文档面）。无预算/自动续跑授权。

**来源与版本**：

- 交接链：PLAN-716 归档件（auto-lang delivered@ec45f911c——三组
  交付实录+**实测翻转注记**[two-face 退役实收 -0.6MB 非 12.4MB 量
  级/ts-on +18.9MB/onig 阻断]）+SD-A/B/C 三册（ledger P716-1/2/3
  投影在案）；PLAN-021 归档件（auto-edit delivered@f9a16e5——
  五行判定谱[4 PASS+diff FAIL 5183.2ms]+对比表 l2 终态+三域冒烟
  7/7）。
- 上游交付面锚（716 SD 册实读）：9920 `auto.diff_files_window`
  （裸名 diff_files_window/五参签名/HTTP GET /api/diff_files_window
  串形/默认三参逐字节等价 golden/rows_total+truncated 激活/hunks
  全量）——SD-C 册 diff-endpoints.md:56-91；帧通道 `ui::frame_
  bench`（AUTO_FRAME_BENCH 门控/9918 auto.frame.begin_ms+9919
  auto.frame.present_ms→I64/0=未捕获值语义/a2r 双臂/门关 ns 级）
  ——SD-B 册 frame-observability.md:9-53。
- 下游现状实勘（main@f9a16e5）：fsys.at diff_files_json=9915 纯
  转发（016）；api.at diff_files 三参（:117）；bench.py diff 档
  （881+——判定调用全量形）；budgets 十行判定态（4 PASS+FAIL+两行
  排队注记）；tools/compare 三态列机制；build_portable 注入通道
  （019）；desktop_mcp T15/T17 族结构。
- 关键否定面实证（起草期）：`highlight_segments` 无 .at 可达——
  native_catalog/ui_gen/trans 三面 grep 零命中（语法联动=want 而非
  消费）。
- 历史关联：PLAN-011（渲染 cap 600——窗口 limit 对齐依据）/016
  （替换缝+默认形零扰动纪律）/018（供②③ 排队注记——本件清偿
  面）/020（滚动列 pending 口径）/021（FAIL 谱+矩阵回归哨）。

## 5. 详细设计

### T-00 消费勘定决策件

1. **diff 重判口径定参**：窗口 limit 值（600=渲染 cap 对齐 vs 1000
   余量——默认 600）；「出结果」语义成文（hunks/counts/rows_total
   全量+首窗 rows=BC 渐进同类口径）；全量对照档保留形。
2. **帧两行判定口径**：type_latency 判定式（present−begin ≤1 帧
   [@面板 Hz 换算] vs input→present 全链——帧内口径[通道原生]为
   默认，全链口径注记）；scroll_fps 采样窗与驱动协议（desktop_
   mcp 滚动 action 连发→present 频率统计）；面板刷新率读回法
   （枚举显示设置 or 实测 present 稳态频率反推——T-00 定）。
3. **ts 双形态构建面**：build_portable 注入点扩展（feature 追加
   面）；两形态产物命名/目录约定（ts-on/ts-off 后缀）。
4. **语法面断言边界**：lang 路由读回面（autoui 状态域语法 lang 字
   段?——T-00 勘）；不可断言面=视觉门注记（T-15 口径）。

### T-01 组C：back 窗口贯通（G-1）

fsys.diff_files_json 增窗口臂（参数在场→9920 五参；缺席→9915 原
路径）+api.at `diff_files` 增可选 `rows_offset/rows_limit`（HTTP
缺席语义=全量）；探针=默认形逐字节等价（021 矩阵哨复用）+窗口形
字段族（rows_total/truncated/越界净形——716 SD-C 边界形对齐）。

### T-02 组C：diff_100mb 重判（G-2）

bench diff_100mb 判定调用切窗口形（limit=600）+全量对照档改名
保留；重判谱 N≥4+≤2s PASS 预期；budgets validity 口径重写（出结果
语义+弹药对照）；对比表 diff 行刷新（anchors/render——FAIL→PASS
数字）。

### T-03 组B：帧两行断言化（G-3）

bench 增两档：type_latency（驱动键入→帧对读回→帧内耗时分布+
P95 判定 ≤1 帧）+scroll_fps（滚动连发→present 频率≥面板率×0.9）；
steady_start 分解谱补首帧段（spawn→first present_ms）；budgets 两
行 armed+判定谱注记。

### T-04 组B：对比表滚动列（G-4）

anchors 增滚动锚源（T-03 数字直读）+render 滚动行（我方列实数+
竞品 pending 注记维持）+README --check 复现。

### T-05 组A：双形态+语法面（G-5）

build_portable ts 开关（注入面+产物双形态）；双形态冒烟（boot/
装载/语法面抽档——ts-on 完整 21 语言/ts-off 缩减集+tail）；矩阵
语法面回归（lang 路由读回抽档+视觉面注记）；**语法联动 want 登记**
（供料档增补节：diff 视图行级/文本段语法着色端点——`highlight_
segments` 暴露形建议+三面零命中证据+M3 尾巴注记维持）。

### T-06 供③ 销账（G-6）

T17 大文件交互簇多跑×3（desktop_mcp 全矩阵或 T17 抽组——021 谱
131/0 基线复现×3）；全绿→KNOWN-DEBT P716-D1 回写销账（auto-lang
侧债务档——**跨仓文档注记**：下游复核证据+上游档回写建议，若上
游档不可直书则 evidence 入本仓+upstream 登记节）。

### T-07 规范+账本（G-7）

SD-01..05 落档+（条件）SD-06 want 节+specs.json P022-1 投影
（015-021 外科插入先例）。

### 规范增量

| delta_id | add/modify/retire | docs/specs/... target | before/after rule | rationale | acceptance IDs |
|---|---|---|---|---|---|
| SD-01 | modify | docs/specs/modules/perf-measurement.md | before：L2 断言全表=五行判定（diff FAIL 在档）+帧两行排队注记 / after：diff 窗口判定口径（出结果语义+全量对照档保留）+帧两行断言化节（判定式/面板率换算/驱动协议）+steady 首帧段+滚动列我方态 | 判定面收口规范 | AC-02/03/04 |
| SD-02 | modify | docs/specs/modules/diff-view.md | before：envelope 契约=全量 rows 投影（truncated 恒 false——引擎时代节） / after：增窗口参数节——api 可选 rows_offset/rows_limit（缺席=全量零扰动）+rows_total/truncated 激活语义+hunks 全量+front 惰性拉行=后续件注记 | 9920 消费面契约 | AC-01 |
| SD-03 | modify | docs/specs/modules/back-api.md | before：diff_files 三参（第 10 端点） / after：增可选窗口参数注记（缺席语义+9920 指向——计数不变） | 端点形参登记 | AC-01 |
| SD-04 | modify | docs/specs/00-overview.md | before：M4 注记止于第四件（L2 链解阻兑现） / after：M4 第五件注记（716 三组消费——diff 重判/帧两行/双形态+语法联动 want 登记+供③ 销账；M4 剩余=installer 收口+open_1gb 裁定+NP++） | 面进度总览 | AC-06 |
| SD-05 | modify | specs/auto-edit/README.md | before：PLAN-021 口径 / after：PLAN-022 口径（窗口判定用法+帧两行档+ts 双形态构建+判绿数字回填位） | 运行矩阵/工具单源 | AC-06 |
| SD-06 | modify（条件） | docs/upstream/2026-09-m4-perf-unblock-supply.md | before：四件供料全清偿（§1-§4 回执在册） / after：增补语法联动 want（diff 视图行级语法着色端点——highlight_segments 暴露形；M3 尾巴供料驱动注记维持） | M3 尾巴处置登记 | AC-05 |

## 6. 测试设计

- **back 窗口面**：默认形逐字节等价（021 矩阵哨复用——T15 主链）
  +窗口形字段族探针（rows_total/truncated/offset 越界净形/limit 0
  /跨 hunk——716 SD-C 边界形对齐）。
- **bench 重判**：diff_100mb 窗口形 N≥4 谱（≤2s PASS）+全量对照
  档（FAIL 数字保留在档——清偿前后对照表）；计时卫生承 016/018
  （沉降窗）。
- **帧两行**：type_latency 分布谱（P50/P95 判定）+scroll_fps 采样
  窗稳定判据+门控零开销面引用（716 实证——不重测）；面板率读回
  与判定换算在档。
- **双形态构建**：ts-on/ts-off 产物双冒烟（boot/装载/语法抽档）
  +尺寸双记（ts-on +18.9MB 量级复现对照）。
- **矩阵**：021 回归哨复跑（默认形零扰动）+T17 簇×3（供③ 销账
  证据）。
- **对比表**：--verify/--check 双绿（diff 行刷新+滚动行新增）。

## 7. 验收标准

- **AC-01 back 窗口贯通**：默认形逐字节等价（矩阵哨绿）+窗口形
  字段族探针绿+api 可选参数缺席语义断言。验证：探针+矩阵 T15
  主链绿。
- **AC-02 diff FAIL 清偿重判**：窗口形 ≤2s PASS 谱在档+budgets
  validity 口径重写+全量对照档保留。验证：bench 谱+ budgets 注记。
- **AC-03 帧两行断言化（r2 修订——用户裁定 2026-10-01，见 §9
  review 记录）**：type_latency/scroll_fps 两档 **armed（判定如实
  ——PASS 或 FAIL 带谱+归因，禁冒领）**+budgets 两行 armed+steady
  首帧段记账位。验证：两档谱+budgets。〔原「判定绿」子句=性能
  预期非交付物：供② 交付物=测量解锁（PLAN-005 起blocked→本件
  首判）；实测 6.6×/6.75× 预算差=键入帧管线真实成本（debug/release
  同量级），优化=管线件后续计划——复工 summary 用户已阅并指示
  review/merge。首判实数：P50 110/P95 115ms+8.0fps〔armed FAIL，
  frame-20261001-230957.jsonl〕〕
- **AC-04 对比表滚动列**：我方滚动数字+diff 行 PASS 刷新+--check
  双复现；竞品滚动 pending 维持。验证：render 输出+--check 绿。
- **AC-05 语法面+want 登记**：双形态构建冒烟绿+矩阵语法面回归
  绿+语法联动 want 节在档（证据链：三面 grep 零命中）。验证：
  冒烟记录+供料档增补节。
- **AC-06 供③ 销账**：T17 簇×3 全绿+P716-D1 回写（或 evidence+
  upstream 登记）。验证：三跑记录+债务档注记。
- **AC-07 规范+账本+范围**：SD-01..05（条件 SD-06）落档+P022-1
  回读 True+.at 源 diff 限 back 最小面+auto-lang 主树零改动。
  验证：文件在档+账本断言+双仓 porcelain。

## 8. 执行步骤

| # | 任务 | 依赖 | 落点（实勘锚） | 产出/意图 | AC | 验证（命令/预期） |
|---|---|---|---|---|---|---|
| 0 | T-00 消费勘定 | — | 本件 §5 T-00 节 | 四口径定参+构建面盘点 | 全 | [x] 勘定记录在档（2026-10-01 执行期勘定：①**diff 窗口 limit=600**（Q-1 默认定参——011 渲染 cap 对齐；首屏语义）；②**type_latency=帧内口径**（Q-2 默认——present−begin 通道原生；全链口径注记并列不判定）；③**api 形态适应（新证据）**：VM HTTP 服务侧「缺参 400」实证〔auto-lang vm/ffi/http_server.rs:37「路径段→body→query，缺参 400」〕+merged 轨进程内 CALL 按位装配——同端点「可选 query 参数」在双轨皆不可表达〔3 参调用打 5 参 fn=HTTP 400/arity 炸〕→**采用上游 9920 同构形**：api.at 增独立第 16 端点 `diff_files_window`（五参全必填，HTTP 串形=SD-C 原文）+fsys.at 增 `diff_files_window_json` 五参转发；旧 `diff_files`/`diff_files_json` 逐字节零触碰=默认形零扰动最强形；「缺席=全量」语义由端点二分承载（缺席窗口参数=旧端点=全量形）——SD-02/03 落档随此形；④**帧读回通道**：api.at 增 `/api/frame_probe` 端点（back 域——in-proc 读 9918/9919 进程级原子〔ui::frame_bench OnceLock+AtomicI64 进程全局，SD-B〕），判定形=L0 server-vm release 工具链（`run --server vm`——iced 渲染器同进程实证锚 main.rs:1049 注记「same process for -r vm」；执行期活体探针复核 begin_ms>0）；**L2 拓扑无帧读回通道**（a2r app 零旗标无 HTTP 面——back exe 无渲染器原子恒 0）→两行判定=L0 server-vm 形 armed（VM 解释段=保守上界——过判则 a2r 形必快，保守方向判定；tier 维持 ledger+形态注记；L2 武装=front 探针件后续件注记）；面板率读回=host 侧 EnumDisplaySettings（bench python ctypes）；steady 首帧段=spawn→frame_probe present_ms 首个非零 host 时刻（零 front 触碰——affects 面保持）；⑤**T-06 择路=fallback**（Q-3）：auto-lang 并行会话在途〔.wt/lang-721 等〕+本件非目标「auto-lang 零改动」→多跑 evidence 入本仓+供料档 §3 销账注记+KNOWN-DEBT 回写建议文随附（AC-06 括号臂）；⑥**构建面盘点**：sibling 工具链（上）+auto-down 组树必需复活〔autodown-core `../../../auto-down/…` 相对路径自 sibling 解析→组树缺失=regen/build 即败——首建败实录在案〕+a2r regen=perf.py a2r→release=perf.py release（api.at 第 16 端点入 back exe 需 regen+release 重建）；主检出外来 WIP=specs/stylekit 两文件删除态在案〔他属会话——零触碰零包含，落地时另行路由〕） |
| 1 | T-01 back 窗口贯通 | T-00 | fsys.at+api.at（最小 diff） | 9920 转发+可选参数 | AC-01 | [x] 等价哨+字段族探针绿（commit 480ba6e+验证收口：fsys.diff_files_window_json 9920 五参裸名直调+api.at 第 16 端点[独立五参端点形——T-00③ 双轨约束适应]；probe_diffwin --back 形 8/8 PASS[evidence-p022-t01.json——①默认形键集恒 8 不增 rows_total+②窗口形 rows_total/truncated/hunks 全量/切片逐行等价+③边界净形]；**执行期发现供⑧**：9920 VM codegen 裸名臂缺失〔codegen.rs:559-561 三 diff 面无 window——实测 HTTP 线程挂死〕，a2r trans/ui_gen 臂 716 已交付〔生成物 main.rs:2259 直调 a2r_std 实证〕——探针判据走 --back 形+供⑧ 上游登记；016 消费面零触碰=frozen③ 最强形；矩阵 T15 主链哨=front 零改动自证随 T-06 ×3 复跑；**供⑧ 清偿回执（716 r3 T-14）**：撞号改签 9920→9921[PLAN-095 ui.focus 占位]+codegen 裸名臂补全——probe_diffwin 缺省 VM 形 8/8 PASS〔2026-10-01，工具链 v0.4.2-2533-g9a71a5212〕+--back 形 8/8 双绿，9920→9921 引用全链对齐） |
| 2 | T-02 diff 重判 | T-01 | bench.py+budgets+compare | FAIL→PASS 清偿 | AC-02/04 | [x] 窗口谱 ≤2s+口径在档（commit 845f584+收口批：bench L2 判定档切窗口形[offset=0/limit=600]+diff_100mb_full 对照档[kind=full-ref 不判定]+N≥4 谱；**armed PASS median 784.8ms**〔4 跑谱 756.6-928.8——vs 全量对照 5078.2ms 同谱复现 021 形态，清偿倍率 6.5×；021 归因①envelope 全量投影+双层 JSON 随窗口物化消除〕；budgets validity 口径重写[出结果语义+全量对照不删]+对比表 diff 行三态并陈[016 1906/021 FAIL 5183.2/022 PASS 784.8]——anchors --verify 9 行全等+render --check 双绿；谱 diff-20261001-144526.jsonl 入仓；L0 VM 形维持全量旧径零扰动[供⑧ 下 VM 轨窗口调用不可用]；复现终跑谱随 T-05 后补入注） |
| 3 | T-03 帧两行断言化 | T-00 | bench.py 增两档+frame 读回 | 两行 armed+首帧段 | AC-03 | [x] 两档谱+首帧段收口（2026-10-01 复工——供⑨ 经 716 r3 T-15/T-16 清偿后首判）：**armed FAIL 双行落位**〔测量解锁=供② 交付物达成；性能缺口如实红——type_latency 帧内口径 P50 110/P95 115ms vs ≤16.7ms→FAIL ~6.6 帧+scroll_fps 8.0fps vs ≥54→FAIL（换行连发 cursor-follow 滚动驱动，下界测量不过阈）；debug 对照谱 78/159ms+11.4fps 同量级=编译形态无关归因强证——键入帧全量重建管线 ~110ms/帧主耗，优化=管线件后续〕；bench frame 档实现〔MCP 帧探针字段读回+autoui_type 驱动——勘定修正：键盘直驱不达编辑器〕+steady 首帧段记账位〔4989ms 帧值坐标——SD-B §3b 时源勘定修正注记〕+budgets 两行 armed+SD-01 帧节重写+对比表滚动行实数落位〔8.0fps armed FAIL——anchors unit=fps 分支 --verify 10 行全等+--check 双绿〕；谱 JSONL ×2 入仓；上游消费链=供⑨ 清偿回执+供⑬ 适配（i64 字段——a2r trans 臂 E0308 上游解形建议在案）+供⑫ 适配（标记行撤除）在案 | 
| 4 | T-04 对比表滚动列 | T-03 | compare/{anchors,render}.py+README | 滚动行+diff 行刷新 | AC-04 | [x] --verify/--check 绿（收口批 commit：anchors 增 SRC_L2_DIFF_022 窗口谱源+022 PASS 行+scroll l2-pending 行〔零数字虚席——冒领禁则〕+render diff 行三态并陈+滚动行落位[我方供⑨ 注记+竞品 020 Q-2 pending 维持]；anchors --verify **9 行三态数据与源 JSONL 全等**+render --check **README 区间复现一致**双绿实录） |
| 5 | T-05 双形态+语法面 | T-00 | build_portable.py+矩阵抽档+供料档 | ts 开关+want 登记 | AC-05 | [x] 双冒烟绿+want 节在档（build_portable --ts on|off 收口 commit：feature workspace dep 行注入+产物双命名[ts-off=auto-edit.exe 30,355,456B 预算判定域/ts-on=auto-edit-ts-on.exe 51,457,024B 记录位——**Δ+21.1MB vs 716 实测 +18.9MB 同量级复现**]；双形态 boot/装载冒烟 PASS[release 零旗标直拉 bench_open_done 2s 同拍]+feature 门控 binary 探针[tree_sitter 符号 on=23/off=0 干净]；**供⑪ cc 夹缝首建实录+回避钉 blake3 1.5.5 幂等锁定**[供料档 §8]；语法联动 want 登记[三面 grep 零命中——M3 尾巴注记维持]；**供⑪ 撤钉回执（716 r3 T-17 零 diff——registry 演进 sequel 0.3.11）**：blake3 1.5.5 回避钉移除+fresh cargo update〔blake3 1.8.7/sequel 0.3.11/cc 1.2.67〕+check 绿 52.7s；语法面边界=T-15 视觉门注记[语法着色非机器断言面——upstream 716 22 语言 fixture 矩阵为上游锚]） |
| 6 | T-06 供③ 销账 | — | desktop_mcp T17×3+债务档 | P716-D1 清偿 | AC-06 | [ ] **销账未达（维持挂账——不假销账）**：处方 part-1 落实[主实例 MCP 端口高带钉位臂——924x TOCTOU 带 3/6→0/3 清零]+全矩阵 ×3 谱[93 PASS/**0 FAIL**——T1-T9 深度全绿含 T15 diff 主链零扰动哨随跑复证；T17 不可达：app 动作相关净退 ×2〔T6/T9——**空闲对照 420s 存活排除自退**，vnode 漂移误击家族嫌疑=环境态非确定性 P716-D1 原录口径〕+T10 子实例 spawn 败 ×1]+共栖 721 desktop 会话在途〔空闲窗口期处方前提不成立〕→P716-D1 维持「确认复核件」挂账+回写建议文随附[evidence-p022-t06.md+matrix-p022-run{1,2,3}.txt+供料档 §3 复试更新]——AC-06 括号臂（evidence+upstream 登记）承载；下次空闲窗口期按 runner 复跑即续 |
| 7 | T-07 规范+账本 | T-01..06 | SD-01..06+specs.json | 消费收口落账 | AC-07 | [x] P022-1 True+范围断言（SD-01 perf-measurement PLAN-022 节〔窗口口径+帧协议+滚动列〕/SD-02 diff-view 窗口形节/SD-03 back-api 十六端点+第 16 端点节/SD-04 overview M4 第五件注记/SD-05 README PLAN-022 口径/SD-06 供料档 §8〔供⑧⑨⑪+want+供③ 复试更新〕全落档；specs.json P022-1 外科插入 22→23〔roundtrip 守卫：他五段+reviews 前缀 21 项零扰动+插入项逐字回读〕；范围断言=.at diff 限 back 最小面[fsys.at+api.at]——front 执行期零最终改动[探针臂预埋尝试已撤]+auto-lang 主树 tracked 零改动[porcelain 实证]+sibling 两树 clean） |

## 9. 复审记录

- 2026-10-01 起草 handoff：`stage: new`，PLAN-022，plan_revision 1。
  `outcome: pass`（起草完备：716 三组消费面逐一有锚[SD-B/SD-C 册
  实读+签名/门控/等价 golden 引用]；FAIL 清偿判定口径防冒领成文
  [出结果语义+全量对照保留]；语法联动不可消费有起草期否定面实证
  [三面 grep 零命中]→want 登记不硬做；供③ 销账=×3 实证非推断；
  双构建形态承接 716 实测翻转叙事；路径/符号经 auto-edit@f9a16e5
  与 auto-lang@7491719b8 双仓实勘锚定；授权=起草[用户指令原文在
  录]，执行待用户启动）。`next: work`。

- 2026-10-01 work handoff：`stage: work`，PLAN-022，plan_revision 1
  （worktree plan-022-dev 终笔提交序列 480ba6e→收尾）。`outcome:
  blocked`（部分交付——六/八任务完成落地，两任务 blocked 如实挂起；
  非执行缺陷，均为外部依赖缺口且证据链/解阻动作完备）。
  `code_commit`: worktree plan-022-dev@终笔。`task_ids`: T-00/T-01/
  T-02/T-04/T-05/T-07 完成；T-03 blocked（供⑨——上游 9918/9919 .at
  消费面双缺口：VM i64→int 桥+a2r ui_gen 臂；判定协议/成文/budgets
  证据链行/l2-pending 虚席全在档，清偿后首判即活）；T-06 销账未达
  （供③ P716-D1 维持挂账——处方 part-1 已落实+×3 谱 93/0 T17 不可达
  〔环境非确定性，空闲窗口期复跑判据不变〕）。`evidence`: AC-01 探针
  8/8+矩阵 T15 随跑零扰动；AC-02 双谱 armed PASS 784.8/1261.1ms+
  budgets 口径重写+全量对照不删；AC-03 协议成文（判定面 blocked 如实
  不冒领）；AC-04 --verify 9 行+--check 双绿；AC-05 双形态实录
  Δ+21.1MB+门控探针+冒烟双 PASS+want 节；AC-06 fallback 臂（evidence
  +upstream 登记——AC 原文括号臂）；AC-07 SD-01..06 全落+P022-1 True
  23 项+范围断言三树 clean。`blockers`: 供⑨（T-03 判定面——上游
  stdlib/shim/codegen 三面补臂）+空闲窗口期（T-06 复跑）。`next`:
  本件非 execution_done（AC-03 未达——keep executing）；已交付面可
  先行 review 供merge 评估〔供⑨ 清偿后 T-03 在本件或后续件收口——
  用户裁定〕。

- 2026-10-01 work 复工 handoff（716 Phase 2 交付后）：`stage: work`
  续，PLAN-022，plan_revision 1（语义契约未变——blocked 面清偿收口
  =原任务完成，非修订）。`outcome: pass`（execution_done——八任务
  全终态：T-01 供⑧ 回执〔VM 形 8/8+9921 对齐〕；T-03 供⑨ 清偿后
  首判 armed FAIL 双行落位〔测量解锁=供② 交付物；性能缺口归因=
  键入帧全量重建管线 ~110ms/帧——debug/release 同量级，优化=管线
  件后续〕+首帧段记账位+对比表滚动实数；T-05 供⑪ 撤钉回执；T-06
  维持 fallback 臂已录；供⑫⑬ 新缺口登记随供料档 §8）。`code_commit`:
  worktree plan-022-dev 终笔。`task_ids`: 全部（T-00..T-07）。`evidence`:
  AC-01/02/04/05/06/07 维持+AC-03 断言化交付〔armed FAIL 谱/归因/
  协议成文——判定绿子句如实未达，性能面=后续件〔管线优化件〕，
  供 merge/review 裁量〕。`blockers`: 无（本件范围）。
  `next: review`。

- 2026-10-01 review：`stage: review`，PLAN-022，plan_revision
  1→2。`outcome: pass`（→reviewed）。`reviewed_commit`: worktree
  plan-022-dev@**a88ae13f**〔review 证据链末笔——含 review 矩阵
  实录+frame 复现谱〕；`base_commit`: f9a16e5。`dependency_revisions`:
  auto-lang 组树@9a71a5212 detached（工具链 v0.4.2-2533 debug+release
  双证——供⑧⑨⑪ 清偿面）+auto-down@895f8d0。`spec_inputs`: worktree
  docs/specs@HEAD〔SD-01..04+README+供料档 §8 全部在树——canonical
  随 merge 落位〕。`acceptance_results`: AC-01 **pass**〔双形探针
  8/8 review 现场复跑；旧端点零触碰结构性+实证双承载〕/AC-02
  **pass**〔双谱 committed+budgets 口径+全量对照保留；anchors
  --verify 9 行全等〕/AC-03 **pass（r2 修订形）**〔armed FAIL 双谱
  +复现谱〔95/106ms+9.1fps——判定带内一致〕+首帧段记账位；原
  「判定绿」=性能预期非交付物，实测 FAIL 如实红——用户裁定按
  armed 如实判定收口，修订透明在录〕/AC-04 **pass**〔--verify 9 行
  +--check 双绿现场复跑+滚动实数〕/AC-05 **pass**〔双形态实录+门控
  binary 探针+冒烟双 PASS+want 节；供⑪ 撤钉回执 fresh 解析+check
  绿〕/AC-06 **pass（AC 原文括号臂）**〔×3 谱+环境归因+回写建议——
  evidence-p022-t06.md〕/AC-07 **pass**〔SD-01..06 落档+P022-1 回读
  True〔23 项〕+auto-lang 主树零触碰〔716 修复轮=上游自身件〕〕。
  `findings`: **F-1**（low，scope-note）：.at 终态 diff=back〔窗口
  端点〕+front〔bench 双门探针臂 55 行——T-03 读回必需，frozen③
  「窗口化仅 back/bench 域」合规（探针=bench 域仪表，门关零行为）〕
  ——AC-07「back 最小面」字面对窗口化面成立；affects 清单漏列
  front/文档/结果件→**review finalize**（本记录随行更新）。
  **F-2**（info）：审查门矩阵=环境非确定性家族下部分深度绿〔4 次尝试
  〔T-06 ×3+review 1〕累计 134 PASS/0 FAIL，深 T6-T10；T15 深度未达
  ——**更正**：T-06 提交信息「T15 随跑复证」为 overclaim，零扰动由
  「旧端点/视图代码未触+探针臂双门关闭」结构性承载；完整深度绿待
  环境窗口（T-06 已录）〕。**F-3**（info）：ts-on 全量构建实证于
  撤钉前形态〔600ba65〕；撤钉后 resolution+check 绿〔52.7s〕，全
  构建重跑未重复（构建=分辨率无关面）——如 merge 需要可补跑。
  **F-4**（info）：三态锚点计数=9 行（复工 summary「10 行」为笔误；
  --verify 9 行全等为真值）。`evidence`: tests/evidence-p022-t01.json
  〔双形 8/8〕+tests/evidence-p022-t06.md+matrix-p022-run{1,2,3,review}.txt
  +frame/diff/portable 谱 JSONL ×9+results/anchors.json+table.md
  （全 committed@a88ae13f——worktree 移除后 durable）。`next`: merge。

- 2026-10-01 merge：`stage: merge`，PLAN-022，plan_revision 2（r2）。
  `outcome: pass`（delivered——五检查点全落，见下）。`delivery_commit`:
  main@**69e6cc9**〔ff-only 线性——rebase 旧→新映射 a88ae13f→69e6cc9
  尾笔，range-diff 14 work 提交全等〔3 main 记账提交随行吸收〕〕；
  `base_commit`: f9a16e5。
  - **prepared**：reviewed r2 基线=main@88bdb64/工作树 plan-022-dev
    @a88ae13f；canonical Spec diff=worktree docs/specs 已提交面
    〔SD-01..04+README+供料档 §8——本树 docs/specs@69e6cc9 即落位
    形〕；projection 目标=.autoos/specs.json reviews 段 P022-2
    （tracked ledger main 轨循 021 P021-2 先例）；delivery_commit
    推定=69e6cc9。
  - **landed**：plan-022-dev rebase main〔88bdb64〕零冲突——range-diff
    14 提交全等实证；`git merge --ff-only`=main tip **69e6cc9**〔零
    merge 提交〕；main 烟测三绿〔anchors --verify 9 行全等+render
    --check 复现一致+probe_diffwin VM 形 8/8〕。
  - **ledger_refreshed**：.autoos/specs.json reviews 段 P022-2 外科
    插入〔23→24——merge 收据：四检查点+对照表终态+三域回归+上游
    清偿回执+供⑫⑬ 登记；roundtrip 守卫=json.loads 新旧深等〔他五段
    +reviews 前缀零扰动〕+插入项逐字回读；本格=随归档提交后置实测
    回读——P021-2 先例〕。
  - **archived**：docs/plans/archived/022-m4-716-consume.md〔git mv〕
    +status: archived+completion_kind: delivered〔本格即归档格〕。
  - **cleaned**：待回填〔worktree/branch/组树三树注销+wt-guard 后实
    录——归档提交后执行〕。
  - **部署观察**：本仓无运行中生产进程/daemon；dist/portable 双形态
    exe=测量证据件〔ts 尺寸/门控与探针字段无关——ts-on 为撤钉前
    分辨率态构建，分辨率已证等价〕；rust-workspace 生成物=测量
    工件非部署件——**零重建项维持**（021 同款观察）。批量回归=
    本仓无 .last-batch-regression 机制不适用〔021 同录〕。

## 10. 待澄清事项

- **B-1 供⑧/供⑨（执行期新增上游缺口——T-01/T-03 实证，非用户裁定项；上游清偿路径登记随 SD-06 供料档 §8）**：供⑧=9920 `auto.diff_files_window` VM codegen 裸名臂缺失〔codegen.rs intrinsics 表三 diff 面无 window 登记——VM 轨 HTTP 调用线程挂死实测；a2r 轨双臂已交付，下游 L2 判定面不受累〕；供⑨=9918/9919 帧通道 .at 消费面双缺口〔VM 轨 i64→int 桥退化——shim 真值实测但 .at 赋值落 0/.str()→None/json→0，time 族同根因[PLAN-005]；a2r ui_gen handler 臂不路由 frame 二段名——regen E0425 实录〕。**T-03 帧两行判定面 blocked 待供⑨ 清偿**；供⑧ 下 L0 VM 形 diff 维持全量旧径（零扰动）。unblock 动作=上游 stdlib/shim/codegen 三面补臂（供料档 §8 验收形态建议随附）。
- **Q-1 diff 窗口 limit 定值（无需裁定，确认口径）**：默认=600
  （对齐 front 渲染 cap——011 口径；首屏语义）；若用户偏好 1000
  余量或其他值，执行前示知——T-00① 按默认定参。
- **Q-2 type_latency 判定口径（无需裁定，确认口径）**：默认=帧内
  口径（present−begin——通道原生可判）；input→present 全链口径
  （含事件派发段）作为注记数字并列在档不判定；若用户希望全链
  口径为判定面（更严——含 MCP 驱动路径噪声），执行前示知。
- **Q-3 供③ 销账回写路径（执行期定）**：P716-D1 记在 auto-lang
  KNOWN-DEBT——本仓多跑证据的回写=跨仓文档注记；若上游档不可直
  书（并行会话在途），fallback=本仓 evidence 入档+upstream 供料
  档登记节（回写建议随附）——T-06 按执行期仓态择路。
