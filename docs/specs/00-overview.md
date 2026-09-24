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

**兄弟仓 Q1 裁定摘要（2026-09-22，战略补注十收口）**：jade-edit 与
auto-edit **两产品长期并存**（auto=原生旗舰轻量编辑器、jade=web 轻量
版并向知识库发展），组件尽量共用（未来插件级共用）。jade 侧战略文档
已自行落账，本册只存摘要不重复正文。
