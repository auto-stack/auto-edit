# evidence-p024 — M4 四面终检表+预算十行终态+v0.1-M4 tag 素材（PLAN-024 T-04，2026-10-02）

## 预算十行终态（对账基=tools/bench/budgets.json@plan-024-dev+判定谱 JSONL）

| # | 行 | 预算 | 终态 | 溯源（grep 锚） |
|---|---|---|---|---|
| 1 | steady_start | ≤80ms | **armed PASS**（021 首判 15.6ms；023 复跑 17.8ms 同带） | budgets row1+steady-20260930-204546 |
| 2 | renderer_cold_start | 随 Q2 | **n/a**（arch note——单 iced 进程内无分离冷启面；683 重设计随形重估） | budgets row2 |
| 3 | warm_start | ≤120ms | **armed PASS**（021：恢复净段 0.0ms；023 复跑 2.6ms） | budgets row3+warm-20260930-230317 |
| 4 | open_100mb | ≤1s | **armed PASS**（021 直拉 863.2ms；「滚动不掉帧」半行=帧两行域注记） | budgets row4+open-20260930-230121 |
| 5 | open_1gb | 可打开（流式） | **ledger-blocked-with-plan（用户裁 (b)，2026-10-02）**——供⑮ 文件后援分页 rope want 入供料档 §10（完整标准设计）；512MB 拒绝位活体维持至供⑮ 交付 | budgets row5+供料档 §10+designs/002 回执 |
| 6 | type_latency | ≤1 帧 | **armed FAIL 维持**（024 重判 P95 95-112ms vs 16.7ms；725 中位 110→1-4ms ~30×——S5 段 layout/shaping/draw 残差归因=auto-lang 余题） | budgets row6+frame-20261002 四谱+evidence-p024-frame-rejudge |
| 7 | scroll_fps | 满刷新率 | **armed FAIL 维持**（024 重判 6.7-8.8fps vs ≥54；022 首判 8.0 同带——S5 域同源） | budgets row7+同上 |
| 8 | diff_100mb | ≤2s | **armed PASS**（022 窗口形 784.8ms 双谱；全量对照档 5183.2ms FAIL 保留在档） | budgets row8+diff-20261001-144526/164312 |
| 9 | idle_mem | ≤150MB（重基线） | **armed PASS**（空窗 9.1MB——023 重基线门下维持；RQHost 后回归 ≤10MB 级承诺） | budgets row9+portable-20261002-093055 |
| 10 | installer | ≤50MB（重基线） | **armed PASS**（30,403,072B 余量 22.0MB——V2b 终态；RQHost 后回归 ≤20MB 承诺） | budgets row10+同上 |

## M4 四面验收核销（战略 §6：预算全绿/installer/portable/公开对比表/语法高亮首批）

1. **预算全绿**：十行终态=6 PASS+2 FAIL（帧两行——S5 上游余题归因回执
   在档）+renderer n/a+open_1gb=(b) 登记收口（供⑮ §10）。**过渡门口径注记**：idle/installer
   两行=独立渲染期重基线门（023 用户裁定——AskUserQuestion 回执链在
   录），RQHost 后回归严格门（≤20MB/≤10MB 级）承诺在案。帧两行双态
   如实（Q-2 口径——tag 随裁）。
2. **installer/portable**：armed PASS 判定终态（V2b 手段集维持；ts-off
   发布形默认+ts-on 记录位）+RQHost 回归承诺指针（战略 §2.1 追记）。
   **核销**。
3. **公开对比表**：我方 L2 列四行全实数（steady/open/diff 窗口形/scroll
   ——024 滚动行=022 首判+024 重判并陈）；竞品三家实数（VS Code/Zed/
   BC5）+NP++ pending（**Q-3 默认口径落表脚注：列完整性=后续补列域非
   里程碑判定门——tag 不等待**）。--verify 10 行+--check 双绿。**核销
   （带 NP++ pending 注记）**。
4. **语法高亮首批**：716 组A tree-sitter 首批交付消费（022——highlight
   臂在链+two-face 语法集面）+供⑭ RQHost 期插件化演进指针（023 用户
   方向裁定登记）。**核销**。

## v0.1-M4 tag 素材（打点=本件 merge 收据位——015-023 惯例；annotated tag）

素材正文（merge 期按 023 已录口径打点——帧两行不阻 tag+注记并陈
〔00-overview M4 第六件注记成文+023 Q-2 用户裁定「里程碑标记≠发布」〕；
Q-1 已裁 (b) 落账（2026-10-02——供⑮ 供料档 §10），Q-2 按 023 已录
口径备料——若 merge 前用户改裁，本素材随裁回填）：

```
M4 速度王座与发布 本仓面收口态（战略 §6——判定面快照）

PLAN-018 预算门开篇+首批锚点/PLAN-019 portable 瘦身（分阶段语义）/
PLAN-020 公开对比表竞品侧先行/PLAN-021 L2 解阻首判（steady/warm/open
armed PASS+diff 全量形 FAIL 对照）/PLAN-022 716 三组消费（diff 窗口形
清偿 PASS 784.8ms+帧两行断言化首判 FAIL）/PLAN-023 installer 收口（≤50MB
重基线 armed PASS 30,403,072B+panic=unwind 勘定+供⑭ 登记）/PLAN-024
收口件（帧两行 725 后重判+对比表滚动行并陈+NP++ Q-3 口径+终检表+本 tag）。

预算十行终态：steady 15.6ms PASS｜warm 0.0ms PASS｜open 863.2ms PASS｜
diff 窗口 784.8ms PASS（全量对照 FAIL 在档）｜idle 9.1MB PASS（≤150MB
重基线）｜installer 30,403,072B PASS（≤50MB 重基线）｜renderer n/a｜
type_latency P95 95-112ms FAIL 维持（725 增量管线中位 110→1-4ms ~30×
生效——残余=S5 段 layout/shaping/draw，auto-lang 余题在册）｜scroll
6.7-8.8fps FAIL 维持（S5 域同源）｜open_1gb=(b) 登记收口——供⑮ 文件后援分页 rope want 入供料档 §10
（用户裁定 2026-10-02）；512MB 拒绝位活体维持至供⑮ 交付。

对比表：我方 L2 判定谱四行全实数（滚动行 022/024 并陈）；竞品 VS Code/
Zed/BC5 三家实数+NP++ pending（Q-3：列完整性非里程碑判定门）。语法高亮
首批：716 组A 消费+供⑭ 插件化演进指针。

v0.1-M4=里程碑标记非发布（对外发布前必须全绿含 RQHost 后 ≤20MB/≤10MB
级回归门——023 Q-2 用户裁定口径）。
```

**打点落位注记**：tag 动作=merge 阶段五检查点后（收口件 merge 收据
惯例——v0.1-M1 b497db7/M2 ed8c107/M3 f4e34c1 先例）；对象=merge 后
main tip commit；`git tag -a v0.1-M4 -F <素材>`；素材数字与终检表逐字
一致（本档对账）。
