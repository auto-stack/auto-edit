# front/back 边界契约（modules/back-api）

> 来源：PLAN-003 交付 + src/back/{api.at,fsys.at}；计数勘正与 IO 字节
> 语义节=PLAN-008 SD-02；搜索服务端点节=PLAN-009 SD-02。

## 契约（src/back/api.at，九 #[api]——PLAN-009 勘正：PLAN-008 计数
「七」未含 PLAN-009 增 regex_replace/search_files）

`ws_root / tree / read_text / read_text_range / write_text / exists /
env_str / regex_replace / search_files`——路由前缀 /api，GET 走 query、
POST 走 body。消费形态：`use back.api: <fns>` 裸函数直调（013-todo/
015-notes 形态）：

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

## 搜索服务端点（PLAN-009 SD-02，M2-02）

- **`regex_replace(text, pattern, replacement, global) str`**（POST
  `/api/regex_replace`）：Rust regex（AutoVM `Regex.replace` shim），与
  内核查找链双轨同语义。**大小写不敏感默认**——pattern 无旗标前缀
  （`(` 开头）时 back 侧补 `(?i)`（裸 Regex.replace 是 case-sensitive，
  不补齐与高亮面内核 builder `case_insensitive(true)` 劈叉，T13.3 实勘
  教训）；查找面 `(?-i)` 直通形态原样透传。flags `"g"`=全局（front
  ReplaceAll 恒 true）。返回 JSON `{"out":<替换后全文>,"count":<真实
  替换数>}`——count 用 **marker 算术**（sentinel 串替换后 len+replace
  商；`Regex.match` 'g' 列表 `.len()` 在 vm handler 字节码恒 20 已弃用，
  upstream §12 观察件），count 无列表帽。
- **`search_files(path, pattern, limit) str`**（GET `/api/search_files`）：
  工作区递归 + 逐行匹配（`split("\n")` 行号天然；跨行不匹配=内核 find
  逐行同口径）。返回 JSON `{"results":[{"file","line","preview"}…],
  "count":<条数>,"truncated":bool}`——count 由 back 计数交付（front 侧
  列表 `.len()` 不可靠同上）。上限：条数达 limit 置 truncated（front
  恒传 500；limit<=0 兜底 500）；`fs.metadata` 文件 >10MB 跳过；读失败
  （非法 UTF-8/锁定/竞态删除）try/catch 静默跳过不中断整体。大小写
  不敏感默认 + `(?i)`/`(?-i)` 前缀透传（与 regex_replace 同约定）。
  preview=行文本截断 200 字符。噪声过滤镜像 `fs.tree` skip-list 语义
  （隐藏段/VCS/build/依赖树；**剥根后相对路径**段匹配——根自身点段如
  `.wt` 组目录不可触发，误杀全部条目实勘教训）。
- **实现注意（1914 工具链实勘，零 auto-lang 改动约束下的选型）**：
  递归枚举用 `fs.list_dir`（codegen 映射 `auto.fs.walk`=递归扁平路径
  JSON）；`fs.walk` 的 codegen 映射错名（`auto.file.walk`，运行期
  File.create 错派 500）、`fs.walk_files`(2847) 未入 bigvm 白名单且
  撞号 `Path.to_string`、`fs.metadata` 被 codegen 映射覆盖为
  `auto.fs.size`（int 字节长；metadata JSON 的 is_dir/len 字段访问不可
  用）——三件登记 upstream §12 供料。is_dir 用 `fs.is_dir`(1009)。
