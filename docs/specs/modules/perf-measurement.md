# 测量模式阶梯与工具链（modules/perf-measurement）

> 来源：docs/strategy/002-north-star-v2.md §5 + PLAN-004/005/006/007
> 交付（tools/perf、tools/bench）。

## 测量模式阶梯（战略 §5，硬约束；L2 形态 PLAN-007 更新）

| 档 | 形态 | 效力 |
|---|---|---|
| **L0** | 日常 VM+merged | 代理指标防结构回归（无预算效力） |
| **L1** | （中间档） | 经 perf.py 链取归因 |
| **L2** | a2r 转译 + release 编译 + **单 iced 直拉**（PLAN-007 起，Q2 中期裁定；原 RQ/rqhost 形态见补注九与下节历史档案） | **预算与门禁只在 L2 数字上评估** |

预算语义拆分：**稳态启动**（单 iced 口径下=进程内 iced 初始化暖态）为
头条硬门禁（回归当天修），**渲染器冷启动**过渡期 n/a（进程内无分离
冷启面，pending 上游 683 重设计后重估——budgets.json 注记同步）；
其余指标 M2/M3 记账、M4 统一收口。原「RQ+预热渲染器=交付拓扑候选」
（渲染成本跨实例摊销）随补注九 Q2 中期裁定撤回待 683 重设计落定重估。

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

## L2 数字面与首基线（PLAN-006 交付，2026-09-22；rqhost 形态历史档案）

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

## L2 单 iced 化（PLAN-007 交付，2026-09-22——Q2 中期裁定落账）

- **拓扑**：release 产物**零旗标直拉**（生成物 main.rs autodesk gate
  实锚——`--autodesk-render` 三态属 client 臂，带 launcher 无 rqhost 走
  broker rendezvous 需宿主；零旗标 = `run_app_devtools` 纯独立 iced 窗）。
  rqhost 生命周期（rq-up/rq-down/daemon 采纳双门/末窗退出协议）随拓扑
  退役；perf.py 的 rq-* 段保留为工具链机构面（L2 门控链 =
  a2r→release）。**拓扑有效性门**：app 日志后端就绪行（"Running with
  Iced backend"）+ 进程存活——单 iced 无 adopt 握手，窗口创建即 iced
  事件循环启动。
- **断言语义变更**：renderer_cold_start 由 armed-record 改
  **arch-blocked-note**（过渡期 n/a——进程内无分离冷启面，pending 上游
  683 远程 renderer 重设计落定后重估；armed-record 位随 rqhost 退役，
  历史基线 JSONL 在档）；steady_start 维持 armed+≤80ms，预热语义注记
  改「进程内 iced 初始化含、系统暖机弃首跑」（budgets.json 同步）。
- **当前 L2 链阻塞（PLAN-007 装载链引入）**：store 分块装载调用
  `code_editor_edit`/`code_editor_delta`、fsys 调 `File.read_text_range`
  ——三内建无 a2r 映射（ui_gen `vm_builtin_host_call` 单源表与
  trans/rust.rs `File` 模块表均缺，681 清偿面外；docs/upstream 登记）。
  `--mode l2` 门控在 a2r 段 exit 3 归因；**降级口径（plan §10-2）**：
  装载链代码审读 + L0 承载内存锚点，L2 锚点补跑随上游解阻另收。单
  iced 拓扑本身已用旧代码 release exe 零旗标直拉探针实证（后端就绪
  行 + BENCH 标记到达、无 daemon、进程干净）。
- **PLAN-006 rqhost 形态数字的档案地位**：`baseline-L2-20260922.md`
  为 rqhost 拓扑下的历史锚点（steady 12.7ms / open100MB 40.6ms /
  480MB 内存），不再作单 iced 形态的回归对照基线；480MB 线性放大
  锚点对 rope 前后对照仍有效（同属 store 镜像缺口）。

## 观测通道（PLAN-014 T-07，2026-09-25——供④ time 族消费）

- **BENCH 标记双录机制（在册）**：`_spawn_tracked` 解析标记行下一裸
  数字行=app 内 epoch 毫秒（供④ `time.now_ms` VM 轨 shim，PLAN-701；
  print 直出 i64 实证形）——`app_epoch` 字段入返回面，`open_ms` 主源
  切 app 侧差值、host `perf_counter` 差降对照列（`open_ms_host`，一跑
  双录）。
- **当前源=host 回退（上游缺口在册）**：供④ vue 臂无 `time.*` 模块
  映射（ts_adapter TS2304×4——front ms 行撤回，docs/upstream §17 新
  want）；front 恢复裸 epoch 行后 app 源自动接管（机制零改动）。
  VM 轨直出形勘定（probe_upstream_consume）：`print(time.now_ms())`
  裸行 ✓；`.str()`/字符串拼接/双参 print=平台缺口不用（i64 算术同缺
  ——701 time-natives spec 桥面节）。
- **F-RV6 口径勘误（供③ T-01 根因回执，随 §17）**：矩阵「进程级早
  崩竞态」根因=**跨会话 `taskkill /IM auto.exe` 清扫误伤**（tools/perf
  /README.md:65 清扫指导+他会话实活实证——watcher 实捕同秒双进程蒸
  发），非工具链快照面竞态；新工具链无干扰五连跑零早崩（PLAN-701
  T-02 谱）。重跑条款维持（干扰不可根除=共享环境常量），归因注记升
  级：早崩先查并行会话清扫（watcher/日志双证），非盲重跑。

## 上游阻塞登记（供料面）

上游供料包文档：`docs/upstream/2026-09-m1-supply.md`（F-R1 a2r 生成器
E0432 / F-RV6 进程级早崩竞态（矩阵基线口径：完成态跑次 ≥49 passed /
0 failed 判绿，无 RESULT 行=竞态早崩重跑一次不计败）/ rope / delta /
分块读 + §10 PLAN-007 增量）。RQ 渲染臂 codeeditor 覆盖（供料 §6）与
a2r 词汇门（§7）已解阻（2026-09-22 上游 PLAN-674/681 delivered）；
L2 链现存 blocked 面=**PLAN-007 装载链三内建的 a2r 映射缺口**（供料
§10 增量：code_editor_edit/delta、File.read_text_range——L2 锚点补跑
随之解阻）、内核帧时间戳插桩（type_latency/scroll_fps 与 steady 首帧
口径升级）与 rope 化（缓冲区类内存）。

**2026-09-29 现势更新（PLAN-018 T-00 勘定）**：装载链映射缺口已大半
清偿——`File.read_text_range` trans 臂在（PLAN-687）、ui_gen 单源表
app 面 19 内建 18 已映射；残余=**三类生成缺口**（G-A envelope 成员
访问投影 `v.field ?? default`/G-B try 块 trans/G-C code_editor_delta
ui_gen 臂——a2r 探针 exit 3 实证，生成物占位全景在
`specs/auto-edit/tests/evidence-p018-survey.md` §①-b），供料归口
`docs/upstream/2026-09-m4-perf-unblock-supply.md` §1（M4 解阻供料包
——同档登记供② 帧插桩/供③ 大文件卡死回归/供④ tree-sitter）。

## 预算门 M4 语义与全表重定（PLAN-018，2026-09-29）

- **断言形态分层（frozen 约束）**：锚点=「记账不阻塞」（L0/release
  工具链全链形态数字入档——本件三新档）；硬判定维持 L2 唯一预算
  效力（战略补注二）——016 的 release 全链判定先例仅限 diff
  （server 侧计算主导）；steady_start/open_100mb 等交互面预算的
  正式判定待供① 解阻后的 a2r release 直拉形态，锚点不冒领。
- **budgets.json 全表重定（十行处置）**：纠偏两行——open_100mb/
  open_1gb validity「rope 前架构性不可达」过期文本纠正为「解锁待测」
  （rope[673]+分块读[687] 上游已交付）；**禁调优放开仅限此两行**
  （解锁条件已满足行——本件放开测量，优化实施仍走计划）；对齐一行
  （diff_100mb 016 达标谱维持）；排队注记三行（type_latency/
  scroll_fps→供②；renderer_cold_start→683 pending 维持）；收口路径
  两行（warm_start/idle_mem——断言化=供① 后 L2 形态）；steady_start
  分解数字回填；installer 裁定材料备齐注记（Q3=用户件 §10 Q-1）。
  断言终态变化：warm_start pending-feature→ledger、open 两行
  arch-blocked→ledger——**arch-blocked 位在 l0 覆盖转缺席=语义退役
  如实显影**（五态词表与 014 行序机制零变更）。
- **首批锚点（2026-09-29，release 工具链 v0.4.2-2205 记账形态）**：
  open_100mb 装载墙钟 4 跑谱 816.1-843.0ms、median 841.0ms——≤1s
  预算行内（首实测锚点；big 态语义=fsize≥50MB 探测门 plain 旁路臂；
  滚动不掉帧半行=供② 后）；1GB=512MB 拒绝位实证（513MB 边界对照
  同形，拒绝形机读=bench_open_rejected 补点标记）；steady_start
  分解 mean 232.6ms>80ms=fail 归因清单——spawn→vm_init 段 224.5ms
  主导（进程起+VM 引导，L0 形态含解释器 boot；瘦身=后续件）+
  vm_init→ws_loaded 8.1ms；warm_start 恢复净段 mean 1.3ms（2ms 轮询
  粒度下限）vs ≤120ms 绿注记位+不读盘面=标记单对实证（非 active
  19 tab 零装载）；idle_mem 空窗 mean 51.4MB（≤60MB 行内）/20tab
  恢复 mean 306.2MB（Δ+255MB=active 单文件装载+语法臂成本归因注记，
  非 20 文件全量装载）。
- **三新档（tools/bench，PLAN-018）**：`open`（100MB 生成式×N 跑谱
  +513MB/1GB truncate 探针拒绝对照）/`steady`（启动链分解×N 2ms
  轮询+≤80ms 对表）/`warm`（空窗+20tab 会话恢复[10MB×20 生成式注入
  隔离 APPDATA]+恢复净段/active 装载/不读盘三分解+两形态内存采样）
  ——锚点档共性：release 工具链全链形态（AUTO_BIN 指 release 构建，
  016 先例）、APPDATA 隔离（保护用户会话+空目录纯态——矩阵 T11
  纪律）、AUTO_PROJECT_DIR 显式钉位（ws_dir 匹配由构造保证，
  stage_diff 先例）、fixture 沉降窗计时卫生（016 writeback 教训）。
  `assert` 默认目标过滤=含 budget_assert 记录的最新文件（results/
  多档 JSONL 命名坑位——011/013 前缀档起既有，本件收口）。
- **app 侧 BENCH 补点（2 处，AUTO_BENCH=1 门控）**：
  `bench_session_restored`（LoadWorkspace 会话恢复链尾——warm 档
  恢复净段读点；恢复链在 bench_ws_loaded 之后执行）/
  `bench_open_rejected`（RunPendingLoad 超大拒绝分支尾——拒绝形
  机读；拒绝在装载标记包夹之前且 console_log 不落 stdout）。未设门
  零行为差异（PLAN-005 纪律，矩阵回归保证）。

## installer/portable 形态（PLAN-019，2026-09-29）

- **Q3 裁定记录（用户 2026-09-29，PLAN-019 §4 授权记录）**：打包路径
  =**a2r 原生化瘦身**（治本——「单 exe 无运行时依赖」战略语义维持，
  执行打包/自解压路径否决）；形态=**纯 portable**（winget/自动更新
  均不入——战略 §9 加分项口径，后续件再议）。
- **构建通道（tools/portable/build_portable.py 一键链）**：regen
  （`auto build -r rust`——上游阻塞[供①]时快照回退复用现势生成物，
  回退语义脚本内建）→ **补丁注入**（[profile.release] 块级替换+依赖
  行 feature 面+基面漂移适配——生成物 Cargo.toml 无 [profile] 节且
  gitignored[每次 regen 覆盖]，注入后置于 regen=幂等通道
  [MARKER 块替换+第二遍哈希等价自证]）→ `cargo build --release` →
  strip（profile 级——MSVC/PE 外部 strip 不采用[校验和/签名面风险]）→
  产物 `dist/portable/auto-edit.exe`+sha256 → **尺寸断言**（≤15MB
  硬判定：达标绿/超限红 exit 1+差距数字；JSONL 记录 tools/portable/
  results/ 入仓）。构建稳定性配方（执行期实录固化）：sccache 旁路+
  RUST_MIN_STACK=16MB+-j2+瞬态崩限次重试（增量推进）。
- **判定口径（frozen ⑤）**：单 exe 直跑（无安装壳/无解压步骤/无外部
  运行时依赖——烟测即证，T-04）；「无运行时依赖」面=无 DLL 侧车+
  无解压残留+进程树单进程探测。
- **分阶段达标语义（用户裁定接受）**：未达标≠失败——差距归因+want
  排队即交付。首件（PLAN-019）终态手段集[lto=fat+codegen-units=1+
  strip+tokio 子集]29,844,480B（-24.3%）未达标；剩余大头=上游域
  （wgpu 渲染栈 4.1MB .text+two-face 全量语法集[.rdata 12.4MB 主项]
  +image/HTTP/字体栈——构成表 evidence-p019-survey §④）；two-face
  子集/lazy 装载 want 登记 m4-perf-unblock-supply §5（条件触发兑现）。
  门控手段测量位在案：panic=abort -7.11MB（back_proxy.rs catch_unwind
  隔离语义面——默认不启用）/opt-level=z -7.65MB（性能护栏位）/
  组合 16,459,264B 距门仅 714KB——用户裁定后+上游 want 即可达标。
- **性能护栏（G-4，防「瘦体积肥延迟」）**：018 锚点档复跑对照
  （工具链轨=open/steady/warm 档——预算行维持门）+产物 exe 直拉面
  （probe_surface.py——steady 代理/open 100MB/idle mem，手段敏感面；
  a2r 门旁路=regen 阻塞期记录性通道，供① 清偿后回归 proxy --mode l2
  标准链）。锚点=记账不阻塞原则不变（硬判定维持 L2 唯一效力）。

### installer/portable 判定终态（PLAN-023，2026-10-02——收口件）

- **现势三代谱重测（工具链 v0.4.2-2546-g986e765ac 组树 clean，ts-off
  发布形）**：V2b 手段集[lto=fat+cgu1+strip+tokio 子集]**30,403,072B**
  （vs 022 代 30,355,456B=+0.16% 代差带内；vs 019 +1.9%）/opt-z 追加谱
  22,206,976B（z 增量 **-8.2MB**）/panic=abort 记录档 22,646,272B
  （abort 增量 **-7.76MB**——.text -4.84/.rdata -2.46/.pdata -0.46MB
  节表三分）；组合（z+abort）投影 16.5~16.8MB——**019「距门 714KB
  即可达标」叙事实证翻转**（716 two-face 退役实收仅 -0.6MB+工具链
  代差；下游深裁可达池仅 axum diet <0.5MB——库存量表 R1-R9，
  evidence-p023-survey §①②）。716 退役红利在节表显影：.rdata
  12.35→8.11MB（-4.2MB）。
- **panic=abort×catch_unwind 语义冲突勘定（本件核心裁定材料）**：
  710 G-B 落地后 `.at try`→`std::panic::catch_unwind` 为现役生成
  语义——生成物 **17 语句/8 语义点**（fsys.at 6 try 块×back/front
  双成员+editor_store.at 5 try；evidence §③ 全列）。abort 下兜底
  全部「进程死亡」化，其中 **load-bearing 两点**：会话恢复
  fresh-start（损坏会话文件=拒启）+装载探测门（512MB 拒绝位/50MB
  big 态门——open_1gb 行判定语义域）；另有搜索/copy/delete 逐项
  错误隔离×3 语义点（back/front 双副本）与 diff badge 装饰面；内核
  back_proxy.rs FFI 隔离点亦破。**abort 出局**（收益 ~7.8MB 对价=
  兜底语义全面致命化）。
- **门重基线（用户裁定 2026-10-02，AskUserQuestion 回执）**：
  installer 行 ≤15MB→**≤50MB**、idle_mem 行 ≤60MB→**≤150MB**
  （渲染暖态语义）——独立渲染期（iced+wgpu 栈在 exe 内）过渡口径；
  **RQHost 渲染拓扑**（编辑器只往 RenderQueue 写 RenderCmd，渲染栈
  移出编辑器 exe）落地后**回归严格门（≤15MB+≤10MB 级）**——回收
  承诺随战略 §2.1 追记（PLAN-023）在案。发布语义不变：重基线后的
  门即当前门（战略「预算未达标的功能不发布」原文不受扰——非放宽
  换绿，系预算随拓扑重分期）。
- **判定终态（armed PASS）**：终态手段集=**V2b 维持**（lto=fat+
  codegen-units=1+strip+tokio 子集；opt-level=3 保性能——M4 速度
  王座语义；panic=unwind 保 17 处兜底；abort/opt-z 留测量档不启用）
  ——30,403,072B ≤ 52,428,800B（**余量 21,998,336B**）。ts-off=
  发布形默认（dist/portable/auto-edit.exe）；ts-on=记录位
  （51,457,024B 022 在档——>50MB 撞线=非发布形正确信号）。源=
  portable-20261002-093055.jsonl；构建通道 build_portable.py
  （BUDGET_BYTES=50MB 随重基线）。工具链轨五行锚点复跑全绿
  （v2546：steady 17.8ms/warm 2.6ms/open 865.8ms/idle 9.1MB/
  diff 窗口形 635.0ms——021/022 对照零回退，evidence §⑤）。

## 公开对比表（PLAN-020，2026-09-29——竞品侧先行件）

战略 §5 指定表位（README 发布与 NP++/VSCode/Zed[打开/滚动] 及 Beyond
Compare[diff 计时]的同机对比表——「公开可复现才有说服力」）。本节=竞品
侧先行半件的规范锚；**我方 L2 正式列待供① 解阻后补**（M4 主线门控现状
不变）。

- **方法论（tools/compare/METHODOLOGY.md 定案）**：t0=CreateProcess 后
  host perf_counter 采样；t_ready 主通道逐对象定义——VS Code=renderer
  RSS 平台（1.5s 滑窗极差判据+确认窗防分块装载假平台——分档
  5MB=3s/100MB=6s；文本模型物化语义）、Zed=Zed.log「Rendered first
  frame」（首帧语义；rope 视口惰性装载注记——非全量）、BC5=file-report
  非空（diff 结果产出，对齐我方 diff_100mb 口径）、NP++=pending（缺位，
  安装=用户面 §10 Q-1）。备通道（窗标题含文件名/进程退出）为对照列。
  **跨对象计时语义不同——直比禁则**，表内以语义列显影。median=上中位
  约定（sorted[N//2]，bench.py 家法——018 锚点同法，METHODOLOGY §5
  frozen）。滚动帧率通道=v1 注记后补（屏幕捕获自动化双缺陷实证：
  前台权拒绝+捕获面污染；与供② 帧插桩及我方 L2 列同期）。
- **三态分层纪律（frozen，018 分层纪律的表内延伸）**：我方列=列元数据
  三态——anchor（锚点，VM 形态注记「非 L2 正式判定」）/surface（产物面，
  last-good 基面注记）/release-judged（release 全链判定先例——**仅限
  diff**，016 先例）/l2-pending（正式判定位虚席，**渲染断言禁止出数**）
  ——锚点/产物面冒领禁则。
- **可复现三要素（frozen）**：数字入表必附 {版本钉版, 环境指纹, 跑谱+
  离散}——缺一即 harness report/表格生成器拒出数（三要素门内建）。
  版本钉版=文件元数据通道（VS Code CLI --version 直启挂起+自更新中间态
  陈旧通道双缺陷实证——bash 包装器报 1.138.0 vs 实际 1.139.1）。
- **harness（tools/compare/）**：`compare.py`（check/run/report——fresh
  profile per run、沉降窗 5s、invalid-run 单次重跑条款[VS Code 间歇
  rc=0 自退现象谱在案——014 F-RV6 归因纪律延展：连续两跑无效 abort
  示知，先查并行会话清扫]）/`anchors.py`（我方三态数据直读 018/019/016
  在档 JSONL——零重算，--verify 逐字对照）/`render_table.py`（数据驱动
  markdown——README 表位生成区间禁手改，--check 复现一致断言）。
- **边界（非目标）**：竞品纯黑盒（仅进程级观察+自建 temp profile，零
  安装域写入）；对外发布/宣传动作=数字齐后另行（README 节=表位落位）；
  NP++ 安装=用户面裁定（装后 harness 补跑即得列，零改动）。

## L2 直拉形态消费复验与首判（PLAN-021，2026-09-30——解阻日）

供①（PLAN-710）→ 残余两面（供料档 §6）→ PLAN-714 r2/r3 清偿 → 本件
fresh worktree 补跑全弧收口（forensics=specs/auto-edit/tests/
evidence-p021-blocked-survey.md；上游登记=供料档 §6/§7）。

- **解阻复验（三重判据首度全绿）**：`perf.py a2r` exit 0+零
  「transpile failed (module skipped)」警告行+三占位零命中+
  **fresh workspace `cargo check --workspace` 过**（018 blocked 态
  清偿闭环）+back fsys.rs 在位+front route-A 实体形（env_str→
  fsys::env_lookup）。工具链钉版=v0.4.2-2366-gacf653d3f（714 r3
  交付点，组树 debug 构建——PATH 坑纪律：release 侧陈旧弃用）。
  构建稳定性配方适用实录：sccache 旁路（RUSTC_WRAPPER 清空——堆
  损坏 0xc0000374 一度，019 配方复用即绿）。
- **L2 直拉形态首判（五行其三，2026-09-30）**：
  - **steady_start armed PASS**：mean 15.6ms（4 跑谱 14.3-16.1，
    首跑弃暖机；分解 init 7.5+ws 8.0）vs ≤80ms——**硬门禁正式判定
    绿（L2 唯一预算效力首次兑现）**；018 VM 形态 232.6ms 归因
    （spawn→vm_init 224.5ms）随直拉形态消失如实显影（L2 init 段
    7.5ms）。
  - **idle_mem armed PASS**：空窗工作集 mean 9.7MB（4 跑 9.48-10.04）
    vs ≤60MB；018 VM 形态 51.4MB 同步收缩。
  - **diff_100mb armed FAIL（记录性）**：back 直拉形态（release
    auto-edit-back /api/diff_files——016 server 侧语义同型）median
    5183.2ms（3 跑谱 4985.8-5412.4）vs ≤2000ms；归因=包络 rows 全量
    投影+双层 JSON 在 a2r back 形态放大（016 rows 惰性投影 want）；
    016 VM 形态 1906/1971ms 达标为形态对照；baseline 小/中档
    22.5/18.9ms+over_lines 173.9ms 全绿。瘦身=后续件。
- **残余缺陷（供料档 §7——open_100mb/warm_start 行维持虚席）**：
  a2r 形态 code_editor 注册断链（装载探测门永假→装载链永递延；
  VM 轨同源正常+旧 a2r 构建正常+新旧视图代码逐字节一致→ui 运行时
  回归，窗口 2205→2366）——回归窗口=710 ui_gen/fix-ui-tier/r3
  分发器嫌疑，上游二分定谳后 `bench open|warm --l2` 补跑（判据面
  已备）。
- **生成码首跑+三域冒烟（G-A/G-B 实证绿）**：release exe 零旗标直拉
  ——boot/渲染/AutoUI MCP 面/零 panic；会话恢复 try 成功臂
  （restored@16.8ms）+坏 JSON catch 臂（fresh start+存活）+front diff
  bypass 投影链 8s 存活窗+back 包络数据面 golden 3/3 计数全对——710
  G-A/G-B 清偿面在真实 app 实证；装载链域（G-B③/G-C）随 §7 缺陷
  blocked。L0 矩阵复跑=VM 轨（不受 §7 累）判绿口径承 018/020。
- **last-good 基面退役（T-01）**：build_portable regen 快照回退臂
  退役（RETIRE_NOTE）；`--regen --skip-build --check-idempotent`
  幂等自证 pass（portable-20260930-165454.jsonl）。portable 全量
  构建随 §7 缺陷装载面无涉——构建面绿（第二段收口件回归解阻）。

## L2 断言全表收口（PLAN-021 残余补跑，2026-09-30——PLAN-714 r4 清偿日）

前节「残余缺陷」已随 **PLAN-714 r4** 清偿（二分定谳=非回归——生成器
Plan 413 原始缺口：`code_editor (key: t.key)` 动态 key 属性在 a2r 视图
构建路径静默回落 "editor"→注册键≠查找键；修复=e93a717da 动态 key 经
`ast_expr_to_rust` 发射贯通注册键）。本件判据面 zero 重设计补跑即全收
口——**预算表五行判定全部落地，M4 预算面板正式判定面过半转正完成**：

- **open_100mb armed PASS**：median 863.2ms（4 跑谱 862.7-889.5）vs
  ≤1s——硬门禁正式判定绿（018 记账形态 841.0ms 同量级复现）；「滚动
  不掉帧」半行=供② 解阻后；超大拒绝位 513MB/1GB 同形复证；工具链
  v0.4.2-2389-ge93a717da（714 r4）；源=open-20260930-230121.jsonl。
- **warm_start armed PASS**：恢复净段 mean 0.0ms（2 跑——轮询粒度
  下限）vs ≤120ms；全链 mean 19.3ms（谱 18.9-19.7，boot 与 steady
  15.6ms 同源量级——018 VM 形态 240ms 放大随直拉消失）；active 装载
  段 1124.0ms 单列（open 行语义）；Δmem 265MB=懒装载语义记录；源=
  warm-20260930-230317.jsonl。
- **三域冒烟 7/7 全绿**：r3 轮 4/7 三 FAIL（§7 归因）全转绿——G-B①
  成功臂 restored@16.9ms/G-B② 坏 JSON catch 臂/G-B③ 装载探测缺文件
  错误形/G-A④ 投影链 8s 存活/G-A⑤ back 包络 golden 3/3/G-C⑥ 装载
  E2E 标记序/G-C⑦ badge 门探测 try；源=gen-smoke-20260930-230652
  .jsonl。生成码三域（G-A/G-B/G-C）自此在真实 app 全部实证。
- **对比表收口**：open_100mb 行 L2 实数补列（863.2ms armed PASS），
  l2-pending 虚席位退役（机制保留）；anchors --verify 7 行+
  render --check 双绿维持。

## diff 窗口判定口径+帧两行断言化协议（PLAN-022，2026-10-01——M4-05）

### diff_100mb 窗口形清偿重判（G-2）

- **判定档切窗口形**：bench `diff --l2` diff_100mb 档判定调用切
  `/api/diff_files_window`（上游 r3 改签 9921 五参——rows_offset=0/rows_limit=
  **600** 对齐 front 渲染 cap[PLAN-011 口径]）。**「出结果」语义
  （防冒领成文）**=全量 hunks/counts/rows_total+首窗 rows 渲染数据
  （BC 渐进显示同类语义；分页消费面 rows_total 真源）。全量形保留
  对照档（`diff_100mb_full`，kind=full-ref——**数字在档不删**：
  016 1906ms/021 FAIL 5183.2ms/022 对照 5078.2ms）。
- **armed PASS（双谱复现）**：median **784.8ms**（N=4 谱 756.6-928.8，
  首跑弃暖机）+复现终跑谱 median 1261.1ms（N=4，同日静窗）——双谱
  ≤2000ms PASS（机器态波动带 784.8-1261.1ms，预算余量 37-61%）——
  021 FAIL 清偿（倍率 6.5×/4.0×）；归因闭环=021 归因
  ①「envelope 全量投影+双层 JSON」（rows 1.8M 行物化）随窗口物化
  （600 行）消除，余量=引擎核心+2×100MB 读（语义 frozen 不动；上游
  census 21.9×↓/−29% 弹药兑现）；工具链 v0.4.2-2474-g95dcfb55b
  （含 716 ec45f911c）；源=diff-20261001-144526.jsonl
  （首跑谱）+diff-20261001-164312.jsonl（复现终跑谱）。
- **VM 轨窗口调用**：供⑧ 上游缺口（codegen 裸名臂缺失——上游
  供料档 §8）**已清偿**（716 r3 T-14——9920 撞号改签 9921+裸名臂
  补全；下游回执=probe_diffwin 缺省 VM 形 8/8 PASS）；L0 VM 形
  diff 档维持全量旧径零扰动（016 判定对照形态——切窗为可选后续）。envelope 窗口形契约=modules/diff-view.md
  窗口形节（SD-02）；端点形=modules/back-api.md 第 16 端点节
  （SD-03）。

### 帧两行断言化（G-3——供⑨ 清偿后首判 armed FAIL，2026-10-01）

- **通道面**：9918 `auto.frame.begin_ms`/9919 `auto.frame.present_ms`
  （716 组B 交付——进程级单调毫秒，0=未捕获；AUTO_FRAME_BENCH 门控
  零开销）。供⑨ 双缺口经 716 r3 T-15/T-16 清偿（int lane 出口形+
  handler 体二段名双轨臂）——下游探针臂重埋后两轨值流贯通
  （VM 轨真值实录+a2r regen exit 0〔i64 字段适配=供⑬，trans 臂
  i64→int 直赋 E0308 上游解形建议在案供料档 §8〕）。
- **首判结果（armed FAIL——测量解锁达成，性能缺口如实红）**：
  type_latency 帧内口径 P50 110ms/P95 115ms vs ≤1 帧〔16.7ms@60Hz
  面板 EnumDisplaySettings 读回〕→ FAIL ~6.6 帧；scroll_fps
  （换行连发 cursor-follow 滚动驱动）8.0fps vs ≥54 → FAIL——同
  根因（键入帧全量重建管线 ~110ms/帧容率上限≈9fps）；**debug 对照
  谱同量级**（78/159ms+11.4fps）=编译形态无关归因强证（管线主耗=
  视图重建+语法臂+layout+present 串行链）；优化 want（增量高亮/
  局部重绘）=后续件。源=frame-20261001-230957.jsonl（release）+
  frame-20261001-225541.jsonl（debug 对照）。
- **判定协议（成文+执行期勘定修正）**：type_latency=帧内口径
  （键入帧 begin→下一 present 差，P95 判定；全链口径注记并列）；
  scroll_fps=滚动驱动→窗内 distinct present 计数/帧值窗时长→
  ≥面板率×0.9（下界测量——MCP 轮询采样≤真值，下界不过阈=FAIL
  成立）；**驱动通道勘定修正**：autoui_keyboard 键入/PageDown 不达
  编辑器（edits 零增实证）→autoui_type 直达 textarea（双臂在场
  值流+光标推进）；**读回通道**=`run -r vm` 单进程 MCP autoui_state
  帧探针字段（`--server vm` 无 UI/`-r vm` 无 HTTP——T-00④ 勘定）。
- **steady 首帧段（记账位）**：帧探针首拍非零 present=4989ms
  〔帧值坐标〕——**时源勘定修正（716 r3 SD-B §3b）**：frame_bench
  时源=首次触及时定格，**非进程起点**——帧值不含 spawn→首触段，
  「spawn→first present」全段分解需 host 标记锚（供⑫ print 拼接
  缺口下标记形撤除，MCP 首采承载——记账位非判定）。
- **budgets 行**：type_latency/scroll_fps 两行 **armed FAIL 落位**
  （ledger tier；首基线锚点=021 diff FAIL 同款语义——测量解锁即
  供② 交付物，性能面收口=管线优化件后续）。

### 对比表滚动列（G-4）

- **我方滚动行落位=l2-pending 零数字虚席**（供⑨ 阻塞如实注记——
  anchors scroll_fps 行+render 滚动行，冒领禁则 PLAN-020 §2 约束①
  同款）；**竞品滚动列维持 pending**（020 Q-2 口径——捕获自动化双
  缺陷实证）。判定协议同上节；供⑨ 清偿后我方列首判出数。
- **diff 行三态并陈**：016 release-judged 1906.0ms+021 l2 FAIL
  5183.2ms（全量形对照）+022 l2 窗口形 PASS 784.8ms——anchors
  --verify 9 行全等+render --check 复现一致双绿（本件收口实录）。
