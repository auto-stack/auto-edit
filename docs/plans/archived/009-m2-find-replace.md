---
plan_id: PLAN-009
status: archived
feature_name: m2-find-replace（M2-02：查找替换 + find-in-files）
author: [agent]
created_at: 2026-09-22T21:34:04+08:00
updated_at: 2026-09-23T03:05:00+08:00
plan_revision: 1
current_step: 7
total_steps: 7
completion_kind: delivered
supersedes_spec_components: []
new_spec_components:
  - "docs/specs/modules/editor-store.md#SD-01（查找替换状态与 effective pattern 拼装节，追加）"
  - "docs/specs/modules/back-api.md#SD-02（搜索服务端点节 + #[api] 计数勘正 7→9）"
  - "docs/specs/00-overview.md#SD-03（M2 注记补 M2-02 交付行，追加）"
touched_goals: []
---

# [PLAN-009] M2-02：查找替换 + find-in-files

## 0. 变更摘要

M2（Notepad++ 对位，战略 §2.2）第二件：**查找替换四态（正则/大小写/整词/
转义）+ 全部替换 + 跨文件查找（find in files）**首次成文并落测。核心洞察
（背景调查实勘）：**查找链内核件已齐**——`code_editor` DSL 已有 `search:`
prop（Plan 413：live 高亮 + 跳首匹配，a2r/vue 生成器与 RQ 投影器三面在册）
+ VM 内建 `code_editor_find(key)`（下一处、回绕、快照隔离）；**缺的全在
编排层**（查找栏 UI、模式拼装、替换服务、find-in-files）。落地路径：
三开关由 front 拼装为**单一 effective pattern 串**（字面模式转义元字符 /
大小写 `(?-i)` 内联旗标 / 整词 `\b` 锚），查找面与替换面共用同一串保语义
一致；**替换与 find-in-files 的正则执行挪 back 新两端点**（`regex_replace`
/`search_files`）——back 走 AutoVM（Rust regex，双轨同语义），front 零
`Regex.*` 调用（绕开 ts_adapter 映射面缺口——`find_all`/`is_match` 无
vue 映射，跨轨禁补件裁定不破）。上游四件 want（上一处/匹配计数/单处替换
端点/goto 行）登记 docs/upstream §12 不实做。
前置：PLAN-008 已 delivered 归档（fda9cdb，矩阵完成态 57/0），M1 全收官。

## 1. 目标

- **G-1 查找栏**：Ctrl+F / 菜单「编辑→查找」开栏；Ctrl+H 展开替换行。
  输入即高亮（内核 search prop live）+「下一处」（按钮/F3）跳转选中。
- **G-2 四态开关拼装**：正则（默认字面+转义）/ 大小写（默认不敏感）/
  整词（默认关）三开关 → 单一 effective pattern；同一串驱动查找高亮、
  替换与 find-in-files（语义一致性由同串保证）。
- **G-3 全部替换**：Replace All 生效（编辑器内容 + 落盘 E2E 断言）+
  console 计数反馈；readonly tab 拦截（PLAN-008 兜底语义延续）。
- **G-4 find-in-files**：back 新端点 `search_files`（工作区递归、逐行
  匹配、`file:line:预览` 条目、上限语义）；front 结果面板（console 面板
  形态组件）+ 点击条目打开文件（pattern 高亮延续到新 tab）。
- **G-5 矩阵与规范**：矩阵扩 T13 检查组（完成态 57/0 → ≥65/0 判绿，
  N 随 T-05 落定）；检测器白名单登记 ReplaceAll（第三件显式全文操作，
  EolConvert 先例）；editor-store/back-api/overview 三册规范增量 +
  upstream §12 登记 + vue 轨 build-green 复验。

### 非目标

- 单处替换（「替换当前选中处」——选区字节偏移在内核手里，front 拿不到；
  上游 `code_editor_replace_next` 端点 want，§12 登记）。
- 上一处差异导航（内核 SearchState 只有 find_next；上游 want）。
- 匹配计数 n/m 显示（front 零全文 tab 拿不到计数底数；上游 match_count
  端点 want。替换计数反馈≠此件——back 侧可数）。
- find-in-files 结果点击**跳行定位**（无 set-cursor/goto 行端点；v1=开
  文件+pattern 高亮首匹配。上游 want）。
- 跨行正则匹配（内核逐行 find 语义对齐，find-in-files 同口径）。
- 大文件 find-in-files（>10MB 跳过，v1 上限语义）；目录过滤/排除模式。
- 会话恢复、大文件模式（M2 其余件，另立计划）。
- auto-lang 侧任何改动（上游 want 走 docs/upstream 登记）。

## 2. 架构方案

分层落点（背景调查实勘，2026-09-22，auto-lang 工具链 1914 钉版勘）：

| 面 | 现状 | 本期形态 | 依据 |
|---|---|---|---|
| 查找高亮/跳转 | 内核已齐：`code_editor` DSL `search:` prop（Plan 413，live 高亮+跳首匹配；renderer.rs apply_search + native_projector.rs 双面）；VM 内建 `code_editor_find(key)`（2914：下一处、回绕、选区、快照隔离、折叠区自动展开） | 零内核改动；front 接线：查找栏 state → search prop 绑定 + find_next 调用 | 查找链是三面（vm/a2r/RQ）已验证路径 |
| 大小写 | 内核 `SearchState` 硬编码 `case_insensitive(true)`（core/mod.rs RegexBuilder） | front 拼 `(?-i)` 内联旗标前缀——Rust regex 内联旗标可覆盖 builder 旗标（T-00①探针实证后定案；若探针翻案→降级=大小写开关仅作用于替换/find-in-files 面（back 'i' 旗标），高亮面登记上游 want） | 语义一致性：同一 effective 串 |
| 整词/转义 | 无 | front 拼装：整词=首尾 `\b` 锚；字面模式=元字符转义例程（Str.replace 链，14 字符 `\^$.|?*+()[]{}{}`；Str.replace/len 双轨皆有映射——PLAN-008 EOL 计数同款选型） | 纯 .at 字符域 |
| 替换 | 无（内核无 replace 端点；front 拿不到选区字节偏移——cursor_col 是 char 列，char→byte 换算需全文） | **back 新端点 `regex_replace(text, pattern, replacement, global)`**：text 经 `code_editor_text` 读出（显式命令路径）→ back Regex.replace（Rust regex，'g' 旗标）→ 回写=结构化 `edit(0, len, out)` 全文重写（EolConvert 链同款）+ delta drain-弃 + dirty。检测器白名单登记第三件 | 正则执行挪 back=双轨同语义（front 零 Regex.* 调用，ts_adapter `find_all`/`is_match` 无映射的坑绕开）；EolConvert 先例全套复用 |
| find-in-files | 无 | **back 新端点 `search_files(path, pattern, limit)`**：`fs.walk_files`（2847 在册）递归 + `fs.metadata` 大小门 + 逐行 `Regex.test`（行号天然，跨行放弃=内核同口径）+ 条目 `{file, line, preview}` JSON 交付（标量返回铁律）；front 结果面板=console 面板形态组件（state 断言面） | back AutoVM 双轨同形（split/vue 经 HTTP 同 back）；front 零 fs.* 铁律不破 |
| 查找栏 UI | 无 | **根视图**（Plan 449 约束：快照定位交互必须留根——tab 条/弹层同款）tab 条与编辑区之间条件行：input（`value:` 双向绑定先例 031）+ 开关按钮组 + 下一处/替换/全部替换/find-in-files 按钮 | 矩阵快照定位依赖 |
| vue 轨 | code_editor 装载位断点死分支在案（upstream §10-3） | 查找栏=input/button 基础 kind（vue 全映射）；正则面全在 back → 预期 build-green；code_editor search prop 的 vue 发射面=死分支内（T-06 复验收口） | 跨轨禁补件裁定 |

**检测器口径（关键约束）**：tools/bench「编辑路径全量读检测器」白名单现为
ActSave/QuitSaveClose + EolConvert（登记制封闭集）——ReplaceAll 是第三件
显式全文操作（读出+重写同 EolConvert 形态），白名单扩登记；查找/下一处/
find-in-files 路径**零全文读**（search prop 增量 diff 进内核 + 行级流式）。

**effective pattern 拼装协议（单一事实源）**：store 收口 helper
`SyncFindEffective`——输入 `find_query` + 三开关 → 产出 `find_effective`
（供 search prop 绑定与两端点消费）。拼装序：字面模式先转义 → 大小写
敏感前缀 `(?-i)` → 整词首尾 `\b`。空 query → 空串（内核语义：清搜索态）。

## 3. 技术栈

.at（editor_store.at 拼装/收口、app.at 根视图查找栏、back/{api,fsys}.at
两端点）、actions DSL（Ctrl+F/Ctrl+H/F3/Ctrl+Shift+F + menubar）、
desktop_mcp 矩阵（T13 检查组）、python 探针（probe_find.py，T-00 决策件）、
tools/bench 检测器白名单。无新依赖；内核零改动。

## 4. 需求分析与背景调查

- **授权记录**：用户 2026-09-22 指令——「计划008已经完成，按照我们的战略
  计划，下一个计划是什么？请 auto-plan-new 写出下一个计划」。授权=按战略
  序列起草下一计划（本件）；执行/work 待用户另行启动。范围=auto-edit 仓
  源码与 docs；auto-lang 零改动（上游 want 登记）。无预算/自动续跑授权。
- **战略依据**：战略 §6 路线图 M2 行=「UTF-8 面（BOM/无损兜底）；查找
  替换/find-in-files；会话恢复；大文件模式；行尾语义」——PLAN-008 交付
  首件（UTF-8 面+行尾），本件为第二件（查找替换/find-in-files）；§2.2
  原文=「查找替换：正则、大小写、整词、转义，跨文件查找（find in
  files）」。节奏纪律：一阶段一主题。
- **规范基线**：docs/specs/modules/editor-store.md（零全文 tab/save 位
  白名单铁律/装载协议——查找链不得破）、back-api.md（七端点+标量返回
  铁律+pac 不写 api:）、00-overview.md M2 注记（PLAN-008 首件在案）。
- **内核现状证据**（auto-lang 1914，2026-09-22 勘）：
  - `code_editor` DSL `search: String` prop（ui/view.rs:666-667「Regex
    search pattern ("" = off). Matches highlight live」）；renderer.rs
    `apply_search`（set_search diff + 非空首跳，VM/rust 两路统一）；
    native_projector.rs:2408（RQ 面同接线）；a2r 生成器支持该 prop
    （ui_gen/rust.rs:4177-4181，字面量与 Ident 绑定两形态）。
  - VM 内建 `code_editor_find(key)`（native_catalog.rs 2914；core/mod.rs
    `find_next`：光标后下一处、回绕、选区选中、滚动入视、折叠区展开、
    rope 快照隔离 Plan 673 T-05）。
  - 内核 `SearchState`：`RegexBuilder.case_insensitive(true)` 硬编码
    （core/mod.rs:410）；仅 find_next 无 find_prev；匹配数无端点。
  - 语言面：`Str.replace/len/substr/find/split` 有 vue ts_adapter 映射
    （PLAN-008 EOL 计数选型实证）；`Regex.match/test/replace/split` 有
    vue 映射但 `Regex.find_all/is_match` **无**（ts_adapter.rs 1168-1260，
    Plan 028 F4 子集）——front 禁用后两者；vm 侧 `Regex.match` 'g'+'i'
    旗标 + 250 条上限（stdlib.rs push_regex_match_list）；`Regex.replace`
    'g' 旗标（stdlib.rs 6652）。
  - back 可用：`fs.walk_files`（2847）/`fs.metadata`（2861）/`File.*`
    （back 层合法，front 拦截面不涉）；try/catch 在语言面（041-trycatch
    先例）。
- **代码锚**：`specs/auto-edit/src/front/app.at`（根视图/actions 声明/
  on 薄委托三挂点；alert-dialog 条件行先例 L244-255）、
  `src/front/editor_store.at`（store 状态/msg/handler 惯例；EolConvert
  链 L537-586=检测器白名单登记件；console_log 反馈先例）、
  `src/back/{api,fsys}.at`（#[api] 契约+实现错名惯例）、
  `src/front/console_panel.at`（结果面板组件形态先例：无 props 直读
  store + autoui_state 断言面）、`tools/bench/bench.py:95`
  （ALLOWED_HANDLERS 封闭集={ActSave,QuitSaveClose,WriteFidelity,
  EolConvert}——ReplaceAllRequest 将为第五件）、
  `tests/desktop_mcp.py` T12 组（L781 起，PLAN-008 检查组挂点先例）、
  `tests/fixtures/`（字节基准先例）。
- **矩阵口径**：完成态 57/0（PLAN-008 收官态）；判绿=完成态 ≥N/0，N 随
  T13 组落定递增；README 运行矩阵单源同步。
- **遗留警示**：主检出 git 状态有并行会话 WIP（specs/stylekit 未提交
  删除两项）——本计划不动该路径；worktree 纪律照 PLAN-008（双 worktree
  guard）。

## 5. 详细设计

### T-00 探针勘定（决策件，先行）

`tests/probe_find.py`（probe_bytefidelity.py 形态：Phase A back HTTP +
Phase B merged UI 全链），vm merged 实例 + python 断言，五项勘定：

1. **search prop 绑定态**：`search: .store.find_effective` Ident 绑定
   （非字面量）在 vm 轨 live 生效（输入变更→高亮更新+首跳）；a2r 生成
   路径 Ident 形态编译过（rust.rs:4181 分支在案，编译面验证即可）。
2. **`(?-i)` 内联旗标 vs 内核 builder 旗标**：大小写敏感 pattern（如
   `(?-i)Alpha`）经 search prop 后 find_next 是否跳过小写匹配——
   Rust regex 文档语义=内联覆盖 builder，实测定案；翻案则走 §2 降级路径
   并登记上游 want（set_search case 旗标）。
3. **整词 `\b` 锚**：`pattern \bfoo\b` 高亮不含 `foobar`（vm 实测）。
4. **input 写回语义**：`input (value: .store.find_query) +
   oninput: .FindInput` 形态下 store 字段写回时机（031 先例=框架写回后
   handler 触发；实测 autoui_state 断言 find_query 值）。
5. **替换链预演**：`code_editor_text` 读出 → back regex_replace（HTTP
   形态）→ `edit(0, len, out)` 重写 → delta drain-弃 → dirty/SyncCursor
   链完整性（EolConvert 链复用面勘定）；`(?i)`/`(?-i)` 前缀串经
   `Regex.replace` 'g' 的 vm 行为。

**产出=§10 T-00 决策记录**：每面「仓内可解 / 降级 / 上游 want」+ 依据；
大小写面定案（正案 `(?-i)` / 降级 back-only）在此落。

- **[✅ 已完成]**（worktree 7c1e866）：probe_find.py + probe_find_app/
  （vm merged 最小载具）；`AUTO_BIN=.wt/edit-009/auto-009.exe python
  tests/probe_find.py` exit 0，**23/0 双跑绿**（r4 三变体对照 + r5 定驻
  重试卫生后终态）。决策全落 §10。

- AC 关联：AC-01..AC-04 前置。验证：`python tests/probe_find.py` 退出码 0
  + 报告落档。

### T-01 store 查找态与拼装收口

`EditorStore` 增：`find_open/find_replace_mode`（栏开合）、`find_query/
find_replacement`、三开关 `find_case/find_word/find_regex`（默认
false/false/false=字面+不敏感+非整词）、派生 `find_effective`（SyncFindEffective
收口：转义→旗标→锚拼装序；输入/开关变更位重算，模板只读惯例）。
字面转义例程 `regex_escape(s)`：14 元字符 Str.replace 链（两轨映射面内）。
msg 增：FindInput, FindToggleCase, FindToggleWord, FindToggleRegex,
FindNext, FindClose, ReplaceAllRequest, FifSearch, FifOpen, FifClose。

- AC 关联：AC-03。验证：vm merged 烟测 autoui_state 读 find_effective
  四组合断言（字面转义/正则直通/大小写前缀/整词锚）。

- **[✅ 已完成]**（worktree 6f0a846）：store 查找态九字段 + msg 十件
  （FindInput/FindReplaceInput 带参= T-00④ 首参形；SyncFindEffective
  内部 helper；FindOpen/FindReplaceOpen 开合为计划 msg 清单必要扩）+
  regex_escape 模块级例程。拼装四组合烟测过（T13.1a-d 矩阵断言面收
  口，89a44fe）。

### T-02 查找栏 UI 与查找链

根视图（app.at）tab 条与编辑区之间条件行：input（value 绑定
`.store.find_query`）+ 三开关按钮（variant 切换态）+「下一处」「×」；
replace_mode 展开行：替换 input + 「全部替换」。actions DSL 增
`edit.find`（Ctrl+F）/`edit.replace`（Ctrl+H）/`edit.find-next`（F3）/
`search.find-in-files`（Ctrl+Shift+F）；menubar 编辑菜单增对应四项
（menubar 族平铺惯例）。查找链接线：code_editor 元素增
`search: .store.find_effective`；FindNext → `code_editor_find(active_key)`
（tab_count>0 门）+ SyncCursor。

- AC 关联：AC-01/AC-02。验证：矩阵 T13 快照（栏/按钮/input 定位）+
  autoui_state（cursor_line 经 FindNext 推进）。

- **[✅ 已完成]**（worktree 6f0a846）：根视图查找栏（input 首参形 +
  三开关双分支 variant + 下一处/×）+ 替换行（Ctrl+H）+ actions 四命令
  （edit.find/edit.replace/edit.find-next/search.find-in-files）+
  menubar 编辑菜单四项 + code_editor `search: .store.find_effective`
  Ident 接线。矩阵 T13.1（开栏/拼装/×关栏）+ T13.2（推进/回绕）收口
  （89a44fe）。

### T-03 替换链（back regex_replace + ReplaceAll）

back 两件：`api.at` 增 `regex_replace(text, pattern, replacement,
global) str`（POST；返回 JSON `{out, count}`——count 经 `Regex.match
"g"` 列表长度，250 上限语义入契约注释）+ `fsys.at` 实现体
`regex_replace_json`（Regex.replace 'g'/单处 + 计数）。front
`ReplaceAllRequest` handler：readonly tab 拦截（复用 WriteFidelity 拦截
面）→ `code_editor_text` 读出（检测器白名单登记第三件）→ back 端点 →
`json.to_value` 解包 → `edit(0, len, out)` 全文重写 + delta drain-弃 +
dirty + SyncCursor + console_log 计数（「替换 N 处」）。空 query/零匹配
零动作。检测器白名单（tools/bench）同步扩 ReplaceAllRequest + 注释更新。

- AC 关联：AC-04/AC-07。验证：矩阵 T13g/T13h（fixture 多处含大小写/
  词中匹配 → 替换 → save E2E 落盘回读断言 + 计数 state/console）。

- **[✅ 已完成]**（worktree 6f0a846+d6a2a9f）：back regex_replace（POST
  /api/regex_replace；marker 算术计数；**大小写不敏感默认+旗标前缀透传
  ——T13.3 实勘裸 Regex.replace case-sensitive 与高亮面劈叉后补齐**）
  + fsys.regex_replace_json + front ReplaceAllRequest（readonly 拦截/
  空 query 零动作/计数反馈）+ bench 白名单第五件。矩阵 T13.3（E2E 落盘
  +「替换 4 处」）/T13.4（readonly 拦截+哈希零变）/T13.5（空 query）
  收口（89a44fe）。

### T-04 find-in-files（back search_files + 结果面板）

back：`api.at` 增 `search_files(path, pattern, limit) str`（GET；JSON
`{results:[{file,line,preview}], truncated:bool}`）+ `fsys.at` 实现
`search_files_json`：`fs.walk_files` 递归 + `fs.metadata` 大小门
（>10MB 跳过）+ try/catch 读（非法 UTF-8/锁定跳过）+ 逐行 `Regex.test`
（行号天然；preview=行文本截断 200 字符）+ 全局条数上限（默认 500，
truncated 标记）。front：`fif_results/fif_count/fif_truncated` 状态 +
`FindResultsPanel` 组件（console_panel 形态：无 props 直读 store +
scroll 列表 + 条目 onclick 直调 store.OpenPath + pattern 高亮延续）+
FifSearch handler（back 调用 + json.to_value 解包）。根视图挂面板
（console_open 同位条件区）。

- AC 关联：AC-05/AC-06。验证：矩阵 T13i/T13j（端点 E2E 结果数/条目
  形态断言 + autoui_state；点击条目后 tabs 增断言）。

- **[✅ 已完成]**（worktree 6f0a846+d6a2a9f，选型偏差在案）：back
  search_files（GET；JSON {results,count,truncated}）+ 根视图内联结果
  面板（**计划原案 FindResultsPanel 组件形态改内联——Plan 449 快照
  定位约束：条目点击必须 MCP 可达，组件子树对快照不可见**）+ FifSearch/
  FifResultClick（OpenPath 公共核复用）。递归枚举=fs.list_dir（fs.walk
  codegen 错名/fs.walk_files 白名单缺登记两 upstream 件，§12）；噪声
  过滤镜像 tree skip-list（剥根相对路径+前导段归一）；count 由 back
  交付（列表 .len() 规避面）。行点击载荷=裸循环索引（TabActivate(i)
  先例；字段访问载荷 r.file 经 MCP 派发面携带字面量不解析——d07ce50
  实勘收口）。矩阵 T13.6（端点+条目点击）/T13.7（500 上限截断）/
  T13.8（>10MB 门）收口（最终态 d07ce50）。

### T-05 矩阵 T13 检查组 + fixtures + 口径同步

`tests/desktop_mcp.py` 增 T13 组（T12 形态，预估 8 检查）：开栏/拼装四
组合/find_next 推进/Replace All E2E 落盘/计数反馈/find-in-files 端点/
结果点击/上限截断。`tests/fixtures/find/` 三件：`find_basic.txt`（多处
匹配+大小写混合+词中匹配）、`find_escape.txt`（元字符字面）、
`find_fif/` 目录（两文件交叉命中）。README 运行矩阵口径：完成态
57/0 → N/0（N=T-05 实落数），判绿下限同步；bench 检测器全量跑绿。

- AC 关联：AC-07。验证：`python tests/desktop_mcp.py` 完成态 ≥N/0 +
  `python tools/bench/bench.py` 检测器段白名单扩
  （ALLOWED_HANDLERS + ReplaceAllRequest）后全绿。

- **[✅ 已完成]**（worktree 89a44fe+d6a2a9f+d07ce50）：T13 组二十检查
  （13.1 开栏/拼装四组合/×关栏、13.2 推进回绕、13.3 E2E、13.4 readonly、
  13.5 空 query、13.6 端点+点击、13.7 截断、13.8 大小门）+ fixtures/
  find/ 四件 + README 口径 **77/0（≥65 判绿）**。完成态 **77/0 双跑绿
  （最终源态 d07ce50）**；bench check 绿（红证自检 PASS + 白名单扩后
  真实扫描不红）。T13 基建勘定（注释在案）：AUTO_OPEN_PATH 被动消费仅
  AUTO_BENCH 门（点+按钮式打开）/fif 面板先开再搜索/console 新行在头
  （倒序）/eff 断言需状态文本转义解码/三处点击重试臂。

### T-06 规范落账 + upstream §12 + vue 复验

SD-01..03 落 docs/specs（追加节+来源注记）；docs/upstream/2026-09-m1-supply.md
增 §12（PLAN-009 四件 want：find_prev / match_count 端点 /
code_editor_replace_next（单处替换）/ set-cursor·goto 行（fif 跳行），
+ T-00② 若翻案的 set_search case 旗标件）；vue 轨
`python scripts/regen_vue.py --build` exit 0 复验（预期绿：查找栏基础
kind + 正则面全在 back；code_editor search prop vue 发射面死分支口径
注记）。

- AC 关联：AC-08。验证：三册 grep 新节在位 + upstream §12 在档 +
  regen_vue --build exit 0。

- **[✅ 已完成]**（worktree d6a2a9f）：SD-01（editor-store.md 查找替换
  节）+ SD-02（back-api.md 九 #[api] 勘正 + 搜索服务端点节）+ SD-03
  （00-overview M2 第二件行）+ upstream §12 九件（四 want + 五观察件，
  超计划原案四件）+ vue 轨 regen_vue --build **exit 0**（to_value 内联
  形=JSON.parse 吸收面；typed str 中间层 TS2339 教训在案；code_editor
  search prop vue 发射面=死分支口径注记不变）。grep 三册新节在位。

### 规范增量

| delta_id | add/modify/retire | docs/specs/... target | before/after rule | rationale | acceptance IDs |
|---|---|---|---|---|---|
| SD-01 | add | modules/editor-store.md（追加「查找替换状态与 effective pattern 拼装」节） | before：无查找面状态/契约。after：find 状态字段清单、SyncFindEffective 拼装协议（转义→旗标→锚序）、ReplaceAll=检测器白名单登记件（第三件）+ EolConvert 链复用、fif 结果态（组件 state 断言面） | 拼装协议是三消费面（高亮/替换/fif）单一事实源，需契约化 | AC-01..AC-04 |
| SD-02 | add+modify | modules/back-api.md（追加「搜索服务端点」节 + 契约计数勘正） | before：七 #[api]。after：九 #[api]（增 regex_replace/search_files）；两端点契约（参数/返回 JSON 形/250·500 上限语义/大小写不敏感默认+`(?-i)` 前缀约定/逐行匹配口径/10MB 跳过） | 端点=跨轨语义一致性的落点；上限语义需成文 | AC-04..AC-06 |
| SD-03 | add | 00-overview.md（M2 注记追加 M2-02 交付行） | before：M2 注记=首件（PLAN-008）。after：补第二件（PLAN-009 查找替换+find-in-files）一行+链接 | 规范总览的 M2 进度面 | AC-08 |

## 6. 测试设计

- **T-00 探针**（probe_find.py）：五项勘定，报告=决策记录；退出码门。
- **矩阵 T13**（desktop_mcp.py，快照+autoui_state 双面）：栏开合（Ctrl+F
  快捷键与菜单双入口）、find_effective 拼装四组合 state 断言、find_next
  cursor_line 推进、Replace All E2E（fixture→替换→save→磁盘回读字节
  断言，T12 形态）、计数反馈、search_files 端点（结果数+条目字段）、
  条目点击开文件、truncated 截断形态。
- **单测/烟测**（T-01/T-03 内嵌）：转义例程四组合、readonly 拦截、
  空 query 零动作。
- **bench 检测器**：白名单扩后全绿（ReplaceAll 登记件）；查找链路径
  零全文读（search prop 增量面）不受检测器影响。
- **vue 轨**：regen_vue --build exit 0（编译面绿；运行面死分支口径
  注记不扩）。

## 7. 验收标准

- **AC-01 查找栏与入口**：Ctrl+F / 编辑菜单开查找栏（快照可见 input +
  三开关 + 下一处按钮）；Ctrl+H 展开替换行；Esc/× 关栏。验证：矩阵
  T13 快照定位 + autoui_state `find_open/find_replace_mode`。
- **AC-02 查找高亮与跳转**：输入 query → 激活编辑器内匹配 live 高亮
  （search prop）+ 首匹配跳转；F3/「下一处」→ cursor_line 按匹配序推进
  （末匹配后回绕）。验证：矩阵 T13 autoui_state cursor_line 序列断言。
- **AC-03 四态拼装**：字面模式（默认）元字符转义；正则模式直通；大小写
  开关 → `(?-i)` 前缀（T-00② 正案）或降级口径（§2）；整词 → `\b` 锚。
  同一 `find_effective` 驱动三消费面。验证：矩阵 T13 state 断言
  `find_effective` 四组合期望串。
- **AC-04 全部替换 E2E**：fixture（多处+大小写混合+词中）→ 全部替换 →
  编辑器内容正确（词中匹配按整词开关语义）+ save 落盘字节断言 +
  「替换 N 处」console/计数反馈；readonly tab 拦截；空 query 零动作。
  验证：矩阵 T13g/h + 磁盘回读。
- **AC-05 find-in-files 端点与结果**：search_files 对 fixtures 目录
  返回正确条目集（file/line/preview 字段、大小写/整词语义与查找面同
  effective 串一致）；>500 条 truncated；>10MB 跳过。验证：矩阵 T13i
  端点 E2E + state 断言。
- **AC-06 结果交互**：点击结果条目 → 对应文件 tab 打开（OpenPath 复用）
  + pattern 高亮在新 tab 生效（首匹配跳转）。验证：矩阵 T13j。
- **AC-07 矩阵与基线**：T13 组入矩阵，完成态 57/0 → ≥65/0 判绿（N 以
  T-05 实落为准，README 同步）；bench 全量读检测器白名单扩
  ReplaceAllRequest 后全绿。验证：两脚本退出码 + README grep。
- **AC-08 规范与上游**：SD-01..03 在册（追加+来源注记）；upstream §12
  ≥4 件 want 在档；vue regen --build exit 0。验证：grep 三册新节 +
  upstream §12 + 构建退出码。

## 8. 执行步骤

| 步 | 任务 | 依赖 | 产出/验证 |
|---|---|---|---|
| 1 | T-00 探针勘定（probe_find.py 五项） | — | §10 决策记录；`python tests/probe_find.py` exit 0 |
| 2 | T-01 store 查找态 + SyncFindEffective | T-00（拼装定案） | 烟测 find_effective 四组合 |
| 3 | T-02 查找栏 UI + actions + 查找链接线 | T-01 | vm 烟测 + T13 前段可跑 |
| 4 | T-03 back regex_replace + ReplaceAll + 白名单 | T-01（T-00⑤ 预演） | 替换 E2E 烟测；检测器绿 |
| 5 | T-04 back search_files + 结果面板 | T-01 | 端点 E2E 烟测 |
| 6 | T-05 矩阵 T13 + fixtures + README 口径 | T-02..T-04 | `desktop_mcp.py` ≥N/0 |
| 7 | T-06 规范 SD-01..03 + upstream §12 + vue 复验 | T-05 | grep 三册 + regen --build exit 0 |

（T-03/T-04 可并行；worktree 纪律照 PLAN-008——专用组 worktree，主检出
零落盘。）

## 9. 复审记录

- **2026-09-22 stage: new（r1，drafting → 交接 work）**：用户指令起草
  下一计划；战略 §6 M2 序列定位=第二件（查找替换/find-in-files，首件
  PLAN-008 已归档）。背景调查实勘：内核查找链三面已齐（search prop/
  code_editor_find），缺口全在编排层；正则执行挪 back 两新端点规避
  ts_adapter 映射缺口（跨轨禁补件裁定）。七步七 AC 八规范动作（SD×3 +
  upstream §12 + 白名单 + README + vue 复验）。outcome: pass（授权=
  起草；执行待用户启动 auto-plan-work）。next: work。

- **work 进入记录（2026-09-22T21:50）**：stage=work；worktree 组建立——
  `D:/autostack/.wt/edit-009/auto-edit`（branch `plan-009-dev`，base
  fda9cdb=main tip）+ 兄弟树 `.wt/edit-009/auto-lang`（detach 5f62ebac5
  =auto-lang main tip，bps 供料，零改动）。**工具链钉版**
  `.wt/edit-009/auto-009.exe`（**1914-g56bfaf1fc-dirty**——与 PLAN-008
  判定矩阵 57/0 同一构建；worktree 内构建不可行=workspace 路径依赖
  `../auto-down` 缺位，PLAN-682 组惯例需 auto-down 兄弟；钉版偏差在案：
  exe 基 56bfaf1fc vs 兄弟 tip 5f62ebac5 差量=PLAN-690 IME/远程渲染
  28 文件，与查找替换面正交且不涉本件任何内核依赖[内核七面源证据在
  两版均在位]——矩阵基线可比性优先）。主检出预检：specs/stylekit 两
  删除 WIP 在案（计划 §4 预告，本计划零触碰）；并行会话 auto.exe
  两进程（auto-lang 主检出 vue 实例 + musk-084 组）不占本组目录锁。

- **work 执行记录（2026-09-22）**：T-00 落（7c1e866，r4 三变体对照 +
  r5 终态 23/0 双跑）；内核七面源证据实勘全在位（1914 与 tip 双版）。
  T-01..T-04 全链落+烟测绿（6f0a846）；T-05 矩阵 T13 二十检查+fixtures
  +README 口径（89a44fe）；T-06 规范三册+upstream §12 九件+vue build
  exit 0（d6a2a9f）；T-04/T-05 收口——fif 行点击 idx 载荷+scroll 降级
  规避+三重试臂（d07ce50）。执行期产品修三处：back regex_replace 大小
  写不敏感默认补齐（SD-02 契约）、fif 噪声过滤前导段归一（gen 树 11k
  文件 walk 8.7s）、to_value 内联形（vue TS2339）。执行期新增 upstream
  §12 观察件五件（四 want 外）。**完成态矩阵 77/0 双跑绿（最终源态
  d07ce50）**+ probe 23/0 + bench check 绿 + vue build exit 0（最终源
  态复验）。

- **work handoff（2026-09-22T02:10）**：stage=work | PLAN-009 | r1 |
  **pass** | code_commit=8d35888（plan-009-dev tip，6 commits
  7c1e866..8d35888） | T-00..T-06 全部 | 证据：矩阵完成态 **77/0 双跑
  绿**（57 基线 + T13 二十检查；判绿下限 ≥65 README 同步；中间跑次
  T6 paste flake 一次按复跑条款绿）+ probe_find.py 23/0 双跑 + bench
  check 绿（红证自检 PASS+白名单扩后真实扫描不红）+ vue regen --build
  exit 0（最终源态）+ 规范三册 grep 新节在位 + upstream §12 九件在档 |
  blockers=无 | worktree 状态=tracked 树 clean（deps/ ×2 junction +
  gen/ vue 树为工具链/pnpm 运行期产物，wt-guard BLOCKED 系预期——
  merge 期按 PLAN-682 处方摘链后移除）| next=review（/auto-plan:review；
  AC-01..08 逐条面见 §7，AC 对应矩阵 T13 组+探针+bench+vue 四验证面；
  非目标边界=§1 非目标清单+AC-06 跳行定位/单处替换等上游件 §12 在档）

- **review pass（2026-09-23T02:45）**：stage=review | PLAN-009 | r1 |
  outcome=**pass** | reviewed_commit=8d358889ff24e0ea451836840233dc2df
  8589c23（plan-009-dev tip，tracked 树 clean 实证） | base=fda9cdb |
  deps=auto-lang 兄弟树 5f62ebac5（零改动，clean 实证）+ 工具链钉版
  `.wt/edit-009/auto-009.exe`（1914-g56bfaf1fc-dirty） |
  spec_inputs=docs/specs/modules/editor-store.md（SD-01 :144 追加节）、
  modules/back-api.md（SD-02 :6 九端点勘正+:56 搜索服务端点节）、
  00-overview.md（SD-03 :74 第二件行）、docs/upstream/2026-09-m1-supply.md
  （§12 :241 九件） | acceptance_results=**AC-01..08 全 pass**——
  AC-01=T13.1（Ctrl+F 开栏+三开关+下一处）+13.1e（×关栏清搜索态）+
  13.3（Ctrl+H 替换行；Esc 项=×析取路径满足，SD-01 边界在案）；
  AC-02=探针 T1（live 首跳）+T13.2（推进 (1,12)→(1,18)→回绕 (3,6)）；
  AC-03=T13.1a-d 四组合（同一 find_effective 驱动 13.3/13.6 两面）；
  AC-04=T13.3（落盘字节等值+「替换 4 处」）+13.4（readonly+哈希零变）+
  13.5（空 query 零动作）；AC-05=T13.6（count==3+truncated False）+
  13.7（500 上限）+13.8（>10MB 门）+执行期 HTTP 独立形态验证
  （search_files count=3 8.7s / regex_replace count=2 200 在案）；
  AC-06=T13.6 条目点击开 tab（idx 载荷修复后）+pattern 延续机制面
  （跳行=非目标 §12）；AC-07=77/0≥65+README grep 同步+bench 白名单扩
  全绿；AC-08=三册 grep 新节+§12 九件（≥4 want）+vue exit 0 |
  findings=无阻塞项；N1=T13.6 条目点击曾属 MCP 字段访问载荷不解析
  竞态（已由 idx 载荷+重试臂收口，复跑三绿；底层限制随 §10/§12 在
  档）；N2=Esc 关栏未接（input 无 keydown 面，SD-01 边界在案，AC-01
  ×路径满足）；N3=fif 全程 ~9s（gen 树 11k 路径，README 注记，v1
  限制）| evidence=**提交态独立复跑**（与实施同会话，判定自工件重建
  非采信执行者自述）：矩阵 77/0（reviewed_commit 复跑）+ probe 23/0 +
  bench check 绿（红证自检 PASS）；SD-02 契约↔实现交叉核（9 #[api]
  实数/大小写默认 (?i) 源码位/500·10MB 门/白名单）；vue exit 0 复用
  理由=d07ce50..8d35888 diff 仅 README（构建输入源等同，git diff
  --stat 实证） | next=**merge**（/auto-plan:merge；worktree 状态=
  deps ×2 junction+gen/ pnpm 树为工具链运行期产物，wt-guard BLOCKED
  系预期，按 PLAN-682 处方摘链后移除）

## 10. 待澄清事项

### T-00 决策记录（2026-09-22，probe_find.py r4 三变体对照 + r5 终态，23/0 双跑）

**① search prop Ident 绑定——正案，零新端点**：
- `search: .store.eff` Ident 绑定 vm 轨 live 生效：eff 变更 → 下轮视图
  apply_search diff + 非空首跳（高亮 + 光标落首匹配，r5 T1 实证：键入
  "axb" 后不经 find 按钮光标落 (3,8)）。a2r 编译面 ui_gen/rust.rs:4181
  Ident 分支在册（编译面验证即可，vue 轨 search prop 发射面=死分支口径
  不变，T-06 注记）。

**② `(?-i)` 内联旗标——正案，无降级无上游件**：
- 内联旗标**覆盖**内核 builder `case_insensitive(true)`：pattern
  `(?-i)Alpha` 首跳落大写 Alpha 末位 (1,12)（builder 压制形态应落小写
  (1,6)，实测未发生）；种子仅一处 Alpha → find_next 回绕原位（r5 T2）。
- 大小写开关定案=`(?-i)` 前缀；高亮/替换/fif 三消费面同串同语义。
- 光标断言约定（探针勘定）：跳转后 cursor=匹配末位（exclusive）。

**③ 整词 `\b` 锚——正案**：`\bfoo\b` 首跳 (2,4) → find_next (2,15)
（foobar 词中 col5-10 跳过，r5 T3）。转义例程同轮正案：
`regex_escape("a.b")`→`a\.b`，字面点跳过 axb（(3,4)→(3,12)）。

**④ input 写回——翻案+定案（Q-2 收口）**：
- 计划 Q-2 预设「031 先例=框架写回后 handler 触发」**翻案**：vm 轨
  input 派发把**键入文本作 handler 首参**（dynamic.rs on_with_input_for
  Plan 370 臂；015-notes `SearchChanged(q)` 形）；框架写回仅根级字段
  （input_state_map 写回面注释「root-level」，store 子树字段
  `.store.X` 不适用）；裸 value（无 oninput）对 store 字段**不 mint**
  type handler（r4 实验报 `No 'type' handler found`）。
- 产品形态定案：`input { value: .store.find_query, oninput: .FindInput }`
  + `msg FindInput(str)` + `.FindInput(q) -> { .find_query = q; …重算 }`
  ——handler 显式赋值，不依赖框架写回。`$event` 形态（r2 实测）不达，
  弃。
- 观察件：启动后 ~2s 内首个 type 派发可被静默丢弃（r3/r4 两轮复现，
  定驻+重试卫生后稳定；疑 PLAN-008 §10-⑤ computed-events 竞态同族）
  ——登记 upstream 观察（§12 随 T-06 落）。

**⑤ 替换链——正案，计数面改 marker 算术（Q-5 勘定修正）**：
- 链完整：`code_editor_text` 读出 → `Regex.replace(text, pat, repl,
  "g")` → `code_editor_edit(0, body.len(), out)` 全文重写 → delta
  drain-弃 → 读回一致（r5 T5：`(?-i)Alpha`→"YY" 后首行
  "alpha YY ALPHA"）。`(?i)`/`(?-i)` 前缀在 Regex.replace/'g' 与计数
  双面均正确（3/1 对照 PASS）。
- **计数翻案**：`Regex.match` 'g' 列表的 `.len()` 在 vm handler 字节码
  **恒 20**（任意 pattern/任意命中数，r3 实证）——弃用；改 **marker
  算术**：替换至 sentinel 串后 `(out.len() - out.replace(m,"").len()) /
  m.len()`（Str.replace/len 双轨映射内，PLAN-008 EOL 计数同款选型）。
  back 端点 `{out, count}` 契约的 count 即此法（真实替换数）；「250
  上限」原语义（Regex.match 列表帽）不再入契约——replace 无列表。
- `Regex.match` 列表 .len() 异常登记 upstream 观察件（§12 随 T-06）。

**执行期追加实勘（T-04/T-05 收口，d07ce50）**：

- **MCP 点击派发的循环载荷形态**：`onclick: .FifResultClick(r.file)`
  字段访问载荷经 MCP press 派发面携带**字面量 `r.file` 不解析**（快照
  实勘 onclick 文本在案）——点击 ok 而 handler 收垃圾参，exists 失败
  静默空转。裸循环索引（`.FifResultClick(idx)`，TabActivate(i) 先例）
  可靠；handler 侧 `.fif_results[i]` 解码列表索引 + `.row.file` 取径
  可行（fif_count 门替代 .len()）。
- **scroll+for 内 button 降级 col**：结果列原 scroll 包装下行按钮降级
  为无 onclick 的 col（Plan 420/449 vm 组件/快照边界又一形态）——去
  scroll 改 overflow-hidden col + max-h-40。
- **vue 轨 to_value 吸收面**：`json.to_value(<api call>)` 内联形转译为
  `JSON.parse(await ...)`（无注解 any）；typed str 中间层让 string 注解
  传染字段访问（TS2339）——内联形为正案（ProbeByteMeta 先例）。
- **T13 基建卫生**（desktop_mcp 注释在案）：AUTO_OPEN_PATH 被动消费仅
  AUTO_BENCH=1 门（打开须点 + 按钮走 ActOpen 旁路）；fif 面板先开再
  搜索；console_lines() 新行在头（倒序）；autoui_state 反斜杠加倍渲染
  需解码；gen/ 树（vue build 产物 ~11k 文件）入场后 fif 全程 ~9s
  （轮询窗按此放宽）。

### 原待澄清（起草时预登记，处置如下）

- **Q-1 `(?-i)` 内联旗标**：已收口（正案，见上②）。
- **Q-2 input 写回时机**：已收口（翻案定案=handler 首参形，见上④；
  `$event` 后备不达，弃）。
- **Q-3 a2r Ident 绑定形态**：编译面分支在册（rust.rs:4181）；vue 轨
  本件预期 build-green（查找栏基础 kind + 正则面全在 back），T-06
  复验收口。

- **merge 收据 PLAN-009:r1（2026-09-23T03:05，五 checkpoint）**：
  `prepared`——reviewed 基线 r1 pass @ 8d35888（base fda9cdb，复审记录
  在档）；canonical spec 增量=reviewed 分支内（SD-01..03 d6a2a9f +
  upstream §12）；账本投影=specs.json reviews 段 P009-1 外科插入
  （+10 行零删除，整文件解析+回读 9 items+insertion-only 证明）；
  delivery commit=**a728d47**（projection-only descendant of
  8d35888，实现/依赖零变更）。`landed`——main ff-only fda9cdb→a728d47
  零 merge 提交（main 未动=无 rebase 需求）；canonical 四锚主检出在位
  （editor-store.md SD-01 :144 / back-api.md 九端点+:56 搜索端点节 /
  00-overview.md :74 第二件行 / upstream §12 :241）；烟测=主 tip 全新
  检出（smoke-main 临时检出+junction→兄弟树 clean blueprints——**主
  检出 bps 链当前被 auto-lang 主检出并行 WIP 断（blueprints/navigation
  删除未提交），非本落地缺陷**，共享环境状态在案）：查找链
  （Ctrl+F+eff）+fif 链（面板+搜索 count=4）PASS。`ledger_refreshed`
  ——.autoos/specs.json（tracked）：reviews 段 9 items（P001..P008+
  P009-1）主检出 json 解析+回读验证。`archived`——plain mv（未跟踪
  文件）→docs/plans/archived/009-m2-find-replace.md + status archived
  + completion_kind **delivered**。`cleaned`——随后行。
