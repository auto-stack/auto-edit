---
plan_id: PLAN-015
status: reviewed
feature_name: M3-03 文件 diff 内联（unified）视图——完全体两视图收尾
author: [agent]
created_at: 2026-09-26T00:18:21Z
updated_at: 2026-09-26T00:18:21Z
plan_revision: 1
current_step: 6
total_steps: 6
supersedes_spec_components: []
new_spec_components:
  - docs/specs/modules/diff-view.md
  - docs/specs/00-overview.md
  - specs/auto-edit/README.md
touched_goals:
  - 战略 §2.3 M3 验收面「文件 diff 完本体：并排+内联两视图」后半
---

# PLAN-015: M3-03 文件 diff 内联（unified）视图

## 0. 变更摘要

文件 diff 视图增**内联（unified）模式**：同一份 envelope 数据在并排
视图之外提供第二种渲染形态——配对行（del|add 同行）展开为「先红后绿」
两行，上下文/单侧行单行渲染，行号双列继承（缺席侧空串）。切换=纯
front 状态投影（**零重比、零 back 调用、envelope 零改动**——PLAN-011
替换缝设计的第一笔红利兑现），hunk 导航（F7/Shift+F7）在内联行序列上
同语义工作。本件=战略 §2.3「并排+内联两视图」的收尾，也是 M3 验收面
中**唯一不被上游内核引擎门控**的剩余项——M3 其余主面（histogram 算法/
100MB ≤2s 预算/差异侧直接编辑+即时重比/与编辑缓冲区比较）全数等待
上游供料包（`docs/upstream/2026-09-diff-engine-supply.md` 五件）承接，
截至本件立项 **auto-lang 无承接立项**（§10 Q-1 在案）。

## 1. 目标

- **G-1 内联渲染**：envelope rows → 内联显示行（irows）投影——
  pair 行两行展开（del 行先、add 行后，统一 diff 惯例），del-only/
  add-only/ctx 行单行；三段标记（pre/mid/post，mid 着重）与行号双列
  字符串（缺席侧空串）按源侧继承；着色=del 红/add 绿/ctx 无底色
  （并排态同款色系）。
- **G-2 模式切换纯态**：action `diff.view-mode` + diff 工具栏按钮
  （并排↔内联）；切换仅重建 front 投影（diff_rows 信封行与 envelope
  派生计数零变化——可断言零重比）；模式跨 DiffCompute 保持、DiffClose
  复位 side。
- **G-3 导航适配**：DiffNext/DiffPrev/DiffScrollToHunk 在内联态扫
  irows（导航归属整数 lo/ro 随投影携带），24px 行高偏移公式不变；
  空 hunk 零动作守卫语义不变。
- **G-4 矩阵与测量**：smoke_t234_diff.py 扩内联断言组——六形态
  golden 推导 irows 期望（python 侧推导器与 011 参考实现同源）、
  切换零重比、内联态 F7 序列/回绕、渲染 cap（irows 独立 600 行截断
  +双注记）；判绿下限随升。
- **G-5 规范与轨**：diff-view.md 追加内联节（SD-01）+ overview M3
  第三件注记（SD-02）+ README 矩阵行（SD-03）；vue 轨
  `scripts/regen_vue.py --build` green；执行期新勘定的上游 want 如有
  → upstream 供料档追加节（预期零——纯 front 件）。

### 非目标

- back/envelope 任何改动（`diff_files` 端点与 envelope 契约零变更——
  替换缝声明的兑现面；back-api.md 无需 delta）。
- 差异侧直接编辑+编辑后即时重比（引擎 `diff_snapshots` + rope 子树
  哈希门控，供料 §1/§2——011 非目标裁定延续）；与编辑中缓冲区比较
  （同门控）。
- 语法高亮联动（M4 tree-sitter 门控）；3-way merge/双向同步向导
  （§9-Q5 开放，M3 收口时裁定）；十六进制比对（非目标）。
- 上下文行数控件（ctx 1/3/8 调整——战略验收面未列，envelope ctx
  参数在册可零改动支持，候选后续件，§10 Q-2）。
- 目录 diff 面任何改动（内联仅文件 diff 态；dir_mode 内卫与 T16 组
  断言零扰动）。
- auto-lang 侧任何改动（上游 want 走 docs/upstream 登记）。

## 2. 架构方案

分层落点（2026-09-26 实勘，auto-edit main@ed8c107）：

| 面 | 现状 | 本期形态 | 依据 |
|---|---|---|---|
| store 投影 | diff_rows=信封行渲染就绪投影（cap 600，editor_store.at:209-231） | **新增 irows 纯派生投影**：`diff_vmode`（"side"/"inline"，跨 compute 保持、close 复位）+ `diff_irows/diff_irows_count/diff_irows_truncated`（显示行：`d_lo/d_ro` 行号串继承缺席空串 + `pre/mid/post` 三段按源侧继承 + `lo/ro` 整数导航归属 + `ix_ctx/ix_del/ix_add` 三形状旗标）+ `diff_dbg_ictx/idel/iadd` 形状计数（矩阵断言面）；派生源=capped diff_rows（600 信封行），irows 再独立 cap 600 显示行（pair 展开最坏 ×2——双 cap 各自注记，hunks 导航仍信封全量语义=截断尾 hunk 零动作，与并排态一致） | PLAN-012 过滤投影先例（front 纯态零重比）；「store 预变换、视图零条件格式化」011 惯例 |
| 切换链 | 无 | handler `DiffToggleView`：vmode 翻转 + irows 重建/清空；**零 back 调用**（envelope 派生计数 diff_dbg_pair/del/add/ctx 与 diff_hunk_count 断言不变=零重比证明面）；DiffCompute 尾段挂钩（vmode=inline 时重算后重建 irows）；DiffClose 复位 vmode=side | 纯 front 态切换（AC-02） |
| 视图 | 四独立 for 循环 ×单 bool 旗标 if（app.at:518-573——同循环多兄弟 if 实勘坑 T-03 规避形态） | vmode 条件双视图：内联态=**三独立 for 循环**（ix_del[含 pair 展开del 行]/ix_add[含 pair 展开 add 行]/ix_ctx——pdel 与 del-only 渲染同构、padd 与 add-only 同构，故三循环足）；行布局=行号双列（12px ×2，缺席空串零宽）+单文本列三段（mid 着重色）；行高 h-6=24px 与并排态同（导航公式共用）；工具栏增模式切换钮（bool 旗标双钮形态） | 011 四循环同款结构首位规避；三段=分离 text 节点断言口径（T-03 教训）维持 |
| action | diff 组四命令（app.at:71-77） | 增 `diff.view-mode`（handler .DiffToggleView，title「切换并排/内联」，enabled_if diff_open 且 !dir_mode；v1 无快捷键）；工具菜单不加静态项（diff 态内按钮即达——menubar 面收敛） | actions DSL 三源单一事实 |
| 导航 | DiffScrollToHunk 扫 diff_rows 首条归属行（editor_store.at:1588-1632，24px float 累加） | vmode 条件扫 irows（归属判定 lo-1∈[a1,a2) ∨ ro-1∈[b1,b2) 同式——irows 携带 lo/ro 整数）；空 hunk/截断尾零动作守卫不变 | G-3 |
| 矩阵 | smoke_t234_diff.py（T15 组：env 旁路自开+golden 对照+导航+错误形） | 扩四断言族：①六形态 irows 推导对照（golden rows→python 推导器→dbg 计数+首末行快照采样）②切换零重比（envelope 派生面不变）③内联态 F7 序列/回绕（hunk_pos 串）④cap 生成式超限形态（tmp 树，fixtures 保 pristine——008 先例） | 判绿下限随升（T-04 定数） |
| vue 轨 | 011/012 基础件全证（row/col/text/button/scroll-pane/for/if 旗标） | 预期 build-green（`scripts/regen_vue.py --build`，README.md:64）；新面无新组件类 | 跨轨禁补件裁定 |
| 上游 | 引擎供料包五件无承接（auto-lang master@729dd4f2f 实勘：活跃计划仅 242 追踪器，701/702 已归档） | **本件零依赖零推动**；执行期勘定新 want 如有 → upstream §18 追加（预期零） | 669 模式（承接时序=用户另驱，§10 Q-1） |

**设计要点如实成文**：irows 派生自 **capped** diff_rows（非信封全量
rows）——双 cap 语义（信封级 600 行注记+内联级 600 行注记并列显示），
超出域不可见属渲染预算口径，hunk 导航对截断尾 hunk 零动作（并排态
现行语义一致，非回归）。

## 3. 技术栈

.at DSL（store handler+模板 for/if 单旗标形态）/ desktop_mcp.py 矩阵
驱动（env 旁路 AUTO_DIFF_A/B 自开臂）/ fixtures golden 对照+python
推导器 / probe_diff.py 探针族扩展（vm merged 最小 app 载具先例）/
vue ts_adapter 生成轨（regen+build）。

## 4. 需求分析与背景调查

**授权记录**：用户 2026-09-26 会话指令「下一阶段是 M3，请规划第一个
计划」——授权=**起草本件**；执行/work 待用户另行启动。范围=auto-edit
仓（specs/auto-edit 源+tests+docs+README）；auto-lang 零改动（上游
want 走 docs/upstream 登记）。无预算/自动续跑授权。

**地形注意**：主检出两枚 stylekit 删除 WIP（specs/stylekit/pac.at、
specs/stylekit/src/front/styles.at——并行会话遗留待路由，PLAN-008 起
在案）——本件不触其路径；merge 期保全回贴先例（012/013/014 同款）。

**来源与版本**：

- auto-edit main@ed8c107（PLAN-014 merge 收据后净态）；auto-lang
  master@729dd4f2f（**diff 引擎供料包无承接立项**——docs/plans 活跃
  仅 242-a2r-feature-gap-tracker，归档最新 702；全树无 diff 模块实勘
  结论维持，供料档 2026-09-23 落档）。
- 规范基：docs/specs/modules/diff-view.md（PLAN-011 交付+012 目录节
  追加后现行版）——envelope 契约/替换缝声明/上限门/front 状态面/
  导航契约/视图断言口径。
- 代码锚（ed8c107）：editor_store.at:209-231（diff 状态面字段）、
  :326-328（diff handler 枚举）、:1399-1492（DiffCompute 消费收口）、
  :1588-1632（DiffScrollToHunk）；app.at:71-77（diff action 注册组）、
  :485-579（diff 视图四循环+工具栏）；tests/smoke_t234_diff.py
  （T15 组）；tests/probe_diff.py（26/0 决策探针+probe_diff_app 载具）；
  tests/fixtures/diff/ 六形态 golden（add_only/del_only/modify/
  big_reorder/…）。
- README.md:64（vue 轨命令）；矩阵判绿基线=完成态 117 检查、下限
  ≥115/0（PLAN-014 注记口径：T17 交互簇上游 UI 卡死回归 blocked 集
  不计判绿）。

**需求定位侧写（M3 面进度账）**：M3-01 文件 diff v1（011）、M3-02
目录 diff v1（012）已落；战略 §2.3 剩余项中——内联视图（本件，无
门控）、语法高亮联动（M4）、差异侧直接编辑+即时重比（引擎）、
histogram/分块并行/100MB ≤2s（引擎）、3-way/双向同步（Q5）。即
**本件完成后，M3 本仓面在引擎落地前再无无阻塞验收项**——后续 M3 件
的排期实质由上游承接时序决定（§10 Q-1）。

## 5. 详细设计

### 5.1 irows 投影契约（store 侧纯派生）

| 源行（diff_rows） | 内联展开 | d_lo/d_ro | pre/mid/post | lo/ro（导航） |
|---|---|---|---|---|
| sx_pair（lk=del+rk=add） | **两行**：del 行先、add 行后 | del 行=d_lo/""；add 行=""/d_ro | del 行取 l*；add 行取 r* | del 行=lo/0；add 行=0/ro |
| sx_ctx | 一行 | d_lo/d_ro（双在） | lpre/lmid/lpost（ctx 行 lpre=全文本 mid 空） | lo/ro 双在 |
| sx_del（单侧删） | 一行 | d_lo/"" | l* | lo/0 |
| sx_add（单侧增） | 一行 | ""/d_ro | r* | 0/ro |

- 字段族：`d_lo/d_ro str`（行号串缺席空串——视图零条件格式化）+
  `pre/mid/post str`（三段）+ `lo/ro int`（导航归属）+
  `ix_ctx/ix_del/ix_add bool`（三形状旗标——pdel/padd 与 del/add
  同构合形，形状语义差异由 dbg 计数与 golden 推导器对照面覆盖）。
- cap：irows >600 显示行截断，`diff_irows_truncated=true`（独立注记，
  与信封级 `diff_rows_truncated` 并列）；counts 与显示域同域（012
  counts/entries 同域先例）。
- 重建时机：DiffToggleView（切换即建/清）；DiffCompute 尾段（vmode=
  inline 时重算后重建）；DiffClose（vmode 复位 side+irows 清空）。

### 5.2 视图与切换

- 内联态行布局：`row { text d_lo (w-12) | text d_ro (w-12) | text
  pre | text mid (着重) | text post (flex-1) }`——行号列着色随形状
  （del 红/add 绿/ctx 灰），文本列底色随形状（del bg-red-100/add
  bg-emerald-100/ctx 无底色），与并排态色系一致。
- 渲染=**三独立 for 循环×单 bool 旗标 if**（结构首位规避，011 T-03
  实勘形态沿用）；内联/并排双视图=vmode 条件（`if .store.diff_vmode_
  inline` 双分支包裹——dir_mode 内卫不变）。
- 工具栏切换钮：bool 旗标双钮形态（inline 态显「并排」、side 态显
  「内联」）；action `diff.view-mode` 注册入 diff 组（enabled_if：
  diff_open 且 !dir_mode）。

### 5.3 导航适配

DiffScrollToHunk 增 vmode 条件：inline 态扫 `diff_irows`（归属判定
同式：lo-1∈[a1,a2) ∨ ro-1∈[b1,b2)，irows 携带 lo/ro 整数）；命中
target×24.0 float 累加偏移（行高 24px=并排态 T-00③ 定标共用）；未
命中（空 hunk/截断尾）零动作守卫不变。

### 5.4 规范增量

| delta_id | add/modify/retire | docs/specs/... target | before/after rule | rationale | acceptance IDs |
|---|---|---|---|---|---|
| SD-01 | add | docs/specs/modules/diff-view.md | before：无内联面 / after：追加「内联视图（M3-03）」节——irows 投影契约（§5.1 表全量）+切换零重比语义+双 cap 注记+导航 irows 域+矩阵断言面（dbg_i* 计数+推导器口径） | 完全体「并排+内联两视图」后半落账；替换缝红利首兑现注记（envelope/back-api 零改动） | AC-01..04 |
| SD-02 | add | docs/specs/00-overview.md | before：M3 面止于第二件注记 / after：M3 第三件注记（内联视图=引擎等待期无阻塞收尾；M3 本仓面引擎前清单清零+上游承接悬案指 §10） | M3 进度账单源 | AC-05 |
| SD-03 | modify | specs/auto-edit/README.md | before：T15 组=并排断言（014 后完成态 120/≥112） / after：T15 组 15.11–15.15 五子组（矩阵承载面）+完成态 125+判绿 ≥117/0（修复轮实录） | 运行矩阵单源 | AC-04/05 |

（back-api.md 零改动=替换缝兑现，非 delta；docs/upstream 零预期增量，
执行期勘定如有走 §18 追加。）

## 6. 测试设计

- **probe 扩展（决策门，不入矩阵计数）**：probe_diff.py 增投影断言
  轮——irows 序列/三段继承/双 cap 与 golden 推导器逐字段对照（载具
  probe_diff_app 现役同款）。
- **矩阵 smoke_t234 扩四断言族**：①六形态 irows 对照（dbg 计数+首末
  行快照采样——三段=分离 text 节点口径）②切换零重比（diff_dbg_pair/
  del/add/ctx 与 diff_hunk_count 切换前后不变）③内联态 F7 序列/回绕
  （diff_hunk_pos 串——scroll 读回投影生态观察件 §17 在案，断言面与
  011 同级）④cap 生成式超限形态（tmp 生成树，>600 irows 截断注记）。
- **vue 轨**：regen+build exit 0（生成物内联视图组件在档复核）。
- **人工视觉门**：着色/间距（a11y 快照不携带 style 行——T-15 口径，
  截图/人工面）。

## 7. 验收标准

- **AC-01 内联渲染语义正确**：六形态 fixture 下 irows 计数/形状分布/
  首末行采样=golden 推导期望。验证：矩阵断言族①全绿。
- **AC-02 切换纯态零重比**：DiffToggleView 后 envelope 派生面
  （diff_dbg_*、diff_hunk_count、diff_adds/dels）不变，且 back 无新
  调用（矩阵旁路链 console 面零新 compute 记录）。验证：断言族②。
- **AC-03 内联态 hunk 导航**：F7/Shift+F7 推进/回绕，diff_hunk_pos
  序列与并排态同源（hunk 集不变）；scroll 目标行=内联序列首条归属
  行（store 侧 target 推导与 011 同级断言口径）。验证：断言族③。
- **AC-04 双 cap 语义**：>600 内联显示行截断+`渲染截断（600）`注记
  （内联级）与信封级注记并列不互斥；hunks 导航全量语义保持。验证：
  断言族④（生成式 tmp fixture）。
- **AC-05 回归面零扰动**：并排态既有 T15 断言、目录 diff T16 组、
  其余检查族不回退；dir_mode 内卫行为不变（内联仅文件 diff 态）。
  验证：全矩阵跑绿（PLAN-014 判绿口径：已知 blocked 集注记维持）。
- **AC-06 规范与轨落账**：SD-01/02/03 落档；vue gen+build exit 0；
  README 完成态+判绿下限更新。验证：文件在档 grep 锚+构建 exit 0+
  矩阵完成态数字一致。

## 8. 执行步骤

| # | 任务 | 依赖 | 落点（实勘锚） | 产出/意图 | AC | 验证（命令/预期） |
|---|---|---|---|---|---|---|
| 1 | [x] T-01 store 投影+切换链：irows 字段族+DiffToggleView+DiffCompute 尾挂钩+DiffClose 复位+dbg_i* 计数 [✅ 已完成 2026-09-26，editor_store.at 六处外科+App 薄委托补位（.DiffToggleView 委托=链接错误勘定位——actions 解析 App.on 非 store）] | — | specs/auto-edit/src/front/editor_store.at（:209-231 状态面、:326-328 枚举、:1399-1492 compute、DiffClose 段） | 投影契约 §5.1 全量实现 | AC-01/02 | probe_diff.py 扩轮全绿（58/0） |
| 2 | [x] T-02 内联视图渲染+切换钮+action 注册 [✅ 已完成 2026-09-26，三独立 for 循环+vmode 互斥包裹（并排四循环零改动）+bool 双钮+diff.view-mode] | T-01 | specs/auto-edit/src/front/app.at（:71-77 action 组、:485-579 视图段） | 三独立 for 循环+vmode 双视图+工具栏双钮 | AC-01 | 烟测快照：钮文翻转/双注记/形状分支渲染 |
| 3 | [x] T-03 导航适配：DiffScrollToHunk vmode 条件扫 irows [✅ 已完成 2026-09-26，src/srcn 条件扫描源——命中式与 24px 偏移公式共用] | T-01 | editor_store.at:1588-1632 | 内联态导航同语义 | AC-03 | 烟测 F7 序列/回绕（hunk_pos 串） |
| 4 | [x] T-04 矩阵扩：断言族①..④+cap 生成式 fixture+完成态定数 [✅ 已完成 2026-09-26：smoke_t234 18→37 检查 ALL PASS（P15 四断言族+关闭复位+重建幂等）；cap 用 **big_reorder 现役 fixture** 替代生成式 tmp 树（同一覆盖意图——信封 600+内联 600 双截断实景，零新 fixture）；T16 下钻面回归 ALL PASS；commit 4c33da4。**环境双坑勘定**：①PATH 二进制 g86b56884b=并行分支构建缺 701 native（shell_add_recent 链接炸）→重建 auto-lang master v2156-g1d597e3f4；②组依赖惯例=`.wt/edit-015/auto-lang`@3e3e1e297 钉版 worktree（014 Q-1b——pac `../../../` 组目录下解析为组兄弟，主检出 junction 断链坑复认）] | T-01..03 | specs/auto-edit/tests/smoke_t234_diff.py（+probe_diff.py derive_inline 导入） | 判绿下限随升 | AC-01..04 | 矩阵跑绿（README 运行口径；新下限数字回填 T-05） |【✅ 修复完成 2026-09-26（commit 762fbf6）：desktop_mcp.py T15 组增 15.11–15.15 五子组全绿——修复轮矩阵 120 passed/5 failed（失败=已知集 T13.6+T17 簇全中、零新失败）；15.12 首轮 FAIL=检查自身缺陷（console 滚动尾窗前缀差量不可靠）改标记计数法后绿；完成态 125=120+5、判绿 ≥117/0】
| 5 | [x] T-05 规范三件：SD-01 diff-view.md 内联节+SD-02 overview 注记+SD-03 README 行 [✅ 已完成 2026-09-26，commit 1490f45；README 口径：T15 组 18→37、完成态 139、判绿 ≥131/0（blocked 集承 014：T12.6+T17 簇）；overview 增「引擎前清单清零」注记+§10 Q-1 指引] | T-04 | docs/specs/modules/diff-view.md、docs/specs/00-overview.md、specs/auto-edit/README.md | 规范增量落账 | AC-05/06 | grep 四锚在档（011 T-06 同款）；数字与矩阵完成态一致 |【✅ 修复完成 2026-09-26：README/overview 数字回填真值（完成态 125=120+5、判绿 ≥117/0、修复轮实录+smoke/probe 定位注记）——commit 762fbf6】
| 6 | [x] T-06 vue 轨复验+收尾：regen+build；上游 want 若有→upstream §18；grep 锚终检 [✅ 已完成 2026-09-26：regen_vue.py --build 双 exit 0（strict gen+vue-tsc+vite 2140 modules）；生成物消费实证（App.vue 4 处/useEditorStore 17 处 diff_irows 引用）；grep 锚全中（SD-01×5/SD-02×2/SD-03×3/源锚 4+6）；上游 want=零增量（环境双坑=已知坑位再应验，已录 README 口径段，非 §18 面）] | T-05 | scripts/regen_vue.py（README.md:64）、docs/upstream/2026-09-m1-supply.md（§18 如需） | 跨轨 green+登记闭环 | AC-05/06 | `python scripts/regen_vue.py --build` exit 0；grep 锚全中 |【✅ 修复轮终检 2026-09-26：vue regen+build 双 exit 0 重跑（F-4 注释改后再证）；grep 锚全中（SD-01×1/SD-02×2/SD-03×3/源锚 4+6）】

## 9. 复审记录

- 2026-09-26 起草 handoff：`stage: new`，PLAN-015，plan_revision 1。
  `outcome: pass`（起草完备：任务覆盖全部 AC 与 SD；路径/符号经仓库
  实勘锚定；授权=起草，执行待用户启动）。`next: work`。
- 2026-09-26 执行 handoff：`stage: work | PLAN-015 | plan_revision 1 |
  outcome: pass | code_commit: worktree plan-015-dev@1490f45（base
  ed8c107；T-01..T-04=4c33da4，T-05=1490f45） | task_ids: T-01..T-06
  全落 | evidence: probe_diff.py 58/0（⑥推导器六形态 23 项新增——
  行数恒等式/计数恒等式/三段继承+行号全行核/pair 邻接/双 cap 模拟）；
  smoke_t234 37/37 ALL PASS（P15 四断言族 19 项新增——推导器对照/
  零重比八字段/钮文翻转/内联导航回绕/双 cap big_reorder 实景+双注记
  快照/关闭复位/重建幂等）；smoke_t345 下钻面回归 ALL PASS；vue 轨
  regen+build 双 exit 0（生成物 App.vue/useEditorStore 消费实证）；
  grep 锚全中（SD-01/02/03+源锚）。**环境双坑勘定**（README 口径段
  在档）：①PATH 二进制 g86b56884b=并行分支构建不含 PLAN-701 native
  （shell_add_recent 链接炸）→auto-lang master 重建 v2156-g1d597e3f4；
  ②组依赖惯例=.wt/edit-015/auto-lang@3e3e1e297 钉版 worktree（014
  Q-1b——pac `../../../` 相对路径在组目录下解析为组兄弟）。scoped
  验证口径：全矩阵跑绿=复审/预落门（AC-05 终判归 review）；本件新增
  检查无 blocked 项。| blockers: 无（§10 Q-1 上游承接悬案维持——
  非本件面）| next: review`。status=execution_done。
- 2026-09-26 复审 handoff：`stage: review | PLAN-015 | plan_revision 1
  | outcome: **needs_fix** | reviewed_commit: 1490f45 | base_commit:
  ed8c107 | dependency_revisions: .wt/edit-015/auto-lang@3e3e1e297（组
  钉版）；工具链 auto v2156-g1d597e3f4（复审期复核二进制未漂移/主检出
  未前移/无并行构建） | spec_inputs: docs/specs/modules/diff-view.md@
  1490f45 追加节+00-overview.md@1490f45 注记+specs/auto-edit/README.md@
  1490f45 口径段 | acceptance_results: AC-01 pass / AC-02 **partial**
  / AC-03 pass / AC-04 **partial** / AC-05 pass / AC-06 **partial** |
  findings: **F-1（P1）**P15 断言族未进矩阵主跑器——矩阵=desktop_mcp.py
  自含 T15 组（15.1–15.10+15.3b=11 检查），smoke_t234_diff.py 系开发
  期烟测件不进矩阵计数；README/overview「完成态 139（120+19）/判绿
  ≥131/0」与实跑矩阵（**完成态 120，第三跑 115 passed/5 failed=已知
  blocked 集注记后计零失败，≥112 达标**）不符——数字失据，AC-04 矩阵
  承载面/AC-06 SD-02/03 数字连带。**F-2（P2）**「跨 DiffCompute 保持」
  生命周期（SD-01）零行为覆盖——compute 尾挂钩未被任何测试触发（env
  旁路每进程一次；唯一 MCP 可驱动重算=目录下钻路径，T16.4 机械在档
  可搭）。**F-3（P2）**AC-02 零重比证明弱：切换前后 envelope 派生字段
  等值不能排除同文件重比（重比后字段同值）——须加 console 无新
  compute 行断言。**F-4（P3 非阻断）**枚举注释「DiffBuild/Irows」断行
  排版微瑕。| evidence: 复审独立复现（非采信执行期汇报）——①probe_
  diff.py 重跑 **58/0**；②smoke_t234_diff.py 重跑 **ALL PASS**（37）；
  ③全矩阵 desktop_mcp.py 三跑（前两跑 F-RV6 族早崩无 RESULT——死亡点
  T6/T3 逐跑异均在未触碰组，环境面非本件回归；静默环境第三跑全程
  `RESULT: 115 passed, 5 failed`，失败项=T17.2/17.3/17.4/17.8[上游 UI
  卡死回归 blocked 簇，014 口径维持——v2156 上仍未复绿]+T13.6[已知
  轮换 flake]，计 **115/0 ≥112 判绿达标**，T15/T16/T18 全绿=本件零
  回归实证；完成态 120 实测=F-1 实证）；④vue 双 exit 0 复用执行期
  证据（源码自 1490f45 零变化+工具链未漂移，重跑假设未变）；⑤探针
  报告在仓（probe_diff_report.txt：58 PASS+⑥族 23 项+RESULT 行）。
  | next: work（修复=F-1 承载面落位：desktop_mcp.py T15 组增 P15 子组
  15.11 投影对照/15.12 零重比+console 断言[F-3]/15.13 内联导航/
  15.14 双 cap big_reorder/15.15 内联态重算-下钻路径[F-2]→全矩阵
  定新完成态与下限→README/overview 数字回填[T-05 重开]+F-4 顺手修；
  行为面代码（store/视图/导航）零改——三套独立复现已证）。
  status=executing（T-04/T-05/T-06 重开；T-01/02/03 证据保全）。
- 2026-09-26 修复 handoff（needs_fix 回工轮）：`stage: work | PLAN-015 |
  plan_revision 1（契约未变——修复=对既定 AC/SD 的补足）| outcome:
  pass | code_commit: worktree plan-015-dev@762fbf6（+4c33da4/1490f45）|
  task_ids: T-04/T-05/T-06 修复重落 | evidence: ①desktop_mcp.py T15 组增
  15.11–15.15 五子组（F-1 承载面）——修复轮全矩阵 `RESULT: 120 passed,
  5 failed`，失败集=已知 blocked 集（T13.6+T17.2/3/4/8）逐项全中零新
  失败，P15 五子组全绿；②15.12 首轮 FAIL=新检查自身缺陷（console=
  滚动尾窗，前缀差量 fallback 误吞全量含 compute 行）→改标记计数法
  （compute 行计数不增+view 行计数 +1，对滚动免疫）后绿——检查器设计
  教训在档；③15.15=F-2 生命周期覆盖（tmp 双改文件下钻链：mod1 切内联
  →返回→mod2 再下钻，vmode 保持 inline+irows 按 probe 参考实现链重建
  期望全中）；④F-4 枚举注释断行修（纯注释——vue regen+build 双 exit 0
  重跑再证）；⑤README/overview 数字回填真值：完成态 125=120+5、判绿
  ≥117/0（014 余量口径承袭）。| blockers: 无 | next: review（再复审）。
- 2026-09-26 再复审 handoff（修复轮验证）：`stage: review | PLAN-015 |
  plan_revision 1 | outcome: **pass** | reviewed_commit: 762fbf6 |
  base_commit: ed8c107 | dependency_revisions: .wt/edit-015/auto-lang@
  3e3e1e297；工具链 v2156-g1d597e3f4 | spec_inputs: diff-view.md 内联节/
  00-overview M3 第三件注记/README PLAN-015 口径段（均@762fbf6）|
  acceptance_results: AC-01..AC-06 全 pass | findings: 复审 F-1 ✓销账
  （矩阵承载面落位 desktop_mcp.py T15 组 15.11–15.15；README/overview
  数字=真值 125/≥117）；F-2 ✓销账（15.15 下钻重算生命周期覆盖 PASS）；
  F-3 ✓销账（15.12 console 标记计数硬证明 PASS）；F-4 ✓销账（注释修+
  vue 复跑双 exit 0）。新发现：无。| evidence: 修复轮全矩阵（代码=
  提交态逐字节一致——跑后仅 README/overview 文档改动）：`RESULT: 120
  passed, 5 failed`，失败集=已知 blocked 集（T13.6+T17.2/3/4/8）逐项
  全中零新失败；P15 五子组全绿（含 15.12 首轮检查器缺陷返工实录——
  console 滚动尾窗教训入档 README 口径段）；probe 58/0 与 smoke 37/37
  复用上轮复审独立复现（py 文件零变化、.at 仅注释改后 vue 复跑绿——
  重跑假设未变，复用理由明示）；grep 锚全中。| next: merge`。
  status=reviewed。

## 10. 待澄清事项

- **Q-1 上游引擎承接时序（M3 关键路径，用户裁定）**：diff 引擎供料包
  （docs/upstream/2026-09-diff-engine-supply.md 五件——§2 rope 子树
  哈希最优先、可独立先行）2026-09-23 落档至今，auto-lang 无承接立项
  （master@729dd4f2f 实勘）。M3 主线（histogram/100MB ≤2s/差异侧
  编辑重比/编辑缓冲区比较）全数门控于此。**本件不阻塞、不推动**；
  承接与排期=用户在 auto-lang 侧另驱计划（669 模式）。建议：本件
  执行期内承接立项，使 M3 主线不因视图尾件空转。
- **Q-2 ctx 行数控件（上下文 1/3/8）**：战略验收面未列；envelope
  ctx 参数在册，纳入=DiffCompute 带参重比（非纯态）+控件面。默认
  非本件（视图件最小面）；用户可裁定提前纳入（约 +1 任务量）。
