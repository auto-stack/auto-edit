# front/back 边界契约（modules/back-api）

> 来源：PLAN-003 交付 + src/back/{api.at,fsys.at}；计数勘正与 IO 字节
> 语义节=PLAN-008 SD-02；搜索服务端点节=PLAN-009 SD-02；目录 diff 与
> 同步端点节=PLAN-012 SD-02；file_size 端点节=PLAN-013 SD-02；
> diff_buffers 第 15 端点节+diff 双端点引擎时代注记=PLAN-016 SD-02；
> diff 窗口第 16 端点节=PLAN-022 SD-03。

## 契约（src/back/api.at，**十六 #[api]**——PLAN-013 十四件+PLAN-016
diff_buffers+PLAN-022 diff_files_window）

`ws_root / tree / read_text / read_text_range / file_size / write_text /
exists / env_str / regex_replace / search_files / diff_files /
diff_files_window / diff_dirs /
sync_copy / sync_delete / diff_buffers`——路由前缀 /api，GET 走 query、
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

## 文件 diff 端点（PLAN-011 SD-02，M3-01；**引擎时代注记=PLAN-016**）

- **`diff_files(path_a, path_b, ctx) str`**（GET `/api/diff_files`）：
  返回 JSON `{hunks:[{a1,a2,b1,b2}],rows:[{lo,ro,ln,rn,lk,rk,lpre,
  lmid,lpost,rpre,rmid,rpost}],adds,dels,truncated,degraded,err}`——
  hunk 区间 0 基半开；rows.lo/ro 1 基缺席侧 0；三段标记=配对行公共
  前后缀裁剪；CR 容忍（
≡
）；`ctx<=0` 兜底 3。
  **引擎时代（PLAN-016 替换缝兑现）**：`fsys.diff_files_json` 实现
  体=native `diff_files`（9915）裸名直调**纯转发**——PLAN-011 过渡
  朴素分层实现体与上限门三门（1MB/10k/DP-200 降级）退役，超限文件
  正常出结果、degraded 恒 false、「等待内核引擎」err 文案族退役；
  上限门节重写与 rows 面缺陷态（D-1——上游修复前 golden 保持过渡
  时代）见 modules/diff-view.md 引擎时代节（SD-01 主册）。
  **rows 预计算归 back 的理由**（历史口径，机制不变）：VM view 不能
  调函数（Plan 402）——front 拿到即渲染。

## 文件 diff 窗口端点（PLAN-022 SD-03，M4-05，第 16 端点）

- **`diff_files_window(path_a, path_b, ctx, rows_offset, rows_limit)
  str`**（GET `/api/diff_files_window`——五参全必填）：PLAN-716 组C
  9921 窗口投影消费[上游 r3 T-14 改签——9920 与 PLAN-095 ui.focus
  撞号定谳]（`fsys.diff_files_window_json` 五参裸名直调纯
  转发）。envelope 窗口形=hunks/adds/dels 恒**全量**+`rows_total`
  （全量行计数——分页/滚动条真源）+`truncated` 激活（头部 offset>0
  或尾部省略任一即置位；9915 旧端点恒 false 不变）+rows=窗口物化段
  [offset..offset+limit]。
- **独立端点=双轨约束的等价承载**（T-00③ 勘定）：VM HTTP 服务缺参
  400+merged 轨按位装配——同端点「可选 query 参数」不可表达，窗口
  走新端点（上游窗口端点 HTTP 串形同构）。**「缺席=全量」语义由端点
  二分承载**：不携窗口参数的消费面（016 front 全量消费）走旧
  `/api/diff_files`（9915 三参——签名与输出逐字节不变，frozen③）。
- **边界形**（上游 SD-C 契约）：offset ≥ rows_total → rows:[]+
  truncated=true（total>0）；limit 0 → 空+truncated=true；跨 hunk
  任意切片=全量 rows[offset..offset+limit] 逐行等价（探针
  tests/probe_diffwin.py --back 形 8/8 PASS 在档——VM 轨窗口调用=
  供⑧ 上游缺口〔codegen 裸名臂缺失〕，判据走 a2r back 形）。
- **判定消费位**=bench diff_100mb 窗口档（limit=600 对齐 front 渲染
  cap——「出结果」口径=全量 hunks/counts/rows_total+首窗 rows，armed
  PASS 784.8ms 在档 budgets validity）；front 惰性拉行=后续件
  （本端点 v1 消费者仅 bench/探针）。

## 目录 diff 与同步端点（PLAN-012 SD-02，M3-02；**引擎时代注记=
PLAN-016**）

- **`diff_dirs(path_a, path_b) str`**（GET `/api/diff_dirs`）：
  返回 JSON `{entries:[{rel,status,size_a,size_b,is_dir,note}],
  counts:{same,added,deleted,modified,binary},truncated,err}`——左=
  旧（deleted=只在左）右=新（added=只在右，BC 同款）；分类序=存在性
  →kind 冲突→二进制启发式（size>0 且 read_text==""，≤2MB 全文域，
  任一侧命中=binary）→尺寸差→≤2MB 全等→>2MB 同尺寸=same+note=
  uncompared（未比对注记）。条目上限 **5000**（truncated 注记，
  counts 与 entries 同域）；skip-list=Explorer/find 同语义；根缺失→
  err 不静默。
  **引擎时代（PLAN-016 替换缝兑现）**：`fsys.diff_dirs_json` 实现
  体=native `diff_dirs`（9917）裸名直调纯转发——过渡长度桶对齐+
  桶积 700k 护栏+「对齐超限」err 形退役（对齐在 Rust 侧，同长巨桶
  目录正常出结果）；五态分类/注记/cap 5000 语义零漂移（对账实证）；
  条目序=引擎每目录排序定序（断言面序不敏感）。
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

## diff_buffers 端点（PLAN-016 SD-02，M3-04 缓冲区比较 v1，第 15 端点）

- **`diff_buffers(key_a, key_b) str`**（GET `/api/diff_buffers`）：双
  已开编辑器快照对打——`fsys.diff_buffers_json` → native
  `diff_snapshots`（9916）裸名直调，**buffer registry 直读，零全文
  VM 往返**（PLAN-011 边界注记「零全文 tab 铁律正解」落位）。返回
  净形 envelope `{hunks:[{a1,a2,b1,b2}],rows:[],adds,dels,truncated:
  false,degraded:false,err}`（rows=文件面渲染投影，缓冲区面供 hunk
  导航）；缺键 err 形「编辑器不存在: …」（值不 raise）。键语义=
  tab.key（code_editor 族同形；registry storage_key 前缀 normalize
  上游对齐——T-00 探针 merged 臂实证）。front 消费面（面板/跳转/
  旁路）见 modules/diff-view.md 缓冲区比较节（SD-01 主册）。
