# 计划-收据索引（reviews/index）

> 结构化收据真源 = `.autoos/specs.json` reviews 段（musk /spec1 API 面）；
> 本页为文档侧导航。计划原文在 `docs/plans/`（001..006 已归档）。

| 计划 | 主题 | 状态 | 收据 | 规范沉淀 |
|---|---|---|---|---|
| PLAN-001 | bootstrap-auto-edit（auto-lang 041 拷贝建仓+双树布局） | archived | P001-1（reviewed pass @ r1 6a3804d） | 00-overview 布局节 |
| PLAN-002 | bps 池方向一（blueprints fork 退役，dep path 消费 canonical） | archived | P002-1（reviewed pass @ r1 3b9c8a6） | 00-overview 布局节 |
| PLAN-003 | front/back 拆分 + 双轨化（vm/vue + api.at 边界） | archived | P003-1（reviewed pass @ r1 7a4ed53） | 01-architecture / modules/back-api |
| PLAN-004 | M1 性能轨①②（功能健康基线 + perf 模式一键化） | archived | P004-1 | modules/perf-measurement |
| PLAN-005 | M1 性能轨③（测量体系 + 去 src 镜像先行段） | archived | P005-1（delivery 31ebb7b ff-only 落 main） | modules/editor-store（src 语义）/ perf-measurement |
| PLAN-006 | m1-l2-baseline-report（L2 数字面：release 直拉运行器+l2 预算武装+首基线） | archived | P006-1（reviewed pass @ r1 9dcb58f≡06cb964 rebase 全等，delivery ff-only 落 main） | perf-measurement L2 节 |

**流程勘定（2026-09-22，勘误 v2）**：规范沉淀**确有发生**——PLAN-002 立
惯例「本仓知识库=.autoos 账本+模块 README，无 docs/specs/」，003/004/005
的 SD-01..03 均按此落 `specs/auto-edit/README.md`（git 实迹：da31576/
83e550e/ade6e73）。**债的真实形态**=规范落点单吊 README（欠结构化分区/
模块册/可导航性），specs.json 四段与 docs/specs/ 从未建立——本册即按
计划+README+代码重建结构化文档面（各册头注含来源）。此后新计划的规范
增量目标改指 docs/specs/（本册），README 保持运行矩阵/快速上手单源。
PLAN-006 的 `docs/plans/006-*.md` 当前为**未提交工作树文件**，其 review
与收据落段待后续流程。此后计划的 merge 阶段须按 00-overview「计划与规范
的关系」节执行规范增量沉淀。
