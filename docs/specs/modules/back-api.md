# front/back 边界契约（modules/back-api）

> 来源：PLAN-003 交付 + src/back/{api.at,fsys.at}；计数勘正与 IO 字节
> 语义节=PLAN-008 SD-02；搜索服务端点节=PLAN-009 SD-02；目录 diff 与
> 同步端点节=PLAN-012 SD-02；file_size 端点节=PLAN-013 SD-02。

## 契约（src/back/api.at，**十四 #[api]**——PLAN-013 勘正：PLAN-012
十三件基础上增 file_size）

`ws_root / tree / read_text / read_text_range / file_size / write_text /
exists / env_str / regex_replace / search_files / diff_files / diff_dirs /
sync_copy / sync_delete`——路由前缀 /api，GET 走 query、
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

## 文件 diff 端点（PLAN-011 SD-02，M3-01）

- **`diff_files(path_a, path_b, ctx) str`**（GET `/api/diff_files`）：
  朴素分层过渡计算层（envelope 契约=替换缝——内核引擎落地仅换
  `fsys.diff_files_json` 实现体，front/矩阵零改动）。返回 JSON
  `{hunks:[{a1,a2,b1,b2}],rows:[{lo,ro,ln,rn,lk,rk,lpre,lmid,lpost,
  rpre,rmid,rpost}],adds,dels,truncated,degraded,err}`——hunk 区间
  0 基半开；rows.lo/ro 1 基缺席侧 0；三段标记=配对行公共前后缀裁剪；
  CR 容忍（
≡
）；`ctx<=0` 兜底 3。上限门：尺寸 **1MB pre-read**
  （fs.metadata 即时拒）+ 行数 **10k** post-split——错误形 err 含
  「等待内核引擎 diff_snapshots（架构阻塞）」注记，hunks/rows 空数组。
  实现约束：单 handler ≤10M VM steps（engine.rs:2145；全链 ~2.2M 实
  测），重计算全内联单函数（2044 文件局部 fn 返回值丢失疑回归缓解，
  upstream §14）；三段标记全局字符预算 100k（超预算行整行 mid）。
  **rows 预计算归 back 的理由**：VM view 不能调函数（Plan 402）——
  front 拿到即渲染。完整契约（含渲染就绪形与视图断言口径）见
  modules/diff-view.md（SD-01 主册）。

## 目录 diff 与同步端点（PLAN-012 SD-02，M3-02）

- **`diff_dirs(path_a, path_b) str`**（GET `/api/diff_dirs`）：递归
  遍历+五态分类。返回 JSON `{entries:[{rel,status,size_a,size_b,
  is_dir,note}],counts:{same,added,deleted,modified,binary},truncated,
  err}`——左=旧（deleted=只在左）右=新（added=只在右，BC 同款）；
  分类序=存在性→kind 冲突→二进制启发式（size>0 且 read_text==""，
  ≤2MB 全文域，任一侧命中=binary）→尺寸差→≤2MB 全等→>2MB 同尺寸=
  same+note=uncompared（未比对注记）。条目上限 **5000**（truncated
  注记，counts 与 entries 同域）；skip-list=Explorer/find 同语义；
  **对齐=长度桶+桶积护栏 Σk²≤700k**（同长巨桶超 VM 10M steps 墙——
  定标 N=800 单桶 0.94s ✓/N=1000 WARN[budget] 死——超限 err 形架构
  注记；正解=sort/hash 原语 upstream §15 want）。根缺失→err 不静默。
- **`sync_copy(src, dst, is_dir) bool`**（POST `/api/sync_copy`）：
  文件=字节往返 read_bytes(1005)→write_bytes(1006)（**fs.copy(1007)
  表面被 `copy` 保留字阻断**[Plan 122 废弃 token 词法收编]——T-00①a
  复现，upstream §15 want；字节面=原生 shim 零 VM 步循环）；≤2MB
  预算域（超限 false）；目录=fs.copy_recursive（静默覆盖，Q-2——
  front 确认链管目标存在形）。空路径/缺失源→false。
- **`sync_delete(path, is_dir) bool`**（POST `/api/sync_delete`）：
  文件=fs.delete；目录=**仅空目录** fs.remove_dir（非空原生失败=T-00
  护栏；递归删除 v1 不提供——remove_dir_all 在册不暴露）。空路径/
  根路径（`/`、`\`、盘根）/缺失→false（空串在 HTTP 层即 missing-param
  错误包）。bool 返回=动作后 exists 磁盘 E2E 终判。
- 安全注记（破坏性动作纪律）：动作仅对已完成一次比对的 entries 态
  开放；覆盖复制/删除=front alert-dialog 确认链；back 空路径拒绝。
  完整契约见 modules/diff-view.md 目录节（SD-01 主册）。

## file_size 端点（PLAN-013 SD-02，M2-04 大文件模式探测链）

- **`file_size(path) str`**（GET `/api/file_size?path=..`）：文件字节
  数，**envelope JSON 串形 `{"size":<字节>}`**。实现=fsys.file_size_impl
  （exists 前置判 + fs.metadata 直通[auto.fs.size 映射，int 字节长]+
  try 门）——缺失/IO 错误 → `size:-1`（metadata 对缺失返 0 无异常，
  0 与空文件歧义故显式判存）。消费方=front RunPendingLoad 装载前门
  （editor-store.md 大文件模式节）：负值跳过模式判定、≥50MB 置 big、
  >512MB 拒绝装载。
- **返回形勘定（T-00 Phase A 实勘，upstream §16 观察）**：裸 int 返回
  过 AutoVM HTTP 面=serialize `null`（merged 进程内直调 ✓ 正常）——
  api.at 头注「返回面 str/int/bool」的 int 腿在 split/vue 轨**不成立**
  （本端点是首个 int 返回件，实勘即破）；JSON 串 envelope=仓内既证
  双轨形（search_files count 同款），本端点从之。want=HTTP 层 int 返回
  序列化修复（清偿后 envelope 可简化，front 侧零行为依赖——`?? -1`
  兜底形保持）。
