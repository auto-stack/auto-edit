# EditorStore 契约（modules/editor-store）

> 来源：src/front/editor_store.at 头注与实现 + PLAN-003/005/007。
> 本册锁定状态语义与不变量；handler 清单以代码为准。

## 状态面（model）

- `tabs`：数组态，每 tab = `{key, title, path, dirty, src}`（Plan 420 P1）。
  `key` 唯一——code_editor registry 按它保存实例。
- 激活/派生标量（active/tab/tab_count/line/col/sel 等）：由 handler 就地
  重算，模板只读（VM view 不能调函数，Plan 402）。
- Console 面板数据、右键菜单坐标锚态、确认弹层开合态均在 store。

## tabs[i].src 数据语义（PLAN-007 改版，硬契约）

**文件 tab 零全文驻留**（PLAN-007 去文本化；PLAN-005 的「初值/外部
重置镜像」契约退役）：文件 tab 的 `src` **恒空串**——正文经分块装载链
直达编辑器 rope，全文永不进 VM 堆。`src` 种子位仅 untitled/演示 tab
用（T-00 裁定的 AC-01 除外位）。`src_active`（激活 tab 初值镜像，
PLAN-005 降格物）随同退役——矩阵内容到达观测面改 `loaded_bytes`
（= 装载完成时最后 envelope 的 total 字节数）。

**装载链协议**（`OpenPath` 公共核 + `RunPendingLoad` Tick 消费，
块 4MB；T-00 四轮探针实证）：

1. **存在性探针**：`code_editor_edit(key, 0, 0, "")` 返 true 才装载
   （空表插入合法形；编辑器 widget 缺席返 false——本 Tick 静默递延，
   下轮重试。视图重建在 handler 外发生，handler 内忙等会死锁）。
2. **装载前对齐**：`code_editor_set_text(key, "")` 对齐 `last_external`
   ——视图构建序为绑定推送**先于** widget 实化（renderer.rs
   `code_editor_set_text(storage_key, value)` → `CodeEditor::new`），
   首建推送落空、`last_external` 留 None，装载后首次重建的 stale 推送
   会**清场**。此刻文本必空，对齐无害，此后绑定推送（content 绑定值
   空串）永续 no-op。注意 set_text 的 VM shim 对 registry false 无差别
   抛错（false 兼指缺席与 guard no-op，后者正是已对齐常见路径）——
   必须 try/catch 吞错。
3. **块位=文件字节偏移**：`read_text_range` envelope 的 `next_offset`
   推进（纯追加态下文件偏移≡编辑器偏移，规避 .at str len 的
   char/byte 歧义）；错误形（envelope `total:-1`）按旧 read_text
   空串语义静默空 tab。
4. **完成即 drain-弃**：`code_editor_delta(key)` 破坏性读、返回值弃
   ——delta 队列无界且 replacement 持块全文拷贝，不弃则装载量级驻留
   吃掉去镜像收益。

**脏态接线（T-00 裁 A）**：沿既有 `SrcChanged`/on 载荷零改动
（`core.edit` 不触发 on_change 回调——装载不踩 SrcChanged/edits，
源码+探针双证）。Tick 侧 delta drain 置 dirty（候选 B，为 M2 会话
恢复预埋增量流）登记后续，非本期。

**save 过渡位**：编辑器全文只在两个 save 位读出（ActSave/
QuitSaveClose）+ `write_text` 落盘（save 时瞬态一份，非驻留）——上游
`code_editor_save(key, path)` 直写端点供料后收口（docs/upstream 登记）。
**违例检测**：`tools/bench` 的"编辑路径全量读检测器"静态检查——
save 位白名单（ActSave/QuitSaveClose）外任何 `code_editor_text` 即红。

## 收口 helper（store handler 间经 store.Xxx() 互调，038/013 先例）

- `RemoveAt`——关闭 tab 的 remove + 索引修补 + 激活态重算（原
  CloseTab/ConfirmClose 各持一份，合一）。
- `SyncCursor`——line/col/sel 三元组读回（原 5 处重复，合一）。
- `OpenPath`——打开文件 tab 公共核（ConsumeOpen/ActOpen/TreeSelect
  三点合一；PLAN-007：零全文 tab + `load_key` 装载递延）。
- `RunPendingLoad`——分块装载消费（PLAN-007：Tick 侧，协议见上节）。

## 数据面边界（PLAN-003 T-02；PLAN-007 扩端点）

全部 IO 经 `use back.api: ws_root, tree, write_text, exists, env_str,
read_text_range` 裸函数直调（merged=进程内 CALL；split/vue=HTTP）。
front 内**禁止** `fs.*`/`File.*`/`Env.get`/`fs.join`（vue 轨拦截面）；
路径拼接走本地字符串（`ws_dir + "/" + id`）。模块名 `fsys` 刻意避与
内建 fs 对象同名（split 扁平化只吃整模块 use）。PLAN-007 增
`read_text_range(path, offset, limit)`（envelope `{text,total,
next_offset}` 直通；`read_text` 全量端点保留供既有消费者）。vue 轨
ts_adapter 不发射 673 内建（`code_editor_edit` 装载位=vue 断点，
docs/upstream 登记）。

## 生命周期约定

- `.Init` 名保留给根 widget 生命周期——store 侧初始化 handler 不得占用
  （现名 `LoadWorkspace`：fs.tree(AUTO_PROJECT_DIR, 4) + json.to_value
  装载真目录树；树节点 id 为相对路径）。
- 脏 tab 关闭与退出/关窗共用确认链（alert-dialog 模态，PLAN-530 族；
  菜单「退出」同入口）。
- 装载时序（PLAN-007）：建 tab（Tick N）→ 视图重建实化编辑器 → 下轮
  Tick（≤800ms，interval 声明期常量不可运行期调）装载——空窗期为
  过渡形态已知项（bench 的 `spawn_to_open_start` 含此等待，`open_ms`
  标记对只包夹纯装载时长）。

## 字节保真元数据与装载/save 协议（PLAN-008，M2-01）

> 来源：PLAN-008（T-00 决策记录 + T-01..T-04）；追加节，PLAN-007 契约
> （零全文 tab/装载协议四件/save 位白名单）不变。

**tabs[i] 三标量**：`bom: bool` / `eol: str`（"crlf"/"lf"/"cr"/"mixed"）/
`readonly: bool`（种子/OpenPath 默认 false/"lf"/false）。状态栏派生标量
`eol_label / bom_active / readonly_active` 由 `SyncByteMeta` 在激活/结构/
元数据变更位（TabActivate/RemoveAt/OpenPath/ProbeByteMeta/ActNew）重算
——模板只读惯例。

**装载探测协议（ProbeByteMeta；RunPendingLoad 装载成功后）**：

1. **采样窗单读**：`read_text_range(path, 0, 65536)` 单窗 envelope
   （687 真分块 IO，磁盘窗口 O(limit)）。**全文件 census 禁止**——envelope
   全文过 VM 字符串池=机构性滞留（PLAN-007 观察 B③：100MB→RSS 1315MB
   实测）；采样窗池驻留常数界 ~3×64KB/次打开。>64KB 文件行尾形态按窗内
   判定（显示语义；字节保真由 save 位重写承载）。
2. **BOM**：窗首字符码点 65279（U+FEFF）→ `bom=true` + 前缀字符运行期
   捕获进 `store.bom_prefix`（语言面无 `\u` 转义、无码点→字符内建，
   T-00 勘定；不变式：任一 tab bom==true ⇒ 非空）+
   `code_editor_edit(key, 0, 3, "")` rope 剥离（byte 边界=EF BB BF；
   core.edit 纯 rope 拼接不经 buffer 漏斗，EOL 安全；delta drain-弃）。
   正文无 BOM 字符（G-1），save 位回写复原。
3. **EOL 分类**：窗内 `Str.match_count` 三计数（"\r\n"/"\n"/"\r"）→
   crlf/lf/cr/mixed（窗内无行尾→lf）。

**save 保真回写（WriteFidelity；ActSave/QuitSaveClose 共用收口，
`code_editor_text` 唯一读出位——检测器白名单登记件）**：按 tab 元数据
包装落盘——`bom` → bom_prefix 前缀回写；`eol`=crlf/cr → 主形态重写
（先 `"\r\n"→"\n"` 幂等归一、lone `"\r"→"\n"`，再 `"\n"→目标`；两步
互抵使无编辑纯形态 rope 无损）；lf/mixed 零动作。重写补偿**buffer 编辑
即归一 LF**：突变漏斗 `push_delta_from_texts(old=rope, new=buffer_text)`
而 buffer_text=`lines.join("\n")` 丢弃 cosmic-text 逐行 LineEnding——
首次键入/cut/paste/undo 即全文 LF（PLAN-008 T-00 实测+源码双证）；
mixed 逐行保真为上游 want（docs/upstream 2026-09 供料 §11）。

**非法 UTF-8 无损兜底（RunPendingLoad 错误形分支）**：load_file 返 -1
且 `exists` → `readonly=true` + 标题后缀「（编码错误-只读）」+ 状态栏
只读标注 + WriteFidelity 拦截落盘（原文件字节零触碰——旧行为会把空
编辑器清写盘，T-00 实测 32B→0B）；文件缺失 → 维持旧静默空 tab 语义 +
console 记录（错误路径专用 exists 前置判定区分两态）。widget 无禁编面
（T-00 勘）——本期边界=save 拦截+显著标注；替换符查看=上游 lossy 读
want。

**行尾转换命令（EolConvert 链，检测器白名单登记件）**：三命令（转
CRLF/LF/CR；编辑菜单「行尾」组=menubar-label 平铺——menubar 族无子
菜单）；mixed 先确认 alert-dialog（EolConvertRequest 门 + EolConfirmGo/
Cancel）；转换本体=code_editor_text 读出 + 归一替换 + **结构化
`edit(0, body.len(), out)` 全文重写**（VM `str.len()`=Rust `s.len()`
字节语义）+ delta drain-弃 + eol 元数据/SyncByteMeta/dirty 同步。
**禁用 handler 侧 `code_editor_set_text` 重写正文**——它触 registry
last_external，下轮视图绑定推送（content=t.src 空串）不等值即清场
（装载协议②同款防御面；PLAN-008 执行期实测教训）。

## 查找替换状态与 effective pattern 拼装（PLAN-009 SD-01，M2-02）

> 来源：PLAN-009 T-01..T-04 交付；拼装协议=T-00 决策记录
> （probe_find.py 23/0 实证）。本节为三消费面（高亮/替换/find-in-files）
> 的语义契约。

**find 状态字段（EditorStore）**：`find_open`（栏开合）/`find_replace_mode`
（替换行展开，Ctrl+H）/`find_query`/`find_replacement`（两输入行）/
`find_case`/`find_word`/`find_regex`（三开关；默认 false/false/false=
字面+不敏感+非整词）/`find_effective`（拼装产出）。
find-in-files 结果态：`fif_results`（条目数组 {file,line,preview}）/
`fif_count`/`fif_truncated`/`fif_open`。

**SyncFindEffective 拼装协议（单一事实源）**：find_query + 三开关 →
find_effective；拼装序固定——①字面模式先转义（`regex_escape` 14 元字符
Str.replace 链，反斜杠最先防二次转义；正则模式直通）→ ②大小写敏感前缀
`(?-i)`（内联旗标覆盖内核 builder `case_insensitive(true)`，T-00② 正案）
→ ③整词首尾 `\b` 锚。空 query → 空串（内核语义=清搜索态、高亮熄灭）。
同一 effective 串驱动 search prop 高亮、back regex_replace、back
search_files 三面——语义一致性由同串保证。

**input 派发协议（T-00④ 定案）**：vm 轨 input 键入文本 = handler 首参
（015-notes SearchChanged(q) 形）——`FindInput(q)`/`FindReplaceInput(r)`
显式赋值 store 字段；框架写回（input_state_map）仅根级字段，store 子树
`.store.X` 不适用；裸 value（无 oninput）对 store 字段不 mint type
handler。视图 `value:` 绑定仅作显示回读（单向）。

**查找高亮/跳转**：code_editor `search: .store.find_effective` Ident 绑定
（T-00① 正案）——eff 变更 → 下轮视图 apply_search diff + 非空首跳（高亮
+光标落首匹配；跳转后 cursor=匹配末位 exclusive）。「下一处」（按钮/F3）
= 内核 `code_editor_find`（光标后下一处、回绕、选区、滚动入视）+
SyncCursor 回读；空 eff/tab_count==0 零动作。

**全部替换（ReplaceAllRequest，检测器白名单第三件显式全文操作）**：
readonly 拦截（WriteFidelity 拦截面复用）→ `code_editor_text` 读出 →
back regex_replace（pattern=find_effective 同串）→ json.to_value 解包 →
count>0 才 `edit(0, len, out)` 全文重写 + delta drain-弃 + dirty +
SyncCursor +「替换 N 处」console 计数。空 query/零匹配零动作。链形态=
EolConvert 复用面（禁 handler 侧 set_text 重写，防 last_external 清场）。

**find-in-files 结果面**：面板内联**根视图**（Plan 449 快照定位约束——
条目点击必须 MCP 可达，组件子树对快照不可见故不用 console_panel 形态）。
搜索打 `.find_effective` 同串（与查找面语义一致）；条目点击 = FifResultClick
→ OpenPath 公共核（同路径已开则激活，TreeSelect 同款遍历）→ pattern 高亮
经 find_effective 天然延续新 tab（首匹配跳转）。

**已知边界**：单处替换/上一处/匹配计数 n/m/goto 行=上游 want
（docs/upstream 2026-09 供料 §12）；Esc 关栏未接（input widget 无
keydown 面，× 按钮为关闭路径）；跨行正则不匹配（内核逐行 find 同口径）。

## 会话持久化与懒恢复（PLAN-010 SD-01，M2-03）

> 来源：PLAN-010 T-01..T-03 交付；恢复协议与 loaded 语义=T-00 决策记录
> （probe_session.py 23/0 实证）。会话=跨进程状态契约；back-api 零端点
> 变更（env_str/read_text/write_text/exists 四件既有复用）。

**会话文件契约**：APPDATA 根 `auto-edit-session.json`（`env_str("APPDATA")`
定位 + 根级落文件——零 mkdir，fs.create_dir 属 back 面；APPDATA 缺席兜底
""=会话链整体禁用，写入挂点与恢复链双重门）。JSON 字段：`ws_dir`（键控
——不匹配即全新启动）/`tabs[]`（仅文件 tab：path/title/cline/ccol；
**untitled 排除**，脏标记与正文永不入会话）/`active`（持久化数组内索引，
-1=激活 tab 为 untitled，恢复按 0 兜底）/`open_count`（防撞号推进）/
`recents[]`（{path,title}）。拼装=front `json_escape` 两字符转义（反斜杠
最先防二次转义）+ `.str()` 整数化（`json.stringify`(1918) 在册但 vue
映射面未证——拼装侧不赌，双轨铁律）；解析=try 门 + `json.to_value` +
`??` 逐字段兜底（损坏 JSON 实测**容忍形**→ws 门/try 门双保险=静默全新
启动，T14.9 回归锚）。

**SessionSave 五挂点（结构变更即时落盘=崩溃恢复底座）**：OpenPath /
RemoveAt / TabActivate / ActNew / **CloseRequest 入口**（退出链三臂——
干净臂直接退出、弹层两臂经确认层退出——共用此单挂点，结构在挂点时已
定型；弹层臂的 WriteFidelity 落盘不改 tab 集，会话保持准确）。写盘先于
Process.exit 的时序由 T-00④/矩阵 T14.5/T14.6 背书。写入频率=结构变更
即时（Q-2 v1 裁定：用户节奏低频、文件 KB 级）。边界如实成文：ActSave
把 untitled tab 升格文件 tab 的路径变更不在五挂点清单（v1 契约面——该
结构变更在下次挂点动作时随写落盘）。

**恢复协议（LoadWorkspace 尾段，bench 标记之后）**：存在门 → try 解析门
→ ws_dir 匹配门（任一不过=静默全新启动，现状零回归）→ tabs 重建（key=
tab-N 顺序推号、title=basename、src 恒空、**loaded=false**、bom/eol/
readonly 默认值——装载时 ProbeByteMeta 重探；缺席/不存在文件条目丢弃）
→ open_count 推进防撞号 → 激活位 + `load_key=active 文件 tab`（仅当
存在；下轮 Tick RunPendingLoad 消费=装载协议②③原样——视图只实化
active 编辑器，**恢复 N tab 只读 1 个文件**）。recents 同源恢复（元素级
防御重建，畸形条目丢弃）。bench 实例 ws 键控自隔离（AUTO_PROJECT_DIR≠
session.ws_dir → 不恢复，steady_start 面零扰动）。

**懒装载协议增补（tabs.loaded 标量）**：`loaded`=「装载完成」——文件 tab
创建位 false（OpenPath）/恢复链位 false；RunPendingLoad 成功分支置 true
（错误形不置位——文件修复后激活可重试）；**TabActivate 触发**：激活
loaded==false 的文件 tab → 置 load_key（path_active 由 TabActivate 联动
写——RunPendingLoad 读 `.path_active` 的协议假设天然满足；编辑器实化前
探针 edit 失败静默递延=协议①）。切回语义=T-00③ 定案 **registry 存留、
切回免重装**（内容留存于编辑器 registry，loaded=true 激活零动作）。
cline/ccol=激活 tab 光标位镜像（SyncCursor 位更新；**持久化但不应用**
——前向兼容位，上游 set-cursor 端点清偿后启用即得光标恢复）。

**recents 契约（最近文件）**：OpenPath 前段维护（去重前移，上限 10 淘尾
）——OpenPath 是全部打开入口的公共核（菜单/树/fif 点击/最近文件四路
同源）；持久化入会话。UI 面=**Explorer 侧栏「最近文件」节**（设计适配
在案：menubar-content 组件内容模型边界——for 不吸收/menubar-label 不
吸收/if 守卫动态条目跨重建不可靠/带参 onclick 实参归零，探针 menu2+
隔离实验实勘，upstream §13 观察；根视图 for+裸循环索引 onclick=fif
结果面板同款已证面）。点击=RecentOpen→RecentOpenAt：已开同路径 tab
激活 / 未开 OpenPath（recents 维护随公共核自带，零重复）。

**检测器口径**：会话链零 `code_editor_text`（结构态/元数据序列化，正文
永不出编辑器）——检测器白名单零变更（对照：009 ReplaceAll=第五件登记）。

**边界（非目标，如实成文）**：脏内容/未保存编辑不恢复（自动存盘/
checkpoint 依赖 back 文件版本化，战略 §3.2 L 线审阅面件）；光标/滚动
恢复应用不启用（无 set-cursor/editor-scroll 端点——docs/upstream §13
want 消费方）；会话恢复开关无 config-as-data 配置面（v1 恒开，配置项列
未来件）；多 workspace 并行会话（v1 单文件 last-wins，ws_dir 键控判匹配
）；tree 展开态/滚动位/fif 结果/查找栏开合等瞬态不恢复（v1 只恢复
tab 集与激活位）。

## 大文件模式（PLAN-013 SD-01，M2-04）

> 来源：PLAN-013 T-01..T-03 交付；探测时点/双阈值/护栏语义=T-00 决策
> 记录（probe_bigfile.py 实证 + 内核静态勘，计划 §10 Q-1..Q-4）。内核
> 零改动（wrap prop/lang plain 白名单/apply_config 热应用皆现役面）。

**模式态与探测协议**：per-tab `big: bool` 标量（阈值 **52428800B=
50MB**，战略 §2.2 原文；≥判 big）。探测位=**RunPendingLoad 装载前门**
（pre-load 形，Q-1 裁定）：`file_size(path)` 一次性（back 第 14 端点，
envelope JSON——**裸 int 返回过 AutoVM HTTP 面=serialize null**，T-00
Phase A 实勘，merged 直调 ✓/split ✗；upstream §16 观察）→ `vsize.size
?? -1`。负值=缺席/IO（跳过模式判定——既有 load_file 错误形承接，零行
为差异）。OpenPath/会话恢复链统一单点（两链 tab 均 loaded=false 建
tab→编辑器空实化（零内容渲染）→Tick 装载；恢复链 big=false 重建、
装载时重探=「重装载即重探」，会话只存 path 天然兼容）。big 置位先于
`load_file`——装载完成渲染时 props 已按模式态走（同 handler 原子性+
apply_config 逐字段 diff 热应用[lang_changed=同 buffer 重建 SyntaxEditor/
wrap_changed=set_wrap，内核 mod.rs apply_config_locked]=首帧即模式态）。

**模式切换链（视图 props）**：big tab → `lang: "plain"`（激活 tab 派生
标量 `lang_active`，SyncByteMeta 重算；Ident 绑定=search prop 已证面）+
`wrap: false` 显式绑定。plain 语义=**跳过**非「延迟」（lang_to_extension
白名单 plain/none/""→None——syntect 高亮跳过+syntax_by_extension 不设；
warm_language 兜底 warm txt=无害常数）。wrap 现状勘定（Q-2）=**恒
false**（内核 builder 默认 view.rs:1921+现视图未绑）——「关折行」项=
零动作注记，显式绑定防内核默认漂移。切换联动=激活 tab 变更→
SyncByteMeta 重算→视图重建（big↔normal 往返无残留；ActNew untitled
化同时清 big/ro_reason）。undo 历史在 lang 切换位重置（内核语义，v1
接受——big 态编辑为小步精修域）。

**命令护栏（全文本三件）**：big 态入口拦截+显式提示（console+状态栏
`big_hint`，绝不静默）——①`ReplaceAllRequest`、②`EolConvertRequest`
（+本体 `EolConvert` 同门=确认链直呼防御）、③`WriteFidelity`（save，
ActSave/QuitSaveClose 双臂同拦）。**readonly 不设**（大文件仍可小步精
修——战略 §1.2 保留清单②；编辑/查找/导航/fif 不受限）；拦截语义=命
令级。实证依据（Q-4，探针 50MB 活体）：全文命令在 2046 工具链可完成
（ReplaceAll 全管线 2.5s/计数精确）——护栏依据=**结构性/战略线**：全
文往返 50MB+ 字符串两次过 VM 池（687 滞留形态；200MB 峰值 RSS
~1.55GB 实测）+工具链漂移（011 实勘 split 49×）+save 唯一路径=全文
VM 往返（直写端点清偿前无正解）。解锁件=上游 `code_editor_save` 直写
端点（§10-2 want 在册，upstream §16 登记）——落地后 big 态 save 解禁，
零 front 改动预期。EolConvert 菜单入口在 menubar-sub（MCP 失明=T12.6
同源已知上游缺——护栏门不可矩阵直驱，门本体在 store 侧成文）。

**超大拒绝位**：**536870912B=512MB**（Q-3 定参；依据=探针 200MB 峰值
RSS ~1.55GB 实测外推 512MB→~4GB 不可控域+687 锚交叉）。`file_size >
512MB` → **拒绝装载**（零 rope 分配——pre 形实质优势）：错误形 tab
（readonly 置位+`ro_reason:"big"`+标题后缀「超大文件-拒绝装载」+
loaded=true 终结装载链[防 TabActivate 懒装载重触发]）+console 注记
（含架构阻塞指向）。readonly 必须保留：空 rope+WriteFidelity 无栏=原
文件被清写盘成 0B（008 T-04 同根拦截面）。状态栏只读标签派生化
`readonly_label`（编码错误/超大拒绝两形态分立）。1GB 线（战略 §2.1
预算行）在拒绝位之上=两段式成文：**拒绝位之内 50MB+ 可开（模式态），
之外拒绝（真分块 IO=上游阻塞，upstream §16）**；分块解码/1GB 可打开
=非目标（v1 纪律）。

**会话恢复兼容**：会话只存 path——重装载即重探（恢复链 big=false，
RunPendingLoad 探测门统一置位）；拒绝形 tab 的 loaded=true 语义=装载
链已终结（拒绝），恢复后激活不重触发。

**检测器口径**：白名单五件封闭集**零变更**（护栏=前置门，不动读出
位；探测链走 back file_size，零 `code_editor_text` 新面）。
