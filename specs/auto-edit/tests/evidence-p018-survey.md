# PLAN-018 T-00 M4 勘定报告（evidence-p018-survey）

> 勘定日：2026-09-29。证据基：auto-edit worktree `plan-018-dev`（base
> 38ca5b7 = main f4e34c1 + 簿记）；auto-lang `master@5bb3f53be`（组
> worktree `.wt/edit-018/auto-lang` detached 钉版，工具链
> v0.4.2-2205-g5bb3f53be release 实构）。计划起草基线为 9b5a10e51，
> tip 漂移 12 提交（plan046 T-03..07/plan047 T-01..07/PLAN-705/706
> ——memo 依赖录制+gallery 修复+http handler async，零触碰 a2r 映射
> 面与语法面；本报告全部锚点按 5bb3f53be 现势复核）。

## ① a2r 映射残余定界（供① 证据基）

**结论：残余已收窄至单点——`code_editor_delta` 的 ui_gen 臂**。
计划起草时（9b5a10e51 勘）的「read_text_range/code_editor_delta 缺席」
两处，现势=一处已被上游老供覆盖：

| 内建 | trans/rust.rs（File/fs 面） | ui_gen/rust.rs（vm_builtin_host_call 单源表 L9673） | app 调用点 |
|---|---|---|---|
| `File.read_text_range` | **✓ 臂在**（L6596，PLAN-687 chunked-read envelope——起草基线时已在，非漂移新增） | 不适用（std fs 内建走 trans 面） | fsys.at:35（back 收口）→ editor_store.at:1053 经 back.api 调用 |
| `code_editor_edit` | 不适用（widget 内建） | **✓ 臂在**（L9716，直调 core 同 VM shim 语义） | editor_store.at:881/1062/1158/1368 |
| `code_editor_delta` | 不适用 | **✗ 零命中**（`_ => None` 回退） | editor_store.at:1063/1159（BOM 剥离 drain+装载 drain-弃） |

**app 面全量对照**（specs/auto-edit/src/front/*.at 19 内建 × ui_gen
映射命中数）：copy 2/cursor_col 1/cursor_line 1/cut 2/**delta 0**/edit 1/
find 1/fold_hidden_count 1/fold_toggle 1/load_file 1/paste 1/redo 1/
save 1/select_all 1/selection_len 1/set_cursor 1/set_text 1/text 2/
undo 1——**18/19 已映射，唯一缺口=code_editor_delta**。

**①-b 生成物三类缺口全景**（a2r 探针生成物 main.rs 逐类勘定——供①
残余不止 delta 臂一点，共三类）：

| 类 | 生成物形态 | 处数 | .at 源形态（实例） | 域 |
|---|---|---|---|---|
| G-A envelope 成员访问 | `/* expr */` 语法占位 | 17 行 | `v.err ?? ""`（editor_store.at:1531）/`v.hunks ?? []`（:1609）/`r.lo ?? 0`（:1543）/`h.a1 ?? 0` 族 | diff 视图全族（011/015/016/017 面——DiffCompute/DiffBufJump/DiffBuildIrows/badge 计数） |
| G-B try/catch 块 | `/* unhandled stmt */` | 4 处 | 会话恢复链 try（:499）/file_size 探测 try（:897）/badge probe try ×2 | 装载链+会话链+badge probe |
| G-C code_editor_delta | 裸调用（E0425 唯一名字解析错） | 3 调用点 | `code_editor_delta(key)`（:1063/:1159）+EOL 转换臂 | 装载 drain-弃/BOM 剥离/EOL |

编译错误普查（a2r log 114 错行）：语法错（expr 占位）+**E0425
`code_editor_delta` ×1（唯一 unresolved name）**+级联（E0308 ×94/
E0599/E0277 Display ×12/E0061 ×4/E0605 ×2——占位符类型推断塌方）。
**装载链专项**：file_size 探测 try（G-B）在 RunPendingLoad 头部——
G-B 不清则装载链 a2r 形态同样不可用（fsize 恒 -1→错误形承接，链
逻辑断裂）；G-A 的 file_size envelope 访问同被 try 缺口先吞。

**期望形态**（供① 三子件）：
- G-C：ui_gen `vm_builtin_host_call` 增 `"code_editor_delta"` 臂，
  镜像 edit 臂同款直调形态
  `auto_lang::ui::code_editor::code_editor_delta(&({a0}))`（返回
  String——VM shim native.rs:709 同源语义：destructive read，Plan
  673 §4.2；未注册键错误形同源）；
- G-B：try/catch 块 trans 臂（Rust 侧 catch 形态映射——`.at` 语义
  =异常兜底走 catch 块）；
- G-A：json.to_value 结果的成员访问投影 `v.field ?? default` 臂
  （serde_json::Value 字段读取+缺省——envelope 契约面通用件）。
三子件清偿边界=「生成物零占位零裸调」——`auto build -r rust`
exit 0 为机读判据。

**L2 链现势探针**（auto build -r rust @worktree，工具链
v0.4.2-2205-g5bb3f53be）：见 §⑤ 探针实录——**仍 blocked（exit 3）**，
且失败面不止 delta 单点：生成物三类占位/裸调（见 §①-b 三类缺口）。

## ② BENCH 标记族盘点（供②/T-04/T-05 证据基）

**现役标记全列**（specs/auto-edit/src/front/editor_store.at，
AUTO_BENCH=1 门控 print 行）：

| 标记 | 行位 | 语义 |
|---|---|---|
| `bench_vm_init` | L469 | LoadWorkspace 头段（进程起→逻辑 init 面） |
| `bench_ws_loaded` | L486 | LoadWorkspace workspace 装载尾（**会话恢复链之前**——L488 注记「会话恢复链（尾段——bench 计时标记之后）」） |
| `bench_open_start` | L954 | RunPendingLoad 装载位包夹头（512MB 拒绝分支与 big 置位**之后**、code_editor_load_file 之前——open_ms=纯装载时长） |
| `bench_open_done` | L1025 | 装载位包夹尾 |

**steady_start 分解缺口清单**：现有分解=进程起（host spawn 计时）→
逻辑 init（vm_init）→workspace（ws_loaded）三段；首帧请求段=勘无
通道（框架合成生命周期仅 Init/Tick/CloseRequest——bench README 探针
矩阵在册，供② 解锁件）。**本件补点=0**（既有三段足够 ≤80ms 对表
归因；首帧缺席=供② 排队注记，不硬造）。

**本件新增标记（T-03/T-05 测量面，最小 diff 2 处 3 行）**：
1. `bench_session_restored`——LoadWorkspace 会话恢复链尾（try 块内
   recents 重建后，L557 console_log 后）——warm_start 恢复链墙钟段；
2. `bench_open_rejected`——RunPendingLoad 512MB 超大拒绝分支尾
   （L911-931 块）——拒绝形机读（拒绝在标记包夹之前，现无 stdout
   观测通道；console_log 不落 stdout——print/console 两通道分立
   实勘）。

两补点均 AUTO_BENCH=1 门控 print（PLAN-005 T-04 同款纪律——未设门
分支不进，矩阵零行为差异）。

## ③ open_100mb 可测形态决策（T-03 档形）

- **读点=BENCH 标记包夹**（bench_open_start/done——纯装载时长语义，
  PLAN-007 起即此形态），host 侧计时（app epoch 双录通道=vue 映射
  缺口在册 §17，open_ms 走 host 回退源——如实注记）。粒度 L0 25ms
  轮询——100MB 秒级锚点粒度足够（≤1s 预算行记账形态，非武装判定）。
- **计时卫生**：fixture 生成与计时之间**沉降窗 5s**（016 diff_100mb
  writeback 教训复用——无窗跑 +600ms 失真实证在档）。
- **big 态交互确认**：RunPendingLoad 探测门 fsize≥524288000（50MB）
  → big 置位先于 load_file（L934-947）——100MB 必经 big 态（plain
  旁路臂，懒语法）——**装载墙钟锚点=big 态语义下的数字**，档注记
  同档成文。512MB 拒绝位（>536870912 拒绝装载零 rope 分配，L903）
  在标记包夹之前——拒绝形经补点标记机读。
- **1GB 档位裁定**：1GB>512MB 落同门拒绝——「可打开」现役不可达
  （拒绝位在 1GB 之下，013 Q-3 定参+真分块 IO 注记 upstream §16）；
  本件 1GB 尝试=战略 ledger 态记录（拒绝形实证+门放开后重测位），
  不硬造可打开假象。拒绝位对照=513MB 探针 fixture（拒绝位边界+1B）。
  探针 fixture 用 truncate 形（逻辑尺寸达标、内容零填充——拒绝路径
  仅 file_size 元数据读，零内容消费；门放开后需真内容重造）。
- **档形裁定**：独立 `stage_open`（不并入 bigfile 档——013 bigfile=
  尺寸杠杆对照语义〔49/50/100 mode on/off 代理〕，本档=装载墙钟
  锚点〔100MB 预算行〕，语义不同不混档）。
- **跑谱**：100MB ×5 跑（首跑弃暖机）——离散度随谱注记（016 四跑
  谱先例）。

## ④ Q2/Q3 裁定材料（§10 Q-1 备料）

- **exe 现尺寸**：主检出 rust-workspace/target/release/auto-edit.exe
  =37,851,136 B（37.8MB，2026-09-22 PLAN-007 era build）——a2r
  release 形态真值锚。
- **差距表**：37.8MB → ≤15MB 预算行（installer 行），需 -22.8MB
  （-60%）。体积构成勘定面（后续件实施时精测）：iced+tiny-skia
  渲染栈、syntect+two-face 语法集（two-face 内嵌全语言定义集）、
  cosmic-text、Rust std+panic/fmt 面；release profile 无 debug
  symbols（cargo 默认）。
- **两路径成本注记**：
  - **a2r 原生化瘦身**：依赖审计+feature 裁剪（two-face 全量语言集
    →按需子集；供④ tree-sitter 化后 syntect/two-face 退役面重叠）+
    LTO/opt-level 复核——治本，与 M4 语法高亮件联动，预期收益最大；
    风险=功能面回归（语法集裁剪需矩阵/用例护栏）。
  - **执行打包**：自解压/压缩容器（≤15MB 交付尺寸口径若按「分发
    包」计）——机械成本低、不碰功能面；代价=运行期解压延迟+AV
    误报面+「单 exe 无运行时依赖」预算行语义需裁定（打包壳算依赖
    吗）。
- **winget 加分项口径**：winget 清单要求安装器静默安装+
  卸载注册+版本升级面——两路径均需补（原生化路径=传统安装器壳；
  打包路径=portable 形+清单注记）。Q3 裁定问题清单见计划 §10 Q-1
  （用户件，本件不含实施）。

## ⑤ a2r 现势探针实录（T-00① 裁决性证据）

`perf.py a2r` @worktree（2026-09-29 11:01，工具链
v0.4.2-2205-g5bb3f53be release）：**BLOCKED exit 3**（perf 归因=
「a2r 生成物编译失败——生成器缺口」）。日志
tools/perf/logs/a2r-20260929-110102.log（入仓）；生成物
rust-workspace/auto-edit/src/main.rs 占位全景=§①-b 三类表。首错
`error: expected expression, found ';'` @main.rs:1258（G-A 占位）。
**结论**：L2 链（a2r→release→直拉）维持 blocked-upstream；供①
清偿判据=`auto build -r rust` exit 0；解阻后 L2 锚点补跑=后续件
（本件锚点按 frozen 约束① 走 release 工具链全链记账形态，不冒领）。

## ⑥ 供③/供④ 现势锚（证据基补全）

- **供③ 大文件卡死回归**：017 执行谱 133/4 中 T17.2/17.3/17.8
  三败=大文件实例 UI 硬卡死族（README PLAN-017 口径节在册：上游
  回归 2046→83c4621b5 窗引入，二分边界+消费面全摘实证；清偿后自动
  复绿）；m1-supply §17 登记。本件执行期如跑矩阵抽查，该族失败
  预期在谱（零新失败判据）。
- **供④ tree-sitter**：auto-lang 全 Cargo.toml 零 tree-sitter
  （grep 实证）；语法面=`code-editor` feature（Cargo.toml:69）=
  cosmic-text 0.15+syntect 5+two-face 0.4（L255-257）；§4.2 内核
  路线 tree-sitter 化（学 Zed 三课）；plan046（memo/keyed 渲染域）
  在途（T-03..T-07 已落 master，渲染域施工中——供④ 语言集/管线
  选型与其无路径冲突，冲突面=渲染性能域协同注记）。
