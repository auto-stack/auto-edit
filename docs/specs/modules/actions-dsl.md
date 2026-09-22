# 动作三源绑定（modules/actions-dsl）

> 来源：README Concepts（Plan 418/423/451）+ app.at actions 块。

## actions {} 声明块（Plan 451 DSL 化）

动作注册表（14 个 action）+ menubar/toolbar 结构以 `widget App` 内的
`actions {}` 声明块表达（原项目根 auto-edit.at 外挂配置退役；外挂文件
形态仍兼容——DSL 优先）。vm 渲染器经 `action_config()` 消费三源：

1. **键盘回退层**（DSL onkeydown 之下）；
2. **menubar{}/toolbar{} 占位的配置合成渲染**；
3. **MCP 自动化同源派发**。

## 契约要点

- `handler: .ActXxx` 在**解析期校验**命中本 widget 的 `on{}` 事件。
- `enabled_if`/`checked_if` 为条件表达式字符串，对**合并根 state** 求值
  （`.tab_count` 等，无前缀）。
- 热重载：改 app.at 后经 MCP `action_config_reload` 工具（或渲染器
  mtime 轮询）重读源文件重新提取 + generation bump → 视图重建
  （实测 50/0 全绿，T10 测试锚此路径）。
- OS 用户键位层（`%APPDATA%/auto/keymaps/auto-edit.at`）保持外部文件
  ——用户偏好覆盖而非 app 代码；app id 由 pac.at 的 `name`（经
  `auto run` 注入 `AUTO_APP_ID`）提供。

## 声明式 menubar 组件族（Plan 630，与 actions DSL 并存）

菜单可改用声明式 `menubar{}` 组件族（不依赖 actions DSL 合成）：VM 端
lowering 到公共 Popover 原语（BottomStart + MENUBAR_OPEN 开合注册表），
Vue 端直出 shadcn Menubar 树。item 支持 `title/icon/shortcut`、
`checked`/`enabled` 表达式（实时求值）与 `onclick`；`menubar-separator`
横向通栏。**空标签 `menubar {}` 保持 actions DSL 合成语义**（向后兼容），
actions 块仍负责快捷键三源绑定。
