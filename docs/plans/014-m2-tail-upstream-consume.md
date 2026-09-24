---
plan_id: PLAN-014
status: drafting
feature_name: m2-tail-upstream-consume-v1（M2 尾件+上游端点消费——跳转列表/化妆件/save 解禁/光标恢复/time 族/vue 复验，形态 A 消费件）
author: [agent]
created_at: 2026-09-24T15:00:00+08:00
updated_at: 2026-09-24T15:00:00+08:00
plan_revision: 1
current_step: 0
total_steps: 11
supersedes_spec_components: []
new_spec_components:
  - "docs/specs/modules/editor-store.md#SD-01（大文件模式节 modify：save 护栏→直写端点解禁——条件供①）"
  - "docs/specs/modules/editor-store.md#SD-02（会话节 modify：光标恢复应用转正+scroll 条件形——条件供②）"
  - "docs/specs/00-overview.md#SD-03（M2 注记补尾件行——跳转列表+消费收口=M2 完全收口）"
  - "docs/specs/modules/perf-measurement.md#SD-04（time 族改接——条件供④）"
touched_goals: []
---

# [PLAN-014] M2 尾件+上游端点消费 v1（形态 A 消费件）

## 0. 变更摘要

形态 A 双子计划的**消费件**（供料件=auto-lang 仓 PLAN-6xx 号，其仓内
立项；两件执行前置互绑）。M2 验收面四件已全 delivered（008/009/010/
013），本件收**最后尾债**：本仓两小件（**任务栏跳转列表**[补注十一
「Windows 集成余=小尾件」原文]**+F-01 化妆件**[006 挂账]）+**上游
端点消费五件**（save 护栏解禁[供① code_editor_save 直写]/光标恢复
启用[供② set-cursor+editor-scroll]/time 族改接[供④]/vue strict 复
验+遮蔽缓解退役判定[供⑤ schema+helper 类型]/F-RV6 口径重定评估
[供③ 稳定化]）。分两段执行：**段一（独立段，无前置可先行）**=T-01
跳转列表勘定+T-02 跳转列表实施+T-03 化妆件；**段二（消费段）**=供
料件对应 delivered 后解锁。save 解禁=013 护栏的解除件消费（§16 原文
「落地后 big 态 save 解禁，零 front 改动预期」）；光标恢复=010 前向
兼容位转正（§13 原文「set-cursor 端点清偿后启用即得，零会话侧改动
」）。非目标：a2r 视图联动（§10）、EOL 逐行保真（§11）、单处替换族
（§12）、tree-sitter/语法高亮（M4）、大文件分块解码（1GB 上游）、
ICustomDestinationList 自定义任务类（勘定判大件则挂账）。

## 1. 目标

- **G-1 任务栏跳转列表**：M2 Windows 集成尾件——勘定实现层（壳自动
  Recent 面已备度/SHAddToRecentDocs 内核 shim/自定义任务类三路裁定，
  T-00①）后按裁定形落地或并入供料段。
- **G-2 bench 化妆件收口**：F-01（stage_assert 重放 l2 文件摘要行序
  取 L0 缺省五态序，误导性「（缺：not-armed）」——从 budget_assert
  记录的 mode 字段取序，006 §F-01 原案）；F-02（_window_opened_since
  重复定义）**已被后续 bench 改造吸收**（2026-09-24 实勘无命中）——
  勘定记录即毕。
- **G-3 save 护栏解禁**（条件供①）：big 态 save 从「拦截+提示」改道
  `code_editor_save` 直写端点（rope→磁盘直写，全文零 VM 往返）；
  normal 态 v1 维持现链（Q-2）；护栏语义退役成文。
- **G-4 光标恢复启用**（条件供②）：会话恢复链 cline/ccol 应用经
  set-cursor（010 前向兼容位转正）；scroll 条件形（供② scroll 写端
  点落地则会话增 scroll 持久化+恢复应用——会话契约扩展 Q-3；否则
  注记保持现状）。
- **G-5 time 族改接**（条件供④）：bench 毫秒值从 host 侧 stdout 落
  文件时间戳改 app 内 time 族来源（§9 观察清偿）。
- **G-6 vue strict 复验**（条件供⑤）：strict gen exit 0+pnpm build
  exit 0 双恢复；regen_vue.py print 遮蔽缓解件（globalThis 改写）
  退役判定（上游 print 映射改道[§16 解锁③]落地则摘）。
- **G-7 口径重定与矩阵**：F-RV6 清偿评估（条件供③：5 连跑矩阵定干
  净基线+重跑条款/T12.6 已知缺注记退役评估）；矩阵扩 T18 检查组
  （save 解禁 E2E/光标恢复/跳转列表可断言面）；README 口径随升。

### 非目标

- a2r 视图-状态联动（§10，独立上游件——L2 open 段，另行跟踪）。
- EOL 逐行保真（§11）/单处替换/find_prev/匹配计数/goto 行（§12）
  ——清单外增强件，另行供料评估。
- tree-sitter/语法高亮 20 语言（M4 门控，designs/001 在档）。
- 大文件分块解码/1GB 线（上游阻塞，013 两段式注记维持）。
- ICustomDestinationList 自定义任务类（若 T-00① 判大件）。
- normal 态 save 链迁移直写端点（v1 仅 big 态解禁——Q-2）。

## 2. 架构方案

分层落点（2026-09-24 实勘：auto-edit main@471071d[013 delivered]/
auto-lang b41e9aa31）：

| 面 | 现状 | 本期形态 | 依据 |
|---|---|---|---|
| 跳转列表 | 内核零 shell 面（crates grep 实勘零 JumpList/RecentDocs 命中）；pac `opens` 文件关联+desktop open_with 接收臂（016）+recents（010）已备 | T-00① 三路裁定：(a) 壳自动 Recent（关联打开 shell 自记账——实测已备度）；(b) SHAddToRecentDocs 内核 shim（**供料段并入**——recents 落盘挂点直调）；(c) 自定义类=非目标 | 补注十一「小尾件」+§13 边界先例 |
| save 直写 | big 态=WriteFidelity 拦截+big_hint（013）；§10-2 want 在册 | 供① `code_editor_save(key, path)` 直写端点 → WriteFidelity big 分支改道直调（bom/eol 包装语义由端点侧承载或注记——T-00② 勘定）；护栏提示退役 | §16「零 front 改动预期」 |
| 光标恢复 | cline/ccol 持久化入会话但恢复不应用（前向兼容位，§13） | 供② set-cursor → 恢复链装载完成位调用（TabActivate/RunPendingLoad 后）；scroll=供② 写端点落地则会话 JSON 增 scroll 字段（会话契约扩展）+恢复应用 | §13 消费方注记 |
| time 族 | bench 毫秒值=host 侧对 stdout 落文件时间戳（§9：VM 轨 time 族未接线） | 供④ time 族接线 → bench 标记携带毫秒值（print 形态或新端点——T-00② 勘定）→ JSONL 字段改源 | §9 登记 |
| vue 臂 | strict gen 红=menubar-sub schema（695 预存）+build 红=§14 helper TS7006×12（预存）；print 遮蔽缓解件在 regen_vue.py | 供⑤ schema+类型注解 → strict/build 双恢复；缓解件退役判定（上游③改道落地则摘，否则保留注记） | §16 解锁三项 |
| 口径 | 判绿=≥N/0+T12.6 已知缺不计+轮换 flake 重跑条款（F-RV6 竞态期） | 供③ 稳定化 → 5 连跑矩阵定干净基线 → 条款退役评估（不达则维持并注记） | §5/012-013 三期收据 |
| bench 化妆 | stage_assert 重放取 L0 缺省序（006 F-01） | `_print_budget_table` 从 budget_assert 记录 mode 取序（~3 行） | 006 §F-01 原案 |
| 检测器 | 白名单五件封闭集 | WriteFidelity 改道=读出位语义变化——**直写端点后 code_editor_text 在 WriteFidelity 位退役**（读出位四→三）→ 检测器白名单勘正（T-05 内） | 013 零变更基线 |

**形态 A 接口面**：供料件契约=本件 §供料回执（§5 前）+docs/upstream
既有登记（§5/§9/§10-2/§13/§14/§15/§16）；供料件在 auto-lang 立号时
从本节取契约面；本件消费任务 T-00② 探针复核实际端点形（契约漂移=
回 new 有界修订）。

## 3. 技术栈

.at（editor_store.at WriteFidelity 改道/恢复链光标应用、back api.at
条件端点消费[无新增 back 端点——直写/set-cursor 走编辑器内核端点族
非 #[api]]）、desktop_mcp 矩阵（T18 组）、tools/bench（F-01 修正+
time 族改接+口径）、scripts/regen_vue.py（缓解件退役判定）、auto-lang
侧供料件（其仓栈：rust 内核端点+VM 内建+cargo 门禁）。无新依赖。

## 4. 需求分析与背景调查

- **授权记录**：用户 2026-09-24 指令「可以合起来做一个跨仓库的计划吗
  ？OK，那么用形态A吧」——形态 A 双子计划授权（供料件 auto-lang 立号
  +本消费件 auto-edit 立号 014，执行前置互绑）。授权=预起草；本件执
  行分段：段一（T-01..T-03）无前置；段二（T-04..T-09）前置=对应供料
  件 delivered。
- **战略依据**：§2.2 M2 清单（会话行「光标+滚动位置」/Windows 集成行
  「任务栏跳转列表」）；补注十一（「Windows 集成余=任务栏跳转列表小
  尾件」原文——M2 剩余面勘定）；§5 性能文化（time 族接线=测量体系
  观察清偿）。
- **上游登记对账**（docs/upstream/2026-09-m1-supply.md）：§10-2
  code_editor_load_file（687 已清偿）+**code_editor_save 直写（在册
  want）**；§9 time 族（观察件）；§13 **set-cursor+editor-scroll
  （want——editor scroll 读+写双端点形）**；§14 helper 族 TS 类型
  want；§15/§16 vue 解锁三项（menubar-sub schema/helper 类型/print
  映射改道）；§5 F-RV6（矩阵竞态，011/012/013 三期收据复现在案）。
- **本仓挂账对账**：006 §F-01（stage_assert 重放行序——**在案待修**
  ）/§F-02（_window_opened_since 重复定义——**2026-09-24 实勘已无
  命中**，被 011/012 期 bench.py 改造吸收，勘定记录即毕）；013 §9
  F-1（vue AC-06 deviation——本件 G-6 消费解阻）；013 §16 code_editor
  _save=护栏解除件（本件 G-3）。
- **跳转列表实勘**（2026-09-24）：auto-lang crates 全 grep 零 shell/
  JumpList/RecentDocs 面；本仓已有=open_with 接收臂（宿主 open_with
  →write_state→ConsumeOpen，016）+pac `opens` 声明（文件关联注册面
  ）+recents（010，会话持久化+Explorer 侧栏）。壳自动 Recent 行为
  待实测（关联双开是否已进跳转列表——T-00①）。
- **代码锚**：`specs/auto-edit/src/front/editor_store.at`（WriteFidelity
  三分支位[big 门 013/readonly 兜底 008/正常链]、恢复链 cline/ccol
  丢弃位[LoadWorkspace 尾段+TabActivate]、recents 维护位[OpenPath 前
  段]）、`tools/bench/bench.py`（stage_assert:765/_print_budget_table
  :400/evaluate_budgets:384）、`scripts/regen_vue.py`（globalThis 遮
  蔽缓解件）、`tests/desktop_mcp.py`（T17 在途——T18 追加位）、
  `tools/bench/results/`（JSONL 惯例）。
- **风险登记**：端点契约漂移（供料件实际形 vs 本件预记——T-00② 探
  针门+漂移回 new 有界修订）；jump list 裁定 (b) 则 G-1 部分改道供
  料段（范围缩减须用户确认——skill 禁静默缩界）；直写端点字节保真
  （bom/eol 包装语义归属端点 or front——T-00② 勘定，SD-01 成文）。
- **矩阵口径**：013 终态 117 检查（判绿 ≥115/0）；T18 后 → ≥N+M/0
  （M=T-05/T-06 实落）；供③落地则重跑条款退役评估（T-09）。

## 5. 详细设计

### 供料回执（形态 A 接口契约——供料件立项取材面）

| 供件 | 端点/件 | 契约预期（T-00② 探针复核前为预记形） | 登记源 |
|---|---|---|---|
| 供① | `code_editor_save(key, path)` | rope→磁盘直写（零全文 VM 往返）；返回 int/bool 形待勘定；**字节保真归属**=预期端点侧裸写（bom/eol 包装仍 front——WriteFidelity 包装逻辑保留、读出+write_text 两步由端点一步承载——T-00② 勘定后 SD-01 定形） | §10-2/§16 |
| 供② | `set-cursor(key, line, col)` + `editor-scroll(key, axis, offset)` 读/写族 | §13 形：scroll 读=per-tab 偏移上报/写=按偏移应用；set-cursor=光标位应用（0 基/1 基待勘定——SyncCursor 现役 +1 面对齐） | §13 |
| 供③ | F-RV6 稳定化 | 矩阵进程级早崩竞态清偿（5 连跑零早崩判据——004 §5 判据形） | §5 |
| 供④ | time 族接线（now_ms/elapsed 形） | bench 标记毫秒值 app 内来源（BENCH 行携值 or 查询端点——勘定） | §9 |
| 供⑤ | menubar-sub 三元素 vue schema + helper 族类型注解 | strict gen 恢复（S002 清零）+TS7006 清零；print 映射改道（§16 解锁③）随件评估 | §14/§15/§16 |

优先序（用户形态 A 裁定语境）：**供③ F-RV6 先行**（矩阵可信度=全
部下游判据的前置）→ 供① save 直写（013 解除件）→ 供② 光标/滚动
→ 供④⑤ 并行可选。供料件编号/立项在 auto-lang 仓（PLAN-6xx），本件
不代立。

### T-01 跳转列表勘定（决策件，段一先行）

`tests/probe_jumplist.py`（probe 族形）+手工面：①壳自动 Recent 实测
（`auto run` 实例经关联双开 fixture→任务栏跳转列表「最近」是否已含
——零改动面勘定）；②内核 shell 面缺口成文（SHAddToRecentDocs/
ICustomDestinationList 两档 shim 的最小形）；③裁定：**(a)** 已备（
零改动+注记）/ **(b)** shim（并入供料段——G-1 部分改道，缩界须用户
确认）/ 自定义类=非目标成文。

- AC 关联：AC-01。验证：探针退出码+决策记录落 §10。

### T-02 跳转列表实施（条件：T-01 裁定形）

裁 (a)=零改动+SD-03 注记即毕；裁 (b)=供料段扩件+本任务改「消费 shim
」：recents 落盘挂点（SessionSave）直调内核 shim 使打开文件进壳
Recent——矩阵可断言面勘定（autoui_state 零 shell 面——E2E=手工/
探针双轨）。custom 类挂账非目标。

- AC 关联：AC-01。验证：裁定形对应矩阵/手工面。

### T-03 bench 化妆件（段一）

F-01：`stage_assert` 重放 l2 文件时摘要行序从 budget_assert 记录的
mode 字段取（006 原案 ~3 行）；l2 results 文件重放复验无「缺：
not-armed」误导行。F-02：勘定记录（已消失，2026-09-24 实勘）。

- AC 关联：AC-02。验证：`bench.py assert --results <l2 文件>` 输出
  断言+bench check/proxy l0 绿。

### T-04 端点消费探针（段二门——前置供①②）

`tests/probe_upstream_consume.py`：三端点形勘定（save 直写返回值/
大文件 E2E 字节；set-cursor 基面+SyncCursor 对齐；editor-scroll 读写
往返）+供④⑤在册状态复核。产出=§10 决策记录+SD-01/02 定形。

- AC 关联：AC-03/AC-04 前置。验证：探针退出码 0+报告落档。

### T-05 save 护栏解禁（前置 T-04）

WriteFidelity big 分支改道：`code_editor_save(.tabs[i].key,
.tabs[i].path)` 直写（bom/eol 包装按 T-04② 勘定形）；拦截提示与
big_hint save 位退役（readonly 兜底保留——008 语义不变）；检测器
白名单勘定（WriteFidelity 读出位退役则登记面勘正）；normal 态零扰
动（Q-2 v1 界定）。

- AC 关联：AC-03。验证：矩阵 T18（big save E2E 磁盘字节+50MB 域
  时长对照[护栏时代 1.3-4.2s→直写预期 <100ms 量级——687 load 对
  称面]）+011/008 既有 save 检查复绿。

### T-06 光标恢复启用（前置 T-04）

恢复链装载完成位（RunPendingLoad 成功分支）经 set-cursor 应用
cline/ccol（0 基换算对齐 SyncCursor 面）；scroll 条件形：供② 写端
点落地则会话 JSON 增 per-tab scroll 字段（会话契约扩展——SD-02 成
文）+恢复应用；否则注记维持（§13「滚动不恢复」现状）。矩阵 T18 断
言：恢复后 line/col=会话值（cline/ccol 现持久化 1 基）。

- AC 关联：AC-04。验证：矩阵 T18+010 既有 T14 组复绿（零误伤）。

### T-07 time 族改接（前置供④ delivered）

bench.py BENCH 标记消费改 app 内毫秒值（形态按 T-04③ 勘定）；
JSONL 字段改源+host 时间戳保留为对照列（一跑双录）；L0/L2 双模回归。

- AC 关联：AC-05。验证：bench proxy l0+JSONL 字段 grep。

### T-08 vue strict 复验+缓解件退役判定（前置供⑤ delivered）

strict gen exit 0+pnpm build exit 0 双复验；regen_vue.py 遮蔽缓解件
退役判定（print 映射改道[§16③]落地=摘除脚本段+恢复直写；未落地=
保留+注记）；README vue 臂注记更新。

- AC 关联：AC-06。验证：构建退出码+grep。

### T-09 F-RV6 口径重定评估（前置供③ delivered）

5 连跑全矩阵（钉版新工具链）：零早崩=干净基线重定+重跑条款/T12.6
已注记退役评估成文；不达=维持现状+漂移记录。

- AC 关联：AC-07。验证：五轮谱+README 口径段。

### T-10 矩阵 T18+README 口径（前置 T-05/T-06 实落）

desktop_mcp.py 增 T18 组（预估 6 检查：big save 直写 E2E 字节/时长
代理、readonly 兜底不受扰、光标恢复 line/col 断言、scroll 条件形、
normal save 零扰动、会话链回归）；README 口径 ≥N+M/0+vue 臂/解除件
注记更新。

- AC 关联：AC-07。验证：矩阵退出码+README grep。

### T-11 规范落账（前置 T-10）

SD-01..04 落 docs/specs（条件形按实落）；upstream §17 登记（消费
收据：供①②④⑤ 清偿核销+供③ 评估面）。vue regen --build exit 0
（AC-06 达成后本行即真）。

- AC 关联：AC-06/AC-07。验证：grep 册+构建退出码。

### 规范增量

| delta_id | add/modify/retire | docs/specs/... target | before/after rule | rationale | acceptance IDs |
|---|---|---|---|---|---|
| SD-01 | modify | modules/editor-store.md（大文件模式节） | before：big 态 save=拦截+提示（护栏，解除件=上游直写端点）。after：直写端点时代语义——WriteFidelity big 分支改道 code_editor_save（包装语义/检测器登记面勘正在节）；readonly 兜底不变 | 013 解除件消费——护栏退役成文 | AC-03 |
| SD-02 | modify | modules/editor-store.md（会话持久化与懒恢复节） | before：cline/ccol 持久化不应用（前向兼容位）；滚动不恢复。after：光标恢复应用启用（set-cursor 消费+基面换算）；scroll 条件形（会话契约扩展按供②实落） | §13 前向兼容位转正 | AC-04 |
| SD-03 | modify | 00-overview.md（M2 注记） | before：第四件行（M2 四件全落）。after：补尾件行（跳转列表+消费收口=M2 **完全收口**叙事；尾债去向注记） | M2 总览进度面 | AC-01/AC-07 |
| SD-04 | modify（条件供④） | modules/perf-measurement.md（观测通道节） | before：毫秒值一律 host 侧 stdout 落文件时间戳。after：time 族接线后 app 内来源为主/host 对照列保留 | §9 观察清偿 | AC-05 |

## 6. 测试设计

- **T-01 探针**（probe_jumplist.py）：壳 Recent 实测+缺口成文；退
  出码门。
- **T-04 探针**（probe_upstream_consume.py）：三端点形勘定；退出码门。
- **矩阵 T18**（desktop_mcp.py）：六检查（§T-10）；独立进程+APPDATA
  隔离惯例。
- **回归面**：008 T12 save E2E/011 T13 readonly 拦截/010 T14 会话组
  /013 T17 组全复绿（护栏改道与光标应用零误伤）。
- **bench**：assert 重放 l2 修正复验+proxy l0 回归+JSONL 改源双录。
- **vue 轨**：strict gen+pnpm build 双 exit 0（供⑤后）。

## 7. 验收标准

- **AC-01 跳转列表**：T-00① 三路裁定成文且按裁定形落地（(a)=零改
  动实测记录+SD-03 注记/(b)=shim 消费后打开文件进壳 Recent——探
  针/手工双轨）。验证：探针退出码+§10 决策记录。
- **AC-02 化妆件**：l2 results 文件 `bench.py assert` 重放无误导
  「缺：not-armed」行（行序取自记录 mode）；F-02 勘定记录在案。
  验证：assert 输出+bench check 绿。
- **AC-03 save 解禁**：big 态 save 走直写端点落盘（50MB E2E 磁盘字
  节对+时长量级改善记录）；readonly 兜底/normal 态零扰动；护栏提
  示退役。验证：矩阵 T18+回归组。
- **AC-04 光标恢复**：会话恢复后 line/col=会话持久值（矩阵 state
  断言）；scroll 按 SD-02 条件形。验证：矩阵 T18。
- **AC-05 time 族**（条件供④）：bench JSONL 毫秒值=app 内来源（
  host 时间戳降对照列）。验证：JSONL 字段+proxy l0。
- **AC-06 vue strict**（条件供⑤）：strict gen exit 0+pnpm build
  exit 0；缓解件退役判定成文。验证：构建退出码。
- **AC-07 口径与收口**：F-RV6 评估成文（条件供③）；矩阵 T18 完成态
  ≥117+M/0 判绿（M 实落，README 同步）；SD-01..04 在册（条件形按
  实落）；upstream §17 消费核销在档。验证：矩阵退出码+README grep
  +grep 册。

## 8. 执行步骤

| 步 | 任务 | 依赖 | 产出/验证 |
|---|---|---|---|
| 1 | T-01 跳转列表勘定（三路裁定） | 无（段一） | §10 决策记录；探针 exit 0 |
| 2 | T-02 跳转列表实施（条件裁定形） | T-01 | 裁定形落地/改道供料段 |
| 3 | T-03 bench 化妆件（F-01 修+F-02 勘定） | 无（段一） | assert 重放复验 |
| 4 | T-04 端点消费探针 | **供①②delivered** | §10 决策记录；探针 exit 0 |
| 5 | T-05 save 护栏解禁 | T-04 | 矩阵 big save E2E |
| 6 | T-06 光标恢复启用 | T-04 | 矩阵 line/col 断言 |
| 7 | T-07 time 族改接 | 供④ | JSONL 改源 |
| 8 | T-08 vue strict 复验+退役判定 | 供⑤ | 双 exit 0 |
| 9 | T-09 F-RV6 口径重定评估 | 供③ | 五轮谱+条款退役评估 |
| 10 | T-10 矩阵 T18+README 口径 | T-05/T-06 | ≥117+M/0 |
| 11 | T-11 规范落账+upstream §17 | T-10 | grep+构建退出码 |

（段一 T-01..T-03 可先行不待供料；段二任务随对应供料件 delivered
逐个解锁——T-05/T-06 可并行；worktree 纪律照旧——专用组 worktree
`.wt/plan-014/auto-edit`，主检出零落盘；钉版纪律——供料件落地后
工具链必换版，判据前核 `auto --version`+重建钉版件。）

## 9. 复审记录

- **2026-09-24 stage: new（r1，drafting → 预备交接）**：用户指令形态
  A 双子计划（跨仓打包——供料件 auto-lang 立号+本消费件 014）。背
  景实勘：M2 验收面四件全 delivered 后尾债三族（本仓小件/上游门控/
  M4 门控）——本件收前两族的可消费面；跳转列表内核零 shell 面（
  grep 实勘）+三路裁定落 T-00①；F-02 已消失（bench.py 实勘无命中
  ——006 挂账部分被后续改造吸收，诚实勘定）；F-01 在案（stage_assert
  :765/_print_budget_table:400 代码锚核对）。供料回执五件契约预记
  （§5 表——T-00② 探针复核门+漂移回 new）。段一/段二分界+逐供件
  解锁形（执行步骤表）。四 SD（三条件形）。**执行分段授权**：段一
  无前置；段二前置=供料件 delivered。outcome: pass（授权=预起草；
  段一可启动 auto-plan-work；供料件立项在 auto-lang 仓待用户启动
  auto-plan-new）。next: work（段一）/ 供料件立项（auto-lang 仓）。

## 10. 待澄清事项

- **Q-1 跳转列表裁定**（T-01）：(a) 壳自动 Recent 已备度实测为准；
  (b) SHAddToRecentDocs shim=供料段扩件（**G-1 部分改道=范围缩减
  须用户确认**——skill 禁静默缩界）；custom 类非目标成文。
- **Q-2 save 解禁语义边界**（T-04②/T-05）：normal 态 v1 维持现链
  （本件预记）还是随直写端点一并迁移（上游件形态而定）——T-00②
  勘定后成文；bom/eol 包装归属（front 保留 vs 端点侧承载）随勘定。
- **Q-3 scroll 恢复的会话契约扩展**（T-06/SD-02）：会话 JSON 增
  per-tab scroll 字段=010 契约变更（SD-02 modify 覆盖）——供② 写
  端点不落地则维持「滚动不恢复」注记，Q 明记不阻塞。
