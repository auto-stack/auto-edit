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
