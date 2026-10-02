# 041-auto-edit — AutoLang 文本编辑器（多文件组件化）

> 本项目（auto-edit 仓）拷贝自 auto-lang `examples/ui/041-auto-edit`，源
> commit 见 [`specs/PROVENANCE.md`](../PROVENANCE.md)；下方 Plan 补记为
> 源仓历史，保留为沿革记录。

一个"严肃应用"轨道的 AutoUI 示例：多 tab 代码编辑器（原生 CodeMirror6 内核），
带菜单栏/工具栏/全局快捷键三源动作触发、右键菜单、脏 tab 关闭确认、Console
面板、撤销重做与文件打开/保存。Plans 413/414/418/420/422/428 持续迭代，
Plan 449 完成组件化重构（单文件 486 行 → 五文件工程）。

## Concepts

- **store 承载全部状态与业务逻辑（038/013 形态）** —— `editor_store.at` 持有
  tabs/光标/Console/弹层等全部状态；App 的 `on` 薄委托 `store.Xxx()`，事件名
  与 `auto-edit.at` 的 handler 映射一一对应（Action=声明层，Event=执行层）。
  重复逻辑收口为两个内部 helper msg：`RemoveAt`（关闭 tab 的 remove+索引修补+
  激活重算，原先 CloseTab/ConfirmClose 各持一份）、`SyncCursor`（line/col/sel
  三元组读回，原先 5 处重复）。store handler 间经 `store.Xxx()` 互调（038
  先例）。派生标量仍由 handler 就地重算——VM view 不能调函数（Plan 402
  约束），模板只读字段。**`tabs[i].src` 数据语义（PLAN-005 收敛）**：仅作
  初值/外部重置（last_external 相等即 no-op，typed 输入不会被 stale 值
  踩掉）；编辑态**不回写**——cut/paste/undo/redo/ctx-cut 后的全文回读已删
  （违例残留），编辑器全文只在两个 save 位读出（ActSave/QuitSaveClose；
  过渡形态，上游 delta/分块读供料后收口）。矩阵正文断言走 save 路径 E2E
  （见 Tests 节注）。
- **013 式组件（无 props + 直调 store）** —— `StatusBar`/`ConsolePanel`/
  `EditorCtxMenu` 不带 props：标量/锚态经 `use editor_store` 直读 `.store.*`，
  自有 msg，handler 直调 `store.Xxx()`（013-todo 的 TodoList 形态）。
- **vm 组件边界（Plan 449 实测定性，重构设计的硬约束）**：
  1. **回调 props（`on_xxx: msg`）会使组件整体退化为空 fallback**——
     015-notes 的 NavTree/EditorPanel 在 vm 模式下即如此（015 是 vue 示例）。
  2. **组件子树对 MCP 快照不可见**（渲染正常、handler 派发正常，但
     `autoui_snapshot` 只走根模板）——测试矩阵靠快照定位的交互不能进组件。
  3. **view fn 片段的参数化条件（onclick 实参/条件样式/if 分支）在 vm
     视图构建中不求值**——片段去重 tab 条不可行（015 的 NoteItem 片段
     先例只在 vue 模式验证过）。
  因此 tab 条（x 按钮形状定位、"+" 的 `onclick: .ActOpen`）、确认弹层
  （"直接关闭" 文本定位）、code_editor 绑定与空态文本留在 App 根视图。
- **vm 字节码 bug 规避**：`code_editor_set_text` 编译进 store handler 会产出
  坏字节码（`virt_memory.rs read_i32` 越界 panic，Plan 449 实测；widget
  handler 中正常）——该调用留在 App 根 handler（`.ActNew` 内，见 app.at）。
- **动作三源绑定（Plan 418/423/451）** —— action 注册表 + menubar/toolbar
  结构以 `widget App` 内的 **`actions {}` 声明块** 表达（Plan 451 起 DSL 化，
  原项目根的 auto-edit.at 外挂配置退役；外挂文件形态仍兼容——DSL 优先）。
  vm 渲染器经 `action_config()` 消费：① 键盘回退层（DSL onkeydown 之下）；
  ② `menubar{}`/`toolbar{}` 占位的配置合成渲染；③ MCP 自动化同源派发。
  `handler: .ActXxx` 在**解析期校验**命中本 widget 的 `on{}` 事件；
  `enabled_if`/`checked_if` 为条件表达式字符串，对合并根 state 求值
  （`.tab_count` 等，无前缀）。热重载：改 app.at 后经 MCP 的
  `action_config_reload` 工具（或渲染器 mtime 轮询）重读源文件重新提取。
- **front/back 拆分（PLAN-003）** —— 全部文件系统面收口 `src/back/`
  （`api.at` 契约 + `fsys.at` Auto 实现本体），front 经
  `use back.api: ws_root, tree, read_text, write_text, exists, env_str`
  裸函数直调（013-todo/015-notes 形态）：vm merged = 进程内 CALL（无
  HTTP）；vm split / vue 轨 = HTTP（ts_adapter 生成 client，vite 代理
  `/api` → AUTO_HTTP_PORT）。front 零 `fs.*`/`File.*`/`Env.get` 内建
  （vue 轨 ts_adapter 将 fs/File 拦为 `__vmOnly` 抛错桩——拆 back 的
  动机）；路径拼接走本地字符串（`ws_dir + "/" + id`，`fs.join` 亦在
  拦截面）。**pac 不写 `api:` 字段**——服务引擎留运行期 `--server`
  切换，默认 AutoVM + merged 直调（`api:"rust"` 会杀 merged）。
- **vue 轨（PLAN-003 双轨化）** —— pac `render: ["vm","vue"]` 单声明 +
  双命令分工（jade-edit PLAN-081 R-1 裁定 A' 同款）：vm 轨
  `auto run -r vm`，vue 轨 `python scripts/regen_vue.py --build`（strict
  裸生成——七类补件链 2026-09-21 退役，上游 auto-lang PLAN-671 全周期
  delivered 后生成器自完备，含 menubar 族 schema 吸收故 `--lenient`
  一并摘除；⚠ 禁止裸 `auto build`：Multi 下选 vm 项走 C/ninja 转译
  路径）。**vue 生成器已支持 actions 消费**
  （快捷键经 keydown 回退层、menubar/toolbar 占位合成——PLAN-070 T-05
  去门化；旧「尚未接入」陈述作废）。vue 首版 = 构建绿 + 生成即展示；
  运行期限制（vm 宿主内建无 vue 运行时）：`dialog_open/dialog_save`
  文件对话框、`console_*` 面板数据、`code_editor_*` 读回族、
  `Env.get`/`Process.exit`——生成器自备 natives 声明层（函数+对象形态
  索引签名 + `__vmOnly`/Proxy 抛错桩——PLAN-671）使构建绿，运行期
  缺口登记于此，深度双轨归后续计划（jade-edit 换基承接同型深水区）。

## Source

| 文件 | 职责 |
|---|---|
| `src/back/api.at` | 后端契约（PLAN-003）：六 `#[api]` fn（ws_root/tree/read_text/write_text/exists/env_str，路由前缀 /api，GET query/POST body）+ 边界语义注记 |
| `src/back/fsys.at` | 后端实现本体：`fs.*`/`File.*`/`Env.get` 收口（ws 根解析 + 四 IO + env 读）；模块名 fsys 避与内建 fs 对象同名，且 split 扁平化只吃整模块 `use` |
| `scripts/regen_vue.py` | vue 轨一键链：strict 裸生成 + pnpm install/build（七类补件 2026-09-21 退役——上游 PLAN-671 清偿，工具链须 ≥1652/含 671） |
| `src/front/app.at` 的 `actions {}` 块 | 动作注册表（14 个 action）+ menubar/toolbar 结构（Plan 451 DSL 化；原根目录 auto-edit.at 已删除） |
| `src/front/app.at` | 根 widget `App`（213 行）：actions 声明块 + view 组合 + on 薄委托；测试定位锚交互（tab 条/确认弹层/编辑区/空态）留根 |
| `src/front/editor_store.at` | `store EditorStore`（342 行）：全部状态 + 业务逻辑 + RemoveAt/SyncCursor 收口；数据面经 `use back.api` 直调（PLAN-003） |
| `src/front/status_bar.at` | `StatusBar` 组件（读 `.store` 标量；`ToggleConsole → store.ActConsole()`） |
| `src/front/console_panel.at` | `ConsolePanel` 组件（`Clear → store.ConsoleClear()`） |
| `src/front/ctx_menu.at` | `EditorCtxMenu` 组件（坐标锚态直读 `.store`；`Cut/Copy/SelectAll/Dismiss → store.Ctx*()`） |

## How to Run

```
cd specs/auto-edit          # 本仓布局（自仓根起）

# —— vm 轨（默认 AutoVM + merged 进程内直调）——
auto run -r vm              # iced 原生窗口（工具链经 PATH 解析）

# —— vm 轨 split 形态 ——
auto run -r vm --no-merge   # VM+VM split：AutoVM HTTP 后端 + 前端窗（HTTP 往返）
auto run --server vm        # 后端独立 serve（只起 AutoVM HTTP，不开窗——vue dev/联调用）
# split 功能环已全绿（2026-09-21 复验：树/打开/编辑/保存/退出存盘经
#   back HTTP 全通）——上游 auto-lang PLAN-669 修复 #[api] 实参按名绑定
#   后解锁（此前 query 集合串直塞/body 不解析致带参契约全空，PLAN-003
#   F-W1→勘误定性为实参装配断层）。工具链须含 669（≥ 2026-09-21 构建）。

# —— 引擎切换（VM+Rust）——
auto run -r vm --server rust   # a2r 生成的 Rust axum 后端
# ⚠ 现状：a2r server 生成器模板假设 api::Db 状态注入 + 契约 fn 转译为
#   空体桩（PLAN-003 F-R1 实勘，编译 E0432）——rust 引擎暂不可用。

# —— vue 轨 ——
python scripts/regen_vue.py --build        # 生成（strict）+ install/build（vue-tsc+vite 绿；补件链已退役）
# vue dev（两终端，jade-edit 同款配方。原「不用 auto run -r vue」围栏已
#   解除——补件退役后其内置再生成即自完备产出，无覆盖损失[PLAN-671]；
#   dev 配方仍推荐下述两终端形态）：
#   终端1（后端独立 serve）：auto run --server vm -B 8173
#   终端2（前端）：cd gen/front/vue && AUTO_HTTP_PORT=8173 pnpm dev
#   vite（pac front_port）代理 /api → AUTO_HTTP_PORT（实测代理 200）。
#   ⚠ 必须显式 --server vm / AUTO_HTTP_PORT 对齐——vue.rs 缺席时默认走
#   rust 引擎。后端 API 经 669 修复可用；vue 首版仍以构建绿为准
#   （vm 宿主内建无 vue 运行时，见 Concepts vue 轨节限制清单）。

# —— 性能模式（L2，PLAN-004：tools/perf 一键链）——
python tools/perf/perf.py check     # 依赖自检+环境指纹（工具链须 ≥1588/含 669）
python tools/perf/perf.py smoke     # rqhost 预热 + VM+RQ 双实例编排验证
python tools/perf/perf.py a2r       # a2r 生成（PLAN-021 复验 exit 0——back member blocked 见 PLAN-021 口径）
python tools/perf/perf.py release   # cargo --release（依赖 a2r 绿后生效）
# 语义=测量模式阶梯（docs/strategy/002-north-star-v2.md §5）：L0 日常
#   VM+merged / L2=a2r+release+RQ（唯一有预算效力）。模式矩阵与阻塞全景
#   见 tools/perf/README.md；退出码 0/3/1（3=blocked-on-upstream：RQ 渲染
#   臂 codeeditor 覆盖缺口[供料 §6]、a2r 词汇门[§7]）。PERF_PROJECT /
#   AUTO_RUST_WORKSPACE 可把验证跑锚到主检出（worktree 零重物）。

# —— 测量套件（PLAN-005：tools/bench，L0 proxy + 预算断言）——
python tools/bench/bench.py check     # 依赖自检+环境指纹+全量读检测器红证自检
python tools/bench/bench.py proxy     # L0 套件：启动分解（弃暖机）/打开计时
                                      #   1/10/100 MB/内存采样/全量读检测/
                                      #   断言报告 → results/<ts>.jsonl
python tools/bench/bench.py assert    # 仅预算断言（对最近 results 文件）
# 阶梯效力引用：--mode l1/l2 经 tools/perf/perf.py 链取归因（blocked
#   exit 3）；硬门禁仅 L2 评估，L0 断言报告逐行显式终态（not-armed/
#   arch-blocked/blocked-upstream/pending-feature/ledger 五类，无静默
#   缺席）。结果 results/ 入仓追踪；fixtures/、logs/ gitignored。
#   观测通道探针矩阵与四问实勘见 tools/bench/README.md。
```

前置：`auto` 在 PATH（或将 `AUTO_BIN` 指向 auto 可执行文件）；`pnpm`
在 PATH（vue 轨 install/build 用）。本仓不构建工具链。bps 蓝图池经
pac.at `dep bps` 消费**兄弟仓** auto-lang 的 blueprints（PLAN-002
方向一；路径相对运行目录——主检出需 auto-edit 与 auto-lang 同居
D:/autostack，组 worktree 需组内 auto-lang 兄弟树；jade 同款依赖
形态）。生成物目录（`deps/ dist/ gen/ rust-workspace/ build/`）均
gitignore，可再生。

## Tests

```
cd specs/auto-edit/tests
python desktop_mcp.py   # MCP 桌面动作矩阵：三源触发/tab 工作区/热重载/OS 键位层
```

前置：`pip install requests`；`AUTO_BIN` 环境变量优先，否则取 PATH 的
`auto`；`AUTO_OPEN_PATH`/`AUTO_SAVE_PATH` 环境变量旁路阻塞式文件对话框
（不设则跳过 T9/T10 分组）。

注（PLAN-005）：T6 正文断言走 **save 路径 E2E**——toolbar 保存落盘后读
`AUTO_SAVE_PATH` 文件比对（`src_active` 不再实时，降格为激活 tab 初值
镜像）；该断言面验的是真实写路径而非模型镜像。

现状注记（2026-09-21，PLAN-004 T-03 以工具链 v0.4.2-1631 五连跑定标，
收据见 `docs/plans/004` 附表 A）：**测试级失败清零**——原 39/6 的
menubar 快照债已随上游修复消散；**进程级早崩 2/5**（app 实例中途死亡、
MCP 拒连、死亡点逐跑异——上游 F-RV6 竞态存活，证据增补见
`docs/upstream/2026-09-m1-supply.md` §5）。基线口径（临时，上游修复后
废除重跑条款重定正式基线）：**完成态跑次 = RESULT 行出现且 ≥49
passed / 0 failed 判绿；无 RESULT 行 = 工具链竞态早崩 → 重跑一次而非
计败**。

PLAN-008 口径更新（2026-09-22，工具链 1914 钉版）：矩阵扩 T12 字节保真
检查组（BOM 正/负向、CRLF/LF 编辑后字节往返、CR 无编辑往返+状态栏
label、mixed→LF 转换经确认弹层、非法 UTF-8 只读兜底+磁盘哈希零变，
fixtures/ 六件入仓）——完成态 **57/0**（50/0 + 7 新检查），判绿下限
随升 **≥56 passed / 0 failed**；menu/paste 类非确定 flake（失败点逐跑
漂移、隔离复现即绿——F-RV6 同族）复跑条款沿用。

PLAN-009 口径更新（2026-09-22，工具链 1914 钉版同版）：矩阵扩 T13 查找
替换检查组（开栏+effective 拼装四组合+×关栏清搜索态、find_next 推进/
回绕、Replace All E2E 落盘字节+计数反馈、readonly 替换拦截+磁盘哈希
零变、空 query 零动作、find-in-files 端点+条目点击开文件、500 条上限
截断、>10MB 大小门，fixtures/find/ 四件入仓）——完成态 **77/0**
（57/0 + 20 新检查），判绿下限随升 **≥65 passed / 0 failed**（T-00
决策探针 `tests/probe_find.py` 23/0 为前置决策门，不入矩阵计数）；
T12 复跑条款沿用；find-in-files 搜索对含生成树（gen/ ~11k 路径）的
workspace 全程 ~9s，T13.6/13.7/13.8 轮询窗已按此放宽。

PLAN-010 口径更新（2026-09-23，工具链 1993 钉版 `auto-010.exe`，
baseline-check 干净检出 77/0 复验同版零回归）：矩阵扩 T14 会话恢复+
最近文件检查组（会话写入字段/untitled 排除/recents 同录、注入会话重启
恢复 tab 序+active+仅 active 装载、激活未装载 tab 触发装载、ws_dir 不
匹配全新启动、taskkill 强杀崩溃恢复、脏 tab 不保存退出恢复=结构在/
脏编辑丢、最近文件侧栏关闭后条目在+点击重开、ActNew untitled 化排除、
损坏 JSON 静默全新启动；每检查独立进程+临时 APPDATA 隔离——T11 先例；
恢复链检查用 python 侧注入会话文件驱动，fixtures/session/ 两件入仓）
——完成态 **86/0**（77/0 + 9 新检查），判绿下限随升 **≥85 passed /
0 failed**（T-00 决策探针 `tests/probe_session.py` 23/0 为前置决策门，
不入矩阵计数；决策记录=Q-1 registry 存留切回免重装/损坏 JSON 容忍形
ws 门兜底）。T12/T13 复跑条款沿用；T14 会话链零 `code_editor_text`
（检测器白名单零变更）。

PLAN-011 口径更新（2026-09-23，工具链 2044-dirty——并行会话施工中
共享 target/debug，判据前必核 `auto --version`）：矩阵扩 T15 文件
diff 检查组（env 旁路 Tick 自开+计数 state、形状计数 dbg 四件、三段
标记**分离节点**口径、hunk 导航推进回绕序列、hunk 位次派生、关闭复原
tab 零扰动、unbalanced 形态 4ctx/1pair/2del、缺文件错误形、行数超限
拒绝、渲染截断 cap 600+truncated+degraded；每检查独立进程+临时
APPDATA 隔离——T11/T14 先例；fixtures/diff/ 六形态 golden 入仓）——
完成态 **97/0**（86/0 + 11 新检查），判绿下限随升 **≥96 passed /
0 failed**（T-00 决策探针 `tests/probe_diff.py` 26/0 为前置决策门，
不入矩阵计数）。T12/T13/T14 复跑条款沿用；F-RV6 进程级早崩在
2044-dirty 复现增补（upstream §14，死亡点逐跑异——无 RESULT 行重跑
条款继续适用）。diff 链零 `code_editor_text`（检测器白名单零变更）；
bench 增 `diff` 计时档（tools/bench `bench.py diff`：small/mid 基线+
尺寸/行数门拒延迟，JSONL 在 results/，档外全文 diff blocked-on-
upstream 注记——引擎 diff_snapshots 时代清偿）。
**PLAN-695 交互注记（2026-09-23 merge 期实勘）**：行尾分组 submenu 化
后 T12.6 mixed→LF 的菜单项对 MCP 失明（menubar-sub 子树不进快照——
裸 main 两级复现，upstream §14 登记）：该项失败=已知上游缺（子菜单命
令矩阵不可驱动），非本件回归、不计判绿口径；清偿后自动恢复计数。

PLAN-012 口径更新（2026-09-23，工具链 2046 钉版 /d/tmp/p012_pin_auto.exe）：
矩阵扩 T16 目录 diff 检查组（env 旁路自开+golden counts 五态、快照形态
徽标/[目录] 标记、过滤纯 front 态、下钻 011 视图复用+返回目录、复制直
执行/覆盖复制确认链/删除确认链磁盘 E2E、关闭复原、根缺失错误形、
>2MB 同尺寸未比对注记；每检查独立进程+临时 APPDATA 隔离；同步动作走
tmp 生成树 fixtures 保 pristine——008 先例；fixtures/dirdiff/ base+rev
五形态 golden 入仓）——完成态 **109 检查**（97 + 12 新检查）。实测谱
（F-RV6 竞态期，五轮 85/5→95/2→104/5→107/2→106/3）：本件 T16 组
**12/12 首轮全绿**（run3）；最优轮 run4 **107/2**（T12.6=R-4 已知上游
缺不计判绿+paste 剪贴板竞态 flake——轮换谱 fold/paste/EOL-conn/
T13.6/T13.8/T14.1 五轮全录，皆非本件路径；无 T16 基线轮 run2 亦 2 败
=噪声地板预存实证）。**判绿口径=≥107 passed / 0 failed（T12.6 已知败
不计+轮换 flake 按重跑条款清零）**；决策探针 `tests/probe_dirdiff.py`
27/0 为前置决策门不入矩阵计数。目录链零 `code_editor_text`（检测器
白名单零变更）；对齐=长度桶+桶积护栏 700k（同长巨桶超限=优雅 err
架构注记——.at 无 sort/hash 原语，upstream §15 want）；文件复制=字节
往返 read_bytes→write_bytes ≤2MB（fs.copy 被 `copy` 保留字阻断——
T-00 勘定 upstream §15 want）。vue 臂双重 blocked-on-upstream（strict
gen 红=menubar-sub 族 schema 缺登记[695 预存主干断层]+helper 族
TS7006[§14]——lenient gen ✓ 34 组件，本件零新增错面）。

PLAN-013 口径更新（2026-09-24，工具链 2046 钉版 /d/tmp/p012_pin_auto.exe
同版续用）：矩阵扩 T17 大文件模式检查组（探测置位+plain 绑定 state 面
big_active/loaded_bytes/lang_active、ReplaceAll 拦截 console+big_hint、
save 拦截磁盘零变 E2E、big↔normal 切换往返 props 联动、超大拒绝 513MB
错误形 tab+readonly_label、阈值下界 49MB 不误伤、normal 态零误伤
replace+save 写通 E2E、会话恢复重探；每检查独立进程+临时 APPDATA
隔离；50/49/513MB 级 fixture 生成式临时构造不入库）——完成态 **117
检查**（109 + 8 新检查）。**判绿口径=≥115 passed / 0 failed（T12.6
已知上游缺[menubar-sub MCP 失明]不计+轮换 flake 按重跑条款清零）**；
决策探针 `tests/probe_bigfile.py`（8/0）为前置决策门不入矩阵计数。
大文件链零 `code_editor_text` 新面（护栏=前置门——检测器白名单零变更
）；探测链=back 第 14 端点 `file_size`（envelope JSON——裸 int 过 HTTP
=serialize null，upstream §16 观察）；超大拒绝位 512MB（200MB 峰值
RSS ~1.55GB 实测外推——upstream §16 归档注记）；EolConvert 菜单入口
menubar-sub MCP 失明（T12.6 同源）——其护栏门在 store 侧（
EolConvertRequest+EolConvert 双门），矩阵不可直驱如实注记。bench 增
`bigfile` 计时档（tools/bench `bench.py bigfile`：49/50/100MB mode
on/off 尺寸杠杆代理对照——mode 无独立开关面，big 由装载前探测派生；
L0 无预算效力口径注记，JSONL 在 results/）。

PLAN-014 口径更新（2026-09-25，工具链=auto-lang master tip 钉版构建
[.wt/plan-014/auto-lang@729dd4f2f target/debug，含 PLAN-701 六件供料]）：
矩阵扩 **T18 上游端点消费检查组**（18.1 readonly 兜底不受扰[513MB 拒绝
形 save blocked+磁盘零变]、18.2 光标恢复 E2E[find 跳匹配持久位→重启
TabActivate 读回——set_cursor 不 republish on_cursor 契约的读回面]、
18.3 scroll 条件形注记[会话无 scroll 字段=「滚动不恢复」现状锚]；
normal 零扰动=T17.7 覆盖、会话链=T17.8 覆盖不重复设检）——完成态
**120 检查**（117 + 3 新检查）。**T17.3 翻转**：save 拦截检查随护栏解
禁退役，改断言 big save 直写（console saved (direct)+字节全等+时长
sane——直写 46ms/字节四变体全等见 tests/probe_upstream_consume.py）。
**判绿口径=≥112 passed / 0 failed（已知 blocked 集不计：T12.6[menubar-
sub MCP 失明]+T17.2/17.3/17.4/17.8[大文件实例 UI 硬卡死=上游回归，
2046→83c4621b5 窗引入——upstream §17 登记，二分边界+消费面全摘实证
非 701/非本件面；清偿后自动复绿]+轮换 flake 按重跑条款清零[T13.6/
T12 BOM 族]）**。执行期谱（v0.4.2-2155 钉版@729dd4f2f）：五连跑零早崩
**run1 114/6、run2 115/5、run3 114/6、run4 116/4、run5 115/5**（T18
簇 12/12 全绿；T17 交互簇 blocked 轮换[17.4 于 run4 翻绿一次]；谱文
件 frv6_run*.spect=实例数 watcher——F-RV6 根因勘误后干扰归因面；另一次
跑窗遭跨会话 /IM auto.exe 清扫全军覆没[15→0 实例实录]=重跑条款归因
样本）。决策探针 probe_upstream_consume.py（字
节保真四变体+50MB 46ms+0 基实证+time 直出形）为前置决策门不入矩阵
计数。time 族双录机制在册（bench.py app_epoch——front ms 行待供④
vue 映射供件，§17 新 want；open_ms 现 host 回退源）。vue 臂**双 exit 0
恢复**（strict gen 33 组件+pnpm build；print 遮蔽缓解件退役——上游供⑤
吸收）。上游消费收据+新 want 登记 docs/upstream §17。

PLAN-015 口径更新（2026-09-26，工具链=auto-lang master 重建
[v2156-g1d597e3f4 target/debug——PATH 旧二进制 g86b56884b 系并行分支
构建**不含 PLAN-701 native**（shell_add_recent 链接炸），判据前核
`auto --version` 含供料提交的坑位二度应验]；组依赖=`.wt/edit-015/
auto-lang`@3e3e1e297 钉版 worktree[014 Q-1b 惯例——pac `../../../`
路径在组目录下解析为组兄弟]）：矩阵扩 T15 组 **P15 内联视图断言族**
（①irows 计数+形状计数 dbg_i\*×3=golden 推导器期望[probe_diff.py
`derive_inline`——六形态行数恒等式/计数恒等式/三段继承+行号全行核/
pair 邻接/双 cap 模拟 58/0 前置门]②切换零重比[envelope 派生面八字段
切换前后不变+钮文翻转快照]③内联态导航[推进+回绕 2→0+位次串]④双
cap=big_reorder 现役 fixture[信封 600+内联 600 拦腰形+双注记快照+
关闭复原]；关闭复位 vmode=side+投影清空；重建幂等）——T15 组
**矩阵承载面=
desktop_mcp.py T15 组增 15.11–15.15 五子组**（投影对照/零重比+console
标记计数/内联导航/双 cap big_reorder/内联态重算-下钻路径——T15 组
11→16 检查），完成态 **125**（120 + 5 新检查）。**判绿
口径=≥117 passed / 0 failed**（已知 blocked 集不计：T12.6[menubar-sub
MCP 失明]+T17.2/17.3/17.4/17.8[大文件实例 UI 硬卡死=上游回归，清偿后
自动复绿]——口径承 014；本件新增检查无 blocked 项）。修复轮实录
（v2156-g1d597e3f4）：**120 passed / 5 failed**=已知集全中零新失败
（15.11–15.15 五项全绿；15.12 首轮 FAIL=检查自身缺陷——console 滚动
尾窗前缀差量不可靠，改标记计数法后绿；smoke_t234 18→37=开发期烟测件
不入矩阵计数）。P15 侧写：
**envelope/back 零改动**（替换缝红利首兑现——diff 链仍零
`code_editor_text`，检测器白名单零变更）；T16 下钻复用面回归绿
（smoke_t345 ALL PASS）。vue 臂 build-green 复验=T-06（014 双 exit 0
基线上，本件新面=基础件 for/if/button 族已证面）。

PLAN-016 口径更新（2026-09-27，工具链=auto-lang master 重建
[v0.4.2-2175-g5c558778f target/debug——含 PLAN-703 交付 46efa926a；
PATH 旧二进制 v2156-g1d597e3f4 早于交付实勘重建，**「判据前核
`auto --version` 哈希含供料提交」坑位三度应验**]；组依赖=
`.wt/edit-016/auto-lang`@5c558778f 钉版 detached worktree[014 Q-1b
惯例——pac `../../../` 组兄弟解析]）：矩阵扩 T15 组 **15.16–15.19
缓冲区比较子组**（旁路自开+装载轮转[load_key 单槽 B→A 固定序——
序错置互抢槽位死锁，首轮烟测实勘]/跳转 set_cursor 切走切回读回
[18.2 契约读回面]/旁路单边残缺/关闭复原 tab 零扰动——缺键端点
err 形由 probe_bufdiff.py 探针承载），**T15.9/T15.10 期望翻转**
（>10k 行从 err 拒转正常 envelope[dels=10493 实证]；700 全换形
degraded=false+700/700+降级注记退役）——完成态 **129**（125 + 4
新检查）。**判绿口径=≥118 passed / 0 failed**（已知 blocked 集
不计：014 承接集 T12.6[menubar-sub MCP 失明]+T17.2/17.3/17.4/
17.8[大文件实例 UI 硬卡死=上游回归]+轮换 flake 重跑条款[T13.6/
T12 BOM 族]；**新增上游缺陷集 D-1/D-2**[供料档 §6.2——引擎 rows
面流位错配/anchor 分块非单调：T15.1/15.2/15.3/15.7/15.11/15.14/
15.15 rows 承载断言 blocked——hunks/counts 面正确，15.4/15.5/
15.6/15.8/15.9/15.10/15.13 不受累；上游修复后自动复绿并随
probe_diff ⑦对账绊线触发 golden 重定]）。执行期谱
（v2175-g5c558778f）：全矩阵单跑 **118 passed / 11 failed**——失败
集=T13.6+T17.2/17.3/17.8（已知族 4）+T15.1/15.2/15.3/15.7/15.11/
15.14/15.15（D 族 7）逐项全中**零新失败**；15.9/15.10 翻转绿、
15.16–15.19 全绿、T16 组 12/12 绿（目录面语义零漂移实证）。决策探针
双门：probe_bufdiff.py（裸名解析+缓冲区消费形 8/0——不入矩阵计数）
+probe_diff.py ⑦引擎对账段（64/0——evidence-p016-recon.json 漂移
逐字段在档，golden 保持过渡时代原样不 golden 化缺陷输出）。T-05
bench diff_100mb 判定 blocked（D-1 连带 envelope 体量失真——供料档
§6.3）；上游消费收据+双缺陷登记 docs/upstream/2026-09-diff-engine-
supply.md §6。

PLAN-016 修复轮口径更新（2026-09-28，工具链=auto-lang master 重建
[v0.4.2-2183-gc8f86ef92——含 PLAN-704 交付 b2f8761e0：D-1 rows 流位
单源化+D-2 anchor 单调过滤，两缺陷清偿]）：**golden 重定轮**——五
简单形 golden 原样恢复（引擎≡过渡参考逐字节全等实证）；big_reorder
golden 按修复后引擎重定（310/310 双向对称+kept 记账+rows 632>600
双 cap 场景自然保持——引擎时代语义=降级退场，漂移史证据
evidence-p016-recon.json 在档）；probe 双绊线恢复严格全等（①′六形
全等+⑦五形 zero-drift+big_reorder 引擎时代换位不变量特判）；T15
rows 面 **blocked 集恢复 014/015 原口径**（D 族 7 项回归正常断言）。
**修复轮全矩阵实录（v2183-gc8f86ef92）：124 passed / 5 failed**——
失败集=T13.6 flake+T17.2/17.3/17.4/17.8 已知族逐项全中**零新失败**
（T15 全组恢复原口径绿含 15.14 改形；判绿=已知集计零 **124/0 ≥117
达标**，完成态 129 不变）。15.14 双 cap 改形注记：生成式 700 全换
fixture（big_reorder 引擎时代形=del/add 块分离换位[632 行、前 600 行
零 pair]——pair 展开 ×2 前提失效，硬断言+smoke_t234 同款改形）。
**bench diff_100mb 判定达成**（战略 §2.1 预算行）：release 工具链全链墙钟 **1906/
1971ms ≤2s**——踩线达成余量 ~5%（四跑谱 1906-2054 在档；引擎计算
~380ms 上游基准在册，链路主耗=2×100MB 读+47MB envelope 全量 rows
投影+49MB 双层 JSON 传输；**计时卫生=fixture writeback 沉降窗 5s**
[无窗跑 2034/2054 与静置分解 1437ms 差 +600ms 失真实证——bench
测量方法修正非放宽]）；over_size/over_lines 档改造为通过延迟形
（4.9/66.2ms）；debug 工具链 14.9s 同档在档（保守上界，不可直比）。
rows 惰性投影/体量治理=观察件 want（红线余量薄根因，登记于供料档
§6.3）。

PLAN-017 口径更新（2026-09-28，工具链=v0.4.2-2183-gc8f86ef92 现役
[含 PLAN-704 b2f8761e0，祖先链核验——判据前核 `auto --version` 纪律
延续]；组依赖=`.wt/edit-017/auto-lang`@c8f86ef92 钉版 detached
worktree[014 Q-1b 惯例——pac `../../../` 组兄弟解析；上游 master 已
漂 705 立项在飞，钉版=工具链构建点]）：矩阵扩 T15 组 **15.20–15.24
差异侧编辑回路子组**（八检查：双侧跳转[A 新开/B 菜单重开新开/行级
A 锚/已开激活——落点读回=切走切回 SyncCursor 面]/保存自动重比[badge
live→保存→视图自动重开+vmode 保持+计数变形+重比行+落盘]/无关保存
零扰动/面板 live 预览[ReplaceAll→防抖单拍保存前变化→钩子刷新一致]/
B 侧跳转[→B kb 激活+b1 读回——label 解析行号真值]）——完成态
**137**（129 + 8 新检查）。**判绿口径=≥125 passed / 0 failed**
（016 修复轮恢复原集 ≥117 基线 + 8 新检查随升；已知 blocked 集不计：
T12.6[menubar-sub MCP 失明]+T17.2/17.3/17.4/17.8[大文件实例 UI 硬
卡死=上游回归]+轮换 flake 重跑条款[T13.6/T12 BOM 族]）。执行期谱
（v2183-gc8f86ef92）：全矩阵单跑 **133 passed / 4 failed**——失败集
=T13.6 flake+T17.2/17.3/17.8 已知族逐项全中**零新失败**（T17.4 本轮
翻绿=016 在录轮换成员）；15.20–15.24 全绿、15.16–15.19/T16 组回归
绿；已知集计零 **133/0 ≥125 达标**。**纯 front 件注记**：产品 back
（src/back/api.at+fsys.at）零 diff（AC-05 路径断言）；probe 载具
（tests/probe_bufdiff_app——测试基建非产品件）为 T-00 勘定扩 env
端点最小面。决策探针 probe_bufdiff.py ③段 **13/0**（badge 轨形/
registry 卸载存活/set_text 驱动面——不入矩阵计数）；smoke_t234 P17
断言族 4 检查（开发期烟测不入矩阵计数——015 惯例）+launch APPDATA
隔离补漏（真实用户会话恢复污染 tab 集=P17② 假红根因）。**console
镜像滞后卫生**：`.console` state 相对 handler 执行异步滞后（开发期
实证）——console 断言改 wait_console_line 轮询式。big 直写臂同钩
（DiffSaveHook 单挂点两臂同位）；big 变体矩阵注记 blocked 承接
（T17 卡死族未清偿，不新增硬红——AC-02 代码路径同位+钩子单挂点
证据在档）。

PLAN-018 口径更新（2026-09-29，工具链=v0.4.2-2205-g5bb3f53be
release 现役构建[组依赖三树 `.wt/edit-018/{auto-edit,auto-lang,
auto-down}` 钉版 detached——**auto-lang Cargo.toml:140 autodown-core
跨仓 path 依赖=组内 auto-down 兄弟树必需**[工具链构建缺树即
failed to read manifest，实测]；判据前核 `auto --version` 纪律延续]）
——**M4 预算门开篇件=tools/docs 面**：app 产品代码仅 BENCH 标记
补点 2 处（`bench_session_restored`/`bench_open_rejected`，
AUTO_BENCH=1 门控未设零差异——editor_store.at 会话恢复链尾/超大
拒绝分支尾）。**bench 扩三档**：`open`（100MB 生成式装载墙钟×N
[首跑弃暖机]+513MB/1GB truncate 探针 512MB 拒绝位对照——记账形态
[016 release 工具链先例]）/`steady`（启动链分解×N 2ms 轮询+≤80ms
对表归因）/`warm`（空窗+20tab 会话恢复[10MB×20 生成式注入隔离
APPDATA]+恢复净段/active 装载/不读盘三分解+两形态内存采样）——
锚点共性=APPDATA 隔离+AUTO_PROJECT_DIR 钉位+fixture 沉降窗 5s
（016 writeback 卫生）。**锚点数字回填 budgets.json validity**
（open_100mb median 841.0ms ≤1s 行内首实测锚；steady 232.6ms 归因
VM boot 224.5ms[瘦身=后续件]；warm 恢复净段 1.3ms ≤120ms 绿注记
+不读盘标记单对实证；idle 空窗 51.4MB ≤60MB 行内；1GB=512MB 拒绝
位实证）。budgets 全表重定：open 两行「架构性不可达」过期文本
纠偏+禁调优放开仅限此两行+warm/idle 行 ledger 化（arch-blocked
位 l0 覆盖转缺席=语义退役显影）。`assert` 默认目标过滤=含
budget_assert 记录的最新文件（results/ 多档 JSONL 命名坑位——
011/013 前缀档起既有，本件收口）。a2r 现势勘定=三类生成缺口残余
（供料档 m4-perf-unblock-supply §1；探针报告 tests/
evidence-p018-survey.md）。矩阵检查集零变更（137/判绿 ≥125/0 承
017；本件全矩阵回归在谱）。

PLAN-019 口径更新（2026-09-29，工具链=v0.4.2-2205-g5bb3f53be release
同 018 锚[组依赖钉版 auto-lang@5bb3f53be/auto-down@3373a5c detached
——`.wt/edit-019` 组三树]）——**M4-02 portable 单 exe 瘦身件=构建
通道/工具面**（.at 源零 diff、矩阵检查集零变更判绿口径承 018）。
**portable 构建用法**：`python tools/portable/build_portable.py`
（一键链=regen[上游阻塞时快照回退复用现势生成物]→[profile.release]+
deps 补丁注入[幂等——MARKER 块替换+第二遍哈希自证]→cargo release
→strip→产物 `dist/portable/auto-edit.exe`+sha256→尺寸断言 ≤15MB
[超限 exit 1+差距数字]）。变体面：`--set lto=fat --set
codegen-units=1 ...`（手段迭代）/--baseline（零手段对照）/
--check-idempotent（幂等自证）。产物面护栏探针：
`python tools/portable/probe_surface.py --variant <tag>`
（steady 代理/open/idle——供① 阻塞期记录性通道）。**首件数字回填**：
基线 39,411,200B→终态 29,844,480B（-24.3%，≤15MB 未达标=分阶段
语义）——手段×尺寸终表/构成占比/门控手段测量位见
`specs/auto-edit/tests/evidence-p019-survey.md`（regen 探针 133 错
实录同档 tests/）；budgets.json installer 行已回填。矩阵检查集零
变更（判绿口径承 018：137/≥125/0——本件抽查档不计入）。

PLAN-020 口径更新（2026-09-29，竞品侧工具面——.at 源零 diff、矩阵
检查集零变更判绿口径承 018/019）。**公开对比表竞品侧先行件**：
测量方法论与四对象计时通道定案见
`tools/compare/METHODOLOGY.md`（VS Code=renderer RSS 平台+确认窗
[5MB=3s/100MB=6s]/Zed=首帧日志行/BC5=report 产出/NP++=pending——
装后补跑即得列；滚动帧率=v1 后补）。竞品基线用法：
`python tools/compare/compare.py check|run <对象> <5mb|100mb>
[-n N]|report`（fresh profile per run+沉降窗 5s+invalid-run 重跑
条款；results/ JSONL 入仓=三要素 {版本钉版,环境指纹,跑谱+离散}）。
我方三态锚点：`python tools/compare/anchors.py [--verify]`
（018/019/016/021-L2 在档 JSONL 直读零重算——锚点[VM 形态]/产物面
[last-good]/L2 直拉判定[steady/diff/open 实数+verdict 随行]）。表格生成：
`python tools/compare/render_table.py [--check]`（数据驱动——文末
「公开对比表」节为生成区间**禁手改**，--check 断言复现一致）。

PLAN-021 口径更新（2026-09-30，工具链=v0.4.2-2366-gacf653d3f 组树
debug 构建[714 r3 交付点 acf653d3f 钉版——含 Try 臂+route-A 深修；
组三树 edit-021/{auto-edit,auto-lang@acf653d3f detached,auto-down@
3373a5c detached}——auto-down 组树必需实录在档[018 教训复验：
跨仓 path 依赖在 crates/auto-lang/Cargo.toml:140]]）。**供① 消费
复验=解阻日首判**：a2r 三重判据首度全绿（exit 0+零 skip 警告+fresh
workspace check 过——018 blocked 态闭环）+last-good 基面退役
（build_portable `--regen` 现势直跑[快照回退臂 RETIRE_NOTE]，幂等
自证 pass）+生成码首跑收据+三域冒烟 G-A/G-B 实证绿。**L2 直拉首判**
（`bench steady|warm|open --l2`+`bench diff --l2`——release 产物/
back 服务零旗标直拉形态档）：steady_start armed **PASS** 15.6ms ≤80ms
（硬门禁正式判定绿）/idle_mem armed **PASS** 9.7MB/diff_100mb armed
**FAIL**（记录性）5183.2ms，对照 018 VM 形态谱归因在
budgets validity。

**残余清偿+全表收口（同日 PLAN-714 r4——e93a717da 动态注册键贯通
[§7 code_editor 注册断链反转]，补跑工具链=v0.4.2-2389-ge93a717da）**：
open_100mb armed **PASS** median 863.2ms ≤1s+warm_start armed **PASS**
恢复净段 0.0ms·全链 19.3ms ≤120ms——**预算表五行判定全部落地**
（判定数字+谱在 budgets validity；「滚动不掉帧」半行=供②/open_1gb=
裁定中/renderer=n/a 维持）；三域冒烟 **7/7 全绿**（r3 轮三 FAIL 全
反转——G-B 两臂+G-A 投影/包络+G-C 装载 E2E/badge try）；对比表
open 行 L2 实数补列+l2-pending 虚席退役（anchors --verify/
render --check 双门绿维持）。L0 矩阵复跑=VM 轨不受累（判绿口径承
018/020）。forensics=tests/
evidence-p021-blocked-survey.md（全弧：两面 forensics+解阻复验+残余
§7 登记→714 r4 清偿）；上游登记=供料档 §6[已清偿归档]/§7[714 r4
清偿归档]。

PLAN-022 口径（2026-10-01，工具链=v0.4.2-2474-g95dcfb55b 组树 debug
构建[716 ec45f911c+719/720；组三树 edit-022/{auto-edit@plan-022-dev,
auto-lang@95dcfb55b detached,auto-down@895f8d0 detached}——auto-down
组树必需复活实录在案（autodown-core 相对路径 sibling 解析，021
「不再需要」结论随 95dcfb55b 现势失效应验）]）。**PLAN-716 三组
消费件**：①**diff_100mb 窗口形清偿重判 armed PASS**——`bench
diff --l2`（判定档切 `/api/diff_files_window` 9920 五参
offset=0/limit=600 渲染 cap 对齐「出结果」口径=全量
hunks/counts/rows_total+首窗 rows）：median **784.8ms**（N=4 谱
756.6-928.8）≤2s——021 FAIL 5183.2ms 清偿（6.5× 倍率；全量对照档
diff_100mb_full 在档不判定，016/021/022 三态数字并陈不删）；判绿
回填位=budgets diff_100mb validity+对比表 diff 行；窗口形契约=
back-api.md 第 16 端点+diff-view.md 窗口形节（VM 轨窗口调用=供⑧
上游缺口——L0 形维持全量旧径零扰动）。②**帧两行断言化首判=供②
交付物达成**（716 r3 供⑨ 清偿后复工——armed FAIL 双行如实红：
type_latency P50 110/P95 115ms vs ≤16.7ms→FAIL ~6.6 帧+scroll_fps
8.0fps vs ≥54→FAIL〔换行连发 cursor-follow 滚动驱动；debug 对照谱
同量级=编译形态无关〕——键入帧全量重建管线 ~110ms/帧主耗，优化=
管线件后续；判定协议/首帧段记账位=SD-01 PLAN-022 节；对比表滚动
行实数落位）；③**双构建形态通道**——`build_portable [--ts on|off]`
（highlight-treesitter feature 门控注入）：ts-off=
dist/portable/auto-edit.exe（发布/installer 约束形——30,355,456B
实录，尺寸门=installer 行判定域，分阶段语义差距在案）/
ts-on=auto-edit-ts-on.exe（语法完整形——51,457,024B，**Δ+21.1MB
vs 716 实测 +18.9MB 同量级**；binary 探针 tree_sitter 符号 on=23/
off=0 干净门控实证）；双形态 boot/装载冒烟 PASS（release 零旗标
直拉 bench_open_done 2s 同拍）；ts-on 构建回避钉=blake3 1.5.5
锁定（供⑪ cc 夹缝——供料档 §8）；④**对比表滚动行落位**（我方
l2-pending 零数字+竞品 020 Q-2 pending 维持——anchors --verify
9 行+render --check 双绿）；⑤**供③ P716-D1 复试销账未达**（×3 谱
93 PASS/0 FAIL T17 不可达——处方 part-1 端口钉位已落实；维持
挂账 evidence-p022-t06.md）。上游消费首跑登记=供料档 §8（供⑧/
⑨/⑪+语法联动 want——highlight_segments 三面 grep 零命中，M3
尾巴供料驱动注记维持）。front 消费面零改动（frozen③）。

PLAN-023 口径（2026-10-02，工具链=v0.4.2-2546-g986e765ac 组树 debug
构建[组三树 edit-023/{auto-edit@plan-023-dev base 5dbfd79,
auto-lang@986e765ac+auto-down@895f8d0 detached}——组结构=构建
load-bearing：生成 ws 根 auto-lang.path 直指组 sibling]）。**M4-06
installer 收口件（判定终态）**：①**门重基线（用户裁定）**——
installer ≤15MB→**≤50MB**、idle_mem ≤60MB→**≤150MB**（渲染暖态）
：独立渲染期过渡口径，RQHost 渲染拓扑落地后回归严格门（≤20MB+
≤10MB 级——同日精调 15→20，双已知路径；战略 §2.1 追记在案）；②**判定终态 armed PASS**——终态
手段集 **V2b 维持**（lto=fat+cgu1+strip+tokio 子集；opt-level=3 保
性能+panic=unwind 保 17 处 catch_unwind 兜底）30,403,072B ≤ 50MB
（余量 22.0MB）；三代谱 V2b/opt-z -8.2MB/abort -7.76MB〔abort 因
catch_unwind×17 语句/8 语义点冲突出局——证据
tests/evidence-p023-survey §③〕；组合投影 16.5~16.8MB（019「距门
714KB」叙事翻转——缺口大头=上游域，深裁可达池仅 axum <0.5MB）；
③**发布构建用法（终态）**——`python tools/portable/build_portable
.py --regen`（默认=ts-off 发布形+V2b 手段集+50MB 门断言，产物
dist/portable/auto-edit.exe；`--ts on` 语法完整形=记录位，>50MB
撞线=非发布形正确信号；`--set` 可注入谱测量）；④**护栏零回退**——
工具链轨五行 v2546 复跑全绿（steady 17.8ms/open 865.8ms/warm
2.6ms/idle 9.1MB/diff 窗口 635.0ms——021/022 对照带内，谱 JSONL×5
入仓）。P023-1 账本投影=merge 期项（015-022 先例）。规范详
modules/perf-measurement.md installer 判定终态节（SD-01）+
00-overview M4 第六件注记（SD-02）+战略 §2.1 追记（SD-04）。

PLAN-024 口径（2026-10-02，工具链=v0.4.2-2579-gb385534d7 release 组树
构建[组三树 edit-024/{auto-edit@plan-024-dev base 957686f,
auto-lang@b385534d7 含 725+auto-down@895f8d0 detached}]）。**M4-07
收口件（判定面快照态）**：①**帧两行重判**——725 管线增量交付后同机
复判 N=4 有效谱：P50 110→1-4ms（中位 ~30×——单帧单建生效，脏帧
builds=1 全体+段和 ~1.8ms）而判定行 FAIL 维持（P95 95-112ms>16.7ms/
scroll 6.7-8.8fps<54——022 首判同带）；分段归因=段外 ~108ms=S5 域
〔layout/shaping/draw 未插桩——尾部帧与 ce_widget_new 组件重建同现+
滚动帧 ~108ms/帧节奏；下游 handler 臂成本排除〕，S5 增量化=auto-lang
余题（evidence-p024-frame-rejudge）；判定口径 frozen 零改动；budgets
两行重判纪元追加。②**对比表滚动行刷新**——022 首判 8.0fps+024 重判
7.0fps 并陈（anchors --verify 10 行+render --check 双绿）；NP++ 未装
四路探测在案→pending 维持+**Q-3 默认口径落表脚注：列完整性=后续补列
域非里程碑判定门——tag 不等待**。③**M4 终检表**——预算十行终态
（6 PASS+2 FAIL+renderer n/a+open_1gb=(b) 登记收口——供⑮ 供料档 §10，ledger-blocked-with-plan）+四面核销
（installer/对比表/语法高亮首批核销；预算面帧两行双态如实）=
modules/perf-measurement.md M4 判定收口节+00-overview M4 第七件注记+
evidence-p024-m4-final-check（tag 素材逐字对账档）。④**v0.1-M4 tag
记录位**——打点=本件 merge 收据（五检查点后；023 已录口径「帧两行不
阻 tag+注记并陈」+里程碑标记≠发布）；M4 完全收口=帧两行清偿后（open_1gb
已按 (b) 落账收口——供⑮ §10，2026-10-02 用户裁定）。P024-1 账本投影=merge 期项（015-023 先例——work 不碰
活账本）。

PLAN-025 口径（2026-10-02，工具链=v0.4.2-2603-g1a15c8eee release 组树
构建[组三树 edit-025/{auto-edit@plan-025-dev base de6cb95,
auto-lang@1a15c8eee 含 728@69059dfaa+auto-down@895f8d0 detached}；
判据前核 `auto --version` 纪律延续]）。**供⑮ 消费件（M4 挂账头号
清偿）**：①**512MB 拒绝位退役**（用户裁 Q-1=(a) 移除——editor_store.at
拒绝臂/`bench_open_rejected` 标记/「只读(超大拒绝)」标签族退役；
big 态命令护栏零回退[ReplaceAll/EolConvert 拦截+save 直写——grep 锚
6+3 处在档]；50MB=唯一分域线）。②**1GB E2E 全链**（T17 组扩容）——
**T17.5 翻转**（513MB+1B 拒绝形→分页装载成功形）+**T17.9-17.12 新
增四链**（1GB 装载[loaded_bytes 全量+big 态]/交互活体+帧带[fprobe_n
前进——占位不冻结下游观测形]/编辑记账[cut 脏标记+关闭确认证实]/
保存 byte-for-byte[全卷 md5 全等]）+**T18.1 重铸**（readonly 兜底·
513MB 拒形→零编辑直写往返 byte-for-byte——编码形兜底由 T12.7/T13.4
承接维持）。**T-00 实勘注记**：编辑器光标键盘[Down/Ctrl+End/字符键]
autoui_keyboard 不达 code_editor（小文件对照同=普适测试基建限制）；
查找下一处在分页 100MB 21s 未决（728 查找债下游实测确认——upstream
回执登记）；014 期大文件实例 UI 硬卡死在 728 未复现（点击/应用级键
全活）。③**open_1gb 断言化**（budgets 行 armed：判定口径=装载成功
E2E 断言非时间预算，4.0s 上游谱=记账注记；bench open 档重铸=真内容
装载锚点族：threshold_50mb 恰界/threshold_50mb_1b 界下 1B 阈界双轨
+boundary_513mb+open_1gb——谱 JSONL 在 results/）。④**检查集变更
注记**：完成态 **141**（137 + T17.9-12 四新检查；T17.5/T18.1 原位
翻转不计新）。**判绿口径=141 passed / 0 failed**——执行期谱
（v0.4.2-2603-g1a15c8eee 首跑）：**141 passed / 0 failed 全绿**
——**014 期已知 blocked 集 T17.2/17.3/17.4/17.8 在 728 工具链自动
复绿**（大文件实例 UI 硬卡死未复现——m1-supply §17 登记形「清偿后
自动复绿（检查零改动）」应验；检查零改动实证）；T12.6 在 0 failed
集内（menubar-sub 债现状随本轮谱观察——单跑实证不作债务清偿判定
复述）；轮换 flake 重跑条款[T13.6/T12 BOM 族]未
触发。1GB 四链双跑谱：**装载 3.2/3.1s·保存 1.0/0.8s**（上游 p728 基准
4.0s/657ms 带内——E2E 计时含派发+轮询粒度 0.25s，粗粒度记账注记）。
全量谱存档=tests/matrix-p025-run1.txt（首跑 stdout 管道截断只留
尾部——复跑全量落盘为 durable receipt，两连 141/0）。
谱与裁定回执=
供料档 §10 消费回执节+modules/perf-measurement.md PLAN-025 节+
editor-store SD（拒绝位退役历史注记+会话现状成文）。P025-1 账本
投影=merge 期项（015-024 先例——work 不碰活账本）。

注：Plan 451 起 T10「热重载」走 DSL 源路径（reload 工具或 mtime 轮询重读
app.at 重新提取 actions + generation bump → 视图重建），实测 50/0 全绿。
OS 用户键位层（`%APPDATA%/auto/keymaps/auto-edit.at`）保持外部文件——那是
用户偏好覆盖而非 app 代码；app id 由 pac.at 的 `name`（经 `auto run` 注入
`AUTO_APP_ID`）提供。

## Plan 626 补记（VM 实机验证四修正）

- **状态栏 行:列**：`text "${.store.line}:${.store.col}"` 多段点路径插值由
  框架修复（aura_view_builder 走条件表达式同款扁平化通道），不可解析时原样
  保留完整模板（含前导点）。
- **脏标记**：脏 tab 标题旁 `*`（`if t.dirty`）；关闭脏 tab 与退出/关窗均走
  标准 `alert-dialog`（PLAN-530 模态族），原固定坐标 confirm popover 退役
  ——VM 下坐标锚弹层有落回普通流的底层缺陷（债务登记），alert-dialog 无此问题。
- **窗口 X 拦截**：声明 `.CloseRequest` handler 的应用可拦截 OS 关窗请求
  （fire 语义同 `.Init`；未声明的应用行为不变）。auto-edit：有脏 tab 弹
  「取消/不保存退出/保存并退出」，否则直接退出；菜单「退出」共用同一入口。
- **Explorer 真目录**：`.Init` → `store.LoadWorkspace()`（Init 名保留给根
  widget 生命周期，store 侧 handler 不得占用）经 `fs.tree(AUTO_PROJECT_DIR, 4)`
  + `json.to_value` 装载真实目录树，头部显示 workspace 名；树节点 id 为相对
  路径，点击经 `fs.join` 读盘开文件。启动日志的 "App.Init failed" 随之消失。

## Plan 629 补记（寄宿公共 scroller）

编辑器滚动条**改用 AutoUI 公共 scroller**（官方 `scrollable`，vue 风格滚动条自动
生效），自绘滚动条与内部滚轮路径退役（headless/单测保留，`AUTO_EDITOR_NO_SCROLLER=1`
可临时关闭寄宿）。集成契约三机制：

- **高度上报**：折叠展开即内容高度变化 → 编辑器重排 → scroller 更新滚动范围与
  thumb 比例（`CodeEditorCore::content_height`，实时 fold 投影）。
- **偏移同步**：滚动偏移由 scroller 持有；编辑器 draw 每帧用 viewport 切片做
  虚拟化渲染（只 shape 可见行，`sync_external_scroll` 粗定位+归一）。
- **光标跟随**：键盘/IME 移动光标出视口 → core 请求标记 → 会话漏斗
  （dispatch_app 尾部）转 `operation::scroll_to`（同拍生效）。

## Plan 630 补记（声明式可复用 menubar 组件族）

菜单改用**声明式 menubar 组件族**（不依赖 actions DSL 合成）：

```at
menubar {
    menubar-menu (value: "file") {
        menubar-trigger "文件"
        menubar-content {
            menubar-item (title: "新建", icon: "file-plus", shortcut: "Ctrl+N") { onclick: .ActNew }
            menubar-separator
            menubar-checkbox-item (title: "切换 Console", checked: .console_open) { onclick: .ActConsole }
        }
    }
}
```

- VM 端 lowering 到公共 Popover 原语（BottomStart + MENUBAR_OPEN 开合注册表）；
  Vue 端直出 shadcn Menubar 组件树——两端同语义。
- item 支持 `title/icon/shortcut`、`checked`/`enabled` 表达式（实时求值）与
  `onclick`；`menubar-separator` 横向通栏。
- `menubar {}` **空标签**保持原 actions DSL 合成语义（向后兼容）；actions 块
  仍负责快捷键三源绑定。

## 公开对比表

> 战略 §5 指定表位（M4 关键产出之三——竞品侧先行半件，PLAN-020）。
> 本节表格由 `tools/compare/render_table.py` 数据驱动生成：
> **手改禁则**——复跑生成器再提交（`--check` 断言复现一致）。

<!-- COMPARE-TABLE:BEGIN（tools/compare/render_table.py 生成——禁手改） -->
### 公开对比表（竞品侧先行件——PLAN-020）

同机测量（数据驱动生成，下方区间禁手改；方法论/计时点定义/通道结论见[tools/compare/METHODOLOGY.md](../../../tools/compare/METHODOLOGY.md)）。**可复现三要素**：每数字附 {版本钉版, 环境指纹, 跑谱+离散}（JSONL 在 `tools/compare/results/` 入仓）。**语义注记（直比禁则）**：各对象 t_ready 判据不同——VS Code=renderer RSS 平台（文本模型物化）、Zed=首帧渲染（rope 视口惰性装载，非全量）、BC5=diff 结果产出、auto-edit open=全量装载完成（BENCH 标记包夹）——跨对象数字不可径直排序，语义列随行。

环境：Windows 11 build 10.0.26200 · Visus · 20 核 · 31.8GB（JSONL 头行含全指纹）

| 指标（档） | 计时语义 | VS Code | Zed | Notepad++ | Beyond Compare 5 | auto-edit（本仓） |
|---|---|---|---|---|---|---|
| 打开 5 MB | 各对象 t_ready（语义列同左口径） | 4,289.1 ms（N=4，4,256.3–4,340.8） | 296.0 ms（N=4，272.6–310.0） | pending（未装——Q-1） | —（diff 对象不适用） | —（无同档在档谱） |
| 打开 100 MB | VS Code=RSS 物化；Zed=首帧（rope 惰性）；本仓=全量装载 | 4,677.7 ms（N=4，4,621.4–4,718.5） | 295.6 ms（N=4，275.4–310.3） | pending（未装——Q-1） | —（diff 对象不适用） | **841.0 ms**〔锚点·VM 形态——非 L2〕；38.2 ms〔产物面·last-good 基面——非 L2〕；**863.2 ms**〔**L2 直拉判定·armed PASS——硬门禁正式判定绿**——N=4，862.7–889.5〕 |
| diff 100 MB（文件对） | BC=report 产出；本仓=diff 端点全链墙钟 （022 起=窗口形判定，全量对照在档） | —（未测） | —（未测） | — | 123,279.8 ms（N=4，119,849.6–126,246.9） | **1,906.0 ms**〔release 全链判定先例（016，仅限 diff）〕；5,183.2 ms〔**L2 直拉判定·armed FAIL（记录性）——归因随行**——N=3，4,985.8–5,412.4〕；**784.8 ms**〔**L2 直拉判定·armed PASS——硬门禁正式判定绿**——N=4，756.6–928.8〕 |
| 滚动帧率 | 各对象=编辑器滚动帧率（语义随行：本仓=present 频率采样，面板率×0.9 判据——PLAN-022 协议在档） | pending（未测——020 Q-2 捕获自动化双缺陷） | pending（未测——020 Q-2 同） | pending（未装——Q-1） | —（diff 对象不适用） | 8.0 fps〔**L2 直拉判定·armed FAIL（首基线锚点）——归因随行**——窗 2,995 ms vs 阈 54.0〕；7.0 fps〔**L2 直拉判定·armed FAIL（首基线锚点）——归因随行**——窗 2,840 ms vs 阈 54.0〕 |

Notepad++ 缺位=安装属用户面（PLAN-020 §10 Q-1），装后 harness 补跑即得列（通道与 VS Code 同形）。**M4 收口口径（PLAN-024 Q-3 默认）**：竞品列完整性=对比表后续补列域，**非里程碑判定门——v0.1-M4 tag 不等待 NP++**（三家竞品实数已足表位成立；2026-10-02 探测四路全空=未装在案）。**我方 L2 正式列=PLAN-021 直拉判定谱**（steady/open——armed 判定随格；diff 行=PLAN-022 窗口形清偿重判 PASS+021 全量形 FAIL 对照并陈；scroll 行=PLAN-022 首判 FAIL+PLAN-024 重判 FAIL 并陈——725 帧管线增量后同机复判，中位改善而 S5 残差[layout/shaping/draw]维持红，归因回执在档；未入表行 warm/idle 判定谱=budgets.json validity）。锚点/产物面数字不冒领（018 分层纪律表内延伸）。发布动作（对外宣传/链接分发）=数字齐后另行；本节=战略 §5 指定表位。
<!-- COMPARE-TABLE:END -->
