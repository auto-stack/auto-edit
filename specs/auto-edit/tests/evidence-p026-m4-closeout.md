# evidence-p026 — M4 完全体收口件终态+预算十行+v0.1-M4.2 tag 素材（PLAN-026 T-04，2026-10-03）

> 收口语义=**Q-2 默认臂（双态如实）**：帧两行终判 FAIL 维持——本件
> =「重判收口」件（731 消费重判完成+归因换代落账），**非十行全绿
> 件**；v0.1-M4.2 tag 语义随降（发布门不解锁，如实注记）。

## 预算十行终态（026 收口态——对账基=tools/bench/budgets.json@plan-026-dev+判定谱 JSONL）

| # | 行 | 预算 | 终态（026 代） | 溯源（grep 锚） |
|---|---|---|---|---|
| 1 | steady_start | ≤80ms | **armed PASS**（021 首判 15.6ms；023 复跑 17.8ms 同带） | budgets row1+steady-20260930-204546 |
| 2 | renderer_cold_start | 随 Q2 | **n/a**（arch note——单 iced 进程内无分离冷启面；683 重设计随形重估） | budgets row2 |
| 3 | warm_start | ≤120ms | **armed PASS**（021：恢复净段 0.0ms；023 复跑 2.6ms） | budgets row3+warm-20260930-230317 |
| 4 | open_100mb | ≤1s | **armed PASS**（021 直拉 863.2ms L2 判定锚；025 后援臂红利 383.3ms 记账） | budgets row4+open-20260930-230121/20261002-174223 |
| 5 | open_1gb | 可打开（流式） | **armed PASS（025 断言化收口）**——装载成功 E2E 断言（非时间预算）；1GB 装载 3774.4ms 上游带内+四链 byte-for-byte | budgets row5+open-20261002-174223 |
| 6 | type_latency | ≤1 帧 | **armed FAIL 维持（026 代）**——P95 156-160ms vs 16.7ms（三代谱系 022 110/115→024 95-112→026 156-160）；归因换代=S5 工作面清偿实证（段外 ~108ms 消散→s5 子段 0.1-0.2ms）+红面=帧泵呈现交付通道（上游域余题第二段） | budgets row6+frame-20261003 四谱+evidence-p026-frame-rejudge |
| 7 | scroll_fps | 满刷新率 | **armed FAIL 维持（026 代）**——8.1-9.5fps vs ≥54（三代同带 8.0/6.7-8.8/8.1-9.5）；交付节奏同源归因 | budgets row7+同上 |
| 8 | diff_100mb | ≤2s | **armed PASS**（022 窗口形 784.8ms 双谱；全量对照档 5183.2ms FAIL 保留在档） | budgets row8+diff-20261001-144526/164312 |
| 9 | idle_mem | ≤150MB（重基线） | **armed PASS**（空窗 9.1MB——023 重基线门下维持；RQHost 后回归 ≤10MB 级承诺） | budgets row9+portable-20261002-093055 |
| 10 | installer | ≤50MB（重基线） | **armed PASS**（30,403,072B 余量 22.0MB——V2b 终态；RQHost 后回归 ≤20MB 承诺） | budgets row10+同上 |

**十行口径：8 PASS+2 FAIL（帧两行）+renderer n/a——十行全绿未达；
发布门维持不解锁（战略 §2.1「预算未达标的功能不发布」如实执行）。**

## M4 三层收口径（本件点位）

1. **M4 管理收口（PLAN-024）**：预算门/四面核销/终检表+tag——已录。
2. **M4.1 能力补全（PLAN-025）**：open_1gb 断言化收口（供⑮ 消费）——已录。
3. **M4.2 验收收口（PLAN-026=本件）**：731 消费重判+归因换代落账——
   **重判收口态**：S5 增量化下游生效实证（帧工作面清偿）+红面换代
   =帧泵呈现交付节奏+判定通道语义适配（均上游域余题第二段）；
   三代谱系全档不删；对比表滚动行三代并陈（--verify 11 行+--check
   双绿）。

## 余题清单终态（tag 注记位——全条件件/上游域）

- **帧泵呈现交付节奏**（上游域余题第二段——731 清偿帧工作面后
  余留：`__frame_pump` 消费滞后/合并+交付率实测 8-9.5fps）；
- **判定通道语义适配**（fprobe_present 读回=泵消费时刻 vs 022
  帧内口径——需上游提供帧工作完成时刻通道或裁定消费时刻通道
  判定语义）；
- 供⑭ tree-sitter 插件化+RQHost 回归门 20MB/10MB（条件触发——
  RQHost 落地后）；
- NP++ 对比表列（用户面——装后补跑即得列）。

## v0.1-M4.2 tag 素材（打点=本件 merge 收据位——v0.1-M1..M4.1 惯例；annotated tag）

```
M4.2 重判收口（PLAN-026——731 消费帧两行终判+M4 完全体三层收口径点位）

PLAN-026：auto-lang PLAN-731（S5 帧尾段增量化 delivered@30bda6831）下游消费重判
——重判前置四门全绿（工具链 v0.4.2-2640-gcb2da5fba release 组树重建核哈希+731
上游谱带内复验三线全带内+帧档 frozen 断言 stage_frame 逐字节全等+面板读回 60Hz）；
终判 N=4 全有效谱 FAIL 维持（type P95 156-160ms vs ≤16.7ms/scroll 8.1-9.5fps vs
≥54——三代谱系 022/024/026 全档不删）；归因换代双态如实：S5 增量化下游生效实证
（024 段外 ~108ms 消散→s5 三子段 0.1-0.2ms+突发重建退位单帧单建——帧工作面全绿
余量 ~8×）+红面换代=帧泵呈现交付通道（__frame_pump 消费滞后/合并+判定通道语义
漂移——上游域余题第二段，回执 evidence-p026-frame-rejudge）。

预算十行（M4.2 态）：steady 15.6ms PASS｜warm 0.0ms PASS｜open_100mb 863.2ms PASS
｜open_1gb armed 断言化 PASS（025——E2E 断言+装载 3774.4ms 带内）｜diff 窗口
784.8ms PASS（全量对照 FAIL 在档）｜idle 9.1MB PASS（≤150MB 重基线）｜installer
30,403,072B PASS（≤50MB 重基线）｜renderer n/a｜type_latency P95 156-160ms FAIL
维持（026 代）｜scroll 8.1-9.5fps FAIL 维持（026 代）。

M4 完全体三层收口径：M4 管理收口（024）+M4.1 能力补全（025 open_1gb）+M4.2 重判
收口（本件）——预算面 8 PASS+2 FAIL+renderer n/a；发布门维持不解锁（战略 §2.1
「预算未达标的功能不发布」如实执行——复判前置=帧泵呈现交付节奏+判定通道语义适配
两上游余题清偿）。

余题终态：帧泵呈现交付节奏+判定通道语义适配（上游域第二段）/供⑭ 插件化+RQHost
回归门 20MB/10MB（条件触发）/NP++ 列（用户面）。

v0.1-M4.2=里程碑标记非发布（对外发布前必须全绿含 RQHost 后 ≤20MB/≤10MB 级回归
门——023 Q-2 用户裁定口径维持）。
```

**打点落位注记**：tag 动作=merge 阶段五检查点后（收口件 merge 收据
惯例——v0.1-M1 b497db7/M2 ed8c107/M3 f4e34c1/M4/M4.1 先例）；对象
=merge 后 main tip commit；`git tag -a v0.1-M4.2 -F <素材>`（Q-1
默认命名）；素材数字与十行终态表逐字一致（本档对账）。

## 731 消费回执（对 upstream 的下游收据——669 模式）

- **清偿确认**：S5 帧尾段增量化下游生效实证（024 段外 ~108ms 帧工
  作→026 s5 三子段 0.1-0.2ms 同上游谱带内；突发重建退位单帧单建）。
- **余题第二段登记**：①帧泵呈现交付节奏（dirty 帧真呈现率 ~11%
  消费滞后/合并+scroll 交付率 8-9.5fps 实测——下游可观测红面）；
  ②判定通道语义适配（fprobe_present=泵消费时刻——与 022 帧内
  口径「键入帧 begin→下一 present 差」的判定语义需上游裁定/供
  帧工作完成时刻通道）。
- **复验异常观察位**：100kb/typenl 相位 MCP 中途拒连一次（app 疑
  似瞬态退出——evidence-p026-upstream-reverify.jsonl 复验谱注记；
  下游四跑同窗零复现）。
