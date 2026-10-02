# evidence-p024 — 帧两行重判谱+分段归因（PLAN-024 T-00/T-01，2026-10-02）

## T-00 重判勘定

- **725 交付谱复核**（auto-lang master b385534d7 含 725[d7e48e8b5]，
  evidence/725/ladder-*.jsonl）：上游阶梯谱改前/改后 segsum P50——
  5KB 11.68→5.30ms、100KB 24.04→5.83ms、1MB 126.76→8.07ms（尺寸
  缩放清零）。725 handoff 预告：「上游谱不含 S5（layout+draw 残差）
  与重 handler 负载——真判定以下游补跑为准；若下游谱仍超界，优先查
  S5 残差（首帧 shaping 债——editor-kernel「现状限制」在册）与
  handler 体成本（下游件域）」。
- **工具链门**：组树 edit-024/auto-lang master b385534d7 release
  重建——`auto --version` = **auto 0.1.0+v0.4.2-2579-gb385534d7**
  （clean 无 -dirty；021-023 核哈希纪律；725 交付在 master 祖先链
  ——git log --grep 725 实证）。`bench.py check` 绿（构建 2579 ≥
  1588；检测器红证自检 PASS；psutil 在位）。
- **协议复核**：判定口径 frozen ① 原样——022 判定谱
  （frame-20261001-230957）头行实证 release 形
  （auto_path=target/release/auto.exe，v2533）；驱动=autoui_type
  直达 textarea+换行连发 cursor-follow；判定=帧内 P95 ≤1 帧
  （16.7ms@60Hz EnumDisplaySettings 读回）/scroll ≥面板×0.9
  （54fps）。
- **NP++ 在位探测**：Program Files/LOCALAPPDATA Programs/PATH/
  注册表 Uninstall 四路全空 → **未装**（G-3 走 pending 注记臂，
  Q-3 默认口径——tag 不等待）。

## T-01 重判谱（N=4 有效+1 无效，release 工具链 v2579）

| 谱（tools/bench/results/） | type P50/P95 ms | valid/focus | scroll fps | 判定 |
|---|---|---|---|---|
| frame-20261002-141456 | 1 / 112 | 23/OK | 8.8 | FAIL/FAIL |
| frame-20261002-141522 | — | 2/**focus_ok=False** | 1.0 | **无效跑弃用**（启动瞬态——驱动通道未贯通，edits 零增；复跑沉降后有效） |
| frame-20261002-141537 | 1 / 95 | 22/OK | 7.5 | FAIL/FAIL |
| frame-20261002-141553 | 4 / 98 | 27/OK | 6.7 | FAIL/FAIL |
| frame-20261002-141631 | 3 / 112 | 25/OK | 7.0 | FAIL/FAIL |

**判定：两行 FAIL 维持**（type_latency P95 95-112ms > 16.7ms；
scroll_fps 6.7-8.8fps < 54——与 022 首基线 110/115ms、8.0fps 对照：
**中位 ~30× 改善[110→1-4ms]，判定行仍红**）。

## 分段归因（[P725-FRAME] stderr 探针——app.log 逐帧）

各组树 run 的 appdata 日志（%TEMP%/bench-p022-frame-appdata-*）：

- **单帧单建成立**：脏帧 builds=1 全体（四跑无一全量重建）——725
  增量管线中位生效实证。
- **快帧**（占绝大多数）：S1 payload 0.0 + S2 vm 0.07-0.10 +
  S3a mcp 0.6-0.7 + S3b build 0.7-1.2 + S4 element 0.4-0.5ms
  ——分段和 ~1.8-2.4ms，帧总 3-5ms（vs 改前 ~110ms）。
  **下游 handler 臂成本排除**（S2/S3 合计 <1ms）。
- **尾部帧**（每跑 1-2 帧，begin→present 95-112ms）：S1-S4 全计
  ~1.8ms 而帧总 ~110ms——**~108ms 为段外耗时=S5 域**（layout/
  shaping/draw，未插桩）。与 `ce_widget_new=1`（编辑器组件重建→
  全量重整形）事件帧同现（run5 上下文行 413-420 实录：
  begin=6885 present=6996 segsum 1.8ms）。
- **滚动段**：帧 begin→begin 节奏 ~108ms/帧（11600→11708→11817
  实录），present=-1 掉泵直落主导（无泵呈现 fall-through），
  distinct present 21-26/3s ≈ 7-9fps——每滚动帧 ~110ms 级 =
  **视口推进→新暴露行整形（S5 域）**。725 管线对该域零效果
  =handoff 预告「上游谱不含 S5」如实显影。

## 结论与回执

- 红面余题=**S5 增量化**（shaping/layout 缓存+视口增量——auto-lang
  上游域另立），非 725 管线回归、非下游 handler 成本。
- 判定口径未动（frozen ①）——P95/面板×0.9 原样，FAIL 为诚实判定。
- budgets 两行+对比表滚动行（022 首判+024 重判并陈）随本谱落账；
  anchors --verify 10 行+render --check 双绿（本件收口实录）。
