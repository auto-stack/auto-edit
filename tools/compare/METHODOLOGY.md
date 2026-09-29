# 公开对比表测量方法论（tools/compare，PLAN-020 T-00 定案）

> 产物性质：T-00 决策件（PLAN-020 §5 T-00）——四对象计时通道结论+
> 计时点定义+降级项清单。基线数字、环境指纹、版本钉版随
> `results/compare-*.jsonl` 入仓；表位=specs/auto-edit/README.md
> 「公开对比表」节（生成器复现，禁手改）。
> 探针证据：`logs/probe-*.json`（probe_channels.py 产物）+ 本文档
> 各结论行内数字即探针实录。

## 1. 对象与版本钉版（2026-09-29 本机实勘）

| 对象 | 可执行 | 版本（钉版） | 在位 |
|---|---|---|---|
| VS Code | `%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe` | 1.139.1（FileVersion；app 目录 04c0d99f4f 对应——自更新中间态勘定：安装域现存双 app 目录 04c0d99f4f[1.139.1]/7debcd0e2a[1.138.0 旧]，bin bash 包装器报陈旧 1.138.0、`Code.exe --version` 直启 GUI 臂挂起 63s——**CLI 探针双缺陷实证，钉版=文件元数据通道**） | ✓ |
| Zed | `D:\soft\zed\Zed.exe` | 1.20.2（ProductVersion 1.20.2+stable.360.7c451e6…） | ✓ |
| Beyond Compare 5 | `C:\Program Files\Beyond Compare 5\BCompare.exe` | 5.0.6.30713（FileVersion） | ✓ |
| Notepad++ | （四处常见安装位查证缺位） | — | ✗ pending（安装=用户面，PLAN-020 §10 Q-1；装后补跑即得列） |

版本钉版以 harness 每次跑谱时实测写入 JSONL 头行为准（`version` 字段
——上表为起草时点实录）；环境指纹（os/CPU/内存/机器名）同头行。

## 2. 计时点定义（t0 / t_ready）

- **t0** = harness `CreateProcess` 返回后的 `perf_counter` 采样点
  （host 侧基准，与 tools/bench `_spawn_tracked` 同形）。
- **t_ready** = 主通道首命中时刻（host 侧轮询粒度 ~5ms）。通道语义
  逐对象定义（**跨对象语义不同——直比禁则，表内以「语义」列显影**）：

| 对象 | t_ready 主通道 | 语义 | 备通道（对照列） |
|---|---|---|---|
| VS Code | renderer 子进程 RSS **平台判据**（1.5s 滑窗极差 <max(8MB, 峰值2%) 成平台候选 + **确认窗无再增长**——再增长超阈值=装载恢复、候选作废重来；确认窗分档 5MB=3s/100MB=6s[中段 >3s 平坦段会骗过 3s 确认——首测假命中 4.7s 实勘]；窗口裁剪留 1.2× 余量防判据永假。**判据整体偏竞品有利侧**——假平台只会低估竞品打开时长，公开对比保守侧） | **文本模型物化完成**（分块装载间歇停顿假平台防御后定案） | 窗标题含文件名（tab 建立语义——1.4s 量级，显著早于物化） |
| Zed | `Zed.log` 行 `[workspace] Rendered first frame` 到达 | **首帧渲染完成**（视口语义） | 窗标题含文件名 |
| BC5 | file-report 输出文件**非空** | **diff 结果产出**（对齐我方 diff_100mb「出结果」口径） | 进程退出（晚于 report ~50ms，1MB 实测） |
| NP++ | （同 VS Code 形——装后勘定） | pending | — |

- **滚动帧率通道（T-00 ③）结论：v1 注记后补**（PLAN-020 §10 Q-2
  默认维持）。证据：自动化屏幕捕获双缺陷实勘——①前台权拒绝
  （SetForegroundWindow 败，Windows 前台锁）；②捕获面污染（全屏
  CopyFromScreen 捕到他应用窗+用户内容——隐私不可入档；PrintWindow
  仅静态单窗且无滚动时序）。手工录屏协议成本/可信度不匹配 v1 位，
  与供② 内核帧插桩及我方 L2 列同期补（口径一致防返工）。
- **CPU 沉降通道**降级为诊断对照（不作计时通道）：编辑器后台活动
  （索引/扩展/遥测）使 CPU 曲线多峰，平台判据不稳。

## 3. 通道勘定证据行（probe_channels.py 实录）

- **VS Code 1MB 冷启**（fresh profile）：标题 1405.0ms / main.log 首
  行 338.0ms（logs/probe-vscode-20260929-212320.json）。100MB 密采样
  曲线定案（2026-09-29）：**0–2.8s 一次性爆发装载至 807MB → GC 回落
  （3.5s 处 807→492）→ 平台微漂（497–526）**——判据落点（~4.7s）=
  GC 沉降后稳定位，比真实物化点晚 ~2s=**保守侧**；早期粗采样「爬升至
  ~12s」读数系 GC 振荡采样伪影（勘误在案）。
- **VS Code 欢迎模态注记**：fresh profile 首跑弹 GitHub Copilot 欢迎模态
  （PrintWindow 窗捕获直证，logs/vscode-100mb-window.png 证据态）。
  处置=fresh profile 每跑同形（零状态复用）——**冷态诚实口径**，模态
  含在数字内并随行注记。
- **Zed 1MB**：标题 424.5ms（logs/probe-zed-20260929-212317.json）；
  Zed.log 含 `Rendered first frame` 行（日志快照在档）。100MB：首帧
  770.0ms / 标题 1021.6ms，**子进程 RSS ~19MB**——rope 视口惰性装载
  （不读全文件）实证。
- **BC5**：脚本语法勘定=一条逻辑命令 `&` 续行（裸换行=独立命令——
  首探 report 未产出实录）+ `/silent`。1MB 对：report 981.6ms / exit
  1031.2ms（BC 自报 0.87s，logs/probe-bc5-20260929-212410.json）。
  100MB 对：report 91,590ms / exit 91,834ms（2026-09-29 首测）。
- **NP++**：缺位取证（probe_channels.py nppp → exit 1，
  `C:\Program Files\Notepad++` 与备用位不存在）。

## 4. fixture 谱（018 同源参数）

生成式（不入库，gitignored）——**与 018 bench open 档同参数同形态**
（跨对象可比性前提）：重复行行体唯一化 + 每 100 行 1 行 CHANGED
散点（1% 散布）；UTF-8 LF。档位：

- **open_100mb**（战略档）：`compare-fixture-open-100mb.txt`；
- **open_5mb**（小文件档——四对象全装载可比档）；
- **diff 对**（BC5 档，对齐我方 diff_100mb 口径——同 fixture 同读盘
  形态）：a 侧同 open 谱；b 侧=CHANGED→CHANGED2 全替换（同 1% 散点
  差异谱），100MB/5MB 两档。
- 计时卫生：fixture 生成后**沉降窗 5s**（016 writeback 教训，018
  纪律延续）；b 侧替换后同沉降。

## 5. 跑谱纪律（承 018）

- N≥4 跑/对象×档，**首跑弃暖机**；median+min/max 离散注记入报告。
- fresh profile per run（编辑器对象）——零会话/状态复用。
- 收编=taskkill **按 PID 树**，禁 `/IM`（014 F-RV6 跨会话误伤教训）。
- 竞品纯黑盒：仅进程级观察+自建 temp profile；不写竞品安装域。

## 6. 降级项清单（T-00 不可自动化/后补项）

| 项 | 处置 | 依据 |
|---|---|---|
| 滚动帧率（四对象） | v1 注记后补（供② 同期） | §2 通道结论 |
| CPU 沉降 | 诊断对照（不入计时面） | §2 通道结论 |
| NP++ 全列 | pending（装后补跑，harness 零改动） | §10 Q-1 用户面 |
| 手工协议模板 | 暂缓（无通道落入手工必选——四对象主通道全自动化实证） | §3 |

## 6-b. 环境干扰条款（VS Code 间歇自退，2026-09-29 立案）

**现象谱**：VS Code 打开测量跑中间歇**自行干净退出**（rc=0，~2–20s
不等；退出后全系统无接管树=真退出；profile main.log 零 shutdown
记录）。本日谱：harness 1/3、诊断 2/3、单例 0/1——高变异。
**假说排除**：非自更新收尾（无重启树）；非 GPU/renderer 崩溃形态
（rc 应非 0）。
**处置（frozen 条款）**：①harness invalid-run 单次重跑（fresh
profile，attempt 记录入 notes）；②连续两跑无效=环境干扰升级——
abort 示知用户，**不盲跑**；③归因纪律承 014 F-RV6 勘误——本机多
会话并行环境，早退/蒸发先查并行会话清扫（watcher/日志双证）。
重跑条款维持（干扰不可根除=共享环境常态）。

## 7. 公开可复现三要素（frozen，PLAN-020 §2 约束②）

数字入表必附：**{版本钉版, 环境指纹, 跑谱+离散}**——缺一即 report
拒出数（harness 内建三要素门）。逐跑 JSONL 行含 run/warmup/t_ready/
备通道/内存注记；头行含版本+指纹+fixture 参数+计时点定义 id。
我方列三态分层（锚点[VM 形态]/产物面[last-good]/L2-pending）为
生成器列元数据，冒领禁则见 PLAN-020 §2 约束①。
