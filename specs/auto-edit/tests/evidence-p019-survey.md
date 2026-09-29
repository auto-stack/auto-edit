# evidence-p019-survey — PLAN-019 T-00 体积勘定决策件

- 日期：2026-09-29；执行仓：worktree `D:/autostack/.wt/edit-019/auto-edit`
  （branch `plan-019-dev`，base main@0698641）。
- 工具链：`auto 0.1.0+v0.4.2-2205-g5bb3f53be` release（组树
  `.wt/edit-019/auto-lang` 构建；**判据前 `auto --version` 核纪律延续**，
  与 018 锚点谱同版）。rustc/cargo 1.98.0（2026-08）。
- 组依赖钉版（018 惯例+本件实证修订）：`auto-down`@3373a5c（detached，
  018 同锚）；`auto-lang` **钉 5bb3f53be**（v2205 同锚，见 §2 漂移归因）。

## ① regen 现势探针（本件新证据——供① 阻塞延续实证）

`auto build -r rust` @worktree（2026-09-29 17:39，v2205-g5bb3f53be）：
**exit 1，133 编译错**（日志入仓
`specs/auto-edit/tests/regen-probe-v2205-20260929.log`）。错谱与 018
§⑤ 三类生成缺口一致（E0061/E0277/E0308/E0425/E0599/E0605）——
**供①（a2r 三类缺口）未清偿，regen 链上游阻塞维持**。本件核心链的
「regen」段在当前工具链+当前 .at 上不可用；构建基面回退「last-good
生成物」（§2）。

## ② 构建基面（regen 阻塞下的 T-00 裁定——复用语义的诚实记账）

- **基面**：主检出（auto-edit@0698641）`specs/auto-edit/rust-workspace/`
  的 last-good 生成物（2026-09-22 PLAN-007 era 生成——**与 37.8MB 旧锚
  同源生成物**；零占位标记实勘=37,851,136B 产物在位可交叉验证）。
  拷贝形态=源文件面（Cargo.toml/Cargo.lock/两 crate src/.cargo，
  11 文件 376KB；target/ 不拷）。
- **依赖钉版漂移与两处适配补丁**（全部在补丁通道内，build_portable.py
  `DEFAULT_PATCHES` 固化——幂等 find/replace，基面演化时 find 不在场=
  跳过）：
  1. `ui-gpui = ["auto-lang/ui-gpui"]` 声明移除（**feature 面，通道边界
     内**）——Sep-22 基面声明该 feature，auto-lang@5bb3f53be（Sep-28）
     feature 重组后无此名；默认构建路径（ui-iced）不受影响。
  2. `ClientOpts { remote: false }` 一行适配（**source 面——计划
     T-00③ 边界的记录性偏差**）：PLAN-683 后置字段，false=本地渲染，
     单 iced 语义（Q2 中期裁定）不变。
- **依赖代差注记**：基面 Cargo.lock（Sep-22 registry 面）+path 依赖
  auto-lang/a2r-std@5bb3f53be（=018 锚点谱同代——rope[673]/分块读[687]
  在内）。**基线重测值 39,411,200 B（37.6MB）vs 旧锚 37,851,136 B
  （37.8MB）= -243KB 依赖代差**——两数不可直比手段收益；本件全部手段
  收益对照以**本基线**为基（内部一致）。
- **备选路（已探、已弃）**：组依赖树钉 Sep-22 同刻 979ce80c2——verbatim
  基面零适配可编，但 rustc 1.98 编 auto-lang@979ce80c2 本体
  STATUS_STACK_BUFFER_OVERRUN 崩（非 sccache 面——裸 rustc 同崩；该
  修订代在当前 rustc 下不可编）。弃用理由：不可编译 > 两行适配。

## ③ 编译稳定性实录（执行环境面——脚本配方依据）

- 本机编译高峰出现 **rustc 0xc0000409（STATUS_STACK_BUFFER_OVERRUN）
  随机崩 + 提交内存耗尽**（事件日志旁证：同窗 dwm.exe 连崩 0xc00001ad
  ——机器级负载不稳；崩点随机分布于 auto-lang/windows-0.58/read-fonts
  等大 crate，同一 crate 跨轮可过=非确定性深递归）。
- **实证绿配方**：`RUSTC_WRAPPER=""`（sccache 旁路——去掉一变量）+
  `RUST_MIN_STACK=16777216` + `-j 2` + **瞬态崩限次重试**（增量编译
  每轮推进——有进展性依据，非盲试；基线实证 2 轮内绿）。
  配方固化 build_portable.py（BUILD_ENV/BUILD_JOBS/TRANSIENT_RETRIES）。

## ④ 基线构成占比（cargo-bloat --crates + PE 节表，2026-09-29）

**PE 节表**（真实 release 产物 39,435,776 B 逐字节核）：

| 节 | raw | 占比 | 内容归因 |
|---|---|---|---|
| .text | 25,693,184 | 65.1% | 代码面（下表逐 crate） |
| .rdata | 12,354,560 | 31.3% | 只读数据面——**two-face 语法全量集内嵌主体+字体/静态表/vtable**（数据节，.text 不可见） |
| .pdata | 1,012,224 | 2.6% | x64 EH unwind 信息（panic=abort 手段的收益域） |
| .data/.reloc/头 | ~375,808 | 1.0% | — |

**.text 逐 crate**（cargo-bloat；≥100KB 档全列）：

| crate | .text | 域归属 |
|---|---|---|
| auto_lang | 5.1MiB | 内核运行时（上游） |
| std | 2.4MiB | 工具链 |
| naga+wgpu_core+wgpu_hal+wgpu+ash | ~4.1MiB | **iced wgpu 渲染后端**（auto-lang iced features 声明——上游） |
| image+image_webp+exr+zune_jpeg+tiff+png | ~2.0MiB | 图像编解码（auto-lang image-pipeline——上游） |
| skrifa+harfrust+cosmic_text+swash+rustybuzz+read_fonts+ttf_parser | ~2.4MiB | 字体/文本整形栈（code-editor 面） |
| reqwest+h2+hyper+hyper_util | ~1.5MiB | HTTP 客户端栈（auto-lang 运行时自依赖——**生成码零直用**，workspace 行不可达[feature 统一+auto-lang 自拉]） |
| iced+iced_graphics+iced_widget+iced_winit+iced_tiny_skia+winit+tiny_skia | ~1.5MiB | iced UI 栈 |
| regex_automata+regex_syntax+aho_corasick | ~0.7MiB | 正则（syntect/应用面共用） |
| usvg+resvg+lyon+zeno | ~0.8MiB | SVG/2D 几何（auto-lang svg 臂——上游） |
| syntect | 0.22MiB | 语法引擎本体（**two-face 数据不在 .text**——见 .rdata 行） |
| auto_edit（生成应用本体） | **0.23MiB** | 本仓 .at 面——**占比 0.6%，非体积杠杆** |
| tokio | 0.21MiB | 异步运行时 |
| auto_val | 0.25MiB | 内核值层（上游） |
| 其余 212 crates | ~2.0MiB | 长尾 |

**构成结论**：产物体积≈全部来自 auto-lang 运行时+其依赖网（wgpu 4.1/
image 2.0/字体 2.4/HTTP 1.5/iced 1.5/SVG 0.8 MiB .text+**.rdata
12.4MB 数据面[two-face 全量语法集为已知主项]**）；本仓生成码仅
0.23MiB。**15MB 目标的剩余大头全在上游域**（供④ tree-sitter 退役
syntect/two-face、auto-lang 依赖/feature 瘦身 want、iced wgpu 裁剪
want）——分阶段语义的定量支撑。

## ⑤ 手段序表（构成实证后的预估/实测收益排序——T-02 迭代序）

| # | 手段 | 通道 | 预估收益（构成实证修正） | 风险/护栏 | 序 |
|---|---|---|---|---|---|
| 1 | LTO=fat + codegen-units=1 | profile 注入 | 跨 794 包巨网跨 crate 内联+DCE——.text 25.7MB 面预估 -10~20%；strip 并入（MSVC release 已无符号表——**strip 收益预期≈0**，018「无 debug symbols」勘定一致性实证，仅作卫生位保留） | 编译时长↑（fat LTO 链接分钟级）；性能中性偏正（护栏仍测） | **先行（V2）** |
| 2 | panic=abort | profile 注入 | **实测 -7.11MB（V2b 29.84→22.74MB，-23.8%）**——远超预估（.pdata 1.0MB+.text landing pad/personality 全退+LTO 交互） | **Q-1 默认不启用坐实**：catch_unwind 实勘=生成码零处，但 **auto-lang back_proxy.rs 生产用点**（FFI 边界 panic 隔离语义）——启用即破隔离；语义面变化待用户裁定（收益数字在案） | 测量位（不入终态） |
| 3 | opt-level=z | profile 注入 | .text 大头压缩预估 -15~30%（代码密度换性能） | **G-4 护栏门**：产物面锚点回退超容差即弃（M4 速度王座）——V4 测量后裁决 | 护栏裁决位 |
| 4 | tokio back "full"→子集 | deps 行 feature 面 | feature 统一后增量面≈signal/process 专项——预估 ≈0~50KB（近乎零） | 零语义面 | 顺带测量（V2b） |
| 5 | iced wgpu 渲染臂裁剪（naga+wgpu 栈 ~4.1MB .text） | **上游**——auto-lang iced features 自声明（workspace 行 features 只增不减[feature 统一语义]，本仓通道不可达） | 大头 | 上游 want（tiny-skia 单后端可行性） | want 排队注记 |
| 6 | two-face 语法集子集/lazy 装载 | **上游**（code-editor feature 粒度——highlight.rs:135 全量内嵌实锚；数据面在 .rdata 12.4MB 内） | 大头 | 供①/供④ 域（tree-sitter 化后 syntect/two-face 整体退役） | **want 登记（SD-05 条件触发）** |
| 7 | auto-lang 依赖瘦身（image 编解码 2.0/HTTP 1.5/SVG 0.8 MiB .text 等） | **上游**（auto-lang 自依赖 web） | 大头 | 上游承接件 | want 排队注记 |

## ⑥ 手段×{尺寸,锚点}终表（T-02 交付——G-4 护栏对照）

**手段×尺寸**（cargo 链全量重编，瞬态崩重试配方下完成）：

| 变体 | profile/deps 注入 | 产物 B | Δ vs 基线 |
|---|---|---|---|
| V1 基线 | （默认 release——零手段） | 39,411,200 | — |
| V2 | lto=fat + codegen-units=1 + strip | 29,844,480 | **-24.3%** |
| V2b | V2+tokio back full→实需子集 | 29,844,480 | ±0（feature 统一——增量面被 LTO+DCE 全消；保留=manifest 语义收紧） |
| V3 | V2b+panic=abort | 22,737,408 | -42.3%（**门控测量位**） |
| V4 | V2b+opt-level=z | 22,199,296 | -43.7%（**护栏测量位**） |
| V5 | V2b+z+abort | 16,459,264 | -58.2%（**超门仅 714KB=0.7MB**——用户裁定面定量） |
| **终态** | V2b 集（授权面） | **29,844,480** | -24.3%（≤15MB 未达标=分阶段语义兑现） |

**G-4 护栏（终态手段集复跑）**——两轨：

*工具链轨锚点档*（bench.py open/steady/warm @v2205，JSONL 入
tools/bench/results/；对照 018 锚点谱）：

| 预算行 | 018 锚 | 本件复跑 | 判定 |
|---|---|---|---|
| open_100mb ≤1s | median 841.0ms | 844.5ms（谱 825.0-844.5） | ✓ 行内（+0.4%） |
| steady_start 不劣化（±10% 容差） | mean 232.6ms | 230.3ms | ✓（-1.0%） |
| warm 净段 ≤120ms | mean 1.3ms | 1.5ms | ✓ 行内 |
| idle_mem ≤60MB | 空窗 51.4MB | 45.9/51.0MB | ✓ 行内 |

*产物 exe 直拉面*（probe_surface.py，手段敏感面——steady 代理
spawn→ws_loaded/open 100MB 标记包夹/idle mem；**a2r 门旁路=regen
阻塞期记录性通道**[供① 清偿后回归 proxy --mode l2 标准链]）：

| 面 | 终态数字 | 对应预算行 | 判定（记账形态） |
|---|---|---|---|
| steady 代理 | 21.2ms（init 13.6+ws 7.6） | ≤80ms | ✓ 大余量 |
| open 100MB | 38.2ms | ≤1s | ✓ 大余量（a2r 原生化装载） |
| idle mem | 10.2MB | ≤60MB | ✓ 大余量 |

护栏结论：**零「瘦体积肥延迟」信号**——终态手段集下两轨全行绿
（产物面较工具链轨原生优势显著=单 iced 直拉绕开 VM boot 的形态
红利，非手段效应）；基线产物面探针未跑（exe 被变体链覆盖——成本
收益裁定弃，归因注记：LTO fat 类手段业界公论性能中性偏正+两轨
预算行大余量为护栏充分证据）。

**烟测（T-04，AC-05）**：四段全绿（smoke-20260929-193647.jsonl）——
①干净目录单 exe 直跑[BENCH open 链标记对+后端就绪行+进程存活，
open 链 1033.9ms 内完成=含首启] ③单进程[零子进程=无 DLL 侧车宿主]
②零解压残留 ④back fsys 契约链[ws_root+read_text——同产物构建面
back 二进制]。diff HTTP 面注记：diff 引擎路由属工具链 VM server
（矩阵 T15.x 域）——生成 back=fys 契约面[api.rs 实勘]，产物面
diff 抽查不可达，按「产物形态非源码变更」口径归矩阵轨（本件抽查
档不入矩阵计数，承 018 判绿口径）。

**幂等自证（AC-02）**：`--check-idempotent` pass——patch 两遍
manifest 字节等价（frozen ②）；ensure 复用/回退语义+构建瞬态崩
重试配方全链实录于 tools/portable/results/portable-*.jsonl。

## ⑦ Q-1/Q-2 预裁定确认口径

- Q-1 panic=abort：默认不启用维持；收益数字入 ⑤ 表供用户裁定（不追加
  登记——非瓶颈即弃口径）。
- Q-2 steady 容差：±10% 运行方差容差默认维持（018 离散谱先例）。
