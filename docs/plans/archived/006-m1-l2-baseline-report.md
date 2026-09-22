---
plan_id: PLAN-006
status: archived
feature_name: m1-l2-baseline-report
author: [zcode]
created_at: 2026-09-22T12:00:00+08:00
updated_at: 2026-09-22T12:50:00+08:00
plan_revision: 1
current_step: 5
total_steps: 5
completion_kind: delivered
supersedes_spec_components: []
new_spec_components: [SD-01 bench README L2 测量语义节（armed 断言+产物路径）, SD-02 perf README 模式矩阵解阻回填, SD-03 docs/specs/modules/perf-measurement.md L2 数字面节（并发规范层补建后按 5c95903 新惯例回寄）]
touched_goals: []
---

# [PLAN-006] M1 性能轨 ④：首份 L2 基线报告（bench L2 数字面 + 预算武装断言）

> 来源：战略 `docs/strategy/002-north-star-v2.md` §5 测量模式阶梯（预算与
> 门禁只在 L2 数字上评估）+ §2.1 预算表；PLAN-005 归档裁定 ④ 为"上游
> 解阻即跑"的后续计划（`docs/plans/archived/005-m1-measure-bench-desrc-mirror.md`
> §1 目标外第 1 条）。**解阻信号已到（2026-09-22）**：上游 PLAN-674（§6 RQ
> codeeditor 覆盖）+ PLAN-681（§7 a2r 部署面 + §4 F-R1-B）delivered 后，
> 主检出重建 `1836-gdcbda3f71` 复验 `perf.py a2r` **exit 0**（生成物落
> `specs/auto-edit/rust-workspace`）+ `perf.py smoke` **2/2 存活 exit 0**
> ——M1 四步序的 ①②③ 前提全部就位，④ 是收官件。
> 目标态一句话：**`bench.py proxy --mode l2` 在真实 L2 形态（a2r release
> 产物 + RQ 预热渲染器）下出首份基线数字，steady_start 硬预算武装判定，
> 报告与 JSONL 入仓。**

## 0. 变更摘要

PLAN-005 建成的测量体系里，`--mode l2` 只有**门控**（perf.py a2r→release→
rq-up 链，blocked 时 exit 3 归因）——门控通过后 `stage_proxy` 仍跑 L0 的
VM 形状数字（`bench.py` L436-465：`_startup_runs` spawn 的是 `auto run -r
vm`），预算断言也只输出 `_L0_STATES` 五类终态。本计划补齐 L2 的**数字面**：

1. **L2 运行器**（bench.py）——release 产物直拉（不经 auto.exe 宿主）：
   rqhost 预热后 spawn `rust-workspace/target/release/auto-edit.exe
   --autodesk-rqhost`（隔离 wellknown）+ `AUTO_BENCH=1`，stdout 落文件轮询
   BENCH 标记行，5 跑弃首跑出启动分解；AUTO_OPEN_PATH 出打开计时；
   内存采样（app WorkingSet64 + rqhost 守护单列）。
2. **预算武装断言**——`evaluate_budgets` 增 l2 分支：steady_start（hard
   ≤80ms）武装出数字与判定；renderer_cold_start 单列记录（Q2 待裁）；
   余行带 L2 数字保持记账语义。
3. **首份 L2 基线报告**——`results/baseline-L2-<ts>.md`，与 L0 基线同口径
   升级（形状分解 + L0↔L2 对照 + 断言终态表 + 口径注记），数据 JSONL 入仓。

零应用代码改动：BENCH 标记/AUTO_OPEN_PATH 播种已在 a2r 生成物中原生在位
（实测证据见 §4）；零 auto-lang 改动（上游仓纪律）。

## 1. 目标

1. **L2 真实形态测量**：`python tools/bench/bench.py proxy --mode l2` 端到
   端 exit 0——运行对象为 a2r **release** 产物（非 debug、非 auto.exe 宿主
   的 `auto run`），RQ 渲染器预热在先；产出启动链分解（5 跑弃首跑）、
   打开计时（1/10/100 MB）、内存采样（app 两态 + rqhost 单列）。
2. **预算断言 L2 语义**：战略 §2.1 全 10 行在 L2 模式下逐行显式终态——
   steady_start 由 not-armed 转**武装**（数字 vs ≤80ms 判定 + 代理口径
   注记）；renderer_cold_start 武装记录（单列，预算值待 Q2）；其余行保持
   记账语义但携带 L2 实测数字（rope 前后对照锚点）。
3. **首份 L2 基线报告**：`results/baseline-L2-<ts>.md` 入仓——L0↔L2 对照
   （同一工具链/同机口径注记）、形状结论、断言终态表；L2 数字**不入公开
   对比面**（战略 §5 硬规，报告为仓内文档）。
4. **文档回填**：bench README 探针矩阵 L2 行翻绿（用法 + armed 语义 +
   产物路径）；perf README 模式矩阵 a2r/RQ 行解阻更新 + release 产物
   路径回填（PLAN-004 T-07 遗留的"实跑回填"槽位）。

### 非目标

- **任何性能调优**——首基线是锚点不是门禁事件；steady_start 若超标只做
  归因分解记录（战略补注 6(d)："回归当天修"的硬门禁语义属 M4 门禁生效
  后；调优另立计划）。
- 键入到上屏/滚动帧率实测（内核帧时间戳插桩 blocked-upstream，供料 §9
  在册——断言槽位维持 blocked 标注）。
- buffer 类（open_100mb/1gb）调优——rope 前架构性不可达，禁调优只记
  基线（战略补注 6(a)）。
- desktop_mcp.py / 矩阵面（F-RV6 上游未立件）；vue 轨任何事。
- 上游仓 auto-lang 的任何修改。应用 `.at` 代码修改（标记与播种已在位）。

## 2. 架构方案

- **分层不变**：perf.py = 模式**编排**（L2 机构：a2r 生成/release 编译/
  rqhost 生命周期原语）；bench.py = 测量**套件**（跑数与断言）。L2 门控链
  已在 bench.py `_mode_gate`（L416-431：a2r→release→rq-up，返回 None 即
  "链通，硬门禁武装"）——本计划只补门控通过后的数字面，不改门控语义。
- **release 产物直拉是 L2 的本义**：稳态启动预算的测量对象是"app 实例 +
  预热渲染器"拓扑；`auto run -r rust -q` 会引入 auto.exe 宿主层与可能的
  再生成/工件面漂移（681 R-1 曾实锤 build 路径工件陈旧假阳）。生成物
  main.rs 自带 RQ 客户端旗标（`--autodesk-rqhost` 采纳 / `--autodesk-render`
  三态，main.rs L1190-1236）——bench 直接 Popen release exe，stdout 重定向
  落文件轮询标记（沿 L0 的 `run_app_tracked` 形状，25ms 轮询粒度）。
- **rqhost 生命周期归 bench 会话**：门控段的 perf.py rq-up 已预热隔离
  实例（wellknown 后缀 + `.rq.json` PID 记账）；bench 会话末按 PID 收
  （rq-down 复用 perf.py），不留孤儿（PLAN-003 坑位纪律）。
- **断言两档语义落地**：`_L0_STATES` 的 not-armed 门在 L2 分支中替换为
  武装态——steady_start 出数字与判定（均值 vs ≤80ms）；renderer_cold_start
  出单列数字（rqhost spawn→pipe-ready，perf.py `_pipe_up` 同法）不判（预算
  值 pending-Q2）；arch-blocked/blocked-upstream/ledger 行维持终态但附 L2
  实测数字列（rope 前后对照的锚点价值）。
- **A 段静态检测零改动**：编辑路径全量读检测扫的是 `src/front/*.at` 源面，
  与运行形态无关，L2 跑中原样执行（结构回归守门）。

## 3. 技术栈

- Python 3 stdlib（bench.py 现状：argparse/json/subprocess/pathlib）——
  零新依赖。
- 内存采样：psutil 优先、缺席回退 PowerShell `Get-Process WorkingSet64`
  （方法名记入 JSONL，PLAN-005 既有约定）。
- cargo release 编译经 perf.py release 段（首跑全量 release 树，预计
  数分钟级；产物 `rust-workspace/target/release/auto-edit.exe`，T-00 实锚）。
- Windows-only（命名管道/DETACHED 进程面，沿 perf.py/bench.py 既有约束）。

## 4. 需求分析与背景调查

- **授权记录**：用户 2026-09-22 会话明示"要现在就用 /auto-plan:new 起 ④
  的计划稿"——授权范围 = 起草本计划；执行（work）按惯例另裁。允许动作 =
  auto-edit 仓 `tools/bench/`、`tools/perf/README.md`、`tools/bench/README.md`、
  `docs/`（报告与计划自身）+ gitignored 产物区（rust-workspace/logs/
  fixtures/results 既有口径）。无预算/自动续跑授权。
- **解阻证据链（2026-09-22 本会话实测）**：auto-lang master `dcbda3f71`
  （PLAN-681 五 checkpoint 闭环）后主检出重建 `auto 0.1.0+v0.4.2-1836-
  gdcbda3f71-dirty`；`perf.py a2r` exit 0（`tools/perf/logs/a2r-post681-
  20260922.log`，生成物 `specs/auto-edit/rust-workspace/{Cargo.toml,
  auto-edit/, auto-edit-back/}`）；`perf.py smoke` 2/2 存活 exit 0。中途
  两坑已记：主检出二进制陈旧假阴（重建纪律）+ auto.exe 孤儿锁 target
  写入（os error 5，taskkill 清）。
- **生成物侧三要素实测在位**（无需任何 .at 改动）：
  - BENCH 标记转译存活：`auto-edit/src/main.rs` L695 `println!("BENCH
    bench_vm_init")`、L702 `bench_ws_loaded`、L660 `bench_open_start/done`，
    均由 `env_str("AUTO_BENCH")=="1"` 门控；
  - AUTO_OPEN_PATH 播种存活：L659（ConsumeOpen 转译）；
  - RQ 采纳旗标：L1190-1236 `--autodesk-rqhost`（well-known rendezvous
    采纳）/ `--autodesk-render=queue|auto|independent` / `--autodesk-client=`。
- **现状缺口**：rust-workspace `target/` 仅 `debug/`——release 从未编译
  （perf.py release 段从未绿跑到产物）；bench.py `stage_proxy` 门控后仍
  跑 `_startup_runs`（VM spawn，L352-364）与 `_open_timing` 的 L0 形状；
  `evaluate_budgets`（L286+）无 l2 武装分支。
- **口径依据**：战略 §2.1 表 = `budgets.json` 全 10 行（tier/unlock 列）；
  §5 阶梯与两档门禁；L0 基线范本 `results/baseline-L0-20260921.md`
  （格式/口径注记的直接模板）。
- **specs 面说明**：本仓无 `docs/specs/` 树——工具面规范载体沿 PLAN-004/
  005 先例 = `tools/*/README.md`（账本 `.autoos/specs.json` 沉淀投影）。
  战略文档是用户裁定层，本计划不改。

## 5. 详细设计

### 5.1 L2 运行器（bench.py 新增 `_l2_suite`，stage_proxy 分派）

流程（`--mode l2` 且门控链通后）：

1. 环境指纹（扩字段：release exe 路径+mtime、渲染守护构建形态
   `renderer_daemon_build`、wellknown 隔离名）。
2. 启动分解 5 跑（弃 run1）：Popen `target/release/auto-edit.exe
   --autodesk-rqhost`（旗标组合以 T-00 勘定为准），env 注入
   `AUTO_RQHOST_WELLKNOWN=<隔离>` + `AUTO_BENCH=1`，stdout 落
   `tools/bench/logs/`，轮询标记到达时刻——逐跑记 `spawn→
   bench_vm_init`（进程引导）与 `bench_vm_init→bench_ws_loaded`
   （workspace 装载），**steady_start = spawn→bench_ws_loaded**（代理
   口径，见 §10-1）；`bench_ws_loaded` 后采 app 内存。每跑结束按 PID
   收（窗口关闭语义按 RQ exit-on-EOF：关管道/杀进程树）。
3. 打开计时：每尺寸（1/10/100 MB）fresh 实例 + `AUTO_OPEN_PATH=<fixture>`，
   `bench_open_start/done` 包夹 + 装载后内存。
4. rqhost 单列：spawn→pipe-ready 毫秒（renderer_cold_start 记录）+
   守护进程内存（稳态、N 跑后）。
5. 静态全量读检测（原样）+ 预算断言（l2 语义）+ JSONL 落 results/。
6. 会话末 rq-down（按 `.rq.json` PID）。

### 5.2 预算断言 L2 语义（`evaluate_budgets` l2 分支）

| 行 | l0 终态 | l2 终态（本计划） |
|---|---|---|
| steady_start | not-armed | **armed-hard**：数字（5 跑均值 spawn→ws_loaded）vs ≤80ms 判定 pass/fail；注记=帧通道 blocked-upstream，代理口径 |
| renderer_cold_start | not-armed | **armed-record**：rqhost spawn→pipe-ready 单列数字；预算值 pending-Q2 不判 |
| warm_start | pending-feature | 不变（M2 会话恢复缺席） |
| open_100mb / open_1gb | arch-blocked | 不变 + 附 L2 数字（rope 前锚点） |
| type_latency / scroll_fps | blocked-upstream | 不变（内核帧插桩） |
| diff_100mb | blocked-upstream | 不变（M3） |
| idle_mem | ledger | 不变 + 附 L2 数字（app 实例；rqhost 单列另记） |
| installer | pending-feature | 不变（Q2） |

退出码语义不变：0 绿 / 3 blocked / 1 真失败。armed-hard 的 fail 是**记录
性判定**（首基线锚点 + 归因分解），不触发本计划任何调优动作。

### 5.3 基线报告（`results/baseline-L2-<ts>.md`）

沿 L0 范本结构：口径注记（L2 唯一预算效力/工具链指纹/release 产物/
渲染守护形态/本机多会话并行声明）→ 启动链分解表（含 L0↔L2 对照列）→
打开计时表（对照 L0）→ 内存（app+rqhost 单列）→ 断言终态表（全 10 行）→
形状结论与后续锚点说明（rope/帧插桩/Q2 解锁后何处复测）。

### 5.4 规范增量

| delta_id | add/modify/retire | target | before/after | rationale | AC |
|---|---|---|---|---|---|
| SD-01 | modify | tools/bench/README.md | before：探针矩阵"启动类硬门禁数字 l2 ⛔ blocked-upstream"；after：L2 行翻绿——用法（`proxy --mode l2` 全链）、armed 断言语义表、release 产物路径、rqhost 单列口径 | L2 数字面建成后的工具规范回填 | AC-07 |
| SD-02 | modify | tools/perf/README.md | before：模式矩阵 a2r/VM+RQ 行标 blocked + "产物路径 T-07 实跑回填"槽位；after：解阻实证记录（2026-09-22 双判据绿）+ release 产物路径回填 | PLAN-004 遗留回填 + 解阻状态沉淀 | AC-07 |

（本仓无 docs/specs 树，工具 README 为规范载体——PLAN-004/005 先例；
账本投影走 merge 期外科插入既有流程。）

## 6. 测试设计

- **T-00 勘定件自带验证**：旗标组合试跑须四标记齐（bench_vm_init/
  bench_ws_loaded/bench_open_start/done 到达 stdout 落文件）+ rqhost 侧
  adopt 可观测（`.rq.json`/日志），否则换旗标组合重试（--autodesk-render=
  queue 备选）。
- **L2 运行器**：`proxy --mode l2` exit 0；JSONL 可解析（python json 逐行）；
  每跑两段数字非 None；内存方法字段在档。
- **断言语义**：l2 分支全 10 行终态枚举与 §5.2 表逐行一致（构造性核对：
  评估函数对武装行输出数字与判定字段）；steady 超标分支以实际数字走通
  （记录性 fail 不改退出码语义——exit 0）。
- **进程卫生**：会话末 tasklist 核验无 auto.exe / auto-edit.exe 孤儿；
  复跑（幂等）第二轮 exit 0。
- **回归**：`bench.py check` 绿；`bench.py proxy`（l0 默认）exit 0——L0
  套件零扰动（本计划不碰 L0 路径的行为）。
- **README**：双侧回填后 diff 审读（口径与战略 §5/§2.1 一致）。

## 7. 验收标准

- **AC-01**：`python tools/bench/bench.py proxy --mode l2` 端到端 exit 0，
  运行对象为 release 产物直拉（日志/JSONL 可证：无 `auto run` 宿主层）；
  JSONL 含 5 跑启动分解（弃首跑标记在档）。验证：命令退出码 + JSONL 解析。
- **AC-02**：steady_start 断言武装——state=armed、数字=均值、判定 vs
  ≤80ms 显式、代理口径注记在档。验证：断言表行核对。
- **AC-03**：renderer_cold_start 单列记录（rqhost spawn→pipe-ready 毫秒 +
  守护内存），pending-Q2 注记。验证：JSONL 字段核对。
- **AC-04**：全 10 行断言终态显式且与 §5.2 表逐行一致。验证：断言输出
  对照表核对。
- **AC-05**：`results/baseline-L2-<ts>.md` 入仓，含 L0↔L2 对照与形状
  结论；仓内文档（不入公开对比面）。验证：文件在档 + 结构核对。
- **AC-06**：JSONL 环境指纹含 auto_version/mtime、release exe 路径+mtime、
  renderer_daemon_build 字段。验证：字段核对。
- **AC-07**：bench/perf README 双侧回填（SD-01/SD-02）。验证：diff 审读。
- **AC-08**：进程卫生——会话末 rqhost/app 按 PID 收编，tasklist 无孤儿；
  复跑幂等。验证：tasklist + 第二轮 exit 0。
- **AC-09**：零 `.at` 应用代码改动、零 auto-lang 改动；如 L2 运行器带出
  a2r 转译缺口 → `docs/upstream/` 登记后按 blocked 归因，禁本地补件
  （用户 2026-09-21 裁定）。验证：git diff 范围核对。

## 8. 执行步骤

- **T-00 [✅ 已完成] [勘定]** release 产物与旗标组合实锚：`perf.py release`（首跑
  release 树编译，时长预算数分钟~十分钟级）→ 产物路径实锚；spawn
  `auto-edit.exe --autodesk-rqhost`（隔离 wellknown + AUTO_BENCH=1）四标记
  到达验证；RQ 采纳旗标正确组合裁定（备选 `--autodesk-render=queue`）。
  产出回填本节与 §5.1。→ AC-01 前置
  - 实锚（2026-09-22，worktree edit-006 + PERF_PROJECT 锚主检出）：check
    绿（1836-gdcbda3f71，mtime 11:35）→ a2r 绿（34s 再生成）→ release
    绿（**5m05s 首编**，19 warnings 无碍）→ 产物
    `specs/auto-edit/rust-workspace/target/release/auto-edit.exe`（37.8 MB）。
  - 旗标组合裁定（探针实测，四标记全到达 + 无 NotCovered 降级日志 +
    app 存活 + rq-down 干净）：`--autodesk-launcher --autodesk-rqhost
    --autodesk-broker=<wellknown> --autodesk-render=queue`。**§5.1 修正**：
    client 臂（生成 main.rs L1190-1236 + session.rs spawn_launcher_outproc
    L3818 同形）不读 `AUTO_RQHOST_WELLKNOWN` env（该 env 只被 daemon 读），
    wellknown 经 `--autodesk-broker=` 传参。
  - 首跑形状预告：steady=spawn→ws_loaded≈130ms（vm_init 122.6 主导 +
    ws 7.6）；open 链在 ws_loaded 后 ~1.3s 才到（client↔rqhost 首帧交换
    间隙——代理口径注记的实证：steady 不含首帧）。
- **T-01 [✅ 已完成] [实现]** bench.py L2 运行器（`_l2_suite`：启动分解/打开计时/
  内存/rqhost 单列/进程收编），stage_proxy l2 分派。→ AC-01/03/06/08
  - 实现要点（worktree edit-006）：`_spawn_tracked` 泛化（L0 wrapper 行为
    保持 25ms 轮询零扰动；L2 直拉 release exe 2ms 轮询）+ `_l2_suite`
    分派 + `_rqhost_start`（冷启动计量 + 锁竞态 3 次重试）。
  - **bring-up 三轮实勘固化为协议**（12:03/12:07/12:15 三跑）：①末窗退出
    语义（rqhost.rs D5）下杀 app 即 daemon 自退——批次重拉方案撞两竞态
    （服务环暂空致管道探测假死→重拉撞 `-lock`；probe→spawn 间隙死）；
    ②BENCH 标记先于 adopt 结果打印——死 daemon 上标记照达但窗未建
    （run2-4 无窗 10MB vs 有窗 35-40MB 实证）。终版=**顺设计**：单一
    daemon 服务全序列 + app keep_alive 累积窗口（rqhost 多 app 共享
    合成器本义）+ suite 末统一收编；每跑「daemon window opened + app
    存活」双拓扑有效性门。
  - 端到端验证：`proxy --mode l2` exit 0（12:19，见 T-03）。
- **T-02 [✅ 已完成] [实现]** `evaluate_budgets` l2 武装分支（§5.2 表语义）。
  → AC-02/04
  - 构造性核对绿（importlib 断言：l2 全 10 行终态与 §5.2 表逐行一致；
    steady fail/pass 双分支 verdict/measured/budget_ms 字段；renderer
    armed-record + daemon_mem_bytes；open_100mb 附 l2_open_ms；idle_mem
    附 app+rqhost 双列；l0/l1 语义零扰动——l1 注记保留，l2 无注记后缀）。
  - 实跑验证：T-03 断言表输出（steady armed pass 12.7ms≤80ms）。
- **T-03 [✅ 已完成] [跑数+报告]** 首份 L2 基线：`proxy --mode l2` exit 0 →
  JSONL 入仓 + `baseline-L2-<ts>.md` 撰写。→ AC-01/02/04/05/06
  - `proxy --mode l2` **exit 0**（2026-09-22 12:19:23，第二轮重试链后
    绿跑）；JSONL `results/20260922-121923.jsonl` 六记录型（env/rqhost/
    startup_runs/open_timing/static_full_read/budget_assert），逐字段
    断言绿（auto_version+mtime、release exe 路径+mtime、
    renderer_daemon_build、5 跑两段数字+steady、rqhost cold+restarts=0+
    稳态内存、断言十行）。
  - **首基线数字**：steady 均值 **12.7ms（pass，≤80ms）**（warm 跑
    12.0/11.7/14.9/12.2；init 段 10.1 主导 + ws 段 2.7）；renderer_cold
    16.9ms（debug 构建）；守护稳态 68.9MB；app 空闲 ~25.8MB 均值；
    open 1MB<2ms / 10MB 2.5ms / 100MB 40.6ms（L0 对照 459.8ms，~11×；
    内存 480MB 线性放大不变——rope 缺口锚点）。
  - 报告 `results/baseline-L2-20260922.md`：口径注记（代理/2ms 粒度/
    单 daemon 协议/双有效性门/多会话并行）+ L0↔L2 对照表 + rqhost 单列
    + 断言终态表 + 后续锚点说明（rope/帧插桩/Q2 解锁复测位）。
  - 首跑暖机现象注记：T-00 探针（冷页缓存）steady≈130ms vs 套件跑
    12-15ms——首次 touch 的页缓存效应，暖机弃跑设计已吸收。
- **T-04 [✅ 已完成] [文档+回归]** README 双侧回填（SD-01/02）+ 回归三连（bench
  check / proxy l0 / proxy l2 复跑幂等）。→ AC-07/08
  - SD-01（bench README）：标题/定位升格（L0+L2 数字面）、用法节 `--mode
    l2` 全链描述、新增「L2 测量语义」节（release 直拉/旗标组合/daemon
    协议/拓扑双门/代理口径）、探针矩阵 L2 行翻绿（2026-09-22 解阻，
    PLAN-674/681 后）、断言语义节加 armed/armed-record 两态、坑位节
    增两条 PLAN-006 实勘（末窗退出+管道探测假死；标记先于 adopt）。
  - SD-02（perf README）：模式矩阵 a2r+RQ 行解阻更新（2026-09-22 双判据
    绿：a2r exit 0 + proxy l2 端到端 exit 0）、release 产物路径实锚回填
    （T-07 遗留槽位：`rust-workspace/target/release/auto-edit.exe` 37.8MB）。
  - 回归三连（12:21-12:22）：check rc=0（检测器红证 PASS）；proxy l0
    **exit 0 零扰动**（五类终态齐/not-armed 原样/数字族与 L0 基线同量级，
    JSONL 20260922-122157）；proxy l2 复跑 **exit 0 幂等**（steady 18.2ms
    pass，JSONL 20260922-122256）；tasklist 零 auto-edit.exe 残留。

依赖序：T-00 → T-01 → T-02 → T-03 → T-04（T-01/T-02 可并行实现，T-03
汇合）。

## 9. 复审记录

- 2026-09-22T12:00:00+08:00 · stage: new · PLAN-006 · r1 · 起草完毕，
  handoff → work。授权范围与 §10 三项待裁见上文。
  - `stage: new`
  - `outcome: pass`（可进 work；§10 项均有默认口径，不阻塞起草）
  - `next: work`（执行前建议用户先裁 §10-1/2/3；均不改变合同结构）
- 2026-09-22T11:55:00+08:00 · stage: work 进入 · PLAN-006 · r1 · 用户
  会话明示"/auto-plan-work 实施它"= 执行授权。§10 三项按计划内默认
  口径执行（1 代理口径采用+注记 / 2 rqhost debug 构建+renderer_daemon_build
  字段在档 / 3 超标只记录+归因分解不调优）。运行环境裁定：组内无
  auto-lang 兄弟树，生成物链按 perf.py 头注既定模式 `PERF_PROJECT` 锚
  主检出 `specs/auto-edit`（本计划零 .at 改动，worktree 分支与 main 的
  app 代码零差异；rust-workspace 等落主检出 gitignored 区）。
- 2026-09-22T12:03:00+08:00 · 并发编辑和解记录 · work 会话发现共享计划
  文件于 12:01:19 被未识别外部动作改为 `status: archived` 并移入
  `docs/plans/archived/`（非本会话任何命令所为；auto-os 今日无会话
  活动、无 Cron 自动化在册）。该状态与在办事实矛盾（零交付、用户
  12:00 前后明示执行指令、worktree edit-006 在跑），按 skill 并发编辑
  和解条款移回 `docs/plans/` 并恢复 `executing`。若归档系用户/他 session
  有意为之，请明示——本会话继续按 executing 推进。
- 2026-09-22T12:32:00+08:00 · stage: work · PLAN-006 · r1 · outcome: pass ·
  code_commit: 9dcb58f（worktree `D:/autostack/.wt/edit-006/auto-edit` @
  `plan-006-dev`，基 main dc99328）· task_ids: T-00..T-04 · evidence:
  五任务全 [x] 在档（上文逐条）；AC-01..09 逐项——01/02/04（l2 端到端
  exit 0 + steady armed pass 12.7ms + 十行终态）、03/06（JSONL 字段断言
  绿）、05（baseline-L2-20260922.md 入仓）、07（README 双侧 diff）、
  08（回归三连 + tasklist 零残留 + 复跑幂等）、09（diff 仅 tools 面 +
  results 数据；零 .at / 零 auto-lang）· blockers: 无 · next: review。
  - 实现层超出计划草案的两项勘定（均已回填 §8 收据）：①旗标组合以
    `--autodesk-broker=` 传参替代 env 注入（§5.1 修正，client 臂不读
    env）；②daemon 生命周期固化为「单一 daemon 全序列 + app keep_alive」
    顺设计（对抗末窗退出语义的批次重拉方案两竞态实勘后弃用）——不属
    合同变更，属 §5.1 内实现细节落定。
  - §10 三项均按默认口径执行并已在报告/JSONL 注记在档（1 代理口径+
    注记 / 2 debug 构建+字段 / 3 超标不调优——本跑 steady pass 未触发）。
- 2026-09-22T12:35:00+08:00 · stage: review · PLAN-006 · r1 · outcome: pass ·
  reviewed_commit: 9dcb58f06ab169ec140bef627b67ca704b2a05e0 · base_commit:
  dc993287676443499eb7ca7507f59e5a530788f3（纯后代，可 ff）·
  dependency_revisions: 工具链 auto 0.1.0+v0.4.2-1836-gdcbda3f71-dirty
  （auto.exe mtime 2026-09-22T11:35，评审时点复核未变；auto-lang master
  已移至 979ce80c2 且工作树脏=他组会话在办，未被本评审工件消费——
  数字生产工具链以 JSONL env 在档为准）· spec_inputs: tools/bench/README.md
  + tools/perf/README.md（本仓无 docs/specs 树，PLAN-004/005 先例）·
  acceptance_results: AC-01..09 全 pass · findings: F-01/F-02 非阻塞
  （见下）· evidence: 复审独立性声明=执行会同上下文，裁定从已提交工件
  重构（非执行者自述）——①两份 l2 JSONL + l0 回归 JSONL 重新解析断言
  （独立重导 §5.2 终态对照表逐行核：steady armed/measured/verdict/
  budget_ms/代理口径注记、renderer armed-record 单列+守护内存、
  open_100mb/idle_mem 锚点字段、l0 not-armed 原样零扰动）；②端到端
  exit 0 证据复用理由：回归三连跑于与 9dcb58f 字节相同的工作树（此后
  零编辑，worktree clean 实证）+ 工具链二进制 mtime 未变；③`bench.py
  assert --results <l2 jsonl>` 重放路径首次行使 exit 0；④AC-05 报告
  14 结构键核对 PASS；⑤AC-07 README 双侧 diff 审读（perf 矩阵解阻
  双判据/产物路径实锚；bench 11 关键断言白空归一化在场核对）；⑥AC-09
  diff 恰 7 文件（tools/bench×5+perf README+results×4 内含），零 .at/
  零 auto-lang；⑦AC-08 现场 tasklist 零 auto-edit.exe；⑧负面用例证据：
  bring-up 期拓扑门两次实弹拦截（12:07 拓扑无效/12:15 锁竞态）+ check
  检测器红证自检 · next: merge。
  - **F-01（非阻塞，化妆）**：`stage_assert` 重放 l2 文件时「终态覆盖」
    摘要行用 L0 缺省五态序，打出误导性的「（缺：not-armed）」（行数据
    正确，无 AC 覆盖）。修正建议：从 budget_assert 记录的 mode 字段取
    序（约 3 行）。
  - **F-02（非阻塞，死代码）**：`_window_opened_since` 字节相同地定义
    两次（bench.py L497/L515——编辑迭代残留；第二定义静默遮蔽第一，
    零行为差异）。修正建议：删一份。
  - 两项均不阻塞 merge；可并入下次触碰 bench.py 的顺手清理，或 merge
    前叫 work 一并收（用户裁）。
  - SD 增量终局：SD-01/SD-02 落两 README（diff 已审，描述现行行为与
    持久决策，非执行日记）；supersedes=[]；touched_goals=[] 的书面说明：
    本计划为工具面规范增量，不触战略文档 goal 面（战略 002 属用户裁定
    层，本计划不改；本仓 goal ID 体系未立）。账本投影走 merge 期外科
    插入既有流程。
  - 环境观察在案：第三 worktree `edit-specs`（他 session 所建 @
    auto-edit-dev-1）与 12:01 外部 archived 事件（§9 前文）同属并发
    活动迹象，与本计划分支无涉。


## 10. 待澄清事项

1. **steady_start 代理口径**：预算语是"启动到可输入"，帧时间戳通道
   blocked-upstream（内核插桩未供料）——首基线以 spawn→bench_ws_loaded
   为代理（app 逻辑就绪含 workspace 装载；首帧观测缺席）。此口径能否作为
   M4 硬门禁数字源，留复审/用户裁。默认：采用 + 注记。
2. **rqhost 守护构建形态**：默认用工具链 debug 构建（`auto.exe rqhost`，
   JSONL 记 `renderer_daemon_build` 字段）；若 steady_start 数字呈渲染端
   瓶颈迹象，再裁是否出 release rqhost 对照（auto-lang 侧 release 全量
   编译，成本高）。默认：debug + 字段在档。
3. **steady_start 首基线超标的处置边界**：本计划只记录 + 归因分解（启动链
   两段分解即归因依据），不启动任何调优（战略补注 6(d)：硬门禁"回归当天
   修"属 M4 门禁生效后语义；当前是首锚点）。默认：如此执行；若用户要求
   当场归因深挖（如 spawn→init 段拆 auto.exe 引导占比），另立小任务。

## 11. 落账收据（merge，PLAN-006:r1）

- 2026-09-22T12:50:00+08:00 · stage: merge · PLAN-006 · r1 · 四 checkpoint
  实证（cleaned 见后补记）：
  - **prepared**：reviewed 基线 = r1 pass @ 9dcb58f（§9 复审记录在档）。
    落账期主检出并发前移 f25cb38/5c95903（docs/specs 规范层补建——纯
    docs 8 文件 365 行，零代码/工具面触碰，代码复审不受影响）；按
    5c95903 新惯例（规范增量改指 docs/specs/）将 SD 内容回寄
    `docs/specs/modules/perf-measurement.md`（L2 数字面节：旗标组合/
    daemon 协议/拓扑双门/armed 语义/首基线锚；并修正并发会话预写的
    过时草案——execution_done 未 review/旧旗标/a2r blocked 旧态）+
    `docs/specs/reviews/index.md` PLAN-006 行收据化 + 账本
    `.autoos/specs.json` reviews 段 P006-1 外科插入（六条目序
    P001..P006；整文件 JSON 解析+条目回读等值+其余段零扰动三验；首
    次插入对象边界错位经 git checkout 还原后重做，段落分隔符以
    chr(92)+"n" 构造杜绝 heredoc 转义歧义）。rebase：
    9dcb58f→06cb964（`git range-diff` 全等=安全重写证明）。delivery
    commit = **ed6cdb0**（projection-only descendant of reviewed 9dcb58f：
    diff 仅两规范文档+账本，实现/依赖零改动）。
  - **landed**：主检出 `git merge --ff-only plan-006-dev` 纯快进
    5c95903→ed6cdb0（无 merge commit；10 文件 +655/−79）；tip ==
    delivery commit 双验；主检出烟测 `bench.py check` rc=0。
  - **ledger_refreshed**：主检出实档回读——specs.json 整文件解析绿，
    reviews 六条目序 P001..P006，P006-1 字段（file=归档路径/
    related/title/content）在档；docs/specs 双侧 PLAN-006 引用各 2 处。
  - **archived**：本文件移入 `docs/plans/archived/`，status: archived
    + completion_kind: delivered；账本 P006-1 与 reviews/index 均指向
    归档路径，provenance 链闭合。
  - SD-03 登记：并发规范层补建（f25cb38/5c95903）后按新惯例回寄的
    docs/specs 落点，与已审 SD-01/02 同源同内容（README 运行矩阵单源
    保持；docs/specs 为规范 canonical）。
  - **cleaned**（12:52 补记）：移树前复验 wt-guard clean + dev 全落
    （plan-006-dev tip ed6cdb0 为 main 祖先）→ worktree
    `D:/autostack/.wt/edit-006/auto-edit` 移除 + 分支 plan-006-dev 删除
    （was ed6cdb0）+ 组目录 edit-006 零残留 + 双侧 prune——worktree list
    仅余主检出。PLAN-006:r1 五 checkpoint 全闭环。
