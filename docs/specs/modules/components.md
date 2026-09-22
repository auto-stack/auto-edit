# 组件模型与 vm 组件边界（modules/components）

> 来源：README Concepts + Plan 449 实测定性（重构设计的硬约束）。

## 013 式组件（无 props + 直调 store）

`StatusBar`（56 行）/`ConsolePanel`（42 行）/`EditorCtxMenu`（41 行）
不带 props：标量/锚态经 `use editor_store` 直读 `.store.*`，自有 msg，
handler 直调 `store.Xxx()`（013-todo TodoList 形态）。

## vm 组件边界三硬约束（Plan 449 实测，新增组件必查）

1. **回调 props（`on_xxx: msg`）使组件整体退化为空 fallback**——
   015-notes 的 NavTree/EditorPanel 在 vm 模式即如此（015 是 vue 示例）。
2. **组件子树对 MCP 快照不可见**——渲染正常、handler 派发正常，但
   `autoui_snapshot` 只走根模板：测试矩阵靠快照定位的交互不能进组件。
3. **view fn 片段的参数化条件（onclick 实参/条件样式/if 分支）在 vm
   视图构建中不求值**——片段去重 tab 条不可行（015 NoteItem 先例只在
   vue 验证过）。

因此以下交互**留在 App 根视图**：tab 条（x 按钮形状定位、"+" 的
`onclick: .ActOpen`）、确认弹层（"直接关闭" 文本定位）、code_editor
绑定与空态文本。

## vm 字节码 bug 规避

`code_editor_set_text` 编译进 store handler 会产出坏字节码
（virt_memory.rs read_i32 越界 panic，Plan 449 实测；widget handler 中
正常）——该调用留在 App 根 handler（`.ActNew` 内）。

## 滚动寄宿（Plan 629）

编辑器滚动条用 AutoUI 公共 scroller（`AUTO_EDITOR_NO_SCROLLER=1` 可
临时关闭寄宿）。三机制：高度上报（折叠展开→content_height→滚动范围）、
偏移同步（scroller 持偏移，draw 每帧 viewport 切片虚拟化）、光标跟随
（出视口→scroll_to 同拍生效）。
