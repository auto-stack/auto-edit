# front/back 边界契约（modules/back-api）

> 来源：PLAN-003 交付 + src/back/{api.at,fsys.at}；计数勘正与 IO 字节
> 语义节=PLAN-008 SD-02。

## 契约（src/back/api.at，七 #[api]——PLAN-008 勘正：PLAN-007 增
read_text_range 后计数「六」未同步）

`ws_root / tree / read_text / read_text_range / write_text / exists /
env_str`——路由前缀 /api，GET 走 query、POST 走 body。消费形态：
`use back.api: <fns>` 裸函数直调（013-todo/015-notes 形态）：

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

## IO 字节语义（PLAN-008 SD-02，M2-01 字节保真边界）

- **BOM/EOL 均 front 字符域处理**（字节保真零新端点）：BOM=U+FEFF 前缀
  字符（read_text_range 窗读可探）；EOL=\r\n/\n/\r 字符替换。back 各
  IO 端点对二者**逐字节直通**（不剥离/不规范化）。
- **非法 UTF-8 错误形直通**：`read_text` → 空串（unwrap_or_default
  惯例）；`read_text_range` → envelope `{"text":"","total":-1,
  "next_offset":null}`；`code_editor_load_file`（编辑器装载端点）→
  -1。下游兜底语义见 editor-store.md 字节保真节（错误形 tab+只读+
  save 拦截）；替换符查看（U+FFFD lossy 渲染）=上游 lossy 读端点
  want（docs/upstream 2026-09 供料 §11）。
