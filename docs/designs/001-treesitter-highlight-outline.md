# tree-sitter 高亮与 outline 设计预研（M4 前置档）

> 状态：**方向已裁定，详细规划留待 M3**（用户 2026-09-23 指示——「把上面
> 的分析和安排记录到设计文档里去。到 M3 时再去详细讨论规划」）。
> 本档=选型分析+阶段安排+体积/启动核算+加载形态的决策记录；M3 收口
> diff 后依此落 tree-sitter 内核化供料件与 M4 首计划。
> 序列背景：战略补注十一（2026-09-23）——010 会话恢复收口 → M3 diff
> 提前开工（大文件模式压后）→ M4 速度王座与发布（语法高亮首批
> tree-sitter + **本档新增：outline 视图搭车**）。

## 1. 决策清单（2026-09-23）

| # | 决策 | 依据 |
|---|---|---|
| D-1 | outline **不走 LSP**，底座=tree-sitter 增量语法树 | 战略宪法 §1.3（重型语言服务出局）+ §3.3（tree-sitter 树上的大纲/跳转，非语言服务）；大纲所需符号（fn/class/struct/impl）全是语法结构 |
| D-2 | **outline 视图放 M4**，随语法高亮首批搭车 | §4.2 一树多用（高亮/大纲/折叠共用增量树）；高亮是重消费者、outline 是轻消费者（tree query→侧栏→点击跳转），边际成本低；viewing-first 气质合 M4 发布面 |
| D-3 | 工程级符号索引/跨文件跳转留 **L2**（路线图原位） | 符号索引深水区，配 L2 组件化/导航主题 |
| D-4 | **首批语言集含 Auto 自身语法（.at）**（用户新增裁定） | dogfooding（本仓工作区即 .at 文件）+ 质量自控（自家语法自家维护）+ 展示性（编辑器跑在自家代码上）；实现注记见 §5 |
| D-5 | 首批形态=**内嵌 10–12 门精简集 + 长尾语言包**（M4/Q3 联合裁定 B/C 形态） | 体积预算实测推断（§4）：20 门全内嵌≈15–30MB raw 大概率撞 ≤15MB 单 exe 硬预算；启动零影响（§6） |
| D-6 | tree-sitter 供料件 **M3 时落**（含逐语言体积实测表/构建旗标统一 `-Os`+strip/首批清单含 .at/.at 语法件） | 供料先行逻辑（diff 供料包同模式）；本档分析数据为估算级，供料件要求实测核算 |

## 2. 选型分析：tree-sitter 是当前最优解

**格局**：编辑器内嵌增量解析赛道，可比产品殊途同归——Zed（tree-sitter
作者的编辑器）/Neovim/Helix/Emacs/GitHub 代码导航全部采用。对我们宪法级
的三条约束全中：增量解析（只重析变化区间，与 rope 快照模型同构）、容错
解析（残缺代码出树，编辑现场常态）、**一树多用**（`highlights.scm`/
`outline.scm`/`folds.scm` 三个查询文件共用一棵树——现内核折叠是独立
实现 core/fold.rs，迁移后高亮/大纲/折叠三件归一）。

**替代品排除**：

| 候选 | 排除理由 |
|---|---|
| syntect（现状，Cargo 实勘 syntect 5 + two-face） | 正则引擎无树可查（outline/折叠无解）；行级匹配多行结构误染；**全文档高亮大文件已是痛点**（core/mod.rs 注释在案：全文档 shape+highlight 实测 26s 量级，靠视口切片缓解） |
| Lezer（CodeMirror 6） | JS 生态，Rust 内核不可嵌 |
| LSP semantic tokens | 宪法排除（§1.3）；进程树与绿色单 exe 冲突 |
| ctags | 外部进程模型，不合进程内增量 |
| stack-graphs（GitHub） | 解定义跳转/引用的另一问题，非 outline |

**结论**：tree-sitter 迁移是「既开新能力（outline/一树三用）也修旧痛点
（syntect 全文档扫描）」的双收益件；无更优替代。

## 3. 阶段安排与序列

```
010 会话恢复（当前）→ M3 diff（提前，补注十一）
  └─ M3 收口时：落 tree-sitter 内核化供料件（D-6）+ 详细规划
→ M4 速度王座与发布：
   ├─ 语法高亮首批（tree-sitter，§6 路线图原列项）
   ├─ outline 视图搭车（D-2）
   └─ 首批语言集+加载形态裁定（与 Q3 installer 联合，D-5）
→ L2：tree-sitter 全量语言 + 轻量符号索引（大纲工程级/跨文件跳转）
```

outline 点击跳转的落点=editor set-cursor/goto 端点——**upstream §12 已
登记 want**（fif 结果跳行/会话光标恢复/outline 三件共用一端点）。

## 4. 首批语言集与体积预算（估算级，供料件要求实测）

单门语法编译后量级（社区实测点）：

| 语言类型 | 编译后大小 |
|---|---|
| 小语法（bash/lua/json/yaml/toml/regex） | ~100–300KB |
| 中语法（python/go/rust/javascript/ruby） | ~0.4–1MB（python .so 实测 ≈503KB） |
| 重语法（typescript+tsx 两门、C++、java、C#） | ~1–3MB/门 |
| 特例（markdown 家族：本体+inline+注入） | 多门成套，易低估 |
| **.at（Auto 自身，D-4）** | 中量级预估（语法复杂度≈配置+表达式语言；自研可控） |

- **20 门合计**：raw ≈15–30MB；统一 `-Os`+strip（去 debug 符号，社区
  记录不 strip 显著膨胀）后 ≈10–20MB。
- **净增量=替换不是叠加**：syntect+two-face 的 Sublime 语法定义打包
  （数 MB）迁移后撤除；净增 ≈+8–17MB。
- **对照硬预算**：§2.1 ≤15MB 单 exe——20 门全内嵌大概率超；**10–12 门
  精选**（四门小语法 json/yaml/toml/bash + .at + rust/go/python/
  javascript/markdown 等核心）增量约 5–8MB，预算内可控。
- 供料件硬要求：**逐语言体积实测表**（构建旗标统一 -Os+strip）、首批
  清单成文、长尾形态（B/C）留 M4/Q3 联合裁定。

## 5. Auto 自身语法（.at）——首批必含（D-4）

- **理由**：本仓/全家桶工作区就是 .at 文件（dogfooding 即展示面）；
  自家语法质量自控；编辑器跑在自家代码上是最自然的产品叙事。
- **归属**：tree-sitter .at 语法（grammar 定义+query 文件三件套）是
  auto-lang 侧交付物，随 tree-sitter 内核化供料件同包。
- **维护注记（漂移风险）**：.at 的语法权威源=auto-lang 手写 parser
  （Parser::from 族）；tree-sitter 语法（grammar.js 形态）是**第二实现**
  ——两实现长期并存有漂移风险。供料件需带同步策略（语法变更 checklist
  或双实现一致性测试面）；首版以「高亮+outline 够用」为准，不追求
  parser 级完备（不用于编译，仅用于编辑器面）。

## 6. 启动性能：零影响（惰性实例化）

- 语法 parser 仅在「打开该语言文件」时实例化+首次解析（典型文件 ms
  级），编辑走增量；**启动空窗口不触任何语法**——steady_start ≤80ms
  预算测暖态空窗口，零扰动。
- 冷启动多读 10–30MB 磁盘在 NVMe ≈几十 ms，OS 页缓存暖态后无感。
- 内核已有同款惰性形态先例（`highlight.rs` `warm_language` 后台预热），
  tree-sitter 沿用。
- 大文件侧注记：Helix 对超大文件禁 tree-sitter 的先例在案——我们的
  大文件模式（压后件）届时与此联动（阈值策略归大文件模式计划）。

## 7. 加载形态三模式与约束

| 模式 | 形态 | 代价 |
|---|---|---|
| A 全内嵌+惰性实例（Zed） | 语法编译进 exe，用到才实例化 | 体积全付，最简单 |
| B 边车语言包（Helix） | `grammars/*.dll` 旁置目录按需加载 | exe 瘦身；破坏「单 exe 无运行时依赖」 |
| C 下载式（Neovim） | 首用下载到 APPDATA | exe 最小；网络/供应链面 |

宪法层面无碍：语法包是**数据/资源非插件生态**（§1.3 禁的是第三方扩展
面）。裁决点=§2.1 预算行 + Q3（installer/更新，M4 前议）——**D-5 折中：
首批 10–12 门内嵌（含 .at），重语法长尾走 B/C，M4 时有实测数字再裁**。

## 8. 后续动作（M3 时）

1. 落 tree-sitter 内核化供料件（docs/upstream 新包或并入现有包——
   含：增量解析树 API 面（节点查询/符号提取）、逐语言体积实测表、
   首批清单（含 .at 语法件+双实现同步策略）、syntect 过渡/兜底策略
   （并存 or 直接替换）、tags/outline/folds 查询约定）。
2. 本档决策接进路线图/战略（如需补注，届时一并）。
3. M4 首计划起草时以供料件上游进展为输入。

## 9. 参考来源

- [Wikipedia: Tree-sitter](https://en.wikipedia.org/wiki/Tree-sitter_(parser_generator))
- [tree-sitter-highlight crate](https://crates.io/crates/tree-sitter-highlight) ·
  [syntect crate](https://crates.io/crates/syntect)
- [Helix: tree-sitter on big files 讨论](https://github.com/helix-editor/helix)
- [Hacker News: python .so ≈503KB 实测](https://news.ycombinator.com)
- [Neovim Treesitter 文档（parser 加载模型）](https://neovim.io)
- [The tree-sitter packaging mess（分发/构建差异）](https://ayats.org)
- [dotat.at tree-sitter 使用记](https://dotat.at) ·
  [Lobste.rs: syntax highlighting with tree-sitter](https://lobste.rs)
- 仓内实勘：`crates/auto-lang/Cargo.toml`（syntect 5/two-face，无
  tree-sitter 依赖）；`core/highlight.rs`（syntect 实现与 warm_language）；
  `core/fold.rs`（折叠独立实现）；`core/mod.rs` 全文档高亮 26s 注记——
  2026-09-23 勘（auto-lang 1914 主检出）。
