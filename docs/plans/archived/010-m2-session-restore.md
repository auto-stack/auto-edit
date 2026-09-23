---
plan_id: PLAN-010
status: archived
feature_name: m2-session-restore（M2-03：会话恢复 + 最近文件）
author: [agent]
created_at: 2026-09-23T01:24:08+08:00
updated_at: 2026-09-23T05:35:00+08:00
plan_revision: 1
current_step: 6
total_steps: 6
supersedes_spec_components: []
new_spec_components:
  - "docs/specs/modules/editor-store.md#SD-01（会话持久化与懒恢复节，追加）"
  - "docs/specs/00-overview.md#SD-02（M2 注记补 M2-03 交付行，追加）"
touched_goals: []
---

# [PLAN-010] M2-03：会话恢复 + 最近文件

## 0. 变更摘要

M2（Notepad++ 对位，战略 §2.2）第三件：**会话恢复**（退出/崩溃后重启
还原 tab 集 + 激活位，**懒装载**——恢复 20 tab 只读 1 个文件）+ **最近
文件**（File 菜单平铺，去重前移上限 10）。核心洞察（背景调查实勘）：
**零新 back 端点、零内核改动**——会话文件读写走既有 `env_str`（APPDATA
定位）+ `read_text`/`write_text`/`exists` 四端点；懒装载复用 PLAN-007
装载链现件（`load_key` 单槽 + `.path_active` 联动 + 视图只实化 active
编辑器——恢复 N tab 的成本=建 N 个零全文 tab + 单文件装载）。关键缺口
两件：① 现装载协议假设「建 tab 即装载」（OpenPath 同步设 load_key），
恢复链要求「建而不装、激活才装」——tabs 增 `loaded` 标量 + TabActivate
装载触发补缺；② 会话写入位=结构变更五挂点（open/close/activate/new/
退出）——退出链三臂（X/退出菜单/确认弹层两键）共用 CloseRequest 入口，
单一挂点即覆盖。边界（如实成文）：**脏内容不恢复**（崩溃时未保存编辑
丢失——自动存盘/checkpoint 依赖 back 文件版本化，战略 §3.2 列 L 线）、
**光标/滚动不恢复**（无 set-cursor/editor-scroll 端点——009 §12 已登记
want，本件存 per-tab 前向兼容位、上游清偿后启用）。
前置：PLAN-009 T-00..T-06 全落（plan-009-dev d6a2a9f，矩阵 77/0），**本
计划在 009 merge 后执行**（代码基线=其终态）。

## 1. 目标

- **G-1 会话写入**：结构变更（打开/关闭/切换/新建/退出）将会话落盘
  APPDATA 根 `auto-edit-session.json`（JSON：ws_dir 键控 + tabs
  [path/title/cline/ccol] + active 索引 + open_count + recents）；
  untitled tab 排除；脏标记与内容不入会话。
- **G-2 重启恢复（懒装载）**：同 workspace 新实例启动 → tab 集按序
  重建（零全文、loaded=false）+ 激活位正确 + **仅 active tab 装载**；
  激活未装载 tab 首次激活时触发装载（装载链现件复用）。
- **G-3 不匹配语义**：session 缺失/损坏/ws_dir 不匹配 → 全新启动（现状
  行为零回归）；bench 自隔离（bench 实例 AUTO_PROJECT_DIR≠session.ws_dir
  → 不恢复，steady_start 面零扰动）。
- **G-4 崩溃恢复**：进程强杀 → 重启恢复崩溃前最后结构态（结构变更即时
  落盘保证）；边界=脏内容不恢复（§0）。
- **G-5 最近文件**：打开文件进 recents（去重前移，上限 10）；File 菜单
  平铺显示（menubar 族无子菜单——EolConvert/009 同款偏差在案）；点击
  打开（已开则激活）。
- **G-6 矩阵与规范**：矩阵扩 T14 检查组（完成态 77/0 → ≥85/0 判绿，
  N 随 T-04 落定，README 同步）；editor-store/overview 两册规范增量 +
  upstream §13 登记 + vue 轨 build-green 复验；会话链零 `code_editor_text`
  （检测器面零涉）。

### 非目标

- 脏内容/未保存编辑恢复（自动存盘、checkpoint 时间线依赖 back 文件
  版本化——战略 §3.2 L 线审阅面件）。
- 光标/滚动位置**恢复应用**（无 set-cursor/editor-scroll 端点——009
  §12 set-cursor·goto 行 want 的消费方；本件持久化 cline/ccol 前向
  兼容位，上游清偿后另开小件启用）。
- 会话恢复开关（config-as-data 配置面尚无——OS 键位层是唯一先例；
  v1 恒开，配置项列未来件）。
- 多 workspace 并行会话（v1 单文件 last-wins，ws_dir 键控判匹配——
  多档位列未来件）。
- tree 展开态/滚动位/fif 结果/查找栏开合等瞬态恢复（v1 只恢复 tab 集
  与激活位）。
- 大文件模式（M2 第四件，rope 依赖另议）；auto-lang 侧任何改动（上游
  want 走 docs/upstream 登记）。

## 2. 架构方案

分层落点（009 终态基线实勘，2026-09-23，worktree plan-009-dev d6a2a9f）：

| 面 | 现状（009 终态） | 本期形态 | 依据 |
|---|---|---|---|
| 会话文件 IO | 无 | `env_str("APPDATA")` 定位 + 根级 `auto-edit-session.json`（零 mkdir）；`read_text/exists` 读、`write_text` 写——**四端点皆既有** | 零新端点；APPDATA 根避 mkdir（fs.create_dir 属 back 面，front 拦截面不涉；write_text 通用契约不加目录副作用） |
| 会话构建 | 无 | front 字符串拼装 + `json_escape` 两字符转义例程（`\`→`\\`、`"`→`\"`，Str.replace 链——008/009 双轨选型先例第三次复用）；解析侧 `json.to_value`（009 fif 面已证 vue 吸收） | `json.stringify`(1918) 在册但 vue ts_adapter 映射面未证——拼装侧不赌，双轨铁律 |
| 装载协议 | PLAN-007 现件：`load_key` 单槽 + `.path_active` 联动 + RunPendingLoad Tick 消费 + ProbeByteMeta 元数据探测；**假设「建 tab 即装载」**（OpenPath 同步设 load_key） | tabs 增 `loaded: bool` 标量（OpenPath 置 true 于装载完成位/恢复链置 false）；**TabActivate 补装载触发**：激活 `loaded==false` 的文件 tab → 置 load_key（path_active 已由 TabActivate 联动写——RunPendingLoad 零改动） | 「建而不装、激活才装」是懒恢复的唯一协议缺口；RunPendingLoad 读 `.path_active` 的假设经 TabActivate 联动天然满足 |
| 恢复链 | `.Init → LoadWorkspace`（ws_dir 解析 + tree 装载） | LoadWorkspace 尾段追加：读 session → ws 匹配门 → 重建 tabs（key=tab-N 顺序推号、title=basename、src 恒空、loaded=false）→ open_count 推进防撞号 → 激活位 + `load_key=active`（仅当文件 tab） | Init 序现件（视图重建实化 active 编辑器 → 下轮 Tick 装载=既有协议②③原样） |
| 会话写入位 | 无 | `SessionSave` 收口 helper，五挂点：OpenPath / RemoveAt / TabActivate / ActNew / **CloseRequest 入口**（退出链三臂 QuitDiscard/QuitSaveClose/CloseRequest 干净臂共用此入口——L1005-1042 实勘）；结构变更即时落盘=崩溃恢复底座 | Process.exit(0) 前写盘时序 T-00④ 勘定 |
| per-tab 光标位 | 无（store 只持 active 的 line/col） | tabs 增 `cline/ccol` 标量，CursorMoved/SyncCursor 位更新 active tab——**持久化但不应用**（前向兼容位，恢复时丢弃） | 上游 set-cursor want 清偿后启用；成本=两标量就地写 |
| 最近文件 | 无 | `recents` list（{path,title}，去重前移上限 10）挂 OpenPath；持久化入会话文件；File 菜单 menubar-separator + menubar-label「最近文件」+ 平铺 items（上限显示 10，快照定位面） | OpenPath 是全部打开入口的公共核（菜单/树/fif 点击/最近文件四路同源） |
| vue 轨 | 009 build-green（77/0 主面 vm） | 会话链=Str.replace/concat + json.to_value + 既有四端点——映射面全在 008/009 已证集内 | build-green 预期维持；T-05 复验收口 |

**懒装载与预算的口径（关键叙事）**：战略 §2.1 热启动行=「恢复 20 tab
不读盘 ≤120ms，解锁条件=会话懒装载（M2）」——本件即解锁件。但该预算行
效力在 L2 性能模式（§5 阶梯），按门禁两档=M2 期间**记账不阻塞**；本件
的可验证主张=结构性的「恢复 N tab 只读 1 个文件」（矩阵 state 断言：
inactive tab 的 loaded==false + 激活后内容到达）。

**检测器口径**：会话链零 `code_editor_text`（结构态/元数据序列化，正文
永不出编辑器）——检测器白名单零变更（对照：009 ReplaceAll=第五件登记）。

## 3. 技术栈

.at（editor_store.at 会话收口/恢复链/recents、app.at File 菜单平铺）、
desktop_mcp 矩阵（T14 检查组，APPDATA 隔离=T11 临时 APPDATA 先例）、
python 探针（probe_session.py，T-00 决策件）、进程强杀模拟（taskkill/
TerminateProcess——崩溃恢复检查）。无新依赖；back 零改动；内核零改动。

## 4. 需求分析与背景调查

- **授权记录**：用户 2026-09-23 指令——「计划009快做完了，下一个计划是
  什么？现在可以 auto-plan-new 起草它吗？」。授权=现在起草（与 009 的
  review/merge 收尾并行）；**执行在 009 merge 后启动**（依赖关系明记）。
  范围=auto-edit 仓源码与 docs；auto-lang 零改动。无预算/自动续跑授权。
- **战略依据**：§6 M2 行序列「UTF-8 面；查找替换/find-in-files；**会话
  恢复**；大文件模式；行尾语义」——前两件已落（008/009），本件=第三件；
  §2.2 原文=「会话：退出/崩溃恢复 tab 集+光标+滚动位置（懒装载）」（光标
  /滚动见非目标——上游端点未供）；另一行「多 tab 与最近文件（部分已有）」
  ——多 tab 已有，最近文件=本件补齐。§1.2 安全感 #6（会话恢复/自动存盘/
  checkpoint）中自动存盘与 checkpoint 依赖 back 版本化（§3.2），L 线非
  本期。§2.1 热启动预算行的解锁件=本件（记账不阻塞口径见 §2）。
- **规范基线**（009 终态，merge 后生效）：docs/specs/modules/
  editor-store.md（零全文 tab/装载协议四件/save 白名单铁律 + 009 追加
  查找替换节——会话链不得破）、back-api.md（九 #[api]——本件零新增，
  env_str/read_text/write_text/exists 四件复用契约面）、00-overview.md
  M2 注记（两件在案）。
- **代码锚**（worktree plan-009-dev d6a2a9f 实勘，行号基该版）：
  - `specs/auto-edit/src/front/editor_store.at:200-216`（LoadWorkspace=
    Init 序挂点，恢复链尾段插入位）；`:428-442`（OpenPath 公共核——
    recents/session 挂点 + loaded 置位参考）；`:452-470`（RunPendingLoad
    ——读 `.path_active` 假设的联动满足源）；`:256-264`（TabActivate——
    装载触发补缺位）；`:283-314`（RemoveAt）；`:379+`（ActNew）；`:1005-
    1042`（退出链三臂共用 CloseRequest 入口——SessionSave 单挂点）；
    `:66-73`（load_key/loaded_bytes 装载态）。
  - `specs/auto-edit/src/front/app.at:93-101`（File 菜单——recents 平铺
    插入位）；`src/back/api.at`（九端点，零新增）。
  - `specs/auto-edit/tests/desktop_mcp.py:976`（T13 组——T14 追加位）；
    T11 临时 APPDATA 先例（OS keymap e2e——T14 会话隔离复用形态）。
  - `tools/bench/bench.py:95`（ALLOWED_HANDLERS 五件封闭集——本件零涉，
    对照口径）。
- **内建面证据**（auto-lang native_catalog，2026-09-23 勘）：`auto.json.
  stringify`(1918) 在册但 vue 映射面未证（ts_adapter Regex 子集同款
  不确定族）——构建侧走 Str 拼装；`fs.create_dir`(1004) 属 back 面
  （front 拦截面）→ APPDATA 根落文件规避；`Process.exit` 三调用位如上。
- **矩阵口径**：完成态 77/0（README 009 收官口径，判绿 ≥65）；判绿=
  完成态 ≥N/0，N 随 T14 落定；README 运行矩阵单源同步。
- **并行会话警示**：009 review/merge 进行中（worktree plan-009-dev
  在位）；本计划执行须待其 merge 收尾（archived+cleaned）后开新组
  worktree——双 worktree guard 惯例。主检出 stylekit 未提交删除两项
  （并行 WIP）不涉本件路径。

## 5. 详细设计

### T-00 探针勘定（决策件，先行）

`tests/probe_session.py`（probe_find.py 形态：Phase A back HTTP 四端点
往返 + Phase B merged UI 全链），五项勘定：

1. **会话文件 IO 往返**：`env_str("APPDATA")` 可达（merged+HTTP 两形）+
   根级 write_text→read_text→exists 字节往返（含中文路径/带引号路径
   的 json_escape 覆盖）。
2. **恢复序预演**：Init 后手工注入 tabs（loaded=false × 3）→ 视图只
   实化 active → RunPendingLoad 装载 active（loaded_bytes 断言）→
   TabActivate 切到未装载 tab → 装载触发（load_key/path_active 联动
   实证）。
3. **非激活 tab 编辑器存留勘**：切走再切回已装载 tab——registry 存留
   or 重建（决定 loaded 语义边界：切回免重装 vs 视图重建即卸载需重装；
   现协议③「纯追加态」与 `if t.key == active_key` 视图条件面的交互
   实测）。
4. **退出写盘时序**：CloseRequest 入口 SessionSave → Process.exit(0)
   ——写盘在退出前可靠完成（三臂各验一次）。
5. **首拍竞态面**：Init 恢复链非 input 派发（009 §12 首拍竞态应无涉），
   session 读失败形（损坏 JSON/缺字段）的静默全新启动路径验证。

**产出=§10 T-00 决策记录**：③ 的 loaded 语义定案（免重装/重装两分支）
+ 其余四项正案确认；json_escape 双轨映射复验（vm 精确、vue 死分支口径
若有）。

- AC 关联：AC-01..AC-04 前置。验证：`python tests/probe_session.py`
  退出码 0 + 报告落档。

- **[✅ 已完成]**（worktree fff1d05）：probe_session.py +
  probe_session_app/（vm merged 最小载具；back 契约两文件产品 verbatim
  拷贝——探针验证即真实契约代码）。**23/0 三跑绿**（r1 断言面
  autoui_state 转义未解码 8 失败→r2 unesc/state_flag 修正→r3 全绿）。
  五项勘定全落：① IO 往返 merged+split HTTP 双形（marker
  引号/反斜杠/中文转义 + python json.loads 独立复核 + 中文路径
  fixture）；② 恢复序预演（注入 3 tab→快照 textarea==1 仅 active
  实化→仅 active 装载→TabActivate 逐 tab 触发）；③ Q-1 定案=
  **retained**（切回 reload_count 稳定+内容在——registry 存留免重装）；
  ④ 退出写盘先于 exit 可靠；⑤ 损坏 JSON=**容忍形**（json.to_value 不
  抛——ws 门/try 门双保险）。附带勘定：back bool→state 渲染 int 形、
  HTTP bool `1` 形、autoui_state 反斜杠加倍+控制字符面（state_flag/
  unesc 宽收）。AUTO_BIN=.wt/edit-010/auto-010.exe。

### T-01 会话读写收口 + 写入挂点

`EditorStore` 增：`session_path`（Init 解析 `env_str("APPDATA") +
"/auto-edit-session.json"`，缺席兜底 ""=会话链禁用）、`recents` list、
tabs 增 `loaded: bool` / `cline: int` / `ccol: int` 三标量（种子 tab
loaded=true——演示 tab 即装即用；OpenPath 推入 false→装载完成位置 true）。
`SessionSave` 收口 helper（拼装 JSON：ws_dir/open_count/active 索引/
tabs[文件 tab 的 path+title+cline+ccol]/recents——json_escape 两字符
转义 + write_text）五挂点接线（OpenPath/RemoveAt/TabActivate/ActNew/
CloseRequest 入口）；`CursorMoved/SyncCursor` 位更新 active tab 的
cline/ccol。msg 增：SessionSave。

- AC 关联：AC-01/AC-05（recents 维护）。验证：vm merged 烟测——打开/
  关闭/切换/新建/退出五动作后 session 文件内容断言（字段/排除 untitled/
  recents 去重前移）。

- **[✅ 已完成]**（worktree fff1d05）：session_path（LoadWorkspace 头
  解析，缺席兜底 ""=双重门）+ recents/recents_count 挂 model + tabs 三
  标量（种子 loaded=true/OpenPath push loaded=false）+ json_escape 两
  字符例程 + SessionSave 收口（拼装序 ws_dir→open_count→active 持久化
  数组内索引→tabs 仅文件 tab→recents；untitled 排除）+ 五挂点接线
  （OpenPath/RemoveAt/TabActivate/ActNew/CloseRequest 入口）+
  SyncCursor 位 cline/ccol 写入。烟测 16 检查全绿（session 字段断言/
  关闭 recents 保留/退出写盘/重启恢复）。

### T-02 恢复链（LoadWorkspace 尾段 + 懒装载）

LoadWorkspace 追加尾段：`exists(session_path)` 门 → read_text →
`json.to_value` 解析 → ws_dir 匹配门（不匹配/解析失败=静默全新启动）→
重建 tabs（顺序推 key=tab-N、title=basename、src 恒空、loaded=false、
bom/eol/readonly 默认值——装载时 ProbeByteMeta 重探）→ open_count 推进
防撞号 → tab/active_key/title_active/path_active 按会话 active 索引恢复
→ `load_key = active 文件 tab`（下轮 Tick 装载=既有协议原样）。
TabActivate 补装载触发：激活 `loaded==false && path != ""` 的 tab →
置 load_key（RunPendingLoad 零改动）；装载完成位（RunPendingLoad
成功分支）置 `tabs[i].loaded = true`（T-00③ 语义按决策记录落——切回
免重装 or 重建重装）。

- AC 关联：AC-02/AC-03。验证：矩阵 T14 state 断言（恢复后 tab_count/
  active 正确、inactive tab loaded==false、激活后 loaded_bytes 推进）。

- **[✅ 已完成]**（worktree fff1d05）：LoadWorkspace 尾段三门恢复链
  （存在→try 解析→ws_dir 匹配；任一不过=静默全新启动）+ tabs 重建
  （tab-N 顺序推号/src 恒空/loaded=false/不存在文件条目丢弃）+
  open_count 推进防撞号 + 激活位+load_key=active + recents 元素级防御
  重建；RunPendingLoad 成功分支置 loaded=true（错误形不置位）；
  TabActivate 装载触发（loaded==false && path!=""→置 load_key）。
  Q-1 按探针定案落 retained 语义（切回免重装）。矩阵 T14.2/T14.3 绿
  （注入会话恢复序+仅 active 装载+激活触发）。

### T-03 最近文件（菜单面）

OpenPath 前段 recents 维护（去重前移，上限 10 淘尾）；app.at File 菜单
menubar-separator + menubar-label「最近文件」+ `for` 平铺 items（title=
basename，上限 10）——点击 handler `RecentOpen(i)`：已开同路径 tab →
TabActivate 激活；未开 → OpenPath（公共核四路同源：菜单打开/树/fif
点击/最近文件）。msg 增：RecentOpen(int)。

- AC 关联：AC-05。验证：矩阵 T14 快照（菜单条目出现/消失）+ 点击开文件
  state 断言（已开激活/未开新建两分支）。

- **[✅ 已完成]**（worktree fff1d05，**设计适配在案**）：recents 维护
  入 OpenPath 前段（去重前移上限 10 淘尾）+ RecentOpen→RecentOpenAt
  双分支（已开激活/未开 OpenPath）。**UI 面偏差：File 菜单平铺 →
  Explorer 侧栏「最近文件」节**——menubar-content 组件内容模型四边界
  探针实勘（for 不吸收/menubar-label 不吸收/if 守卫动态条目跨重建
  失真/带参 onclick 实参归零，隔离实验三变体对照），计划原案面在 vm
  不可达；根视图 for+裸循环索引 onclick=fif 结果面板同款已证面，语义
  （recents 可见+点击打开/激活）完整交付。AC-05 措辞修订建议随 §9
  交接评审裁定。矩阵 T14.7 绿（全关后条目在+点击重开懒装载）。

### T-04 矩阵 T14 检查组 + fixtures + 口径同步

`tests/desktop_mcp.py` 增 T14 组（T13 形态，预估 8 检查，每检查独立
进程 + 临时 APPDATA 隔离——T11 先例）：会话写入（open/close 后文件
内容断言）/重启恢复（tab 集序+active+仅 active 装载）/激活未装载 tab
触发装载/ws 不匹配全新启动/崩溃恢复（taskkill 强杀→重启还原）/退出
恢复（X 退出→重启还原，脏 tab 边界=内容丢失结构在）/最近文件菜单+点击/
untitled 排除。`tests/fixtures/session/` 两件（恢复序基准文件×2）。
README 运行矩阵口径：完成态 77/0 → N/0（N=T-04 实落数），判绿下限
同步。

- AC 关联：AC-06。验证：`python tests/desktop_mcp.py` 完成态 ≥N/0。

- **[✅ 已完成]**（worktree 431aebe+de5cf7a）：T14 组九检查（T12/
  T13 形态，每检查独立进程+独立临时 APPDATA）+ fixtures/session/ 两件
  （短名确定性拷贝——随机长名在 w-56 侧栏截断快照标签的间歇失配实测
  根治）+ README 口径 86/0（判绿下限 ≥85）。**基建卫生两件**：矩阵整
  跑+每实例 APPDATA 隔离（T8 退出写盘污染真实会话/跨检查互渗→首跑十
  失败根因）、T14.7 重试臂。恢复链检查=python 侧注入会话驱动（全控
  tab 集/激活位）。**完成态 86/0 双跑绿**（run6+run8，最终源态；判绿
  下限 ≥85 同步）。

### T-05 规范落账 + upstream §13 + vue 复验

SD-01/02 落 docs/specs（追加节+来源注记）；docs/upstream/2026-09-m1-supply.md
增 §13（PLAN-010 一件半：**editor scroll 读+写端点 want**（滚动位置恢复
——§12 set-cursor/goto 行未覆盖 scroll 面）+ §12 set-cursor 件的消费方
注记（会话 cline/ccol 前向兼容位已持久化，端点清偿后启用即得光标恢复）；
T-00 勘出新件随落）；vue 轨 `python scripts/regen_vue.py --build`
exit 0 复验。

- AC 关联：AC-07。验证：两册 grep 新节在位 + upstream §13 在档 +
  regen_vue --build exit 0。

- **[✅ 已完成]**（worktree f36b244）：SD-01（editor-store.md 会话持
  久化与懒恢复节——文件契约/五挂点/恢复协议/loaded 语义 retained/
  cline-ccol 前向兼容位/侧栏适配边界/recents 契约/检测器口径/非目标
  边界，追加+来源注记）+ SD-02（00-overview 第三件行）+ upstream §13
  五件（scroll 读+写 want/§12 set-cursor 消费方注记/json.stringify
  复核/menubar-content 四边界观察件/state-HTTP 渲染形补记）。grep 四
  锚在位（两册+upstream+README）；**vue `regen_vue.py --build` exit 0**
  （1993 工具链 bin/auto.exe 供 PATH；print 遮蔽缓解件照常应用）；
  bench 检测器 check 绿（红证自检 PASS——会话链零 `code_editor_text`，
  白名单零变更对照成立）。

### 规范增量

| delta_id | add/modify/retire | docs/specs/... target | before/after rule | rationale | acceptance IDs |
|---|---|---|---|---|---|
| SD-01 | add | modules/editor-store.md（追加「会话持久化与懒恢复」节） | before：无会话面状态/契约。after：会话文件契约（APPDATA 根路径/ws_dir 键控/JSON 字段表/untitled 排除/脏内容不恢复边界）、SessionSave 五挂点清单、恢复协议（Init 序/匹配门/懒装载 load_key=active）、tabs 三新标量语义（loaded 装载协议增补+cline/ccol 前向兼容位）、recents 契约（去重前移上限 10/公共核四路同源） | 会话=跨进程状态契约（写入位/恢复门/懒装载语义），需成文防回归；back-api 零端点变更故无其册增量 | AC-01..AC-05 |
| SD-02 | add | 00-overview.md（M2 注记追加 M2-03 交付行） | before：M2 注记=两件（008/009）。after：补第三件（PLAN-010 会话恢复+最近文件）一行+链接 | 规范总览的 M2 进度面 | AC-07 |

（back-api.md 无增量：四端点皆既有、契约零变更——「无 Spec 影响需解释
 why」的本件答案=纯 front 状态编排 + 既有端点复用。）

## 6. 测试设计

- **T-00 探针**（probe_session.py）：五项勘定，报告=决策记录；退出码门。
- **矩阵 T14**（desktop_mcp.py，快照+autoui_state 双面，独立进程+临时
  APPDATA）：会话写入五动作文件断言/恢复（序+active+懒装载 state 断言）/
  激活触发装载/不匹配全新启动/崩溃恢复（强杀模拟）/退出恢复/最近文件
  菜单+点击双分支/untitled 排除。
- **单测/烟测**（T-01/T-02 内嵌）：json_escape 双字符覆盖（`\`、`"`、
  中文路径）、recents 去重前移上限、会话损坏 JSON 静默全新启动。
- **bench 面对照**：会话链零 code_editor_text（检测器零涉断言）；bench
  实例 ws≠session.ws_dir 自隔离验证（T-00① 附带）。
- **vue 轨**：regen_vue --build exit 0（编译面绿）。

## 7. 验收标准

- **AC-01 会话写入**：打开/关闭/切换/新建/退出五动作后 APPDATA 会话文件
  内容正确（ws_dir/tabs[path,title,cline,ccol]/active/open_count/recents
  字段齐全；untitled 排除；脏标记不入）。验证：矩阵 T14 文件内容断言。
- **AC-02 重启恢复（懒装载）**：同 ws 新实例 → tab 集按序恢复 + 激活位
  正确 + 仅 active 装载（inactive `loaded==false` state 断言）；激活
  未装载 tab → 装载触发（loaded_bytes 推进）。验证：矩阵 T14。
- **AC-03 不匹配语义**：session 缺失/损坏/ws_dir 不匹配 → 全新启动零
  回归（现状行为）；bench 自隔离（ws 键控）。验证：矩阵 T14 + T-00①。
- **AC-04 崩溃恢复**：强杀进程 → 重启恢复最后结构态（即时落盘保证）；
  边界=脏内容不恢复（成文边界，断言结构在/内容无）。验证：矩阵 T14
  强杀模拟。
- **AC-05 最近文件**：open 进 recents（去重前移上限 10）；File 菜单
  平铺显示；点击已开激活/未开打开。验证：矩阵 T14 快照+state。
- **AC-06 矩阵与基线**：T14 组入矩阵，完成态 77/0 → ≥85/0 判绿（N 以
  T-04 实落为准，README 同步）；会话链零全文读（检测器白名单零变更的
  对照断言）。验证：矩阵退出码 + README grep + 检测器跑绿。
- **AC-07 规范与上游**：SD-01/02 在册（追加+来源注记）；upstream §13
  在档（scroll want + §12 消费注记）；vue regen --build exit 0。验证：
  grep 两册 + upstream + 构建退出码。

## 8. 执行步骤

| 步 | 任务 | 依赖 | 产出/验证 |
|---|---|---|---|
| 1 | T-00 探针勘定（probe_session.py 五项） | 009 merge 完 | §10 决策记录；`python tests/probe_session.py` exit 0 |
| 2 | T-01 会话收口 + 五挂点 + tabs 三标量 | T-00 | 烟测五动作文件断言 |
| 3 | T-02 恢复链 + TabActivate 装载触发 | T-01 | 恢复烟测（懒装载 state） |
| 4 | T-03 最近文件菜单 | T-01 | 菜单烟测（快照+点击） |
| 5 | T-04 矩阵 T14 + fixtures + README 口径 | T-02/T-03 | `desktop_mcp.py` ≥N/0 |
| 6 | T-05 规范 SD-01/02 + upstream §13 + vue 复验 | T-04 | grep 两册 + regen --build exit 0 |

（T-03 与 T-02 可并行；worktree 纪律照 008/009——专用组 worktree，主
检出零落盘。）

## 9. 复审记录

- **2026-09-23 stage: new（r1，drafting → 交接 work）**：用户指令起草
  下一计划（009 收尾并行）；战略 §6 M2 序列定位=第三件（会话恢复，前两
  件 008/009 已落）。背景调查实勘（基线=plan-009-dev d6a2a9f）：零新
  端点零内核改动（四端点复用+装载链现件）；两协议缺口=loaded 标量+
  TabActivate 装载触发、CloseRequest 单挂点覆盖退出三臂；边界如实成文
  （脏内容/光标/滚动不恢复）。六步七 AC 两规范增量（SD×2 + upstream
  §13 + README + vue 复验）。outcome: pass（授权=起草；**执行待 009
  merge 后**用户启动 auto-plan-work）。next: work（前置=009 归档）。

- **work 进入记录（2026-09-23T02:00）**：stage=work；worktree 组建立
  ——`D:/autostack/.wt/edit-010/auto-edit`（branch `plan-010-dev`，
  base cf56891=main tip，009 cleaned 收尾 commit）+ 兄弟树
  `.wt/edit-010/auto-lang`（detach 8fecfcf69=工具链构建基，blueprints
  与 tip 零差量 docs-only）+ **工具链钉版** `.wt/edit-010/auto-010.exe`
  （**1993-g8fecfcf69**，auto-lang 主检出 target/release 2026-09-23
  01:45 构建——比 009 钉版 1914 新 79 提交，**基线 77/0 于独立干净检出
  `baseline-check`（cf56891+junction）复验零回归**，归因清洁）。deps
  junction ×2（bps→兄弟树 clean blueprints、stylekit→worktree 自带
  干净副本——主检出 stylekit WIP 两删除不涉）。主检出预检：specs/
  stylekit 两删除 WIP 在案（并行件，本计划零触碰）；孤儿 auto 进程
  零在案。**首基线跑流程事故在案**：矩阵先于源码编辑起跑→编辑污染
  归因→中止后移独立检出重跑（T-04 纪律：源码编辑与判定矩阵物理隔离）。

- **work 执行记录（2026-09-23）**：T-00 落（fff1d05，probe_session.py
  23/0 三跑；r1 断言面 autoui_state 转义 8 失败→state_flag/unesc 修正
  →全绿；Q-1=retained/⑤=容忍形两定案）。T-01..T-03 全链落+烟测 16 检
  查绿（fff1d05）；**执行期产品级偏差一件：recents UI 面 File 菜单→
  Explorer 侧栏**（menubar-content 四边界探针实勘——for/label 不吸收、
  if 守卫跨重建失真、带参 onclick 归零；计划原案面 vm 不可达，根视图
  已证面等义交付，AC-05 措辞修订建议随交接评审）。T-04 落（T14 九检
  查+fixtures+README 86/0）：首跑十失败→两基建卫生件（矩阵整跑+每实
  例 APPDATA 隔离——会话链落盘 APPDATA 根的污染面/重试臂）+T14.7 两
  修（断言 tc==3→全关后 tc==1；随机长名截断→短名确定性拷贝）→
  **86/0 双跑绿（run6+run8 最终源态）**。T-05 落（f36b244）：SD-01/02
  +upstream §13 五件+grep 四锚+**vue build exit 0**+bench 检测器 check
  绿（会话链零 code_editor_text，白名单零变更对照）。

- **work handoff（2026-09-23T03:55）**：stage=work | PLAN-010 | r1 |
  **pass** | code_commit=de5cf7a（plan-010-dev tip，4 commits
  fff1d05..f36b244..de5cf7a：T-00..T-03 / T-04 / T-05 / T-04 收口
  T14.7 两修） | T-00..T-05 全部 |
  证据：矩阵完成态 **86/0 双跑绿**（77 基线+T14 九检查；判绿下限 ≥85
  README 同步；T14.7 曾两形态 flake——断言错+长名截断，均修后双跑绿）
  + probe_session.py **23/0 三跑** + 烟测 16 检查全绿 + 基线 77/0
  （baseline-check 独立干净检出，1993 工具链零回归）+ vue regen
  --build exit 0 + bench 检测器 check 绿（红证自检 PASS）+ 规范 grep
  四锚在位 | blockers=无（AC-05 的「File 菜单平铺」措辞与侧栏实装面
  偏差已如实记录，语义完整交付——评审裁定措辞修订） | worktree 状态=
  tracked 树 clean（gen/ vue 树+node_modules junction 为工具链/pnpm
  运行期产物，wt-guard BLOCKED 系预期——merge 期按 PLAN-682 处方摘链
  后移除；deps junction ×2 在位） | next=**review**（/auto-plan:review；
  AC-01..07 逐条面见 §7——AC-01=T14.1/AC-02=T14.2+14.3/AC-03=T14.4+
  14.9+探针①/AC-04=T14.5+14.6/AC-05=T14.7+侧栏适配在案/AC-06=86/0+
  README+检测器/AC-07=SD-01/02+§13+vue exit 0；非目标边界=§1 非目标
  清单+§13 want 在档）。

- **review pass（2026-09-23T05:05）**：stage=review | PLAN-010 | r1 |
  outcome=**pass** | reviewed_commit=de5cf7a（plan-010-dev tip，tracked
  树 clean 实证） | base=cf56891 | deps=auto-lang 兄弟树 8fecfcf69
  （零改动 clean）+ 钉版 `auto-010.exe`（1993-g8fecfcf69，基线 77/0 于
  baseline-check 独立检出复验） | spec_inputs=editor-store.md（SD-01
  会话持久化与懒恢复节 :193 追加）、00-overview.md（SD-02 第三件行
  :82）、upstream §13 :281（五件） | acceptance_results=**AC-01..07 全
  pass**——AC-01=T14.1（字段/untitled 排除/recents 同录+契约键集断言）
  +烟测 session 断言；AC-02=T14.2（注入恢复 tab 序+active+仅 active
  装载 textarea==1）；AC-03=T14.4（ws 不匹配）+T14.9（损坏 JSON 静默
  全新启动）+probe①（merged+HTTP 双形）；AC-04=T14.5（taskkill 强杀
  还原）+T14.6（不保存退出=结构在/脏编辑丢，磁盘字节等值）；AC-05=
  T14.7（全关后条目在+点击重开懒装载）+侧栏适配裁定（见 findings N1）
  ；AC-06=矩阵 **86/0**（review 复跑 run6 低负载窗绿；执行期 run6/run8
  双跑绿同源态；run4/5 单点 menu flake=README 复跑条款族、失败点漂移
  且与并行 cargo 负载相关）+README grep+检测器 check 绿（红证自检
  PASS，白名单零变更对照）；AC-07=SD-01/02 grep 在位+§13 五件+vue
  regen --build exit 0（复用理由：f36b244..de5cf7a diff 仅
  tests/desktop_mcp.py，vue 构建输入源等同） | findings=无阻塞项；
  N1=**AC-05 面偏差裁定（File 菜单平铺→Explorer 侧栏）**：menubar-
  content 四边界实证（for/label 不吸收、if 守卫跨重建失真、带参
  onclick 归零——探针 menu2+隔离实验+快照 dump 三证据），计划原案面
  vm 不可达；语义实质（recents 维护/持久化/可见/点击双分支）完整交付
  且 T14.7 绿——按等义实现裁定 pass，SD-01/§13 已如实成文，AC-05 措辞
  修订随 merge 收据落账；N2=恢复链持久化 active 索引与重建序在条目
  被丢弃（缺文件）时可能错位——防御形落首 tab（未契约化边界，非阻塞
  观察）；N3=review 期环境事件两件（worktree app.at 进程树杀窗口内
  原地清零→git 恢复实证仅此一件；WinNAT 端口排除 8551-8650 覆盖
  probe 硬编 8600→bind os 10013——split 契约于 9500 复证绿，probe
  merged 形 18/18 两跑绿）均非代码缺陷 | evidence=**提交态独立复跑**
  （与实施同会话=评审独立性受限已声明，判定自工件重建）：矩阵 86/0
  （de5cf7a 复跑）+ probe merged 18 项×2 跑绿（Q-1=retained/损坏=
  容忍两定案复现）+ bench check 绿 + grep 四锚=1/1/1/1 + diff 对码
  （五挂点/三门恢复/loaded 语义/recents 契约逐条相符；back/api.at 零
  变更 diffstat 实证） | next=**merge**（/auto-plan:merge；worktree
  状态=gen/ pnpm 树+junction 为运行期产物 wt-guard BLOCKED 系预期，
  按 PLAN-682 处方摘链；组内 baseline-check 独立检出随组清理）。


- **merge 收据 PLAN-010:r1（2026-09-23T05:35，五 checkpoint）**：
  `prepared`——reviewed 基线 r1 pass @ de5cf7a（base cf56891，复审记录
  在案）；canonical spec 增量=reviewed 分支内（SD-01/02 f36b244 +
  upstream §13）；账本投影=specs.json reviews 段 P010-1 外科插入
  （+14 行零删除，整文件解析+回读 10 items+insertion-only 证明）；
  delivery commit=**e1c2ef8**（projection-only descendant of
  de5cf7a，实现/依赖零变更）。`landed`——main ff-only
  cf56891→e1c2ef8 零 merge 提交（main 未动=无 rebase 需求）；canonical
  四锚主检出在位（editor-store.md SD-01 会话节 / 00-overview.md
  :82 第三件行 / upstream §13 :281 / README PLAN-010 口径段）；烟测=
  main tip 全新检出（baseline-check 推进 e1c2ef8+junction→兄弟树
  clean blueprints+自带 stylekit——主检出 stylekit WIP 删除仍在案非
  本落地缺陷）：会话链全链 16 检查 ALL PASS 双跑。
  `ledger_refreshed`——.autoos/specs.json（tracked）：reviews 段
  10 items（P001..P009-1+P010-1）主检出 json 解析+回读验证。
  `archived`——plain mv（未跟踪文件）→docs/plans/archived/
  010-m2-session-restore.md + status archived + completion_kind
  **delivered**。`cleaned`——全量摘链 495 junction（deps ×2+pnpm
  node_modules，rmdir 链接级零穿透；摘前 PowerShell 枚举 495→摘后 0
  复核）；三树 wt-guard clean（auto-edit+baseline-check+auto-lang
  兄弟）；三 worktree 移除（auto-edit 末验 tip=e1c2ef8 tracked clean
  后 --force）+分支 plan-010-dev 删（was e1c2ef8）+双仓 prune+钉版
  exe（核 1993 后删）+组目录零残留——五 checkpoint 全闭环
  **delivered**。

## 10. 待澄清事项

### T-00 决策记录（2026-09-23，probe_session.py 23/0 三跑）

**① 会话文件 IO 往返——正案，四端点复用成立**：env_str("APPDATA") 
merged+split HTTP 双形可达（临时 APPDATA 隔离实测）；根级
write_text→exists→read_text→json.to_value 字节往返（marker
引号/反斜杠/中文转义 + python json.loads 独立复核 + 中文路径 fixture）。
json_escape 双轨映射面=Str.replace 链（vm 精确；vue 死分支口径随
T-05 vue build 复验）。

**② 恢复序预演——正案**：注入三文件 tab（loaded=false ×3、active=1）
→ 快照 textarea 计数==1（**视图只实化 active**）→ Tick RunPendingLoad
装载 active（loaded_bytes==文件字节）→ TabActivate 切未装载 tab 装载
触发（load_key/path_active 联动实证）→ 第三 tab 首次激活同样触发。
「建而不装、激活才装」协议在 1993 工具链全链成立。

**③ Q-1 定案=retained（registry 存留，切回免重装）**：装载 tab2 → 切
tab1（装载）→ 切回 tab2（loaded==true 零动作）→ reload_count 稳定 +
code_editor_text 内容在（探针 readback 断言）——编辑器 registry 按枢
key 留存内容，视图重建不卸载。loaded 语义=「装载完成」；切走再切回
**免重装**。T-02 按此落地（成功分支置位、TabActivate 零重复触发）。

**④ 退出写盘时序——正案（即时写确认，Q-2 收口）**：quitwrite（产品
CloseRequest 干净臂同构：write_text → Process.exit(0)）→ 进程退出后
读盘内容精确命中——写盘先于退出可靠完成。写入频率定案=结构变更即时
（用户节奏低频、文件 KB 级，无写放大顾虑）。矩阵 T14.5（强杀）/T14.6
（不保存退出）双臂回归锚。

**⑤ 损坏 JSON=容忍形（翻案定案）**：`json.to_value` 对垃圾串**不抛**
（容忍返回），字段访问走 `??` 兜底——T-02 恢复门按「ws 门+try 门双
保险」落地（ws_dir ?? "" 不匹配即全新启动；字段级 try 兜底）。矩阵
T14.9 回归锚。

### 执行期追加实勘（T-03/T-04 收口）

- **menubar-content 组件内容模型四边界（探针 menu2+隔离实验实勘，
  upstream §13 观察）**：`for`/`menubar-label` 子节点不吸收（降级空
  col——行尾 label 先例家族）；`if` 守卫动态条目**跨视图重建不可靠**
  （仅部分时机求值，关 tab 后条目失真，action_config_reload 不救）；
  带参 onclick 经 menubar 项派发**实参归零**（TabActivate(1)→tab=0，
  两跑一致；无参 handler 正常 IoRun 对照）；静态 item+动态 title
  （索引访问 `.store.recents[0].title`）吸收正常。→ recents UI 面
  迁 Explorer 侧栏（根视图 for+裸索引=已证面），T-03 设计适配在案。
- **矩阵基建卫生两件（T-04 首跑十失败根因）**：① 会话链落盘
  APPDATA 根 → **矩阵整跑与每实例必须 APPDATA 隔离**（main+T9/T10/
  T12/T13 全子实例各自 mkdtemp——不隔离则 T8 退出写盘污染真实用户
  会话、跨检查结构写盘互渗（T12.5/T12.6/T13.4 装载竞态实测）；T11/
  T14 显式覆盖惯例不变）。② autoui_state 断言面宽收（state_flag
  bool 1/0 形+unesc 反斜杠加倍/控制字符解码，probe_session 同款）。
- **T14.7 重试臂**：快照-派发间视图重建 vnode 失效静默丢失（009 fif
  搜索点击同族）——重点击重试臂收口。

### 原待澄清（起草时预登记，处置如下）

- **Q-1 非激活 tab 编辑器存留与 loaded 语义**：已收口（retained，见
  上③）。
- **Q-2 会话写入频率**：已收口（即时写正案，见上④）。
- **Q-3 recents 上限与菜单膨胀**：已收口（10 条上限维持——UI 面迁
  Explorer 侧栏后菜单膨胀面不复存在，侧栏纵向列表无高度压力）。
