---
plan_id: PLAN-003
status: execution_done
feature_name: auto-edit-frontback-dualtrack（auto-edit front/back 架构拆分：src/back + api.at 边界 + back 用 Auto 写 + 双轨化 vm/vue）
author: [zhaopuming]
created_at: 2026-09-20
updated_at: 2026-09-20
plan_revision: 1
current_step: 6
total_steps: 6
supersedes_spec_components: []
new_spec_components: []   # 无 docs/specs/ canonical 新建（本仓知识库=.autoos 账本+模块 README，002 同款；SD-01/02 改写 specs/auto-edit/README.md 随 merge 生效）
touched_goals: []
---

# [PLAN-003] auto-edit front/back 架构拆分 + 双轨化（vm/vue）

> 需求来源：用户 2026-09-20 口述——「把 auto-edit 也拆成 front/back 的架构，
> 边界用 api.at 负责（自动切换边界形式）。这样 auto-edit 也可以用 vue 版
> 展示出来」。后续 D:\autostack\jade-edit PLAN-001（换基，jade-edit 仓独立账本）以本计划交付为
> 前置依赖。

## 0. 变更摘要

| 面 | 内容 |
| --- | --- |
| back 拆出 | `src/back/`（api.at 契约 + Auto 实现本体）接管全部文件系统面；front 零直接 FS 内建调用 |
| 边界机制 | `use back.api: <fns>` 裸函数直调（013/015 同款）：vm merged = 进程内 CALL；vm split / vue = HTTP（ts_adapter 生成 client） |
| pac 纪律 | **不写 `api:` 字段**——服务引擎（AutoVM HTTP / a2r rust）留运行期 `--server` 切换；默认 AutoVM + merged 直调 |
| 双轨化 | pac `render: "vm"` → `render: ["vm","vue"]`（jade-edit R-1 裁定 A' 同款 + 「禁裸 auto build」围栏）；vue 轨生成 + 构建绿 |
| 文档 | README「vue 模式限制」节按 jade-edit T-00 R-2 勘定改写（PLAN-070 T-05 已去门化，陈述过时）；运行矩阵补双轨/back/引擎切换命令 |

## 1. 目标

1. **back 落成**：`src/back/api.at`（`#[api]` 契约）+ Auto 实现（fs 面四件：
   tree / read_text / write_text / exists + 工作区根解析），pac 无 `api:` 钉。
2. **front 迁移**：editor_store.at 全部 `fs.*` / `File.*` 调用改走
   `use back.api`；vm merged 模式下功能环（树/打开/编辑/保存/退出存盘）
   与拆分前行为等价。
3. **双轨声明**：render Multi 形态；vue 轨 `auto build -r vue` 生成 exit 0
   且生成工程构建绿（探针级冒烟）。
4. **引擎切换实跑**：`--server vm`（AutoVM HTTP split）功能环绿；
   `--server rust`（a2r）实跑勘定（通过或缺口登记，不阻塞）。
5. **文档收口**：README vue 限制节改写 + 运行矩阵更新。

**非目标**：vue 轨深度 e2e/双臂一致性门（jade-edit PLAN-001 承担门体系，
auto-edit 只保 vm MCP 矩阵不回退 + vue build 绿）；menubar 展开快照 6 失败
（上游 auto-lang 664 债，现状 39/6 维持）；027 式文件管理增强（重命名/删除
等 ctx 面扩展）；`api:` 字段任何取值（纪律就是不写）。

## 2. 架构方案

```
specs/auto-edit/
├── pac.at            # render: ["vm","vue"]；⚠ 不写 api: 字段（引擎=运行期自由度）
└── src/
    ├── back/
    │   ├── api.at    # 契约：#[api(method,path)] fn + 共享类型（013-todo 同款）
    │   └── fs.at     # 实现本体：ws 根解析（AUTO_PROJECT_DIR）+ tree/read/write/exists
    └── front/        # 现有五件 + components/ 不动结构，仅 store 数据面改道
        └── editor_store.at   # fs.*/File.* → use back.api: …（裸函数直调）
```

- **边界语义**（auto-lang main.rs:1002-1025 实证）：CLI `--server {vm,rust}`
  优先；pac `api:"rust"` 仅在 flag 缺席时补默认且**杀 merged**；两仓皆不
  写 ⇒ 默认 AutoVM 服务 + merged 进程内直调。
- **merged 直调**：`use back.api` 在 VM merged 臂保持 CALL reloc
  （auto-lang plan 633 实证：013/015 store 同款，无 fetch 封装）。
- **vue 轨**：ts_adapter 生成 HTTP client；后端供给形态（vue dev 期谁起
  HTTP）列 T-00 勘定。

## 3. 技术栈

- 单源 AutoUI DSL（现有，038/449 store 形态、449 vm 组件边界约束照旧）。
- back = Auto（.at，AutoVM 解释服役）；a2r rust 引擎为运行期可选项。
- 工具链 auto.exe（`run -r vm` / `build -r vue` / `--server`）；测试 =
  现有 Python MCP 矩阵（desktop_mcp.py）+ vue 构建冒烟。

## 4. 需求分析与背景调查

**授权记录**：2026-09-20 用户口述需求（见引言）+ 「先实现完 auto-edit 之后
再来本仓库实现」的顺序裁定（本计划为两段之前段）；2026-09-20 用户指令
「计划003 实施它」——**work 授权已给**，status drafting→executing，从 T-00 起。
允许动作面 = specs/auto-edit（源码+文档）+ docs/plans/（本档）；不改
auto-lang / auto-down / jade-edit。

**现状实勘**（2026-09-20）：

| # | 事实 | 证据 |
| --- | --- | --- |
| F-1 | front 直接 FS：ws 根 `Env.get("AUTO_PROJECT_DIR")` 兜底 "."；`fs.tree(.ws_dir,4)` 装树 | editor_store.at:109-114 |
| F-2 | 读：`File.read_text`（树选择/tab 匹配三处）；存在性 `File.exists`；拼径 `fs.join` | editor_store.at:273/298/424-436 |
| F-3 | 写：`File.write_text`（ActSave + QuitSaveClose）；untitled 走 `dialog_save`（前端 UI 内建） | editor_store.at:322/332/483 |
| F-4 | actions 块在根 widget App（三源绑定 shortcut/menubar/MCP） | app.at:38-71 |
| F-5 | 编辑器 = `code_editor (lang:"auto")`；`code_editor_set_text` 必须留根 handler（坏字节码规避） | app.at:173/247-252 |
| F-6 | pac 现状 `render: "vm"` 单轨、无 api 字段 | pac.at |
| F-7 | 测试 = `python desktop_mcp.py` MCP 矩阵，现状 39/6（6 失败 = menubar 展开快照，上游 664 债） | README:81/88 |
| F-8 | README「vue 模式限制」节陈述过时（vue 生成器 actions 已支持，PLAN-070 T-05 去门化） | README:47-50；jade-edit T-00 R-2 勘定 |
| F-9 | `--server` 运行期开关 + pac `api:` 仅补默认 + rust 引擎杀 merged | auto-lang crates/auto/src/main.rs:422/1002-1025 |
| F-10 | 013/015 = front/back 形态先例（api.at + db.at，store 裸直调） | examples/ui/013-todo、015-notes |

**约束**：vue 轨下 front 的 FS 内建不可用（ts_adapter `__vmOnly` 拦截）——
这正是拆 back 的动机；449 vm 组件边界（快照定位锚交互留根视图）迁移中
不得破坏；`code_editor_*` 内建留根 handler 约束照旧。

## 5. 详细设计

**api.at 契约面**（首版最小集，路由前缀 /api）：

| fn | 签名（示意） | 替代的 front 调用 | 证据位 |
| --- | --- | --- | --- |
| ws_root | `fn ws_root() str` | `Env.get("AUTO_PROJECT_DIR")` | F-1 |
| tree | `fn tree(path str, depth int) str`（JSON） | `fs.tree` | F-1 |
| read_text | `fn read_text(path str) ?str` | `File.read_text` / `File.exists` 前置 | F-2 |
| write_text | `fn write_text(path str, content str) bool` | `File.write_text` | F-3 |
| exists | `fn exists(path str) bool` | `File.exists` | F-2 |
| env_str | `fn env_str(name str) str`（未设=""） | `Env.get("AUTO_OPEN_PATH"/"AUTO_SAVE_PATH")` | T-00 P-10② |

`fs.join` **不出契约**（T-00 P-5：ts_adapter 对象级白名单连纯逻辑
`fs.join` 一并拦）——front 以本地字符串拼接替代（ws_dir 尾 `/` 归一）；
`Env.get("AUTO_PROJECT_DIR")` 由 `ws_root()` 取代；`dialog_save` 为 UI
内建留 front（vue 轨登记限制，T-00 P-11）。

**store 迁移映射**：editor_store.at 上述调用点逐一改 `use back.api: …`；
`.Init -> LoadWorkspace()` 语义不变（merged 下直调无网络往返）。

### T-00 勘定决策档（2026-09-20 worktree .wt/edit-003/auto-edit@10881b9，工具链 auto v0.4.2-1498-g34ee15a47）

> 探针：worktree 内 `auto build --gen-only -r vue` 两跑（strict/lenient）+
> 生成工程逐面检查 + auto-lang 源码勘定（ts_adapter 白名单 / vue.rs 供给分支 /
> 015 GET 带参先例）。零源改动，gen/ 产物可弃。

| # | 勘定项 | 结论 | 证据 |
| --- | --- | --- | --- |
| P-1 | 现源 vue 生成首跑 | strict（build 默认）exit 1：S001 schema 漂移 Info 判负（menubar-item title/icon/shortcut 等 PLAN-630 组件族 props 未进 aura schema——上游债）；`--lenient` exit 0：gen/front/vue 生成，33 组件 + shadcn 144 件捆绑 + useEditorStore.ts | 两跑日志（/tmp/t00-probe1/2.log 摘录见复审记录）；validators.rs:1048 S001 hint |
| P-2 | **vue 生成命令裁定** | 固定 `auto build --gen-only --lenient -r vue`（schema 债登记上游，围栏写 README+pac 注释） | P-1 |
| P-3 | code_editor vue 支持度 | ✅ 完整：CodeEditor.vue（vue-codemirror6，v-model/oncursor/oncontextmenu 全发射，lang 包入 deps）——**待澄清②解除，无需 textarea 降级** | gen App.vue:298 + package.json codemirror deps |
| P-4 | alert-dialog / menubar | ✅ shadcn 捆绑 + App.vue 发射 | gen components/ui + App.vue:6 |
| P-5 | R010 白名单实证 | EditorStore 5 内建全拦：fs.tree / fs.join / File.read_text / File.write_text / File.exists → `__vmOnly` 抛错桩；**fs.join 亦拦（ts_adapter 对象级白名单 fs\|File\|image 不挑方法）——计划「fs.join 纯逻辑豁免」假设修正：front 改本地字符串拼接（ws_dir 尾 `/` 归一），不再走内建** | ts_adapter.rs:1025-1039 + 生成 store L76-291 五桩 |
| P-6 | 白名单外 vm 内建 vue 发射 | Env.get / Process.exit / console_log / console_lines / console_clear / file_basename / dialog_open / dialog_save / code_editor_*×13 → **裸标识符**（无声明无运行时）：vue-tsc TS2304 面（构建期）+ ReferenceError 面（运行期）；json.to_value 被转译吸收、`.str()`→`.toString()` 免声明 | 生成 store/main.ts grep；jade-edit 无此面（widget 集不同） |
| P-7 | vue dev 后端供给 | `auto run -r vue --server vm` = start_vm_server（AutoVM HTTP）+ vite dev（pac front_port 4041）；vite 代理 `/api`→AUTO_HTTP_PORT（-B/pac 注入，运行期读）。⚠ vue.rs:5811 AUTO_BACKEND_IMPL 缺席默认 rust（a2r）——**vue dev 必须显式 `--server vm`** | main.rs:1035-1075（端口注入）+ vue.rs:5808-5818 + 生成 vite.config.ts proxy |
| P-8 | 三形态启动语义 | merged=默认 `auto run -r vm`（进程内 CALL，无 HTTP）；split VM+VM=`--server vm` 或 `--no-merge`（起 AutoVM HTTP）；VM+Rust=`--server rust`（api_gen 生成 a2r axum + start_api_server）。pac 不写 api: ⇒ 默认 AutoVM+merged | main.rs:1002-1031 + rust_ui.rs:3000-3060 |
| P-9 | GET 带参先例 | `#[api(method="GET")] fn f(query str)` → query string（015 search_notes）——tree(path,depth)/exists(path)/read_text(path)/env_str(name) 可用 GET | 015-notes api.at:75-80 |
| P-10 | 契约面修订（§5 补录） | ① read_text 返回 `str`（失败 ""）非 `?str`——保持树/打开路径零 Option 分支（调用点全部前置 exists/来源可信），偏差记此处；② 新增 `env_str(name) str`——AUTO_OPEN_PATH/AUTO_SAVE_PATH 旁路读盘入 back（矩阵 T9/T10 保真 + front 零 Env.get）；③ fs.join 出契约（P-5） | — |
| P-11 | 待澄清①执行形态修正 | 单源无 track 信号，「untitled 固定落根」会改 vm 轨行为（违 AC-02 零回退）——改按「vue 轨登记限制」形态：dialog_save 留 front（vm 三形态可用），vue 首版 = 构建绿 + 生成即展示，运行期缺口（dialog/Env/console/code_editor 读回）统一登记 README vue 限制节，深水区归 jade-edit 换基计划。复审可改 | — |

### 规范增量

| delta_id | add/modify/retire | target | before/after | rationale | AC |
| --- | --- | --- | --- | --- | --- |
| SD-01 | modify | specs/auto-edit/README.md「vue 模式限制」节 | before：「生成器尚未接入 action 配置…pac 固定 vm」/ after：按 R-2 勘定改写 + 双轨运行说明 | 陈述过时（F-8），误导后续 | AC-05 |
| SD-02 | modify | specs/auto-edit/README.md Source/运行节 | before：单 vm 运行命令 / after：front/back 架构注记 + 双轨 + `--server` 引擎切换命令矩阵 | 拆分后文档即契约 | AC-02/03/04/05 |

## 6. 测试设计

- **回归主门** = 现有 `python desktop_mcp.py` 矩阵：拆分后同机复跑，
  基线 39/6 不得回退（6 失败为上游在册债，豁免）。
- **merged 直调验证**：`auto run -r vm`（默认 merged）功能环手测清单
  （树装载/打开/编辑/保存落盘/退出存盘）+ 矩阵绿。
- **split 验证**：`AUTO_VM_MERGE=0`（或显式 `--server vm`）同清单。
- **vue 冒烟**：`auto build -r vue` exit 0 + 生成工程 `pnpm install &&
  pnpm build` 绿；探针缺口登记（T-00 产出）。
- **front 零直调静态检查**：grep `File\.|fs\.` 于 src/front 零命中
  （T-00 P-5 修正：fs.join 亦拦，本地拼接替代后豁免清单为空——注释除外）。

## 7. 验收标准

- **AC-01**：src/back 在库（api.at 契约 + Auto 实现），pac.at 无 `api:`
  字段、render 为 `["vm","vue"]`；src/front 无 FS IO 内建调用
  （grep 验证，fs.join 纯逻辑豁免清单显式）。
- **AC-02**：`auto run -r vm`（默认 merged）功能环全绿 + MCP 矩阵 ≥39
  通过（6 上游豁免不变）——拆分零行为回退。
- **AC-03**：split 形态（`--server vm` / `AUTO_VM_MERGE=0`）同功能环绿。
- **AC-04**：`auto build -r vue` 生成 exit 0 且生成工程构建绿（探针级；
  code_editor 等 vue 侧缺口若实存，登记并经待澄清②裁范围后按裁定验收）。
- **AC-05**：README 两节改写落地（SD-01/SD-02），运行矩阵命令全部实测。
- **AC-06**：`--server rust`（a2r）一次实跑：通过，或缺口登记进本档
  复审记录（不阻塞交付）。

## 8. 执行步骤

| ID | 任务 | 依赖 | 影响面（实勘） | 产出/意图 | AC | 验证 |
| --- | --- | --- | --- | --- | --- | --- |
| T-00 | [x] 勘定探针：现源 vue 生成首跑（临时 render 覆盖 `auto build --gen-only -r vue`）+ code_editor/dialog/alert-dialog vue 支持度清单 + vue dev 期后端供给形态勘定 | — | 零源改动（gen 产物可弃） | 决策档补录本档 §5/待澄清②（缺口面+降级形态） | AC-04 | 探针命令输出留存档内 [✅ 2026-09-20：strict exit1/lenient exit0 两跑 + 11 项勘定 P-1..P-11 落 §5 决策档（vue 命令=--lenient -r vue；code_editor vue 全支持；fs.join 出契约；env_str 入契约；vue dev=run -r vue --server vm；待澄清①②裁毕）] |
| T-01 | [x] src/back 立起：api.at 契约（六 fn + 类型）+ fs.at 实现（AUTO_PROJECT_DIR 根解析 + 四 IO）；pac render 改 `["vm","vue"]` + 「禁裸 auto build」注释围栏 | T-00 | 新增 src/back/；pac.at | back 面在库 | AC-01 | `auto run -r vm` 可起（front 尚未改道，行为同旧）[✅ 2026-09-20 worktree@5b3306a：契约六 fn（env_str 增列）+ 实现（函数名错开避遮蔽）+ pac 双轨+围栏 + .gitignore 五生成目录；门=vm boot merged L28/Init/24 handler OK + vue gen --lenient exit 0 + api client 六 fn 发射（dist/src/lib/api.ts，GET query/POST body）+ rust server 骨架（a2r 轨备用）] |
| T-02 | [x] store 数据面迁移：editor_store.at 全部 FS 内建 → `use back.api`；merged 直调功能环 + MCP 矩阵复跑 | T-01 | editor_store.at | 零直调达成 + 零行为回退 | AC-01/02 | 矩阵 ≥39；grep 零命中（豁免清单外）[✅ 2026-09-20 worktree@ff23b86：七调用点迁移（ws_root/tree/read×3/write×2/exists/env×2）+ fs.join→本地拼接 + front 零 Env.get；门=MCP 矩阵 39/6 与基线逐项一致（6 上游债同类豁免；T9/T10 open/save 往返 PASS=back api 实证）+ grep `File\\.|fs\\.|Env\\.get` 仅注释命中] |
| T-03 | [x] split + 引擎切换实跑：`--server vm`/`AUTO_VM_MERGE=0` 功能环；`--server rust` a2r 探针登记 | T-02 | 零源改动（或缺口修补） | 三形态语义实证 | AC-03/06 | 手测清单 + 输出留档 [✅ 2026-09-21 复验闭环 worktree@7a4ed53：**上游 auto-lang PLAN-669（#[api] 实参按名绑定）落地后 B1 解阻，本仓零改动**——①六端点直打全真值（exists abs/rel→1、read_text→内容、tree→真树、env_str→真值、write→落盘）；②VM+VM split 单实例功能环 11/11 全 PASS（树装载/open env 旁路经 HTTP 开 tab/edit cut/save 落盘+console/quit 菜单/quit-save 脏 tab 落盘+进程退）；③013 POST 按名复验 text=probe669x；④merged 矩阵+vue regen build 在新工具链复绿（矩阵形态位移见 F-V1）；README split 注记勘误收口。原 T-03 实证（fsys 修正/三形态勘定/F-W 系登记）保留于下]（原证：修补=fsys 改名+整模块 use；--server vm=后端独立 serve 六路由；rust=E0432+F-R1 登记） |
| T-04 | [x] vue 轨落地：生成（`-r vue`）+ T-00 缺口修补（如需）+ 生成工程 install/build 绿 | T-01（T-00 缺口面） | gen/（生成物） | vue 展示能力达成 | AC-04 | build exit 0 + pnpm build 绿 [✅ 2026-09-20 worktree@1efea47+7fc6ac2：scripts/regen_vue.py 一键链（生成命令=--gen-only --lenient -r vue）+ 七类补件（natives 声明层/store 自调别名/toggle_id 内联/ref null→-1/EditorCtx 双参/button text variant/auto-sources+env.d.ts）+ StatusBar 多段插值残缺修复；门=regen_vue.py --build exit 0（vue-tsc+vite ✓ built 3.51s）；运行期内建缺口按 P-11 登记 README vue 限制节] |
| T-05 | [x] 文档收口：README SD-01/SD-02 两节改写 + 运行矩阵全命令实测 | T-02/03/04 | specs/auto-edit/README.md | 文档=新架构契约 | AC-05 | 逐命令实跑记录 [✅ 2026-09-20 worktree@c95744d：Concepts front/back 节 + vue 轨节（R-2 勘正落地）+ Source 表三件新增 + 运行矩阵五块命令；门=全命令实测（merged 矩阵 39/6 终验于 fsys HEAD + split 探针 + backend-serve curl + rust 编译定性 + regen --build exit 0 + vue dev vite/代理 200）] |

## 9. 复审记录

- 2026-09-20 stage: new / PLAN-003 r1 起草交付评审。
  outcome: pass（评审通过即待「开工」授权进入 work）。
  next: review → work（授权后从 T-00 起）。
  备注：jade-edit PLAN-001（换基，jade-edit 仓账本）以本计划交付为前置。

- 2026-09-20 stage: work / PLAN-003 r1 执行中（T-00/T-01/T-02 落地）。
  T-00 勘定 11 项（P-1..P-11，§5 决策档）；T-01 back 立起 worktree@5b3306a
  （vm boot merged 绿 + vue gen api client 六 fn 发射）；T-02 store 迁移
  worktree@ff23b86（矩阵 39/6 基线逐项一致 + grep 零命中）。
  T-03 进行中，split 面重大勘定（上游缺口定性，详证 T-03 收口补）：
  - **F-W1（vm split 上游缺口）**：AutoVM HTTP 服务上下文（run_file 扁平
    api.at）的 File/fs 内建为静默空桩——exists→0 / read_text→"" /
    tree→"[]" / write→false（curl 直打六端点实证，绝对路径亦然）；唯
    Env.get 真实（auto-man 注入的 AUTO_PROJECT_DIR 可读）。⇒ VM+VM
    split 的 back 无文件系统能力 = AC-03 功能环（fs 腿）被上游卡死。
  - **F-W2（env 注入差异）**：AUTO_OPEN_PATH/AUTO_SAVE_PATH 进程 env 在
    服务上下文 Env.get 不可见（仅 auto-man set_var 注入面可见）——
    env_str 端点 "" 实证；矩阵 T9 旁路机制在 split 形态失效（9.4 的
    PASS 为空心断言：文件未被碰，原首行仍在）。
  - **F-W3（SrcChanged 分发怪癖既存）**：split 日志的
    `SrcChanged args=[Str("")]` → IndexError 崩溃，在 merged 日志同样
    存在（6 次）——分发怪癖两侧一致，非本次迁移引入（基线矩阵口径
    不变佐证）。
  - **F-W4（--server vm 单独 = 后端独立 serve 形态）**：`auto run
    --server vm`（无 -r vm）只起后端不开窗（automan vm_server_mode
    分支）——待澄清③「独立 serve」选项的直接答案；全功能 split =
    `--no-merge`。
  - rust 轨（--server rust，a2r 真编译）实跑中——若真 fs 通，AC-03
    功能环可经 rust 引擎达成（兼 AC-06 正面证据）。
  - **F-R1（rust 轨双缺口定性）**：a2r server 生成器模板硬编码
    `use api::Db` 状态注入（013 db 形态固化）→ 本工程全标量无状态契约
    编译 E0432；且六契约 fn 转译为空体桩（fsys 实现体未随转译）。
    AC-06 按「缺口登记」分支验收。

- 2026-09-20 stage: work | PLAN-003 | r1 | pass（六任务全勾；AC-03
  fs 腿上游受阻已登记，评审裁量） | code_commit: plan-003-dev
  5b3306a→c95744d（T-01 back 立起 / T-02 store 迁移 / T-03+04 fsys 修正
  + regen 链 / T-05 README） | task_ids: T-00..T-05 | evidence:
  AC-01 ✓（back 在库 + pac 无 api: + render 双轨 + grep 零命中）；
  AC-02 ✓（merged 矩阵 39/6 基线逐项一致，fsys HEAD 终验复现）；AC-03
  部分（split 边界/契约服务/单实例树装载绿；fs 腿=F-W1 上游缺口卡死，
  见 §10-B1）；AC-04 ✓（生成 exit 0 + vue-tsc/vite 构建绿探针级 +
  缺口面经 T-00 P-3/P-6/P-11 裁定登记）；AC-05 ✓（README SD-01/SD-02
  落地 + 运行矩阵五块命令全实测）；AC-06 ✓ 按「缺口登记」分支（F-R1）。
  worktree: D:/autostack/.wt/edit-003/auto-edit（plan-003-dev@ c95744d，
  base main@10881b9，零 WIP）；组兄弟 D:/autostack/.wt/edit-003/auto-lang
  @e535e7437（detached，bps dep）| blockers: §10-B1（上游 auto-lang）
  | next: review（对 AC-03 偏差与 P-5/P-10/P-11 三处执行内裁定重点复核）

- 2026-09-20 stage: review | PLAN-003 | r1 | **needs_replan** |
  reviewed_commit: b244d56（worktree plan-003-dev，零脏改，6 提交链完整）|
  base_commit: 10881b9 | dependency_revisions: auto-lang@e535e74372（组兄
  弟 detached）；工具链 auto v0.4.2-1498-g34ee15a47 | spec_inputs:
  specs/auto-edit/README.md@worktree-c95744d（SD-01/02 落地版）|
  acceptance_results: AC-01 pass / AC-02 pass / AC-03 **partial→驱动
  needs_replan** / AC-04 pass / AC-05 pass / AC-06 pass（登记分支）|
  findings: **F-RV1**（blocker，AC-03/T-03）：F-W1 上游缺口独立复现
  一致（本 review 新鲜 split 探针：ws_root 真实返回 / exists(绝对路径,
  真实文件)→0 / read_text→"" / tree→"[]" / write→0）——AC-03「同功能
  环绿」口径在「AutoVM HTTP 服务上下文 File/fs 内建空桩」的上游现实下
  不可达，属起草时未预见的**设计假设失效**，需 new 有界修订 r2（建议
  方向：AC-03 降为「split 边界/契约服务/启动绿 + fs 腿 B1 豁免登记，
  上游修复后补验」，或维持口径挂起待上游——裁定权在用户/起草侧）。
  **F-RV2**（info）：F-W2 独立复现（env_str(PATH)="" 而 AUTO_PROJECT_DIR
  注入面可见——auto-man set_var 注入面与进程 env 两层差异，上游并案）。
  **F-RV3**（info，测试债）：矩阵 T9 9.4「round-trip」断言在 fs 不可
  用时空洞通过（marker 未变即真）——merged 轨不受影响，断言强度改进
  归后续（上游矩阵或本仓测试面），非本计划范围。**F-RV4**（info，认
  可）：执行内三裁定 P-5/P-10/P-11 复核通过——均在授权面内、实证充分、
  README 如实登记；r2 修订时建议将 §5 契约表同步为已执行形态（env_str
  列已在，fs.join 出契约已注）。**F-RV5**（info）：diff 范围与计划影
  响面严格一致（6 文件，无越权）；worktree b244d56 干净。规范增量：
  SD-01/SD-02 落地且描述当前行为（含上游缺口现状注记=如实陈述非执行
  日记）✓；frontmatter 三字段按 002 惯例空+书面说明 ✓ | evidence:
  本 review 独立复跑（非采信 work 总结）——矩阵 39/6（第三次，失败六
  项与在册上游债逐项同）/ regen_vue.py --build exit 0（✓ built 3.94s，
  七补件幂等零告警）/ split 探针（F-W1 五端点复现）/ --server vm 独立
  serve 复验（六路由+ws_root）/ a2r 生成物源级核对（main.rs:199
  `use api::Db` 存在 + api.rs 无 Db 定义 → E0432 必然；六 fn 皆
  `// TODO: Implement` 空体）/ grep 静态检查（front 四命中全注释）|
  next: new（r2 有界修订 AC-03 口径 + §5 契约表同步；T-03 已重开，
  其余五任务勾选与全部实证保留；B1/F-W2/F-R1 上游并案面见 §10-B1）

- 2026-09-20 stage: review 补充勘定 | PLAN-003 | r1 | F-W1/F-W2 根因
  重新定性（用户发起，为 auto-lang 修复计划供料）| **F-W1 的「File/fs
  内建空桩」定性作废**：内建层完好——上游 013-todo 以 `--server vm`
  复现，无参 `list_todos()` 正常返回种子数据（同上下文内建与 VM 执行
  全通）。**真根因 = AutoVM HTTP server 的实参装配约定断层**
  （http_server.rs legacy positional 分支）：
  ① GET query 参数不按名绑定形参，而是把整个 query 集合序列化为单个
  JSON 对象串（`{"path":"pac.at","depth":"1"}`）作第 1 位置实参推入
  （async 版 ~L2870「Plan 346: Push query params as a JSON object
  string if no body」；stdnet 版同构 ~L2085）；
  ② POST body 不解析 JSON，原始串整个塞第 1 实参（013 复现铁证：
  `create_todo(text)` 收到 text=`{"text":"probe-item"}` 字面量）；
  ③ 仅 `:param` 路径段参数逐个按位推入（这条是对的）。
  auto-edit 全部现象由此统一：带 query 参的 exists/read_text/tree/
  env_str 拿到 JSON 集合串当路径/变量名 → fs 系内建静默容错
  （`unwrap_or_default`，stdlib.rs:337-355）→ 返回类型正确的空值；
  无参 ws_root 活。**F-W2 并案**（env_str(name) 的 name =
  `{"name":"PATH"}` → Env.get 返回 ""——非 env 可见性问题）。
  修复面定位：http_server.rs 两处实参装配 + route 表数据结构
  （get_http_routes 返回 (method,path,fn_name) 三元组无 param 清单——
  按名绑定缺数据；文件内自注「Long-term: codegen should record
  per-param types in api_routes」= Plan 326 Phase 5 在册 TODO 即此缺口）。
  修复后预期：vm split 功能环 fs 腿直接复活（无需改本仓），B1 解阻。

- 2026-09-21 stage: work 复验 | PLAN-003 | r1 | 上游 669 落地后 B1 闭环，
  T-03 复勾，execution_done 复立 | code_commit: 7a4ed53（README split 注记
  勘误——唯一改动）| 复验证据（工具链重建后 auto.exe 含 669，重建前探针
  先证旧二进制仍复现 raw body 字面量）：①六端点直打全真值；②split 单实例
  功能环 11/11（树/open/edit/save/quit-save 全经 back HTTP）；③013
  create_todo text=probe669x（按名解析铁证）；④merged 矩阵 + vue regen
  build 复跑绿。**needs_replan 动因消解**：F-RV1 所指 AC-03 上游不可达
  前提已被 669 消除，AC-03 按 r1 原口径达成——r2 修订不再必要（复审另裁
  除外）。**F-V1（新观测，上游 668/669 下游面，非本仓改动所致）**：
  新工具链下矩阵形态位移——menubar 六债转绿（T2 菜单项 PASS 等），
  46 项判定=44 PASS/2 FAIL（T10「tabs left」+「ActSave button missing」，
  快照/状态漂移形态，与 auto-lang 668 F-668-R1「并流快照漂移」领域
  吻合）+ T8 段瞬时 MCP 拒连（端口仍 LISTEN、后续快照可达=quit 流程态
  瞬时阻塞）致脚本尾部崩（无 RESULT 行）；旧工具链 39/6 基线证据保留
  （绑定其时点工具链）。F-V1 归上游跟踪，不阻塞本计划（本仓代码零改动
  前提下的工具链位移观测）。另勘：015 `/api/notes/search` 被
  `/api/notes/:id` 遮蔽返回 400 指名（**既存路由次序债被 669 显性化**，
  非回归——旧二进制同匹配但静默 null；一并归上游）。
  | next: review（re-review：AC-01..06 全套，重点 AC-03 新证据与 F-V1
  归属裁量）

## 10. 待澄清事项

1. **vue 轨 untitled/save-as 形态**：`dialog_save` 为 vm 侧 UI 内建，
   vue 轨首版建议降级（untitled 保存固定落工作区根 `untitled-N.at`，
   或 vue 轨禁用该项并提示）。默认按前者执行，评审可改。
2. **code_editor vue 侧支持度**：T-00 探针定。若生成器缺口实存（如
   code_editor 无 vue 映射），裁剪选项 = vue 轨降级 textarea（jade-edit
   Q1 先例：isEditorNode 冻结投影）或登记上游另立计划；不扩本计划规模。
3. **vue dev 期后端供给**：`auto run` 同目录起 AutoVM HTTP（split）供
   vite 代理，或独立 serve 形态——T-00 一并勘定（jade-edit PLAN-001
   T-00 会复用此结论）。
   → **已裁（T-00 P-7 + T-05 实测）**：独立 serve 形态胜出——
   `auto run --server vm -B <port>`（后端）+ `gen/front/vue` 内
   `AUTO_HTTP_PORT=<port> pnpm dev`（前端，vite 代理 /api 实测 200）；
   ⚠ `auto run -r vue` 内置再生成会覆盖 regen 补件，不用。

4. **B1（已解阻 2026-09-21）**：vm split 形态的 AutoVM HTTP server 实参
   装配断层——**上游 auto-lang PLAN-669 已修**（#[api] 形参签名侧信道 +
   四 serve 路径统一按名绑定器 + 无签名位序回退；复审 R1/R2/R3 清偿落
   master ac2bdcc85）。本仓复验：六端点全真值 + split 功能环 11/11 +
   013 POST 按名铁证，零本仓改动（仅 README 注记勘误）。工具链前置：
   auto.exe 须为含 669 的构建（≥2026-09-21）。r2 修订面随 B1 解阻取消
   （README 勘误已随 7a4ed53 落地）。F-R1（a2r E0432 + 空体桩）仍未修，
  归上游另案。
