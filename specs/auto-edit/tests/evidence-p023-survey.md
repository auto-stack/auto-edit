# evidence-p023-survey — PLAN-023 T-00 决策件三件套

日期：2026-10-02。工作树：`.wt/edit-023/auto-edit`（plan-023-dev，
base 5dbfd79）。工具链：`auto 0.1.0+v0.4.2-2546-g986e765ac`
（组树 edit-023/auto-lang debug clean 重建 1m50s——sccache；主检出
exe=v0.4.2-2511-gb50dce902**-dirty** 不可用，纪律剔除）。
依赖树：auto-lang@986e765ac + auto-down@895f8d0（均 detached clean；
组结构=构建 load-bearing——生成 ws 根 Cargo.toml `auto-lang.path =
../../../../auto-lang/crates/auto-lang` 直指组 sibling，非仅 regen 面）。

## ① ts-off 全谱重测（三代数字表——019 谱对照列）

谱构建纪律：build_portable 一键链（`--regen` 现势直跑→V2b 补丁注入
→cargo release -j2→尺寸断言）。ts-off=发布约束形（默认——零注入）。
每谱 JSONL 在 tools/portable/results/（portable-20261002-*.jsonl）。

| 谱 | 手段集 | 019 谱（2026-09-29 代） | 本件现势谱（2026-10-02） | Δ | 门判定 |
|---|---|---|---|---|---|
| 基线 | 零手段（--baseline） | 39,411,200 B | 本件不重跑（对照锚=022 ts-off 同态 30,355,456B+019 基线列——代差注记在案） | — | 超限 |
| V2b | lto=fat+cgu1+strip+tokio 子集 | 29,844,480 B（-24.3%） | **30,403,072 B**（portable-20261002-093055.jsonl；sha256 7afc34aebde52f62） | vs 022 代 +47,616B（+0.16%——工具链 v2474→v2546 代差带内）；vs 019 +558,592B（+1.9%=工具链代+716 净效应） | 超限 14,674,432 B |
| V2b+opt-z | + opt-level=z | （019 V4 增量 -7.65MB——单测谱未发布） | **22,206,976 B**（portable-20261002-093937.jsonl；sha256 4e9c08673622ee7f） | **z 增量 -8,196,096 B（-7.8MB——vs 019 -7.65MB 同带）** | 超限 6,478,336 B |

**V2b+opt-z PE 节表**（22,206,976B）：.text 13,506,048（60.8%）/
.rdata 7,745,024（34.9%）/.pdata 655,872/.reloc 88,576——z 增量
几乎全落 .text（21.37→13.51MB，-7.87MB）；.rdata 仅 -0.36MB。
| V2b+panic=abort（记录档） | + panic=abort（冲突面 pending 裁定——不入默认） | 组合 16,459,264 B（=V2b+z+abort；距门 714KB） | **22,646,272 B**（portable-20261002-095356.jsonl；sha256 f29dff1b02c63cc5） | **abort 增量 -7,756,800 B（-7.4MB——vs 019 -7.11MB 同带）** | 超限 6,917,632 B |

**V2b+abort PE 节表**（22,646,272B）：.text 16,532,992（73.0%）/
.rdata 5,650,944（25.0%）/.pdata 168,960（0.7%）/.reloc 81,920——
vs V2b：.text -4.84MB（landing pad/personality/EH 代码面退）+
.rdata -2.46MB（vtable/unwind 关联数据折叠——019 未单列的面）+
.pdata -0.46MB（EH 表域 019 预判主项实证）。

**组合（z+abort）投影**：019 交互实证 z 基上 abort 增量=5.73MB
（V4 22.19→V5 16.46）——现势投影 combo ≈ 22.207-5.73×(1+代差)
≈ **16.5~16.8MB（超门 ~0.8~1.1MB）**；019 代 combo/V2b 比值法
16.77MB 互证。两法一致：**三路无一达门**（(a) 最近仍超 ~1MB）。

**V2b 现势 PE 节表**（dist/portable/auto-edit.exe@30,403,072B 逐字节解析）：
.text 21,371,904（70.3%）/.rdata 8,108,544（26.7%）/.data 210,432/
.pdata 628,736（2.1%）/.reloc 82,432。019 基线节表对照（39,435,776B
零手段形）：.rdata 12,354,560→8,108,544（**-4.2MB=716 two-face 退役
显影+手段面**）；.pdata 1,012,224→628,736（LTO/cgu1 面）。

019 锚注：panic=abort 增量 -7.11MB / opt-level=z 增量 -7.65MB /
组合 16,459,264B；716 two-face 退役实收 -0.6MB（022 ts-off
30,355,456B vs 019 同态 29,844,480B——差值含工具链代差+716 净效应）。

## ② deps 深裁库存量表（逐项{预估收益,功能风险,下游可达性}）

通道边界（T-00③ frozen）：仅生成物 manifest 的 **feature 子集面**
（不动版本/path/依赖增删）。feature 统一语义=全图并集——auto-lang
自声明即下限底座。审计输入=生成 ws 三 manifest + auto-lang
crates/auto-lang/Cargo.toml@986e765ac（本节所有「上游域」判定的
底座证据）。

| # | 项 | 现势声明面 | 预估收益 | 功能风险 | 下游可达性 |
|---|---|---|---|---|---|
| R1 | back tokio full→子集 | back 成员 `features=["full"]`；**auto-lang:199 自声明 `tokio={workspace=true,features=["full"]}`=统一底座** | **≈0**（底座已 full——019 实测 ≈0~50KB 与本审计一致） | 零 | **不可达**（上游域——auto-lang 自声明面） |
| R2 | axum 0.7 默认面 diet | ws 根 `axum="0.7"`（默认 features=form/http1/json/matched-path/original-uri/query/tokio/tower-log/tracing）；**auto-lang:327 自用 axum 0.8 `features=["json"]`=独立版本并存**（0.7 行=back 侧唯一定义点） | 0.2~0.5MB 级（0.7 侧 form/query/tracing 等臂裁剪；0.8 侧不动） | 生成 back 代码 axum API 面需逐点核对（路由/Json/Query 提取器） | **可达**（根行 patch——唯一定义点） |
| R3 | front reqwest feature diet | front 成员 `["blocking","json","multipart","cookies","gzip","brotli"]`；**auto-lang:214 自声明含全八 features（+stream）** | **≈0**（底座⊇成员行） | 零 | **不可达**（上游域） |
| R4 | tungstenite/native-tls | front 成员+auto-lang:216 双声明 `native-tls`；**生成 front 码零直调**（grep 实证）——消费面全在 auto-lang 内部 | 整 dep 级（>0.5MB 含 TLS 栈）——但移除=依赖增删越界 | 远程渲染臂（683 退役后 local 形零用） | **不可达**（通道禁令+上游域双壁垒——want 登记面） |
| R5 | iced features diet | ws 根 `["tokio","advanced"]`；**auto-lang:249 自声明 `["tokio","image","svg","advanced","canvas","unconditional-rendering"]`** | ≈0（底座⊇根行） | canvas/svg=UI 框架必需 | **不可达**（上游域） |
| R6 | image-pipeline（back 成员行） | back 成员 `auto-lang={features=["ui","image-pipeline"]}`；**back 生成码 auto_media 端点直调 `image_pipeline::media_http_response(global_media_registry())`**（back main.rs:10-22 实锚——媒体 HTTP 服务面功能依赖） | 0（功能依赖实锚——裁即编译红） | 媒体服务端点=byte-range 流面本体 | **不可达**（功能依赖——非纯 feature 增量） |
| R7 | ureq json | ws 根声明；**双成员均零消费**（生成 manifest 无 ureq.workspace 行） | **=0**（未编译进产物——019 构成表无 ureq 行互证） | 零 | 非杠杆（生成器残留行——注记即可） |
| R8 | 字体/文本整形栈 | cosmic-text(vi,syntect)/skrifa/harfrust/swash/rustybuzz——code-editor 渲染本体 | 大头但不可裁 | 替换=重写文本栈 | **不可达**（上游域——019 构成表 2.4MiB 行） |
| R9 | wgpu 渲染栈 | iced wgpu 后端（auto-lang ui-iced 默认臂） | 大头（019 构成 4.1MiB .text） | tiny-skia 单后端=上游 want（019 §⑤ 行5 在案） | **不可达**（上游域 want 维持） |

**库存量结论（审计定稿——构建后数字复核）**：下游可达池=**仅 R2**
（axum 0.7 根行 diet——唯一定义点+API 面已核〔routing/serve/Path/
Query/Response/http/body/CorsLayer；Json/form/multipart/original-uri/
matched-path/tower-log/tracing 生成码零直用〕），预估 **0.2~0.5MB**；
R1/R3/R5 上游底座、R4 双壁垒、R6 功能依赖、R7 零消费、R8/R9 上游
域。对照门差 ~15MB（V2b 形）为量级错配；「剩余大头=上游域」结论
（019 构成表）在 716/022 现势下维持——**深裁路线 (b) 数学上不可达
门的定量支撑**。

## ③ panic=abort×catch_unwind 冲突面（裁定材料主体）

### ③-a 生成点全列（现势 regen 实锚——9 谱面 regen-20261002-091537）

生成物共 **16 行 17 语句** catch_unwind（`std::panic::catch_unwind
(AssertUnwindSafe(…))` 形——710 G-B `.at try`→catch_unwind 转译）：

| 生成点 | 成员/文件 | 语义点（.at 源） | 兜底语义（现役） | panic=abort 下后果 |
|---|---|---|---|---|
| fsys.rs:193 | back | search_files_json——fsys.at:208 逐文件读 | 单文件读败（非法 UTF-8/锁定/竞态删除/目录误入）**静默跳过**，搜索继续 | 进程死亡（一个坏文件杀整个搜索+应用） |
| fsys.rs:239/247/255 | back | sync_copy_impl——fsys.at:331/339/347 | copy 逐项异常→该项失败回报，其余继续 | 进程死亡（复制批全灭） |
| fsys.rs:282/289 | back | sync_delete_impl——fsys.at:375/382 | delete 逐项异常→该项失败回报 | 进程死亡（删除批全灭） |
| main.rs:2231/2277/2285/2293/2320/2327 | front | 同上三函数的 front 成员副本（dir-diff 进程内轨） | 同上 | 同上（front 侧同型 ×6） |
| main.rs:1226 | front | editor_store.at:523——diff badge probe（code_editor_set_text 探针） | 探针 panic→badge 重算跳过（纯装饰面） | 进程死亡 |
| main.rs:1327 | front | editor_store.at:2818——diff badge gate（file_size 探针→50MB 门） | panic→badge gate 维持 true（保守态） | 进程死亡 |
| main.rs:1665 | front | editor_store.at:1689——**会话恢复**（session json parse/装载全臂） | panic→`"session: parse failed — fresh start"` **兜底全新启动** | 进程死亡——**损坏会话文件=应用无法启动**（每次启动复现） |
| main.rs:1727×2 | front | editor_store.at:955/1013——**装载链探测门**（file_size→512MB 拒绝位+50MB big 态门；set_text 探针） | panic→fsize=-1→既有装载错误链/拒绝形（open_1gb 拒绝语义的承载点） | 进程死亡——**512MB 拒绝位失效为进程死亡**（budgets open_1gb 行语义面） |

内核侧（auto-lang 域，非生成码）：back_proxy.rs FFI 边界 panic 隔离
1 处生产用点（019 §⑤ 实勘——abort 即破该隔离；上游域）。

### ③-b 降级后果语义归纳（三路裁定材料）

- **load-bearing 兜底（2 点）**：会话恢复 fresh-start（稳健性主点
  ——损坏会话=拒启）、装载探测门（512MB 拒绝位/50MB big 门——
  budgets open_1gb 行判定语义域）。
- **逐项隔离兜底（3 语义点×2 成员）**：搜索跳过/copy/delete 批内
  逐项错误隔离——单坏文件升级为全操作（及进程）失败。
- **装饰面兜底（2 点）**：diff badge 探针——panic 概率低、后果纯
  视觉，但 abort 下同样致命化。
- **量级**：panic 触发条件=IO 竞态/损坏输入/编码异常——正常谱低频，
  ** editor 场景（损坏会话+超大文件）为真实入口**。abort 的收益
  （019 谱 -7.11MB）换的是这些点的「进程死亡化」。

### ③-c 三路裁定材料（Q-1 请示面——现势谱回填定稿）

| 路 | 内容 | 尺寸预期（现势谱+投影） | 语义代价 | 工期 |
|---|---|---|---|---|
| (a) panic=abort 入集 | abort+opt-z+V2b；兜底点逐点风险接受记录（③-b） | 组合投影 **≈16.5~16.8MB（超门 ~0.9~1.1MB）** | ③-b 全表致命化（会话恢复/512MB 拒绝门/逐项隔离×3 语义点）+back_proxy 内核隔离破 | 最短（纯 profile，1 构建+护栏复跑） |
| (b) 深裁路线 | 无 abort——V2b+opt-z+可达池全落（仅 R2 axum≈0.2~0.5MB） | **≈21.9~22.0MB（超门 ~6.2MB）**——缺口大头=上游域登记（R1/R3/R5/R8/R9 底座+wgpu/two-face 遗留） | 零语义代价 | 中（R2 一构建+cargo tree 特性图+护栏复跑） |
| (c) 分阶段维持 | 手段集维持 V2b（+z/abort 谱记录档）；≤15MB 遗留注记 | **30,403,072 B（超门 14.0MB）** | 零 | 零（谱已齐） |

**裁定面核心事实（三谱实证）**：①三路无一达 ≤15MB——(a) 最近仍
超 ~1MB（019「距门 714KB 即可达标」叙事在 716/022/工具链代差后
**已翻转入超门 ~1MB**——上游 want 未兑现前不可达）；②深裁可达池
仅 R2（<0.5MB）——(b) 数学上与 (c) 同为超门态，差别仅 z 的 7.8MB
与其护栏面；③语义冲突面（③-a/b 17 语句/8 语义点）使 (a) 的 ~1MB
收益对价=兜底语义全面致命化。**Q-2（tag 口径）在任一路径下均为活
问题**（无路达门→tag 必带注记或顺延）。

## ④ 附：构建通道缺陷修复记录（T-02 前置）

`stage_ts_patch` ts-on 终迹 return 缺失（68432be 撤钉批误删——
600ba65 双 return 形对照；ts-on 路径隐式 None→main 解包 TypeError，
ts-on 记录档构建通道断；ts-off 默认臂早退零扰）。修复 commit
**c0b402d**（worktree plan-023-dev）：return 复位+单元级三路径验证
（注入 (0,msg)/幂等二遍 (0,msg)/ts-off 早退）+py_compile 绿。全链
ts-on 实录不重跑（022 在档 51,457,024B——非目标判定域）。

## ⑤ T-04 工具链轨五行锚点复跑（v2546 工具链——裁定无关独立证据，
先于 T-02 落地：L2 判定面与 portable 手段集设计不敏感〔probe_surface
header 勘定语义〕，对三路裁定均有效）

L2 直拉标准链：perf.py a2r（14s——生成器缓存绿）→release（3m47s
pristine 无补丁基面——与 portable 补丁面分离纪律）→bench --l2 五行。
JSONL：steady-20261002-100425/warm-20261002-100436/open-20261002-
100505（首谱）+100637（复跑谱）/diff-20261002-100551。

| 行 | 现势谱（v0.4.2-2546-g986e765ac） | 021/022 对照基 | 判定 |
|---|---|---|---|
| steady_start | mean 17.8ms（median 17.0） | 021: 15.6ms | **armed PASS**（≤80；+2.2ms 工具链代漂注记——预算余量 4.5×） |
| warm_start 净段 | 2.6ms（全链 40.0ms；active 1130.6ms；Δmem 257MB） | 021: 0.0ms（2ms 轮询粒度带） | **armed PASS**（≤120） |
| open_100mb | median 865.8ms（4 跑 863.6-866.1 紧带） | 021: 863.2ms | **armed PASS**（≤1s——同带 ±0.3%；**首谱 1467.5ms〔open-100505〕=三连 release 构建余压机器态噪声——复跑如实显影，重试理由=瞬态条件改变，022 diff 784.8/1261.1 波动带同族先例**） |
| idle_mem | 9.1MB（空窗工作集 9,527,296B） | 021: 9.7MB | **armed PASS**（≤60） |
| diff_100mb 窗口形 | median 635.0ms（over_size 18.6/over_lines 84.7 全绿） | 022: 784.8/1261.1ms | **armed PASS**（≤2s——022 双谱带内偏好）；full-ref 对照档 5254.0ms（021 FAIL 5183.2ms 同形互证——数字在档不删） |
| open_1gb/513mb | rejected=True ×2 | 021 同形 | 拒绝位复证——**装载探测兜底链（③-a load-bearing 点）在 unwind 态活体功能正常** |

产物面（probe_surface 三行+烟测四段）=终态手段集 exe 依赖——T-02
裁定后件（dist/portable 现存 abort 记录档产物，非终态形）。

## ⑥ 裁定收口与终态判定（T-01/T-02/T-03——用户回执后）

- **裁定回执（2026-10-02，AskUserQuestion 两轮）**：第一轮（三路
  裁定）自主会话未获应答→blocked handoff；用户随后在对话中提出
  **门重基线**提议，第二轮问询定案：**installer ≤15MB→≤50MB、
  idle_mem ≤60MB→≤150MB（渲染暖态语义）——独立渲染期（iced+wgpu）
  过渡口径，RQHost 渲染拓扑落地后回归严格门（≤15MB+≤10MB 级）**；
  口径采 **50MB+150MB（推荐档）**。Q-1 收口为 **(c) 变体**：手段集
  维持 V2b（opt-level=3 保性能——M4 速度王座语义；panic=unwind 保
  17 处兜底；abort/opt-z 留测量档不启用）。Q-2 消解：installer 行
  重基线门下 **armed PASS**——tag 携带「重基线注记」而非「未达
  注记」。裁定语义=预算随渲染拓扑重分期（非放宽换绿）——战略
  §2.1 追记（PLAN-023）+发布语义原文不受扰。
- **落地面（双 face 同步——019 F-1 纪律）**：build_portable.py
  `BUDGET_BYTES=50*1024*1024`（注释=裁定出处+RQHost 回收）；
  budgets.json installer/idle_mem 两行（budget+validity+unlock——
  历史数字在档不删）；bench.py `_L0_STATES.installer` 文本+
  `idle_mem` 硬编码 60→150MB（armed 注记更新）。验证：py_compile
  ×2+JSON 有效性+`bench check` 绿（四证）。
- **终态判定（armed PASS——随终态构建回填）**：终态 V2b canonical
  构建（regen→V2b 补丁→release→50MB 门断言）在途——数字/sha/
  JSONL 名以 tools/portable/results/ 终态记录为准（首谱 V2b
  30,403,072B ≤ 52,428,800B 预期余量 21,998,336B——判定以实测
  为准不预写）。dist/portable/auto-edit.exe=发布形定稿（ts-off
  默认）。
- **产物面护栏（T-04 后半）**：见 §⑦。

## ⑦ 产物面护栏（终态 exe——probe_surface+烟测）

（随终态 exe 探针回填。）

## ⑧ 附：主检出预检记录（入场）

- `specs/stylekit/pac.at`+`specs/stylekit/src/front/styles.at` 删除态
  （43 行）+`tools/compare/results/table.md` 行尾幻影 M（零内容 diff
  ——CRLF/LF）：**022 T-00⑥ 已裁「他属会话 WIP——零触碰零包含，
  落地时另行路由」先例维持**；本件三谱构建均在 worktree 生成物面
  （gitignored），主检出 WIP 零包含零扰动。
- 立项簿记 commit：main@28d888b（plan 文件入册+executing）。
