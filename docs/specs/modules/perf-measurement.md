# 测量模式阶梯与工具链（modules/perf-measurement）

> 来源：docs/strategy/002-north-star-v2.md §5 + PLAN-004/005/006 交付
> （tools/perf、tools/bench）。

## 测量模式阶梯（战略 §5，硬约束）

| 档 | 形态 | 效力 |
|---|---|---|
| **L0** | 日常 VM+merged | 代理指标防结构回归（无预算效力） |
| **L1** | （中间档） | 经 perf.py 链取归因 |
| **L2** | a2r 转译 + release 编译 + RQ（外部统一渲染器做 compositor） | **预算与门禁只在 L2 数字上评估** |

预算语义拆分：**稳态启动**（渲染器暖态）为头条硬门禁（回归当天修），
**渲染器冷启动**一次性成本单列（Q2 待裁）；其余指标 M2/M3 记账、M4
统一收口。RQ+预热渲染器不只是测量配置，更是交付拓扑候选（渲染成本跨
实例摊销=notepad 高频开关秒开），与 exe 路径联合入 Q2。

**过早优化宪法**（v2 裁定 6）：缓冲区类预算（100MB/1GB/diff）在内核
rope 化前架构性不可达——此前禁止对该路径调优；bench 只记基线并标
"架构阻塞"。M1 内部排序（裁定 8）：①功能健康 → ②性能模式一键化 →
③测量体系 → ④才做性能测试；上游供料包（F-R1/F-RV6/rope/delta/分块
读）为 M1 第一优先。

## 工具链

- **tools/perf/**（PLAN-004，一键化）：`check`（依赖自检+环境指纹）/
  `smoke`（rqhost 预热+双实例编排验证）/ `a2r` / `release` / `rq-up` /
  `rq-down`。退出码 0/3/1（**3=blocked-on-upstream**）。a2r/RQ 面已解阻
  （2026-09-22：上游 PLAN-674 §6 RQ codeeditor 覆盖 + PLAN-681 §7 a2r
  部署面/§4 F-R1-B delivered，工具链 1836-gdcbda3f71 下 `perf.py a2r`
  exit 0）；release 产物
  `specs/auto-edit/rust-workspace/target/release/auto-edit.exe`（首编
  5m05s，37.8MB）。
- **tools/bench/**（PLAN-005，L0 测量+断言）：`check`/`proxy`（启动
  分解弃暖机、打开计时 1/10/100 MB fixture、内存采样、**全量读检测**、
  断言报告 → results/<ts>.jsonl 入仓）/`assert`（仅预算断言）。断言
  报告逐行显式终态（无静默缺席）：l0 五类（not-armed/arch-blocked/
  blocked-upstream/pending-feature/ledger）；l2 六类（armed/
  armed-record 替 not-armed 位，余四类同）。fixtures/logs gitignored。
- **L2 运行器**（PLAN-006 已交付，见下节）：release 产物直拉 + rqhost
  预热 + 预算武装断言 + 首份 L2 基线。

## L2 数字面与首基线（PLAN-006 交付，2026-09-22）

- **运行形态**：门控链（a2r→release→rq-up，perf.py 编排）通过后，
  bench 直拉 release exe：`--autodesk-launcher --autodesk-rqhost
  --autodesk-broker=<wellknown> --autodesk-render=queue`（T-00 实锚：
  client 臂不读 `AUTO_RQHOST_WELLKNOWN` env——该 env 只被 daemon 读，
  wellknown 经 broker 传参）；`AUTO_BENCH=1` 门控标记，host 侧
  perf_counter 2ms 轮询粒度。
- **daemon 生命周期协议**（顺设计，不与末窗退出语义对抗）：rqhost
  daemon 在最后一个客户端窗口关闭后自退（rqhost.rs D5）——单一
  daemon 服务整个测量序列，app 全程保活（窗口累积=多 app 共享合成器
  本义），suite 末统一收编全部 app + rq-down。批次间重拉方案已弃用
  （两竞态实勘：服务环暂空致管道探测假死→重拉撞 `-lock` 锁；
  probe→spawn 间隙死）。
- **拓扑有效性双门**：每跑断言 daemon 侧「window opened」+ app 存活
  ——BENCH 标记先于 adopt 结果打印（死 daemon 上标记照达而窗未建），
  纯标记不证拓扑。
- **武装断言语义**：steady_start=armed（spawn→bench_ws_loaded **代理
  口径**——首帧通道 blocked-upstream；均值 vs ≤80ms 显式判定，fail=
  记录性判定不改退出码）；renderer_cold_start=armed-record（rqhost
  spawn→pipe-ready 单列，预算值 pending-Q2 不判）；余行保持记账终态
  但附 L2 锚点数字（rope 前后对照）。
- **首基线锚**（`tools/bench/results/baseline-L2-20260922.md` + JSONL）：
  steady **12.7ms pass**（L0~362ms——auto.exe 宿主+VM 层被 release 直拉
  消除）、rqhost 冷启动 16.9ms（debug 构建，`renderer_daemon_build`
  在档）+守护稳态 68.9MB 单列、open 100MB 40.6ms（L0 459.8ms，~11×）
  但内存 480MB 线性放大不变（rope 缺口锚点，禁调优）。

## 上游阻塞登记（供料面）

上游供料包文档：`docs/upstream/2026-09-m1-supply.md`（F-R1 a2r 生成器
E0432 / F-RV6 进程级早崩竞态（矩阵基线口径：完成态跑次 ≥49 passed /
0 failed 判绿，无 RESULT 行=竞态早崩重跑一次不计败）/ rope / delta /
分块读）。RQ 渲染臂 codeeditor 覆盖（供料 §6）与 a2r 词汇门（§7）
已解阻（2026-09-22 上游 PLAN-674/681 delivered）；L2 链现存
blocked 面=内核帧时间戳插桩（type_latency/scroll_fps 与 steady 首帧
口径升级）与 rope 化（缓冲区类内存）。
