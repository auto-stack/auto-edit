### 公开对比表（竞品侧先行件——PLAN-020）

同机测量（数据驱动生成，下方区间禁手改；方法论/计时点定义/通道结论见[tools/compare/METHODOLOGY.md](../../../tools/compare/METHODOLOGY.md)）。**可复现三要素**：每数字附 {版本钉版, 环境指纹, 跑谱+离散}（JSONL 在 `tools/compare/results/` 入仓）。**语义注记（直比禁则）**：各对象 t_ready 判据不同——VS Code=renderer RSS 平台（文本模型物化）、Zed=首帧渲染（rope 视口惰性装载，非全量）、BC5=diff 结果产出、auto-edit open=全量装载完成（BENCH 标记包夹）——跨对象数字不可径直排序，语义列随行。

环境：Windows 11 build 10.0.26200 · Visus · 20 核 · 31.8GB（JSONL 头行含全指纹）

| 指标（档） | 计时语义 | VS Code | Zed | Notepad++ | Beyond Compare 5 | auto-edit（本仓） |
|---|---|---|---|---|---|---|
| 打开 5 MB | 各对象 t_ready（语义列同左口径） | 4,289.1 ms（N=4，4,256.3–4,340.8） | 296.0 ms（N=4，272.6–310.0） | pending（未装——Q-1） | —（diff 对象不适用） | —（无同档在档谱） |
| 打开 100 MB | VS Code=RSS 物化；Zed=首帧（rope 惰性）；本仓=全量装载 | 4,677.7 ms（N=4，4,621.4–4,718.5） | 295.6 ms（N=4，275.4–310.3） | pending（未装——Q-1） | —（diff 对象不适用） | **841.0 ms**〔锚点·VM 形态——非 L2〕；38.2 ms〔产物面·last-good 基面——非 L2〕；**863.2 ms**〔**L2 直拉判定·armed PASS——硬门禁正式判定绿**——N=4，862.7–889.5〕 |
| diff 100 MB（文件对） | BC=report 产出；本仓=diff 端点全链墙钟 （022 起=窗口形判定，全量对照在档） | —（未测） | —（未测） | — | 123,279.8 ms（N=4，119,849.6–126,246.9） | **1,906.0 ms**〔release 全链判定先例（016，仅限 diff）〕；5,183.2 ms〔**L2 直拉判定·armed FAIL（记录性）——归因随行**——N=3，4,985.8–5,412.4〕；**784.8 ms**〔**L2 直拉判定·armed PASS——硬门禁正式判定绿**——N=4，756.6–928.8〕 |
| 滚动帧率 | 各对象=编辑器滚动帧率（语义随行：本仓=present 频率采样，面板率×0.9 判据——PLAN-022 协议在档） | pending（未测——020 Q-2 捕获自动化双缺陷） | pending（未测——020 Q-2 同） | pending（未装——Q-1） | —（diff 对象不适用） | 8.0 fps〔**L2 直拉判定·armed FAIL（首基线锚点）——归因随行**——窗 2,995 ms vs 阈 54.0〕 |

Notepad++ 缺位=安装属用户面（PLAN-020 §10 Q-1），装后 harness 补跑即得列（通道与 VS Code 同形）。**我方 L2 正式列=PLAN-021 直拉判定谱**（steady/open——armed 判定随格；diff 行=PLAN-022 窗口形清偿重判 PASS+021 全量形 FAIL 对照并陈；scroll 行=供⑨ 上游阻塞虚席——判定协议在档待清偿；未入表行 warm/idle 判定谱=budgets.json validity）。锚点/产物面数字不冒领（018 分层纪律表内延伸）。发布动作（对外宣传/链接分发）=数字齐后另行；本节=战略 §5 指定表位。
