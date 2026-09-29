---
plan_id: PLAN-020
status: archived
completion_kind: delivered
feature_name: M4-03 公开对比表竞品侧先行件（测量方法论勘定+竞品同机 harness+NP++/VSCode/Zed/BC5 基线+我方锚点占位列——L2 正式列待供①）
author: [agent]
created_at: 2026-09-29T21:11:42+08:00
updated_at: 2026-09-29T22:52:30+08:00
plan_revision: 1
current_step: 6
total_steps: 6
supersedes_spec_components: []
new_spec_components:
  - docs/specs/modules/perf-measurement.md（SD-01：公开对比表节——方法论/竞品侧先行/我方列三态分层纪律）
  - docs/specs/00-overview.md（SD-02：M4 第三件注记）
  - specs/auto-edit/README.md（SD-03：PLAN-020 口径+公开对比表节占位）
touched_goals:
  - 战略 §5 公开对比（M4 关键产出「公开对比表 NP++/Zed/BC」的竞品侧先行半件）；§6 路线图 M4 行
affects: [tools/compare/（新）, specs/auto-edit/README.md, docs/specs/modules/perf-measurement.md]
---

# [PLAN-020] M4-03 公开对比表竞品侧先行件

## 0. 变更摘要

PLAN-019 交付后下游 M4 主线全数门控于上游：L2 断言全表与 regen
现势化=供①（a2r 映射残余——019 勘定 regen 探针 **133 错实录**，
last-good 基面维持）；installer 收口=two-face want（供料档 §5 已登记）
；语法高亮首批=供④。auto-lang 侧 707/708/709 三件在途均他域
（HTTP streaming/widgets-gallery 渲染响应/原生槽位交互——2026-09-29
实勘），**M4 供料包无承接**（关键路径注记：供① 承接建议路由
auto-lang 侧计划——本件不替代）。本件=对比表件中**唯一无门控的
半件：竞品侧先行**（战略 §5「README 发布与 NP++/VSCode/Zed[打开/
滚动]及 Beyond Compare[diff 计时]的同机对比表——公开可复现才有说
服力」——竞品数字不依赖我方 L2）：**测量方法论勘定**（四对象计时
通道+计时点定义——可自动化优先/不可行降级文档化手工协议）→
**同机 harness**（tools/compare/——fixture 同源 018 生成式+环境
指纹+版本钉版+多跑谱）→ **竞品基线数字**（VS Code/Zed/BC5 三家
实勘在位；**NP++ 缺位**=安装属用户面 §10 Q-1）→ **我方锚点占位列
**（018 锚点+019 产物面数字——三态注记[锚点/产物面/L2-pending]
**防冒领**）→ **表格生成器+README 占位节**（数据驱动 markdown——
我方 L2 正式列待供① 解阻后补）。

## 1. 目标

- **G-1 测量方法论勘定（T-00 决策件）**：四对象×指标通道——
  **VS Code**（`code <file>` 启动+打开 100MB：进程起→窗口就绪→文件
  装载完成探针[UIA/WinEvent/窗口标题/扩展主机就绪日志]——通道
  可行性实证）；**Zed**（同形——D:\soft\zed 在位）；**NP++**（同形
  ——**本机缺位实勘**，处置=§10 Q-1）；**BC5**（diff 100MB 计时——
  BCompare.exe CLI/脚本通道[`//silent` 形]实勘；对齐我方 diff_100mb
  档口径[同 fixture 同读盘形态]）。**滚动帧率**通道评估（屏幕捕获
  帧分析 vs 手工录屏协议 vs v1 注记后补——T-00 证据定）。**口径
  全承 018 纪律**：同机/同 fixture/多跑谱 N≥4+median/离散注记/
  沉降窗（fixture writeback 教训）。产出=方法论文档（计时点定义+
  通道结论+降级项清单）。
- **G-2 竞品测量 harness**：`tools/compare/`（compare.py 形态——
  bench.py 先例复用）：fixture 生成（100MB=018 同源参数+小文件
  档）、四对象计时通道实现、JSONL 记录（环境指纹[承 bench _finger
  print]+竞品版本钉版+跑谱）、报告器（median+离散）。
- **G-3 竞品基线数字**：打开 100MB 墙钟（VS Code/Zed/[NP++ 视
  安装]）+BC5 diff 100MB 计时——**版本+环境+跑谱全在档**（公开
  可复现三要素）。NP++ 未装期间=列在表+pending 注记（不阻塞判绿
  ——AC 口径见 §7）。
- **G-4 我方锚点占位列（三态分层防冒领）**：①018 锚点（open_
  100mb 841ms——**VM 形态注记**「记账锚点非 L2 正式判定」）；②
  019 产物面（portable exe probe_surface 数字——release a2r 形态
  但 last-good 基面注记）；③**L2-pending 位**（正式列=供① 解阻后
  L2 形态重测补列——明确注记不冒领）。三态在表格生成器里为列
  元数据（非自由文本）。
- **G-5 表格生成器+README 占位**：JSONL→markdown 表（数据驱动
  ——竞品列实数/我方列三态注记）；specs/auto-edit/README.md 增
  「公开对比表」节（占位形态：竞品实数+我方锚点注记+L2-pending
  说明——**发布动作（对外宣传）不在本件**，README 节本身即战略
  指定位置）。
- **G-6 规范+账本**：perf-measurement.md 对比表节（方法论+分层
  纪律）；overview M4 第三件注记；README 口径；specs.json P020-1。

### 非目标

- **我方 L2 正式数字列**（供① 解阻后 L2 形态重测补列——本件只
  占位注记；**不冒领**=frozen 纪律）。
- 对外发布/宣传动作（README 节=战略指定表位，对外推送/宣传=数字
  齐后另行）；滚动帧率若 T-00 判自动化不可行——降级项按 T-00 结论
  处置（手工协议 or 注记后补），不硬做不可信数字。
- 竞品侧任何改动/逆向（纯黑盒测量——进程起/参数/窗口探针仅此）；
  NP++ 安装动作（用户面——§10 Q-1）。
- M4 关键路径件（供① 承接——auto-lang 侧计划；本件并行不替代）；
  供②③④/two-face want（上游承接位维持）。
- 应用产品代码改动（.at 源零 diff；矩阵检查集零变更——判绿口径
  承 018/019）。

## 2. 架构方案

分层落点（2026-09-29 实勘，auto-edit main@94df8dc）：

| 面 | 现状 | 本期形态 | 依据 |
|---|---|---|---|
| 对比表 | 无（战略 §5 口径在册：同机/全部 L2 数字/公开可复现） | **竞品侧先行**：方法论+harness+基线数字+我方三态占位列——我方 L2 列位虚席（供① 后补） | 战略 §5/§6 M4 行；overview「对比表=下一 blocker 位」注记（L2 数字齐后件=最终态；本件=其竞品半） |
| 竞品在位 | VS Code ✓（LOCALAPPDATA）/Zed ✓（D:\soft\zed）/BC5 ✓（Program Files\Beyond Compare 5）/**NP++ ✗**（缺位实勘） | 三家实跑+NP++ pending 列（安装=用户面）；版本钉版入 JSONL | 本机探查实录（2026-09-29） |
| 测量通道 | 无竞品计时面 | 四通道勘定：启动/打开墙钟（进程起→就绪探针——UIA/WinEvent/标题/日志多通道备选）+BC5 CLI；滚动帧率通道评估 | T-00 决策件；Zed performance 页面先例（公开可复现方法论形态） |
| fixture | 018 open 档生成式（100MB 参数在册） | 同源复用（同参数同形态——跨对象可比性前提）+小文件档 | 018 bench stage_open |
| 我方数字 | 018 锚点谱+019 产物面 probe_surface JSONL 在档 | 三态列元数据（锚点[VM 形态]/产物面[last-good 基面]/L2-pending） | 018 分层纪律（锚点≠正式判定）延展 |
| 表格 | 无 | 生成器（JSONL→markdown）+README 节 | 战略「README 发布」位 |

**关键设计约束（frozen）**：
① **三态分层防冒领**——我方列不得以锚点/产物面数字冒充 L2 正式
判定（018 纪律的表内延伸：列元数据强制注记形态）。② **公开可复现
三要素**——数字必附{版本钉版,环境指纹,跑谱+离散}（缺一即不入表）。
③ 竞品黑盒纪律（仅进程级测量，无侵入）。④ fixture 同源（与我方
018 档同参数——表内可比性前提；BC5 档对齐 diff_100mb 口径）。
⑤ NP++ 缺位不阻塞判绿（pending 列注记；AC-03 以三家为门）。

## 3. 技术栈

python harness（bench.py 先例形态——环境指纹/JSONL/报告器复用）+
Windows 探针面（UIA/WinEvent/窗口标题/进程树——T-00 定通道）+
生成式 fixture（018 参数同源）。无 .at 源改动；工具链面仅我方
数字引用（018/019 JSONL 直读——不重跑）。

## 4. 需求分析与背景调查

**授权记录**：用户 2026-09-29 会话指令「计划 019 已经完成；请继续
规划下一个计划文件」——授权=**起草本件**；执行/work 待用户另行
启动。范围=auto-edit 单仓（tools/docs——竞品测量只读黑盒+specs
文档面）；auto-lang 零改动（供① 承接建议路由其本仓计划——§0
注记）。无预算/自动续跑授权。

**来源与版本**：

- 交接链：PLAN-019 归档件（delivered@94df8dc）——M4 第二件注记
  尾行「对比表=下一 blocker 位（L2 数字齐后件——供① 解阻+锚点
  L2 化前置）」；019 手段终表/门控组合 16.46MB 数据/two-face want
  （供料档 §5）。
- 战略口径：§5 性能文化（「公开对比：README 发布与 NP++/VSCode/
  Zed[打开/滚动]及 Beyond Compare[diff 计时]的同机对比表——'最快/
  最好比对'只有公开可复现才有说服力[Zed performance 页面先例]。
  全部为 L2 数字」）；§6 M4 行（公开对比表=四关键产出之三）。
- 现状实勘（auto-edit main@94df8dc + 本机 2026-09-29）：overview
  M4 第二件注记；budgets diff_100mb 达标谱（018）；018/019 JSONL
  在 results/；竞品在位探查（VS Code/Zed/BC5 ✓、NP++ ✗——四处
  常见安装位查证）。
- 上游实勘（auto-lang master@66c9cac19）：707（HTTP stream async
  relay）/708（vm-render-responsiveness——widgets-gallery 域 r2
  修订稿）/709（原生槽位交互）三件在途**均非 M4 供料包承接**——
  供①..④+§5 want 排队位维持（关键路径注记依据）。
- 历史关联：PLAN-006（L2 基线报告先例——同机多跑谱方法论形态）、
  018（fixture 参数/纪律/锚点）、019（产物面 probe_surface 数字）。

## 5. 详细设计

### T-00 测量方法论勘定（决策件，产物=方法论文档）

1. **打开 100MB 墙钟通道**（VS Code/Zed/NP++ 形）：启动态探针
   候选——UIA 就绪事件/WinEvent 窗口显示/窗口标题变化/进程 CPU
   降落/各家日志面（VS Code 扩展主机日志形）——**每对象双通道
   以上实证**取稳态主通道+备通道（离散对照）；计时点定义成文
   （t0=CreateProcess、t_ready=探针命中——「文件装载完成」语义
   对齐我方 BENCH 装载完成标记）。
2. **BC5 diff 计时通道**：BCompare.exe CLI 形（`//silent`/脚本
   比较）实勘——可比对我方 diff_100mb 口径（同 fixture、同
   「出结果」语义[结果窗生成/脚本输出]）。
3. **滚动帧率通道评估**：屏幕捕获帧分析（ DXGI/ffmpeg 抽帧法）
   成本与可信度 vs 手工录屏协议 vs v1 注记后补——证据定案（默认
   倾向：v1 注记后补=供② 帧插桩与我方 L2 列同期，避免竞品侧先行
   的帧率数字与我方口径错位）。
4. **NP++ 处置**：缺位注记+pending 列（安装=用户面 §10 Q-1——
   不擅自安装）。
5. **手工协议降级模板**（不可自动化项）：计时点定义+步骤+双人/
   录屏凭证要求（若 T-00 判某通道必须手工）。

### T-01 竞品测量 harness（G-2）

`tools/compare/compare.py`：对象注册表（exe 路径+版本读取+通道
绑定）；fixture 生成（018 同源参数复用——100MB 档+小文件档）；
`run <对象> <档>`→JSONL（环境指纹+版本+跑谱行）；`report`→median
+离散表。bench.py 模块复用（指纹/报告器形制）。

### T-02 竞品基线跑谱（G-3）

四对象×档位 N≥4 跑谱（沉降窗纪律——018 教训）；产物=竞品基线
JSONL+报告（VS Code/Zed/BC5 实数；NP++ pending 行）。

### T-03 我方锚点占位列（G-4）

018/019 JSONL 直读（不重跑）→三态列数据（锚点/产物面/L2-pending
——列元数据形）；「VM 形态/last-good 基面」注记随行。

### T-04 表格生成器+README 节（G-5）

JSONL→markdown 表生成器（`tools/compare/render_table.py` 形——
数据驱动，三态列元数据渲染）；specs/auto-edit/README.md 增「公开
对比表」节（表+方法论链接+可复现三要素说明+L2-pending 说明——
README 节=战略指定表位）。

### T-05 规范增量+账本（G-6）

perf-measurement.md 增「公开对比表」节（SD-01——方法论摘要/三态
分层纪律/竞品侧先行边界）；overview M4 第三件注记（SD-02）；README
PLAN-020 口径（SD-03）；specs.json P020-1 投影（015-019 外科插入
先例）。

### 规范增量

| delta_id | add/modify/retire | docs/specs/... target | before/after rule | rationale | acceptance IDs |
|---|---|---|---|---|---|
| SD-01 | modify | docs/specs/modules/perf-measurement.md | before：预算断言五态机制在册；无对比表面 / after：增「公开对比表」节——竞品侧先行方法论（计时点定义/通道/降级协议）+可复现三要素{版本,环境,跑谱}+我方列三态分层纪律（锚点[VM 形态]/产物面[last-good]/L2-pending——冒领禁则） | 战略 §5 表位的规范锚 | AC-01/04 |
| SD-02 | modify | docs/specs/00-overview.md | before：M4 第二件注记（对比表=下一 blocker 位） / after：M4 第三件注记（竞品侧先行件——基线数字在档+我方 L2 列虚席待供①；关键路径=供① 承接注记维持） | 面进度总览承接 | AC-06 |
| SD-03 | modify | specs/auto-edit/README.md | before：PLAN-019 口径 / after：PLAN-020 口径+「公开对比表」节（表+三要素+L2-pending 说明——战略指定表位落位） | 运行矩阵/工具单源+战略表位 | AC-05/06 |

## 6. 测试设计

- **harness 验证**：`run`/`report` 一键链 exit 0+JSONL 在档+幂等
  复跑；环境指纹与版本钉版字段完整性（缺一即 report 拒出数——
  三要素门内建）。
- **通道稳定性**：每对象主/备通道双测（离散对照——主备差>阈值
  通道存疑处理）；N≥4 跑谱离散注记（018 四跑谱先例）。
- **数字可复现**：竞品基线行=同机重跑复现（±容差注记——机器态
  漂移如实记录）；我方占位列与 018/019 JSONL 数字逐字对照（直读
  零重算——grep 锚）。
- **表格生成器**：三态列元数据渲染断言（L2-pending 列不得出数）；
  markdown 结构 lint（表列对齐）。
- **矩阵零扰动**：.at 源零 diff；判绿口径承 018/019（本件不动
  检查集）。

## 7. 验收标准

- **AC-01 方法论文档**：四对象通道结论+计时点定义+降级项清单在
  档（含 NP++ 处置与滚动帧率 T-00 结论）。验证：文档在档+结论有
  探针证据行。
- **AC-02 harness**：一键链 exit 0+JSONL（环境指纹+版本钉版+跑
  谱）+幂等复跑绿。验证：执行记录+文件在档。
- **AC-03 竞品基线**：VS Code/Zed/BC5 三家数字在档（N≥4 跑谱+
  median+离散注记）；NP++=pending 注记行（不阻塞判绿）。验证：
  基线 JSONL+报告。
- **AC-04 我方占位三态**：锚点/产物面数字与 018/019 JSONL 逐字
  对照一致；L2-pending 列零数字（生成器断言）。验证：对照表+生成
  器测试。
- **AC-05 README 表节**：表格+三要素说明+L2-pending 说明在档
  （数据驱动生成——手改禁则注记）。验证：README 节在档+生成器
  复现一致。
- **AC-06 规范+账本**：SD-01..03 落档+specs.json P020-1 回读
  True。验证：文件在档+账本断言。
- **AC-07 范围零越界**：.at 源与矩阵检查集零 diff；auto-lang 主树
  零改动；竞品纯黑盒（无文件写入竞品安装域）。验证：双仓
  porcelain+diff --stat 路径断言。

## 8. 执行步骤

| # | 任务 | 依赖 | 落点（实勘锚） | 产出/意图 | AC | 验证（命令/预期） |
|---|---|---|---|---|---|---|
| 0 | T-00 方法论勘定 | — | 本件 §5 T-00 节+方法论文档（tools/compare/） | 四通道定案+计时点定义 | AC-01 | [x] **[修复回勾 2d77cf8]** F-2 关闭（median 约定成文）——review 首轮发现：median 约定未成文（实录=上中位 sorted[N//2]，bench.py 家法/018 锚点 841.0 同法；标准复算不一致且未注明——须在 METHODOLOGY §5+report 表头成文）——修复后随复审回勾。原执行证据：方法论在档 tools/compare/METHODOLOGY.md（§2 计时点定义/§3 探针证据行/§6 降级清单/§6-b 环境干扰条款）——四通道定案：VS Code=renderer RSS 平台（文本模型物化语义，1.5s 滑窗极差判据）、Zed=Zed.log「Rendered first frame」（首帧语义，rope 惰性注记 RSS~19MB）、BC5=file-report 非空（`&` 续行+/silent 语法勘定）、NP++=pending；滚动帧率=v1 后补（Q-2 默认维持——前台权拒绝+捕获面污染他窗双缺陷实证）；VS Code 版本钉版=文件元数据 1.139.1（CLI --version 直启挂起 63s+自更新中间态 bash 包装器陈旧通道双缺陷；app 目录 04c0d99f4f/7debcd0e2a 双立在案） |
| 1 | T-01 harness | T-00 | tools/compare/compare.py | 一键测量链 | AC-02 | [x] check/run/report 三子命令绿（check 四对象在位+版本；run zed/vscode/bc5 5mb 各 -n 3/-n 4 exit 0+JSONL 在档+幂等复跑）；report 三要素门实证拒出（残缺文件「头/摘要行缺」拒出数 exit 1）；通道判据 bug 两连修实录（deque(maxlen=24) 5ms 轮询下窗跨 ~200ms<1500ms 永假 → 时间窗裁剪；再 popleft 阈值=判据阈值使 >= 永假 → 1.2× 裁剪余量定案——VS Code 5mb 曲线 584MB 峰→448-450MB 平台@4.6s 直证）；invalid-run 重跑条款落地（VS Code 间歇 rc=0 自退现象谱 1/3、2/3、0/1——014 F-RV6 归因纪律延展，连续两跑无效 abort 示知） |
| 2 | T-02 竞品基线跑谱 | T-01 | results/（compare JSONL） | 三家实数+NP++ pending | AC-03 | [x] 官方谱六组合全绿（-n 5 首跑弃暖机 N=4 计入，results/ 入仓）：open 5mb——VS Code 4289.1ms[4256.3–4340.8]/Zed 296.0[272.6–310.0]；open 100mb——VS Code 4677.7[4621.4–4718.5]/Zed 295.6[275.4–310.3][rope 惰性=与 5mb 同量级实证]；diff 100mb——BC5 123,279.8[119,849.6–126,246.9]（对探针首测 91.6s 差=盘缓存态变异，N=4 median 承载）；diff 5mb——BC5 4547.7（备档）；NP++=pending 行（§10 Q-1 维持）。通道勘定插曲实录：VS Code 100MB 判据两轮校准（假平台嫌疑→密采样曲线定案 0–2.8s 爆发装载至 807MB+GC 回落→确认窗分档 5MB=3s/100MB=6s——判据落点=GC 沉降后稳定位，偏竞品有利侧；早期粗采样「爬升 ~12s」读数勘误为 GC 振荡伪影） |
| 3 | T-03 我方占位列 | — | 018/019 JSONL 直读 | 三态列数据 | AC-04 | [x] anchors.py 六行三态全绿（直读零重算）：anchor=open_100mb 841.0ms[VM 形态注记，open-20260929-110820]/surface=open 38.2ms+steady 21.2ms[last-good 基面注记，surface-20260929-193232]/release-judged=diff_100mb 1906.0ms[016 先例仅限 diff，diff-20260928-152047，旁证 152015=1971.3]/l2-pending×2 零数字；--verify 逐字对照绿（AC-04）；直读源扩 016 diff 谱=BC5 行我方对照必需（018 分层纪律内语义，语义注记随行） |
| 4 | T-04 表生成器+README | T-02/03 | tools/compare/render_table.py+README | 数据驱动表+节占位 | AC-05 | [x] 表落 specs/auto-edit/README.md 文末「公开对比表」节（BEGIN/END 生成区间+手改禁则引言）；--check 双复现一致绿；l2-pending 渲染断言禁出数内建；三要素门竞品格缺一拒出数；生成器区间判定 bug 一修（引言误入比对域→区间收缩至 [BEGIN..END]，引言归静态面）；results/table.md 独立件同源 |
| 5 | T-05 规范+账本 | T-00..04 | SD-01..03+specs.json | 对比表面落账 | AC-06 | [x] **[修复回勾 2d77cf8]** F-1 关闭（分档措辞）——review 首轮发现：SD-01/SD-02「3s 确认窗」措辞须改分档（5MB=3s/100MB=6s——METHODOLOGY 已正确，canonical spec 与现行为偏差）——修复后随复审回勾。原执行证据：SD-01 落档（perf-measurement.md 增「公开对比表」节——方法论摘要/三态分层纪律/三要素/工具面/边界五段）+SD-02 落档（00-overview.md M4 第三件注记——L2 列仍虚席+关键路径注记维持）+SD-03 落档（README PLAN-020 口径段+表节）；P020-1 账本投影=merge 期项（016/017/018/019 先例——work 不碰活账本，随 review/merge 轮兑现，AC-06 全满足于 merge 收口） |

**执行记录**（skill §7 要求项）：worktree=`D:/autostack/.wt/edit-020/auto-edit`
（branch `plan-020-dev`，base=main@94df8dc，2026-09-29 创建）；依赖修订=
无（本件零依赖仓改动——auto-lang/auto-down 主树零触碰）；主检出预检=
stylekit 两删除（`specs/stylekit/pac.at`+`src/front/styles.at`）=019 归档
件已裁定的他属 WIP，零纳入零触碰；探针通道实证于本机 2026-09-29
（VS Code 1.139.1 自更新中间态/Zed 1.20.2/BC5 5.0.6.30713，证据
logs/probe-*.json）。

## 9. 复审记录

- 2026-09-29 起草 handoff：`stage: new`，PLAN-020，plan_revision 1。
  `outcome: pass`（起草完备：下游 M4 全门控现状实勘成立[供①
  regen 133 错/对比表 L2 前置/供④]——竞品侧=唯一无门控半件且为
  战略表位必经；三态分层防冒领纪律承 018；竞品在位三家实证+NP++
  缺位处置成文；关键路径[供① 承接路由 auto-lang]显式注记不与
  本件混淆；路径/符号经 auto-edit@94df8dc+auto-lang@66c9cac19+
  本机探查三源锚定；授权=起草，执行待用户启动）。`next: work`。

- 2026-09-29 work handoff：`stage: work`，PLAN-020，plan_revision 1。
  `outcome: pass` | code_commit: worktree plan-020-dev@**e8ea6f4**
  （base 94df8dc；单笔全落 T-00..T-05，worktree 清洁态）|
  task_ids: T-00..T-05 全落（current_step 6/6）| evidence: AC-01
  方法论在档（四通道定案+计时点定义+降级清单+环境干扰条款，探针
  JSON 证据在 logs/）；AC-02 harness 三子命令绿+幂等复跑+三要素门
  实证拒出（残缺文件拒出数 exit 1 实录）；AC-03 官方基线六组合
  N=4 计入 median+离散全在档（VS Code 4289.1/4677.7、Zed 296.0/
  295.6、BC5 4547.7/123,279.8ms——NP++ pending 行）；AC-04 anchors
  六行三态直读零重算+--verify 逐字对照绿+l2-pending 渲染断言禁
  出数；AC-05 README 表节落位+--check 双复现一致+手改禁则；AC-06
  SD-01..03 全落档（P020-1 账本投影=merge 期项——016..019 先例，
  AC-06 全满足于 merge 收口）；AC-07 范围零越界（worktree porcelain
  面=tools/docs+.gitignore 四文件；.at 源零 diff；auto-lang 主树
  本会话零触碰[其现存修改=707/709 在途会话他属 WIP]；竞品纯黑盒
  ——自建 temp profile，零安装域写入）。执行勘定要点：VS Code
  版本钉版=文件元数据 1.139.1（CLI --version 直启挂起 63s+自更新
  中间态 bash 包装器陈旧通道双缺陷，app 目录双立在案）；通道判据
  三连修（deque 窗永假×2→时间窗+1.2× 裁剪余量；确认窗分档
  5MB=3s/100MB=6s——100MB 密采样曲线定案 0–2.8s 爆发装载+GC 回落，
  判据落点=GC 沉降后稳定位偏竞品有利侧）；VS Code 间歇 rc=0 自退
  现象谱在案（invalid-run 单次重跑条款，连续两跑无效 abort——
  014 F-RV6 归因纪律延展）；滚动帧率=v1 后补（§10 Q-2 默认维持
  ——捕获自动化双缺陷实证：前台权拒绝+捕获面污染他窗）。worktree
  =D:/autostack/.wt/edit-020/auto-edit（留 review/merge 用）|
  blockers: 无（§10 Q-1 NP++ 安装=用户面待裁定，不阻塞判绿——
  pending 列已落）| next: review（P020-1 账本投影随 merge 轮兑现）。

- 2026-09-29 review：`stage: review`，PLAN-020，plan_revision 1。
  `outcome: needs_fix` | reviewed_commit: worktree plan-020-dev@
  e8ea6f4054e5330de699acdc952d4862a18b70d7（base 94df8dc；worktree
  清洁态）| dependency_revisions: 无依赖仓改动 | spec_inputs:
  docs/specs/modules/perf-measurement.md@e8ea6f4/00-overview.md@
  e8ea6f4/specs/auto-edit/README.md@e8ea6f4 | **同会话复审限定声明**：
  本审读在实现会话内进行（用户授权同链），结论按技能要求从工件
  重建（只读验证重跑+独立复算+负例测试），不依赖执行者摘要。
  acceptance_results: AC-01 pass（方法论在档+结论有探针证据行）/
  AC-02 pass（check+report 只读重跑绿；幂等=执行期双跑双文件实录；
  负例双测绿——l2-pending 出数断言拦截+三要素门拒出 rc=1+
  _load_latest 残缺文件 None[临时 RESULTS 零入仓]）/ AC-03 **partial**
  （六文件 N≥4+三要素齐全独立复核绿；README/表数字交叉抽查一致；
  但 median 复算失配→F-2）/ AC-04 pass（anchors --verify 绿+负例
  断言）/ AC-05 pass（--check 绿+数字抽查）/ AC-06 pass（SD-01..03
  grep 锚在档；P020-1=merge 期项注记在案）/ AC-07 pass（--name-only
  路径断言零越界+零 .at+auto-lang 本会话零触碰）。**findings**:
  **F-1（minor→须修）** SD-01/SD-02「3s 确认窗」措辞落后于分档实现
  （5MB=3s/100MB=6s——METHODOLOGY 已正确，canonical spec 文本与
  现行为偏差；技能要求 delta 描述现行为）；**F-2（medium→须修）**
  median 定义未成文——harness 记录值=上中位 sorted[N//2]（六官方
  文件逐一精确复核全等；bench.py 家法一致——018 锚点 841.0 同为
  上中位），但标准复算（statistics.median）不一致[BC5-100mb 记录
  123279.8 vs 标准中位 122985.7]且 METHODOLOGY/report 表头未注明
  约定——公开可复现表口径缺口。修复面=纯文档措辞（METHODOLOGY
  median 约定成文+report 表头注记+SD-01/02 分档措辞），零重测零
  数字变更。evidence: 本记录内命令/结果摘录（results/ JSONL 持久
  在仓）| next: work（单轮有界修复——F-1/F-2；修复后复审按未变
  代码重用既有证据+定点重验）。

- 2026-09-29 review（修复轮复审）：`stage: review`，PLAN-020，
  plan_revision 1。`outcome: pass` | reviewed_commit: worktree
  plan-020-dev@**2d77cf8**（F-1/F-2 修复；base 仍 94df8dc；
  worktree 清洁态）| spec_inputs: perf-measurement.md@2d77cf8/
  00-overview.md@2d77cf8/README.md@2d77cf8+METHODOLOGY.md@2d77cf8
  | **证据重用声明**：修复轮=纯文档措辞（git show --stat 四文件：
  00-overview/perf-measurement/METHODOLOGY/compare.py——零测量
  零数据零机制变更），首轮已重跑的只读验证（report/anchors
  --verify/--check）与负例双测对未变面继续有效（复审当轮再证：
  report 表头新注记在位、anchors --verify 绿、--check 绿——
  修复提交前即时复跑三项全绿在执行实录）。acceptance_results:
  AC-01 pass（F-2 关闭——median 约定 METHODOLOGY §5 frozen 成文，
  三处「上中位」锚）/ AC-02 pass（同首轮+report 表头注记定点绿）/
  AC-03 pass（F-2 关闭——六官方文件实录值=上中位逐文件精确复核
  全等[首轮独立复算证据]；约定成文后复算口径闭合）/ AC-04 pass
  （首轮+定点）/ AC-05 pass（--check 修复后绿——表内容零变更）/
  AC-06 pass（F-1 关闭——SD-01/02 分档措辞 grep 锚：perf-
  measurement「分档 5MB=3s/100MB=6s」+overview「确认窗分档防假
  平台：5MB=3s/100MB=6s」；P020-1=merge 期项注记维持）/ AC-07
  pass（修复轮 diff --stat 四文件均在既授权面）。findings: 无
  未决 | next: merge（P020-1 账本投影随 merge 轮兑现）。

## 10. 待澄清事项

- **Q-1 NP++ 安装（用户面）**：本机缺位实勘（四处常见安装位）。
  战略对位产品（M2 验收面即「替代 Notepad++」）——对比表缺 NP++
  列=明显缺口。**安装动作=用户裁定**（winget/scoop/官网便携版均可
  ——建议便携版免污染）；装后 harness 补跑即得列（通道与 VS Code
  同形）。未装期间 pending 列注记不阻塞本件判绿。
- **Q-2 滚动帧率竞品侧口径（无需裁定，确认默认）**：T-00 默认倾向
  =v1 注记后补（与我方 L2 列+供② 帧插桩同期——避免竞品帧率数字
  与我方口径错位后返工）；若用户希望竞品侧先行出帧率数（屏幕捕获
  帧分析法），执行期示知——T-00 ③ 将按示知改判。
  **执行期处置（2026-09-29）**：默认维持成立——屏幕捕获自动化双
  缺陷实证（前台权拒绝[SetForegroundWindow 败]+全屏捕获面污染他
  窗[首测捕到无关应用内容，证据件即删]；PrintWindow 仅静态单窗无
  滚动时序），METHODOLOGY §2/§6 定案 v1 注记后补。
- **Q-3 表发布形态（无需裁定，确认口径）**：README 节=战略指定
  表位；「发布」动作（对外宣传/链接分发）=数字齐后另行——本件
  只落表与方法论。

- 2026-09-29 merge：`stage: merge`，PLAN-020:r1，`outcome: pass`。
  **prepared**：评审基线=worktree plan-020-dev@2d77cf8（pass 复审
  @e8d1793 记录）；canonical delta=SD-01..03 已在评审提交内
  （e8ea6f4 落+2d77cf8 修）；投影目标=.autoos/specs.json reviews 段
  P020-1（file 预指归档位）；SD-03 落 specs/auto-edit/README.md=
  运行矩阵单源成文惯例（00-overview 规范结构节+011..019 五件先例
  +018/019 口径节在 main——docs/specs 之外先例核查在案）。
  **landed**：rebase main 后 range-diff 全等证明（`e8ea6f4 =
  46917d4`、`2d77cf8 = 125b79f` 补丁恒等——安全重写证明）；旧→新
  映射[e8ea6f4→46917d4, 2d77cf8→125b79f, a99b733→4c14c8e]；
  `git merge --ff-only` 落地**零合并提交**，main tip=**4c14c8e**
  （delivery commit=纯账本投影后代，diff 2d77cf8..a99b733 仅
  .autoos/specs.json+12 行——实现/依赖零变更核验在案）；main 烟测
  =report/anchors --verify/render --check 三绿（落地后即时复跑）。
  **ledger_refreshed**：P020-1 外科插入 19→20 项（roundtrip 字节
  等价先证 indent=2/ascii=false/尾换行；回读断言前 19 项深等+他
  五段深等+尾插在位——断言初版把整文档 dict 与 items list 相比恒
  假[审查 bug 非数据问题]，以 git HEAD~1 为基准重验绿；断言先跑
  与 git add 换行串联未短路致提交先于验证落——流程失误如实注记，
  数据本体验证绿后 a99b733 保留）+落地后 main 回读 20 项末项
  P020-1 ✓。**archived**：git mv → docs/plans/archived/020-m4-
  compare-table-competitor-side.md+status: archived+completion_kind:
  delivered。**cleaned**：待回填（wt-guard→注销→组目录清）。部署
  观察：本件=tools/docs 面（compare 工具+规范文档+README）——零
  重建项（无产品二进制/vue 束/依赖仓产物消费面；bench/portable
  工具链零触碰）。