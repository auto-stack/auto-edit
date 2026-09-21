# tools/bench — 测量套件（PLAN-005 B 段）

**定位**：与 `tools/perf/`（perf.py = 性能模式**切换**编排，L2 机构）同族分层
——bench.py = 测量**套件**（跑数与断言）：L0 proxy 报告 + 预算断言 +
结构回归代理检测。战略依据 `docs/strategy/002-north-star-v2.md` §5
（测量模式阶梯、两档门禁、代理指标三件）与 §2.1（预算表全 10 行 +
解锁条件列）。**L0/L1 数字永不入公开对比面**（战略 §5 硬规）。

## 用法

```
python tools/bench/bench.py check                    # 依赖自检+环境指纹+检测器红证自检
python tools/bench/bench.py proxy                    # L0 套件：5 跑启动分解（弃首跑暖机）
                                                     #   + 打开计时 1/10/100 MB + 内存采样
                                                     #   + 全量读检测 + 预算断言 → results/*.jsonl
python tools/bench/bench.py proxy --full             # fixture 集加 512 MB
python tools/bench/bench.py proxy --mode l1          # VM+RQ：经 perf.py smoke，§6 blocked → exit 3 归因
python tools/bench/bench.py proxy --mode l2          # a2r/release/RQ：经 perf.py 链，§7/§6 blocked → exit 3
python tools/bench/bench.py assert                   # 仅预算断言（对最近 results 文件）
```

退出码：`0` 绿；`3` blocked-on-upstream（模式门控归因）；`1` 真失败
（含**全量读检测红 = 编辑路径结构回归**）。

结果追踪：`results/<ts>.jsonl` 入仓（环境指纹 + 逐指标 + 断言终态）；
`fixtures/`、`logs/` gitignored（可再生）。app 阶段插桩 = `AUTO_BENCH=1`
门控的 `BENCH <stage>` 裸标记行（editor_store.at PLAN-005 T-04；未设门
零行为差异，矩阵回归保证）。

## 探针矩阵（T-03 观测通道实勘，四问全答）

| 指标 | 模式 | 观测通道 | 状态 |
|---|---|---|---|
| 启动链分解（spawn→vm_init→ws_loaded） | l0（vm） | host spawn 计时 + stdout 落文件轮询 BENCH 标记行到达时刻 | ✅ 在位 |
| 打开文件计时（1/10/100/512 MB） | l0（vm） | host 时间戳包夹 `bench_open_start/done`；fixture 经 `AUTO_BENCH=1` 门挂载 `AUTO_OPEN_PATH`（免 UI 触发） | ✅ 在位 |
| 内存采样（idle/loaded） | l0（vm） | psutil 缺席 → PowerShell `Get-Process -Id <pid>` WorkingSet64（方法名记入结果 JSON） | ✅ 在位（回退法） |
| 编辑路径全量读检测 | 静态 | `src/front/*.at` 扫描：`code_editor_text` 允许位 = editor_store 的 ActSave/QuitSaveClose handler；构造性红证 = check 内置样例自检 | ✅ 在位（A 段即首个绿证） |
| 启动类硬门禁数字 | l2 | perf.py a2r/release/rq-up 链 + bench 数字面 | ⛔ blocked-upstream（供料 §7 a2r 词汇门 / §6 RQ 覆盖） |
| 键入到上屏 | 需内核 | .at 层无帧时间戳通道（勘无，见问 2） | ⛔ blocked-upstream（内核帧时间戳插桩小供料，战略 §2.1 已登记） |
| 滚动帧率 | 需内核 | 同上（视口切片内核已做，帧率观测无通道） | ⛔ blocked-upstream |
| 分配计数 | VM 层 | 无内建通道（native_catalog 无分配计数项） | ➖ 登记暂缺（不硬造） |

### 四问明细

1. **time import 形态实测**：VM 轨 time 族内建（`auto.time.now_ms/now_sec/now`）
   在 native_catalog 有登记但**无运行时 shim**——裸形态与 `use auto.time`
   模块限定形态均返 `0`（探针 A/B，进程实测；实装仅在 a2r-std = Rust 轨）。
   `Instant.now()`+`.elapsed()` 对（Plan 240）VM 有 shim 但 elapsed 返回
   约定坏（.at 侧得 None，探针 C）。vue 轨 ts_adapter 有 `Time.now_ms()`
   →`Date.now()` 桥（os-003）——bench 只服务 vm/a2r 轨，记录即可。
   **裁定：BENCH 标记行为裸 `<stage>`（print → stdout 落文件），毫秒值
   一律 host 侧记**（到达时刻轮询 25ms 粒度——L0 proxy 形状分解足够；
   app 侧毫秒钟待上游 time 族接线后再升级）。
2. **首帧观测通道**：勘无。框架合成生命周期仅 `Init`/`Tick`/`CloseRequest`
   三者（`call_handler` 全枚举实证）；快照 "(rendered)" 标记仅存在于 MCP
   快照面（mcp_server.rs），无非 MCP 等价物。→ 键入/滚动预算行
   blocked-upstream 登记 + 供料包一句注记（docs/upstream/ 增量）。
3. **内存采样法**：psutil 缺席（本机实测）→ PowerShell `Get-Process -Id
   <pid>` WorkingSet64 采样（实测 11,993,088 字节成功）；方法名记入
   结果 JSON 的 mem 字段元组。
4. **fixture 与磁盘预算**：1 MB ≈ 0s / 10 MB ≈ 0.01s / 100 MB ≈ 0.15s
   生成成本（实测）；默认集 1/10/100 MB（磁盘峰值 ~111 MB）、`--full`
   含 512 MB（~623 MB）——按计划 §10 默认口径裁定成立。

## 预算断言语义

`budgets.json` = 战略 §2.1 全 10 行，每行 `{metric, budget, tier,
validity, unlock}`。断言报告逐行显式终态（五类之一，无静默缺席）：

- `not-armed`——硬门禁（启动/首帧类）遇非 L2：不评估，防 L0 数字误判；
- `arch-blocked`——缓冲区类（100MB/1GB 打开），rope 前架构性不可达，
  禁调优只记基线（战略补注 6(a)）；
- `blocked-upstream`——键入/滚动（内核帧插桩）与 diff（M3 引擎）；
- `pending-feature`——热启动（M2 会话恢复）、安装包（Q2 exe 路径）；
- `ledger`——记账不阻塞（空闲内存：L0 采样记录，预算断言 M4 收口）。

## 已知坑位（沿 PLAN-003/004 实勘）

- Git Bash `timeout`/壳 PID 断层留 auto.exe 孤儿——bench 一律 Python
  `subprocess.Popen` 直驱 + `taskkill /PID <pid> /T /F` 按树收编；
  **绝不 `taskkill //IM auto.exe`**（连坐其他会话实例）。
- auto.exe stdout 一律落文件（`tools/bench/logs/`），禁管道直读（会塞满
  阻塞，PLAN-003 坑位）。
- 工具链构建号门 ≥1588（与 perf.py 同门）；`AUTO_BIN` 可显式指定。
- 组 worktree 下 a2r 依赖冷编译首跑可能无诊断死（瞬态；复跑即分类
  正常——2026-09-21 实测，基线对照同因 PLAN-027 词汇门 exit 3）。
