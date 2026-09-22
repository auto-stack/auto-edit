# 测量模式阶梯与工具链（modules/perf-measurement）

> 来源：docs/strategy/002-north-star-v2.md §5 + PLAN-004/005/006 交付
> （tools/perf、tools/bench）。

## 测量模式阶梯（战略 §5，硬约束）

| 档 | 形态 | 效力 |
|---|---|---|
| **L0** | 日常 VM+merged | 代理指标防结构回归（无预算效力） |
| **L1** | （中间档） | 经 perf.py 链取归因 |
| **L2** | a2r 转译 + release 编译 + RQ（外部统一渲染器做 compositor） | **预算与门禁只在 L2 数字上评估** |

预算语义拆分：**稳态启动**（渲染器暖态）为头条硬门禁（回归当天修），
**渲染器冷启动**一次性成本单列（Q2 待裁）；其余指标 M2/M3 记账、M4
统一收口。RQ+预热渲染器不只是测量配置，更是交付拓扑候选（渲染成本跨
实例摊销=notepad 高频开关秒开），与 exe 路径联合入 Q2。

**过早优化宪法**（v2 裁定 6）：缓冲区类预算（100MB/1GB/diff）在内核
rope 化前架构性不可达——此前禁止对该路径调优；bench 只记基线并标
"架构阻塞"。M1 内部排序（裁定 8）：①功能健康 → ②性能模式一键化 →
③测量体系 → ④才做性能测试；上游供料包（F-R1/F-RV6/rope/delta/分块
读）为 M1 第一优先。

## 工具链

- **tools/perf/**（PLAN-004，一键化）：`check`（依赖自检+环境指纹）/
  `smoke`（rqhost 预热+双实例编排验证）/ `a2r` / `release`。退出码
  0/3/1（**3=blocked-on-upstream**：RQ 渲染臂 codeeditor 覆盖缺口
  [供料 §6]、a2r 词汇门[§7]——当前 a2r 即 blocked）。
- **tools/bench/**（PLAN-005，L0 测量+断言）：`check`/`proxy`（启动
  分解弃暖机、打开计时 1/10/100 MB fixture、内存采样、**全量读检测**、
  断言报告 → results/<ts>.jsonl 入仓）/`assert`（仅预算断言）。断言
  报告逐行显式终态（not-armed/arch-blocked/blocked-upstream/
  pending-feature/ledger 五类，无静默缺席）。fixtures/logs gitignored。
- **L2 运行器**（PLAN-006，execution_done 未归档）：release 产物直拉
  （rqhost 预热后 spawn `rust-workspace/target/release/auto-edit.exe
  --autodesk-rqhost` + AUTO_BENCH=1），5 跑弃首跑出启动分解；
  evaluate_budgets 增 l2 分支（steady_start hard ≤80ms 武装出数字）。

## 上游阻塞登记（供料面）

上游供料包文档：`docs/upstream/2026-09-m1-supply.md`（F-R1 a2r 生成器
E0432 / F-RV6 进程级早崩竞态（矩阵基线口径：完成态跑次 ≥49 passed /
0 failed 判绿，无 RESULT 行=竞态早崩重跑一次不计败）/ rope / delta /
分块读）。**RQ 渲染臂 codeeditor 覆盖缺口**（供料 §6）与 **a2r 词汇门**
（§7）为 L2 链当前两处 blocked-on-upstream。
