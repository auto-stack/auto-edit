# front/back 边界契约（modules/back-api）

> 来源：PLAN-003 交付 + src/back/{api.at,fsys.at}。

## 契约（src/back/api.at，六 #[api]）

`ws_root / tree / read_text / write_text / exists / env_str`——路由前缀
/api，GET 走 query、POST 走 body。消费形态：`use back.api: <fns>` 裸
函数直调（013-todo/015-notes 形态）：

| 轨道/形态 | 通路 |
|---|---|
| vm merged（默认） | 进程内 CALL（无 HTTP） |
| vm split | AutoVM HTTP 后端 |
| vue | HTTP（ts_adapter 生成 client；vite 代理 /api → AUTO_HTTP_PORT） |

## 边界铁律

- front **零** `fs.*`/`File.*`/`Env.get` 内建（vue 轨 ts_adapter 将其拦为
  `__vmOnly` 抛错桩——拆 back 的动机）；`fs.join` 亦在拦截面，路径拼接
  走本地字符串。
- 实现本体 `fsys.at`：ws 根解析 + 四 IO + env 读；模块名 `fsys` 避与
  内建 fs 对象同名（split 扁平化只吃整模块 `use`）。
- **pac 不写 `api:` 字段**——服务引擎留运行期 `--server` 切换；默认
  AutoVM + merged 直调（`api:"rust"` 会杀 merged）。

## split 功能环状态

全绿（2026-09-21 复验：树/打开/编辑/保存/退出存盘经 back HTTP 全通）——
上游 auto-lang PLAN-669 修复 #[api] 实参按名绑定后解锁（此前 query 集合
串直塞/body 不解析致带参契约全空，PLAN-003 F-W1→勘误定性为实参装配
断层）。工具链须含 669（≥ 2026-09-21 构建）。

## 引擎切换现状（rust 臂 blocked）

`auto run -r vm --server rust`（a2r 生成的 Rust axum 后端）**当前不可用**：
a2r server 生成器模板假设 api::Db 状态注入 + 契约 fn 转译为空体桩
（PLAN-003 F-R1 实勘，编译 E0432）。阻塞全景与供料归因见
[perf-measurement.md](perf-measurement.md)。
