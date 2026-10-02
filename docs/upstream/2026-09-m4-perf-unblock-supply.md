# auto-edit → auto-lang 上游供料包：M4 性能解阻（2026-09-29）

> 来源：PLAN-018（M4-01 性能预算门开篇——M1「供料先行+本仓并行」
> 开篇模式复用，战略补注三(c)；路线图 §6 M4「速度王座与发布」四产出
> 全部门控于上游解阻或用户裁定，本包=解阻件归口）。
> 战略依据 `docs/strategy/002-north-star-v2.md`：§2.1（性能预算表
> 「预算未达标不发布」M4 生效）/§4.2（内核路线 tree-sitter 化）/
> §5（测量模式阶梯）/§6（M4 关键产出）。
> 证据基：auto-edit main@f4e34c1（worktree plan-018-dev 执行）；auto-lang
> master@5bb3f53be（组 worktree 钉版，工具链 v0.4.2-2205-g5bb3f53be）。
> 勘定报告：auto-edit `specs/auto-edit/tests/evidence-p018-survey.md`
> （2026-09-29 实勘——本包 §1 三类缺口的逐行证据在彼）。
> 上游实勘（2026-09-29 @5bb3f53be）：ui_gen/rust.rs
> `vm_builtin_host_call` 单源表 19 内建 18 已映射（code_editor_edit
> L9716 实锚）、trans/rust.rs `File.read_text_range` 臂在（L6596，
> PLAN-687）；`a2r 探针`（auto build -r rust）exit 3——生成物三类
> 缺口见 §1。语法面 syntect 5/two-face 0.4（code-editor feature，
> Cargo.toml:69/255-257）、零 tree-sitter。plan046/047（memo/keyed
> 渲染域+依赖录制）在途——与本包无路径冲突（供④ 渲染性能域协同
> 注记见 §4）。

## 1. a2r 生成缺口残余清偿（L2 主形态解阻——三子件）

- **诉求**：`auto build -r rust` 生成物零占位零裸调（exit 0 机读
  判据）。三类：
  - **G-C `code_editor_delta` ui_gen 臂**（唯一名字解析错 E0425，
    生成物 3 裸调用点）：`vm_builtin_host_call` 单源表增
    `"code_editor_delta"` 臂，镜像 `code_editor_edit` 臂同款直调
    形态 `auto_lang::ui::code_editor::code_editor_delta(&({a0}))`
    （返回 String——VM shim native.rs:709 同源语义：destructive
    read，Plan 673 §4.2；未注册键错误形同源）。
  - **G-B try/catch 块 trans 臂**（生成物 4 处 `/* unhandled
    stmt */`）：`.at` try/catch 映射 Rust 形态（异常兜底走 catch
    块）。实例=会话恢复链 try（editor_store.at:499——PLAN-010）/
    file_size 装载探测 try（:897——PLAN-013）/badge probe try ×2
    （PLAN-017）。
  - **G-A envelope 成员访问投影**（生成物 17 行 `/* expr */`）：
    `json.to_value` 结果的成员访问 `v.field ?? default` 臂
    （serde_json::Value 字段读取+缺省回退）。实例=diff envelope
    全族 `v.err ?? ""`/`v.hunks ?? []`/`r.lo ?? 0`/`h.a1 ?? 0`
    （011/015/016/017 diff 视图面）。
- **动机**：L2 主形态（a2r release 直拉——唯一预算效力形态，战略
  §5）自 PLAN-007 装载链引入起 blocked（perf README 在册）；上游
  已分批清偿大半（PLAN-687 read_text_range trans 臂/code_editor_edit
  ui_gen 臂等 18/19 内建），残余三类为全预算行正式判定的最后一公里：
  steady_start/warm_start/open_100mb/open_1gb/idle_mem 的 L2 断言化、
  diff_100mb 的 L2 硬门禁收口（现为 stage_diff server 侧记账形态）
  全部以 L2 链打通为前提。「预算未达标不发布」（M4 生效）需要可判。
- **期望形态**：三类清偿后 `auto build -r rust` exit 0；生成物
  grep 零 `/* expr */`/`/* unhandled stmt */`/裸 `code_editor_delta`。
  语义同源纪律：G-C 直调 core 实现（不绕 VM shim）；G-A/G-B 与
  VM 轨语义逐形对拍（envelope 缺省=?? 右值；try 异常=catch 块承接）。
- **验收形态建议**：上游单测（三类各构造用例：try 成功/异常两臂、
  envelope 嵌套成员+缺省、delta 未注册键错误形）；下游验收=auto-edit
  `perf.py a2r` exit 0 + L2 锚点补跑（bench `--mode l2` 全链）——
  装载链（G-B×G-C）与 diff 视图面（G-A）两域矩阵回归由下游承担。

## 2. 内核帧时间戳插桩（type_latency/scroll_fps 测量解锁）

- **诉求**：内核提供帧生命周期观测通道（最小面）：帧开始/呈现完成
  时间戳可从 .at 层读到（BENCH 标记族同款 stdout 形态或 .at 可调
  只读内建），或等价的事件订阅点。
- **动机**：战略 §2.1 两行测量面缺通道（PLAN-005 T-03 勘无——.at
  层无帧时间戳观测通道，框架合成生命周期仅 Init/Tick/CloseRequest
  三者，"rendered" 标记仅存在于 MCP 快照面）：type_latency（键入到
  上屏 ≤1 帧）与 scroll_fps（满刷新率）无法测量；steady_start 首帧
  段分解（现=spawn→ws_loaded 三段，首帧段缺席）同需此件。
- **期望形态**：观测零行为差异（未订阅/未标记时无额外开销——
  PLAN-005 AUTO_BENCH 门控纪律同款）；时间源单调、可换算毫秒；
  .at 侧可达（VM 与 a2r 两轨同源——G-A/G-B 清偿后 a2r 轨可达性
  同步成立）。
- **验收形态建议**：上游探针（标记到达序+开销测量）；下游
  bench type_latency/scroll_fps 档建立+budgets 两行断言化（供②
  排队注记位现挂 m4-perf-unblock-supply）。

## 3. 大文件实例 UI 硬卡死回归清偿（T17 blocked 族）

- **诉求**：清偿 2046→83c4621b5 窗引入的大文件实例 UI 硬卡死回归
  （m1-supply §17 在册：二分边界+消费面全摘实证非 701/非下游面）。
  **2026-09-29 现势更新（PLAN-018 执行期）**：下游全矩阵单跑
  （v0.4.2-2205 release 工具链）T17.2/17.3/17.8 **三检查全绿**
  （136/1，唯一败=T17.4 轮换 flake 在录成员）——**疑似已解阻**
  （归因候选=上游 plan046/047 渲染域窗/release 工具链形态；单跑
  不定案）。本件定性改「确认复核件」：上游确认清偿 commit（或
  勘定回归已消）+下游多跑复核持续绿后本件核销；若复现则原诉求
  恢复。
- **2026-10-01 复试更新（PLAN-022 T-06——多跑 ×3 执行，销账未达）**：
  工具链 v0.4.2-2474-g95dcfb55b（含 716+719/720）。**处方 part-1
  已落实**=主实例 MCP 端口高带钉位（desktop_mcp.py 主实例
  AUTOUI_MCP_PORT 钉位臂——924x TOCTOU 竞态带绕开，三跑主实例
  3/3 boot 成功[P716-D1 六启动三败同点位清零]）。**×3 谱**：
  93 PASS/**0 FAIL**（run1 30/0 深 T9、run2 22/0 深 T6、run3 41/0
  深 T9+T10 spawn），**T17 不可达**——app 进程中途净退 ×2
  （"vm interpreter returned ok=true"——动作相关：T9 关 tab 循环/
  T6 菜单+工具栏点击；**空闲对照 420s 存活**〔13 心跳零自退——
  自退定时器排除，退出=驱动动作相关 vnode 漂移误击家族〕）+
  T10 子实例 spawn 失败 ×1。共栖环境=PLAN-721 desktop 会话在途
  （desktop-721i 实例）——P716-D1「共栖负载空闲窗口期」处方前提
  今日不成立。**处置=按 P716-D1 自身分支「复现面持续」**：本件
  维持「确认复核件」挂账（不假销账），矩阵检查面 0 FAIL 为
  正面信号（ wherever ran 全绿——T17.2/17.3/17.8 复验位未达，
  下次空闲窗口期重试；evidence=tests/matrix-p022-run{1,2,3}.txt
  +evidence-p022-t06.md）。
- **动机**：下游矩阵 T17.2/17.3/17.8 三检查 blocked（017 执行谱
  133/4 已知族全中——README PLAN-017 口径节）；大文件交互面（打开
  50MB+ 实例的 UI 响应）=M4 open_100mb「滚动不掉帧」半行的前置面；
  清偿后自动复绿（014 口径原文）。
- **期望形态**：大文件实例打开→交互（滚动/激活切换）不冻结 UI
  线程；卡死族三检查复绿。
- **验收形态建议**：上游最小复现探针（50MB fixture 实例交互序列）；
  下游矩阵 T17 族自动复绿即验收（判绿口径恢复全检查计入）。

## 4. tree-sitter 首批（语法高亮 M4 件——勘定+实施两段式）

- **诉求**：内核语法高亮面 tree-sitter 化首批（常见 20 语言起步）
  ——§4.2 内核路线（学 Zed 三课）。**建议两段式**：先勘定件
  （语言集定界/管线选型[tree-sitter crate 版本与 grammar 分发形]/
  与 syntect 共存策略[迁移期双轨或切换]），实施件另立。
- **动机**：M4 产出「语法高亮首批」；M3 收口注记（overview M3
  第五件）尾行=「剩余语法高亮联动=M4 首批 tree-sitter——供料驱动」。
  现势=code-editor feature 全 syntect 5/two-face 0.4（Cargo.toml
  实勘）、零 tree-sitter 依赖。供①/供③/供② 解阻前不阻塞——
  最大件先勘定后供。
- **期望形态**：增量高亮（编辑路径增量重高亮，非全量重算——
  rope 快照隔离消费形态同 diff 后台任务先例）；大文件模式 big 态
  旁路语义保持（plain 臂不受扰）；体积影响评估（two-face 全语言
  内嵌集退役=installer 预算行联动收益，Q2/Q3 材料注记）。
- **验收形态建议**：上游基准（首批语言集高亮正确性+增量重高亮
  延迟）；下游矩阵语法面回归+bench 大文件装载墙钟不回退（plain
  旁路域不变）。
- **协同注记**：plan046/047（memo/keyed 渲染域+依赖录制）在途——
  高亮重算面与其缓存域正交（高亮=文本域派生，memo=视图域），无
  路径冲突；tree-sitter 增量面若消费 memo 依赖录制通道（047 基建）
  属实施件选型空间，勘定件注记即可。

---

## 5. two-face 语法集子集/lazy 装载 feature 粒度（installer 瘦身第二段——PLAN-019 条件触发）

- **诉求**：code-editor 的 syntect/two-face 高亮面获得**语法集子集或
  lazy 装载 feature 粒度**——common 集起步（类似供④ tree-sitter
  「常见 20 语言」口径），全量集退为 opt-in feature。
- **触发证据（PLAN-019 T-00 构成精测，2026-09-29）**：portable 产物
  39.4MB 基线的 **.rdata 数据节 12.4MB**——two-face 全量语法定义集
  内嵌为主体（`two_face::syntax::extra_no_newlines()` 全量构造实锚
  auto-lang `crates/auto-lang/src/ui/code_editor/core/highlight.rs:135`，
  @5bb3f53be 复核在位）；two-face .text 仅 ~65KB——**重量全在数据节**，
  本仓 profile/feature 通道不可达（终态手段集 29.8MB / 门控组合实测
  16.46MB 距 ≤15MB 门 714KB——installer 行第二段收口的定量依据，
  budgets.json installer 行 validity 同源）。
- **期望形态**：子集 feature（如 `syntax-common`）或运行时按需装载
  （lazy 反序列化）；大文件 big 态 plain 旁路臂语义保持（013 定参
  域不受扰）；与 code-editor feature 的启用关系沿现状（ui-iced 路径
  不回退）。
- **验收形态建议**：尺寸差值（two-face 全量→common 的产物数据节差）+
  矩阵语法面回归（高亮正确性抽查档）+ code_editor 装载链不回退。
- **与供④ 协同（want 生命周期注记）**：供④ tree-sitter 化落地后
  syntect/two-face 整体退役——本 want 的生命周期可能止于供④（子集
  粒度若先行落地，其价值=供④ 交付前的过渡期瘦身；两件不冲突，
  先后由上游排程）。

## 6. 供① 残余两面（PLAN-021 下游复验登记——back 转译器 Try 臂缺口，2026-09-30）

- **登记时点**：2026-09-30，PLAN-021（L2 链解阻兑现件）fresh worktree
  消费复验。证据基=specs/auto-edit/tests/evidence-p021-blocked-survey.md
  （全 forensics 在档）；工具链 v0.4.2-2311-g7fcf913eb（含 710 交付）。
- **诉求**：通用 Rust 转译器（crates/auto-lang/src/trans/rust.rs 语句
  分派路径——auto-man api_gen `transpile_back_module_to_rs` 所用）补
  **语句级 `Stmt::Try` 臂**，镜像 710 G-B 臂形（ui_gen/rust.rs 已有：
  catch_unwind(AssertUnwindSafe)/Ok 丢弃/Err 进 catch/catch(e) 绑定=
  panic_message 载荷）。单臂落点两面全解：
  - **面一（back crate）**：`fsys.at:208` try（PLAN-012 find-in-files
    读兜底，空 catch 体+for{if break} 体）现判 `unsupported statement:
    Try`→fsys.rs 整模块跳过（a2r 日志 ⚠ 行在档）→api_impl.rs:3
    `use crate::fsys` 悬空→**back member E0432**（15 处 fsys:: 引用）。
  - **面二（front route-A）**：`merged_route_a_impl`（auto-man/src/
    rust_ui.rs:903）伴生转译链 `.ok()?`——fsys.at 失败→整体 None→
    front api 客户端族（env_str/read_text/exists/file_size/tree/
    ws_root/write_text/read_text_range）回退**恒空桩**（D-7 收口形；
    API_DATA 只写无读+无 HTTP 客户端=死端）→AUTO_BENCH/AUTO_OPEN_PATH
    恒空、会话恢复/工作区/打开链功能死亡——**L2 直拉形态全预算行
    不可测**。
- **动机**：L2 主形态消费（本件主判定面）两面全阻；生成码首跑收据
  =进程/渲染/MCP 面健康+零 panic+编译零占位（front G-A/G-C 面成立）
  ——缺口精确限定在「back 模块转译通路缺 Try 语句臂」一点。
- **验收形态建议**：同供① 三重判据+本件复验位——①`auto build -r
  rust` exit 0 且 a2r 日志零「transpile failed (module skipped)」
  警告行；②**fresh workspace**（regen 前清 rust-workspace）
  `cargo check --workspace` 过；③front 生成物含 route-A 伴生嵌入
  （env_str 实体非 D-7 桩形）；④下游 L2 判定谱补跑（本件 §8 已备
  判据面 zero 重设计——bench --l2 三档+smoke_gen 三域）。
- **判据盲区增补（710 corpus 复盘）**：710 实机判据「cargo check 过」
  系 tmp 拷贝**携带陈旧 rust-workspace**（旧代 fsys.rs 与旧 api_impl
  自洽）掩蔽缺模块洞+front 桩化本就编译绿——判定集建议增：①skip
  警告行 grep；②fresh-copy 卫生（regen 前清生成区或文件清单 diff）；
  ③api 客户端桩形检测（`String::new()` 恒返形 grep）。
- **量级评估**：单转译器臂（先例形态在库可镜像）+判据三行——710
  D-4..D-8 快速修订件同档；建议与 PLAN-714（供④ 勘定）并档排程。

## 7. a2r 形态 code_editor 注册断链（PLAN-021 解阻后复验新发现，2026-09-30）

> §6 两面已经 PLAN-714 r2/r3 清偿（下游 fresh regen 复验：零 skip 警告+
> back fsys.rs 在位+front route-A 实体形+workspace check 绿——AC-R2-4
> 解阻确认收到）。本节=r3 解阻后下游 L2 判定谱补跑暴露的**残余缺陷**。

- **现象**：fresh a2r release exe（工具链 v0.4.2-2366-gacf653d3f）装载
  链死——store 装载探测门 `code_editor_edit(load_key,0,0,"")` 永 false
  （stderr 刷 `code_editor_edit: no editor registered for key
  "__code_editor_tab-N"`）→RunPendingLoad 永递延→bench_open_start
  永不达（auto-edit warm/open 档 L2 化首跑实录）。
- **对照三连**：①VM 轨同工具链同 .at `run -r vm`——装载链正常
  （bench_open_done 触发）；②旧 a2r 构建（019 代产物，ui=2205-crate
  构建）正常（probe_surface open 38.2ms+标记对在档）；③新旧生成物
  editor 视图构造**逐字节一致**（`View::code_editor("editor")`——无
  key 绑定参数，buffer 键=运行时推导）→缺口在 **ui 运行时/widget
  注册面**（.at `code_editor (key: t.key)` 的动态 key 属性在 a2r 视图
  构建路径未达注册——注册键与 store 查找键「__code_editor_tab-N」
  脱节）。
- **回归窗口**：ui 构建 2205→2366（嫌疑面：710 ui_gen 774 行面/
  fix-ui-tier WidgetRegistry 增量注册改造[c80887ab7]/r3 内建分发器
  三处+借位 clone 窄门[29563c588]）——上游二分定谳。
- **影响**：下游 open_100mb/warm_start 两预算行 L2 直拉形态不可测
  （steady_start/idle_mem/diff_100mb[back 面]不受累——已出实数）；
  装载链 E2E/编辑回路冒烟面 blocked。
- **验收形态建议**：下游复验位=auto-edit `bench open --l2` 标记对
  达成（bench_open_start/done）+warm 20tab 恢复链 active 装载完成；
  上游探针=a2r 轨 code_editor 注册键 dump（编辑器实例化后 registry
  键集 vs store 查找键对照）。
- **判定集缺口注记（714 r3 AC-R2-4 复盘）**：r3 下游确认=编译级
  三重判据（exit 0/check/桩形）——**运行时装载 E2E 不在其集**，建议
  census 判定增第④行：fresh a2r exe 装载标记对 E2E（AUTO_OPEN_PATH
  小文件→start/done 标记对）。

## 8. PLAN-716 消费面双缺口（供⑧/供⑨——PLAN-022 下游首跑实证，2026-10-01）

> 716 三组交付（ec45f911c，2026-09-30 delivered）的下游消费首跑暴露
> 两处交付面缺口——**「实机帧序 live-fire 归下游 bench 档」（SD-B 供②
> 验收分工原文）的下游首跑即触供⑨**；供⑧=组C 消费首跑触面。证据链
> 全在下游实录（工具链 v0.4.2-2474-g95dcfb55b=组树 debug 构建@95dcfb55b
> ——含 716 交付锚 ec45f911c）。

### 供⑧：9920 `auto.diff_files_window` VM codegen 裸名臂缺失

- **现象**：下游 api.at 第 16 端点（`diff_files_window` 五参转发
  fsys 裸名直调）——VM server 形态（`run --server vm`）调用 **HTTP
  线程挂死**（请求不达 handler、无 500、curl 悬挂；同实例 9915 旧
  端点正常 200/10ms）。
- **根因面**：五面注册缺一——catalog+shim（native.rs:901/917 双 cfg
  臂在册）+a2r trans 裸名臂（rust.rs:5107 在册）+ui_gen 直调臂
  （rust.rs:10487 在册）在位，唯 **vm/codegen.rs intrinsics 裸名表**
  漏登记（:559-561 `diff_files`/`diff_snapshots`/`diff_dirs` 三面
  在册、`diff_files_window` 缺席）——裸名无本地符号亦无 intrinsic
  绑定→VM 轨解析挂死。a2r 轨不受累（trans/ui_gen 臂覆盖——下游
  L2 判定面 PASS 实证：窗口形 median 784.8ms）。
- **验收形态建议**：codegen.rs intrinsics 补
  `("diff_files_window", NATIVE_DIFF_FILES_WINDOW)` 一行+下游复验=
  `probe_diffwin.py`（缺省 VM 形）8/8 PASS[VM 轨窗口形断言解封]；
  回执后下游 L0 形 diff 档可切窗（当前 L0 维持全量旧径零扰动）。
- **清偿回执（2026-10-01，PLAN-716 r3 T-14 delivered@9a71a5212 谱）**：
  实勘升级=根因双重（intrinsics 漏登记+**9920 与 PLAN-095 ui.focus
  撞号**〔shim 表注册序后者覆盖→VM 轨窗口调用恒派 ui_focus 静默
  no-op〕）→窗口件改签 **9921**+intrinsics 补臂（守护探针
  native_catalog_ids_and_names_unique 随行）。下游回执=
  `probe_diffwin.py` 缺省 VM 形 **8/8 PASS**（2026-10-01，工具链
  v0.4.2-2533-g9a71a5212）+--back 形 8/8 维持双绿；auto-edit 侧
  9920→9921 引用全链对齐。

### 供⑨：9918/9919 帧通道 .at 消费面双缺口

- **现象①（VM 轨 i64→int 桥退化）**：shim 层真值在档（进程内同址
  单调读 0→1→…→1435→1451 实测〔FB-DBG 临时插桩，已还原〕），但
  .at 侧三面全断——`var fb int = frame.begin_ms()` 落 **0**；
  `frame.begin_ms().str()`→**None**〔下游 Tick 处理器 TypeError
  "unsupported operand for +: 'str' and 'NoneType'" 实录〕；
  `json.from_value({b: frame.begin_ms()})`→**0**〔api 探针实测〕。
  **time 族 now_ms 返 0 同根因**（PLAN-005 T-03 登记「VM 轨 time 族
  内建未接线」——本件实证其根因面=i64 native 返回→.at int 域桥）。
- **现象②（a2r ui_gen handler 臂）**：front 探针臂预埋尝试（store
  handler 内 `frame.begin_ms()` 采样）→ **regen 编译失败
  E0425 cannot find value `frame`**〔ui_gen/rust.rs 直调臂不路由
  handler 体二段名——模块 fn 体 trans 臂有映射（:5107 同族），
  handler 臂缺席〕→下游探针臂撤除（front 回零改动）。
- **上游探针盲区注记**：plan716_supply_probes
  `frame_timestamps_vm_readback` 驻 Rust i64 lane（call_i64 直读——
  源码自注「epoch 系全宽值才需字符串出口——701 注记口径」，Int lane
  语义自觉规避 .at 面）——.at 消费面属测试盲区非回归。
- **验收形态建议**：①stdlib/shim 出口形修复（`-> int` 判型重勘或
  701 全宽值字符串出口先例的字符串变体——上游定形）+VM 轨探针增
  .at 侧赋值/str 断言；②ui_gen handler 臂补 frame 二段名路由
  （code_editor_delta 直调纪律同款）+下游复验=front 探针臂重埋
  regen exit 0+帧值流经面。清偿后下游 T-03 帧两行判定面即活
  （协议在档：type_latency=帧内 P95≤1 帧/scroll_fps=distinct
  present 计数≥面板率×0.9——budgets 两行 blocked 证据链行）。
- **清偿回执（2026-10-01，716 r3 T-15/T-16 delivered）**：①出口形=
  int lane 统一（stdlib `-> int`+shim push_i32+catalog Int；值域
  毫秒 saturating<2^31≈24.8 天；SD-B §3b 时源坐标勘定修正
  〔process_start=首触定格非进程起点〕）；②handler 体二段名路由
  补臂（ui_gen 直调+trans Dot-path 双轨）。下游回执=front 探针臂
  重埋后 VM 轨值流贯通〔fprobe_begin 4535/present 3561 真值+首帧
  帧值 33ms 实录〕+**a2r regen exit 0**〔23s，含探针臂——i64 字段
  适配形，见供⑬〕。**供⑬（本轮下游复验新发现）**：a2r trans 臂
  发射 Rust 原生 `frame_begin_ms(): i64` 直赋 .at int（i32）字段
  →**E0308 mismatched types**〔a2r-20261001-225955.log 实录——
  T-16 探针=grep 发射形未过编译赋值面〕；下游适配=探针字段
  `i64` 承接（VM 轨 int 源隐式加宽两轨验证绿）；上游解形建议=
  trans 臂发射 `as i32` 收窄或 Rust 面 frame fn 改 i32 返回
  〔值域毫秒 saturating 与 SD-B §3b 一致〕。

### 供⑪：highlight-treesitter+sql 的 cc 版本夹缝（PLAN-022 T-05 首建实证）

- **现象**：ts-on 形构建（生成 ws——workspace auto-lang dep 行
  `features=["highlight-treesitter"]` 注入）→ **cargo 解析失败**
  `failed to select a version for cc`：tree-sitter-sequel 0.3.2
  （sql 登记位——716 组A T-04）钉 `cc ~1.0.90`〔≥1.0.90 <1.1〕vs
  新纪元 blake3 1.8.7（regen 时现势解析）钉 `cc ^1.1.12`——同 major
  单版本选一→空交集〔首建败实录 release-20261001-160555.log〕。
- **根因**：依赖钉版脆弱性（sequel 的 `~` 紧钉 vs 对齐族 cc 需求
  随 registry 演进上移）——上游 716 执行期 lock 处于兼容纪元
  （实证推测：其 lock 的 blake3/cc 组合未过 1.1 缝），regen 现势
  解析即触。
- **下游回避（已在案）**：ts-on 构建流程锁定 `blake3 --precise
  1.5.5`（兼容纪元降钉——cc 1.2.67 双满足，cargo check 绿 1m06s
  实证；build_portable stage_ts_patch 内建幂等钉位）。
- **验收形态建议**：上游 Cargo.toml 面解钉（sequel 升级/换源或
  blake3 需求面放宽）→ 下游撤回避钉复验 `--ts on` 构建绿。
- **清偿回执（2026-10-01，716 r3 T-17 零 diff）**：registry 演进
  自然解钉——tree-sitter-sequel 0.3.2→**0.3.11**〔cc ~1.0.90→
  ~1.2.1〕与 blake3 1.8.7 交集非空。下游**撤钉回执完成**：
  build_portable blake3 1.5.5 回避钉移除+fresh `cargo update`
  （blake3 1.8.7/sequel 0.3.11/cc 1.2.67）+`cargo check -p
  auto-edit` 绿〔52.7s 含 feature〕。

### 供⑫：a2r trans print 拼接形缺口（PLAN-022 复工期新发现，2026-10-01）

- **现象**：.at `print("前缀" + int值.str())`（帧探针首帧标记行）
  → a2r 发射 `println!(format!("{}{}", …))`——**println! 首参须
  字符串字面量→编译错误**〔a2r-20261001-225955.log
  "format argument must be a string literal" 实录，多处〕。
- **根因面**：trans print 臂对拼接实参发射 format! 内嵌形——历史
  无事因 print() 消费面=bench 标记族全常量（front 消息面走
  console_log 非此臂）。
- **下游适配**：首帧标记行撤除（帧值经 MCP 字段读回，等价承载）。
- **验收形态建议**：print 臂拼接实参发射 `println!("{}", format!(…))`
  或拆 print! 链；下游回执=探针标记行重埋 regen exit 0。

### 语法高亮联动 want 登记（M3 尾巴处置——本件 §1 G-5 定案）

- **want**：diff 视图行级/文本段语法着色端点——`highlight_segments`
  （716 组A 交付的 ts/syntect 双轨高亮管线入口）的 .at 可达暴露形。
  **起草期否定面实证**：native_catalog/ui_gen/trans 三面 grep 零命中
  ——highlight_segments 无 VM native/a2r 臂=下游不可消费（语法联动
  非本件消费面，want 登记不硬做）。
- **期望形**：native 暴露（如 `auto.highlight_segments(text, lang)
  → str`（JSON 段元组面））+ui_gen 直调臂——diff 视图 12 字段 rows
  的 ln/rn 行级着色消费（diff-view.md 后续件）。
- **M3 尾巴注记维持**：「文件 diff 完全家」尾项=供料驱动（战略
  §2.3 口径）——端点交付后另立消费件。

## 9. RQHost 期 tree-sitter 语法「插件化」want（供⑭——PLAN-023 期用户方向裁定，2026-10-02）

- **裁定**：用户 2026-10-02（PLAN-023 重基线追询）——RQHost 渲染
  拓扑落地后，tree-sitter 语法改**「插件」按需下载使用**形态；
  **现行 ts-off/ts-on 双形态维持不变**（现状无碍——用户原话
  「现在ts-off或on问题都不大」），触发前零动作。
- **背景**：现行 21 语言全量静态捆绑（ts-on 实测 +18.9~21.1MB
  〔019 716 双口径〕）——RQHost 期 ≤20MB exe 门（战略 §2.1 追记
  回收承诺）下全量捆绑不可行；curated 子集设想（§5 two-face 子集
  同类思路）被插件路线**吸收替代**（用户明示取向）。
- **期望形（auto-lang 域基础设施件）**：①语法包 loader——动态库
  加载 tree_sitter Language + 版本钉 + 用户缓存目录（Neovim/
  Helix 同型；上游 21 个 tree-sitter-* crate 的可插拔重组）；
  ②**供应链安全面设计先行**（原生代码运行时下载=信任边界从构建
  期移到包源——发布签名+镜像源+哈希校验，缺一不上线）；③离线
  兜底=syntect 缩减集维持缺省形（ts-off 语义自然延续——包未装/
  离线时零回归）。
- **触发条件**：RQHost 渲染拓扑落地后，与 ≤20MB/≤10MB 严格门
  重估同批（战略 §2.1 追记联动）；实施走 auto-lang 立项。
- **验收形态建议**：插件化后 ts-on 静态形退役或降级开发档；单语
  语法包体积/首载时延在档；离线兜底回归=矩阵语法面全绿。

## 10. 真流式装载 want——文件后援分页 rope（供⑮——PLAN-024 期用户裁定 Q-1，2026-10-02）

- **裁定链**：战略 §2.1 open_1gb 行「可打开（分块/mmap 流式）」vs 现势
  512MB 拒绝位（013 定参——018/021/023 三代实测复证活体）的矛盾成文
  =designs/002；**用户裁定 (b)「登记上游供料，实现完整的标准的文件
  后援分页 rope」（2026-10-02 AskUserQuestion 回执）**。本件=want
  登记（M4 以 ledger-blocked-with-plan 收口）；实施=auto-lang 独立
  立项（装载链重构域，本包非目标）。
- **目标形态（完整标准设计——设计种子，上游立项时勘定细化）**：
  ①**不可变基底（文件后援分页）**——打开=只读句柄+页表
  〔{文件偏移, 长度, 行数} 逐页〕；基底页永不在原地修改（偏移恒真
  的前提）；装载预扫一次顺序读只记行数（廉价，不建结构——「共 X 行」
  /跳转行号免全量调入可答）。②**编辑覆盖层（overlay/journal）**——
  全部键入/删除进覆盖层，读路径=overlay 优先、基底按页调入
  （fault-in）；虚拟长度/行数=overlay 记帐。③**淘汰与内存上界契约**——
  LRU 淘汰，淘汰页退化为 {偏移, 长度} 指针；常驻=可见窗+预取缓冲+
  覆盖层，**RSS 上界目标 10MB 级 @1GB 文档**（契约入验收）。④**异步
  调入+预取**——滚动方向预读；未就绪页占位渲染（滚动同步等磁盘=
  帧超标放大——024 S5 域归因教训在档）；725 帧管线增量更新对分块
  载荷到达友好（顺风面）。⑤**保存语义**——原文件未改区段照抄+覆盖
  层增量写回，临时文件+原子改名（崩溃安全）；外部修改检测策略随形
  定（句柄保持+mtime/大小探测——拒绝位语义同步重估）。⑥**消费方
  契约改造面**——查找（overlay+基底逐页扫描）/撤销（overlay 记帐）/
  diff（按需区间调入）/行号跳转/状态栏（渐进行数）全部长出 overlay
  意识。⑦**大文件态语义保持**——≥50MB big 态绕语法臂维持；**512MB
  拒绝位随本件交付退役**（重估移除或抬升，open_1gb 行届时断言化重测）。
- **验收形态建议**：1GB 装载成功+常驻 ≤上界契约+滚动/编辑不掉帧
  （帧档口径）+保存往返 byte-for-byte；bench open_1gb 档真流式判定
  谱在档（拒绝位退役重测——budgets 行 unlock 指向本节）。
- **量级与排程**：装载链重构域——量级≈供① 三类或更大（designs/002
  §2 成文）；M4 不等待（ledger-blocked-with-plan 收口）；建议与供⑭
  RQHost 期同批排程评估（同为上游基础设施件）。

**优先级建议（auto-edit 视角，PLAN-021 后更新）**：**§6 最先**
（供① 残余两面——L2 主形态单点缺口，单臂两面全解）→ §1 其余复验面
（三类已清偿面随 §6 解阻一并复验）→ §3（交互面 blocked 族清偿）→
§2（两行测量解锁+首帧分解补全）→ §4（最大件，勘定先行两段式）→
§5（installer 第二段，随供④/用户裁定排程——PLAN-019 条件触发件）→
§8（供⑧ 一行臂+供⑨ 双面——PLAN-022 消费首跑实证，T-03 判定面
unblock 位；供⑪ cc 夹缝解钉——ts-on 构建面回归）→ §9（供⑭ RQHost 期
条件触发位——非独立排程项，随渲染拓扑落地同批议）→ §10（供⑮ 文件
后援分页 rope——M4 ledger-blocked-with-plan 收口位，与供⑭ 同批评估
排程）。

**回执方式**：同 M1/diff-engine 两包——各件落地落上游 plan 后，
auto-edit 侧以零改动或最小改动复验解阻（669 先例；供① 回执=
`perf.py a2r` exit 0 + L2 锚点补跑；供③ 回执=矩阵 T17 族复绿），
并在本仓 budgets.json 对应行 unlock/validity 注记更新（§2.1 预算
表 M4 收口路径）。

**回执预告位（供⑮——PLAN-728 承接实施，2026-10-02）**：上游
auto-lang PLAN-728（文件后援分页 rope 实施件，worktree
plan-728-dev）已实施七面内核能力——`Node::Chunk` 页描述符+预扫页表
（打开即答行数/摘要，零驻留）、LRU 页缓存（6MB 预算+≤12MB@1GB 结构
计量契约）、异步预取（±16 页保温）、合并保存（temp+原子改名+外部修
改拒绝+byte-for-byte）、`Rope`/`RopeSnapshot` API 零破坏（签名钉在
案）、装载链 50MB 阈值分臂（`code_editor_load_file` 替换全量读）。
契约册=auto-lang `docs/specs/auto-lang/ui/design/paged-rope.md`
（SD-01）。**下游消费件待立**（669 模式）：①512MB 拒绝位处置
（editor_store.at:946——移除 vs 抬升两案在 SD-01 回执节，本仓裁定）；
②open_1gb budgets 行 unlock 断言化重测；③适配件面（`code_editor_
text` 全量读出改走 doc_snapshot/分段读；S2 视口物化窗口滚动/窗口外
打字/fold 面三件与本件头窗口（2MB）协同——673 延后裁定在案）；
④1GB E2E 矩阵（装载/编辑/保存/内存实测谱：auto-lang 侧基准
`docs/reports/p728-bench.jsonl` 已含四线谱先行）。回执行文按「回执
方式」节惯例：零改动/最小改动复验解阻后在本节追加清偿回执行。

**消费回执（供⑮——PLAN-025 兑现，2026-10-02）**：669 模式闭环，
供⑮ 全弧终结——want 登记〔本件 §10，024 期用户裁定 (b)〕→ 内核
实施〔auto-lang PLAN-728 delivered@69059dfaa：七面能力+阈值 50MB
定案+基准谱 1GB 装载 4.0s/即答 0.16ms/结构 3.03MB/RSS 17MB/保存
657ms〕→ 下游消费〔PLAN-025：门退役+1GB E2E+budgets 断言化〕
三段链成文。分项：

- **①512MB 拒绝位处置=用户裁 (a) 移除**（AskUserQuestion 回执
  2026-10-02；728 契约册退役回执两案中 (a) 臂——「内核上界契约
  +下游 budgets open_1gb 断言化重测兜底」）：editor_store.at 拒绝
  臂整支退役（拒绝分支/BENCH bench_open_rejected/拒绝 console 行
  /「只读(超大拒绝)」标签族），安全语义由 big 态命令护栏承载
  （ReplaceAll/EolConvert 拦截+save 直写零回退——grep 锚在档）；
  50MB 界=唯一分域线（与内核 PAGED_LOAD_THRESHOLD 对齐注记）。
- **②open_1gb budgets 行 unlock 断言化重测=armed**：「可打开」
  判定口径成文（装载成功 E2E 断言——矩阵 T17.9-12 四链+bench
  stage open 装载锚点族全成；非时间预算；4.0s 谱=记账注记）。
  bench open 档重铸：拒绝位对照档（truncate 探针+rejected 断言）
  退役→真内容装载锚点族（threshold_50mb 恰界/threshold_50mb_1b
  界下 1B 阈界双轨+boundary_513mb+open_1gb）。
- **③适配件面**：`code_editor_text` 全量读出改道/S2 视口物化/
  fold 面三件=673 延后裁定维持（本件零触碰——矩阵大文件链零
  `code_editor_text` 白名单口径不变）。
- **④1GB E2E 矩阵**：T17 组扩容（17.9-17.12 四链冒烟：装载/
  交互活体+帧带/编辑记账/保存 byte-for-byte——全绿谱见 README
  PLAN-025 口径+results JSONL）。**消费反馈两项**（下游实勘回传，
  upstream 余题域）：(a) **查找全文档扫描债确认为高优先**——
  find 下一处在分页 100MB（release 工具链）21s 未决（728 契约册
  「帧域协同注记」已知债务位 800ms@50MB debug 的下游实测放大），
  页级换行索引/行游标缓存=建议上游承接件；(b) **014 期「大文件
  实例 UI 线程硬卡死」在 728 工具链未复现**（装载/点击/应用级键
  全活——T17 交互簇 blocked 集预期自动复绿；m1-supply §17 登记
  形态随本回执更新注记）。MCP 驱动面缺口（编辑器光标键盘/字符
  键不达 code_editor——小文件对照同，普适测试基建限制非产品缺）
  =测试域注记，不在上游域。
