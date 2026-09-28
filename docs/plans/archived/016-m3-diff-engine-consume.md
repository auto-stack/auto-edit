---
plan_id: PLAN-016
status: executing
feature_name: M3-04 diff 引擎消费件——替换缝兑现（fsys 实现体换内核直调+上限门全套退场+diff_snapshots 缓冲区比较 v1+100MB bench 真跑）
author: [agent]
created_at: 2026-09-27T21:26:58+08:00
updated_at: 2026-09-28T03:40:00+08:00
plan_revision: 1
current_step: 8
total_steps: 8
supersedes_spec_components: []
new_spec_components:
  - docs/specs/modules/diff-view.md（SD-01：引擎时代节——过渡计算层退役注记/上限门节重写/缓冲区比较节新增）
  - docs/specs/modules/back-api.md（SD-02：diff_buffers 第 15 端点节+diff 实现体 native 直调注记）
  - docs/specs/00-overview.md（SD-03：M3 第四件注记）
  - specs/auto-edit/README.md（SD-04：PLAN-016 口径——判绿重定/工具链门/组依赖）
  - docs/strategy/002-north-star-v2.md（SD-05：§2.1 预算表 diff 行解锁注记——供料包回执条款）
  - docs/upstream/2026-09-diff-engine-supply.md（SD-06：消费回执节——014 §17 先例格式）
touched_goals:
  - 战略 §2.1 预算行「100 MB 文件全量 diff 出结果 ≤ 2 s」（解锁条件=diff 引擎——本件兑现判定）
  - 战略 §2.3 M3 验收面「与编辑缓冲区比较」（diff_snapshots 解锁件）+ 算法行「histogram/patience 优先，大文件分块并行」（引擎时代达成）
affects: [specs/auto-edit/src/back/fsys.at, specs/auto-edit/src/back/api.at, specs/auto-edit/src/front/editor_store.at, specs/auto-edit/src/front/app.at, specs/auto-edit/tests/desktop_mcp.py, specs/auto-edit/tests/probe_diff.py, tools/bench/bench.py, tools/bench/budgets.json]
---

# [PLAN-016] M3-04 diff 引擎消费件（形态 B 消费侧兑现）

## 0. 变更摘要

auto-lang **PLAN-703 diff 引擎供料包**（五件，2026-09-27 delivered 归档，
delivery commit **46efa926a**，master tip b84d9d8f2）的**下游消费件**——
PLAN-703 §4 回执预记点名的「diff 引擎消费件」：**替换缝兑现**（back
`fsys.diff_files_json`/`diff_dirs_json` 实现体换 native 直调——PLAN-011
声明的「仅换实现体，envelope/视图零改动」承诺在本件兑现）→ **上限门
全套退场**（1MB 尺寸门/10k 行门/DP-200 降级/桶积 700k 四门随实现体替换
消亡；degraded 恒 false；front 渲染 cap 600 保留）→ **diff_snapshots
缓冲区比较 v1**（编辑中缓冲区对打——hunk 净形视图+跳转，011 边界注记
「零全文 tab 铁律的正解」落位）→ **100MB bench 档真跑**（战略 §2.1
预算行 ≤2s 判定——L2 性能模式唯一有预算效力的口径，703 Q-2 承接）。
每面独立可验；**golden/矩阵期望按证据同步**（引擎 histogram 与过渡
DP-LCS 在 corner 形可能漂移——逐字段 diff 在档重定，非静默放宽）。

## 1. 目标

- **G-1 替换缝兑现（文件 diff）**：`fsys.diff_files_json` 过渡实现
  （~200 行朴素分层，fsys.at:262-约 470）退役为 native
  `diff_files(path_a, path_b, ctx)` 裸名直调（9915）；envelope 契约
  零变化（12 字段 rows/hunks 0 基半开/CR 容忍/err 形——上游 SD-03 逐
  字段同形交付）；`api.at`/`editor_store.at`/`app.at` diff 既有路径
  **零改动**（缓冲区比较=纯新增面）。
- **G-2 上限门退场（文件 diff）**：1MB 尺寸门/10k 行门随实现体替换
  消亡——超限文件从 err 拒转为正常出结果；DP-200 降级退场（**degraded
  恒 false**——引擎时代无降级语义，上游成文）；矩阵 T15.9（>10k 拒绝）
  /T15.10（degraded 截断）期望**翻转**。front 渲染 cap 600+truncated
  注记保留（显示域截断，非计算域）。
- **G-3 替换缝兑现（目录 diff）**：`fsys.diff_dirs_json` 过渡实现
  （~250 行，fsys.at:803-约 1050）退役为 native `diff_dirs` 直调
  （9917）；五态分类/counts 同域/skip-list/>2MB 同尺寸「同(未比对)」
  注记**行为保持**（上游 SD-03 明文保持下游可见态）；对齐长度桶+
  桶积 700k 护栏退场（对齐在 Rust 侧——同长巨桶目录正常出结果）。
- **G-4 缓冲区比较 v1（diff_snapshots 解锁）**：back 第 15 端点
  `diff_buffers(key_a, key_b)`（#[api] GET → fsys 转发 native
  `diff_snapshots` 9916——buffer registry 直读，零全文 VM 往返）；
  front 入口（工具菜单「比较缓冲区…」）+ hunk **净形**视图（rows:[]
  ——计数+hunk 位置列表，envelope 净形口径上游成文）+ 跳转（切 tab+
  `code_editor_set_cursor` 014 消费先例）；env 旁路 `AUTO_DIFFBUF_A/B`
  （矩阵驱动面，011/012 Tick 消费先例）。
- **G-5 100MB bench 真跑**：bench `diff` 档扩 **100MB 散点改档**（生成
  式合成对——与上游 T-04 基准形态对齐）；budgets.json `diff_100mb`
  从 blocked-upstream 解锁为实测判定（**≤2s=L2 唯一预算效力**）；门拒
  档（over_size/over_lines）从「门拒延迟证明」改造为「通过延迟证明」。
- **G-6 期望同步与判绿重定**：golden 六形态对账（引擎 envelope vs
  probe_diff ②python 参考——漂移逐字段证据在档）；矩阵判绿口径重定
  （承 015 blocked 集：T12.6+T17.2/17.3/17.4/17.8——大文件实例 UI
  卡死上游回归与本件 diff server 链无交集，口径原样承接）。

### 非目标

- **差异侧直接编辑重比**（战略 §2.3 完全体项）——建基于本件缓冲区
  比较面的大 UX 件，另行立项（M3 收口剩余=本项+语法高亮联动）。
- 语法高亮联动（tree-sitter 门控——M3 完全体剩余项另裁）；3-way merge/
  双向同步向导（战略 §9-Q5 开放问题）；十六进制比对（下游非目标传导）。
- >2MB 同尺寸 uncompared 升级为字节级比对（上游注记「矩阵行为变更为
  后续件」——本件保持注记态）；mtime 快路开启（上游 opt-in 默认关，
  parity 风险注记——行为零变化）。
- vue 轨缓冲区比较（浏览器轨无本地 editor registry——v1 注记不涉）；
  100MB **全异形** envelope 巨串治理（rows 全量投影=上游 v1 形——观察
  件登记，非本件）。
- auto-lang 侧任何改动（供料已 delivered；发现上游缺陷回 upstream 登记
  新供料/修订件，不在本仓修）。

## 2. 架构方案

分层落点（2026-09-27 实勘，auto-edit main@f74542d + auto-lang
master@b84d9d8f2）：

| 面 | 现状 | 本期形态 | 依据 |
|---|---|---|---|
| fsys.diff_files_json | 过渡朴素分层全内联（公共前后缀裁剪→≤200 行 DP-LCS→大中段降级 replace→索引对齐配对+三段→ctx 切 hunk，fsys.at:262 起约 200 行；门 0 存在性+门 1 尺寸 1MB+门 2 行数 10k） | **纯转发** `return diff_files(path_a, path_b, ctx)`（native 裸名 9915；ctx<=0 钳 3 上游侧已有；缺文件 err 形上游同形）——过渡实现与三门整体退役，头注改引擎时代消费注记 | PLAN-011 替换缝声明；703 SD-03 envelope 逐字段同形；裸名 intrinsics 实勘（vm/codegen.rs:556） |
| fsys.diff_dirs_json | 全内联（双侧 list_dir 递归+五态分类+长度桶对齐+桶积 700k 护栏+cap 5000，fsys.at:803 起约 250 行） | **纯转发** `return diff_dirs(path_a, path_b)`（9917）——五态/>2MB 注记/cap 5000 上游同形保持；桶形对齐与护栏整体退役 | 同上（SD-03 dirs 节） |
| 上限门 | 尺寸 1MB/行数 10k/DP-200/桶积 700k 四门（T-00 §10 保守定参——VM 步墙代偿） | **四门全退场**（计算域入 Rust；100MB 合成基准上游 0.35-0.9s 在档）；front 渲染 cap 600+truncated 保留（显示域）；「等待内核引擎」err 文案族退役 | diff-view.md 上限门节；703 §4 回执预记「全套退场」原文 |
| 缓冲区比较 | 无（011 边界注记：与编辑中缓冲区比较需全文读出撞零全文 tab 铁律） | back：api.at `diff_buffers`（第 15 #[api]）→ fsys.diff_buffers_json → native `diff_snapshots(key_a,key_b)`（9916，registry 直读，hunk 净形 rows:[]）；front：editor_store `diff_buf_*` 状态族+净形列表视图+跳转（切 tab+set_cursor[014 换算先例]）；入口=menubar 静态 item+env 旁路 AUTO_DIFFBUF_A/B | 011 边界注记；SD-03 snapshots 节；code_editor_save/set_cursor 消费先例（tab.key 键语义同形） |
| bench diff 档 | diff_small/mid（基线墙钟）+over_size/over_lines（门拒延迟+blocked 注记）；budgets.json diff_100mb=blocked-upstream | 扩 **diff_100mb**（100MB 散点改生成式合成对——真跑判定 ≤2s）；门拒档改造为通过延迟档；budgets 解锁注记+实测值回填 | 战略 §2.1/§5；bench.py:345/822-835；703 Q-2 口径（绝对量判定归下游 L2） |
| golden/矩阵 | 六形态 golden=过渡实现产物；T15.9/T15.10 断言门拒/degraded 形 | **期望同步**（对账漂移=逐字段证据重定——011 已知偏差 corner[相邻 hunk b 窗交叠双渲染]预期消失）；检查族结构不变、期望值翻转/重定；新增 T15.16+ 缓冲区子组 | 015 判绿口径承 015 blocked 集；期望同步非静默放宽铁律 |

**关键设计约束（frozen）**：
① envelope 契约=计算层↔视图层唯一接口（011 声明）——本件只换 fsys
实现体，envelope 字段族/视图既有路径零改动（缓冲区比较=独立新面）。
② **裸名落位=fsys.at**：native 裸名 `diff_files`/`diff_dirs` 与
api.at `pub fn diff_files`/editor_store `use back.api: diff_files`
**同名**——转发写在 fsys.at（其内无本地 `diff_files` 符号，仅
`diff_files_json`）天然回避解析歧义；api.at/前端导入名零扰动（T-00
探针复核解析优先级，矩阵 T15.1-15.6 主链兼为回归哨）。③ 键语义=
tab.key（code_editor 族同形；VM 轨 storage_key 前缀 normalize 上游
已勘定）。④ 判绿口径变更仅限本件新增/翻转检查，承 015 blocked 集
原样。

## 3. 技术栈

.at back（VM 轨 native 裸名直调——merged/split 双轨同源，#[api] 生成
器既有惯例）+ front 状态面（store 全承载，013 组件边界）+ python
矩阵/探针/合成 fixture（生成式大件不入库——013 先例）+ bench L2 口径。
**工具链纪律**（014/015 双坑位应验）：判据前必核 `auto --version`
提交哈希**含 46efa926a**（PATH 二进制可能为并行分支构建——86b56884b
不含 701 native 教训）；组依赖 worktree `.wt/edit-016/auto-lang` 钉版
（pac `../../../` 组兄弟解析，014 Q-1b/015 惯例）。

## 4. 需求分析与背景调查

**授权记录**：用户 2026-09-27 会话指令「计划 703 已经在 auto-lang
实施完毕。请继续 auto-plan-new 下一个计划文件」——授权=**起草本件**
（下游消费件——703 §4 回执预记「本件 delivered 后下游立项」点名+015
overview 注记「M3 后续件排期实质由上游承接时序决定」承接）；执行/
work 待用户另行启动。范围=auto-edit 单仓（specs/docs/tools）；
auto-lang 零改动。无预算/自动续跑授权。

**来源与版本**：

- 供料侧：auto-lang PLAN-703 归档件（docs/plans/archive/
  703-diff-engine-supply-pack-v1.md）+ SD 三册（docs/specs/auto-lang/
  ui/design/{rope-subtree-hash,diff-engine,diff-endpoints}.md@master）
  + delivery 提交链（8fd8850a3→…→46efa926a；natives 9915/9916/9917
  注册五面实勘：native_catalog.rs:58-60、vm/codegen.rs:556-558、
  ui_gen/rust.rs:9755-9767）。上游基准：100MB 全形态 0.35-0.9s（压进
  ≤2s 线）+快照 O(1) 快路 10.6µs（相对量在档；绝对量判定归本件 L2）。
- 消费侧现状实勘（auto-edit main@f74542d）：fsys.at:262
  diff_files_json（三门+过渡分层）/fsys.at:803 diff_dirs_json（桶积
  护栏+cap 5000）；api.at:117/131 双端点+#[api] 计 14（第 15 位空闲）；
  editor_store.at:54 `use back.api: … diff_files, diff_dirs`（裸名
  同名面）；desktop_mcp.py T15 组 16 检查（15.9 门拒/15.10 degraded
  截断=翻转面）/T16 组 12 检查（T16.10 >2MB 注记=保持面）；probe_
  diff.py ②python 参考实现（对账基）；bench.py:345 diff_100mb
  blocked+822-835 门拒档；budgets.json:59-66 解锁条款。
- 历史关联：PLAN-011（替换缝声明+上限门 T-00 定参——本件全数清偿）/
  012（目录面+桶积护栏）/015（内联件+「引擎前清单清零」注记——本件
  即其 §10 悬案的承接件）；PLAN-014（形态 A 消费先例——收据格式/
  工具链坑位/组依赖惯例）；669 模式（零/最小改动消费）。
- 在册背景：大文件实例 UI 硬卡死回归（2046→83c4621b5 窗，043/552/
  700/702 期业主）——T17 交互簇 blocked 集承 015；与 diff server 链
  （不开编辑器实例）无交集，本件不受阻、口径原样承接。

**消费预告（回执预记）**：本件 delivered 后 M3 剩余=差异侧直接编辑
重比+语法高亮联动（后续件）；上游新 want（如全异形 envelope 体量/
vue 轨缓冲区面）随执行期实勘登记 upstream。

## 5. 详细设计

### 供料回执（供→消接口对账面）

| 703 供件 | 本件消费位 | 消费形态 | 预期改动量 |
|---|---|---|---|
| 供①a 行级引擎 | fsys.diff_files_json 实现体 | native 裸名直调（envelope 同形） | −200 行过渡实现+1 行转发 |
| 供①b refinement | rows 三段标记（mid 段引擎化） | envelope 直享（100k 字符预算随 VM 步墙退场——refine 恒开） | 零（契约同形） |
| 供② rope 哈希 | （内核内部——引擎剪枝/快照快路） | 间接（性能红利） | 零 |
| 供③ 分块并行 | bench diff_100mb 档 | L2 真跑判定 ≤2s | bench.py 扩档+budgets 解锁 |
| 供④ 目录比对 | fsys.diff_dirs_json 实现体 | native 直调（五态/注记保持） | −250 行+1 行转发 |
| 供⑤ 端点 | 三面全消费 | diff_files/diff_dirs 转发+diff_buffers 新面 | api/fsys/front 三点 |

### T-00 消费勘定决策件（有界调查，决策产物）

1. **工具链门**：master（≥46efa926a）重建 target/debug；`auto --version`
   核哈希含 46efa926a；组依赖 `.wt/edit-016/auto-lang` 钉版建组。
2. **裸名解析探针**：最小 back 探针（probe_diff_app 形态）在 fsys 形
   模块内裸调 `diff_files`/`diff_dirs`/`diff_snapshots`——断言绑定
   native（9915-9917 shim 出 envelope）而非未定义/误绑；api.at 本地
   `pub fn diff_files` 与前端 `use back.api: diff_files` 导入名解析
   零扰动（既有绑定回归哨=T15.1-15.6）。
3. **缓冲区比较消费形定案**：候选 (a) **双已开 tab 比较**（front 持
   两 key 直传——零装载面，默认）；(b) active tab vs 磁盘版（需
   probe 装载面：code_editor_load_file 建 probe key 后 9916——轨形
   实勘[split 态 registry 共享/生命周期]后可采，否则后续件）。手动
   选择形态：v1=面板双 tab 序号输入（dirs 面板输入框先例——select
   组件无现役，实勘 app.at 零用例）。决策产物=本节补记+探针证据。

### T-01 fsys.diff_files_json 替换（G-1/G-2）

函数体整体替换为 native 直调（签名/返回不变）；头注从过渡分层描述
改为引擎时代消费注记（供料回执指向 703/SD-03）；三门与「等待内核
引擎」err 文案族随体退役。**验收眼**：>1MB/>10k 行文件从 err 拒转
正常 envelope（矩阵 15.9 翻转面）。

### T-02 fsys.diff_dirs_json 替换（G-3）

同形纯转发；桶形对齐+桶积 700k 护栏+「对齐超限」err 形退役；五态
分类/>2MB uncompared 注记/cap 5000/truncated 语义保持（上游同形
交付——T16 组复跑全绿即证）。

### T-03 golden 对账+矩阵期望同步（G-6）

probe_diff.py 扩 **⑦引擎对账段**：六形态+内联推导器 ⑥ 输入族+corner
（相邻 hunk b 窗交叠已知偏差形）×引擎 envelope 逐字段对照 python 参考
——漂移逐字段 diff 报告入 evidence（evidence-p016-*.json 先例命名）；
fixtures golden 按证据重定（同步≠放宽：每处漂移有 diff 行在档）。
desktop_mcp.py：15.9 期望翻转（>10k 行通过+计数到位）/15.10 重定
（degraded=false+配对行形状计数替换整块 replace 形）/散点主链 15.1-15.8
+15.11-15.15 复跑（预期零漂移——简单形 histogram≡DP-LCS，若漂移按
对账证据同步）；T16 组全数复跑（保持面）。

### T-04 缓冲区比较 v1（G-4）

- back：api.at 增 `diff_buffers(key_a, key_b)`（GET /api/diff_
  buffers，第 15 #[api]）→ fsys.diff_buffers_json → native
  `diff_snapshots`。envelope：`{hunks:[{a1,a2,b1,b2}], adds, dels,
  rows:[], err}` 净形（上游口径）；缺键 err 形（「编辑器不存在: …」
  上游同形）。
- front：editor_store `diff_buf_open/diff_buf_ka/diff_buf_kb/
  diff_buf_na/diff_buf_nb`（键与显示名）+`diff_buf_hunks/_count/
  diff_buf_adds/diff_buf_dels/diff_buf_err`（净形+计数）+`diff_buf_
  bypass_done`；handler 族：DiffBufOpen（面板开+默认键=active 与次
  tab）/DiffBufCompute（调 back+净形入 store）/DiffBufJump（hunk 行
  点击→切对应 tab+`code_editor_set_cursor(key, line, 0)`[1 基→0 基
  换算，014 先例]）/DiffBufClose（清态+tab 零扰动）。
- 视图：净形列表（行=`L{a1+1}–{a2} ↔ R{b1+1}–{b2}`+双侧缓冲区名
  头+±计数）——独立面板条件面（diff_open/diff 视图互斥，dir_mode
  同款 handler 组维护不变式）；「比较缓冲区…」menubar 静态 item
  （010 四边界内）+action `diff.buf-compare`。
- 矩阵旁路：env `AUTO_DIFFBUF_A/B` 双设 → Tick 消费（011/012 同款：
  双路径装载成 tab→取 key→DiffBufCompute 预填）；单边残缺 console 记
  零动作。

### T-05 bench 100MB 真跑（G-5）

stage_diff 扩 `diff_100mb` 档：生成式 100MB 散点改合成对（~1.4M 行×
散点改，与上游 T-04 基准形态对齐——生成式临时构造不入库，013 先例）；
计时=/api/diff_files 全链墙钟（app `--server vm` 既有形态）；判定
**≤2s**（超限=红——性能是发布门槛）。over_size/over_lines 档改造：
门拒延迟→通过延迟（>1MB/>10k 形真跑）；budgets.json diff_100mb
解锁注记+实测值回填（validity→引擎时代实测）。产出=JSONL+报告数字
回填 SD-05/README。

### T-06 规范增量+账本

diff-view.md：过渡计算层节标注退役（保留历史+指向引擎）、上限门节
重写（四门退场/渲染 cap 保留/门拒 err 文案族退役）、新增缓冲区比较
节（envelope 净形/状态面/入口/跳转/矩阵断言口径）；back-api.md：
diff_buffers 第 15 端点节+计数勘正 14→15+diff 双端点实现体 native
直调注记；00-overview M3 第四件注记；README PLAN-016 口径（判绿重定
数字真值回填）；战略 §2.1 预算表 diff 行解锁注记（变更记录追加——
供料包回执条款原文要求）；供料包文档尾部消费回执节（014 §17 格式：
六供件逐项核销+残留 want）。specs.json reviews 段 P016-1 投影
（015 先例外科插入法）。

### 规范增量

| delta_id | add/modify/retire | docs/specs/... target | before/after rule | rationale | acceptance IDs |
|---|---|---|---|---|---|
| SD-01 | modify | docs/specs/modules/diff-view.md | before：过渡计算层=现役（朴素分层五步+选型依据）；上限门=1MB/10k/DP-200/渲染 600 四门在册；无缓冲区面 / after：过渡计算层节标注**退役**（引擎时代——保留历史口径+指向 703 SD-02/03）；上限门节重写（计算域四门退场+degraded 恒 false+渲染 cap 600 保留）；新增缓冲区比较节（净形 envelope/状态面/入口/跳转/断言口径） | 替换缝兑现落账；011/012 契约面的引擎时代口径 | AC-01/02/03/04 |
| SD-02 | modify | docs/specs/modules/back-api.md | before：#[api] 计 14；diff_files/diff_dirs=fsys 过渡实现体 / after：计数勘正 14→15（diff_buffers 新增节）；diff 双端点实现体=native 直调注记（9915/9917 指向） | 第 15 端点落账；实现体变更登记 | AC-01/03/04 |
| SD-03 | modify | docs/specs/00-overview.md | before：M3 三件注记止于 015（引擎前清单清零+上游承接悬案指 §10） / after：M3 第四件注记（消费件——替换缝兑现/门退场/缓冲区 v1/100MB 判定；M3 剩余=差异侧编辑+语法联动注记） | 面进度总览承接 | AC-06 |
| SD-04 | modify | specs/auto-edit/README.md | before：PLAN-015 口径（125/≥117；工具链 v2156-g1d597e3f4） / after：PLAN-016 口径（判绿重定数字=T-03/T-04 执行后真值回填；工具链门=含 46efa926a；组依赖 .wt/edit-016） | 运行矩阵/判绿单源更新 | AC-06 |
| SD-05 | modify | docs/strategy/002-north-star-v2.md | before：§2.1 diff 行解锁条件=diff 引擎（M3）/ after：解锁注记+实测值（2026-09 引擎时代 ≤2s 判定结果；变更记录追加行） | 供料包「回执方式」条款（README/战略解锁注记） | AC-05 |
| SD-06 | modify | docs/upstream/2026-09-diff-engine-supply.md | before：五件供料无回执 / after：尾部消费回执节（六供件逐项核销+漂移/残留 want——014 §17 格式） | 上下游收据链闭环 | AC-07 |

## 6. 测试设计

- **探针（前置决策门，不入矩阵计数）**：probe_diff.py ⑦引擎对账段
  （六形态+⑥推导器输入族+corner×引擎逐字段 vs python 参考——漂移
  diff 报告入档）；T-00 裸名解析探针+缓冲区消费形勘定（新 probe_
  bufdiff.py 或 probe_diff_app 扩段——净形/缺键/跳转链）。
- **矩阵（desktop_mcp.py）**：T15 组期望同步（15.9 翻转/15.10 重定/
  主链复跑）+新增 **15.16-15.19 缓冲区子组**（旁路自开+净形计数/
  跳转 set_cursor 生效[切 tab+光标位读回]/缺键 err 形/关闭复原+tab
  零扰动）；T16 组全数复跑（五态/下钻/同步动作/注记保持——桶积面
  增同长巨桶目录通过检查）；判绿口径重定（承 015 blocked 集）。
- **golden**：fixtures/diff 六形态按对账证据重定（每处漂移有 diff
  行）；fixtures/dirdiff 五形态预期零漂移（分类语义上游同形——若
  漂移同法证据重定）。
- **bench（L2）**：diff_100mb 散点档 ≤2s 判定+1/10/100 三档数字在档；
  over_size/over_lines 通过延迟改造后绿。
- **双轨**：merged 直调裸串+split HTTP 双层解码既有形态复跑（diff
  双端点）；vue 臂 build-green 复验（014 双 exit 0 基线——本件新面
  为既有 for/if/button 族）。
- **跨仓**：上游 natives 行为=703 交付面（探针 7/0 在档）——本件
  消费侧发现上游缺陷回 upstream 登记新件，不在本仓修。

## 7. 验收标准

- **AC-01 替换缝兑现（文件）**：fsys.diff_files_json=native 直调
  （grep 锚：无 DP-LCS/桶形残留）；envelope 形零变化（探针⑦六形态
  逐字段对账）；api.at/editor_store.at/app.at diff 既有路径零改动
  （diff 行数=0 的 grep 证据）。验证：探针 exit 0+矩阵 T15 主链绿。
- **AC-02 上限门退场（文件）**：>1MB 与 >10k 行文件正常出结果
  （15.9 翻转面）；700 行全换形 degraded=false+配对三段（15.10 重定
  面）；「等待内核引擎」err 文案 grep 零残留。验证：矩阵新期望绿+
  grep 空。
- **AC-03 替换缝兑现（目录）**：diff_dirs_json=native 直调；T16 组
  12 检查全绿（五态/下钻/同步/注记保持）；同长巨桶目录（>700k 桶积
  形）正常出结果。验证：矩阵 T16 绿+巨桶探针绿。
- **AC-04 缓冲区比较 v1**：diff_buffers 端点净形（hunks/adds/dels/
  rows:[]/err）；旁路自开+跳转（set_cursor 生效读回）+缺键 err 形+
  关闭复原；tab.key 键语义（装载两 tab 后比对出 hunks）。验证：
  矩阵 15.16-15.19 绿。
- **AC-05 100MB bench 判定**：diff_100mb 散点档 ≤2s（L2 口径）+
  budgets.json 解锁注记+实测回填。验证：bench stage_diff 全档绿+
  JSONL 数字在档。
- **AC-06 期望同步+判绿重定**：golden 重定每处漂移有证据行；判绿
  新口径数字=执行后真值回填 README（承 015 blocked 集注记）。验证：
  矩阵全量跑 ≥新下限/0 failed+evidence 在档。
- **AC-07 规范+账本**：SD-01..06 落档+供料回执节+specs.json P016-1
  投影。验证：文件在档+账本回读断言+grep 锚。
- **AC-08 消费零越界**：auto-lang 主树零改动（本仓 worktree 流程内
  不触上游路径）；发现上游缺陷=upstream 登记而非本仓修。验证：
  双仓 porcelain/grep 锚。

## 8. 执行步骤

| # | 任务 | 依赖 | 落点（实勘锚） | 产出/意图 | AC | 验证（命令/预期） |
|---|---|---|---|---|---|---|
| 0 | [x] T-00 消费勘定决策件（工具链门+裸名探针+缓冲区消费形） [✅ 已完成 2026-09-27，commit 60c8c86：工具链门=PATH 旧二进制 v2156-g1d597e3f4 早于 703 交付实勘[字节级零 diff natives 串]→auto-lang master 重建 v0.4.2-2175-g5c558778f[46efa926a 祖先链核验]——坑位三度应验；probe_bufdiff.py+probe_bufdiff_app 载具 8/0 全绿（split 臂 6：df/dd 正路径+ctx=0 钳 3 逐字节同形+缺文件/缺目录/缺键 err 形=非 Undefined 绑定证明；merged 臂 2：tab-N 键 registry 直读净形+缺键 err 点名缺席侧）；消费形定案 **(a) 双已开 tab 比较+面板双序号输入**（决策产物 report decisions 段在档；两面尾行语义差异[文件面吸收/快照面保留]实勘在档）；组依赖 .wt/edit-016/auto-lang@5c558778f 钉版 detached] | — | 本件 §5 T-00 节+probe 扩段 | 三勘定案+依赖组就位 | AC-01/04 | [x] `auto --version` 含 46efa926a（经祖先链）；裸名探针 exit 0；消费形定案补记 |
| 1 | [x] T-01 fsys.diff_files_json 替换 [✅ 代码落位 2026-09-27（commit 2beb4f8）：native 裸名直调纯转发+头注引擎时代消费注记；三门与「等待内核引擎」err 文案族随体退役（grep 零残留；实现体内部门常量/降级符号零残留脚本断言）。**验收面部分 blocked 承上游 D-1/D-2**：hunks/counts 面=探针⑦对账 modify 逐字段零漂移+15.9 翻转绿（>10k 行 dels=10493）+超限通过两检绿；rows 面五形态漂移=上游双缺陷受控（见 §9 blockers）——**不 golden 化缺陷输出**，golden 保持过渡时代原样] | T-00 | specs/auto-edit/src/back/fsys.at:250（原 :262） | native 直调+门退场 | AC-01/02 | [x] 探针⑦绊线绿+矩阵 15.9/15.10 新期望绿（rows 面 golden 重定=上游修复轮尾巴） |
| 2 | [x] T-02 fsys.diff_dirs_json 替换 [✅ 已完成 2026-09-27（commit 2beb4f8）：native 直调纯转发+桶形对齐/桶积 700k 护栏/「对齐超限」err 退役；**验收绿**：dirdiff 五形态 golden 语义零漂移（entries statuses/counts/note 逐字段全等——对账脚本在档）+同长 900 文件巨桶正常出结果（护栏退场实证）+>2MB 同尺寸 uncompared 注记保持+T16 组 12/12 全绿；条目序漂移=引擎每目录排序定序（断言面序不敏感，零语义差）] | T-00 | fsys.at:266（原 :803） | native 直调+护栏退场 | AC-03 | [x] 矩阵 T16 全绿+巨桶探针绿 |
| 3 | [x] T-03 golden 对账+矩阵期望同步（rows 面 golden 同步=blocked 承上游） [✅ 对账与绊线落位 2026-09-27（commit 2beb4f8）：probe_diff.py ⑦引擎对账段——六形态×引擎 envelope 逐字段对照 python 参考，**漂移逐字段证据 evidence-p016-recon.json 在档**（row 级 fields/engine/reference 三列）；①′对照改文档态绊线+⑦=实测态绊线（上游修复后 FAIL→强制重定轮）；15.9 期望翻转（通过形 dels=10493 推导在档）/15.10 重定（degraded=false+700/700+降级注记退役断言）；15.16-15.19 新增；主链 15.1-15.8+15.11-15.15 复跑=全谱 118/11 零新失败。**修复轮 golden 重定完成**（五简单形原样恢复=引擎≡过渡参考全等；big_reorder 按修复后引擎重定 310/310+rows 632——绊线红相→重定→绿相全谱在档）] | T-01/02 | probe_diff.py ⑦+desktop_mcp.py T15+fixtures/diff（golden 未动） | 漂移证据重定+判绿口径 | AC-06 | [x] probe 64/0+矩阵全量 118/11（失败集=D 族 7+已知族 4 逐项全中） |
| 4 | [x] T-04 缓冲区比较 v1 [✅ 已完成 2026-09-27（commit 2beb4f8）：back=api.at 第 15 #[api] diff_buffers→fsys.diff_buffers_json→native diff_snapshots（净形 rows:[]+缺键 err 形——T-00 探针实证）；front=editor_store diff_buf_* 状态族+DiffBufOpen/AInput/BInput/Compute/Run/Jump/Close/BypassTick 八 handler（DiffBufRun=消费收口内部件；to_int 平式解析序号）+app.at 面板（双序号输入+净形行按钮 label 预变换——模板算术插值未证面规避）+menubar 静态 item+action diff.buf-compare+Tick 挂臂；**旁路=OpenPath×2→跨 Tick 装载等待（tabs[].loaded 双真门）→DiffBufRun——load_key 单槽协议 B→A 固定序轮转（序错置互抢槽位死锁，首轮烟测实勘修正）**；跳转=切 ka tab+set_cursor(ka,a1,0)（A 侧首位左锚，B 侧=后续件）；矩阵 15.16-15.19 全绿（含切走切回光标读回 line=2）] | T-00 | api.at（第 15 #[api]）+fsys.at+editor_store.at+app.at | 端点+面板+跳转+旁路 | AC-04 | [x] 矩阵 15.16-15.19 绿（缺键端点 err 形=probe_bufdiff ② 承载） |
| 5 | [x] T-05 bench 100MB 真跑 [✅ 修复轮清偿 2026-09-28（commit 2d94928）：stage_diff 扩 diff_100mb 档（生成式 ~100MB 1% 散点改对——上游 T-04 基准形态）+over_size/over_lines 改通过延迟形+**≤2000ms 硬判定**；实测=**release 全链 1906/1971ms ≤2s 达成**（踩线余量 ~5%，四跑谱 1906-2054 在档；计时卫生=fixture writeback 沉降窗 5s——无窗 2034/2054 vs 静置分解 1437=+600ms 失真实证，测量方法修正非放宽）；分解=引擎计算 ~380ms 在册+链路主耗 2×100MB 读+47MB envelope 全量 rows 投影+49MB 双层 JSON（rows 惰性投影=观察件 want，红线余量薄根因）；debug 14.9s 同档在档；budgets.json/README/SD-05 实测回填] | T-01 | tools/bench/bench.py stage_diff+budgets.json | 100MB 档+门拒档改造+解锁 | AC-05 | [x] stage_diff 全档绿（100MB ≤2s——判定谱与卫生学在档 JSONL） |
| 6 | [x] T-06 规范增量+账本 [✅ 已完成 2026-09-27（commit 2beb4f8）：SD-01 diff-view.md（过渡节/上限门节退役注记+引擎时代与缓冲区比较新节——净形 envelope/状态面/handler 族/旁路 B→A 序/矩阵断言口径/D-1/D-2 规范锚）；SD-02 back-api.md（计数勘正 14→15+第 15 端点节+diff 双端点引擎时代注记）；SD-03 00-overview M3 第四件注记（部分 blocked 如实成文）；SD-04 README PLAN-016 口径（完成态 129/判绿 ≥118/0/D 族集注记/执行谱 118/11）；SD-05 战略 §2.1 预算行 blocked 注记+变更记录补注十二；SD-06 供料档 §6 消费回执（六供件核销+D-1/D-2 登记源码行级+残留 want 三件）] | T-01..05 | SD-01..06 六册 | 引擎时代口径+回执闭环 | AC-07 | [x] 文件在档+grep 锚（P016-1 账本投影=merge 期项，随 review/merge 轮） |
| 7 | [x] T-07 收尾核查（零越界+判绿真值回填） [✅ 已完成 2026-09-28：README 数字=执行谱真值（129/≥118/0/118-11）；双仓零越界=auto-lang 主树+钉版 worktree porcelain 全净（只读消费：构建/测试执行零源改）；vue 臂双 exit 0（regen+pnpm build，生成物 diff_buf 消费 9 处实证）；本 handoff 记录落 §9] | T-06 | 双仓状态+README 数字 | 消费收据终态 | AC-08 | [x] 双树 clean+README 数字=实测真值 |

## 9. 复审记录

- 2026-09-27 起草 handoff：`stage: new`，PLAN-016，plan_revision 1。
  `outcome: pass`（起草完备：703 六供件消费位全覆盖+供料回执表+裸名
  冲突落位设计与 T-00 探针先行+期望同步方法论成文；路径/符号经
  auto-edit@f74542d 与 auto-lang@b84d9d8f2 双仓实勘锚定；授权=起草，
  执行待用户启动）。`next: work`。
- 2026-09-28 执行 handoff：`stage: work | PLAN-016 | plan_revision 1 |
  outcome: **blocked**（部分——6.5/8 任务全落，T-05 全项+T-03 golden
  重定半项 blocked-on-upstream）| code_commit: worktree plan-016-dev@
  6fc1d45（base f74542d；T-00=60c8c86，实现+规范=2beb4f8，SD-06 移植=
  6fc1d45）| task_ids: T-00/T-01/T-02/T-03/T-04/T-06/T-07 落，T-05
  blocked | evidence: ①工具链门——PATH 旧二进制 v2156-g1d597e3f4 早于
  703 交付（字节级零 diff natives 串）→master 重建 v0.4.2-2175-g5c558778f
  （46efa926a 祖先链核验），坑位三度应验；②probe_bufdiff.py 8/0（裸名
  绑定+缓冲区消费形 (a) 定案）；③probe_diff.py **64/0**（①′文档态
  绊线+⑦对账段——evidence-p016-recon.json 漂移逐字段在档，golden 保持
  过渡时代不 golden 化缺陷输出）；④全矩阵 **118 passed / 11 failed**
  =已知族 4（T13.6 flake+T17.2/17.3/17.8 上游卡死簇）+上游缺陷族 7
  （T15.1/15.2/15.3/15.7/15.11/15.14/15.15——rows 承载面，预测集逐项
  全中）**零新失败**；15.9/15.10 翻转绿、15.16-15.19 全绿、T16 组
  12/12 绿；⑤vue 臂 regen+build 双 exit 0（生成物 diff_buf 消费 9 处
  实证）；⑥fsys.at 1150→350 行（三门/桶积护栏/降级面退役 grep 零
  残留）；⑦双仓零越界=auto-lang 主树+钉版 worktree porcelain 全净、
  wt-guard clean（pnpm 晶格 491 枚+deps 2 枚 junction 链接级摘除后复扫
  零 reparse）。| blockers: **上游双缺陷（供料档 §6.2 登记，源码行级
  根因+最小复现+修法建议）**——D-1 rows 面流位错配
  （group_hunks_annotated 的 fc/lc=changes 下标 vs build_rows 流下标
  ——变更行丢失/前导 ctx 重复/O(H²) 放大）+D-2 anchor 分块非单调
  （anchor_partition 缺单调过滤——换位族 counts 本身错，big_reorder
  双向 +620/-0 内部不一致实证）。**精确解阻=auto-lang 修订件修复
  D-1/D-2 并交付（新 delivery commit）→下游工具链重建→probe ⑦绊线
  FAIL 触发重定轮（golden 重定+T15 判绿恢复+T-05 bench diff_100mb
  真跑+budgets.json/README/SD-05 实测回填）**；消费侧不修（AC-08）。
  | next: 用户裁定——(i) 上游修复立项后回 work 清偿尾巴（T-05+golden
  重定），或 (ii) 本件先行 review（6.5/8 面完整+证据链在档——rows 面
  blocked 集已注记判绿口径）。status 维持 executing（blocked 未清）。
- 2026-09-28 修复轮（尾巴清偿）handoff：`stage: work | PLAN-016 |
  plan_revision 1（契约未变——blocked 尾巴按 PLAN-704 交付清偿）|
  outcome: pass | code_commit: worktree plan-016-dev@2d94928（修复轮；
  前序 60c8c86/2beb4f8/6fc1d45/主检出簿记 c14b49f/3bcf48e/c25d4d1）|
  task_ids: T-03 golden 尾+T-05 全项清偿，T-00..T-08 全落 | evidence:
  ①工具链 v0.4.2-2183-gc8f86ef92（含 PLAN-704 b2f8761e0 祖先链核验）；
  ②绊线红相=①′/⑦ 八 FAIL 逐项实证（引擎漂移清零的否定面）→golden
  重定→probe **64/0** 绿相（①′六形严格全等+⑦五形 zero-drift+
  big_reorder 引擎时代换位不变量）；③全矩阵 **124 passed / 5 failed**
  =已知族全中（T13.6 flake+T17.2/17.3/17.4/17.8 上游卡死簇）**零新
  失败**——T15 全组恢复原口径绿、D 族清零、15.16-15.19 缓冲区组保持；
  判绿口径恢复 014/015 原集（≥117/0 基线，本轮 124/0 计法达标）；
  ④15.14 双 cap 改形（生成式 700 全换——big_reorder 引擎时代形
  del/add 块分离零 pair 展开前提失效，硬断言+smoke 同款，fixtures
  pristine）；⑤bench diff_100mb **1906/1971ms ≤2s 达成**（踩线 ~5%
  余量；writeback 沉降窗卫生学+分解归因在档）+budgets/README/SD-01/
  SD-05/供料档 §6.2 清偿注记回填。| blockers: 无 | next: review`。
  status=execution_done。
- 2026-09-28 复审 handoff：`stage: review | PLAN-016 | plan_revision 1
  | outcome: **pass** | reviewed_commit: worktree plan-016-dev@bce25f0
  （修复轮 2d94928+复审 F-1/F-2/F-3 文档同步）| base_commit: master
  main@f74542d（簿记 c14b49f/3bcf48e/c25d4d1/4c7a629 在先）|
  dependency_revisions: 工具链 auto v0.4.2-2183-gc8f86ef92（含
  PLAN-704 b2f8761e0）；组依赖 .wt/edit-016/auto-lang@5c558778f
  （blueprint 解析面）| spec_inputs: diff-view.md 引擎时代与缓冲区
  比较节（SD-01 清偿态）+back-api.md 第 15 端点节（SD-02）+
  00-overview M3 第四件注记（SD-03，F-1 清偿态）+README PLAN-016/
  修复轮口径（SD-04，F-2 终数回填）+战略 §2.1/补注十二（SD-05）+
  供料档 §6 含清偿完成（SD-06）| acceptance_results: AC-01..08 全
  pass（①native 直调+门符号零残留+五形 zero-drift ②15.9/15.10 绿+
  err 文案 grep 零残留 ③T16 12/12+巨桶 ④15.16-15.19+第 15 端点
  ⑤1906/1971ms ≤2s+JSONL×5 入库+回填 ⑥重定漂移行在档+终数 ⑦SD
  六册+同步 ⑧双仓净+缺陷 upstream 登记实录）| findings: F-1（P2）
  overview blocked 时代文本未随修复轮更新→已修（bce25f0）；F-2（P2）
  README 修复轮段缺终数占位→已修（bce25f0）；F-3（P3）bench 判定
  JSONL 未入库→已修（bce25f0，results 入仓惯例）——三项文档/证据
  面复审轮内闭合，行为面零改动 | evidence: 复审独立复现（reviewed
  commit 态）：probe_diff.py **64/0**+全矩阵 **125 passed / 4
  failed**（T13.6 flake+T17.2/17.3/17.8 已知族，T17.4 本轮翻绿=轮换
  成员；计 125/0 ≥117 达标）；静态锚=「等待内核引擎」/门内部符号
  grep 零残留+api 计数 15+diff_buffers 锚 12；vue 臂双 exit 0 证据
  复用（.at 源自构建后零变化——git diff 2beb4f8..HEAD src/ 空）；
  AC-08 双仓 porcelain 全净。复审限制声明=实现会话自审（独立会话
  不可用）——判定自工件与两次独立复现重构，非执行期汇报采信。|
  next: merge`。status=reviewed。
- 2026-09-28 merge 收据（PLAN-016:r1，五检查点）：
  - **prepared**：评审基线=reviewed pass @r1（reviewed_commit bce25f0，
    复审记录在案含 F-1/F-2/F-3 闭合）；canonical Spec 六册已随交付
    提交在档（SD-01..06@943f0db）；账本投影目标=.autoos/specs.json
    reviews 段；跨仓关联=auto-lang PLAN-704 delivered（b2f8761e0）。
  - **landed**：dev 分支 rebase 上 main（簿记位在先 c14b49f..cce1cfe
    五提交）——旧→新映射 60c8c86→ddbecd6/2beb4f8→3440e3a/6fc1d45→
    399c36c/2f439ff→c3ae23d/2d94928→8897427/bce25f0→943f0db/
    b69bf35→a2720c1，`git range-diff` 7/7 全等（安全改写证明）；
    main `git merge --ff-only plan-016-dev` → tip=a2720c1=delivery
    commit（零合并提交）；落地后主检出冒烟 smoke_t234 ALL PASS
    （known-good，含改形后双 cap 面）。
  - **ledger_refreshed**：.autoos/specs.json reviews 段 P016-1 外科
    尾插（15→16 项——roundtrip 字节等价先证[indent=2/ascii=false/
    尾换行]；回读断言前 15 项零扰动+他五段零扰动）；commit a2720c1。
  - **archived**：本行所在提交——git mv 至 docs/plans/archived/ +
    status: archived + completion_kind: delivered。
  - **cleaned**：git 侧全净实证——wt-guard clean ✓×2（edit-016/
    auto-edit 与组依赖 edit-016/auto-lang 双双零 reparse point；
    junction 晶格首轮清理后修复轮未重建）；worktree 注销 ✓×2（各属
    主仓注销；双仓 worktree list 零 edit-016 条目）/branch
    plan-016-dev 删 ✓（was a2720c1）/组目录 .wt/edit-016 rmdir ✓。
    五检查点全落，completion_kind=delivered。
  - **部署观察项（landing ≠ deployment）**：三项生产面消费件均当前
    ——①debug 工具链二进制 v0.4.2-2183-gc8f86ef92（修复轮重建，含
    PLAN-704）；②release 二进制同版（修复轮 bench 判定构建）；
    ③vue 生成束（gen/front/vue/dist）=首轮 build 产物+修复轮 .at
    源零变化（git diff 2beb4f8..HEAD src/ 空实证）——三者无陈旧面，
    无需重建动作。

## 10. 待澄清事项

- **Q-3（blocked 主项，2026-09-28 执行期新增）上游 D-1/D-2 修复时序
  （用户裁定）**：本件 6.5/8 落地、T-05 与 rows 面 golden 重定
  blocked-on-upstream（§9 handoff blockers 节——缺陷已在供料档 §6.2
  完成登记含修法建议，auto-lang 侧需修订件立项）。请裁定：
  (i) 先在 auto-lang 立项修复（建议——缺陷随 M3 主线放大，bench/
  golden 尾巴一并解阻），下游修复轮回 work 清偿；(ii) 本件先行
  review/merge（部分面交付——rows 面回退态=上游缺陷在案注记，
  判绿口径已按 blocked 集重定）。
  **【2026-09-28 用户裁定 (i)】**：auto-lang **PLAN-704**
  （704-diff-rows-anchor-fix）已立项起草（master@ca68427fc——D-1
  流位单源化+D-2 anchor LIS 单调过滤，4 AC/4 T+SD 两册）；交付后
  本件回 work 清偿尾巴（工具链重建→⑦绊线触发 golden 重定+bench
  diff_100mb 真跑+README/SD-05/budgets.json 实测回填）。
  **【同日清偿完成·Q-3 关闭】**PLAN-704 delivered（b2f8761e0）→本件
  修复轮三步全落（§9 修复轮 handoff）——本件终态 execution_done，
  next=review。
- **Q-1 缓冲区比较手动形态预裁定（已按 T-00 证据定案，结案）**：
  T-00 探针实证候选 (a) 成立（tab.key registry 直读零装载面）——
  面板双 tab 序号输入+默认=active 与次 tab；(b) active vs 磁盘版
  未采（probe 装载面留后续件）。
- **Q-2 100MB bench fixture 形态确认（维持原口径）**：散点改合成对
  （与上游 T-04 基准形态对齐）；全异形不入 bench 档（观察件）——
  真跑判定随 Q-3 修复轮执行。
