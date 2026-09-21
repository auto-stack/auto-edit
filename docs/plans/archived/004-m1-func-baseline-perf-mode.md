---
plan_id: PLAN-004
status: archived
feature_name: M1 性能轨①+②——功能健康基线 + perf 模式一键化
author: [agent]
created_at: 2026-09-21T02:35:32Z
updated_at: 2026-09-21T03:56:00Z
plan_revision: 1
current_step: 8
completion_kind: delivered
total_steps: 8
supersedes_spec_components: []
new_spec_components: []
touched_goals: [M1-性能轨①-功能健康基线, M1-性能轨②-perf模式一键化, 上游供料包M1]
---

# PLAN-004：M1 性能轨①+②——功能健康基线 + perf 模式一键化

战略依据：`docs/strategy/002-north-star-v2.md` §6 M1 行 + 变更记录补注三
（四步序裁定：①基本功能正常 → ②性能模式一键化 → ③测量体系 → ④性能
测试；本计划覆盖 ①②，③④为后续计划）。

## 0. 变更摘要

M1 性能轨前两步：(a) 上游供料包文档（M1 第一优先的落地件）；(b) 建立
"测量对象健康"基线——desktop_mcp 矩阵稳定性重跑与基线口径固化、
split/vue 双轨功能环复验收据；(c) `tools/perf/` 性能模式一键化——RQ
（外部统一渲染器）编排 + a2r→release 链的自动化切换脚本，含模式实勘探
针与 F-R1 阻塞段的显式归因处理。不产出任何性能数字（那是 ③④）。

## 1. 目标

1. **上游供料包发车**：把 M1 对 auto-lang 的三件诉求（内核 rope 单写者
   版 + 统一 delta + 分块读；a2r server 模板 F-R1；矩阵非确定 F-RV6）
   连同证据整理为一份可立项文档，供上游走它自己的 plan 流程。
2. **功能健康基线**：矩阵跑次分布记录 + 临时判绿口径固化（完成态 ≥39，
   F-RV6 待上游）；split 轨功能环（tree/open/edit/save/quit 经 back
   HTTP）与 vue 轨构建绿复验，各留收据。
3. **perf 模式一键化**：`tools/perf/perf.py` 阶段化编排（依赖自检 /
   a2r 生成 / release 编译 / RQ 渲染器预热管理 / 实例启动 / smoke），
   把"性能模式启动复杂"从手动操作变一条命令；当前被 F-R1 阻塞的段必须
   被脚本捕获并归因打印（blocked: F-R1），不许裸崩。

### 非目标

- ③测量体系（bench 探针/阶段插桩/预算断言）与 ④首份 L2 基线报告——
  后续计划。
- 去 src 镜像先行段（删 editor_store 五处全量回读）——并行小件，另立。
- 任何性能优化本身；任何 specs/auto-edit 应用逻辑改动（发现的 bug 走
  独立小修，不塞本计划）。
- 上游仓库（auto-lang）内的任何修改。

## 2. 架构方案

- **零侵入编排层**：`tools/perf/` 是新增工具目录（与
  `specs/auto-edit/scripts/regen_vue.py`、`tests/desktop_mcp.py` 同族的
  Python 编排件），只调 `auto` CLI / `cargo` / `pnpm`，不改应用源。
  产物落 `rust-workspace/`、`build/`、`gen/`（均 gitignore，可再生）。
- **模式阶梯落地**（战略 §5）：L0=VM+merged（现状，日常）；本计划交付
  L2 的**切换机构**——RQ 渲染器预热（常驻，pid/port 文件管理）+ a2r
  release 链。L2 的测量效力在 ④ 才兑现。
- **基线=收据+口径，不改代码**：矩阵稳定性以"多跑次分布记录进计划 +
  README 口径更新"固化；split/vue 复验按 README 既有配方重跑。
- **阻塞显性化**：F-R1（a2r server 模板 `use api::Db` 硬编码 + 契约
  空体桩，编译 E0432）使 a2r 段端到端不可用——脚本对该段做
  捕获-归因-退出码标记，验收按"脚本行为正确"而非"编译通过"计。

## 3. 技术栈

Python 3（编排与探针，requests 可用）；`auto` CLI（须为含上游 PLAN-669
的构建，≥2026-09-21 版本，版本敏感）；cargo（release 链）；pnpm（vue
复验）；Git Bash 执行环境。

## 4. 需求分析与背景调查

**授权**：用户 2026-09-21 会话口头批准开工（"OK，那么开工"），范围为
本计划 ①②（③④明确排除）；仓库/操作范围 = 本仓 docs/、tools/、
specs/auto-edit/README.md 的文档性增量 + 只读复验既有配方。无预算限制
约定；无自动延续限制。

**Spec 状态**：本仓无 `docs/specs/`；canonical 模块 Spec =
`specs/auto-edit/README.md`（PROVENANCE 管理，源 auto-lang
92c8013）。账本 `.autoos/specs.json` 为派生索引。

**代码/事实证据**（均已实读）：

- 矩阵现状注记：`specs/auto-edit/README.md:137-139`——39/6，6 失败同属
  menubar 展开项快照缺失；F-RV6（auto-lang 工具链竞态，双侧非确定，
  完成态跑次 ≥39 即可，工具链稳定后重定基线）。
- split 功能环 2026-09-21 曾复验绿：`README.md:96-99`（树/打开/编辑/
  保存/退出存盘经 back HTTP 全通；工具链须含 669）。
- vue 轨口径：构建绿为准（`README.md:107-115`，
  `scripts/regen_vue.py --build`；dev 配方 = `auto run --server vm -B
  <port>` + `AUTO_HTTP_PORT=<port> pnpm dev`）。
- a2r 不可用现状：`README.md:101-104`（F-R1：模板假设 `api::Db` 状态
  注入 + 契约 fn 空体桩 → E0432）。
- 裸 `auto build` 禁令与 C/ninja 脚枪：`specs/auto-edit/pac.at:8-9`。
- 后端契约面：`src/back/api.at` 六 `#[api]` fn（perf 模式下 app 侧数据
  面不变）。
- 环境指纹基线：本仓根曾有 `matrix_out.txt`（2026-09-20 跑次残留，
  gitignore 外——收口时清理或移入收据归档）。

**执行环境坑位**（worktree 执行者必读，源自 PLAN-003 实勘）：

- Git Bash `timeout` 杀 .bat/cmd 壳会留 auto.exe 孤儿（占端口 10048）
  ——复跑前 `taskkill //F //IM auto.exe`。
- auto.exe stdout 重定向到管道会塞满阻塞——探针输出一律落文件。
- 工具链版本核对：merge/构建时间 vs `target/debug/auto.exe` mtime，
  陈旧须重建（`cargo build --features ui-iced --bin auto`，增量 ~2min）。
- curl 探针路径带盘符须 URL 编码（%3A%5C），且先排除"服务端不解码"
  假象（未编码/相对/编码三形态对照）。

## 5. 详细设计

### 5.1 上游供料包（T-01 产物）

`docs/upstream/2026-09-m1-supply.md`，五节各含【诉求 + 现象 + 复现/
证据 + 期望形态】：

1. **内核 rope 化（单写者版）**：行数组 → rope+摘要（长度/行数/点-偏移），
   O(log n) 编辑定位；明确不要协作基因（无 OT/CRDT，主线程写 + 后台只读
   快照）。预算动机：100MB ≤1s、1GB 可打开（战略 §2.1 解锁条件列）。
2. **统一 delta 协议**：code_editor 编辑事件从整文本回读改区间增量；
   人击键/agent 结构化写/undo 走同一事件流。
3. **back 分块读**：`read_text` 之外增 offset/limit 分块端点。
4. **F-R1**：a2r server 模板 `use api::Db` 硬编码 + 契约 fn 空体桩
   （现象 E0432；本仓 README:101-104 登记）——perf 模式 a2r 段的硬阻塞。
5. **F-RV6**：669/668 后矩阵双侧非确定（对照跑证据在 PLAN-003 归档档），
   诉求 = 工具链稳定化，解锁矩阵正式重定基线。

### 5.2 RQ/a2r 实勘探针（T-02 产物：`tools/perf/README.md` 初版）

待勘问题（全部为当前未知/未登记面）：

- RQ 模式启动面：外部统一渲染器如何拉起（命令/参数/端口）？app 侧如何
  以 RQ 模式启动（flag/env）？
- RQ 对 **VM 轨** 是否可用，还是仅 a2r/rust 轨？（决定 T-06 的可达范围：
  VM+RQ 可用则预热+实例验证现在就能做；否则 RQ 段随 F-R1 一起 blocked。）
- a2r 对本 pac（`render: ["vm","vue"]` Multi）的生成入口与行为（pac 警告
  裸 build 走 C/ninja；a2r 显式入口待勘，`rust-workspace/` 生成方式）。
- release 编译链：cargo profile、产物路径、exe 启动所需资产。

产出 = 模式矩阵表（VM+merged / VM+RQ / a2r+RQ 各自：启动命令、已知阻
塞、验证状态），作为 perf.py 设计输入与规范增量素材。

### 5.3 `tools/perf/perf.py`（T-05–T-07 产物）

```
python tools/perf/perf.py <stage>
  check    依赖自检（auto 在位+版本指纹/cargo/pnpm），打印环境指纹
  a2r      生成 rust workspace（F-R1 阻塞段：捕获 stderr，识别 E0432/
           空体桩特征 → 打印 "blocked: F-R1 (see docs/upstream/…)"，
           退出码 3）
  release  cargo release 编译（依赖 a2r 成功；否则同上归因退出）
  rq-up    预热外部统一渲染器（常驻；pid/port 记 tools/perf/.rq.json；
           幂等：已在位则复用）
  rq-down  收掉渲染器（按 pid 文件，清理孤儿按上文坑位法）
  run      RQ 模式启动一个 app 实例（接预热渲染器；stdout 落文件）
  smoke    check→（可达段）rq-up→run→探针确认→清理，端到端退出码 0
```

约束：所有外部进程输出落 `tools/perf/logs/`（防管道阻塞）；`run` 前
`taskkill //F //IM auto.exe` 清孤儿（或按 T-02 结论收窄目标进程名）；
退出码约定：0=绿，3=blocked-on-upstream（F-R1/F-RV6 类），1=真失败。
`.rq.json`、`logs/` 入 `.gitignore`。

### 5.4 基线与收据（T-03/T-04）

- 矩阵：连跑 ≥5 次（清孤儿后），记录每次 PASS 数与失败集到本计划
  §9 附表；口径固化为「完成态跑次 ≥39 判绿（临时，F-RV6 后重定）」。
- split 复验：按 README 配方（`auto run -r vm --no-merge` + 探针经
  back HTTP 走 tree/open/edit/save/quit 环）。
- vue 复验：`python scripts/regen_vue.py --build` 退出码 0。
- 三者收据均记入本计划 §9（命令、退出码、关键输出行、时间戳）。

### 规范增量

| delta_id | add/modify/retire | docs/specs/... target | before/after rule | rationale | acceptance IDs |
|---|---|---|---|---|---|
| SD-01 | modify | specs/auto-edit/README.md（How to Run） | before：无 perf 模式运行法；after：增「性能模式（L2）」节——`tools/perf/perf.py` 用法、模式阶梯引用（战略 §5）、F-R1 阻塞注记 | 战略补注二/三：切换复杂=一次性工具债，须进 canonical 运行文档 | AC-06 |
| SD-02 | modify | specs/auto-edit/README.md（Tests） | before：39/6 现状注记；after：≥5 跑分布口径 + 完成态 ≥39 判绿（临时，F-RV6 待上游）+ 本计划收据指针 | 基线口径是 spec 级事实，散在计划里会失联 | AC-02 |

（`docs/upstream/` 与 `tools/perf/` 为新增工具/文档目录，不属 specs 面。）

## 6. 测试设计

- `perf.py check`：依赖缺席时非零退出并指名缺失项；在位时打印版本指纹。
- `perf.py smoke`：可达段端到端 0；F-R1 段验证"归因退出码 3 + 提示文案"
  （构造性验证：直接跑 a2r 段，断言 stderr 特征被识别）。
- RQ 段：预热后连开 ≥2 实例成功、`rq-down` 后 pid 文件清理且端口释放。
- 矩阵/双轨复验：退出码 + §9 收据表。
- 全部探针输出文件化，无管道依赖（坑位约束）。

## 7. 验收标准

- **AC-01** `docs/upstream/2026-09-m1-supply.md` 存在，含 5.1 五节且每节
  有证据路径（可 `ls`/`grep` 复核指向真实文件行）。
- **AC-02** README Tests 节口径更新落盘（SD-02），且本计划 §9 附 ≥5 次
  矩阵跑次分布表。
- **AC-03** split 功能环复验收据（§9：命令+退出码+功能环五项各一行
  结果）；vue `regen_vue.py --build` 退出码 0 收据。
- **AC-04** `perf.py check` 在本机绿（打印 auto 版本指纹，确认 ≥669 构建）。
- **AC-05** RQ 编排按 T-02 结论二选一验收：(a) VM+RQ 可用——`rq-up` +
  连开 ≥2 实例 + `rq-down` 清理干净，smoke 端到端 0；(b) 仅 a2r 可用——
  RQ 段标记 blocked-on-F-R1，`tools/perf/README.md` 模式矩阵表如实登记，
  且 blocked 归因退出码 3 行为已构造性验证。
- **AC-06** README How to Run 增「性能模式（L2）」节（SD-01），命令可
  复制执行。
- **AC-07** `tools/perf/README.md` 模式矩阵表：三模式启动命令/已知阻塞/
  验证状态三列齐全，无"未知"残留（T-02 勘毕的判据）。

## 8. 执行步骤

| ID | 任务 | 依赖 | 产出/意图 | AC | 验证 |
|---|---|---|---|---|---|
| T-01 | [x] 上游供料包文档 | — | `docs/upstream/2026-09-m1-supply.md`（§5.1 五节） | AC-01 | ✅ 86cdfb2：五节齐（rope 单写者版/统一 delta/分块读/F-R1/F-RV6），证据路径含内核 `crates/auto-lang/src/ui/code_editor/core/mod.rs` 定位与归档 F-* 行号 |
| T-02 | [x] RQ/a2r 实勘探针 | — | `tools/perf/README.md` 模式矩阵（§5.2 四问全答） | AC-07 | ✅ c7636f7：①RQ=`auto rqhost`+`run -q`（wellknown 管道+单实例锁+末窗退出）②**VM 轨官方支持**（`-q` 注记 vm/rust tracks）→AC-05 走 (a) 分支 ③a2r=仓外 `<project>/rust-workspace/`+`AUTO_RUST_WORKSPACE` 权威 env，工具链 cargo 默认 debug→release 由 perf.py 补 ④**F-R1 只阻 `--server rust` 不阻 merged**——L2 主形态 `-r rust -q` 无需等上游 |
| T-03 | [x] 矩阵稳定性重跑 | — | ≥5 跑次分布表进 §9；README 口径更新（SD-02） | AC-02 | ✅ 1328b1f：附表 A 五连跑（50/0×2、49/0、早崩×2）；README 口径落账并入 T-08 批次；供料 §5 增补 1631 实测（f03a1b0） |
| T-04 | [x] split/vue 双轨复验 | — | §9 收据（split 五项功能环 + vue 构建退出码） | AC-03 | ✅ b0b4676（F-1 修复后）：split 全绿（附表 B）+ **vue `regen_vue.py --build` 退出码 0**（worktree 全新生成+install+build；日志 `.auto/plan004-vue-fix.log` 零 error TS）；补件⑥/1b 在 committed/dirty 两依赖世界各走正确分支（幂等设计覆盖工具链漂移） |
| T-05 | [x] perf.py 骨架 + check | T-02 | 阶段化 CLI + `check`（环境指纹） | AC-04 | ✅ 93fc83a：check 实测绿（v0.4.2-1631 ≥1588 门/cargo 1.98/pnpm 11.6，指纹落 logs/env-*.txt）；七段 CLI 齐（check/a2r/release/rq-up/rq-down/run/smoke），退出码 0/3/1，F-R1 特征识别+隔离 wellknown+按 PID 收 |
| T-06 | [x] RQ 段编排 | T-02/T-05 | `rq-up/run/rq-down`（或 blocked 登记，按 T-02） | AC-05 | ✅ 44e3a74：**blocked 登记分支（等价调整）**——blocker 从预案的 F-R1 改判为新缺口「RQ 渲染臂未覆盖 codeeditor」（coverage::native_queue_set 基础集外，供料 §6）；编排链全验证（rq-up 管道探测绿/run 双实例派发/rq-down 按 PID 清理）；smoke 实测 exit 3 构造性验证成立 |
| T-07 | [x] a2r+release 段编排 | T-05 | `a2r/release` 阶段 + F-R1 归因退出 | AC-05/06 联动 | ✅ ab57177：a2r 实测 exit 3（BLOCKED 归因：**PLAN-027 词汇门**拒 value/text/title 等 23 错——新缺口供料 §7，非 F-R1）；分类补丁构造性验证（exit 3 + 首错行打印）；release 段在位待 a2r 绿后生效 |
| T-08 | [x] 规范增量落账 + 收口自检 | T-01..T-07 | SD-01 落盘；.gitignore 增补（.rq.json/logs）；matrix_out.txt 清理；AC 逐条复核 | AC-06 | ✅ ab57177：SD-01（性能模式节）+ SD-02（1631 定标口径）落 specs/auto-edit/README.md；matrix_out/err 双清 + `/matrix_*.txt` 围栏；AC 复核见 §9 终局记录 |

## 9. 复审记录

- 2026-09-21T02:35:32Z · stage: new · r1 起草 · 授权=用户会话批准
  （范围①②）；待 work 接手。（执行期收据附表：矩阵跑次分布 / split+vue
  复验 / smoke 结果——由 T-03/T-04/T-06 回填。）
- 2026-09-21T03:17:42Z · stage: work · r1 · **execution_done** ·
  outcome: **pass（带 3 项上游 blocked 登记）** · code_commit:
  worktree `.wt/edit-004/auto-edit` @ `plan-004-dev`（86cdfb2 →
  c7636f7 → 93fc83a → 44e3a74 → ab57177，5 commits）+ 主检出记账
  （872345a/61c3bca/1328b1f）· task_ids: T-01..T-08 全 [x] ·
  **AC 复核**：AC-01 ✓（供料包八节超集交付）；AC-02 ✓（SD-02 落盘 +
  附表 A 五连跑）；AC-03 split ✓ / **vue = blocked-upstream**
  （§8/PLAN-671，fetch 后复证非缓存）；AC-04 ✓；AC-05 ✓（(b) 等价
  分支：blocker 改判 §6 codeeditor 覆盖，exit 3 构造性验证）；AC-06 ✓
  （SD-01 落盘 + a2r 词汇门归因 exit 3）；AC-07 ✓（矩阵全行实测态，
  无"未知"）· **blockers（全上游，供料包在档）**：①§6 RQ 渲染臂
  codeeditor 覆盖（阻 L1/L2 的 RQ 面）；②§7 a2r 词汇门（阻 L2 主形态
  与 release 段）；③§8 vue 1631 构建红（PLAN-671 证据增补）。
  · next: **review**（复审请重点核：AC-03 vue blocked 定性、AC-05
  blocker 改判的等价性、供料 §6/§7 的证据充分性）。
- 工程注记：组目录 `.wt/edit-004/`（auto-edit 主树 + auto-lang detach
  兄弟树 @ e82b95b22 供 bps 依赖）；worktree 全部验证跑经 PERF_PROJECT
  锚主检出（gitignored 生成物），worktree 零重物、guard 友好。
- 2026-09-21T03:40Z · stage: review · plan_revision: 1 · outcome:
  **needs_fix** · reviewed_commit: worktree ab57177 · base: main fb68b27 ·
  deps: 工具链 v0.4.2-1631（e82b95b22-dirty），兄弟树 detach @ e82b95b22 ·
  spec_inputs: specs/auto-edit/README.md（worktree SD-01/02 版）·
  独立性声明：执行会话内复审，结论自工件与可复现命令重建。
  **acceptance_results**：AC-01 ✓（供料八节，引文行号与 editor_store.at
  实测 grep 一致：镜像位 229/350/359/376/393 + save 位 338/492）；AC-02 ✓
  （SD-02 落盘 + 附表 A，RESULT 行磁盘复核 49/50/50 + 两无 RESULT）；
  AC-03 **partial→needs_fix**（split 六端点绿有效；vue 红）；AC-04 ✓
  （复审重跑 exit 0）；AC-05 ✓（等价性裁定见 F-2）；AC-06 ✓；AC-07 ✓。
  矩阵证据复用理由：分支触碰面 diff --stat 证明应用源零改动（仅
  docs/tools/README/.gitignore/matrix 清理），矩阵跑于同源 fb68b27。
  **findings**：
  - **F-1（major，AC-03/T-04）**：vue blocked-upstream 定性**不成立**。
    法证链：①1631 生成器已自 emitting `src/natives.d.ts`（671 函数形态
    内建吸收中间态，`(...args: any[])` 宽松签名），函数们由它解析——
    本仓补件的 `src/lib/natives.d.ts` 不在 tsc 程序内（listFilesOnly
    实证：仅 src/natives.d.ts + src/lib/natives.ts 入程序），其
    `Process/Env` 对象声明因此失效；②生成器 natives 吸收只覆盖函数形态，
    **漏了对象形态内建（Process/Env）**——探针实证：向 src/natives.d.ts
    追加两行对象声明后 TS2304×3 全消；③TS1117 = 本仓补件⑥（button
    text variant）非幂等——生成器 671 已吸收 text variant（带
    `// PLAN-671 ⑥` 注释的 `text: ""`），补件仍盲目追加 `text:` →
    重复属性（L14 补件旧值 vs L30 生成器新值）。**修法（本仓补件层，
    ~10 行）**：regen_vue.py 补件⑥加在场守卫（`text:` 已存在则跳过）；
    补件①改/增打生成器侧 src/natives.d.ts（追加 Process/Env 声明）；
    重跑 `regen_vue.py --build` 断言 exit 0；同步**勘误供料 §8**：
    TS1117 不再请上游纳入 671（上游已修），改为「671 natives 吸收需
    覆盖对象形态内建」单项。
  - **F-2（info，AC-05 等价性裁定——用户指定复审焦点②）**：AC-05(b)
    文字的 "blocked-on-F-R1" 是起草期对 blocker 的预判名，分支的实质
    要求是「blocked 登记 + 矩阵如实 + exit 3 构造性验证」三机制——
    实测 blocker 为 §6 codeeditor 覆盖（T-02 静探无法预见、恰为 (b)
    机制存在的理由），三机制全数满足且附表 C 留痕。裁定：**按机制等价
    满足，pass**；不改 AC 文本（预判名非验收物）。
  - **F-3（info）**：release 段与 rust+RQ 端到端未实测（a2r §7 阻），
    与登记一致，非缺口。
  next: **work**（修复 F-1 后重开 T-04 → execution_done → 复审只需
  复核 F-1 修复面：vue exit 0 + 供料 §8 勘误）。
- 2026-09-21T03:44:46Z · stage: work · r1 · **execution_done（F-1 修复
  回合）** · outcome: pass · code_commit: b0b4676（worktree，第 6 个）·
  task_ids: T-04（重开→复勾）· evidence: vue 全新生成链退出码 0 + 零
  error TS（附表 B）；补件⑥守卫与 1b 追加在 committed/dirty 两依赖
  世界各验证一分支；供料 §8 勘误收窄为单项真实上游诉求 · blockers:
  无新增（上游三登记 §6/§7/§8-收窄后不变）· next: **review（仅复核
  F-1 修复面）**。
- 2026-09-21T03:49:28Z · stage: review · plan_revision: 1 · outcome:
  **pass（scoped，F-1 修复面）** · reviewed_commit: worktree b0b4676 ·
  base: ab57177（上轮 needs_fix 基线）· 独立性声明：执行会话内，自工件
  重建。**复核四项**：①补件⑥守卫 ✓（在场跳过 + 缺位补插双分支，8 空格
  variant 锚与两世界生成物实测缩进一致）；②补件 1b ✓（存在性门 +
  逐声明缺席追加，追加内容与复审探针逐字节同型）；③vue exit 0 ✓
  （收据复核：`vue_fix_exit=0` + 零 error TS；运行与提交内容同一——
  编辑→跑→提交无中间改动，worktree clean 实证；committed 世界走
  ⑥插入/1b 跳过分支，dirty 世界走守卫/追加分支[探针证]，双分支覆盖）；
  ④供料 §8 勘误 ✓（button 条划线作废+归因下游非幂等、真实诉求收窄为
  「671 natives 吸收覆盖对象形态内建」单项，与法证事实一致）。
  **AC 终态**：AC-01/02/04/05/06/07 沿用 a5d882f 结论（F-1 diff 仅触
  regen_vue.py+供料，证据面未受扰动）；**AC-03 全量 pass**（split +
  vue exit 0）。findings：F-4（info，非阻塞）——README 存一处"七类"
  计数（PLAN-003 期上游缺口分类；1b 为第 1 类扩展非新类，计数语义仍
  成立，不改）。规范增量 SD-01/02 不受 F-1 影响，终版确认。
  next: **merge**（用户已预授权衔接）。
- **PLAN-004:r1 merge 收据（2026-09-21 03:56Z）**
  - `prepared` ✓：账本投影提交 6bcc275（projection-only descendant
    of reviewed b0b4676；.autoos/specs.json reviews 段 P004-1 外科插入，
    10 insertions/0 deletions，回读序 P001-1..P004-1 校验）。
  - `landed` ✓：rebase plan-004-dev → main（8/8 提交，range-diff 全等
    `=`；映射 6bcc275→f7d2a12 等）；`git merge --ff-only` 落 main，
    tip=f7d2a12=delivery；主检出烟测 `perf.py check` exit 0（1631
    门通过）；树零脏面。
  - `ledger_refreshed` ✓：主检出账本回读 P004-1 在册（file 指向本
    归档档路径，随 ff-merge 落位）。
  - `archived` ✓：本档 `docs/plans/archived/004-m1-func-baseline-
    perf-mode.md`，status: archived，completion_kind: delivered。
  - `cleaned` ✓：双树移除前 fresh guard clean（auto-edit 树含 vue 验证
    跑遗留——11 轮链接级清理 ~543 junctions 后 clean；auto-lang 兄弟树
    首检 clean）；`git worktree remove`（auto-edit --force 清 gitignored
    残留）+ `branch -d plan-004-dev`（was f7d2a12=delivery）+ 组目录
    edit-004 移除 + 双仓 `worktree prune`——终态 auto-edit 仅 main@af7f7c7、
    auto-lang 仅 master，`.wt/` 无 edit-004 残留。坑位备忘：本机 grep 为
    ugrep，`[\\/]` 字符类过滤失灵——guard 输出过滤用 `^D:` 盘符锚。
- **附表 A：矩阵跑次分布（T-03 收据，2026-09-21）**
  - 环境：auto `v0.4.2-1631-ge82b95b22`（2026-09-21 10:14 构建，-dirty）；
    命令 `cd specs/auto-edit/tests && python desktop_mcp.py`（env 旁路
    `AUTO_OPEN_PATH=src/back/api.at`、`AUTO_SAVE_PATH=.auto/plan004-matrix/
    save-probe.txt`）；轮间隔 `taskkill //F //IM auto.exe` + sleep 2；日志
    `.auto/plan004-matrix/run{1..5}.log` + `summary.txt`（gitignored）。
  - 分布：

    | run | RESULT | exit | 注 |
    |---|---|---|---|
    | 1 | 50 passed / 0 failed | 0 | 完整（至 T11 OS 键位层） |
    | 2 | 50 passed / 0 failed | 0 | 完整 |
    | 3 | 无 RESULT（早崩） | 1 | T3b 后 app 实例死：MCP 9247 拒连（WinError 10061） |
    | 4 | 49 passed / 0 failed | 0 | 完整；1 项 render-timing skip（editor node not yet in snapshot） |
    | 5 | 无 RESULT（早崩） | 1 | T6 后同形态（9247 拒连） |

  - 结论：①**测试级失败 = 0**——README 39/6 的 menubar 快照债在 1631
    清零（上游 1589–1631 区间顺带修复，本仓零改动受益）；②**进程级早崩
    2/5**——app 实例中途死亡、死亡点逐跑不同（T3b/T6），F-RV6 竞态存活，
    形态从"失败集漂移"收敛为"实例死亡"；③**基线口径（临时，F-RV6 修复
    后废除重跑条款）**：完成态跑次 = RESULT 行出现且 **≥49 passed /
    0 failed 判绿**；无 RESULT = 工具链竞态早崩 → 重跑一次而非计失败。
- **附表 B：split+vue 双轨复验收据（T-04）**
  - split（VM+VM，2026-09-21 11:09，主检出 `specs/auto-edit`，工具链
    1631）：`AUTO_OPEN_PATH=<api.at> auto run -r vm --no-merge -B 8199`
    （stdout 落 `.auto/plan004-split.log`）。六端点全真值：
    ①`/api/ws_root`→真实根路径；②`/api/exists`(abs)→1；③`/api/read_text`
    首段与源一致；④`/api/env_str(AUTO_OPEN_PATH)`→回传旁路值；
    ⑤`/api/tree(depth=2)`→真 JSON（含 deps/ 挂载面）；⑥`POST
    /api/write_text`→1 且回读逐字一致（HTTP 日志 200/0ms ×2）。
    实例按命令行过滤精确回收（pid 27896，端口复核关闭）——期间并行
    a2r 构建的 auto.exe 未受连坐。UI 侧功能环由矩阵（merged，同 UI
    代码，附表 A）+ PLAN-003 split 11/11 存档收据共同覆盖。
  - vue 旧红收据（沿革，11:09/11:15 主检出双跑同错 + fetch 刷新排除
    缓存）：TS1117（button 重复属性）+ TS2304（`Process` 未声明 ×3）
    ——复审 F-1 法证定性为过渡补件层两根因（非上游 blocked），日志
    `.auto/plan004-vue.log` / `.auto/plan004-vue2.log`。
  - vue（F-1 修复后收据，2026-09-21 11:44，b0b4676）：worktree
    `specs/auto-edit` 全新生成链 `python scripts/regen_vue.py --build`
    → **退出码 0**（生成 + 补件 + pnpm install + vue-tsc + vite 全绿；
    日志 `.auto/plan004-vue-fix.log`，全零 error TS）。补件分支持痕：
    本轮（bps 依赖解析至兄弟树=**已提交** e82b95b22 世界）补件⑥执行
    插入（生成物无 text variant）、1b 无生成器侧文件跳过；主检出
    （**dirty** auto-lang 世界：生成器发射 text variant + src/natives.d.ts）
    分支经复审探针验证。两分支幂等成立=对工具链 dirty/committed 漂移
    免疫，正是过渡补件的验收形态。旧红收据（vue/vue2 双跑同错 + 复审
    法证）保留于上方为沿革。
- **附表 C：RQ/a2r/release/smoke 收据（T-06 已回填，T-07 待补）**
  - T-06（44e3a74，2026-09-21 11:03/11:07 两轮）：
    - smoke 轮1（11:03）：rq-up 绿（pid 24492，wellknown 管道探测过）；
      双 VM 实例派发（20960/14784）后 0/2 存活——app 日志死因
      `native queue 臂视图未覆盖: tag:codeeditor`（拒绝渲染语义）；
      rqhost 侧 `adopt App→…app-1/-2` 后 `adoption 未达 Active（预算
      耗尽弃置）`；rq-down 清理正常。exit 1。
    - smoke 轮2（11:07，分类补丁后）：同场景 exit **3**（BLOCKED 归因
      打印成立）——AC-05/06 构造性验证。
    - 结论：编排链在位；**app 渲染阻塞 = 新上游缺口（供料 §6）**，
      与 F-R1 无关；L1（VM+RQ）与 L2 的 RQ 面均待上游 native_queue_set
      增补 codeeditor 后解阻。
  - T-07（ab57177，11:09 首跑 / 11:15 复跑）：`PERF_PROJECT=主检出
    specs/auto-edit python tools/perf/perf.py a2r` 两轮均失败——
    首轮 exit 1（未分类形态）触发分类补丁；补丁后 exit **3**：BLOCKED
    归因打印「生成器缺口（上游，供料 §7）。首错：error: a2r codegen:
    prop \`value\` not in the recognized vocabulary (PLAN-027 explicit
    rejection gate)」——生成物 23 错全为词汇拒绝门（value/text/title
    等嵌 compile_error!，a2r-*.log 全量在档）。release 段在位但因 a2r
    阻未生效；`--server rust` 的 F-R1 独立且仍未修（供料 §4，未复验——
    非本形态依赖）。

## 10. 待澄清事项

- RQ 模式是否支持 VM 轨（T-02 自解，决定 AC-05 走 a/b 哪支）。
- a2r 对本 pac 的显式生成入口（T-02 自解；若上游无入口则升上游供料）。
- F-R1/F-RV6 上游解阻时点（不可控；本计划以 blocked 显性化对冲，解阻
  后 ③④ 计划接管）。
- RQ 渲染器的进程名/清理目标（T-02 结论回填 rq-down 实现）。
