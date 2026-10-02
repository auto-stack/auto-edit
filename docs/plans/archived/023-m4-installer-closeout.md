---
plan_id: PLAN-023
status: archived
completion_kind: delivered
feature_name: M4-06 installer 收口件（ts-off 发布形尺寸判定+门控手段裁定〔panic=abort×catch_unwind 语义冲突勘定〕+deps 深裁挤压→≤15MB armed）
author: [agent]
created_at: 2026-10-02T09:09:08+08:00
updated_at: 2026-10-02T11:10:00+08:00
plan_revision: 1
current_step: 6
total_steps: 6
supersedes_spec_components: []
new_spec_components:
  - docs/specs/modules/perf-measurement.md（SD-01：installer/portable 形态节收口——判定终态+门控裁定记录+冲突面注记）
  - docs/specs/00-overview.md（SD-02：M4 第六件注记——installer 收口+M4 剩余清单终态）
  - specs/auto-edit/README.md（SD-03：PLAN-023 口径+发布构建用法）
  - docs/strategy/002-north-star-v2.md（SD-04：§2.1 两行重基线〔用户裁定 2026-10-02——执行期增补，见 §5 规范增量表〕）
touched_goals:
  - 战略 §2.1 预算行「安装包 ≤15 MB 单 exe，无运行时依赖」——本件判定收口（M4 验收面四件之 installer 的终态件）
affects: [tools/portable/build_portable.py, tools/bench/budgets.json, tools/bench/bench.py, specs/auto-edit/README.md]
---

# [PLAN-023] M4-06 installer 收口件（≤15MB 判定终态）

## 0. 变更摘要

M4 installer 面的**判定终态件**（019 分阶段语义的收口）。前置已齐：
022 交付 **ts-off/ts-on 载荷开关**（build_portable `TS_FEATURE`——
ts-off=发布/installer 约束形）；716 交付 two-face 退役（**实收仅
-0.6MB——019 的 12.4MB 弹药叙事已翻转入档**）。本件三步收口：
**①现势重建+挤压库存量盘点**（ts-off 形全手段重建——基线重测
[019 V2b=29.8MB 时代之后：710 G-B 生成形态/716 退役/022 增量全在
谱]+deps 深裁库存量表[iced feature 面/ureq/axum/tokio 细粒度/
image 字体栈——019 勘定「剩余大头=上游域」的下游可达部分]）→
**②门控手段裁定（用户件——起草期发现的语义冲突为本件核心裁定面
）**：**panic=abort 与 710 G-B 的 catch_unwind 生成形态互斥**（.at
try/catch→`std::panic::catch_unwind`[fsys.at 装载兜底/editor_store
会话恢复等 4+ 处]——panic=abort 下 catch 失效=兜底语义降级；019
时代组合 16.46MB 中 panic=abort 贡献 -7.11MB，**出局则 opt-z 单独
≈21.6MB、距门 ~6.6MB**）→三路裁定：**(a) 接受降级**（兜底面逐点
风险评估+用户明示接受）/ **(b) 深裁路线**（无 panic=abort——deps
库存量全落+缺口归因，若不达=上游域缺口登记）/ **(c) 分阶段维持**
（≤15MB 遗留注记——**M4 tag 口径随裁**）→ **③判定收口**（达标=
budgets installer armed PASS+portable 烟测复跑+L2 锚点护栏复跑
[019 G-4 双轨先例——收口 profile 下 steady/warm/open/diff 五行零
回退]；未达标=差距归因终表+裁定态注记）。**本件判定结果直接决定
v0.1-M4 tag 时点口径**（§10 Q-2）。

## 1. 目标

- **G-1 现势重建+库存量盘点（T-00 决策件）**：ts-off 形全手段谱
  重测（V2b 手段集[lto=fat+cgu1+strip+tokio 子集]于当前树——716
  退役后基线修正；opt-z 单独谱；panic=abort 谱仅记录不默认[冲突面
  pending 裁定]）+ **deps 深裁库存量表**（iced features 面逐项
  必要性审计/ureq json 面/axum 默认面/tokio rt 细粒度/image 编解码
  族/字体栈——各自预估收益与功能风险行）+ **panic=abort×catch_
  unwind 冲突面成文**（生成形态 4+ 处逐点清单+降级后果语义表——
  裁定材料主体）。
- **G-2 门控手段裁定（用户件——Q-1）**：三路（a/b/c）裁定材料齐
  备后请示；裁定结果落 budgets/规范档（SD-01 裁定记录节——019
  Q3 裁定落账先例同款）。
- **G-3 判定收口**：依裁定执行终态手段集→**≤15MB 判定**（达标=
  armed PASS；未达标=差距归因终表[构成占比对照 019 表]+裁定态注
  记）+产物 dist/portable 双形态命名定稿（ts-off 发布形默认）。
- **G-4 护栏+烟测复跑**：收口 profile 下 L2 五行锚点零回退复跑
  （steady/warm/open/idle/diff——019 G-4 双轨纪律）+portable 烟测
  复跑（单 exe 直跑+无依赖面——019 T-04 四段）。
- **G-5 规范+账本**：SD 三册+P023-1；（条件）上游域缺口登记
  （深裁路线若现不可达大头——wgpu 栈 4.1MB .text 等[019 构成表]
  →供料档增补）。

### 非目标

- **ts-on 形态判定**（语法完整形非发布形——尺寸仅记录不判定；
  716 +18.9MB 实测在册）。
- 帧两行 FAIL 清偿（上游管线件——auto-lang 域另行立项；本件
  profile 护栏不含帧档）。
- open_1gb 裁定与实施（用户件+上游域）；NP++ 列（用户件）。
- onig/syntect 摘除（上游 cosmic-text 解耦——716 偏差注记另档）；
  上游 deps 面（内核 feature 粒度）——本件只做**下游可达**的
  deps 裁剪（生成物 Cargo deps 行+profile 面）。
- winget/自动更新（Q3 裁定已出——后续件域维持）；执行打包路径
  （已裁出局）。

## 2. 架构方案

分层落点（2026-10-02 实勘，auto-edit main@5dbfd79）：

| 面 | 现状 | 本期形态 | 依据 |
|---|---|---|---|
| 构建通道 | build_portable ts 双形态开关（022——TS_FEATURE 注入幂等）+V2b 手段集（019） | ts-off 发布形默认+手段集终态化（依裁定） | 022 T-05；019 T-02 |
| 尺寸基线 | 019 谱：基线 39.4→V2b 29.8→组合 16.46（panic -7.11/opt-z -7.65）；716 退役 -0.6MB 翻转 | 现势全谱重测（716/710/022 增量后）+库存量表 | 019 手段终表；716 实测注记 |
| 门控冲突 | panic=abort=019「用户裁定面」未裁；**710 G-B 落地后 try/catch→catch_unwind 为现役语义**（fsys/editor_store 兜底 4+ 处） | **冲突面成文+三路裁定**（a 降级/b 深裁/c 分阶段）——本件核心决策件 | 710 SD-A（catch_unwind 形）；019 Q-1 遗留 |
| 判定面 | budgets installer 行=ledger+分阶段注记（019） | armed PASS 或 差距归因终表+裁定态 | budgets.json:75-81 |
| 护栏 | 019 G-4 双轨（工具链轨+产物面）先例 | 收口 profile 五行零回退复跑+烟测四段 | 019/021/022 判定谱 |

**关键设计约束（frozen）**：
① **语义冲突不默认**——panic=abort 在裁定前不入默认手段集（谱
记录不启用；019 时代其为未裁门控项，710 G-B 后升格语义冲突项）。
② 判定双态如实（达标=armed PASS；未达标=归因+裁定注记——**不
以放宽口径换绿**；tag 口径随裁定 Q-2）。③ 深裁域限**下游可达**
（生成物 deps 行/profile——内核 feature 面缺口只登记不实施）。
④ 护栏先行（终态手段集每步配五行锚点复跑——019 纪律）。

## 3. 技术栈

python build_portable/bench 工具族（019/022 通道复用）+cargo
profile/deps 注入（幂等补丁）+尺寸分解（PE 节表/cargo-bloat 形
——019 先例）+desktop_mcp 烟测。工具链纪律承 021/022（master
重建含 716+；`auto --version` 核哈希）。

## 4. 需求分析与背景调查

**授权记录**：用户 2026-10-02 会话指令「OK，auto-plan-new 立项
023；然后把 auto-lang 的立项 prompt 说出来」——授权=**起草本件**
；执行/work 待用户另行启动。范围=auto-edit 单仓（tools/docs/
budgets）；auto-lang 零改动（上游缺口=登记）。**Q-1 三路裁定=
用户件**（材料由 T-00 备齐后请示）。无预算/自动续跑授权。

**来源与版本**：

- 交接链：PLAN-019（分阶段语义+手段终表+V2b/组合谱+门控未裁）
  /PLAN-716 r2（退役实收 -0.6MB 翻转注记+SD-A 尺寸三态表）/PLAN-
  022（ts 双形态通道+TS_FEATURE 幂等注入）。
- 冲突面证据链：710 SD-A（a2r-app-mapping-completeness——G-B
  try/catch→catch_unwind 生成形态+变量逃逸形）+本仓生成物实况
  （fsys.at:208 try 等 4+ 处兜底为现役语义——021 Q-4 修复史）；
  panic=abort×catch_unwind 互斥=Rust 语义事实（abort 下 unwind
  表弃用）。
- 现状实勘（main@5dbfd79）：build_portable.py:86-94（TS_FEATURE
  开关实锚）；budgets installer 行（019 注记态）；019 evidence
  构成表（wgpu 栈 4.1MB .text/two-face 域/image/HTTP/字体栈——
  「剩余大头=上游域」注记）。
- 战略口径：§2.1 installer 行（≤15MB 单 exe 无运行时依赖）+§9
  Q3 裁定（纯 portable——019 SD-04 落账）。

## 5. 详细设计

### T-00 现势重建+库存量盘点+冲突面成文（决策件）

1. **全谱重测**（ts-off 形）：V2b 手段集现势基线→opt-z 追加谱→
   （记录档）panic=abort 谱——三代数字表（019 谱对照列）。
2. **deps 深裁库存量表**：逐项{预估收益, 功能风险, 下游可达性}
   ——iced features 审计（advanced/tokio 面逐项）/ureq json/
   axum cors/tokio rt/profile 面/image 编解码/字体栈。
3. **冲突面成文**：catch_unwind 生成点全列（grep 生成物）+降级
   后果语义表（每兜底点的失败模式：进程死亡 vs catch 兜底）+
   三路裁定材料（a/b/c 各自：尺寸预期/语义代价/工期）。

### T-01 门控手段裁定（G-2——用户件）

Q-1 请示（材料=T-00③）；裁定落档（budgets 注记+SD-01 裁定记录
节——019 Q3 落账先例）。

### T-02 终态手段集执行（G-3）

依裁定：**(a)** panic=abort 入集+兜底点降级注记逐点成文（风险
接受记录）/ **(b)** 深裁库存量逐项落位（护栏门联动——每项一档
{尺寸,锚点}/回滚纪律 019 同款）/ **(c)** 手段集维持 V2b+opt-z
谱（分阶段注记终态）。产物双形态命名定稿（ts-off 默认发布形）。

### T-03 判定收口（G-3）

≤15MB 判定（达标 armed PASS/未达标差距归因终表——构成占比对照
019 表+裁定态注记）；budgets installer 行终态。

### T-04 护栏+烟测复跑（G-4）

收口 profile 五行锚点零回退复跑（steady/warm/open/idle/diff
——021/022 判定谱对照）+portable 烟测四段复跑（单 exe 直跑/无
依赖面——019 T-04）。

### T-05 规范+账本（G-5）

SD-01..03 落档+（条件）上游缺口登记（深裁路线不可达大头→供料
档增补节）+specs.json P023-1。

### 规范增量

| delta_id | add/modify/retire | docs/specs/... target | before/after rule | rationale | acceptance IDs |
|---|---|---|---|---|---|
| SD-01 | modify | docs/specs/modules/perf-measurement.md | before：installer/portable 形态节=分阶段（29.8MB+门控待裁） / after：判定终态节——现势三代谱+门控裁定记录（含冲突面语义表）+终态手段集+判定结果（armed PASS/归因终表）+ts-off 发布形默认 | installer 面收口真源 | AC-02/03 |
| SD-02 | modify | docs/specs/00-overview.md | before：M4 第五件注记（剩余=installer 收口+帧两行+open_1gb） / after：M4 第六件注记（installer 终态+M4 剩余清单=帧两行[上游管线件]+open_1gb 裁定[+NP++ 建议]——tag 口径注记） | 面进度与 tag 前置总览 | AC-05 |
| SD-03 | modify | specs/auto-edit/README.md | before：PLAN-022 口径 / after：PLAN-023 口径（发布构建用法[ts-off 默认]+判定数字回填位） | 运行矩阵/工具单源 | AC-05 |
| SD-04 | modify（执行期增补——用户重基线裁定触发） | docs/strategy/002-north-star-v2.md | before：§2.1 安装包 ≤15MB/空闲内存 ≤60MB / after：≤50MB（独立渲染期口径）+≤150MB（渲染暖态语义）——RQHost 后回归 ≤20MB〔同日精调 15→20，双已知路径校准〕/≤10MB 级；变更记录追记行（PLAN-023） | 用户裁定落账（预算随渲染拓扑重分期——019 SD-04 先例同款） | AC-02/05 |

## 6. 测试设计

- **三代谱重测**：ts-off V2b 现势/opt-z/(panic 记录档)——N≥2 构建
  谱+尺寸分解表（PE 节表对照 019 表列）。
- **深裁库存量验证**（若走 (b)）：逐项{尺寸收益,五行锚点}对照行
  ——护栏红即回滚记录（019 纪律）。
- **判定断言**：build_portable 尺寸门（≤15MB 绿/超限红+数字）+
  budgets 断言面一致（五态机制）。
- **护栏复跑**：收口 profile 五行 L2 锚点（对照 021/022 谱——容
  差带内零回退）+烟测四段。
- **幂等**：手段集注入幂等复跑（019/022 通道验证复用）。

## 7. 验收标准

- **AC-01 现势谱+库存量+冲突面**：三代数字表+deps 库存量表+
  catch_unwind 冲突面语义表在档（裁定材料完备）。验证：T-00 报告
  （evidence-p023-*）。
- **AC-02 裁定落档**：三路裁定结果+理由入 budgets/SD-01（用户件
  ——回执原文在录）。验证：注记+裁定节在档。
- **AC-03 判定终态**：达标=budgets installer armed PASS+门双态
  （绿/超限红）验证；未达标=差距归因终表+裁定态注记（双态如实
  ——不以放宽换绿）。验证：budgets+判定报告。
- **AC-04 护栏+烟测**：五行锚点零回退谱+烟测四段绿。验证：复跑
  谱 JSONL+烟测记录。
- **AC-05 规范+账本**：SD-01..03 落档+P023-1 回读 True+（条件）
  上游缺口登记在档。验证：文件在档+账本断言。
- **AC-06 范围**：auto-lang 主树零改动+.at 源零 diff（构建通道/
  工具/文档面）。验证：双仓 porcelain+路径断言。

## 8. 执行步骤

| # | 任务 | 依赖 | 落点（实勘锚） | 产出/意图 | AC | 验证（命令/预期） |
|---|---|---|---|---|---|---|
| 0 | T-00 现势谱+库存量+冲突面 | — | build_portable+evidence-p023 | 裁定材料三件套 | AC-01 | [x] 三表在档（evidence-p023-survey@worktree 75d7ca6：三代谱〔V2b 30,403,072/opt-z 22,206,976/abort 22,646,272——三路无一达门〕+库存量 R1-R9〔可达池仅 R2 axum<0.5MB〕+冲突面 17 语句/8 语义点） |
| 1 | T-01 门控裁定 | T-00 | §10 Q-1 请示+budgets/SD | 用户裁定落档 | AC-02 | [x] 裁定回执在录（两轮 AskUserQuestion——首轮三路问询自主会话未应答→用户提出门重基线→次轮定案 **50MB+150MB/手段集 V2b 维持**；回执原文+落地面=evidence §⑥+SD-04 战略追记） |
| 2 | T-02 终态手段集 | T-01 | build_portable 注入面 | 依裁定执行 | AC-03 | [x] 手段谱+护栏门（(c) 变体=V2b 维持终态：opt-level=3 保性能+panic=unwind 保 17 兜底；abort/opt-z 留测量档；ts_on return 修复 c0b402d；BUDGET_BYTES=50MB 随重基线；ts-off 默认发布形双命名维持） |
| 3 | T-03 判定收口 | T-02 | budgets.json+判定报告 | installer 终态 | AC-03 | [x] **armed PASS**（30,403,072B ≤ 52,428,800B 余量 22,025,728B——portable-103531 exit 0 整链绿；103518 伪红录〔陈旧门〕如实注记；三次构建尺寸字节一致=确定性；budgets installer/idle_mem 双行改判在档） |
| 4 | T-04 护栏+烟测 | T-02 | bench 五行+烟测四段 | 零回退证 | AC-04 | [x] 双轨全绿（工具链轨五行 armed PASS：steady 17.8/open 865.8/warm 2.6/idle 9.1MB/diff 窗口 635.0ms——021/022 对照带内；产物面 probe_surface steady 17.3/open 866.5/idle 9.8MB 同带+烟测四段 exit 0——0d49e65+ad40699） |
| 5 | T-05 规范+账本 | T-01..04 | SD-01..03+specs.json | 收口落账 | AC-05/06 | [x] SD-01..04 落档（SD-04=执行期增补战略 §2.1 重基线追记）+范围断言（.at 零 diff+组双树 clean+变更路径全在 affects 域——git diff main..plan-023-dev 全列核）；P023-1 账本投影=merge 期项（015-022 先例——work 不碰活账本） |

- 2026-10-02 起草 handoff：`stage: new`，PLAN-023，plan_revision 1。

- **2026-10-02 work 进度（T-00 落）**：工作树组 edit-023 三树
  （auto-edit@plan-023-dev base 5dbfd79+auto-lang@986e765ac+auto-down
  @895f8d0 detached）+工具链 v0.4.2-2546-g986e765ac 组树 clean 重建
  〔主检出 exe=2511-dirty 纪律剔除〕。T-00 三件套落档
  （evidence-p023-survey@75d7ca6）：①三代谱 ts-off——V2b
  **30,403,072B**/opt-z **22,206,976B**/abort 记录档 **22,646,272B**
  （增量 z -8.2MB/abort -7.76MB；节表三分全列——.rdata 12.35→8.11MB
  =716 two-face 退役显影）；**组合投影 16.5~16.8MB（超门 ~1MB）——
  三路无一达门，019「距门 714KB 即可达标」叙事翻转入案**。②库存量
  R1-R9：可达池仅 R2（axum 0.7 根行 diet≈0.2~0.5MB）；tokio/reqwest/
  iced 底座=auto-lang 自声明（上游域）；image-pipeline=功能依赖实锚
  （auto_media 端点）；tungstenite=通道禁令+上游域双壁垒。③冲突面
  17 语句/8 语义点成文（会话恢复 fresh-start+512MB 拒绝门
  =load-bearing）。前置修复：stage_ts_patch ts-on 终迹 return 复位
  （c0b402d——68432be 撤钉批误删，单元级三路径验证）。`outcome:
  (执行中)`——T-01 Q-1/Q-2 请示在途（用户件）。

- **2026-10-02 work handoff（blocked）**：`stage: work` | PLAN-023
  | plan_revision 1 | `outcome: blocked` | code_commit: worktree
  plan-023-dev@**eed88ec**（base 5dbfd79；四笔=c0b402d 修复/
  75d7ca6 T-00 证据/0d49e65 T-04 五行/eed88ec 节序；worktree 清洁态
  +组双树 detached clean=AC-06 零越界）| task_ids: T-00 全落
  ／T-04 工具链轨半落／T-01 blocked／T-02/T-03/T-04 产物面/T-05
  pending（裁定后件）| evidence: evidence-p023-survey（①三代谱
  V2b 30,403,072B/opt-z 22,206,976B/abort 22,646,272B+节表三分；
  ②库存量 R1-R9 可达池仅 R2；③冲突面 17 语句/8 语义点；⑤五行
  armed PASS 全绿谱——steady 17.8/warm 2.6/open 865.8/idle 9.1MB/
  diff 窗口 635.0ms+1gb 拒绝位双复证）+portable JSONL×3+bench
  JSONL×5 入仓 | blockers: **Q-1 三路裁定+Q-2 tag 口径=用户件**
  （AskUserQuestion 2026-10-02 已发未获应答——自主会话；
  **解锁动作=用户回执三选一**（a：abort 入集·最近门但 17 语句
  兜底致命化+内核隔离破，超门 ~1MB／b：深裁 opt-z+R2·零语义
  代价，超门 ~6.2MB+上游登记／c：维持 V2b·超门 14MB 遗留）+
  Q-2（tag 带未达注记 vs tag 顺延——三路无一达门已实证，本问
  必活））| next: 用户裁定回执→T-02 终态手段集执行（依裁定）
  →T-03 判定收口（未达标=差距归因终表+裁定态注记已定局）→
  T-04 产物面收尾→T-05 规范+账本。**工作树保留**（edit-023 三树
  ——复用至 merge）。

- **2026-10-02 work handoff（pass——execution_done）**：`stage:
  work` | PLAN-023 | plan_revision 1 | `outcome: pass` |
  code_commit: worktree plan-023-dev@**ad40699**（base 5dbfd79；
  七笔=c0b402d 修复/75d7ca6 T-00/0d49e65 T-04 五行/eed88ec 节序/
  ef7189d 裁定落地批/ad40699 终态收口+范围审计；worktree 清洁态）
  | task_ids: T-00..T-05 全落（current_step 6/6）| evidence:
  evidence-p023-survey（①三代谱+节表；②库存量 R1-R9；③冲突面
  17 语句/8 语义点；⑤五行 armed PASS；⑥裁定收口+终态判定；⑦
  产物面双轨全绿）+JSONL×12 入仓（portable×5/bench×5/surface+
  smoke）| blockers: 无 | next: review。
  收口要点：①**用户重基线裁定**（两轮 AskUserQuestion——
  installer ≤50MB+idle_mem ≤150MB 渲染暖态，RQHost 后回归
  ≤15MB/≤10MB 级；手段集 (c) 变体 V2b 维持）——Q-1/Q-2 双收口
  （Q-2 消解=armed PASS 路径，tag 携重基线注记）；②判定终态
  **armed PASS** 30,403,072B ≤ 50MB 余量 22.0MB（exit 0 整链绿
  ——15MB 门时代后首绿；陈旧门伪红录如实注记）；③冲突面勘定
  为 019 未有的现役语义事实（catch_unwind×17——abort 出局的
  量化依据，上游 back_proxy 隔离面注记）；④产物双轨零回退
  （17.3/866.5/9.8MB vs 工具链轨 17.8/865.8/9.1 同带）+烟测
  四段绿；⑤P023-1 账本投影=merge 期项（015-022 先例）；⑥主检
  出外来 WIP（stylekit 两 .at）零触碰零包含维持（022 T-00⑥
  先例），落地路由属其属主会话。

- **2026-10-02 work 追记（重基线同日精调——评审基线前移）**：
  用户追询后 RQHost 期 exe 门 **15→20MB**（内存 ≤10MB 级维持）
  ——精调依据=evidence §⑥ 精调行（RQHost 单项≈24.8MB/+opt-z
  ≈16.6MB；20MB=双已知路径即达）；八面同步 commit
  worktree plan-023-dev@**b823d28**（残留 grep 零命中）；独立
  渲染期 50MB/150MB 门不变。**评审基线随 b823d28**（前录
  ad40699 为其真前缀）。`outcome: pass` 维持——范围/AC 面无
  新变化（纯承诺数字精调+文档面）。同批登记**供⑭**（RQHost 期
  tree-sitter 语法插件化 want——用户方向裁定「到时候把 TS 做成
  插件下载」，现行 ts-off/on 双形态维持零动作）入供料档 §9
  （worktree c0cc3e3）。

- **2026-10-02 merge 收据（PLAN-023:r1）**：`stage: merge` |
  plan_revision 1 | `outcome: delivered`（五检查点）——
  - **prepared**：评审基线=main@c159445 记录/worktree plan-023-dev@
    c0cc3e3（base 5dbfd79；八笔 c0b402d..c0cc3e3）；canonical
    diff=worktree 已提交面五文件（blob 冻结=review 记录五哈希）；
    projection 目标=ledger reviews 段 P023-1（24→25）。
  - **landed**：rebase main 零冲突+range-diff **8 对全 `=`**（映射
    c0b402d→cda9081/75d7ca6→0d561c6/0d49e65→d119228/eed88ec→
    41751ac/ef7189d→bda49de/ad40699→24ff800/b823d28→3e505da/
    c0cc3e3→**d2b8623**）+`git merge --ff-only` 零合并提交+main
    tip=d2b8623175f75655194c108638a5aab7d7bad86c ✓+main known-good
    烟测三绿（bench check 门+canonical 六文件 PLAN-023 锚点+账本
    可解析 24 项）。
  - **ledger_refreshed**：.autoos/specs.json reviews 段 P023-1 外科
    插入（24→25——roundtrip 守卫=json.loads 新旧深等〔他五段+
    reviews 前缀 24 项零扰动〕+插入项逐字回读；tracked 账本
    routing=主检出落定后直改+commit〔022 1dcf44d 同款先例〕）；
    P023-1 file 指 archived 路径+content=收据衍生摘要（@e138364）。
  - **archived**：git mv→docs/plans/archived/023-m4-installer-
    closeout.md+status: archived+completion_kind: delivered ✓
    （本行）。
  - **cleaned**：wt-guard 三树——auto-edit 首轮 BLOCKED（regen
    物化 junction 两枚 deps/bps+deps/stylekit——019 同款处方
    `MSYS_NO_PATHCONV=1 cmd /c rmdir` link-only 移除，目标零穿透
    [bps→组 auto-lang blueprints/stylekit→本树，均随组注销；主检出
    specs/stylekit 完好单验]）→复跑 clean；auto-lang/auto-down 一次
    clean→三 worktree 注销（auto-edit 首发静默绿）+branch 删
    plan-023-dev（was e138364——**内容全落：8 笔 ff@d2b8623+ledger
    笔 cherry-pick 54900f3 字节等价已验**）+组目录 .wt/edit-023 清
    ✓（worktree list 三仓仅余 main+他属计划组树零触碰）。
  - **路由纠偏注记（如实录）**：ledger 插入提交 e138364 实际落于
    worktree 分支（cd 后执行）——main 当时未含 P023-1；发现后
    cherry-pick→main@**54900f3**（与 e138364 版账本字节等价
    ——`git diff e138364:… 54900f3:…` 零行；main 回读 reviews=25
    latest=P023-1）；归档提交 86f4657（main）在其前——时序与
    P022 先例（landed→archive→ledger）有别但三检查点最终态齐备，
    偏差与本纠偏一并入档。
  - 部署观察：本件=tools/docs/budgets 面（无 .at/无后端/无 vue 束
    改动）——后端 release 二进制/依赖仓产物/生成 web 束零触及
    （零重建项维持，021/022 同录）；portable 产物=可再生工件
    （build_portable 一键链，非部署面）；dist/portable/auto-edit.exe
    30,403,072B=worktree 构建定稿随组注销消隐——再生即得
    （sha/尺寸收据在档）。
  - 批量回归：本仓无机制（无 .last-batch-regression.json——022
    同录不适用）。

- **2026-10-02 review**：`stage: review` | PLAN-023 | plan_revision
  1 | `outcome: pass`（→reviewed）| reviewed_commit: worktree
  plan-023-dev@**c0cc3e313e90d5e024553568426cbc4309ccc3c8**（base
  5dbfd79；九笔序列 c0b402d→75d7ca6→0d49e65→eed88ec→ef7189d→
  ad40699→b823d28→c0cc3e3；worktree 清洁态 0 dirty）|
  dependency_revisions: auto-lang@986e765ac（detached clean）+
  auto-down@895f8d0（detached clean）+工具链
  v0.4.2-2546-g986e765ac（组树 debug clean，--version 核）|
  spec_inputs: SD-01..05 目标五文件@c0cc3e3〔blob 冻结：
  perf-measurement=fcc60abe/00-overview=626b7285/README=2bedf705/
  strategy=193e5b58/供料档=5da4870e〕| 复审声明：**执行同会话
  复审——独立性限制如实声明，结论全从工件重构**（JSONL 交叉核对
  +独立重跑+live 面直调，不采信执行摘要）。
  **acceptance_results**：AC-01 pass（三谱 JSONL 实测数与 evidence
  表逐字节核对〔30,403,072/22,206,976/22,646,272〕+catch_unwind
  独立重计 **17** 语句✓+库存量表 R1-R9 在档）；AC-02 pass（两轮
  AskUserQuestion 回执+追询原文在录〔evidence §⑥〕+budgets 双行
  重基线注记+战略 §2.1 两行+追记精调段在档）；AC-03 pass（
  **armed PASS live 复证**：portable-103531 exit 0——30,403,072B
  ≤ 52,428,800B 余量 22,025,728B+dist exe sha
  06235f6727eeb9a3/size 逐字节核+**门双态在档**〔103518=
  陈旧门伪红 RED 带差距数字/103531=50MB GREEN〕+live
  evaluate_budgets 直调〔idle_mem=armed/pass@150MB 新门+installer
  =ledger@50MB 新口径——019 F-1 双 face 同步同法复核〕）；AC-04
  pass（五行 JSONL 键值全 MATCH〔17.8/2.6/865.8/635.0+1gb 拒绝
  双复证〕+smoke verdict=pass+surface_summary 全对〔17.3/866.5/
  9.8MB/exe_size 30,403,072〕）；AC-05 pass（SD-01..05 锚点五文件
  全在档〔PLAN-023 命中 1-5 处/文件〕+供⑭ 在册+P023-1=merge 期项
  路由〔015-022 先例——过程性路由非契约项，merge 轮兑现〕）；
  AC-06 pass（.at 零 diff✓+组双树 porcelain 0✓+diff 路径 21 文件
  全在 affects 域+活账本 .autoos 零触及✓）。
  **findings**：无 F 级。非发现项注记两条：N-1 surface/probe
  JSONL 指纹行=PATH 回退 2511-dirty 元数据（测量对象=dist exe
  本体直拉——判定谱工具链 2546 不受扰；证据卫生注记）；N-2
  bench assert 无参=历史谱回放器语义（输出旧态非现行——019 复审
  已勘定：实时一致性面=check/evaluate_budgets，本review 已用
  后者直调复证）。执行期语义扩展注记：SD-04（战略 §2.1）+
  门数字两轮精调（50/150→RQHost 承诺 15→20）系执行期用户裁定
  授权扩展（AskUserQuestion 回执+追询原文在录）——无先前复审
  被失效，plan_revision 维持 1（记录性/时间戳不触修订语义）。
  next: merge。
  `outcome: pass`（起草完备：三前置在位[ts-off 通道/退役翻转/手段
  谱]；**起草期核心发现=panic=abort×catch_unwind 语义冲突**——
  019 未裁门控项经 710 G-B 升格为语义冲突项，三路裁定面成文防
  默认启用；判定双态如实纪律；深裁域限下游可达防越界；路径/符号
  经 auto-edit@5dbfd79 实勘锚定[build_portable TS_FEATURE/budgets
  行/019 谱]；授权=起草[用户指令原文在录]，执行待用户启动——
  T-01 裁定为用户件）。`next: work`（T-00 可先行，裁定点在 T-01）。

## 10. 待澄清事项

- **Q-1 门控手段三路裁定（用户件——T-00 材料齐后请示）**：
  **【已裁定收口 2026-10-02：两轮 AskUserQuestion——用户提出并
  确认门重基线（installer ≤15MB→≤50MB+idle_mem ≤60MB→≤150MB
  渲染暖态；RQHost 后回归 **≤20MB**/≤10MB 级——**同日精调：
  15→20MB 经实测校准**〔RQHost 单项≈24.8MB/+opt-z≈16.6MB；
  20MB=opt-z 或 ~5MB 上游 diet 双已知路径即达〕），手段集采 (c)
  变体 V2b 维持。落档=SD-04 战略追记+budgets 双行+build_portable
  门常量+bench 断言面】**。
  **(a) panic=abort 入集**（尺寸最优路径[组合投影 **16.5~16.8MB
  ——仍超门 ~1MB**；019「距门 714KB 可达标」叙事经 716/022/工具链
  代差后翻转]——代价=try/catch 兜底降级：**生成物 17 语句/8 语义
  点** catch_unwind 失效〔evidence-p023-survey §③ 全列——会话恢复
  fresh-start/512MB 拒绝装载门=load-bearing+搜索/copy/delete 逐项
  隔离×2 成员+badge 装饰面〕+内核 back_proxy 隔离破；需逐点风险
  接受记录）；**(b) 深裁路线**（无 panic=abort——opt-z -8.2MB
  +可达池仅 R2 axum <0.5MB〔库存量表 R1-R9 实证：tokio/reqwest/
  iced 底座=auto-lang 自声明上游域；image-pipeline=功能依赖〕，
  落地 ~21.9MB **超门 ~6.2MB**——缺口归因+上游域登记）；**(c)
  分阶段维持**（V2b 30.4MB 超门 14.0MB 遗留注记——手段集零改动）。
  **核心事实：三路无一达 ≤15MB**（材料=evidence-p023-survey §①）。
- **Q-2 M4 tag 口径（随 Q-1 联动，用户件）**：**【已消解
  2026-10-02：installer 行在重基线门（≤50MB）下 armed PASS——tag
  携带「重基线注记」而非「未达注记」；战略「预算未达标的功能
  不发布」发布语义原文不受扰（重基线系预算随拓扑重分期非放宽
  换绿，回收承诺在案）】**。
- **Q-3 opt-z 护栏容差（无需裁定，确认口径）**：承 019 G-4 默认
  ——五行预算行零回退+steady ±10% 容差带；021 判定谱为对照基。
