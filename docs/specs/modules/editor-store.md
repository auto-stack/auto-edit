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
