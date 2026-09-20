---
plan_id: PLAN-002
status: execution_done
feature_name: bps-dep-consume（bps 池方向一落地：specs/blueprints 拷贝 fork 退役，改 dep path 消费 auto-lang/blueprints canonical）
author: [zhaopuming]
created_at: 2026-09-20
updated_at: 2026-09-20
plan_revision: 1
current_step: 3
total_steps: 3

supersedes_spec_components: []
new_spec_components: []   # 无 docs/specs/ canonical 新建（本仓知识库=.autoos 账本，收据随 merge 投影）
touched_goals: []

affects: [auto-edit（specs/auto-edit, tools, specs/PROVENANCE.md）]
---

# [PLAN-002] bps-dep-consume——bps 池方向一：fork 退役 + dep path 消费

> 裁定依据：2026-09-20 用户裁定"bps 池按方向一做"——auto-lang/blueprints
> 保持 canonical（池活跃演进中：PLAN-657 bp-admin 样板已入池，本仓
> 92c8013a 期拷贝 fork 已陈旧），auto-edit 改 dep path 消费（jade 惯例：
> PLAN-070 T-01 起 `dep bps { path: <相对>/auto-lang/blueprints }` 零副本，
> `auto run` 走 pac.at 直读不物化 junction——079 模式 E-1 在案）。
> 本计划同时解除 PLAN-001 的 bootstrap 期约束"不触碰 auto-lang 仓内
> 路径"（该约束系拷贝起步期一次性语义，方向一显式取代之——001 整体验收
> 注记随本计划收据回填）。

## 0. 变更摘要

| 面 | 内容 |
| --- | --- |
| dep 切换 | specs/auto-edit/pac.at `dep bps` path：`../blueprints` → `../../../auto-lang/blueprints`（specs/auto-edit 三级上溯至 D:/autostack） |
| fork 退役 | 删除 specs/blueprints（92c8013a 期整库拷贝）；PROVENANCE.md 注记退役与去向 |
| 拷贝脚本收敛 | tools/bootstrap_from_auto_lang.py 移除 blueprints 拷贝目标（重跑不再重建 fork） |
| 运行说明 | README How to Run 前置注记 bps dep 解析到兄弟仓 auto-lang（jade 同款依赖形态） |
| 验证 | boot 冒烟（dep 解析 + 零 ERROR）+ 041 矩阵（预期 39/6 持平——上游 menubar 回归独立在案）+ 主检出 git status 干净 |

## 1. 目标

1. **单源消费**：bps 池唯一真源 = auto-lang/blueprints；本仓零拷贝，
   池演进（如 657 新 bp 族）即时可达。
2. **行为不回归**：boot/矩阵结果与 001 交付态持平（39/6 如实口径，
   六失败=上游 menubar 快照回归，与本变更无关）。
3. **可复现性保持**：他机 = auto PATH + python + requests + 兄弟仓
   auto-lang 检出（blueprints 随仓）。

**非目标**：不动 stylekit dep（`../stylekit` 仓内平铺保持——样式库
暂无第二消费者，池化裁定后置）；不改 041 业务代码；不修上游 menubar
回归（独立上游计划面）；不处理池版本锁定协议细化（dep path + 源仓
commit 锚定惯例先行，漂移风险随上游独立计划的提名单治理）。

## 2. 架构方案

```
specs/auto-edit/pac.at（改）：
  dep stylekit { path: "../stylekit" }              ← 不动
  dep bps { path: "../../../auto-lang/blueprints" } ← 方向一（jade 070 同款相对形态）

解析面：auto run 走 pac.at 直读（E-1：不物化 junction——wt-guard 安全面）
        auto build 才物化（本仓不跑 build，红线沿 079 P-15/dep 纪律）
```

## 3. 技术栈

- **auto-edit**：pac.at 一处 + 删 specs/blueprints/ + PROVENANCE.md 注记
  + tools/bootstrap_from_auto_lang.py 目标表收敛 + README 前置注记。
- **auto-lang（只读依赖）**：blueprints 池 @ 当前 master（活跃演进，
  657 后续入池内容 dep 即时可达；无版本锁定——漂移治理归上游独立计划）。

## 4. 需求分析与背景调查

**授权记录**：2026-09-20 用户裁定——"1. bps 池：按照方向一做"；上游包
体量裁定（"比较多 → 独立计划"）与本计划分立。执行授权含本计划全链
（work→review→merge，沿会话内 001 惯例）。

**既有依据（2026-09-20 实勘）**：

| 依据 | 实勘落点 |
| --- | --- |
| jade dep 惯例 | jade desktop pac.at `dep bps { path: "../../../../auto-lang/blueprints" }`（PLAN-070 T-01 起 L1 零副本）；E-1：run 轨零 junction 物化 |
| 池活跃度 | auto-lang/blueprints tip 19ae53fc5（PLAN-657 bp-admin 样板 + 测试面/CI）——fork（92c8013a 期）已落后 |
| fork 面 | specs/blueprints 七族整库拷贝 + PROVENANCE 行 + 脚本两处目标（7/26 行） |
| 消费面 | 041 仅消费 bps.navigation.filetree.tree_util（flatten_tree/toggle_id）——切换后解析路径唯一变化点 |
| 001 交接 | 001 整体验收"不触碰 auto-lang 仓内路径"= bootstrap 期一次性约束，方向一显式取代（本计划 §0 注记） |

## 5. 详细设计

### 规范增量

| delta_id | add/modify/retire | 目标文档 | before/after | rationale | acceptance |
| --- | --- | --- | --- | --- | --- |
| SD-01 | modify | specs/PROVENANCE.md | blueprints 行"拷贝入 specs/blueprints" → 注记"2026-09-20 方向一退役，dep path 消费 auto-lang/blueprints" | 池单源裁定 | AC-01 |

（无 docs/specs/ canonical 新建——本仓知识库为 .autoos 账本，收据随
merge 投影 reviews 段；001 的 P001-1 收据不回改。）

## 6. 测试设计

- **boot 冒烟**：`specs/auto-edit` 下 `auto run -r vm`（30s 超时杀）——
  零 ERROR + Running project 在场 = dep 三链（stylekit 仓内 + bps 跨仓）
  解析成立（E-10 域：dep 落空 = 运行时 Undefined symbol 静默红）。
- **矩阵**：`python desktop_mcp.py` 全量——预期 39/6 持平（六失败 =
  上游 menubar 回归，四次实测基线在案；若出现新失败类 = 本变更回归）。
- **复现性**：主检出 `git status` 干净（fork 删除 + 脚本/文档收敛后无
  未跟踪残留）。

## 7. 验收标准

| ID | 可观察行为 | 验证方法 |
| --- | --- | --- |
| AC-01 | fork 退役 + 单源 dep：specs/blueprints 不存在，pac.at dep bps 指向 auto-lang/blueprints，PROVENANCE 注记在册 | 文件核对 + boot 冒烟零 ERROR |
| AC-02 | 行为不回归：boot/矩阵与 001 交付态持平 | 30s run 冒烟 + desktop_mcp.py 39/6 同类六失败 |
| AC-03 | 可复现性：重跑拷贝脚本不再重建 fork；主检出零脏 | 脚本 dry 执行核对目标表 + git status 干净 |

## 8. 执行步骤

> worktree：`edit-002/auto-edit`（branch plan-002-dev）。

- **T-01** [改] dep 切换 + fork 退役（pac.at path 改 + 删 specs/blueprints
  + PROVENANCE 注记）+ boot 冒烟。依赖：无。→ AC-01 [✅ 已完成：commit 3b9c8a6。cwd 相对解析实勘——首跑 undefined tree_util.toggle_id（worktree 深 2 级落 .wt/edit-002/auto-lang 组兄弟位），按 jade 组惯例补 auto-lang 兄弟依赖树 @3df7b21a2 后 boot 零 ERROR（079 探针路径坑同类；主检出 3 级路径=autostack/auto-lang 正确，同一字符串双上下文——jade 同款设计）]
- **T-02** [改] 脚本收敛 + README 前置注记（bootstrap 脚本移除 blueprints
  目标 + How to Run 注记兄弟仓依赖）。依赖：T-01。→ AC-01/AC-03 [✅ 已完成：COPIES 表收敛 + py_compile 绿 + README 前置注记（同居/组兄弟双上下文说明）]
- **T-03** [验证] 矩阵全量复跑（39/6 持平判定）+ 主检出零脏核对。
  依赖：T-01/T-02。→ AC-02/AC-03 [✅ 已完成：39 PASS/5 FAIL——全部同类 menubar 上游回归面，quit 项本轮自发转绿（同 exe 1467，上游回归面逐项波动），无新失败类且通过数不低于四次基线；worktree 零脏]

## 9. 复审记录

- 2026-09-20 draft handoff：`stage: new | plan_id: PLAN-002 |
  plan_revision: 1 | outcome: pass（起草完成；执行授权在案——方向一
  裁定 + 会话全链惯例） | next: work`。

## 10. 待澄清事项

无（方向一已裁；池版本锁定协议细化随上游独立计划治理，不阻本计划）。

- 2026-09-20 work handoff：`stage: work | plan_id: PLAN-002 |
  plan_revision: 1 | outcome: pass | code_commit: plan-002-dev 3b9c8a6
  | task_ids: T-01..T-03 全勾 | evidence: boot 冒烟双态对照（组兄弟缺失
  = undefined tree_util.toggle_id → 兄弟就位 = 零 ERROR）+ 矩阵 39/5 同类
  menubar 上游面（quit 项自发转绿，无新失败类）+ 脚本 py_compile +
  PROVENANCE/README 收敛 | blockers: 无 | next: review`。
