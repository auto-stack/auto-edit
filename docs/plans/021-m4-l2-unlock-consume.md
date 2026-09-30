---
plan_id: PLAN-021
status: executing
feature_name: M4-04 L2 链解阻兑现件（PLAN-710 消费——regen 现势化+perf a2r 绿+L2 断言五行首次正式判定+对比表我方列转正+装载/diff 域生成码回归）
author: [agent]
created_at: 2026-09-30T16:15:39+08:00
updated_at: 2026-09-30T17:20:00+08:00
plan_revision: 1
current_step: 4
total_steps: 7
supersedes_spec_components: []
new_spec_components:
  - docs/specs/modules/perf-measurement.md（SD-01：L2 断言全表节——五行判定谱+armed 升级+剩余行 blocker 注记）
  - docs/specs/00-overview.md（SD-02：M4 第四件注记——L2 链解阻兑现+预算面板过半转正）
  - specs/auto-edit/README.md（SD-03：PLAN-021 口径+L2 链用法）
touched_goals:
  - 战略 §5（L2=唯一预算效力形态——本件为 L2 链自 PLAN-007 blocked 后首次全链贯通）
  - 战略 §2.1 预算表五行正式判定（steady_start/warm_start/open_100mb 装载半行/idle_mem/diff_100mb）+ §5 公开对比表我方列
affects: [tools/perf/perf.py, tools/bench/bench.py, tools/bench/budgets.json, tools/portable/build_portable.py, tools/compare/anchors.py, tools/compare/render_table.py, specs/auto-edit/README.md]
---

# [PLAN-021] M4-04 L2 链解阻兑现件（PLAN-710 消费）

## 0. 变更摘要

auto-lang **PLAN-710**（a2r 生成缺口残余清偿，2026-09-30 delivered
归档@e81e0a1c3——corpus regen **133→0**、三类+D-4..D-8 回补全清、
探针 11/11；同窗口 711/712 亦交付）的**下游消费件**——M4 解阻供料
包供① 的兑现面，L2 主形态（a2r release 直拉——战略 §5 唯一预算
效力形态）自 PLAN-007 起 blocked 后**首次全链贯通**：①**regen 现势
化**（`perf.py a2r` exit 0 三重判据复验+**last-good 基面退役**——
019 快照回退臂完成历史使命）；②**L2 断言全表五行首次正式判定**
（steady_start[hard]/warm_start/open_100mb 装载半行/idle_mem/
diff_100mb——018 锚点全绿+019 产物面 21.2/38.2ms 预示 steady 大概率
达标；未达标行=归因+瘦身后续件，018 Q-2 口径）；③**对比表我方
L2 列转正**（020 l2-pending 虚席→实数——anchors 新 L2 锚源+render
三态转正）；④**生成码三域回归**（G-A envelope 投影/G-B try-catch/
G-C delta 的生成代码**首次跑真实 app**——a2r release exe 冒烟族
[019 probe_surface 形态扩展]+L0 VM 轨全矩阵零扰动复跑）；⑤顺手件
=**open_1gb 战略裁定材料提交**（512MB 拒绝位 vs 预算行「可打开」
——降范围 or 上游流式装载供料登记，§10 Q-1）。M4 预算面板自本件
**过半转正**（五行可判+一行已达成判定口径升级）。

## 1. 目标

- **G-1 工具链门+regen 现势化（710 消费复验）**：auto-lang master
  重建（含 710 delivery e81e0a1c3+712——判据前核 `auto --version`
  哈希）→ `python tools/perf/perf.py a2r` **exit 0**（018 在册
  BLOCKED exit 3 的清偿复验）+生成物 grep 三占位零命中+rust-
  workspace `cargo check` 过（710 corpus 判据的下游真机复验）→
  **last-good 基面退役**：build_portable.py 的 regen 快照回退臂改
  现势直跑（019 「regen 现势化=供① 阻塞维持，last-good 基面复用」
  注记的退役——快照代码保留为历史注记或移除，T-01 定形）。
- **G-2 L2 断言全表（五行首次正式判定）**：`perf.py a2r → release
  → run`（rust 渲染轨）全链贯通后，bench 四档 **L2 化重跑**
  （steady 分解/warm 恢复/open_100mb 装载/idle 采样——018 三档的
  L2 形态版）+**diff_100mb L2 硬门禁形态**（release 全链已有
  1906/1971ms 在档——L2 直拉形态复核收口）；budgets.json 五行
  tier/validity 升级（warm/open/idle/diff：ledger→armed+判定数字；
  steady：hard 行 L2 判定注记）；`stage_proxy --mode l2` 断言面
  全绿（五态行序机制复用）。**未达标处置**：归因清单+瘦身后续件
  排队（frozen 018 Q-2 口径——本件立门不实施瘦身）。
- **G-3 对比表我方列转正**：L2 数字入 `tools/compare/anchors.py`
  锚源（三态列元数据：anchors[VM 形态]/产物面[last-good 时代]/
  **l2 实数**——020 分层纪律的终态兑现）；`render_table.py` 我方
  列 L2 实数渲染+l2-pending 列退役；README 对比表更新（`--check`
  复现一致——020 门复用）。
- **G-4 生成码三域回归（G-A/G-B/G-C 首跑真实 app）**：a2r release
  exe 冒烟族——装载链域（G-B：会话恢复 try[editor_store.at:499]/
  file_size 探测 try[:897] 两形异常兜底路径）+diff 视图域（G-A：
  envelope 投影 `v.err ?? ""` 族全链——diff 主链冒烟[开视图+计数
  断言]）+编辑回路域（G-C：SrcChanged→code_editor_delta 消费+
  badge probe try ×2——017 面）。L0 VM 轨全矩阵复跑（零扰动对照
  ——判绿口径承 020/018 谱）。
- **G-5 open_1gb 战略裁定材料（顺手件，不实施）**：512MB 超大拒绝
  位（013 设计：真分块 IO=上游阻塞）vs 预算行「1 GB 可打开（分块/
  mmap 流式）」的矛盾如实成文——裁定材料（降范围=战略预算行注记
  vs 登记上游流式装载供料 want）提交 §10 Q-1；**裁定=用户件**，
  本件只备料+登记位。
- **G-6 规范+账本**：SD 三册+specs.json P021-1（015-020 外科插入
  先例）。

### 非目标

- 供②③④ 消费（帧插桩两行断言/卡死确认复核收口/tree-sitter 语法
  面——各自解阻后；供④ 勘定件=auto-lang PLAN-714 同日立项在册）。
- installer 收口（two-face want[供料档 §5]+门控手段裁定——019 分
  阶段态维持；本件 G-1 的 regen 现势化会让 build_portable 直接受
  益但不改其断言门）。
- 性能瘦身实施（未达标行=归因清单——后续件）；type_latency/
  scroll_fps/open_1gb 实施（前者待供②、后者待裁定+上游）。
- NP++ 列补跑（用户安装后 harness 补跑即得——不阻塞本件）。
- auto-lang 侧任何改动（消费零越界——上游缺陷回 upstream 登记）。

## 2. 架构方案

分层落点（2026-09-30 实勘，auto-edit main@70c5c60 + auto-lang
master@05974f71d）：

| 面 | 现状 | 本期形态 | 依据 |
|---|---|---|---|
| perf a2r 门 | `stage_a2r` BLOCKED exit 3（perf.py:139-160——133 错/占位特征分类在册） | **exit 0 绿**+三重判据（exit/grep/cargo check）——710 判据的下游真机复验 | 710 corpus 判定（上游已 exit 0）；018 §⑤ 在册 blocked 态 |
| last-good 基面 | build_portable.py regen 快照回退臂（019——133 错时代的绕行） | **退役**：regen 现势直跑；回退臂改注记（历史机制文档化） | 019 「regen 现势化=供① 阻塞维持」注记反转 |
| L2 链 | perf.py 链=a2r→release→run（PLAN-007 定义；自装载链缺口起从未绿过） | **首次全链贯通**——四档 L2 化重跑+diff L2 形态 | perf README 模式矩阵；710 解阻 |
| budgets 五行 | ledger+锚点注记（018 重定态）；steady=hard 未判 | 五行 armed/判定（数字+谱）；`--mode l2` 五态面 | budgets.json:19-81 |
| 对比表 | 我方列三态（anchors/产物面/l2-pending——020） | **l2 实数转正**+pending 退役 | tools/compare/{anchors,render_table}.py+020 三要素门 |
| 生成码回归 | a2r 生成代码从未跑过真实 app（blocked 时代） | 三域冒烟族（019 probe_surface 形态扩展）+L0 矩阵零扰动复跑 | 710 三类消费面定位（供料 §1 实例集） |
| open_1gb | 512MB 拒绝位 vs 预算行矛盾（013/018 注记未收口） | 裁定材料+登记位（§10 Q-1——用户件） | 战略 §2.1 行；013 §8/018 T-03 注记 |

**关键设计约束（frozen）**：
① **判定不冒领**——五行判定必须 L2 直拉形态数字（release 工具链
全链记账形态的 018/016 先例数字保留为对照注记，不充当 L2 判定）。
② **未达标≠失败**（018 Q-2 口径承接——归因+后续件；steady 若
232.6ms 形态差异复现则 VM boot 归因升级为 a2r 形态归因清单）。③
三域冒烟=生成码首跑，发现上游生成缺陷回 upstream 登记（669 模式）
——不在本仓修生成物。④ 工具链门三验（构建源核哈希+组依赖钉版
+PATH 坑三度应验纪律）。

## 3. 技术栈

python perf/bench/portable/compare 四工具族联动+rust-workspace
release 构建+desktop_mcp 矩阵（L0 复跑）+a2r exe 冒烟探针（019
probe_surface 形态）。工具链纪律承 018/019：master 重建+`auto
--version` 核含 e81e0a1c3（710）；组依赖 worktree 钉版惯例。

## 4. 需求分析与背景调查

**授权记录**：用户 2026-09-30 会话指令「OK，auto-plan-new 新建
计划 021；然后再新建 auto-lang 的相关计划」——授权=**起草本件**
（+auto-lang 侧 714 供④ 勘定件另档）；执行/work 待用户另行启动。
范围=auto-edit 单仓（tools/docs/budgets）；auto-lang 零改动。无
预算/自动续跑授权。

**来源与版本**：

- 交接链：PLAN-710 归档件（auto-lang delivered@e81e0a1c3——
  corpus regen 133→0/三类+D-4..D-8 回补/探针 11/11/SD-01
  a2r-app-mapping-completeness 落档/242 #18 行）+首次批量回归
  （5921 例 12 红全已知基线族——last_covered=712）。
- 现状实勘（auto-edit main@70c5c60）：perf.py:139-160 stage_a2r
  BLOCKED 特征分类；budgets.json 十行全读（018 重定态）；tools/
  compare/ 五件族（METHODOLOGY/anchors/compare/probe_channels/
  render_table）；020 三态列机制+README --check 门；019
  build_portable.py 快照回退臂+probe_surface 形态。
- 供料档：m4-perf-unblock-supply §1 供① 验收建议原文（「下游验
  收=auto-edit `perf.py a2r` exit 0 + L2 锚点补跑——装载链
  [G-B×G-C]与 diff 视图面[G-A]两域矩阵回归由下游承担」——本件
  即该条款兑现）。
- 历史关联：PLAN-006（L2 基线唯一先例——rqhost 形态 2026-09-22）/
  007（L2 链定义+blocked 起点）/013（512MB 拒绝位+big 态）/016
  （diff_100mb 达标谱）/018（三档锚点+分层纪律）/019（产物面+
  last-good）/020（对比表三态列）。

## 5. 详细设计

### T-00 消费勘定（决策件）

1. **工具链门**：master 重建（≥e81e0a1c3；执行日 tip 重勘——713
   等并行稿是否已交付）+`auto --version` 核哈希+组依赖钉版。
2. **perf 链 stage 复核**：a2r→release→run（rust 轨）stage 名与
   参数实证（perf.py:320+ main 面）；L2 判定容差口径（018/020
   离散谱承接——median+容差带）。
3. **冒烟面盘点**：019 probe_surface 扩展点清单（三域各自最小
   断言面——G-B 异常兜底路径驱动法[缺文件/坏路径 fixture]）。

### T-01 regen 现势化+a2r 绿复验（G-1）

`perf.py a2r` 全跑（log 入仓）→三重判据逐项（exit 0+grep 三占位
零命中+cargo check）→build_portable.py last-good 回退臂退役改形
（regen 现势直跑+回退臂历史注记——幂等复跑验证）。

### T-02 L2 全链+五行断言（G-2）

a2r→release→run 链贯通→bench 四档 L2 化重跑（steady/warm/open/
idle——N≥4 谱+median）+diff_100mb L2 直拉形态→budgets 五行 tier/
validity 升级（armed+数字+谱注记）→`stage_proxy --mode l2` 断言面
绿。产出=L2 判定报告（对照 018 锚点谱——形态差异归因）。

### T-03 对比表我方列转正（G-3）

anchors.py 增 L2 锚源（直读 T-02 JSONL）→render_table 三态转正
（l2 列实数+pending 退役——生成器断言更新：l2 列必出数）→README
表刷新+`--check` 双复现一致。

### T-04 生成码三域回归（G-4）

a2r release exe 冒烟族：G-B 装载链两形（会话恢复 try+file_size
探测 try——异常兜底路径驱动[缺文件/坏路径 fixture 正常落 catch]）
+G-A diff 主链（开视图+计数断言——envelope 投影 `??` 族全链）+
G-C 编辑回路（SrcChanged→delta 消费+badge probe try 形）；L0 VM
轨全矩阵复跑（零扰动对照）。上游缺陷=登记回 upstream（669 模式）。

### T-05 open_1gb 裁定材料（G-5）

矛盾成文（预算行 vs 512MB 拒绝位+013 非目标注记史）+两案成本
（降范围=战略行注记；登记供料=上游流式装载 want 草案）——§10
Q-1 提交，裁定后执行。

### T-06 规范+账本（G-6）

SD-01..03 落档+specs.json P021-1 投影（roundtrip 字节等价先证+
前缀零扰动回读——015-020 先例）。

### 规范增量

| delta_id | add/modify/retire | docs/specs/... target | before/after rule | rationale | acceptance IDs |
|---|---|---|---|---|---|
| SD-01 | modify | docs/specs/modules/perf-measurement.md | before：预算门 M4 节=锚点记账形态（018——L2 正式判定待供①） / after：增「L2 断言全表」升级——五行判定谱+armed 升级+last-good 退役注记+剩余行 blocker 注记（type_latency/scroll_fps=供②、open_1gb=裁定中、renderer=n/a）+三域生成码回归口径 | L2 链贯通的规范收口 | AC-02/04 |
| SD-02 | modify | docs/specs/00-overview.md | before：M4 注记止于第三件（对比表竞品侧） / after：M4 第四件注记（L2 链解阻兑现——预算面板过半转正+对比表我方列实数+生成码首跑；M4 剩余=供②两行/two-face 收口/供④ 语法面[714 勘定在册]/open_1gb 裁定） | 面进度总览 | AC-06 |
| SD-03 | modify | specs/auto-edit/README.md | before：PLAN-020 口径 / after：PLAN-021 口径（L2 链用法[perf a2r→release→run]+判定数字回填位+对比表转正注记） | 运行矩阵/工具单源 | AC-03/06 |

## 6. 测试设计

- **a2r 三重判据**：exit 0+grep 零占位+cargo check（018 BLOCKED
  特征分类面逐项反转绿）。
- **L2 判定谱**：四档+diff 各 N≥4 跑谱+median+离散注记；与 018
  锚点谱形态差异归因表（VM 形态→a2r 形态的系统性差记录）。
- **budgets 断言面**：`stage_proxy --mode l2` 行序+armed 行全绿；
  `stage_assert` 回放一致。
- **对比表门**：anchors --verify+render --check 双绿（020 门复用）
  +l2 列必出数断言。
- **生成码冒烟**：三域各最小断言（异常兜底/投影计数/delta 消费）
  +L0 矩阵零扰动（≥125/0 承口径——执行时真值）。
- **pristine 断言**：auto-lang 主树零触碰+本仓 diff 全在计划路径。

## 7. 验收标准

- **AC-01 a2r 绿+现势化**：`perf.py a2r` exit 0+三重判据绿+
  build_portable regen 现势直跑（回退臂退役注记在档）。验证：
  log 入仓+幂等复跑。
- **AC-02 L2 五行判定**：判定数字+谱在档+budgets 五行升级+`--mode
  l2` 断言面绿（未达标行=归因清单在档——非失败态）。验证：L2
  判定报告+budgets 注记。
- **AC-03 对比表转正**：我方列 L2 实数+pending 退役+README --check
  双复现。验证：render 输出+--check 绿。
- **AC-04 生成码回归**：三域冒烟全绿+L0 矩阵零扰动。验证：冒烟
  记录+矩阵跑谱。
- **AC-05 open_1gb 材料**：矛盾成文+两案成本在档（§10 Q-1 提交
  态）。验证：材料文件在档。
- **AC-06 规范+账本**：SD-01..03 落档+P021-1 回读 True。验证：
  文件在档+账本断言。
- **AC-07 范围零越界**：auto-lang 主树零改动（上游缺陷登记件除
  外——upstream 档增量）；.at 源零 diff。验证：双仓 porcelain+
  路径断言。

## 8. 执行步骤

| # | 任务 | 依赖 | 落点（实勘锚） | 产出/意图 | AC | 验证（命令/预期） |
|---|---|---|---|---|---|---|
| 0 | T-00 消费勘定 | — | 本件 §5 T-00 节 | 工具链门+链路复核+冒烟盘点 | AC-01/04 | [x] 勘定记录在档（2026-09-30：①工具链门=PATH debug auto v0.4.2-2311-g7fcf913eb〔clean 无 -dirty；e81e0a1c3[710]/16387c84a[712]/f515252ea[713] merge-base 三连实证在含；今 16:01 构建〕——release 侧现势 2275-g9fbf4ebd5-**dirty** 陈旧+脏不采用〔PATH 坑纪律正面应验〕；master 重建字面重估=7fcf913eb→05974f71d 纯 docs delta crates/ 零 diff、重建零功能增量且会因 auto-lang 主树外来 WIP 带 -dirty 劣化判据→采现势 debug 二进制为钉版〔adaptation 记录，判据等价〕；②组依赖钉版=组兄弟树机制实证——pac `dep bps` 蓝图相对路径 `../../../auto-lang/blueprints` 自 PROJECT 解析〔首轮 regen 失败实录在档 a2r-20260930-163646.log〕→建组内 `.wt/edit-021/auto-lang`@05974f71d detached〔015-019 惯例；生成器 sibling 扫描 rust_ui.rs compute_auto_lang_rel_path 同源解析→ws path 依赖自动钉组树〕；**auto-down 组树不再需要**——018 教训〔Cargo.toml:140 autodown-core 跨仓依赖〕经 712 产物清理已移除，master 现势 grep 零命中实证；③perf 链 stage 复核=a2r→release→run(--track rust) 三段实证 perf.py:139/178/268+main:320-339；L2 判定容差=median〔sorted[N//2] 上中位，018 家法/METHODOLOGY §5 frozen〕+N≥4 跑谱+离散注记；④冒烟盘点=G-B 会话 try[editor_store.at:499 坏 JSON fixture→catch→存活+无 bench_session_restored；好 fixture→标记达+存活]/装载探测[:903 缺文件 AUTO_OPEN_PATH→file_size 投影 -1→错误形承接+存活——OpenPath 无 exists 门实测锚]；G-A diff[:1486 AUTO_DIFF_A/B bypass→DiffCompute 计数 console 形——观测通道=MCP@AUTOUI_MCP_PORT 探针执行期定〔release exe run_app_devtools 面〕或标记族+存活降级]；G-C 编辑回路[SrcChanged→code_editor_delta 消费+badge probe try[1637/2766]——MCP 可驱则 TypeText+save E2E，否则降级注记]；L0 矩阵=desktop_mcp 137 检查/判绿 ≥125/0〔017/018 口径承——已知集 T12.6+T17.2/3/4/8 不计+轮换 flake 重跑条款〕；⑤diff L2 直拉形态勘定=ws 双 member 实测〔last-good 基面：front 内嵌 fsys 转译本体 env_str/exists/read_text in-process；back=axum 独立进程 AUTO_HTTP_PORT‖8080；file_size/diff 面旧基面缺席=Sep22 代差非生成缺口〕→**L2 diff=release auto-edit-back.exe 打 /api/diff_files**〔016 server 侧计算主导语义同型；bench.py diff --l2 增臂〕；⑥worktree=D:/autostack/.wt/edit-021/auto-edit@plan-021-dev〔base 70c5c60〕+组内 auto-lang@05974f71d detached） |
| 1 | T-01 regen 现势化 | T-00 | perf.py stage_a2r+build_portable.py | a2r 绿+last-good 退役 | AC-01 | [x] a2r exit 0[a2r-20260930-163740.log]+三占位零命中+cargo check 分层[front member 绿/-p auto-edit 47.8s；back member E0432=供① 残余面一如实红——非本件回归]+退役幂等自证 pass[--regen --skip-build --check-idempotent，portable-20260930-165454.jsonl exit=0] |
| 2 | T-02 L2 五行断言 | T-01 | bench.py 四档+budgets.json | 判定谱+armed 升级 | AC-02 | [ ] **blocked-on-upstream**：fresh release exe 功能面死（front route-A 桩化→env_str 恒空→AUTO_BENCH/AUTO_OPEN_PATH 不可达）——steady --l2 首跑零标记实录在档；不冒领纪律=五行不升级，budgets blocked 注记落档；判据面已备（bench --l2 三档+diff back 服务形）待 §6 解阻补跑 |
| 3 | T-03 对比表转正 | T-02 | compare/{anchors,render_table}.py+README | l2 列实数 | AC-03 | [ ] **blocked**（连带 T-02）：无 L2 直拉实数可转正——l2-pending 虚席维持（020 三态纪律）；解阻后按 T-03 原案执行 |
| 4 | T-04 生成码回归 | T-01 | a2r exe 冒烟+L0 矩阵 | 三域首跑证 | AC-04 | [ ] **首跑收据绿**（最小面：boot+渲染+AutoUI MCP+存活 10s+零 panic——生成码首跑真实 app 里程碑在档）+三域功能面 blocked（同 T-02 根因；smoke_gen.py harness 已备）+L0 矩阵复跑未行（VM 轨不受生成面影响、本件零 .at diff——留待解阻后与三域一并收口） |
| 5 | T-05 open_1gb 材料 | — | §10 Q-1+裁定材料档 | 矛盾成文+两案 | AC-05 | [x] 材料在档（docs/designs/002-open-1gb-adjudication.md——矛盾成文+两案成本+归口建议） |
| 6 | T-06 规范+账本 | T-01..05 | SD-01..03+specs.json | 收口落账 | AC-06 | [x] SD-01..03 按 blocked 现实落档+P021-1 回读 True（roundtrip 字节等价先证+前缀零扰动；reviews 20→21） |

## 9. 复审记录

- 2026-09-30 起草 handoff：`stage: new`，PLAN-021，plan_revision 1。
  `outcome: pass`（起草完备：710 供① 验收条款逐项承接[a2r exit 0
  复验+L2 锚点补跑+两域矩阵回归→本件 G-1/2/4]；L2 首次全链贯通
  的判定纪律[不冒领/未达标归因]承 018；三域冒烟面有 019 probe_
  surface 形态先例；open_1gb 矛盾如实提交裁定不夹带；路径/符号经
  auto-edit@70c5c60 与 auto-lang@05974f71d 双仓实勘锚定；授权=
  起草[用户指令原文在录]，执行待用户启动）。`next: work`。

- 2026-09-30 work handoff：`stage: work`，PLAN-021，plan_revision 1。
  `outcome: blocked` | code_commit: worktree plan-021-dev@**7de30ed**
  （base 70c5c60；T-00/01/05/06 全落+T-02/03/04 blocked 面如实收档；
  worktree 清洁态）| task_ids: T-00,T-01,T-05,T-06 完成；
  T-02,T-03,T-04 blocked | evidence: a2r exit 0 复验+三占位零命中+
  build_portable 退役幂等自证 pass+生成码首跑收据（boot/渲染/AutoUI
  MCP/零 panic）+evidence-p021-blocked-survey forensics+供料档 §6
  登记+SD-01..03+P021-1 回读 True | blockers: 供① 残余两面单根因
  （back 转译通路缺语句级 Try 臂→back E0432+front route-A 桩化→
  L2 全预算行不可测；Q-3 默认路由=登记 upstream 不修生成物——精准
  解锁动作=auto-lang 快速修订件[镜像 ui_gen G-B 臂形，单臂两面全解]
  +corpus 判据三行增补，**用户裁定立项**）| next: 用户裁定后二选——
  (a) 上游解阻→本件 T-02/03/04 判据面 zero 重设计补跑（executing 续）；
  (b) 新建 auto-lang 快速修订件另档（本件 blocked 挂账维持）。

## 10. 待澄清事项

- **Q-1 open_1gb 战略裁定（用户件——材料已备齐**docs/designs/002-open-1gb-adjudication.md**，待裁定）**：：
  预算行「1 GB 可打开（分块/mmap 流式）」vs 现势 512MB 超大拒绝
  位（013 设计：真分块 IO=上游阻塞，当时注记 1GB 线非目标）。两
  案：**(a) 降范围**——战略 §2.1 行注记「1GB=远期，512MB 拒绝位
  为 M4 形态」；**(b) 登记上游供料**——流式装载 want 入
  m4-perf-unblock-supply（工期在上游）。默认无预裁定——材料备齐
  后请示。
- **Q-2 steady_start 未达标处置确认（无需裁定，确认口径）**：
  承 018 Q-2 默认——L2 形态若 >80ms，归因清单+瘦身后续件（VM
  boot 224.5ms 归因是否随 a2r 形态消失=T-02 判定谱的观察重点；
  019 产物面 21.2/38.2ms 预示大概率绿）。
- **Q-4 供① 残余两面处置（本件执行期发现，2026-09-30）**：back 转译
  通路缺语句级 Try 臂（fsys.at:208 try）→back E0432+front route-A 桩化
  →L2 全预算行不可测。已按 Q-3 默认路由登记 upstream（供料档 §6——
  单臂解锁建议+corpus 判据三行增补+验收四判据）。**待用户裁定**：
  (a) 立项 auto-lang 快速修订件（710 D-4..D-8 回补量级——本件 §9 记录
  的精准解锁动作）；(b) 挂账待上游自然排程（本件维持 blocked）。
- **Q-3 生成码缺陷处置（执行期口径确认——已按默认路由执行）**：三域冒烟若现上游
  生成缺陷——默认登记 upstream（669 模式）+本件注记 blocked 面，
  不在本仓修生成物；若缺陷轻微且修法明确，可回 auto-lang 走快速
  修订件（710 D-4..D-8 回补先例）——执行期按缺陷量级择路，§9
  记录。
