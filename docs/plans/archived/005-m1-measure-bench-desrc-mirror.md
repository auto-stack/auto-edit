---
plan_id: PLAN-005
status: archived
feature_name: M1 性能轨③测量体系 + 去 src 镜像先行段
author: [agent]
created_at: 2026-09-21T05:22:29Z
updated_at: 2026-09-21T07:40:00Z
plan_revision: 1
current_step: 7
completion_kind: delivered
total_steps: 7
supersedes_spec_components: []
new_spec_components: []
touched_goals: [M1-性能轨③-测量体系, M1-并行件-去src镜像先行段]
---

# PLAN-005：M1 性能轨③测量体系 + 去 src 镜像先行段

战略依据：`docs/strategy/002-north-star-v2.md` §6 M1 行四步序的 **③ 建立测量
体系**（bench + 阶段插桩 + 预算断言；①② 已由 PLAN-004 交付）+ M1 并行件
**去 src 镜像先行段**（§4.3 写路径重构的先行小件）。两件均不被上游阻塞
（L2 测量**运行**被供料 §6/§7 阻，但测量**体系**本身的建设不被阻——
blocked 段以归因显性化对冲，与 PLAN-004 perf.py 同法）。

## 0. 变更摘要

两段一件：

- **A 段（去 src 镜像先行段）**：删 `editor_store.at` 五处编辑路径全量回读
  （cut/paste/undo/redo/ctx-cut 后的 `code_editor_text()` 写回镜像），store 的
  `tabs[i].src` 收敛为其头注已声明的"初值/外部重置"单一语义；矩阵 T6 的
  正文断言通道从 `src_active` 镜像迁移到 **save 路径 E2E**（触发保存→读盘
  比对，断言面反而更强）。save 位两处全量读保留（落盘本需全文，过渡形态
  直至上游 delta/分块供料）。
- **B 段（测量体系）**：`tools/bench/` 测量套件——阶段插桩（`AUTO_BENCH`
  环境门控的 BENCH 标记行，`time.now_ms()` 时间戳）、启动链分解 N 跑、
  打开文件计时（1/10/100/512 MB fixture）、内存采样、代理指标静态检查
  （编辑路径全量读检测——A 段即其首个绿证）、预算断言（战略 §2.1 全表
  落 `budgets.json`，两档门禁：硬门禁仅 L2 生效，L0 报告逐指标显式状态
  标注，杜绝静默缺席与 L0 数字误判）。首跑 L0 proxy 基线入仓追踪
  ——**不是** ④ 的 L2 基线报告（④ 另立，待上游解阻）。

## 1. 目标

1. **编辑路径去镜像**：`code_editor_text()` 在 editor_store 仅存两个 save
   调用位；编辑后 store 不再持有全文镜像。行为零变化（last_external
   no-op 语义本就覆盖——现状 typed 输入从不镜像，回读仅覆盖 cut/paste/
   undo/redo 四操作，删除即对齐）。矩阵全绿 + vue 构建绿双轨复验。
2. **阶段插桩**：app 侧 env 门控标记行（进程内逻辑阶段：init/ws 装载/
   文件打开），host 侧进程级观测（spawn 计时/内存采样）——全部独立于
   desktop_mcp/MCP 链（战略 §5：绕开 F-RV6 非确定）。
3. **bench 套件**：`python tools/bench/bench.py` 一条命令出 L0 proxy
   报告（启动链分解 + 打开计时 + 内存 + 断言状态表），结果 JSONL 入仓；
   `--mode l1/l2` 接 perf.py 编排，blocked 段归因退出码 3。
4. **预算断言**：战略 §2.1 预算表全部 10 行进 `budgets.json`，每行带
   tier（hard/ledger）与解锁条件；断言报告每行显式终态
   （not-armed@L0 / arch-blocked-until-rope / blocked-upstream /
   pending-M2/M3-feature / ledger-recorded），无静默跳过。

### 非目标

- **④ 首份 L2 基线报告**——L2 运行被供料 §6（RQ 渲染臂 codeeditor 覆盖）
  /§7（a2r 词汇门）阻塞；体系建成后 ④ 是"解阻即跑"的后续计划。
- **store 完全去文本化**（buffer 句柄/统一 delta/分块读）——上游 rope/delta
  供料（供料包 §1–§3）后的 M1 主计划；本计划只删镜像回读这一先行小件。
- 任何性能优化本身；键入到上屏/滚动帧率的实测（需内核帧时间戳插桩，
  上游小供料，战略 §2.1 已登记——本计划只留断言槽位标 blocked）。
- desktop_mcp.py 的 F-RV6 早崩修复（上游 §5）；矩阵结构性改版。
- 上游仓 auto-lang 的任何修改。
- 公开对比表——L0/L1 数字永不入公开对比面（战略 §5 硬规）。

## 2. 架构方案

- **A 段是纯删除，不是重构**：editor_store 头注（L24–26）与 Plan 420 P1
  设计本就声明 `src 仅作初值/外部重置（last_external 相等即 no-op）`；五处
  回读是违例残留。模板 `content: t.src`（app.at L174）重喂 stale 初值 ==
  last_external → no-op，编辑器内部文本不丢（该机制现状每日被行使——
  `SrcChanged` 从不镜像，typed 输入全靠它）。矩阵断言依赖回写（T6 注释
  L384–388 自认"模型重同步依赖 code_editor_text() 写回"）→ 断言通道迁移
  save E2E，模型不再需要重同步。
- **B 段与 tools/perf 同族分层**：perf.py=模式**切换**编排（L2 机构），
  bench.py=测量**套件**（跑数与断言）；`bench --mode l2` 复用 perf.py 阶段
  （rq-up/release/run），不复制实现。退出码沿用 0/3/1 约定。
- **双观测面，零 MCP 依赖**：①host 面——进程 spawn 计时、stdout 落文件
  （PLAN-003 坑位：禁管道直读）、内存采样（psutil 优先，PowerShell
  `Get-Process` 回退，方法记入结果）；②app 面——`AUTO_BENCH=1` 门控的
  BENCH 标记行（`time.now_ms()` 自记时间戳，console_log → stdout 落文件）。
  VM time 原生在位（auto-lang `vm/codegen.rs` `auto.time.now_ms` 映射，
  examples/a2rs/03_image_scraper.at 先例；import 形态 T-03 实测落账）。
- **插桩零常态成本**：未设 AUTO_BENCH = 零行为差异（矩阵回归保证）；
  不新增 back 端点（env_str 已有；标记走 console_log，不写盘）。
- **断言语义先于数字**：预算效力只在 L2（战略 §5 阶梯）；L0 报告的价值
  = 启动链**形状**分解 + 结构回归代理（全量读检测）+ 缓冲区类基线记账
  （rope 前架构阻塞，禁调优，只记基线——战略补注 6(a)）。
- **结果入仓追踪**：`tools/bench/results/*.jsonl`（每跑一文件：环境指纹+
  逐指标数) + `baseline-L0-<date>.md` 摘要；fixtures（≤512 MB）gitignored。

## 3. 技术栈

Python 3（标准库为主；requests 已是矩阵前置；psutil 可选——缺席回退
PowerShell）；`auto` CLI（≥1631，沿 perf.py `MIN_TOOLCHAIN_BUILD` 门）；
Git Bash 执行环境；Windows-only（进程面同 perf.py）。

## 4. 需求分析与背景调查

**授权**：用户 2026-09-21 会话指定本计划立项（"PLAN-005 候选——③测量体系
+ 去 src 镜像先行段……先把这个测量体系规划计划吧"）——**起草已授权**；
执行授权待 work 接手前由用户给出。仓库/操作范围 = 本仓
`specs/auto-edit/`（app 源+tests+scripts）、`tools/bench/`（新增）、
`docs/`（计划+供料包注记）、README 规范增量。无预算限制约定；无自动
延续限制。

**Spec 状态**：本仓无 `docs/specs/`；canonical 模块 Spec =
`specs/auto-edit/README.md`（PROVENANCE 管理）。账本 `.autoos/specs.json`
为派生索引（merge 期事务，本计划不动）。

**代码/事实证据**（均已实读，行号为当前 main@fdc92aa）：

- 镜像位五处：`editor_store.at` L229（.CtxCut）/L350（.ActUndo）/L359
  （.ActRedo）/L376（.ActCut）/L393（.ActPaste）——模式统一为
  `.tabs[.tab].src = code_editor_text(.active_key)` + `.src_active` 联动行；
  save 位两处：L338（.ActSave）/L492（.QuitSaveClose）——保留。
- 头注 L24–26 已声明目标语义（src 仅初值/外部重置）——回读与其自相矛盾。
- 模板绑定：`app.at` L171–180，激活 tab 的 `code_editor` `content: t.src`。
- 矩阵依赖面：`tests/desktop_mcp.py` L384–400（T6 src_active 断言通道与
  "模型重同步依赖写回"自认）+ L427–452（cut/undo/redo/copy/cut/paste 八条
  正文断言）；L535–543（T9.2 开 tab 断言读 src_active——**创建时设置，不
  受本变更影响**）。`src_active` 无 UI 消费者（status_bar/console_panel/
  ctx_menu 零命中，rg 实证）。
- vue 轨：`code_editor_*` 读回族本就是 vue 运行期缺口（README Concepts
  vue 节，ts_adapter 仅补类型声明）——删回读只减不加，构建绿不受威胁。
- time 原生：auto-lang `crates/auto-lang/src/vm/codegen.rs` 存在
  `auto.time.now_ms/now_sec/sleep_ms` 映射；调用先例
  `examples/a2rs/03_image_scraper.at`（`time.now_ms()`）。
- perf.py 约定（bench 沿用）：退出码 0/3/1；输出落 `tools/perf/logs/`；
  `PERF_PROJECT` 锚主检出；rqhost 按 PID 收（`taskkill //IM auto.exe` 连坐
  坑）；工具链构建号门。
- 上游阻塞现状（PLAN-004 终局登记，供料包 `docs/upstream/2026-09-m1-supply.md`）：
  L1 的 RQ 面=§6；L2 主形态 a2r=§7；F-R1=§4（只阻 `--server rust`）；
  F-RV6=§5。**③体系建设对四者零依赖**（L0 面 VM+merged 全可达）。
- 战略条款：§5 性能文化（bench 清单/两档门禁/模式阶梯/代理指标三件：
  阶段时间戳插桩、编辑路径全量读检测、分配计数）；§2.1 预算表 10 行+
  解锁条件列；补注 6(a) rope 前禁调优、只记基线标"架构阻塞"。

**执行环境坑位**（沿 PLAN-003/004 实勘，work 执行者必读）：

- Git Bash `timeout` 杀 .bat/cmd 壳留 auto.exe 孤儿（占端口）——bench 每
  轮按 PID 收；与 rqhost PID 收编区分。
- auto.exe stdout 重定向管道会塞满阻塞——一律落文件。
- 工具链 mtime 核对（陈旧重建，增量 ~2min）。
- 本机 grep 为 ugrep，字符类过滤失灵——脚本内过滤用盘符锚（`^D:`）。

## 5. 详细设计

### 5.1 A 段：去镜像（T-01/T-02）

删除五处（L229/L350/L359/L376/L393）的
`.tabs[.tab].src = code_editor_text(.active_key)` 与紧随的
`.src_active = .tabs[.tab].src` 两行；各 handler 保留：内建调用
（cut/paste/undo/redo 本体）、dirty 置位（cut/paste 位）、console_log。
头注 L24–26 补一句"PLAN-005 起编辑态不回写；全文只在 save 位读出"。
`.src_active` 语义降格为"激活 tab 初值镜像"（TabActivate/ActSwitchTab/
开 tab 的赋值保留——它们读的是 tabs[i].src 本值，非实时编辑态）。

矩阵 T6 迁移（desktop_mcp.py L384–455 区段）：`src_now()` 改为
save-then-read——`toolbar("save")`（icon "save" 在 toolbar 声明中）触发
ActSave → 读 `AUTO_SAVE_PATH` 文件内容比对。映射：cut→save→断言空；
undo→save→断言 marker 在；redo→save→断言空；undo(2)→save→marker；
copy（无文本变化，保留 console 断言）；cut(2)→save→空；paste→save→
marker。starter tab path="" → ActSave 走 AUTO_SAVE_PATH 旁路（既有
Plan 420 P2 机制），首存后 path_active 持久指向该文件，续存覆盖即可。
T6 头注释（"模型重同步依赖写回"）随之改写为 save E2E 语义。

### 5.2 B 段：观测通道实勘（T-03 → `tools/bench/README.md`）

四问勘毕落探针矩阵表（指标 × 模式 × 观测通道 × 状态），PLAN-004 T-02
同法：

1. time import 形态实测（`use time` 模块限定 vs 裸函数；vue 轨是否在
   拦截面——bench 只服务 vm/a2r 轨，记录即可）。
2. **首帧观测通道**：.at 层有无首帧/首渲染后生命周期钩子（候选：Tick
   首拍、渲染器回调、快照"(rendered)"机制的非 MCP 等价物）。勘得=插桩
   阶段加 first_frame；勘无=预算表该行标 blocked-upstream（内核帧时间戳
   插桩小供料，战略 §2.1 已登记），供料包追加一句注记（docs 增量）。
3. 内存采样法：psutil 在位性实测；回退 PowerShell `Get-Process
   -Id <pid>` 采样（WorkingSet）；方法名记入结果 JSON。
4. fixture 与磁盘预算：1/10/100/512 MB 生成耗时/占用实测；默认集与
   `--full` 集裁定（512 MB 非默认）。

### 5.3 阶段插桩（T-04）

`AUTO_BENCH=1`（env_str 门控）时输出 BENCH 行（console_log → stdout 落
文件，格式 `BENCH <stage> <now_ms>`）：

- `bench_vm_init`——store 首个 handler 入口（LoadWorkspace 开头）；
- `bench_ws_loaded`——LoadWorkspace 尾（树装载完）；
- `bench_open_start`/`bench_open_done`——ConsumeOpen 内 read_text 包夹
  （打开文件计时；AUTO_OPEN_PATH 路径即 bench fixture 挂载点）；
- 首帧阶段按 T-03 结论增补或登记 blocked。

未设 env = 这些行一个不多（分支不进）。host 侧 spawn t0 与 app 侧
now_ms 首行差 ≈ spawn→init（跨进程时钟同机可比）；app 内各阶段差为
纯 app 时钟，精确。

### 5.4 bench.py（T-05/T-06）

```
python tools/bench/bench.py <cmd> [--mode l0|l1|l2] [--runs N] [--full]
  proxy    L0 套件：fixture 生成 → N 跑启动分解（弃首跑暖机）→ 打开
           计时（默认 1/10/100 MB；--full 含 512）→ 内存采样 →
           代理静态检查 → 断言报告 → results/<ts>.jsonl + 摘要
  assert   仅预算断言（对既有 results 文件或现场跑数）
  check    依赖自检 + 环境指纹（perf.py check 同族）
```

- `--mode l1/l2`：l1=VM+RQ（供料 §6 blocked→exit 3 归因）；l2=经 perf.py
  a2r/release/rq-up 链（§7/§6 blocked→exit 3）。断言 tier=hard 的指标
  仅在 l2 完整跑通时评估，否则整行标 not-armed 并归因。
- `budgets.json`：战略 §2.1 全 10 行（稳态启动 80ms/渲染器冷启动单列/
  热启动 120ms/100MB≤1s/1GB 可打开/键入≤16ms/滚动满帧率/diff 100MB≤2s/
  空闲内存 60MB/安装包 15MB），每行 `{metric, budget, tier, validity,
  unlock}`；L0 断言报告逐行输出终态，五类：`not-armed`（硬门禁遇非 L2）/
  `arch-blocked`（缓冲区类，rope 前——只记基线）/`blocked-upstream`
  （键入/滚动需内核插桩；diff 需 M3 引擎）/`pending-feature`（热启动需
  M2 会话恢复）/`ledger`（记账不阻塞）。
- 代理静态检查（全量读检测）：扫 `src/front/*.at`，`code_editor_text`
  允许位=editor_store 的 save 上下文（白名单行锚），编辑 handler 上下文
  出现即红——A 段即其绿证；构造性红证=喂含镜像形态样例断言判红。
  分配计数：T-03 勘 VM 层可达性（无通道则 README 登记暂缺，不硬造）。

### 5.5 结果追踪与规范落账（T-07）

`tools/bench/results/`（入仓）：`<ts>.jsonl`（环境指纹+逐指标+终态）+
`baseline-L0-<date>.md`（首跑摘要表：启动链分解各阶段均值/分布、打开
计时、内存、断言状态全表）。README 增量见规范增量表。

### 规范增量

| delta_id | add/modify/retire | docs/specs/... target | before/after rule | rationale | acceptance IDs |
|---|---|---|---|---|---|
| SD-01 | modify | specs/auto-edit/README.md（Concepts · store 节） | before：未言 src 镜像细节（回读违例与头注矛盾不可见）；after：明文 `tabs[i].src` 仅初值/外部重置，编辑态不回写（PLAN-005 起五处回读删除），全文读出仅 save 位（过渡形态，上游 delta 后收口）；矩阵正文断言走 save 路径 E2E | store 数据语义是 spec 级事实；去镜像后语义与代码一致须固化，防回读回归 | AC-01/07 |
| SD-02 | modify | specs/auto-edit/README.md（How to Run · 性能模式节后） | before：仅 tools/perf 节；after：增 `tools/bench/` 用法（proxy/assert/check、`--mode` 阶梯效力引用、结果追踪口径、fixtures gitignored 注记） | 测量体系是 canonical 运行面，命令须可复制执行 | AC-05/06/08 |
| SD-03 | modify | specs/auto-edit/README.md（Tests 节） | before：矩阵口径无断言通道说明；after：补一句"T6 正文断言走 save E2E（PLAN-005 起，src_active 不再实时）" | 矩阵读者须知道正文断言验的是真实写路径 | AC-01 |

（`tools/bench/` 为新增工具目录，不属 specs 面——PLAN-004 tools/perf 同款
裁定。）

## 6. 测试设计

- A 段回归：全矩阵（README 口径完成态 ≥49/0；F-RV6 早崩重跑条款沿 PLAN-004
  附表 A）+ `regen_vue.py --build` exit 0 + grep 证据（镜像形态零残留）。
- T6 迁移自证：迁移后矩阵 T6 八条正文断言逐条过（save E2E 通道）。
- 插桩无扰动：同树 AUTO_BENCH 未设矩阵绿；设=stdout 文件含 BENCH 行且
  矩阵行为同（BENCH 行只在 console 面板多行文本，不影响断言——T-04 验证
  并在必要时调断言过滤）。
- bench 端到端：`bench.py proxy` exit 0，JSONL 可解析、字段齐（指纹/阶段/
  指标/终态）；`--mode l2` exit 3 + 归因打印（构造性验证沿 PLAN-004
  smoke 法）。
- 断言语义自证：L0 报告中 hard 指标全部 not-armed（无一误判绿/红）；
  budgets.json 行数 == 战略 §2.1 行数（10）。
- 静态检查构造性红证：镜像样例判红。

## 7. 验收标准

- **AC-01** 五处镜像回读删除：`rg -F "code_editor_text" editor_store.at`
  仅剩 ActSave（L338 位）与 QuitSaveClose（L492 位）两个 save 上下文；
  迁移后全矩阵完成态 ≥49/0（§9 收据：跑次分布表）。
- **AC-02** vue 双轨构建绿：`python scripts/regen_vue.py --build` 退出码 0
  （收据入 §9）。
- **AC-03** `tools/bench/README.md` 探针矩阵表四列齐（指标×模式×观测通道×
  状态），T-03 四问全答、无"未知"残留。
- **AC-04** 插桩门控：AUTO_BENCH 未设=矩阵绿零扰动；设=stdout 落文件含
  `BENCH <stage> <now_ms>` 行且阶段集与 §5.3 一致（+首帧或其 blocked
  登记）。
- **AC-05** `bench.py proxy` 端到端 exit 0：≥5 跑启动分解（含弃暖机注记）
  + 默认 fixture 集打开计时 + 内存采样（方法记录）+ `results/*.jsonl`
  入仓且可解析。
- **AC-06** 预算断言：`budgets.json` 覆盖战略 §2.1 全 10 行；L0 断言报告
  逐行显式终态（五类之一），无静默缺席；hard 指标在 L0 全 not-armed；
  `--mode l2` 下 blocked 指标归因 exit 3。
- **AC-07** 全量读代理检测在位：对当前树绿 + 构造性红证双收据；检测结果
  进 proxy 报告。
- **AC-08** 规范增量 SD-01/02/03 落盘，README bench 命令可复制执行；
  L0 proxy 首跑基线摘要（`baseline-L0-*.md`）入仓。

## 8. 执行步骤

| ID | 任务 | 依赖 | 产出/意图 | AC | 验证 |
|---|---|---|---|---|---|
| T-01 | 删五处镜像回读 + 语义注释对齐 | — | editor_store.at：五处两行删除、头注补记、src_active 降格注记 | AC-01 | grep 仅存两 save 位；编译过（auto run -r vm 起窗冒烟） |
| T-02 | 矩阵 T6 迁移 save E2E + 双轨复验 | T-01 | desktop_mcp.py T6 通道改写 + 头注；全矩阵 + vue build 收据 | AC-01/02 | 矩阵完成态 ≥49/0；regen_vue --build exit 0 |
| T-03 | 观测通道实勘 | —（与 A 段并行） | tools/bench/README.md 探针矩阵（四问全答） | AC-03 | 表无"未知"；首帧通道勘得或 blocked 登记二选一落账 |
| T-04 | AUTO_BENCH 门控阶段插桩 | T-03 | editor_store/app BENCH 行（§5.3 阶段集） | AC-04 | 双态验证：未设矩阵绿；设=BENCH 行齐 |
| T-05 | bench.py 核心（L0 套件 + 模式门控） | T-03/T-04 | fixtures/启动分解/打开计时/内存/JSONL/--mode l1l2 exit 3 | AC-05 | proxy 端到端 exit 0；l2 构造性 exit 3 |
| T-06 | 预算断言 + 代理静态检查 | T-05 + T-01（树须已去镜像） | budgets.json + 断言报告 + 全量读检测（含红证） | AC-06/07 | §2.1 行数核对；五类终态齐；红证收据 |
| T-07 | L0 基线首跑 + 规范落账 + 收口自检 | T-01..T-06 | results/ 首跑 + baseline 摘要 + SD-01..03 + AC 逐条复核 | AC-08 | README 命令复制执行绿；§9 终局记录 |

### 执行收据（r1，2026-09-21，base fdc92aa → plan-005-dev 4e1a576/1e53889/ade6e73/73d07b5 + merge 8a5ab1c/3123c50）

> **主检出并行变更对账**：执行期另一会话在 main 落 d845e54（vue671
> 复跑收口：七类补件链退役，regen_vue.py 退化 strict 裸生成 wrapper）。
> 已 merge 进本分支（8a5ab1c，regen_vue.py 冲突取退役版基底）；本分支
> 原补件③在场守卫随生成器原生内联作废；⑧print 遮蔽在新世界复现（同
> 四 TS2339）→ 以**单行外科缓解**重落地（3123c50：store 生成物
> console.log→globalThis.console.log，幂等守卫；生成器硬编码缺口非七类
> 已吸收补件，供料 §9 登记）。**合并对 vm 轨面零改动**（git diff
> 73d07b5..HEAD 仅 regen_vue.py/README/供料 docs）——vm 轨证据不失效；
> vue 面直接复验 exit 0。

- **T-01 [x]**：五处（CtxCut/ActUndo/ActRedo/ActCut/ActPaste）两行删除；头注
  补"PLAN-005 起编辑态不回写"；src_active 降格注记落声明位。收据：
  `rg -F "code_editor_text" editor_store.at` 仅剩 ActSave（L367）+
  QuitSaveClose（L513）两个 write_text save 位；`auto run -r vm` 起窗
  冒烟 9s+ 零 error/panic（1652 工具链，PID 树收编）。
- **T-02 [x]**：T6 `src_now()` 改 save-then-read（toolbar("save") →
  "saved:" console 计数轮询确认落盘 → 读 AUTO_SAVE_PATH）；T9 前重置
  roundtrip 文件保 marker 隔离（修复迁移引入的空串 IndexError 脆性）。
  矩阵跑次分布（1652 工具链，AUTO_BIN=debug auto.exe）：**50/0×2**
  （run2/run7）+ 39/9（run1 首轮冷降级：菜单快照失联+save 读取竞态，
  加固前形态）+ 49/1（run3/run5：paste 轮转 flake）+ 无 RESULT×2
  （run4/run6 早崩，按 README 基线条款重跑）。**非回归定谳**：基线
  原码（主检出 fdc92aa）同工具链同形（base1 早崩@12 PASS 无 RESULT、
  base2 50/0）；paste flake 机制定谳 = `code_editor_paste` 内
  `clipboard_get()` 瞬态失败静默 no-op（arboard 争用，返回 Bool 不报
  剪贴板成败——供料包 §9 已登记）。**合并后补验**（vm 轨代码与证据轮
  字节级一致，diff 证）：会话末段机况退化（今日 30+ 实例spawn、并行
  会话争用、两度 T9 泄漏孤儿清编）出现五连早崩（run8-12，死亡点散布
  T2-T6，app 日志尾=正常 Tick 无错截断=F-RV6 静默死签名）——按盲重试
  上限停试，证据效力以代码同一性论证 + 基线对照承载；复审可在静置
  机器上重定。vue build：首跑红（TS2339 print→
  console.log 与 store `console` 字段遮蔽 + TS2393 toggle_id 重复——
  后者为 1652 生成器 vs 补件漂移，主检出同红）→ 补件③在场守卫 + ⑧
  globalThis 改写后 **exit 0**；合并 d845e54 退役链后 ⑧ 以单行缓解
  重落地复验 **exit 0**（3123c50）。
- **T-03 [x]**：四问全答落 `tools/bench/README.md` 探针矩阵（四列齐，
  无"未知"）。① time 形态：VM 轨 time 族目录登记无运行时 shim，裸/
  use 两形态均返 0（探针 A/B），Instant.elapsed 返回约定坏（探针 C），
  实装仅在 a2r-std；② 首帧：勘无（生命周期仅 Init/Tick/CloseRequest，
  call_handler 全枚举）→ blocked-upstream 登记 + 供料包 §9 注记；③
  内存：psutil 缺席 → PowerShell WorkingSet64 实测成功；④ fixture：
  1/10/100MB 生成 0/0.01/0.15s，默认集裁定成立。
- **T-04 [x]**：**语义修订（证据支撑）**——§5.3 的 app 侧 now_ms 通道
  因 VM 轨 time 族未接线不可行，BENCH 行改裸 `<stage>`（print→stdout
  落文件，不进 console 面板故矩阵断言零扰动），毫秒值 host 侧记
  （JSONL markers 字段）；ConsumeOpen 增 AUTO_BENCH 门控的
  AUTO_OPEN_PATH 播种（bench 免 UI 触发挂载，未设门零行为差异）。
  双态验证：未设=矩阵绿（多轮全程未设）；设=四标记齐（实测 0.858/
  0.860/6.330/6.448s——spawn→init、init→ws、open 包夹）。
- **T-05 [x]**：bench.py 三命令（check/proxy/assert）。proxy 端到端
  **exit 0**：5 跑弃暖机（spawn→init 287–534ms、init→ws<25ms 轮询粒度）
  + 打开计时（1/10/100MB = 26/26/460ms，内存 230/251/521MB——整串
  镜像线性放大直接证据）+ 内存采样（方法记入 JSONL）+ JSONL 落
  results/ 可解析。`--mode l1` exit 3（perf smoke 归因 §6）；`--mode l2`
  exit 3（perf a2r 归因 §7 PLAN-027 词汇门，与主检出基线同因同形；
  首跑冷编译无诊断死为瞬态，复跑即分类正常）。
- **T-06 [x]**：budgets.json 战略 §2.1 全 10 行（{metric,budget,tier,
  validity,unlock}）；L0 断言报告逐行终态五类齐（not-armed×2/
  pending-feature×2/arch-blocked×2/blocked-upstream×3/ledger×1），hard
  行在 L0 全 not-armed；全量读检测当前树 green（允许位=两 save 位）
  + 构造性红证自检 PASS（bench check 内置样例：ActCut 位与非 store
  位判红、ActSave 位不误报）。
- **T-07 [x]**：`results/baseline-L0-20260921.md` 首跑摘要入仓（启动链
  形状/打开计时/内存/检测/终态全表）；SD-01/02/03 落 canonical README
  （Concepts store 节 src 语义 / How to Run 测量套件节 / Tests T6 save
  E2E 注）；README 命令复制执行三连绿（check/proxy/assert exit 0）。

### AC 终局对照

| AC | 终态 | 关键收据 |
|---|---|---|
| AC-01 | ✅ | rg 仅两 save 位；矩阵 50/0×2（分布与基线对照见 T-02） |
| AC-02 | ✅ | regen_vue --build exit 0（补件③⑧后） |
| AC-03 | ✅ | 探针矩阵四列齐，四问全答无"未知" |
| AC-04 | ✅ | 双态验证过；阶段集=§5.3 四标记+首帧 blocked 登记（行格式语义修订见 T-04 收据） |
| AC-05 | ✅ | proxy exit 0；JSONL 入仓可解析；≥5 跑弃暖机 |
| AC-06 | ✅ | 10 行全；五类终态齐；hard 全 not-armed；l2 exit 3 归因 |
| AC-07 | ✅ | 当前树 green + 红证自检 PASS；结果进 proxy 报告 |
| AC-08 | ✅ | SD-01..03 落盘；命令复制执行绿；baseline md 入仓 |

并行性：A 段（T-01/T-02）与 T-03 互不依赖；T-04 起串行于 T-03。

## 9. 复审记录

- 2026-09-21T05:22:29Z · stage: new · r1 起草 · 授权=用户会话指定立项
  （起草）；执行授权待 work 前。两段范围=A 段去镜像 + B 段测量体系；
  ④ L2 基线报告明确排除（待上游）。next: work（或用户先裁 §10 事项）。
- 2026-09-21T06:45:00Z · stage: work · PLAN-005 · r1 · **pass** ·
  code_commit=plan-005-dev@3123c50（4e1a576 T-01/02/04 + 1e53889
  T-03/05/06 + ade6e73 T-07 + 73d07b5 供料补记 + 8a5ab1c merge main
  d845e54 + 3123c50 print 遮蔽缓解；base=main@fdc92aa，执行期 main
  前移 d845e54 已对账合并）·
  task_ids=T-01..T-07 全 · evidence=AC-01..08 全过（终局对照表见 §8
  执行收据；矩阵 50/0×2 + 基线原码对照定谳非回归 + 合并后 vm 轨代码
  同一性 diff 证；vue build exit 0 双世界[补件链/退役链各验一次]；
  proxy/l1/l2 构造性三连）· blockers=无阻塞级——两项语义修订
  已按证据落账：① BENCH 行改 host 侧毫秒（VM 轨 time 族未接线四探针
  实证，供料包 §9 登记，AC-04 行格式随之）；② 矩阵 paste 轮转随机红
  =上游剪贴板瞬态失败（同 §9 登记，机制分析+基线对照排除本迁移回归）。
  附记：会话末段机况退化五连早崩（run8-12，F-RV6 类），按盲重试上限
  停试——vm 轨证据以代码同一性承载，复审可静置重定。
  worktree=组 edit-005 双树（auto-edit plan-005-dev + auto-lang 兄弟
  @055808724 detached，只读 blueprints 供料）留存待复审 · next: review
  （auto-plan-review，revision-bound r1）。

- 2026-09-21T07:25:00Z · stage: review · PLAN-005 · plan_revision r1 ·
  **pass** · reviewed_commit=3123c5082a9d83258575e2de99af5c47d6bf4a7a ·
  base_commit=fdc92aa（执行期 main 前移 d845e54，已 merge=8a5ab1c，
  merge-base=d845e54=main HEAD）· dependency_revisions=auto-lang 兄弟
  worktree@055808724（detached 只读 bps 供料）+ 工具链 v0.4.2-1652 ·
  spec_inputs=specs/auto-edit/README.md（delta 冻结哈希
  git-hash aa9e0d2ba49f98ce79637ad4a2239ad63191c5e6）·
  acceptance_results=AC-01 pass（含环境附记）/AC-02 pass（复跑瞬态一次）
  /AC-03 pass/AC-04 pass（语义修订版）/AC-05 pass/AC-06 pass/AC-07 pass/
  AC-08 pass · findings=RV-01..RV-05（全非阻塞，见下）· evidence=本
  复审全量重跑取证（同会话内审——独立性受限已在判定中声明，结论自
  工件重建）：①AC-01 grep 复现仅两 save 位（L367/L513）；②矩阵复现=
  复审窗口两轮早崩（21/19 PASS 无 RESULT）+ **基线原码同窗口同形早崩**
  （12 PASS 无 RESULT）——F-RV6 竞态窗口定谳环境归因，完成态门承载=
  执行期 50/0×2 且 vm 轨代码与 HEAD 字节同一（git diff 73d07b5..HEAD
  vm 面零改动实证）；③AC-02 vue 复跑首红（strict 生成对 bps 池 dep
  校验非确定中止，绿跑同 Warning 同过）复跑 exit 0+缓解行发射；④AC-04
  设门态四标记独立复现（vm_init/ws_loaded/open_start/open_done），未设
  门态=矩阵全程；⑤AC-05 proxy 复跑 exit 0+JSONL 解析字段齐（env 七键/
  4 非暖机跑/三尺寸 open+内存+方法名/检测 green/10 行五态/hard 全
  not-armed）；⑥AC-06 budgets=10 行==§2.1、assert 复跑五类齐、l2 复跑
  exit 3 归因；⑦AC-07 check 红证自检 PASS+proxy 树检 green；⑧AC-08
  baseline md+首跑 JSONL 在 HEAD、README 三命令复制执行绿、SD-01..03
  落文与现行行为一致（delta 表 §5 在案）。 · next: merge（auto-plan-merge）。

  **复审 findings（非阻塞，全数登记）：**

  - **RV-01**（语义修订追认）：AC-04 字面 "BENCH <stage> <now_ms>" 落地
    为裸 `<stage>` 行 + host 侧毫秒（JSONL markers 字段）——VM 轨 time
    族未接线四探针实证（§8 T-04 收据），供料 §9 已登记；上游接线后可
    升级 app 侧毫秒。实质验收点（标记在场/阶段集一致/门控零扰动）全过。
  - **RV-02**（环境附记）：矩阵完成态门在本复审窗口不可独立复现——分支
    与基线原码同窗口均早崩（F-RV6 竞态，README 基线条款覆盖）；门证据
    以执行期 50/0×2 + vm 轨代码字节同一性承载。静置机器可重跑定标。
  - **RV-03**（上游债确认）：矩阵 paste 轮转随机红=剪贴板瞬态失败静默
    no-op + 返回 Bool 可观测性缺口（供料 §9 已登记）——非本计划缺陷。
  - **RV-04**（瞬态观察）：vue strict 生成对 bps 池 dep 校验存在非确定
    中止（同输入两跑一红一绿，绿跑同 Warning）——上游池 strictness/
    缓存面观察项，不阻塞。
  - **RV-05**（预存改进项）：desktop_mcp.py T9/T10 子进程收编为直线代码
    非 finally——异常穿越即泄漏孤儿（本日两度清编）；预存形态非本计划
    引入，后续矩阵稳定性小改可顺手收口。

## 10. 待澄清事项

- **执行授权**：work 开工前需用户确认（流程性，非设计歧义）。
- **首帧通道勘无时的供料包动作**（T-03 分支）：若 .at 层无首帧钩子，
  本计划落 blocked-upstream 登记 + 供料包注记一句（docs 小增量，work 期
  自主）；若用户希望正式扩供料包立上游件，另议。默认按前者。
- **fixture 默认集**：默认 1/10/100 MB、`--full` 含 512——磁盘预算执行期
  按 T-03 实测定；若用户有"必须默认全尺寸"的口径，开工前示下。

- 2026-09-21T07:40:00Z · stage: merge · **PLAN-005:r1 归集收据** ·
  outcome=pass（至 archived 四 checkpoint；cleaned 见下条补记）·
  delivery_commit=**31ebb7b**（projection-only descendant of reviewed
  3123c50：账本 P005-1 外科插入 + 复审 proxy JSONL；实现/依赖零改动，
  按 merge 技能限定条款承继复审效力）·
  - **prepared**：canonical delta（SD-01..03）已在 reviewed 提交内
    （ade6e73），冻结哈希 aa9e0d2b 复核未漂移；账本投影在 worktree 落
    （字节级拼接保持原序列化格式，整文件 JSON 解析+五条目序+字段断言
    三验）。
  - **landed**：merge-base=main@d845e54（分支经 8a5ab1c 已含 main，无需
    rebase）→ 主检出 `git merge --ff-only plan-005-dev` 纯快进，main
    tip==31ebb7b，无合并提交；主检出烟测 `bench.py check` 绿（红证自检
    PASS + 构建 1652 门）。（执行注记：一次多余的手动 rebase 调用因合并
    提交拉平重放自找冲突，即时 abort 零影响——分支未动，ff-only 直落。）
  - **ledger_refreshed**：主检出 `.autoos/specs.json` 回读——reviews 段
    P001-1..P005-1 五条目序正确，P005-1 file→本归档路径、title 绑
    3123c50、related=[PLAN-004, PLAN-005]；SD 三处内容 grep 在位。
  - **archived**：本文件 `docs/plans/archived/005-m1-measure-bench-
    desrc-mirror.md`，status=archived + completion_kind=delivered。
  - **cleaned**：待补记（双树 wt-guard → worktree/分支/组目录移除）。
