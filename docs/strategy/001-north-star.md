# auto-edit 北极星战略 v1（2026-09-21）

> 状态：**已被 v2 取代**（`002-north-star-v2.md`，2026-09-21 同日五条
> 裁定修订：剥离协作倾向/砍补全与语言服务/编码 UTF-8 唯一/砍 ACP 搭载面
> 收敛工具定位/新增 diff 对打 BC 战场）。本文存档不改，仅作沿革。
> 原注：本文是产品与架构的战略层决策记录；修订走追加（v2/v3），
> 不回改历史版。
> 输入：PLAN-003 交付后的仓库实况 + Zed 架构调研（见 §4 引用）。

---

## 0. 摘要

auto-edit 的北极星：**AI 时代的轻量高性能文本工作台**——人只做 AI 做不好的
事（浏览、精修、审阅、取舍），批量产出交给 agent；编辑器本体为此保持
Notepad++ 级的轻与快。中期（M 线）以可量化的性能预算打赢 Notepad++ 对位；
长期（L 线）以「双面 agent 架构」（编辑器既可被 agent 驱动、也可搭载
agent）成为 AI 原生编辑器，而不是复刻 VSCode 的功能广度。

---

## 1. 产品哲学：AI 时代编辑器的角色反转

### 1.1 为什么"精简"是对的

VSCode 的重量来自它的历史使命：**人是唯一的编辑者**。所以它需要插件市场
补齐人的短板（snippet 体系、重构菜单、格式化器、主题生态、调试器集成）。
AI 时代这个前提反转了：批量编辑、重构、跨文件改动、样板代码——这些恰好
是插件/功能所服务的场景——都交给了 agent。编辑器的职责从"帮人写"收缩为
"让人看、让人挑、让人小修"。

### 1.2 保留清单（人在 AI 时代仍必须自己做的事）

1. **打开任何文件都快** —— 日志、配置、数据文件、上百 MB 的转储；文件级
   而非工程级入口（这是 Notepad++ 的本体，不是 VSCode 的本体）。
2. **小步精修** —— 手比 agent 快的场景：改一个值、挪一行、改错别字。
   键入延迟必须低于感知阈值。
3. **审阅 AI 产出** —— agent 的修改以 diff 到达，人做逐块取舍
   （接受/拒绝/修改后再接受）。这是长期形态的核心交互面。
4. **上下文投喂** —— 选中"给 agent 看什么"（文件/选区/目录），是人的
   判断，不是 agent 的。
5. **即席记录** —— notepad 本体：scratch、临时粘贴、快速笔记。
6. **安全感** —— 会话恢复、自动存盘、checkpoint（"AI 改坏之前长什么样"）。

### 1.3 裁剪清单（明确不做，写进宪法）

- **插件市场 / 第三方扩展生态**。扩展存在的前提（补人的短板）已失效。
  配置面用 config-as-data（键位/外观/行为均为数据文件，已有 OS 键位层
  先例）。远期若确需扩展面，学 Zed 用 WASM 沙箱，但不是承诺。
- **snippet/模板体系、重构工具菜单、可视化设计器**。这些是"agent 的工作"。
- **远程开发/容器/SSH 工作区**。agent 在哪里跑是 agent 侧的事。
- **多人协同编辑**。Zed 的 CRDT 是为多人协作服务的重投入；auto-edit 的
  并发问题是"人 vs agent"，用事务化编辑 + checkpoint 解决，不需要 CRDT。
- **vim 仿真、深度主题市场、IRC 式长尾功能**。Zed 在 vim mode 上投了大量
  资源——那是抢存量用户的打法，不是我们的阶段。

### 1.4 竞争定位

| | Notepad++ | VSCode | Zed | **auto-edit** |
|---|---|---|---|---|
| 启动/轻量 | 好（C++/Win） | 差（Electron） | 中（快但重于 NP++） | **目标：最优** |
| 大文件 | 好 | 差 | 中 | **目标：最优** |
| 平台 | Win only | 全 | 全（2025-10 起 Win 正式支持） | **Win first** |
| 定位轴 | 文件瑞士军刀 | 人写代码的 IDE | 人写代码的 IDE + 协作 | **人机共驾工作台** |
| agent 面 | 无 | 靠插件(Cursor 类分叉) | ACP（Bring Your Own Agent） | **双面原生（§3.1）** |
| 技术栈 | Scintilla/Win32 | Electron/TS | Rust/GPUI | **AutoLang/iced+wgpu/内核 Rust** |

一句话：**不和 Zed 抢"工程 IDE"，和 Notepad++ 抢"文件入口"，用 Zed 的
工程方法（不是它的功能面）做到性能最优，用双面 agent 架构拿 AI 原生身位。**

---

## 2. 中期目标（M 线）：Windows 上替代 Notepad++

"性能最好、启动最快、最流畅"必须是可以**被测出来并公开复现**的，否则只是
口号。M 线的第一件事就是立性能预算与基准设施（§5），然后逐项对位。

### 2.1 性能预算（2026 硬件参照：NVMe + 中端 CPU）

| 指标 | 预算 | 参照 |
|---|---|---|
| 冷启动到可输入（空窗口） | ≤ 80 ms | NP++ 实测约 150–300 ms |
| 热启动（会话恢复，懒装载） | ≤ 120 ms | 恢复 20 tab 不读盘 |
| 打开 100 MB 文本 | ≤ 1 s，滚动不掉帧 | NP++ 约数秒；VSCode 基本不可用 |
| 打开 1 GB 日志 | 可打开（分块/mmap 流式） | 多数编辑器放弃 |
| 键入到上屏 | ≤ 1 帧（16 ms，120 Hz 下 8 ms） | 感知阈值内 |
| 滚动帧率 | 满刷新率（120 Hz 面板跑满） | 内核已做视口切片（Plan 629） |
| 空闲内存 | ≤ 60 MB | NP++ 约 20–50 MB |
| 安装包 | ≤ 15 MB 单 exe，无运行时依赖 | 对位 NP++ 的"绿色" |

预算未达标的功能**不发布**——性能是发布门槛，不是优化项。

### 2.2 Notepad++ 对位功能清单（M 线验收面）

必做（缺一即不算"替代"）：
- [ ] 编码：GBK/GB18030/UTF-8(含 BOM)/UTF-16 自动检测与手动切换——
      **中文 Windows 的生死线**，当前 back `read_all` 无编码语义
- [ ] 行尾：CRLF/LF/CR 识别、状态栏显示、转换命令；保留原行尾保存
- [ ] 查找替换：正则、大小写、整词、转义，跨文件查找（find in files）
- [ ] 会话：退出/崩溃恢复 tab 集+光标+滚动位置（懒装载）
- [ ] 大文件：> 50 MB 进入大文件模式（关折行/懒语法/分块解码）
- [ ] Windows 集成：右键"用 auto-edit 打开"（已有 open_with 接收臂，
      PLAN-016 T-08）、文件关联（pac `opens` 已声明）、任务栏跳转列表
- [ ] 脏标记/退出确认（已有：alert-dialog 三选一，Plan 626 T-06）
- [ ] 多 tab 与最近文件（部分已有）
- [ ] 语法高亮：常见 20 语言起步（内核 tree-sitter 化后解锁，§4.2）

明确不做（NP++ 有但裁掉）：宏录制、FTP/SFTP、插件生态、MD5/哈希工具箱
这类"顺手塞进去"的功能——它们违反 §1.3 宪法。

### 2.3 发布形态

单文件原生 exe（vm 轨已是 iced 原生窗，无 node/electron 依赖）；提供
portable zip + 安装器两种分发；自动更新走后置（M3 再议）。**交付形态上
依赖工具链的独立 exe 打包路径**（§4.4，当前 `auto run` 是解释执行入口，
standalone 打包是 M1 必须澄清的工具链问题）。

---

## 3. 长期目标（L 线）：AI 原生综合编辑器

### 3.1 双面 agent 架构（本产品的差异化核心）

编辑器与 agent 的关系有两个方向，auto-edit **两个都做原生**：

- **Editor-as-server（编辑器被驱动）**：PLAN-003 的 back HTTP API +
  MCP 自动化面（`desktop_mcp.py` 已是雏形）自然长成 agent 驱动协议——
  外部 agent 可以 open/read/**结构化 delta 写**/save/screenshot/查询
  状态。这比 VSCode 的 CDP/扩展 hack 干净得多，且**今天的地基已经存在**。
- **Editor-as-client（编辑器搭载 agent）**：学 Zed 的
  [ACP（Agent Client Protocol）](https://agentclientprotocol.com)——
  JSON-RPC 开放标准，编辑器作为 client 拉起/接入外部 agent
  （Gemini CLI、Goose 等，Zed 2025-08 起 Bring Your Own Agent）。
  agent 面板是编辑器内的第一等公民，而不是插件。

两面合起来：**任何 agent 都能驱动 auto-edit，auto-edit 也能搭载任何
agent**。这是 Cursor/VSCode 分叉做不到的开放性（它们绑定自家 agent），
也是"高性能版 VSCode"在 AI 时代的正确打开方式。

### 3.2 审阅面（review）是长期形态的第一交互

- agent 修改以**结构化 diff**到达：逐 hunk 接受/拒绝/编辑后接受；
- checkpoint 时间线：每次 agent 会话前自动打点，可整体回滚
  （依赖 back 的文件版本化，不需要 CRDT）；
- 上下文投喂交互：把当前选区/文件/目录"交给"当前 agent 会话。

### 3.3 长期仍裁掉的

工程 IDE 面的大部分（调试器集成、测试树、远程容器、多人协作）维持
§1.3 裁剪。长期新增的只有：diff review、agent 面板、工程级搜索
（ripgrep 式）、tree-sitter 多语言高亮、（可能）LSP host——注意
**LSP host 服务于"人读代码"的跳转/悬停，不服务于补全**（补全是 agent
的事）。AutoLang 自身的语言服务生态已在 `auto-vscode`/`auto-zed` 兄弟
仓验证过一遍，可复用其 server。

---

## 4. 架构蓝图

### 4.1 分层（沿用现状，职责收紧）

```
┌────────────────────────────────────────────────┐
│ 应用层 auto-edit（本仓，specs/auto-edit）        │
│  front: store/actions/组件（.at）               │
│  back:  文件/编码/搜索/会话 API（.at，#[api]）   │
├────────────────────────────────────────────────┤
│ 编辑器内核（auto-lang/auto-ui 内，Rust）         │
│  code_editor_core → rope 化 buffer/增量/diff/HL │
├────────────────────────────────────────────────┤
│ 框架层：AutoUI(iced+wgpu) / AutoVM / a2r        │
│ 工具链：auto（编译/运行/生成）                    │
└────────────────────────────────────────────────┘
```

原则：**热路径全部下沉内核（Rust），应用层只做编排**。现状已经如此
（编辑/撤销/光标都在 code_editor_* 内建），这是对的，坚持并深化。
auto-edit 对内核的诉求以「本仓供料 → auto-lang 立上游计划」模式推进
（PLAN-669 先例）。

### 4.2 内核路线（学 Zed 的三课）

Zed 的性能来自三件套，全部可迁移到 code_editor_core：

1. **Rope + 摘要树**（[Zed: Rope & SumTree](https://zed.dev/blog/zed-decoded-rope-sumtree)）：
   平衡树叶存文本块，节点缓存摘要（长度/行数/点-偏移换算），O(log n)
   编辑与定位；Zed 的 SumTree 在 20+ 处复用（显示行、高亮 span）。
   → code_editor_core 当前是行数组形态；大文件目标倒逼 rope 化，
   且**编辑 API 必须从"整文本回读"改为增量 delta**（见 4.3）。
2. **增量一切**：tree-sitter 增量语法解析（Zed 创始人即 tree-sitter
   作者）→ M 线语法高亮与 L 线代码导航共用同一棵增量树；增量搜索索引。
3. **GPU 直渲**（[Zed: GPUI](https://zed.dev/blog/videogame-speed-ui-hardware-rendered-gpui)）：
   Zed 自写 GPUI 是因为当年 Rust 无够快 UI 框架；我们走 iced+wgpu
   已是 GPU 路径，且内核已做"只 shape 可见行"的视口虚拟化（Plan 629）。
   差距在帧预算纪律（§5 的 bench 门禁兜底），不在重写 UI 框架。

### 4.3 应用层去文本化（本仓近期最重要的一刀)

现状 store 每个 tab 持整文件字符串镜像（`tabs[i].src`），cut/paste/undo
后 `code_editor_text()` 全量回读（editor_store.at 中 5 处）；back
`read_text` 也是整串交付。这对大文件是**结构性死罪**——100 MB 文件每击键
复制一次不可接受。目标形态：

- store 只持 **buffer 句柄**（key/path/dirty/元数据），文本本体只活在
  内核 buffer registry；
- 编辑事件携带 **delta**（区间替换），store 消费 delta 维护脏标记，
  不再回读全文；
- back API 增加分块读（offset/limit）与编码参数；
- 大文件模式下 front 甚至不"拥有"全文——视口拉取。

这是 M1 的本仓主计划候选（对上游的配套诉求：delta 事件与增量写 API）。

### 4.4 引擎与进程模型

- **默认 merged（进程内直调）**：性能主路径，维持 PLAN-003 裁定
  （pac 永不写 `api:`）。
- **split（HTTP）**：自动化/agent 驱动与联调形态，天然崩溃隔离。
- **a2r（原生 Rust 编译）**：standalone exe 交付与终极性能的依赖——
  当前 F-R1（server 模板硬编码 `api::Db`）未解，且 app 级转译路径
  （C/ninja）被裁定为脚枪。**M1 需要在 auto-lang 立项澄清独立 exe
  的官方打包路径**（解释执行 + 打包资产，或 a2r 修复），这是 M 线
  交付形态的前置。
- 重活（解析/搜索/大文件 IO）一律出主线程——iced 事件循环只做编排。

### 4.5 配置与扩展策略

- config-as-data：键位（已有 OS 键位层 `%APPDATA%/auto/keymaps`）、
  外观、行为均为数据文件；actions DSL 继续做三源绑定的单一事实。
- 无插件承诺（§1.3）；远期若开放，Zed 的 WASM 沙箱隔离是唯一可接受
  形态（无 Node 运行时、按能力授权）。

---

## 5. 性能文化（M1 立即建立）

- `tools/bench/`：启动（冷/热）、打开文件（1/10/100/512 MB）、键入延迟、
  滚动帧率、内存——机器可复现脚本，结果入仓追踪。
- **CI 门禁**：性能预算回归即红（§2.1 表是断言，不是愿景）。
- 公开对比：README 发布与 NP++/VSCode/Zed 的同机对比表——"最快"只有
  公开可复现才有营销价值（Zed 的 performance 页面先例）。
- 前置修复：desktop_mcp 矩阵的工具链非确定性（F-RV6）必须先稳定，
  否则 bench 与功能矩阵互相污染归因。

---

## 6. 路线图（映射 auto-plan 序列）

| 阶段 | 主题 | 主战场 | 关键产出 |
|---|---|---|---|
| M1 | 地基与测量 | 本仓 + 上游供料 | bench harness + 性能预算门禁；store 去文本化（delta 化）；独立 exe 打包路径澄清（上游）；上游 F-RV6 稳定化 |
| M2 | Notepad++ 对位 | 本仓 | 编码族（GBK 等）；查找替换/find-in-files；会话恢复；大文件模式；行尾语义 |
| M3 | 速度王座与发布 | 本仓 + 工具链 | 预算全绿；installer/portable；公开对比表；语法高亮首批（依赖 tree-sitter 化） |
| L1 | AI 面 v1 | 本仓 + 内核 | diff review（hunk 级取舍）；checkpoint；editor-as-server 的 agent 协议面（back API 扩容 + MCP） |
| L2 | agent 搭载与导航 | 本仓 + 上游 | ACP client（agent 面板）；tree-sitter 全量语言；工程搜索；LSP host（跳转/悬停，非补全） |

节奏纪律：一阶段一主题；每阶段收口走既有 auto-plan 全周期
（new → work → review → merge）。vue 轨七类补件上游化是并行卫生态
（auto-lang 侧计划），不占 M/L 线主线。

---

## 7. 上游依赖与风险登记

| 项 | 性质 | 影响阶段 |
|---|---|---|
| a2r server 模板 F-R1（`api::Db` 硬编码 + 契约空体桩） | 上游修复 | M1（打包路径）、L 线（原生引擎） |
| 矩阵非确定竞态 F-RV6（669/668 后） | 上游修复 | M1（bench 可信度前置） |
| 内核 rope 化 / delta API / tree-sitter / 编码 | 上游新立（本仓供料） | M1–M3 |
| vue 生成器七类补件上游化 | 上游修复（用户已有意向） | 卫生态 |
| 015 `/api/notes/search` 路由遮蔽 F-RV7 | 上游修复（低优先） | 无直接阻塞 |
| 单人节奏 | 项目风险 | 靠 §1.3 裁剪宪法 + 一阶段一主题护scope |
| Zed on Windows 免费且快 | 竞争风险 | 靠"文件入口 + 双面 agent + 轻"差异化，不拼 IDE 功能面 |

---

## 8. 兄弟仓分工

- **auto-lang / auto-ui**：工具链与内核的 canonical 仓；auto-edit 是其
  **旗舰应用 + 内核需求供料方 + 性能标尺**（669 模式放大版）。
- **jade-edit**：同族编辑器（vue 轨先行），其 PLAN-001 换基以 PLAN-003
  交付为前置，现已可开工。战略关系待裁定（见 §9-Q1）。
- **auto-zed / auto-vscode**：AutoLang 语言侧的宿主集成，证明过语言服务
  生态；auto-edit 的 LSP host 可复用其 server 实现。

## 9. 待裁定（open questions）

- **Q1 jade-edit 与 auto-edit 的终局关系**：合并为单产品双轨，还是
  长期并存（jade=web 轻量版 / auto=原生旗舰）？建议 M1 结束前裁定，
  避免双线同质消耗。
- **Q2 独立 exe 技术路径**：解释执行打包 vs a2r 原生化——上游澄清后
  按 M1 结论锁死。
- **Q3 安装器与自动更新**：M3 前议（winget 上架是加分项，不设为硬目标）。

---

*调研参考：[Zed Rope & SumTree](https://zed.dev/blog/zed-decoded-rope-sumtree) ·
[Zed GPUI](https://zed.dev/blog/videogame-speed-ui-hardware-rendered-gpui) ·
[ACP](https://agentclientprotocol.com) ·
[Zed Windows 正式支持（2025-10）](https://zed.dev/blog)*
