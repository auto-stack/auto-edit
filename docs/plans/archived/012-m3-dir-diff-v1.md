---
plan_id: PLAN-012
status: archived
completion_kind: delivered
feature_name: m3-dir-diff-v1（M3-02：目录 diff v1——递归比对/状态过滤/基础同步/文件 diff 下钻）
author: [agent]
created_at: 2026-09-23T15:21:52+08:00
updated_at: 2026-09-24T01:40:00+08:00
plan_revision: 1
current_step: 7
total_steps: 7
supersedes_spec_components: []
new_spec_components:
  - "docs/specs/modules/diff-view.md#SD-01（目录 diff 节追加：分类语义/entry 契约/同步动作/下钻）"
  - "docs/specs/modules/back-api.md#SD-02（diff_dirs/sync 两端点节 + #[api] 计数勘正 10→13）"
  - "docs/specs/00-overview.md#SD-03（M3 注记追加第二件行）"
touched_goals: []
---

# [PLAN-012] M3-02：目录 diff v1（递归比对 + 状态过滤 + 基础同步 + 下钻）

## 0. 变更摘要

M3（diff 对打 Beyond Compare，战略 §2.3）第二件，**预起草**（011 文件
diff v1 在途执行中——worktree plan-011-dev T-00 探针已起，无 commit；
本计划**执行前置=011 merge 归档**）。战略 §2.3 原文：「目录 diff v1：
递归比对、按状态过滤（新增/改/删/二进制）、基础同步动作（单向复制/
删除）」。核心判断（背景调查实勘）：**完全引擎无关**——目录比对 v1
的实质=元数据递归遍历+分类（走 back `fs.list_dir/is_dir/size` 现役集，
009 search_files_json 先例全套复用），内容级「改」判定=尺寸差+小文件
（≤2MB）`Str ==` 全等比对（瞬态、上限语义成文）；同步动作三内建在册
（`fs.copy`(1007)/`fs.delete`(1003)/`fs.remove_dir_all`(1015)）——但
**009 教训=catalog 在册≠codegen 映射正确**（fs.walk 错名/walk_files
撞号/metadata 覆盖三案在册），T-00 逐个 HTTP 实测定案。与 011 的协同
是本件最大增量：**「改」条目下钻→011 文件 diff 视图**（BC 工作流闭环：
目录比对→双击改项→并排 diff），复用 diff_files 端点与 diff 视图态零
新视图件。边界如实成文：二进制判定=启发式（size>0 且 read_text==""
——非法 UTF-8 即二进制近似）；同尺寸二进制不比对内容（字节级 hash=
内核件 want）；目录选择=路径输入框+env 旁路（`dialog_open` 文件专用，
folder picker=上游 want）；双向同步向导=§9-Q5 开放问题非本期。
前置：PLAN-011 终态（diff_files 端点+diff 视图态+diff-view.md 册+
矩阵 N/0——README 口径）。

## 1. 目标

- **G-1 目录 diff 入口**：「工具→比较目录…」（静态 menubar item）→
  目录面板（diff 视图态扩展 `diff_mode: "file"/"dirs"`）：双路径输入框
  + 比较按钮；矩阵旁路=env `AUTO_DIRDIFF_A/B`（011 AUTO_DIFF 先例）。
- **G-2 递归比对与分类**：back 新端点 `diff_dirs(path_a, path_b)`——
  递归遍历（list_dir 先例）+ 五态分类：同/改/删（只在左）/增（只在
  右）/二进制（启发式）；envelope（entries+五计数+truncated）；上限
  语义（条目 cap、内容比对 cap 2MB、超限注记不静默）。
- **G-3 状态过滤与计数**：面板过滤按钮组（全部/增/删/改/二进制）+
  计数栏；过滤纯 front 态（envelope 全量在 store，过滤不重比对）。
- **G-4 下钻文件 diff**：「改」条目点击 → 011 文件 diff 视图
  （diff_files+并排渲染+hunk 导航全套复用）；其余条目点击 → OpenPath
  编辑器打开（fif 点击先例）。
- **G-5 基础同步动作**：单向复制（左→右/右→左，fs.copy/
  copy_recursive）+ 删除（fs.delete/remove_dir_all）——**破坏性动作
  alert-dialog 确认链**（EolConvert/quit 先例）；动作后自动重比
  （刷新=重调 diff_dirs，结果与磁盘 E2E 断言）。
- **G-6 矩阵与规范**：矩阵扩 T16 检查组（五形态 golden+过滤+下钻+
  同步 E2E）；diff-view.md 目录节 + back-api 勘正（10→13 端点）+
  overview 第二件行；upstream §15（folder picker want 等）；vue
  build-green。

### 非目标

- 双向同步向导（战略 §9-Q5 开放问题——M3 收口按使用反馈裁定）。
- 3-way merge（§9-Q5 同）、十六进制比对（战略非目标）。
- 同尺寸二进制内容比对（字节级 file-hash=内核件，§15 登记并入 diff
  供料包 §4 目录比对件的关联注记）。
- 目录内容预览列（改项 hunk 摘要——引擎时代件）、监控/自动刷新。
- >2MB 文件内容比对（同尺寸大文件分类=「同(未比对)」注记态——hash
  want 清偿后收口）。
- 目录 picker 对话框（dialog_open 文件专用——folder picker 上游 want；
  v1 路径输入框+env 旁路）。
- auto-lang 侧任何改动（上游 want 走 docs/upstream 登记）。

## 2. 架构方案

分层落点（2026-09-23 实勘：auto-edit main@e780d93 / 011 在途 plan-011-dev
基线 e780d93 / auto-lang fe785d185）：

| 面 | 现状 | 本期形态 | 依据 |
|---|---|---|---|
| 递归遍历 | 009 search_files_json 现役：`fs.list_dir`（递归扁平 JSON，fs.walk 错名规避）+`fs.is_dir`+`fs.size`（fsys.at:129-176 实锚） | 同套复用（双侧各遍历一次→相对路径集对齐→逐条分类） | 009 实战验证集，零新原语 |
| 分类 | 无 | 五态：**只在左=删/只在右=增**（左右=旧新语义，BC 同款）；双侧均有：size 差→改；size 同且 ≤2MB→`read_text` 全等比对（同/改）；size 同且 >2MB→「同(未比对)」注记态；**二进制启发式**=size>0 且 read_text==""（非法 UTF-8 即二进制近似——back-api.md IO 语义节错误形惯例）；双侧二进制=尺寸比对 | .at 原语面内自洽；上限与启发式成文，hash want 清偿后收口 |
| 同步动作 | 内建在册：fs.copy(1007)/fs.delete(1003)/fs.remove_dir_all(1015)/fs.copy_recursive(2862)——**codegen 映射正确性未证**（009 三案教训） | back 两端点：`sync_copy(src, dst)`（文件 fs.copy/目录 copy_recursive）+ `sync_delete(path, is_dir)`（fs.delete/remove_dir_all）——T-00 逐个 HTTP 实测定案，错名者登记 §15 并降级（对应动作 disabled+注记） | 破坏性动作收口 back（front 零 fs 铁律不破） |
| 视图 | 011 落 diff 全幅态（diff_open+rows+hunk 导航——diff-view.md 册） | `diff_mode` 扩展：dirs 态=路径输入行+过滤按钮组+计数栏+entries 列表（root view 渲染——009 fif 根视图面板先例+010 menubar 四边界教训：动态列表留根视图，菜单项静态） | 复用 011 视图态骨架；entry 行=相对路径+状态徽标+双侧尺寸 |
| 下钻 | 011 diff_files+并排视图现成 | 「改」entry 点击→`diff_files(abs_a, abs_b)`→diff_mode 切 file+rows 装载（011 DiffCompute 收口复用）+返回目录态按钮 | BC 工作流闭环；零新视图件 |
| 确认链 | alert-dialog 先例（EolConvert/quit/关脏 tab） | 删除/覆盖复制（目标已存在）→确认弹层；动作后 DiffDirsRefresh 重比 | 破坏性动作纪律 |
| bench | 011 落 diff 计时档 | 目录档 v1 不扩（元数据遍历非预算面）——引擎落地后目录比对计时随供料包 §4 收口 | 预算表无目录行；scope 纪律 |
| 检测器 | 白名单五件封闭集 | 零变更（目录链零 code_editor_text） | 纯 back 读 |
| vue 轨 | 011 build-green（预期） | 新增面=back 三端点（HTTP 同形）+根视图基础 kind；fs.* 全在 back（ts_adapter 拦截面不涉） | 跨轨天然一致 |

**安全注记（同步动作）**：v1 护栏=①动作仅对「已完成一次比对」的
entries 态开放（无比对无动作）；②删除/覆盖目标必须确认；③back 端点
空路径拒绝。目录级递归删除（remove_dir_all）默认**不提供**（仅空目录
fs.delete——危险面收敛），递归删除列未来件+护栏设计随用反馈。

## 3. 技术栈

.at（editor_store.at 目录 diff 状态/过滤/同步 handler、app.at dirs 态
面板+确认弹层、back/{api,fsys}.at 三端点）、desktop_mcp 矩阵（T16 组+
目录 fixtures）、python 探针（probe_dirdiff.py，T-00 决策件：三内建
实测+启发式验证）。无新依赖；内核零改动。

## 4. 需求分析与背景调查

- **授权记录**：用户 2026-09-23 指令——「计划011如果完成的话，下一步
  计划是什么？现在可以提前规划下一步计划吗？」。授权=**预起草**（与
  011 执行并行）；**执行前置=011 merge 归档**（依赖其 diff_files 端点/
  视图态/规范册）。范围=auto-edit 仓源码与 docs；auto-lang 零改动。
  无预算/自动续跑授权。
- **战略依据**：§2.3 目录 diff v1 原文（递归比对/状态过滤/基础同步
  动作——单向复制/删除；双向同步向导列 §9-Q5）；§6 M3 行（目录 diff
  v1 + 基础同步）；补注十一（M3 提前开工序列——011 文件 diff v1 为
  首件，本件为第二件）。
- **规范基线**：011 终态（**预落**）：modules/diff-view.md（新建册——
  本件 SD-01 追加目录节）、back-api.md（十端点——本件勘正至十三）、
  00-overview.md M3 开篇注记（本件追加第二件行）。
- **内建面证据**（native_catalog，2026-09-23 勘）：`fs.copy`(1007)/
  `fs.delete`(1003)/`fs.remove_dir`(1014)/`fs.remove_dir_all`(1015)/
  `fs.copy_recursive`(2862)/`fs.rename`(2994) 在册——**映射正确性
  未证**（009 §12 三案：fs.walk 错名/walk_files 白名单缺+撞号/
  metadata 被 auto.fs.size 覆盖——catalog 在册≠可用，T-00 逐个 HTTP
  实测为决策件核心）；`dialog_open`(2927)=文件选择（filter 参数形）
  ——folder picker 无（want）。
- **代码锚**：`specs/auto-edit/src/back/fsys.at:129-176`
  （search_files_json——list_dir/is_dir/size 递归遍历现役先例，本件
  遍历核复用形态）；`src/back/api.at`（九 #[api] 现状——011 落第十
  件 diff_files，本件再增三件）；`src/front/editor_store.at`（011 终态
  增 diff 状态族——本件扩展 diff_mode/dirs 态；fif 下钻先例 L772-787
  形态）；`src/front/app.at`（011 终态增 diff 全幅态——本件 dirs 态
  插入位；静态 menubar 先例；alert-dialog 确认链先例 L244-255）；
  `tests/desktop_mcp.py`（T15 在途——T16 追加位）；`tests/fixtures/`
  （diff/ 011 在途——本件 fixtures/dirdiff/）。
- **矩阵口径**：011 终态 N/0（README 口径，预估 ≥95）；T16 后 →
  ≥N+M/0（M=T-05 实落），README 单源同步。
- **并行警示**：011 worktree 在途（plan-011-dev，T-00 探针已起）——
  本计划**不得抢跑**（执行前置明记）；lang-695 worktree 并行（auto-lang
  侧，与本件无涉）。主检出未提交项含本会话产物（战略补注/供料包/
  designs/001/011 草案）——随各自计划 merge 周期入库。

## 5. 详细设计

### T-00 探针勘定（决策件，先行）

`tests/probe_dirdiff.py`（probe_find 形态：Phase A back HTTP + Phase B
merged），四项：

1. **fs 三内建映射实测**（核心——009 三案教训）：`fs.copy`/
   `fs.delete`/`fs.remove_dir`/`fs.copy_recursive`/`fs.remove_dir_all`
   逐个 back HTTP 调用（构造 tmp fixture：文件复制/删除、空目录删除、
   递归复制/删除）——在册可用者定案入 T-02；错名/未登记者登记 §15，
   对应同步动作降级（disabled+注记）。
2. **二进制启发式**：invalid UTF-8 fixture（008 fixtures 复用）→
   read_text=="" && size>0 判定验证；空文件（0B）不误判。
3. **内容比对上限**：2MB×2 同尺寸不同内容 fixture → Str == 比对正确性
   + 瞬态池驻留观察（RSS 采样，PLAN-007 观察 B 口径——2MB 级预期无
   虑，实测注记）。
4. **dialog_open 目录能力勘**：filter 形态能否选目录（预期否）——
   定案 v1 路径输入框方案+folder picker want 登记。

**产出=§10 T-00 决策记录**：三内建可用性表+启发式正案+方案冻结。

- AC 关联：AC-02/AC-05 前置。验证：`python tests/probe_dirdiff.py`
  退出码 0 + 报告落档。

### T-01 back diff_dirs（递归比对+分类）

`api.at` 增 `diff_dirs(path_a, path_b) str`（GET）+ `fsys.at` 实现
`diff_dirs_json`：双侧 `fs.list_dir` 遍历（search_files 先例）→ 相对
路径集对齐 → 五态分类（§2 分类序：存在性→二进制启发式→尺寸差→
≤2MB 内容全等→>2MB 注记态）→ envelope `{entries:[{rel,status,size_a,
size_b}],counts,truncated,err}`（entries 全量+truncated 上限 5000 条；
json 拼装 Str 链+json_escape——第五次复用）。错误形（根不存在）=
envelope err 不静默。

- AC 关联：AC-02。验证：Phase A 五形态 golden 对照（fixtures/dirdiff/
  构造：同/改/增/删/二进制）。

### T-02 back sync 两端点

`sync_copy(src, dst) bool`（POST；文件=fs.copy，目录=fs.copy_recursive；
目标存在=T-00① 可用性定案的覆盖语义）+ `sync_delete(path, is_dir) bool`
（POST；文件=fs.delete；目录=**仅空目录** fs.remove_dir——递归删除
v1 不提供，§2 安全注记）。空路径/根路径拒绝。T-00① 判不可用的内建
→ 对应端点降级（返回 false+console 注记）+§15 登记。

- AC 关联：AC-05。验证：Phase A tmp fixture 复制/删除 E2E。

### T-03 front dirs 面板（diff_mode 扩展）

`EditorStore` 增：`diff_mode`（"file"/"dirs"）、`dir_a/dir_b`（输入框
绑定）、`dir_entries/dir_counts`（envelope 解包）、`dir_filter`
（"all"/"added"/"deleted"/"modified"/"binary"）、`dir_truncated/
dir_err`。msg 增：DirDiffOpen, DirDiffCompute, DirFilter(str),
DirDiffClose, DirDiffRefresh。app.at dirs 态：路径输入行（input×2+
比较按钮）+计数栏+过滤按钮组（静态五钮）+entries `for` 渲染（相对
路径+状态徽标+双侧尺寸；根视图——快照定位面）。env 旁路
`AUTO_DIRDIFF_A/B`（DiffOpen 消费，011 AUTO_DIFF 同款）。

- AC 关联：AC-01/AC-03。验证：merged 烟测（旁路开+entries/counts
  state 断言+过滤切换）。

### T-04 下钻与同步动作

「改」entry 点击 → `DiffDrillIn(rel)`：abs 拼路径 → diff_files 调用
→ diff_mode 切 "file"（011 视图复用）+「返回目录」按钮（mode 切回，
entries 态保留不重比）。非改 entry 点击 → OpenPath（fif 先例）。entry
动作按钮：复制→对侧（`CopyTo(side)`——sync_copy+确认[目标存在时]）；
删除（`EntryDelete`——alert-dialog 确认链+sync_delete）。动作成功 →
DirDiffRefresh（重比+计数/过滤态保持）。

- AC 关联：AC-04/AC-05。验证：矩阵 T16（下钻 state+磁盘 E2E）。

### T-05 矩阵 T16 检查组 + fixtures + 口径

`tests/desktop_mcp.py` 增 T16 组（预估 10 检查，独立进程+env 旁路+
tmp 目录隔离[fixtures 拷贝保 pristine——008 先例]）：旁路开栏/五形态
golden（entries+counts state 断言）/过滤四态/下钻文件 diff（diff_mode
切换+rows 到达）/返回目录态/复制→重比变同（磁盘断言）/删除确认链→
条目消失/二进制形态/超限注记（>2MB 生成式 fixture）/错误形（根缺失）。
README 口径：N/0 → ≥N+M/0（判绿下限同步）。

- AC 关联：AC-06。验证：`python tests/desktop_mcp.py` 完成态 ≥N+M/0。

### T-06 规范落账 + upstream §15 + vue 复验

SD-01..03 落 docs/specs（追加节+来源注记）；upstream m1-supply 增
§15（PLAN-012 件：**folder picker want**（dialog_pick_folder——目录
选择对话框）；**file-hash 比对 want**（同尺寸大文件/二进制内容级分类
——diff 供料包 §4 目录比对件的下游细化）；T-00① 判不可用的 fs 内建
错名/缺登记者随落）；vue 轨 regen --build exit 0 复验。

- AC 关联：AC-07。验证：grep 三册+§15 在档+构建退出码。

### 规范增量

| delta_id | add/modify/retire | docs/specs/... target | before/after rule | rationale | acceptance IDs |
|---|---|---|---|---|---|
| SD-01 | add | modules/diff-view.md（追加「目录 diff」节） | before：011 册=文件 diff 面。after：dirs 态状态字段、五态分类语义（存在性→二进制启发式→尺寸→内容全等→注记态序）、entry 契约、过滤语义（front 纯态）、下钻协议（改项→file 模式复用 011 视图）、同步动作安全注记（确认链/仅空目录删/护栏三条） | 目录面同册归口（同一视图态族）；启发式与上限语义需成文防误用 | AC-01..AC-05 |
| SD-02 | add+modify | modules/back-api.md（追加两同步端点节 + 计数勘正） | before：十 #[api]（011 终态）。after：十三（增 diff_dirs/sync_copy/sync_delete）；契约（envelope 形/五态语义/上限 5000 条+2MB/错误形/安全注记） | 端点=跨轨落点；安全语义成文 | AC-02/AC-05 |
| SD-03 | add | 00-overview.md（M3 注记追加第二件行） | before：M3 注记=首件（011）。after：补第二件（目录 diff v1）一行+链接 | 总览阶段进度面 | AC-07 |

## 6. 测试设计

- **T-00 探针**（probe_dirdiff.py）：四项勘定；退出码门。
- **golden 五形态**（fixtures/dirdiff/：base/rev 两目录树——同/改/
  增/删/二进制齐备）：envelope entries+counts 逐字段对拍（python 参考
  生成 golden）。
- **矩阵 T16**（快照+autoui_state 双面）：十件如 §T-05；同步动作走
  tmp 拷贝 E2E+磁盘断言（复制产物 sha/内容、删除消失）。
- **单测/烟测**（T-03 内嵌）：过滤纯态不重比（比对计数不变断言）、
  env 旁路、错误形 console 记录。
- **vue 轨**：regen_vue --build exit 0。

## 7. 验收标准

- **AC-01 入口**：「工具→比较目录…」开 dirs 面板；双路径输入+比较
  生效；env `AUTO_DIRDIFF_A/B` 旁路生效；取消/空路径零动作。验证：
  矩阵 T16+手动注记。
- **AC-02 分类正确性**：五形态 golden 逐字段对照（五态+双侧尺寸+
  counts）；>2MB 同尺寸=「同(未比对)」注记态；二进制启发式正判
  （invalid UTF-8 fixture）；错误形不静默。验证：Phase A+矩阵 T16。
- **AC-03 过滤与计数**：五过滤钮切换正确（front 纯态——重比对零
  发生）；计数栏五数与 entries 一致；truncated 注记。验证：矩阵 T16
  state 断言。
- **AC-04 下钻**：「改」条目→file 模式（diff_files+011 并排视图+
  hunk 导航复用）；返回目录态 entries 保留。验证：矩阵 T16（diff_mode
  切换+rows state）。
- **AC-05 同步动作 E2E**：复制（确认链）→对侧文件出现+重比变「同」
  （磁盘断言）；删除（确认链）→条目消失+重比计数更新；仅空目录可删
  （递归删除不提供）；T-00① 判不可用内建→动作 disabled+注记。验证：
  矩阵 T16 tmp E2E。
- **AC-06 矩阵基线**：T16 组入矩阵，完成态 011 终态 N/0 → ≥N+M/0
  判绿（M 以 T-05 实落为准，README 同步）。验证：矩阵退出码+README
  grep。
- **AC-07 规范与上游**：SD-01..03 在册；upstream §15 在档（folder
  picker/file-hash want+T-00 勘出件）；vue regen --build exit 0。
  验证：grep+构建退出码。

## 8. 执行步骤

| 步 | 任务 | 依赖 | 产出/验证 |
|---|---|---|---|
| 1 | [x] T-00 探针勘定（三内建实测+启发式+上限+picker 勘） [✅ 已完成 2026-09-23]：**16/0 exit 0**（三轮迭代：token 解析 harness 错位→presence 解析；bin 子串碰撞→左边界锚定）；①a fs.copy 保留字阻断可复现证据（迷你 app）+字节往返获救+四内建全 ok+护栏/覆盖/启发式/2MB 全勘定——证据：probe_dirdiff_report.{txt,json}，载具 probe_dirdiff_app/，fixtures/dirdiff+golden 在仓（提交 T-00-1） | **011 merge** | §10 决策记录；exit 0 |
| 2 | [x] T-01 back diff_dirs（遍历+分类+envelope） [✅ 已完成 2026-09-23]：fsys.diff_dirs_json 全内联+api 第十一件 GET /api/diff_dirs；探针 ⑤′ golden 逐字段+根缺失 err 一把过；**桶积护栏 700k**（定标 N=600 0.40s/N=800 0.94s 过、N=1000 WARN[budget] fn=fsys#diff_dirs_json 死 body='0'→优雅超限 err 形，011 上限门同款）——commit 9f738b4 | T-00 | Phase A golden 绿 |
| 3 | [x] T-02 back sync 两端点 [✅ 已完成 2026-09-23]：sync_copy（文件=字节往返≤2MB[超限 false]/目录=copy_recursive）+sync_delete（文件=fs.delete/目录=仅空目录 remove_dir/空+根+缺失护栏）POST 两件；探针 ⑥′ 六项 E2E 全绿（含非空目录拒绝/空路径 HTTP 层拒）——同上 commit | T-00① | tmp E2E 绿 |
| 4 | [x] T-03 front dirs 面板（diff_mode+过滤+计数） [✅ 已完成 2026-09-23]：editor_store 目录状态族+22 msg+handlers+app.at dirs 面板（dir_mode 顶层面板+diff_open 内卫——011 编辑区条件零改动）；**五状态五独立 for 行渲染**（011 同循环兄弟 if 仅首生效实勘规避）；徽标/尺寸/目录标记/未比对注记全 store 预变换；五过滤钮=front 纯态零重比；env 旁路臂 AUTO_DIRDIFF_A/B——烟测 S1 断言全绿（同上提交） | T-01 | merged 烟测 state |
| 5 | [x] T-04 下钻+同步动作（确认链+刷新） [✅ 已完成 2026-09-23]：DirRowClick 改→DiffCompute 复用（dir_from_dirs 门=DiffCompute err/DiffClose 双外科归位，011 路径零扰动）+返回目录钮；同步动作=恢复直执行/双侧恒确认（Q-2）+删除确认链 alert-dialog+DirDiffRefresh 重比过滤保持——**烟测 47/47 ALL PASS**（下钻 rows 到达/返回 entries 保留/复制磁盘 E2E/覆盖确认/删除确认链/错误形）（同上提交） | T-02/T-03 | 下钻/同步烟测 |
| 6 | [x] T-05 矩阵 T16+fixtures+README [✅ 已完成 2026-09-23]：T16 组 12 检查（golden counts/快照形态/过滤纯态/下钻返回/同步动作磁盘 E2E×3/关闭复原/错误形/>2MB 未比对注记）——**T16 12/12 首轮全绿**（run3）；完成态 **109 检查**，五轮谱 85/5→95/2→104/5→107/2→106/3（T12.6=R-4 已知败不计+轮换竞态 flake 皆非本件路径，无 T16 基线轮 run2 亦 2 败=噪声地板预存）；README 判绿口径 **≥107/0**（已知败不计+重跑条款）落账（提交 8296b65） | T-04 | ≥N+M/0 |
| 7 | [x] T-06 规范 SD+upstream §15+vue [✅ 已完成 2026-09-23，vue 臂双重 blocked-on-upstream 在案 §9]：SD-01 目录节+SD-02 勘正十三件+SD-03 第二件行+§15 八件（de54aec）；grep 四锚在档（diff-view/back-api/overview/README 各 1-2 锚）；vue 定性=strict gen 红 menubar-sub schema（**695 预存主干断层**）+lenient gen ✓ 34 组件+build 红 TS7006×12 全在 §14 helper 行（本件零新增错面）——精确解锁动作两项在档（§15） | T-05 | grep+build exit 0 |

（T-02 与 T-03 可并行；worktree 纪律照旧——专用组 worktree，主检出
零落盘。）

## 9. 复审记录

- **2026-09-23 stage: new（r1，drafting → 预备交接）**：用户指令预起草
  011 后继；战略 §2.3 定位=M3-02（目录 diff v1，011 非目标已标注候选）。
  背景调查实勘：完全引擎无关（list_dir 现役集+尺寸/全等分类）；同步
  三内建在册但映射正确性未证（009 三案教训→T-00 决策件）；下钻=011
  视图复用（BC 工作流闭环）。边界如实成文（二进制启发式/2MB 上限/
  folder picker want/双向向导 Q5）。七步七 AC 三规范增量（追加节+勘正
  13 端点+注记行）+upstream §15。**执行前置=011 merge 归档**（011
  worktree 在途 T-00）。outcome: pass（授权=预起草；执行待 011 收口后
  用户启动 auto-plan-work）。next: work（前置=011 归档）。

- **2026-09-23 stage: work（executing 进入，T-00 起）**：用户指令
  「计划012: 完成它」；前置核实=011 merge 归档闭环（31b3b16 五检查点
  delivered，执行前置解除）。worktree=`D:/autostack/.wt/plan-012/auto-edit`
  （branch `plan-012-dev`，base=main tip **31b3b16**，零提交起步）；
  deps junction ×2（bps→auto-lang/blueprints、stylekit→主检出
  specs/stylekit——010/011 先例，merge 清理摘除）；工具链钉版
  `/d/tmp/p012_pin_auto.exe`（**v0.4.2-2046-g02ae0ac1c-dirty**，与
  target/debug 同版同体积——011 Q-7 纪律：矩阵/bench/构建一律钉版
  执行）。主检出预检：stylekit 两删除（`specs/stylekit/pac.at`、
  `specs/stylekit/src/front/styles.at`）=并行会话 WIP 挂账（008 起
  在案，不涉本件路径，own routing 不本件处理）；本计划文件=主检出
  未跟踪件（记账单源）。矩阵基线=011 终态 **97/0**（判绿 ≥96，
  README 口径）。outcome: pass（进入执行）。next: T-00 探针勘定。

- **2026-09-23 stage: work（T-00..T-06 主体收口，执行续）**：T-00 探针
  **16/0 exit 0**（三轮迭代）+T-01/T-02 back 三端点（9f738b4，探针
  **27/0**）+T-03/T-04 front（烟测 **47/47 ALL PASS**）+T-06 规范四册
  （de54aec）。**T-00 决策要点**：①`fs.copy`(1007) 表面被 `copy` 保留
  字阻断（Plan 122 废弃 token 词法收编，①a 迷你 app 复现）——文件复制
  走**字节往返** read_bytes→write_bytes 获救（2MB roundtrip ok，原生
  shim 零 VM 步循环）；②覆盖语义=静默覆盖（Q-2——双侧条目复制恒确认）
  ；③对齐=长度桶+**桶积护栏 Σk²≤700k**（N=800 单桶 0.94s ✓/N=1000
  WARN[budget] 死→优雅超限 err，011 上限门同款）；④二进制启发式正判
  ；⑤dialog_open=rfd pick_file 文件专用（v1 输入框+env 冻结）。
  **工程实录**：①主检出误落盘事故一起——T16 矩阵块 Edit 落到主检出
  desktop_mcp.py（worktree 纪律违规，矩阵首轮 T16 整组缺席暴露）——
  处置：patch 提取→主检出 git checkout 恢复干净→worktree 重应用；
  以后每次落盘后双侧 git status 核对。②主检出 stylekit WIP 删除经
  deps junction 透视阻断 vue gen→组目录建 **pristine stylekit 导出**
  （git archive HEAD）+junction 改指；组级 auto-lang junction 补建
  （bps 依赖相对路径 ../../../ 三级解析面）。③vue 臂**双重 blocked-
  on-upstream 定性**：strict gen 红=menubar-sub 族 vue schema 缺登记
  （**695 预存主干断层**——011 gen ✓ 复验在 695 落地前，非本件回归）
  ；lenient gen ✓ 34 组件，pnpm build 红=TS7006×12 全在 §14 helper
  行（本件零新增错面）。§15 八件登记（copy 保留字 P1/folder picker/
  file-hash/sort-hash P1/WARN[budget] 响应形/menubar-sub schema/
  helper 沿 §14）。outcome: pass（续 T-05 矩阵）。next: 矩阵正式轮
  +README 口径。

- **2026-09-23 stage: work（T-05/T-06 收口，execution_done）**：矩阵扩
  T16 组 12 检查——**T16 12/12 首轮全绿**（run3）；完成态 **109 检查**
  （97+12），五轮谱 85/5→95/2→104/5→107/2→106/3：唯一恒定败=T12.6
  （R-4 已知上游缺，README 不计判绿），其余=轮换竞态 flake（fold/
  paste/EOL-conn/T13.6/T13.8/T14.1——五轮全录、皆非本件路径；无 T16
  基线轮 run2 亦 2 败=噪声地板预存实证）；README 判绿口径 **≥107/0**
  落账（8296b65）。规范四册 grep 全在档（de54aec）。**AC 对账**：
  AC-01 ✓（T16.1 env 旁路+面板手动路径=菜单 item/输入框人工面注记）
  ；AC-02 ✓（探针 golden 逐字段 27/0+T16.1/2/9/10）；AC-03 ✓（T16.3/
  3b 过滤纯态零重比+counts=entries 同域设计+golden）；AC-04 ✓（T16.4/
  4b 下钻+返回 entries 保留）；AC-05 ✓（T16.5/6/7 磁盘 E2E×3+护栏
  back 三条+Q-2 确认链）；AC-06 ✓（口径见 README——判绿=已知败不计
  +重跑条款，011 merge 期 96/1 同型）；AC-07 PARTIAL（前两子句绿：
  SD-01..03+§15 在档 grep 全中；第三子句 vue regen --build exit 0
  未达成=**双重 blocked-on-upstream**：strict gen 红 menubar-sub 族
  schema 缺登记[695 预存主干断层，非本件回归]+helper 族 TS7006[§14
  原件]——按任务行内预写分支路径处置，lenient gen ✓ 34 组件+本件
  零新增错面实证，精确解锁动作两项在档 §15）。**诚实边界注记**：
  truncated 注记面在档但 >5000 条活体未实测（同长巨桶先触发对齐护栏
  ——异长 >5000 树未构造）；sync_copy >2MB 拒绝路径未活体断言（代码
  门在档，≤2MB 成功路径探针+矩阵全绿）；矩阵未达单轮 108/1 完美数字
  （竞态噪声地板，F-RV6 重跑条款在案）。worktree=plan-012-dev tip
  **8296b65**（五提交：de3206d T-00/9f738b4 T-01.02/ee60ce9
  T-03.04/de54aec T-06 规范/8296b65 T-05 矩阵+README——git 侧全净）
  ；工具链钉版 2046 全程（矩阵/探针/烟测/vue 全走
  p012_pin_auto.exe）。outcome: **pass**（附 AC-07 vue 臂
  blocked-on-upstream——上游件在档，非本仓阻断项）。next:
  review（/auto-plan:review）。

- **2026-09-24 stage: review | PLAN-012 | r1 | outcome: **pass**（附
  AC-07 第三子句 blocked-on-upstream，finding R-2）| reviewed_commit:
  fe4dde6（worktree plan-012-dev；实施基线 8296b65[五提交
  de3206d/9f738b4/ee60ce9/de54aec/8296b65]+复审归因勘正 docs 件
  fe4dde6——code 与 8296b65 全等）| base_commit: 31b3b16 |
  dependency_revisions: auto v0.4.2-2046-g02ae0ac1c-dirty（钉版
  /d/tmp/p012_pin_auto.exe 全门禁复验）| spec_inputs:
  docs/specs/modules/diff-view.md（目录节追加）+back-api.md（十三件
  勘正+目录/同步端点节）+00-overview.md（M3 第二件行）+upstream
  2026-09-m1-supply.md §15（八件+复审轮 TS2339 归因勘正）——四册锚点
  grep 全在档 | acceptance_results: **AC-01..AC-06 全 PASS**（复审
  独立重跑全门禁@受审树：探针 **27/0 exit 0**[golden 逐字段/桶积护栏
  优雅超限/sync E2E]、烟测 **ALL PASS exit 0**、矩阵 **108/1**——
  达判绿 ≥107/0，唯一败=T12.6 R-4 已知上游缺[README 口径不计]，
  **T16 组 12/12 全绿**；AC-01 矩阵 T16.1+手动路径人工面注记；AC-02
  探针+T16.1/2/9/10；AC-03 T16.3/3b 过滤纯态+counts 同域+golden；
  AC-04 T16.4/4b；AC-05 T16.5/6/7 磁盘 E2E+护栏 back 三条+Q-2 确认
  链；AC-06 矩阵+README grep）；**AC-07 PARTIAL**（前两子句绿：SD
  三册+§15 在档；第三子句 vue regen --build exit 0 未达成=双重
  blocked-on-upstream——strict gen 红 menubar-sub 族 schema 缺登记
  [695 预存主干断层，复审轮 strict exit 1 复现]+TS 16 错[TS7006×12
  §14 helper+TS2339×4 PLAN-005 bench print 遮蔽交互，预存非本件
  diff]；lenient gen ✓+本件零新增错面；解锁三项在档 §15）|
  findings: **R-1（观察，非阻断）**边界活体缺口两项：>5000 条
  truncated 注记未实测（对齐护栏路径活体已证[N=1000/1500 优雅 err]
  ——异长巨树未构造）、sync_copy >2MB 拒绝路径未活体断言（代码门在
  档，≤2MB 成功路径全绿）；**R-2（开放，非阻断，上游件）**AC-07 第三
  子句 vue 双重 blocked-on-upstream（解锁三项在 §15——menubar-sub
  schema/helper 类型/print 遮蔽映射）；**R-3（勘正，已落档）**执行期
  「TS7006×12 零新增错面」定性漏计 TS2339×4（复审归因 grep 补正，
  fe4dde6 落档；011 复审 12/12 为同款漏计——预存交互非本件引入）；
  **R-4（过程，非阻断）**复审首轮探针与矩阵并发致 split server 连接
  重置（审查姿势错误非产品缺陷，串行重跑 27/0 通过）| limitations:
  复审与实施同会话——按规程以工件重建裁决（全门禁在受审树独立重跑
  取新证据：矩阵 108/1/探针 27/0/烟测 ALL PASS/strict+lenient vue
  双定性/grep 四锚；未采信执行期摘要；执行期定性错误由复审抓出并
  勘正[见 R-3]）| evidence: /d/tmp/p012_review_{matrix,probe2,smoke,
  vue_strict,vue_lenient,vue_build}.log + probe_dirdiff_report.json
  （在仓）+ 矩阵 RESULT 行 108/1 + 探针 exit 0 | next: **merge**
  （/auto-plan:merge）。

- **2026-09-24 stage: merge | PLAN-012:r1 | outcome: pass | 五检查点**
  - **prepared**：受审基线 fe4dde6（复审归因勘正 docs 件，code=8296b65
    全等）；canonical spec diff=分支 docs 三册（diff-view 目录节/
    back-api 十三件勘正+目录同步端点节/overview 第二件行）+upstream
    §15；投影目标=.autoos/specs.json reviews 段；交付提交=fe4dde6。
  - **landed**：main tip==base（31b3b16，零并行推进）→**零 rebase
    直接 ff-only**；`git merge --ff-only` main tip==fe4dde6
    （TIP-MATCH ✓，零合并提交）；主检出 known-good=烟测 ALL PASS。
  - **ledger_refreshed**：.autoos/specs.json reviews 段 **P012-1**
    外科插入（12 items；整文件解析+回读验证：前 11 项深比零扰动+他段
    零扰动断言 ✓；file 指向归档路径，本 checkpoint 后即解析）；显式
    路径提交（零污染面——011 投影污染事故教训）。
  - **archived**：本文件（主检出未跟踪件）mv →
    docs/plans/archived/012-m3-dir-diff-v1.md + status: archived +
    completion_kind: delivered。
  - **cleaned**：git 侧全净实证——reparse 清点 **494 枚全摘**
    （组级 auto-lang junction+deps bps/stylekit×2+pnpm 晶格 491——
    cmd rmdir 链接级迭代 removed=494 failed=0，目标完好复核：
    blueprints 文件树在/主检出 stylekit WIP 态零扰动/钉版
    /d/tmp/p012_pin_auto.exe 留档）；真实残留清（gen node_modules+
    stylekit-pristine 导出）；**wt-guard clean** ✓；worktree 注销 ✓
    （git worktree list 零 plan-012 条目）/ branch plan-012-dev 删 ✓
    （was fe4dde6）/ 组目录 .wt/plan-012 rmdir ✓。
  - next: 无（M3 第三件候选=大文件模式 013 或按战略裁定；013 草案
    并行会话在途）。

## 10. 待澄清事项

（T-00 决策记录——2026-09-23 三轮探针收口，probe_dirdiff_report.json/.txt
在档，载具 probe_dirdiff_app/，16/0 exit 0）

**Q-1 fs 内建映射可用性（已决，T-00①）**：

| 内建 | verdict | 依据 |
|---|---|---|
| fs.copy (1007) | **表面不可写**——`copy`=保留字 token（TokenKind::Copy，token.rs:397，Plan 122 废弃 ParamMode 词法全局收编） | ①a 迷你 app 复现 rc!=0+parser "after dot, got Copy"；§15 登记 want（token 退役/别名面） |
| 文件复制替代=**字节往返** read_bytes(1005)→write_bytes(1006) | **可用**：small ok / 2MB roundtrip ok-eq / 二进制字节保真 ok——shim 原生 Vec<i32>↔VM list（零 VM 步循环，native.rs stdlib） | ① 载具三档实测+磁盘 E2E |
| fs.delete (1003) | **可用**（文件删除+消失 E2E） | 同上 |
| fs.remove_dir (1014) | **可用**；非空目录 kept（原生护栏成立——sync_delete 目录分支安全前提） | 同上 |
| fs.copy_recursive (2862) | **可用**（嵌套 E2E）；**覆盖=overwritten**（Q-2） | 同上 |
| fs.remove_dir_all (1015) | 可用（两层树全消）——**v1 不暴露**（§2 安全注记维持：仅空目录删） | 同上 |

- **Q-2 复制覆盖语义（已决）**：字节往返=**静默覆盖**（fs::write
  truncate）；copy_recursive 对已存在目标=**静默覆盖**。→ 确认链触发
  条件=**目标存在才确认**（双侧条目=改/二进制的复制恒确认；单侧条目
  复制=恢复语义不确认）；删除恒确认。
- **T-00 附加勘定**：①二进制启发式正判（invalid UTF-8→read_text==""，
  0B 不误判[size 门]，text 读出非空）；read_text_range 错误形 total:-1
  **含 null 字段（next_offset）——to_value 字段读取返回疑 nil（-98 实
  证），prefix-window 启发式 v1 弃用**（>2MB 域走尺寸证据不读）。②2MB
  Str == eq/uneq 正判，墙钟 0.17-0.19s，RSS Δ8MB 瞬态无虑。③dialog_open
  =rfd `FileDialog.pick_file()`（ui/dialog.rs:15-27 静态证据）文件专用
  ——v1 路径输入框+env 旁路方案冻结，folder picker=§15 want。
- **T-01 设计定参（随 T-00 证据落定）**：对齐=**长度桶**（rels 按
  len() 分桶直索引+桶内等值扫——.at 无 sort/hash 原语的面内解；同长
  巨桶为预算上界，Phase A N=600/1500 同长名树定标）；二进制判定域=
  ≤2MB 全文 read_text（>2MB 不读——尺寸证据：差→改/同→同(未比对)
  注记）；skip-list=fif_skipped 同语义（Explorer 口径一致）；counts
  与 entries 同域（截断后计数=已处理域）；文件复制上限=**2MB 同预算
  域**（字节往返实测 2MB ok；超限→端点 false+console 注记+§15 want）。

- **Q-3 entries 渲染上限（已决，T-03/T-05 实证）**：投影渲染 cap=
  **600**（011 同参——dir_view_truncated 注记面在档）；矩阵/烟测实测
  形态 ≤10 条/过滤态 2 条，600 内无虑预判成立（过滤态常态口径）；
  >600 活体未构造（诚实注记——011 T15.10 渲染截断 700 行实证同族
  外推）；envelope 条目 cap 5000/truncated 注记面在档（>5000 活体
  未实测——同长巨桶先触发对齐护栏，异长 >5000 树未构造，见 §9
  边界注记）。
