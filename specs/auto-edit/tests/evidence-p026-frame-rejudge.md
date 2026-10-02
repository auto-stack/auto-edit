# evidence-p026 — 帧两行终判谱+S5 子段归因（PLAN-026 T-00/T-01，2026-10-03）

## T-00 重判勘定

- **工具链门**：组三树 edit-026〔auto-edit@plan-026-dev base 08685d6/
  auto-lang@cb2da5fba detached+auto-down@895f8d0 detached〕——release
  组树重建 `cargo build --release -p auto`，`auto --version` =
  **auto 0.1.0+v0.4.2-2640-gcb2da5fba**（clean 无 -dirty；021-025 核
  哈希纪律；731@30bda6831+733@550895b68 祖先链 merge-base --is-ancestor
  双实证）。`bench.py check` 绿（构建 2640 ≥ 1588；检测器红证自检
  PASS；psutil 在位）。
- **731 上游谱带内复验（重判前置——frozen ⑤）**：组树 ladder.py 复跑
  （`--label after-release-p026` + 组树 release 二进制——731 回执
  `ladder.py --label <x> --out <p>` 处方原样），对照
  `ladder-after-release.jsonl`（auto-lang evidence/731 在档）：

  | 线（1mb） | 731 回执 | 026 复验 | 带 |
  |---|---|---|---|
  | type s5 P50 | 0.36ms | 0.37ms | ✓ 带内 |
  | scroll s5 P50 | 0.42ms | 0.35ms | ✓ 带内 |
  | typenl s5 P50 | 0.34ms | 0.33ms | ✓ 带内 |
  | type 泵率 | 1.46/s | 1.95/s | ✓ 同带 |
  | scroll 泵率 | 0.41/s | 0.41/s | ✓ 全等 |
  | typenl 泵率 | 1.69/s | 2.14/s | ✓ 同带 |

  全线带内=**环境噪声排除，重判放行**。复验谱=tests/
  evidence-p026-upstream-reverify.jsonl。复验异常注记：100kb/typenl
  相位 MCP 通道中途拒连（9 次派发败→frames=2/pump 0.02——app 侧疑
  似瞬态退出；1mb 全相位完整带内=门槛基面不受累；022/024「组树冷
  编译首跑无诊断死瞬态」同族观察位）。
- **帧档 frozen 断言（口径零改动）**：`stage_frame` 区域
  （_FRAME_MCP_PORT_BASE→main）f183f53[022 T-03 首判]→08685d6
  **逐字节全等**（diff 实证；023/025 对 bench.py 的改动均在
  installer/open/steady 区域）；驱动协议 autoui_type 直达 textarea+
  换行连发 cursor-follow 原样；面板率 EnumDisplaySettings 读回
  60Hz（budget 16.67ms/threshold 54.0 全谱在录）。

## T-01 终判谱（N=4 全有效，release 工具链 v2640）

| 谱（tools/bench/results/） | type P50/P95 ms | valid/focus | scroll fps | 判定 |
|---|---|---|---|---|
| frame-20261003-003935 | 71 / 158 | 27/OK | 8.41 | FAIL/FAIL |
| frame-20261003-003954 | 78 / 160 | 28/OK | 8.76 | FAIL/FAIL |
| frame-20261003-004012 | 78 / 158 | 27/OK | 8.10 | FAIL/FAIL |
| frame-20261003-004030 | 78 / 156 | 28/OK | 9.53 | FAIL/FAIL |

**判定：两行 FAIL 维持**（type_latency P95 156-160ms > 16.7ms；
scroll_fps 8.1-9.5fps < 54）——frozen 口径如实红，Q-2 默认臂落账
（归因回执+upstream 余题回执；tag 语义降为「重判收口」，十行全绿
未达=发布门不解锁）。

## S5 子段归因（[P725-FRAME] 731 插桩下沉后首度下游可见）

各组树 run 的 appdata 日志（%TEMP%/bench-p022-frame-appdata-*，四跑
119-136 帧/跑）与 024 时代日志（bench-p022-frame-appdata-drc1elov/
3xrf3nem，v2579）同法对照：

- **S5 增量化下游生效实证（024 遗题清偿面）**：024 的段外 ~108ms
  （S5 域 layout/shaping/draw 未插桩）在 026 谱中**消散**——s5 三
  子段全相位 **0.1-0.2ms**（layout ~0.04/shaping ~0.12-0.15/draw
  ~0.17-0.21ms，与上游 731 谱同量级）；024 慢帧归因面（尾部帧
  ×ce_widget_new 同现+滚动帧 ~108ms/帧整形节奏）在 026 **零复现**
  （全谱唯一慢帧=第 0 帧首建 s4_element 91-92ms——024 同款一次形
  ，装载后首帧域=first_present 记账位，非判定域）。
- **快帧域更优**：type 窗 segsum median ~2ms（026 单帧单建）vs
  024 突发形 0.4-0.6ms×突发（b2b 3-4ms 突发串）——731 增量管线
  消除突发重建，**帧工作面全绿**（vs 16.7ms 预算余量 ~8×）。
- **红面真因=帧泵呈现通道（present 交付节奏）**：dirty 帧真呈现
  率仅 ~11%（paired 14-18/帧 119-136；024 突发形 17-24%）——
  `__frame_pump`（711 泵 listen_raw RedrawRequested）消费滞后/合并
  形态在 731 泵治理后变更，fprobe_present 读回=**泵消费时刻**而非
  帧工作完成时刻→bench 帧内口径读到的 P50 71-78/P95 156-160ms
  **=present 字段陈旧度**（驱动节奏 77ms/键+消费合并），非帧构建
  时长。731 对照报告「泵消费率 ≪ 实际呈现率=测量配对面非呈现丢失
  」上游同机理；**下游判定通道语义随之漂移**（022 frozen 口径的
  读回通道在 731 后读数含义改变——通道面事实，非口径变更）。
  scroll 行同域：8.1-9.5fps=呈现交付节奏实测（022 8.0/024 6.7-8.8
  同带）——**三代谱系同带、红面同源**（交付节奏 <54 阈，任一读法
  皆红：真实呈现若随键节奏 77ms≈13fps 仍 <54；泵消费读法 8-9fps
  亦 <54——双读法 FAIL 稳健）。

## 结论与回执（Q-2 默认臂——双态如实）

- **判定终态**：两行 FAIL 维持（frozen 口径零改动——P95/面板×0.9
  原样）；三代谱系（022 首判 110/115ms+8.0fps → 024 重判 95-112ms
  +6.7-8.8fps → 026 终判 156-160ms+8.1-9.5fps）全数在档不删。
- **红面余题换代**：731 清偿了帧工作面（S5 增量化生效实证）；
  余题=**帧泵呈现交付节奏**（__frame_pump 消费滞后/合并——711 泵
  域+731 泵治理交互面）+**判定通道语义适配**（fprobe_present 读回
  语义与 022 帧内口径的匹配性裁定）——**均上游域（auto-lang）**
  ，消费缺陷回执登记 upstream（非本仓调优域）。
- **upstream 回执要点**：①帧工作面清偿确认（下游对照=024 段外
  ~108ms→026 s5 子段 0.1-0.2ms）；②泵呈现交付节奏=下游可观测红
  面（paired ~11%+scroll 8-9.5fps 交付率实测）；③fprobe 判定通道
  在泵治理后读数=消费时刻陈旧度——重判口径若需反映帧工作面，
  需上游提供工作完成时刻通道（s4 后/s5 后时间戳）或裁定消费时刻
  通道的判定语义；④100kb/typenl 相位瞬态退出一次（复验异常注记
  ——观察位）。
- budgets 两行 026 代注记+对比表滚动行三代并陈+tag 语义降为
  「重判收口」（十行全绿未达=发布门不解锁，如实注记）随本谱落账。
