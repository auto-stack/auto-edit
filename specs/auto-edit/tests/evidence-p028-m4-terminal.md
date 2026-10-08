# evidence-p028 — M4 终态件素材对账档（PLAN-028 T-05，2026-10-08）

> v0.1-M4.4 tag 素材（Q-2 默认命名——十行全绿/发布门解锁终态层语义；
> 打点=merge 期五检查点后惯例）。本档=tag 素材与终态工件逐字对账
> 基（027 m4-accept-green 先例）。对账域=①十行终态 ②M4 终层收口径
> ③发布门终态 ④余题清单终态 ⑤复判证据链。

## ① 预算十行终态（对账基=budgets.json@plan-028-dev + SD-01 PLAN-028 节表）

| # | 行 | 终态（028 代） | 判定谱锚 | 对账 |
|---|---|---|---|---|
| 1 | steady_start | armed PASS（021 15.6ms 首判锚；023 复跑 17.8ms 同带） | steady-20260930-204546 | ✓ 前代维持 |
| 2 | renderer_cold_start | n/a（arch note——683 重设计随形） | budgets row2 | ✓ 前代维持 |
| 3 | warm_start | armed PASS（021 0.0ms；023 复跑 2.6ms） | warm-20260930-230317 | ✓ 前代维持 |
| 4 | open_100mb | armed PASS（021 863.2ms L2 判定锚；025 后援臂红利 383.3ms 记账） | open-20260930-230121 | ✓ 前代维持 |
| 5 | open_1gb | armed PASS（025 断言化收口——E2E 断言非时间预算） | open-20261002-174223 | ✓ 前代维持 |
| 6 | type_latency | armed PASS（027 首绿+028 复证 P95 3-6ms） | frame-20261008-2150xx | ✓ 028 注记随行 |
| 7 | scroll_fps | **armed PASS（028 首绿转绿 61.0-61.7fps≥54）** | frame-20261008-2150xx+evidence-p028-drive-channel | ✓ 028 注记随行 |
| 8 | diff_100mb | armed PASS（022 窗口形 784.8ms 双谱；全量对照 FAIL 保留） | diff-20261001-144526/164312 | ✓ 前代维持 |
| 9 | idle_mem | armed PASS（9.1MB——≤150MB 重基线门下） | portable-20261002-093055 | ✓ 前代维持 |
| 10 | installer | armed PASS（30,403,072B——≤50MB 重基线） | 同上 | ✓ 前代维持 |

十行全绿：9 armed PASS+renderer n/a 唯一例外（arch note 非判定域——
683 重设计随形，不属预算判定语义）。**budget 字段 diff=零 frozen
实证**（本件 budgets.json 仅 validity/unlock 注记面增量——十行
budget/tier 语义零触碰）。

## ② M4 终层收口径点位（SD-02 00-overview M4 终态注记随行）

M4 管理收口（024）→ M4.1 能力补全（025）→ M4.2 重判收口（026）→
M4.3 验收全绿（027）→ **M4.4 十行全绿/发布门解锁终态（028/本件）**。
五层收口逐件在档（00-overview 注记链+perf-measurement SD 节链）。

## ③ 发布门终态（战略 §2.1 兑现时点成文——SD-01 PLAN-028 节）

- **发布门解锁时点=2026-10-08（PLAN-028 scroll_fps 转绿）**：十行
  预算面全绿——「预算未达标的功能不发布——性能是发布门槛（M4
  生效）」技术条件位达成。
- **解锁=预算面条件注记，非发布动作**——对外发布决策与动作（渠道/
  时机/文案）=产品决策另行（Q-3 口径延续）。
- RQHost 后严格门双承诺注记维持：idle_mem 回归 ≤10MB 级+installer
  回归 ≤20MB（渲染拓扑落地后同批议——不随本解锁失效）。
- scroll 判定读数语义如实注记：armed PASS 判读=count/window frozen
  口径（61+fps——N=4 全有效 61.0/61.7/61.0/61.3）；span 口径顶
  55-57 对 54 薄余量带并陈；满刷新率（120Hz 面板跑满）重基线语义=
  后续重估位（当前判定基=60Hz 面板×0.9——SD-01 PLAN-022 节口径）。

## ④ M4 挂账余题清单终态（SD-02 随行）

- scroll 判定读数 span 口径对满刷新率重估位（后续件）。
- renderer_cold_start n/a（683 重设计随形）。
- 供⑭ 插件化（条件件）。
- RQHost 回归门（条件触发）。
- NP++ 列（用户面——装后 harness 补跑）。
- 判定通道语义适配余题=**关闭**（027）；泵域余题=**关闭**（028——
  740 push 通道清偿+Q-1 驱动通道裁定落实施）。

## ⑤ 复判证据链（T-00..T-02 全档）

- 工具链门：v0.4.2-2769-g85f7159c2 release 组树重建 clean（edit-028
  三树：auto-edit@plan-028-dev base 25f3015+auto-lang@85f7159c2
  detached〔740@ab7a650bd+6d69dbdc7 祖先链 merge-base 双实证〕+
  auto-down@895f8d0 detached）+bench check 绿 2769≥1588。
- 740 复验：evidence-p028-upstream-reverify.jsonl（ladder740.py 处方
  复跑 1mb probe 34/54Hz——scroll follow 1.08/1.04 vs 回执 1.08/1.06
  ±10% 带内+type 1.63/1.11 同形）。
- 驱动通道标定：evidence-p028-drive-channel.jsonl（--drive-cal v2
  隔离相：serialized 43.1Hz 封顶/paced k2/4/8@60Hz follow 1.011-1.022
  带内/unpaced 474Hz 饱和参照；交付顶 ~55-61fps 全通道同顶）。
- Q-1 回执：AskUserQuestion 提请 2026-10-08，自主跑次无实时回执→
  计划 §10 预告默认臂 (b) pipelined-paced k2@60Hz 执行（标定前置
  达成背书）——**裁定随复审门确认**（计划 §10 Q-1 在案）。
- 终判谱：frame-20261008-214932（冒烟 61.0fps）+215003/215028/
  215053/215117（N=4——61.0/61.7/61.0/61.3fps+type P95 3-6ms）。
- 对比表：anchors 13 行 --verify 绿+render --check 绿（五代并陈）。
- 范围断言：零 .at diff+auto-lang/auto-down 组树双净+修订面 diff
  限 bench.py 帧区域 scroll 驱动段+probe --drive-cal 增量+compare
  双件叙事行+budgets 注记面+三 SD（详见本件提交 diff 勘界）。

## tag 素材块（merge 收据逐字引用基）

v0.1-M4.4——「M4.4 十行全绿/发布门解锁终态层」：scroll_fps armed
PASS 首绿转绿（61.0-61.7fps≥54——740 消费+Q-1 驱动通道裁定）+
type_latency 复证维持+十行预算面全绿（renderer n/a 例外）+发布门
解锁时点成文（2026-10-08，战略 §2.1 技术条件位——发布动作另行）+
五代滚动谱系收口（022 8.0→024 6.7-8.8→026 8.1-9.5→027 9.6-10.0→
028 61.0-61.7）。
