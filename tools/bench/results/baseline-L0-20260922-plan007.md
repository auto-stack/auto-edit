# L0 装载链改造锚点复跑（PLAN-007；终态=上游 687 端点）— 2026-09-22

> **口径**：PLAN-007 T-03 复跑摘要。store 去文本化（src 镜像退役 →
> 装载链）后的 L0/vm 装载锚点，对照 PLAN-005/006 旧锚
> （`baseline-L0-20260921.md` / `baseline-L2-20260922.md`）。
> **终态数据（上游 PLAN-687 装载端点）**：工具链
> `v0.4.2-1855-gea2a4af4d-dirty`（lang-687 worktree 构建含
> code_editor_load_file nat#9908），数据源
> `results/20260922-150608.jsonl`。**中间形态**（分块装载三形状，
> 工具链 1850）数据源 `20260922-140727/141056/141652.jsonl`——
> 100MB 装载内存 729-1356MB 反例与归因留档（upstream §10 观察 B）。

## 装载链形态（T-03 定调）

- **块上限 2GB=实践单块直载**：edit 每调用 O(n) 全文重写（S1 固有），
  块数=时长平方因子——4MB 块 100MB 超 120s 窗未捕获（首跑），16MB
  块 78s/1356MB，单块 30-84s/729-1315MB（内存与块数无关，时长单块
  最优）。
- **`spawn_to_open_start` ≈ 3.3s**（三档同值，固定开销）：装载在编辑器
  widget 实化后的下一轮 Tick（800ms interval）+ app 引导。`open_ms`
  标记对只包夹纯装载时长（包夹语义保持）。

## 锚点对照（L0/vm）

| 尺寸 | 旧锚（src 镜像，2026-09-21） | 新（单块装载，本表） | Δ |
|---|---|---|---|
| 1 MB | 229.5 MB / 25.7ms | 236 MB / 284ms | **持平**（+7MB/+258ms） |
| 10 MB | 251.3 MB / 25.7ms | 334 MB / 1.8s | +83MB（+33%） |
| 100 MB | 521.1 MB / 459.8ms | 729-1356MB / 30-84s | **+208~+835MB（不降反升）** |
| 启动 steady | ~362ms（2026-09-21） | 286ms（工具链/机器差异） | — |

## 反向结果归因（AC-02 未达；upstream §10 观察 B）

去 store 镜像省下的 ~200-300MB（src + src_active 拷贝）被装载机构的
全文过载成本吞没反超：①`read_text_range` 双轨实现=**全量读盘假分块**
（`fs::read` 全文件 + from_utf8 全文验证 + 切片——IO 层未分块）；
②envelope（含全文的 JSON 串）经 VM 字符串池过载滞留；③`code_editor_
edit` O(n) 全文重写 churn（Buffer+rope 每 pass 重建）。1MB 持平证明
小文件无劣化——劣化随文件尺寸超线性。**修复面全在上游**（真分块 IO /
envelope 流式 / S2 增量 rewrite）；处置提案见 plan §10-5（待用户裁定）。

## 结构回归代理

- **编辑路径全量读检测：green**——允许位 ActSave/QuitSaveClose 两
  save 位（白名单零改动；src 退役后 `code_editor_text` 允许位仍=两
  save 位，检测器面不变）。


## 终态锚点（上游 PLAN-687 装载端点，2026-09-22 追加）

`code_editor_load_file(key, path)`（nat#9908，native 端到端：
std::fs 单趟读 + core.set_text 单次重写 + delta drain-弃 +
last_external 不触）——下游 RunPendingLoad 一行调用，全文零 VM
过载：

| 尺寸 | 旧锚（src 镜像，2026-09-21） | 中间（分块装载） | **终态（端点）** |
|---|---|---|---|
| 1 MB | 229.5 MB | 236 MB | **219 MB** |
| 10 MB | 251.3 MB | 334 MB | **218 MB** |
| 100 MB | 521.1 MB / 459.8ms | 729-1356MB / 30-84s | **219 MB / <25ms** |

**形状结论**：内存全档 Flat ~219MB（与文件尺寸解耦——编辑器侧
布局惰性物化 + 零 VM 侧滞留）；100MB 较锚 -58%。装载时长低于
L0 25ms 轮询粒度（标记对同窗到达）。中间形态的反例归因（envelope
过 VM 池滞留 ~8× 线性 / read_text_range 假分块 / edit O(n) 多趟）
由端点形态整体绕开——真分块 read_text_range（PLAN-687 T-01/02）
作为流式消费面在档，S2 解阻后可回归分块装载。
