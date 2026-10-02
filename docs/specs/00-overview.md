# auto-edit 规范总览（00-overview）

> 本册为 auto-edit 的规范知识层总览。规范正文自 PLAN-001..006 六个计划、
> `specs/auto-edit/README.md` 与代码重建（2026-09-22）。历史口径勘定：
> PLAN-002 立惯例「知识库=.autoos 账本+模块 README」——六计划的 SD 增量
> 均落 README（git 实迹在案），docs/specs/ 与 specs.json 四段从未建立；
> 本册补齐结构化文档面，README 保留为运行矩阵/快速上手单源。

## 项目定位（北极星摘要，全量见 docs/strategy/002-north-star-v2.md）

**AI 时代的轻量高性能文本工作台**：编辑器大部分时候用来**看**代码
（浏览/比对/审阅），批量编辑经 agent 结构化命令发生，人只做小步精修与
取舍；编辑器本体是**工具**——被 agent 驱动（tool use）、被其他应用嵌入
（编辑页组件化/Blueprint 化共享给 auto-musk 等），**不是 agent 宿主**
（那是 auto-musk 的位）。中期战场：diff 对打 Beyond Compare（M3）。

五条战略裁定（v2，2026-09-21）：①剥离多人协同（要 rope 性能不要协作
复杂度，viewing-first）；②重型语言服务出局（语义导航归 agent）；
③编码降维 UTF-8（含 BOM 与无损兜底，GBK 非目标）；④agent 交互收敛为
被驱动+被嵌入（ACP 搭载面砍除）；⑤缓冲区类预算（100MB/1GB/diff）在
内核 rope 化前**架构性不可达**——禁止提前调优，bench 只记基线并标
"架构阻塞"。

## 仓布局与命名注意

```
auto-edit/
├── docs/plans/          # 计划（6 个：001..005 归档 + 006 在途）
├── docs/strategy/       # 北极星战略（001-v1 存档 / 002-v2 现行基线）
├── docs/specs/          # 本册（规范知识层，2026-09-22 重建）
├── specs/               # ⚠ 命名碰撞：vendored 工程落地（非规范）
│   ├── PROVENANCE.md    # 拷贝来源：auto-lang examples/ui/{041-auto-edit,stylekit}
│   └── auto-edit/       # auto-edit 应用本体（src/ rust-workspace/ gen/ …）
└── tools/               # bootstrap_from_auto_lang.py / perf / bench
```

**`specs/` ≠ 规范**：它是 `tools/bootstrap_from_auto_lang.py` 从 auto-lang
vendored 的工程落地区（PROVENANCE.md 记录源 commit 与路径表，PLAN-002
起 blueprints fork 退役、改 dep path 消费）。规范文档唯一位置 =
`docs/specs/`（本册）。浏览 vendored 源码用文件浏览器，不进规范树。
bps 蓝图池经 `specs/auto-edit/pac.at` 的 `dep bps` 指向**兄弟仓**
auto-lang/blueprints（路径相对运行目录，主检出需同居 D:/autostack，
组 worktree 需组内兄弟树）。

## 规范结构

| 文件 | 内容 |
|---|---|
| [01-architecture.md](01-architecture.md) | 架构总纲：store 全承载/组件边界/actions DSL/front-back 拆分/双轨 |
| [modules/editor-store.md](modules/editor-store.md) | EditorStore 状态与数据契约（tabs/src 语义/收口 helper） |
| [modules/components.md](modules/components.md) | 013 组件模型与 vm 组件边界三硬约束 |
| [modules/actions-dsl.md](modules/actions-dsl.md) | 动作三源绑定（actions{} 声明块/热重载/OS 键位层） |
| [modules/back-api.md](modules/back-api.md) | front/back 边界契约（六 #[api]/引擎切换/fs 收口） |
| [modules/perf-measurement.md](modules/perf-measurement.md) | 测量模式阶梯与工具链（perf/bench/预算断言/上游阻塞） |
| [reviews/index.md](reviews/index.md) | 计划-收据索引（P001..P006） |

## 计划与规范的关系（流程约定）

计划实施 → review pass → **merge 阶段沉淀规范增量**（本册或模块册追加
节，注明来源计划）→ 归档。`.autoos/specs.json` 是 musk 结构化规范存储
（`/spec1` 命令读写面），其 reviews 段承载计划收据；文档规范以本册为
canonical。新计划修订规范走追加+来源注记，不回改历史节。

## M2 面开篇注记（PLAN-008，2026-09-22）

M2（Notepad++ 对位，战略 §2.2）首件已落：**打开→编辑→保存链路的文件
字节保真契约**（UTF-8 BOM 形态保留 / CRLF-LF-CR 识别-显示-转换-保留 /
非法 UTF-8 无损兜底——错误 tab+只读+save 拦截，绝不静默转码落盘）。
规范详 [modules/editor-store.md](modules/editor-store.md) 字节保真节与
[modules/back-api.md](modules/back-api.md) IO 字节语义节；矩阵 T12 检查
组（完成态 57/0）与 tests/fixtures/ 六件字节基准在仓。上游件（lossy
读端点/EOL 逐行保真）登记 docs/upstream 2026-09 供料 §11。

**第二件已落（PLAN-009，2026-09-22）**：**查找替换四态（正则/大小写/
整词/转义）+ 全部替换 + 跨文件查找（find-in-files）**——单一
find_effective 串拼装协议驱动高亮/替换/fif 三消费面（editor-store.md
查找替换节 + back-api.md 搜索服务端点节）；矩阵扩 T13 检查组（完成态
75/0）+ tests/fixtures/find/ 四件；检测器白名单扩 ReplaceAllRequest
（第三件显式全文操作）。上游件（单处替换/find_prev/匹配计数/goto 行
+ T-00 衍生观察件）登记 docs/upstream 2026-09 供料 §12。

**第三件已落（PLAN-010，2026-09-23）**：**会话恢复（懒装载）+ 最近文件**
——退出/崩溃后重启还原 tab 集+激活位，恢复 N tab 只读 1 个文件（懒装载
复用 PLAN-007 装载链现件）；APPDATA 根会话文件+SessionSave 五挂点即时
落盘=崩溃恢复底座；最近文件去重前移上限 10（Explorer 侧栏节——
menubar-content 动态子节点边界适配在案）。边界如实成文：脏内容不恢复
（back 版本化=L 线）、光标/滚动持久化但不应用（上游 set-cursor/scroll
端点 want 登记 docs/upstream §13）。editor-store.md 会话持久化与懒恢复
节；**back-api 零端点变更**（env_str/read_text/write_text/exists 四件
既有复用）；矩阵扩 T14 检查组（完成态 86/0）+ fixtures/session/ 两件。

**第四件已落（PLAN-013，2026-09-24）——M2 四件全落**：**大文件模式
v1（50MB 档）**——>50MB 进入大文件模式（战略 §2.2）：装载前探测门
（back 第 14 端点 `file_size` envelope）置 per-tab big 态→关折行（wrap
显式 false——现状勘定恒 false，零动作注记）+懒语法（lang plain=syntect
旁路，跳过非延迟）+**全文本命令护栏**（ReplaceAll/EolConvert/save 三
入口 big 态拦截+显式提示，readonly 不设=小步精修保留）；超大拒绝位
512MB（>之拒绝装载零 rope 分配——真分块 IO=上游阻塞，1GB 线非目标
注记，upstream §16）。内核零改动（wrap prop/plain 白名单/apply_config
热应用皆现役面）。editor-store.md 大文件模式节+back-api.md file_size
端点节（计数勘正 13→14）；矩阵扩 T17 检查组+bench bigfile 档（mode
on/off 尺寸杠杆代理对照）；决策探针 tests/probe_bigfile.py 为前置
决策门不入矩阵计数。上游件（code_editor_save 直写端点[护栏解除件]/
HTTP int 返回 serialize null 观察）登记 docs/upstream §16。

**M2 尾件与消费收口（PLAN-014，2026-09-25）——M2 完全收口**：M2 验
收面四件（008/009/010/013）后的尾债收口——**任务栏跳转列表**（补注
十一「Windows 集成余=小尾件」原文）：T-01 五面勘定裁定 (b)（源/二
进制/注册/动态全零，probe_jumplist.py）→用户确认改道供料段→供⑥
SHAddToRecentDocs shim（PLAN-701）→T-02 OpenPath 公共核直调消费（
editor-store.md 会话节消费条）；跳转列表壳记账的矩阵可断言面=零
（autoui_state 无 shell 面）——E2E 归手工/后续探针件。**上游端点消
费五件**（供料=PLAN-701，2026-09-25 delivered）：save 护栏解禁（供①
直写端点——big save 46ms/字节全等，T17.3 翻转）、光标恢复转正（供②
set_cursor——T18.2 断言）、time 族双录机制（供④——vue 映射缺口在
册 §17）、vue strict 双 exit 0 恢复（供⑤——print 缓解件退役）、
F-RV6 口径评估（供③——根因=跨会话 /IM sweep 误伤勘定，非工具链竞
态，§5 勘误随 §17）。矩阵扩 T18 检查组；上游消费收据登记 docs/
upstream §17。M2 面自本件起=**完全收口**（剩余增强件——滚动恢复/
EOL 逐行保真/单处替换族/tree-sitter——均为清单外后续件，M4 门控或
另行供料评估）。

## M3 面开篇注记（PLAN-011，2026-09-23）

M3（diff 对打 Beyond Compare，战略 §2.3）首件已落：**文件 diff v1——
并排只读视图 + 过渡计算层 + hunk 导航**（补注十一提前开工口径：
M2/M3 交错，大文件模式压后）。核心形态：**引擎无关编排层先行**——
back 端点 `diff_files`（第十件 #[api]）落朴素分层过渡计算（公共前后缀
裁剪 → ≤200 行 DP-LCS → 大中段降级 replace → 索引对齐配对+行内三段
标记 → ctx 窗切 hunk），**envelope 契约=替换缝**（内核 diff 引擎落地
仅换 back 实现体，视图/矩阵零改动）；根视图全幅并排视图（行号×2/
种类着色/三段 mid 着重/±计数/hunk 位次）+ F7/Shift+F7 hunk 导航
（scroll_to 24px/行，T-00 实测定参）。边界如实成文：**双文件磁盘态
比较**（与编辑中缓冲区比较需全文读出撞零全文 tab 铁律——引擎
diff_snapshots 端点直读 rope 才是正解，供料 §5）；文件上限 10k 行/
1MB（T-00 保守定参，50k/2MB 预判不成立已注记）；100MB ≤2s 预算
blocked-on-upstream 记账（bench `diff` 档门拒延迟+基线 JSONL）。
规范详 [modules/diff-view.md](modules/diff-view.md)（新册）+
[modules/back-api.md](modules/back-api.md) 文件 diff 端点节（计数勘正
9→10）；矩阵扩 T15 检查组 + tests/fixtures/diff/ 六形态 golden；
决策探针 tests/probe_diff.py（26/0）为前置决策门不入矩阵计数。上游件
（函数返回值丢失疑回归 P1/嵌套大表挂死崩/onscroll 回声漂移/性能漂移
对测/F-RV6 复现增补）登记 docs/upstream 2026-09 供料 §14。

## M3 第二件注记（PLAN-012，2026-09-23）

M3 第二件已落：**目录 diff v1——递归比对 + 状态过滤 + 基础同步 +
文件 diff 下钻**（战略 §2.3；BC 工作流闭环=目录比对→双击改项→并排
diff）。核心形态：**引擎无关**（元数据递归遍历走 009 search_files
现役集 list_dir/is_dir/size）+ **五态分类**（同/改/删[只在左]/增
[只在右]/二进制启发式[非法 UTF-8≈read_text==""，≤2MB 全文域]）+
**基础同步**（单向复制/单侧删除，破坏性动作 alert-dialog 确认链；
文件复制=字节往返 read_bytes→write_bytes——fs.copy 被 `copy` 保留字
阻断，T-00 勘定 upstream §15 want）+ 下钻复用 011 文件 diff 视图
（dir_from_dirs 归位门，零新视图件）。边界如实成文：>2MB 同尺寸=
「同(未比对)」注记态（hash want）；对齐=长度桶+桶积护栏 700k（同长
巨桶超 VM 步数预算=优雅 err——sort/hash 原语 want）；folder picker
无（v1 路径输入框+env 旁路）；递归删除不提供（仅空目录）。
规范详 [modules/diff-view.md](modules/diff-view.md) 目录节（SD-01
追加）+ [modules/back-api.md](modules/back-api.md) 目录 diff 与同步
端点节（计数勘正 10→13）；矩阵扩 T16 检查组 + tests/fixtures/dirdiff/
五形态 golden；决策探针 tests/probe_dirdiff.py（27/0）为前置决策门
不入矩阵计数。上游件（copy 保留字阻断/folder picker want/file-hash
比对 want/sort-hash 原语 want）登记 docs/upstream 2026-09 供料 §15。

## M3 第三件注记（PLAN-015，2026-09-26）

M3 第三件已落：**文件 diff 内联（unified）视图——完全体两视图收尾**
（战略 §2.3「并排+内联两视图」后半）。核心形态：**纯视图件**——
irows 投影派生自既有渲染行（pair 行两行展开 del 先 add 后、三段按源侧
继承、行号双列缺席空串），切换=纯 front 状态重建（**零 back 调用零
重比**，矩阵断言 envelope 派生面不变），hunk 导航 vmode 条件扫 irows
（24px 偏移公式共用），双 cap 独立截断（信封 600+内联 600 并列注记，
拦腰形合法——big_reorder 298 全 pair+1 孤 del 实证）。**envelope/
back 零改动=PLAN-011 替换缝红利首兑现**（内核引擎落地仍仅换
`fsys.diff_files_json` 实现体）。边界如实成文：**本件后 M3 本仓面在
引擎落地前再无无阻塞验收项**——histogram/100MB ≤2s/差异侧直接编辑
重比/与编辑缓冲区比较全数门控于上游供料包
（docs/upstream/2026-09-diff-engine-supply.md 五件，**截至本件无承接
立项**——M3 后续件排期实质由上游承接时序决定，PLAN-015 §10 Q-1 在案）。
规范详 [modules/diff-view.md](modules/diff-view.md) 内联视图节（SD-01
追加）+ README 矩阵 T15 组 P15 断言族（**矩阵承载面=desktop_mcp.py
T15 组 15.11–15.15 五子组**——完成态 125 检查=120+5、判绿 ≥117/0，
修复轮 120/5=已知集全中零新失败；smoke_t234 37 项=开发期烟测件不入
矩阵计数；决策探针 probe_diff.py ⑥推导器 58/0 为前置决策门）。

## M3 第四件注记（PLAN-016，2026-09-27 立项/09-28 修复轮清偿——上游承接后首件）

M3 第四件=**diff 引擎消费件**（auto-lang PLAN-703 供料包
46efa926a 的下游兑现，015 注记「引擎前清单清零+上游承接悬案」的承接
件）：**替换缝兑现**（fsys.diff_files_json/diff_dirs_json 实现体换
native 9915/9917 裸名直调纯转发——PLAN-011 声明落位；上限门四门
退场、degraded 恒 false、「等待内核引擎」文案族退役；目录面语义零
漂移+同长巨桶正常出结果）+ **diff_snapshots 缓冲区比较 v1**（第 15
端点 diff_buffers 净形+面板双序号输入+跳转 set_cursor+AUTO_DIFFBUF
旁路——011 边界注记正解落位）+ **100MB bench 真跑**（战略 §2.1
预算行判定）。
**修复轮清偿（2026-09-28，auto-lang PLAN-704 b2f8761e0）**：执行期
勘定的引擎双缺陷（D-1 rows 面流位错配/D-2 anchor 非单调——供料档
§6.2 源码行级根因在案）由上游修订件清偿→下游 golden 重定轮完成
（五简单形 golden 原样恢复=引擎≡过渡参考逐字节全等；big_reorder 按
修复后引擎重定 310/310 引擎时代换位语义）、T15 rows 面判绿恢复
（修复轮全矩阵 124/5=已知族全中零新失败——判绿回 014/015 原集）、
bench diff_100mb **≤2s 达成**（release 全链 1906/1971ms，踩线余量
~5%；缺陷期绊线纪律与对账证据 evidence-p016-recon.json 保全在档）。
M3 剩余=**差异侧直接编辑重比**+**语法高亮联动**（后续件）。
规范详 modules/diff-view.md 引擎时代与缓冲区比较节（SD-01）+
modules/back-api.md 第 15 端点节（SD-02）+ 供料档消费回执节
（SD-06）。

## M3 第五件注记（PLAN-017，2026-09-28——M3 本仓面收口）

M3 第五件已落：**差异侧编辑回路——差异侧直接编辑 v1**（战略 §2.3
完全体项「差异侧直接编辑（编辑后即时重比）」的 v1 形态=编辑回路
闭环）：**双侧跳转编辑**（diff 视图头部双钮+hunk 变更行内联钮→目标
文件 tab 打开/激活+装载等待落 hunk 首行——016 装载轮转先例 handler
化；跳转即藏视图、保存后自动重开）+ **保存自动重比**（WriteFidelity
两臂单挂点三域分派——文件 diff 重比/下钻双刷新/缓冲区面板刷新，
vmode·过滤态保持、无关保存零动作）+ **净形即时预览**（内容变更位
防抖单拍——缓冲区面板 live 刷新+文件视图 badge「预览 +N/-M（未
保存）」probe 隐藏键轨形[T-00③ 勘定]）+ **B 侧跳转补全**（016 尾注
清偿——DiffBufJump 双臂+净形行双钮）。**边界如实成文**：BC 同款
「diff 视图内直接键入（in-place）」=上游混源（file↔buffer）rows
envelope 缺位——供料 want 登记（供料档 §6.3），in-place 形态属后续
件。**本件后 M3 本仓面收口**（剩余语法高亮联动=M4 首批 tree-sitter
——供料驱动）。纯 front 件（back 零改动）。规范详 modules/
diff-view.md 差异侧编辑回路节（SD-01）。

## M4 面开篇注记（PLAN-018，2026-09-29）

M4（速度王座与发布，战略 §6）开篇件已落：**M4 解阻供料包落档+
budgets 全表重定+可达行首批锚点**。M4 四产出（预算全绿/installer/
公开对比表 NP++·Zed·BC/语法高亮首批 tree-sitter）全部门控于上游
解阻或用户裁定——本件按 M1「供料先行+本仓并行」开篇模式：**供料包
四件**（`docs/upstream/2026-09-m4-perf-unblock-supply.md`——供① a2r
生成缺口三类残余[G-A envelope 访问投影/G-B try 块/G-C delta 臂；
a2r 探针 exit 3 实证，read_text_range=687 已解、18/19 内建已映射]/
供② 内核帧时间戳插桩/供③ 大文件实例卡死回归[T17 blocked 族]/
供④ tree-sitter 首批[现役 syntect/two-face 实勘，两段式]）；
**budgets.json 全表重定**（open 两行过期「架构性不可达」文本纠偏
「解锁待测」+禁调优放开仅限此两行+供料排队注记+断言终态 ledger 化
——arch-blocked 位 l0 覆盖转缺席=语义退役显影）；**可达行首批锚点**
（release 工具链全链记账形态：open_100mb 装载墙钟 median 841.0ms
≤1s 行内首实测锚[big 态语义]+1GB=512MB 拒绝位实证+513MB 边界对照/
steady_start 分解 232.6ms 归因 VM boot 段 224.5ms[瘦身=后续件]/
warm_start 恢复净段 1.3ms ≤120ms 绿注记+不读盘标记单对实证/
idle_mem 空窗 51.4MB ≤60MB 行内）。**断言形态分层（frozen）**：锚点
=记账不阻塞，硬判定维持 L2 唯一预算效力——供① 解阻后切正主 L2
形态，锚点不冒领。M4 主线预告=上游承接逐件清偿→L2 断言全表→Q3
裁定→installer→公开对比表。规范详 modules/perf-measurement.md
预算门 M4 节（SD-02）+ specs/auto-edit/README.md PLAN-018 口径
（SD-04）+ 供料档（SD-01）。

**M4 第二件注记（PLAN-019，2026-09-29）**：installer/portable 瘦身件
已落（Q3 裁定兑现：**a2r 原生化瘦身+纯 portable**——winget/自动更新
不入后续件议）。构建通道 `tools/portable/build_portable.py`（regen→
补丁注入幂等通道→release→strip→dist 断言——regen 现势化=供① 阻塞
维持，last-good 基面复用+漂移适配在案）。**首件未达标=分阶段语义**
：基线 39.4MB→终态手段集 29.8MB（lto=fat+cgu1+strip+tokio 子集，
-24.3%）；门控组合实测 16.46MB 距 ≤15MB 门仅 714KB（panic=abort
[back_proxy catch_unwind 语义面]/opt-level=z[性能护栏]——用户裁定面）；
剩余大头=上游域（wgpu 栈 4.1MB .text+two-face 全量语法集[.rdata
12.4MB 主项]+image/HTTP/字体栈——构成表 evidence-p019-survey §④），
two-face 子集 want 已登记（供料档 §5 条件触发）。**对比表=下一
blocker 位**（L2 数字齐后件——供① 解阻+锚点 L2 化前置）。规范详
modules/perf-measurement.md installer/portable 形态节+budgets.json
installer 行（数字回填）。

**M4 第三件注记（PLAN-020，2026-09-29）**：公开对比表**竞品侧先行
件**已落（对比表件中唯一无门控半件——竞品数字不依赖我方 L2）。
测量方法论勘定（四对象计时通道+计时点定义——VS Code=renderer RSS
平台[确认窗分档防假平台：5MB=3s/100MB=6s]/Zed=首帧日志行[rope 惰性
注记]/BC5=report 产出/NP++=pending[缺位，安装=用户面 Q-1]；滚动
帧率=v1 后补——捕获自动化双缺陷实证；median=上中位约定 frozen）
+同机 harness（tools/compare/ 三脚本——三要素门内建+invalid-run
重跑条款）+竞品基线数字（VS Code 1.139.1/Zed 1.20.2/BC5 5.0.6 实谱
在档，results/ 入仓）+我方锚点占位列（**三态分层防冒领**：锚点
[VM 形态]/产物面[last-good]/L2-pending[禁出数]；diff 行=016 release
全链判定先例 1906ms）+README 表位生成区间。**我方 L2 正式列仍虚席**
（供① 解阻后 L2 形态重测补列——关键路径注记维持：供① 承接建议
路由 auto-lang 侧计划，本件不替代）。规范详 modules/
perf-measurement.md 公开对比表节（SD-01）+specs/auto-edit/README.md
PLAN-020 口径与表节（SD-03）。

**M4 第四件注记（PLAN-021，2026-09-30——解阻日首判）**：L2 链解阻
兑现件（供① PLAN-710 消费）全弧收口——**供① 残余两面经 PLAN-714
r2/r3 清偿[用户指令收纳 714 r2→needs_replan→r3 深修 delivered]，本件
fresh 补跑=L2 直拉形态首判落地**。绿面：a2r 三重判据首度全绿（exit 0+
零 skip 警告+fresh workspace check 过+route-A 实体形）+last-good 基面
退役（regen 现势直跑+幂等自证）+生成码首跑收据+三域冒烟 G-A/G-B 实证
（会话 try 两臂+包络投影 golden 3/3）。**首判数字（五行其三）**：
steady_start armed **PASS** mean 15.6ms ≤80ms（L2 唯一预算效力首次
兑现——018 VM 形态 232.6ms 归因随直拉消失）/idle_mem armed **PASS**
9.7MB ≤60MB/diff_100mb armed **FAIL**（记录性）5183.2ms >2s（back
直拉形态——016 VM 1906ms 达标为形态对照，rows 惰性投影 want 直拉化
放大）。**残余已清偿+全表收口（同日 714 r4——e93a717da 动态注册键
贯通）**：open_100mb armed **PASS** median 863.2ms ≤1s（018 记账形态
841.0ms 同量级复现）/warm_start armed **PASS** 恢复净段 0.0ms·全链
19.3ms ≤120ms（018 VM 形态 240ms 放大随直拉消失）——**预算表五行判
定全部落地**（三 PASS+diff 记录性 FAIL；「滚动不掉帧」半行=供②、
open_1gb=裁定中、renderer=n/a 维持）；三域冒烟 7/7 全绿（§7 三 FAIL
反转）；对比表 open 行 L2 实数补列+l2-pending 虚席退役。M4 剩余=
供② 两行断言（type_latency/scroll_fps）/installer two-face 收口/
供④ 语法面实施件[714 勘定+实施契约在档]/open_1gb 裁定（材料在档
Q-1）。规范详
modules/perf-measurement.md PLAN-021 节（SD-01）+README PLAN-021
口径（SD-03）。

**M4 第五件注记（PLAN-022，2026-10-01——PLAN-716 三组消费件）**：
auto-lang PLAN-716（三组合一，2026-09-30 delivered——组C diff 窗口
端点/组B 帧观测通道/组A tree-sitter 双轨+tail 固化）的下游消费件
已落：**①diff_100mb FAIL 清偿重判**——判定档切窗口形（9920
`/api/diff_files_window` 五参消费，limit=600 渲染 cap 对齐「出结果」
口径=全量 hunks/counts/rows_total+首窗 rows；全量形保留对照档不删）
——**armed PASS median 784.8ms** ≤2s（021 FAIL 5183.2ms 清偿，6.5×
倍率；对比表 diff 行三态并陈）；**②对比表滚动列落位**（我方
l2-pending 零数字虚席+竞品 020 Q-2 pending 维持——协议在档不冒领）；
**③双构建形态通道**（build_portable `--ts on/off`——highlight-
treesitter feature 门控注入，ts-off=发布/installer 约束形[默认]/
ts-on=语法完整形[+18.9MB 量级]，产物双命名 dist 断言分域）；**④供③
P716-D1 销账多跑**（全矩阵 ×3——P716-D1 处方落实[主实例 MCP 端口
高带钉位臂]+T17 簇×3 谱在档）；**⑤上游消费首跑双缺口登记（供⑧/
供⑨，供料档 §8）**——9920 VM codegen 裸名臂缺失（L0 形窗口调用
挂死；L2 判定面不受累）+9918/9919 .at 消费面双缺口（VM i64→int 桥
退化+a2r ui_gen 臂 E0425——**帧两行判定面 blocked 待供⑨**，协议
成文+budgets 两行证据链行+l2-pending 虚席位）；**⑥语法高亮联动
want 登记**（highlight_segments 无 .at 可达面——三面 grep 零命中
实证，M3 尾巴供料驱动注记维持，供料档 §8 want 节）。front 消费面
零改动（窗口化仅 back/bench 域——frozen③ 维持）。**M4 剩余=
installer 收口件**（ts-off 形态尺寸判定+门控手段裁定——本件 ts-off
通道即其前置）/open_1gb 裁定（用户件）/NP++ 列（用户安装后补跑）/
帧两行首判（待供⑨）。规范详 modules/perf-measurement.md PLAN-022
节（SD-01）+modules/diff-view.md 窗口形节（SD-02）+
modules/back-api.md 第 16 端点节（SD-03）+README PLAN-022 口径
（SD-05）+供料档 §8（SD-06）。

**M4 第六件注记（PLAN-023，2026-10-02——installer 收口件，判定终态
）**：**①现势三代谱重测**（工具链 v0.4.2-2546-g986e765ac，ts-off
发布形）——V2b **30,403,072B**/opt-z 22,206,976B/abort 记录档
22,646,272B；组合投影 16.5~16.8MB——019「距门 714KB 可达标」叙事
实证翻转（下游深裁可达池仅 axum diet <0.5MB，缺口大头=上游域）；
**②panic=abort×catch_unwind 冲突勘定**（生成物 17 语句/8 语义点
——会话恢复 fresh-start+512MB 拒绝门=load-bearing）→abort 出局；
**③门重基线（用户裁定——AskUserQuestion 回执 2026-10-02）**：
installer ≤15MB→**≤50MB**、idle_mem ≤60MB→**≤150MB**（渲染暖态
）——独立渲染期过渡口径，**RQHost 渲染拓扑落地后回归严格门
（≤20MB+≤10MB 级——同日精调 15→20MB，双已知路径校准）**（回收承诺=战略 §2.1 追记在案）；**④判定终态
=armed PASS**（V2b 维持：opt-level=3 保性能+panic=unwind 保兜底
——30,403,072B ≤ 50MB 余量 22.0MB；ts-off=发布形默认）；**⑤护栏
零回退**（工具链轨五行 v2546 复跑全绿——steady 17.8ms/open
865.8ms/warm 2.6ms/idle 9.1MB/diff 窗口 635.0ms，021/022 对照带内
；产物面 probe_surface+烟测四段随终态 exe）。**M4 剩余清单终态**：
帧两行 FAIL 清偿（上游管线件——auto-lang 域另行立项）+open_1gb
裁定（用户件+上游域）+NP++ 列（用户安装后补跑）——**M4 tag 口径
=installer 行 armed PASS（重基线门下）随第五件帧两行 armed FAIL
注记并陈**（帧两行=上游管线件不阻 tag，注记在案即可）。规范详
modules/perf-measurement.md installer 判定终态节（SD-01）+
specs/auto-edit/README.md PLAN-023 口径（SD-03）+
docs/strategy/002-north-star-v2.md §2.1 重基线追记（SD-04）。

**M4 第七件注记（PLAN-024，2026-10-02——M4 收口件，判定面快照态）**：
**①帧两行重判（725 帧管线增量交付后同机复判，release v0.4.2-2579-
gb385534d7，N=4 有效谱）**——P50 110→1-4ms（**中位 ~30×：单帧单建/
载荷增量/脏域重建生效实证，脏帧 builds=1 全体**）而判定行 **FAIL
维持**（P95 95-112ms>16.7ms/scroll 6.7-8.8fps<54——022 首判同带）；
分段归因=**段外 ~108ms=S5 域（layout/shaping/draw 未插桩）**〔尾部帧
与 ce_widget_new 组件重建事件同现；滚动帧 begin→begin ~108ms 节奏+
掉泵直落主导——725 handoff 预告如实显影；下游 handler 臂成本排除〕；
**S5 增量化=auto-lang 余题**（归因回执 evidence-p024-frame-rejudge）；
判定口径 frozen 零改动。**②收口三注记**：NP++ 未装（四路探测 2026-
10-02）→对比表 pending 维持+**Q-3 默认口径落档：列完整性=后续补列域
非里程碑判定门——tag 不等待**；对比表滚动行=022 首判+024 重判并陈
（--verify 10 行+--check 双绿）；**open_1gb 裁定落账=用户裁 (b)
（2026-10-02）**——供⑮ 文件后援分页 rope want 入供料档 §10（完整
标准设计种子：不可变基底+编辑覆盖层+LRU/RSS 上界+异步调入+保存
合并），M4 以 ledger-blocked-with-plan 收口（战略承诺保持；512MB
拒绝位活体维持至供⑮ 交付）。**③M4 终检表**=预算十行终态
（6 PASS+2 FAIL+renderer n/a+open_1gb 待裁——过渡门口径注记随行）+
四面核销（installer/对比表/语法高亮首批=核销；预算面=帧两行余题
双态如实）——详 modules/perf-measurement.md M4 判定收口节（SD-01）+
specs/auto-edit/README.md PLAN-024 口径（SD-03）。**④v0.1-M4 tag
记录位**：打点=本件 merge 收据（五检查点后——v0.1-M1/M2/M3 惯例；
素材 evidence-p024-m4-final-check 逐字对账；口径=023 已录「帧两行
不阻 tag+注记并陈」+里程碑标记≠发布）；**M4 完全收口=帧两行清偿
（S5 上游件）后——open_1gb 已按 (b) 落账即收口**；L1/L2 线开篇=
tag 后另议（战略 §6 顺序）。

**M4 后续件注记（PLAN-025，2026-10-02——供⑮ 消费件，M4 挂账余题
清单头号件清偿）**：上游 PLAN-728（文件后援分页 rope，
delivered@69059dfaa）交付后下游消费兑现——**①512MB 拒绝位退役**
（用户裁 Q-1=(a) 移除，AskUserQuestion 回执 2026-10-02：editor_store.at
拒绝臂/「只读(超大拒绝)」标签族退役；big 态命令护栏零回退；50MB=
唯一分域线〔与内核 PAGED_LOAD_THRESHOLD 对齐〕）；**②1GB E2E 全
链**（T17.9-12 四链冒烟+T17.5 翻转 513MB+1B 装载成功形+T18.1 重铸
零编辑直写往返）；**③open_1gb 断言化收口**（budgets 行 armed——
「可打开」=装载成功 E2E 断言非时间预算；bench open 档重铸：拒绝位
对照档退役→真内容装载锚点族〔阈界双轨 50MB 恰界/界下 1B+513MB
边界+1GB〕）；**④供料档 §10 消费回执节**（供⑮ 全弧终结：want
登记[024]→728 实施→025 消费三段闭环——669 模式）。附带：>50MB
tab 会话语义现状成文（editor-store SD：全量入册懒恢复、1GB 恢复=
再装载 ~4s 按现状接受）；014 期大文件实例 UI 硬卡死在 728 工具链
未复现（T17 交互簇预期自动复绿）+查找分页扫描债下游实测确认（upstream
余题回传）。详供料档 §10 消费回执+editor-store SD（PLAN-025 节）+
perf-measurement SD（open_1gb 断言化节）+README PLAN-025 口径。
**M4 挂账余题清单更新**：open_1gb=清偿（本件）；剩余=S5 段增量化
〔帧两行——auto-lang 域〕/供⑭ 插件化/RQHost 回归门（均 auto-lang
域为主）。

**兄弟仓 Q1 裁定摘要（2026-09-22，战略补注十收口）**：jade-edit 与
auto-edit **两产品长期并存**（auto=原生旗舰轻量编辑器、jade=web 轻量
版并向知识库发展），组件尽量共用（未来插件级共用）。jade 侧战略文档
已自行落账，本册只存摘要不重复正文。
