# 041-auto-edit — AutoLang 文本编辑器（多文件组件化）

> 本项目（auto-edit 仓）拷贝自 auto-lang `examples/ui/041-auto-edit`，源
> commit 见 [`specs/PROVENANCE.md`](../PROVENANCE.md)；下方 Plan 补记为
> 源仓历史，保留为沿革记录。

一个"严肃应用"轨道的 AutoUI 示例：多 tab 代码编辑器（原生 CodeMirror6 内核），
带菜单栏/工具栏/全局快捷键三源动作触发、右键菜单、脏 tab 关闭确认、Console
面板、撤销重做与文件打开/保存。Plans 413/414/418/420/422/428 持续迭代，
Plan 449 完成组件化重构（单文件 486 行 → 五文件工程）。

## Concepts

- **store 承载全部状态与业务逻辑（038/013 形态）** —— `editor_store.at` 持有
  tabs/光标/Console/弹层等全部状态；App 的 `on` 薄委托 `store.Xxx()`，事件名
  与 `auto-edit.at` 的 handler 映射一一对应（Action=声明层，Event=执行层）。
  重复逻辑收口为两个内部 helper msg：`RemoveAt`（关闭 tab 的 remove+索引修补+
  激活重算，原先 CloseTab/ConfirmClose 各持一份）、`SyncCursor`（line/col/sel
  三元组读回，原先 5 处重复）。store handler 间经 `store.Xxx()` 互调（038
  先例）。派生标量仍由 handler 就地重算——VM view 不能调函数（Plan 402
  约束），模板只读字段。
- **013 式组件（无 props + 直调 store）** —— `StatusBar`/`ConsolePanel`/
  `EditorCtxMenu` 不带 props：标量/锚态经 `use editor_store` 直读 `.store.*`，
  自有 msg，handler 直调 `store.Xxx()`（013-todo 的 TodoList 形态）。
- **vm 组件边界（Plan 449 实测定性，重构设计的硬约束）**：
  1. **回调 props（`on_xxx: msg`）会使组件整体退化为空 fallback**——
     015-notes 的 NavTree/EditorPanel 在 vm 模式下即如此（015 是 vue 示例）。
  2. **组件子树对 MCP 快照不可见**（渲染正常、handler 派发正常，但
     `autoui_snapshot` 只走根模板）——测试矩阵靠快照定位的交互不能进组件。
  3. **view fn 片段的参数化条件（onclick 实参/条件样式/if 分支）在 vm
     视图构建中不求值**——片段去重 tab 条不可行（015 的 NoteItem 片段
     先例只在 vue 模式验证过）。
  因此 tab 条（x 按钮形状定位、"+" 的 `onclick: .ActOpen`）、确认弹层
  （"直接关闭" 文本定位）、code_editor 绑定与空态文本留在 App 根视图。
- **vm 字节码 bug 规避**：`code_editor_set_text` 编译进 store handler 会产出
  坏字节码（`virt_memory.rs read_i32` 越界 panic，Plan 449 实测；widget
  handler 中正常）——该调用留在 App 根 handler（`.ActNew` 内，见 app.at）。
- **动作三源绑定（Plan 418/423/451）** —— action 注册表 + menubar/toolbar
  结构以 `widget App` 内的 **`actions {}` 声明块** 表达（Plan 451 起 DSL 化，
  原项目根的 auto-edit.at 外挂配置退役；外挂文件形态仍兼容——DSL 优先）。
  vm 渲染器经 `action_config()` 消费：① 键盘回退层（DSL onkeydown 之下）；
  ② `menubar{}`/`toolbar{}` 占位的配置合成渲染；③ MCP 自动化同源派发。
  `handler: .ActXxx` 在**解析期校验**命中本 widget 的 `on{}` 事件；
  `enabled_if`/`checked_if` 为条件表达式字符串，对合并根 state 求值
  （`.tab_count` 等，无前缀）。热重载：改 app.at 后经 MCP 的
  `action_config_reload` 工具（或渲染器 mtime 轮询）重读源文件重新提取。
- **front/back 拆分（PLAN-003）** —— 全部文件系统面收口 `src/back/`
  （`api.at` 契约 + `fsys.at` Auto 实现本体），front 经
  `use back.api: ws_root, tree, read_text, write_text, exists, env_str`
  裸函数直调（013-todo/015-notes 形态）：vm merged = 进程内 CALL（无
  HTTP）；vm split / vue 轨 = HTTP（ts_adapter 生成 client，vite 代理
  `/api` → AUTO_HTTP_PORT）。front 零 `fs.*`/`File.*`/`Env.get` 内建
  （vue 轨 ts_adapter 将 fs/File 拦为 `__vmOnly` 抛错桩——拆 back 的
  动机）；路径拼接走本地字符串（`ws_dir + "/" + id`，`fs.join` 亦在
  拦截面）。**pac 不写 `api:` 字段**——服务引擎留运行期 `--server`
  切换，默认 AutoVM + merged 直调（`api:"rust"` 会杀 merged）。
- **vue 轨（PLAN-003 双轨化）** —— pac `render: ["vm","vue"]` 单声明 +
  双命令分工（jade-edit PLAN-081 R-1 裁定 A' 同款）：vm 轨
  `auto run -r vm`，vue 轨 `python scripts/regen_vue.py --build`（生成
  固定 `--lenient`——S001 schema 漂移 = 上游 aura schema 未吸收
  PLAN-630 menubar 族 props，债在上游；⚠ 禁止裸 `auto build`：Multi
  下选 vm 项走 C/ninja 转译路径）。**vue 生成器已支持 actions 消费**
  （快捷键经 keydown 回退层、menubar/toolbar 占位合成——PLAN-070 T-05
  去门化；旧「尚未接入」陈述作废）。vue 首版 = 构建绿 + 生成即展示；
  运行期限制（vm 宿主内建无 vue 运行时）：`dialog_open/dialog_save`
  文件对话框、`console_*` 面板数据、`code_editor_*` 读回族、
  `Env.get`/`Process.exit`——由 `scripts/regen_vue.py` 补类型声明使
  构建绿，运行期缺口登记于此，深度双轨归后续计划（jade-edit 换基
  承接同型深水区）。

## Source

| 文件 | 职责 |
|---|---|
| `src/back/api.at` | 后端契约（PLAN-003）：六 `#[api]` fn（ws_root/tree/read_text/write_text/exists/env_str，路由前缀 /api，GET query/POST body）+ 边界语义注记 |
| `src/back/fsys.at` | 后端实现本体：`fs.*`/`File.*`/`Env.get` 收口（ws 根解析 + 四 IO + env 读）；模块名 fsys 避与内建 fs 对象同名，且 split 扁平化只吃整模块 `use` |
| `scripts/regen_vue.py` | vue 轨一键链（PLAN-003 T-04）：生成 + 七类生成器缺口补件 + pnpm install/build |
| `src/front/app.at` 的 `actions {}` 块 | 动作注册表（14 个 action）+ menubar/toolbar 结构（Plan 451 DSL 化；原根目录 auto-edit.at 已删除） |
| `src/front/app.at` | 根 widget `App`（213 行）：actions 声明块 + view 组合 + on 薄委托；测试定位锚交互（tab 条/确认弹层/编辑区/空态）留根 |
| `src/front/editor_store.at` | `store EditorStore`（342 行）：全部状态 + 业务逻辑 + RemoveAt/SyncCursor 收口；数据面经 `use back.api` 直调（PLAN-003） |
| `src/front/status_bar.at` | `StatusBar` 组件（读 `.store` 标量；`ToggleConsole → store.ActConsole()`） |
| `src/front/console_panel.at` | `ConsolePanel` 组件（`Clear → store.ConsoleClear()`） |
| `src/front/ctx_menu.at` | `EditorCtxMenu` 组件（坐标锚态直读 `.store`；`Cut/Copy/SelectAll/Dismiss → store.Ctx*()`） |

## How to Run

```
cd specs/auto-edit          # 本仓布局（自仓根起）

# —— vm 轨（默认 AutoVM + merged 进程内直调）——
auto run -r vm              # iced 原生窗口（工具链经 PATH 解析）

# —— vm 轨 split 形态 ——
auto run -r vm --no-merge   # VM+VM split：AutoVM HTTP 后端 + 前端窗（HTTP 往返）
auto run --server vm        # 后端独立 serve（只起 AutoVM HTTP，不开窗——vue dev/联调用）
# split 功能环已全绿（2026-09-21 复验：树/打开/编辑/保存/退出存盘经
#   back HTTP 全通）——上游 auto-lang PLAN-669 修复 #[api] 实参按名绑定
#   后解锁（此前 query 集合串直塞/body 不解析致带参契约全空，PLAN-003
#   F-W1→勘误定性为实参装配断层）。工具链须含 669（≥ 2026-09-21 构建）。

# —— 引擎切换（VM+Rust）——
auto run -r vm --server rust   # a2r 生成的 Rust axum 后端
# ⚠ 现状：a2r server 生成器模板假设 api::Db 状态注入 + 契约 fn 转译为
#   空体桩（PLAN-003 F-R1 实勘，编译 E0432）——rust 引擎暂不可用。

# —— vue 轨 ——
python scripts/regen_vue.py --build        # 生成 + 补件 + install/build（vue-tsc+vite 绿）
# vue dev（两终端，jade-edit 同款配方；⚠ 不用 auto run -r vue——其内置
# 再生成会覆盖 regen_vue.py 补件）：
#   终端1（后端独立 serve）：auto run --server vm -B 8173
#   终端2（前端）：cd gen/front/vue && AUTO_HTTP_PORT=8173 pnpm dev
#   vite（pac front_port）代理 /api → AUTO_HTTP_PORT（实测代理 200）。
#   ⚠ 必须显式 --server vm / AUTO_HTTP_PORT 对齐——vue.rs 缺席时默认走
#   rust 引擎。后端 API 经 669 修复可用；vue 首版仍以构建绿为准
#   （vm 宿主内建无 vue 运行时，见 Concepts vue 轨节限制清单）。

# —— 性能模式（L2，PLAN-004：tools/perf 一键链）——
python tools/perf/perf.py check     # 依赖自检+环境指纹（工具链须 ≥1588/含 669）
python tools/perf/perf.py smoke     # rqhost 预热 + VM+RQ 双实例编排验证
python tools/perf/perf.py a2r       # a2r 生成（当前 blocked：上游词汇门，供料 §7）
python tools/perf/perf.py release   # cargo --release（依赖 a2r 绿后生效）
# 语义=测量模式阶梯（docs/strategy/002-north-star-v2.md §5）：L0 日常
#   VM+merged / L2=a2r+release+RQ（唯一有预算效力）。模式矩阵与阻塞全景
#   见 tools/perf/README.md；退出码 0/3/1（3=blocked-on-upstream：RQ 渲染
#   臂 codeeditor 覆盖缺口[供料 §6]、a2r 词汇门[§7]）。PERF_PROJECT /
#   AUTO_RUST_WORKSPACE 可把验证跑锚到主检出（worktree 零重物）。
```

前置：`auto` 在 PATH（或将 `AUTO_BIN` 指向 auto 可执行文件）；`pnpm`
在 PATH（vue 轨 install/build 用）。本仓不构建工具链。bps 蓝图池经
pac.at `dep bps` 消费**兄弟仓** auto-lang 的 blueprints（PLAN-002
方向一；路径相对运行目录——主检出需 auto-edit 与 auto-lang 同居
D:/autostack，组 worktree 需组内 auto-lang 兄弟树；jade 同款依赖
形态）。生成物目录（`deps/ dist/ gen/ rust-workspace/ build/`）均
gitignore，可再生。

## Tests

```
cd specs/auto-edit/tests
python desktop_mcp.py   # MCP 桌面动作矩阵：三源触发/tab 工作区/热重载/OS 键位层
```

前置：`pip install requests`；`AUTO_BIN` 环境变量优先，否则取 PATH 的
`auto`；`AUTO_OPEN_PATH`/`AUTO_SAVE_PATH` 环境变量旁路阻塞式文件对话框
（不设则跳过 T9/T10 分组）。

现状注记（2026-09-21，PLAN-004 T-03 以工具链 v0.4.2-1631 五连跑定标，
收据见 `docs/plans/004` 附表 A）：**测试级失败清零**——原 39/6 的
menubar 快照债已随上游修复消散；**进程级早崩 2/5**（app 实例中途死亡、
MCP 拒连、死亡点逐跑异——上游 F-RV6 竞态存活，证据增补见
`docs/upstream/2026-09-m1-supply.md` §5）。基线口径（临时，上游修复后
废除重跑条款重定正式基线）：**完成态跑次 = RESULT 行出现且 ≥49
passed / 0 failed 判绿；无 RESULT 行 = 工具链竞态早崩 → 重跑一次而非
计败**。

注：Plan 451 起 T10「热重载」走 DSL 源路径（reload 工具或 mtime 轮询重读
app.at 重新提取 actions + generation bump → 视图重建），实测 50/0 全绿。
OS 用户键位层（`%APPDATA%/auto/keymaps/auto-edit.at`）保持外部文件——那是
用户偏好覆盖而非 app 代码；app id 由 pac.at 的 `name`（经 `auto run` 注入
`AUTO_APP_ID`）提供。

## Plan 626 补记（VM 实机验证四修正）

- **状态栏 行:列**：`text "${.store.line}:${.store.col}"` 多段点路径插值由
  框架修复（aura_view_builder 走条件表达式同款扁平化通道），不可解析时原样
  保留完整模板（含前导点）。
- **脏标记**：脏 tab 标题旁 `*`（`if t.dirty`）；关闭脏 tab 与退出/关窗均走
  标准 `alert-dialog`（PLAN-530 模态族），原固定坐标 confirm popover 退役
  ——VM 下坐标锚弹层有落回普通流的底层缺陷（债务登记），alert-dialog 无此问题。
- **窗口 X 拦截**：声明 `.CloseRequest` handler 的应用可拦截 OS 关窗请求
  （fire 语义同 `.Init`；未声明的应用行为不变）。auto-edit：有脏 tab 弹
  「取消/不保存退出/保存并退出」，否则直接退出；菜单「退出」共用同一入口。
- **Explorer 真目录**：`.Init` → `store.LoadWorkspace()`（Init 名保留给根
  widget 生命周期，store 侧 handler 不得占用）经 `fs.tree(AUTO_PROJECT_DIR, 4)`
  + `json.to_value` 装载真实目录树，头部显示 workspace 名；树节点 id 为相对
  路径，点击经 `fs.join` 读盘开文件。启动日志的 "App.Init failed" 随之消失。

## Plan 629 补记（寄宿公共 scroller）

编辑器滚动条**改用 AutoUI 公共 scroller**（官方 `scrollable`，vue 风格滚动条自动
生效），自绘滚动条与内部滚轮路径退役（headless/单测保留，`AUTO_EDITOR_NO_SCROLLER=1`
可临时关闭寄宿）。集成契约三机制：

- **高度上报**：折叠展开即内容高度变化 → 编辑器重排 → scroller 更新滚动范围与
  thumb 比例（`CodeEditorCore::content_height`，实时 fold 投影）。
- **偏移同步**：滚动偏移由 scroller 持有；编辑器 draw 每帧用 viewport 切片做
  虚拟化渲染（只 shape 可见行，`sync_external_scroll` 粗定位+归一）。
- **光标跟随**：键盘/IME 移动光标出视口 → core 请求标记 → 会话漏斗
  （dispatch_app 尾部）转 `operation::scroll_to`（同拍生效）。

## Plan 630 补记（声明式可复用 menubar 组件族）

菜单改用**声明式 menubar 组件族**（不依赖 actions DSL 合成）：

```at
menubar {
    menubar-menu (value: "file") {
        menubar-trigger "文件"
        menubar-content {
            menubar-item (title: "新建", icon: "file-plus", shortcut: "Ctrl+N") { onclick: .ActNew }
            menubar-separator
            menubar-checkbox-item (title: "切换 Console", checked: .console_open) { onclick: .ActConsole }
        }
    }
}
```

- VM 端 lowering 到公共 Popover 原语（BottomStart + MENUBAR_OPEN 开合注册表）；
  Vue 端直出 shadcn Menubar 组件树——两端同语义。
- item 支持 `title/icon/shortcut`、`checked`/`enabled` 表达式（实时求值）与
  `onclick`；`menubar-separator` 横向通栏。
- `menubar {}` **空标签**保持原 actions DSL 合成语义（向后兼容）；actions 块
  仍负责快捷键三源绑定。
