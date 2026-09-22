# 架构总纲（01-architecture）

> 来源：README Concepts（架构真源）+ PLAN-001/003 交付 + 代码
> （src/front 943 行 + src/back 108 行）。修订走追加。

## 形态：单工程双轨（PLAN-003，jade-edit R-1 裁定 A' 同款）

`pac.at` 单声明 `render: ["vm","vue"]` + 双命令分工：

- **vm 轨（主）**：`auto run -r vm`（iced 原生窗）。三种后端形态：
  - merged（默认）：AutoVM 进程内直调，无 HTTP；
  - split：`auto run -r vm --no-merge`（AutoVM HTTP 后端 + 前端窗）；
  - 独立 serve：`auto run --server vm`（vue dev/联调用）。
- **vue 轨**：`python scripts/regen_vue.py --build`（strict 裸生成 + 构建
  绿；2026-09-21 起七类补件链退役——上游 PLAN-671 生成器自完备）。
  ⚠ **禁止裸 `auto build`**（Multi 下选 vm 项走 C/ninja 转译路径）。
  vue 首版 = 构建绿 + 生成即展示；运行期限制清单见 README（vm 宿主内建
  无 vue 运行时：dialog/console_*/code_editor_* 读回/Env.get 等）。

## 分层：store 全承载 + App 薄委托（Plan 449 / 038·013 形态）

`editor_store.at`（527 行）持有全部状态与业务逻辑；`app.at`（274 行）
= actions 声明块 + view 组合 + `on` 薄委托 `store.Xxx()`（事件名与
action 一一对应，Action=声明层，Event=执行层）。store 字段经 lib.rs
**合并进根 state（无前缀）**；派生标量（tab/tab_count/line/col/sel）
由 handler 就地重算——VM view 不能调函数（Plan 402 约束），模板只读
字段。详见 [modules/editor-store.md](modules/editor-store.md)。

## 组件：013 式（无 props + 直调 store）

`StatusBar`/`ConsolePanel`/`EditorCtxMenu` 不带 props：标量/锚态经
`use editor_store` 直读 `.store.*`，自有 msg，handler 直调 store。
vm 组件边界三硬约束（Plan 449 实测定性）见
[modules/components.md](modules/components.md)——tab 条/确认弹层/
code_editor 绑定/空态文本因此留在 App 根视图。

## front/back 拆分（PLAN-003）

全部文件系统面收口 `src/back/`（`api.at` 契约 + `fsys.at` Auto 实现）；
front 经 `use back.api: …` 裸函数直调，**零 `fs.*`/`File.*`/`Env.get`
内建**（vue 轨 ts_adapter 将其拦为 `__vmOnly` 抛错桩）。**pac 不写
`api:` 字段**——服务引擎留运行期 `--server` 切换（`api:"rust"` 会杀
merged；rust 引擎当前 a2r 生成器 E0432 blocked，见 perf 册）。契约细节
见 [modules/back-api.md](modules/back-api.md)。

## 动作三源（Plan 418/423/451）

menubar/toolbar/快捷键共用 `app.at` 的 **`actions {}` 声明块**（14 个
action；DSL 优先，外挂 auto-edit.at 形态兼容）。`handler: .ActXxx`
解析期校验；`enabled_if`/`checked_if` 对合并根 state 求值。见
[modules/actions-dsl.md](modules/actions-dsl.md)。

## 源文件清单（现役）

| 文件 | 行数 | 职责 |
|---|---|---|
| src/front/app.at | 274 | 根 widget：actions 块 + view + on 薄委托 + 测试锚交互 |
| src/front/editor_store.at | 527 | EditorStore：全部状态与业务逻辑 |
| src/front/status_bar.at | 56 | 状态栏组件（行:列 等） |
| src/front/console_panel.at | 42 | Console 面板组件 |
| src/front/ctx_menu.at | 41 | 右键菜单组件 |
| src/back/api.at | 65 | 六 #[api] 契约 |
| src/back/fsys.at | 43 | fs/File/Env 收口实现 |
| scripts/regen_vue.py | — | vue 轨一键链 |
| tests/desktop_mcp.py | 879 | MCP 桌面动作矩阵（唯一测试面） |

生成物目录（deps/dist/gen/rust-workspace/build）gitignored、可再生。
运行矩阵（含引擎切换/vue dev 双终端/perf/bench 命令）以
`specs/auto-edit/README.md` How to Run 节为准（保持单源，不在此复制）。

## 历史沿革锚点

- Plan 449：单文件 486 行 → 五文件工程组件化（vm 边界三约束即源于此）。
- Plan 626 补记：VM 实机验证四修正（状态栏插值/脏标记 `*`+alert-dialog
  模态/窗口 X 拦截 `.CloseRequest`/Explorer 真目录树）。
- Plan 629 补记：编辑器滚动条改寄宿公共 scroller（高度上报/偏移同步/
  光标跟随三机制；`AUTO_EDITOR_NO_SCROLLER=1` 可关）。
- Plan 630 补记：声明式 menubar 组件族（VM lowering 到 Popover 原语，
  Vue 直出 shadcn Menubar；空 `menubar {}` 保持 actions 合成语义）。
- PLAN-001/002：bootstrap 与 bps dep 消费（见 PROVENANCE 与 reviews 册）。
