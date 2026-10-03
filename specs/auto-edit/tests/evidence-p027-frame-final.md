# evidence-p027 — 帧两行终裁谱+泵回环上限定谳+协议修订记录（PLAN-027 T-00/T-01，2026-10-03）

## T-00 终裁勘定（四门）

- **工具链门**：组三树 edit-027〔auto-edit@plan-027-dev base 252028a/
  auto-lang@de3a64353 detached+auto-down@895f8d0 detached——autodown-core
  组 sibling 解析 load-bearing 维持〕——release 组树重建
  `cargo build --release -p auto`，`auto --version` = **auto 0.1.0+
  v0.4.2-2704-gde3a64353**（clean 无 -dirty；735@4195f7af9+737@59ff4e66f+
  731@30bda6831 祖先链 merge-base --is-ancestor 三实证）。plan 起草
  时 master 实勘位 fecf9a590 已被 737 交付推进（delivered@59ff4e66f
  merge 收据在档）——735 祖先链在位=门语义满足，737 增量〔MCP 工具
  执行 spawn_blocking——MCP 驱动通道面〕如实注记。`bench.py check`
  绿（构建 2702≥1588 PATH debug 侧；正式跑 AUTO_BIN 钉 worktree
  release 2704——PATH 坑纪律）。
- **735 回执谱同机复验（带内——frozen ⑤）**：组树 ladder735.py 处方
  复跑（`--label p027-reverify`），对照 ladder-p735-after.jsonl
  （auto-lang evidence/735 在档）：

  | 线（1mb） | 735 回执 | 027 复验 | 带 |
  |---|---|---|---|
  | type s5 P50 | 0.36ms | 0.37ms | ✓ 带内 |
  | scroll s5 P50 | 0.33ms | 0.36ms | ✓ 带内 |
  | typenl s5 P50 | 0.30ms | 0.36ms | ✓ 带内 |
  | type 泵率 | 10.07/s | 10.28/s | ✓ 同带 |
  | scroll 泵率 | 2.60/s | 2.76/s | ✓ 同带 |
  | typenl 泵率 | 10.08/s | 10.56/s | ✓ 同带 |

  配对率 **100% 全相位**（复验 236 帧零 orphan——735 §2 改后终态
  下游复现）+type total P95 0.01ms 全等——零回退环境噪声排除，重判
  放行。复验谱=tests/evidence-p027-upstream-reverify.jsonl（026 时代
  100kb/typenl 拒连瞬态本轮零复现）。
- **通道新鲜度勘定（带内——9920 条件路由位关闭）**：
  probe_frame_channel.py Phase A——fprobe_present（9919 泵消费时刻）
  vs 行通道 draw_end（735 真值）值域对齐 Δ：**P50 1ms/min 0ms/max
  19-31ms**（两跑一致）+行配对 100%——配对修复后消费≈呈现→**零上游
  依赖，9920 不接线**（735 §3.2 建议项按其预设条件关闭）。证据=
  tests/evidence-p027-frame-channel.jsonl。
- **Q-1 材料定稿+用户裁定（双修采纳，2026-10-03 AskUserQuestion
  回执）**：材料=上述校准数字+下节泵上限发现；裁定=(a) 读回切呈现
  面+(b) 16ms 节拍；阈值/语义 frozen 原样（修订=测量实施面）。

## T-00 校准实证（泵回环吞吐上限定谳——735 §4 候选 (b) 下游实证）

- **MCP 调用地板**：背靠背 autoui_type p50 14.1-15.8ms（min 1.5-14.4/
  max 21.8-27.4）→16ms 节拍下有效驱动 ~30ms 周期（~34Hz——调用时延
  主导，节拍再降无效；MCP 通道持续驱动上限 ~63-71Hz）。
- **泵回环 ~95ms/圈=呈现吞吐上限 ~10/s**：16ms 节拍换行窗（~34Hz
  驱动）distinct draw_end 35-37/3.5s≈**9.95-10.53/s**（两跑一致）；
  draw_end 间隔 **91-95ms 恒定与驱动节拍无关**；突发内 0-1ms 连建
  （每 ~93ms 泵醒一次派发 ~6 帧）+帧工作面 2-3ms 全绿（builds=1，
  begin→present=draw_end 2-4ms）——事件循环数百 fps 能力确认（735
  §1「滚动突发期送达间 2-3ms」下游复现）。
- **735 §3.3 预判的下游修正**：「frozen 判据在 60ms 驱动下物理不可
  达——驱动器本身是帧率上限」——下游实证：泵上限（~10/s）<驱动上
  限（~34Hz），scroll 判据在**任何测量实施修订**下物理不可达；解锁
  前置=上游泵域清偿（泵 pacing=735 §4 候选 (b) 域，不在 735 修复
  范围=上游域余题②定谳）。

## T-01 终判谱（N=4 全有效，release v2704 L0 VM 形，修订协议）

| 谱（tools/bench/results/） | type P50/P95 ms（行通道） | frames/配对 | fprobe 对照 P50/P95 | scroll fps（行通道） | fprobe 对照 | 判定 |
|---|---|---|---|---|---|---|
| frame-20261003-114018（冒烟） | 3 / 4 | 25/100% | 110 / 111 | 9.87 | 7.90 | PASS/FAIL |
| frame-20261003-114048 | 3 / 3 | 26/100% | 108 / 112 | 9.67 | 7.21 | PASS/FAIL |
| frame-20261003-114111 | 2 / 3 | 24/100% | 94 / 107 | 9.64 | 8.11 | PASS/FAIL |
| frame-20261003-114135 | 3 / 4 | 27/100% | 94 / 111 | 9.98 | 5.42 | PASS/FAIL |
| frame-20261003-114158 | 3 / 4 | 30/100% | 94 / 136 | 9.99 | 8.82 | PASS/FAIL |

**判定：type_latency armed PASS（027 代首绿——P50 2-3/P95 3-4ms ≤
16.7ms）；scroll_fps armed FAIL 维持（9.6-10.0fps < 54）**——frozen
口径如实执行（修订仅测量实施面）。fprobe 对照列=泵消费时刻读数
（type P50 94-110ms 陈旧度——026 读数语义对照实证；scroll 5.4-8.8
同带）。

**四代谱系（历史不删+通道换代直比禁则）**：022 首判 110/115ms+
8.0fps → 024 重判 95-112ms+6.7-8.8fps → 026 终判 156-160ms+
8.1-9.5fps → **027 终裁 3-4ms+9.6-10.0fps**。type 面 027 数字与前代
**不可径直跨代直比**（读回通道换代：022-026=泵消费通道〔陈旧度语
义〕，027=呈现面真值通道〔735 配对修复后〕）；scroll 面同带可比
（同一泵上限主导——027 微升=16ms 节拍驱动读数）。

## 协议修订记录（Q-1 回执——防冒领分界）

修订面四项（bench.py stage_frame 帧区域一次修订+probe 探针新件）：

1. **读回主读切行通道**：[P725-FRAME] total_ms（present 列=draw_end
   优先真值）——022 帧内口径（键入帧 begin→下一 present 差）的如实
   通道；fprobe 快照差分退役为对照列（逐跑并录 role=comparison，
   不判定）。
2. **驱动节拍 16ms**（主读相——面板周期量级）；对照相维持 022 原样
   （60ms+密集轮询）=A/B 双通道同跑实录。
3. **成员过滤勘定**：type 判定域=dirty==1∧present>0（配对脏帧）——
   ladder 上游款 s2_us>0 条件在下游不适用（真实 app 脏帧 VM 段常
   0µs——T-01 首跑实勘，19/22 脏帧 s2=0 而帧时 2-4ms 完好）。
4. **窗口切片=值域锚点**（相边界 fprobe_begin 帧时基读数）+运行末
   整读日志——app stdout 块缓冲滞后使中途行数切片不可靠（执行期
   勘定：驱动期 ~9 脏帧/s 在档而 mark 切片仅得 2-5）。

**frozen 断言**：budgets budget/threshold 字段 diff=零；判定语义零
变更（P95 ≤1 帧+面板×0.9 原样）；面板 EnumDisplaySettings 读回
60Hz（budget 16.67ms/threshold 54.0 全谱在录）；修订合法性=Q-1
用户裁定回执（2026-10-03）。
