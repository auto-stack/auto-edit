---
plan_id: PLAN-008
status: execution_done
feature_name: m2-utf8-eol-byte-fidelity（M2-01：UTF-8 面 + 行尾语义——打开到保存的文件字节保真）
author: [zhaopuming]
created_at: 2026-09-22T19:00:00+08:00
updated_at: 2026-09-22T21:05:00+08:00
plan_revision: 1
current_step: 7
total_steps: 7
supersedes_spec_components: []
new_spec_components:
  - "docs/specs/modules/editor-store.md#SD-01（tab 字节保真元数据 + 装载/save 协议增补节）"
  - "docs/specs/modules/back-api.md#SD-02（端点计数勘正 + IO 字节语义节）"
  - "docs/specs/00-overview.md#SD-03（M2 面开篇注记 + 兄弟仓 Q1 裁定摘要）"
  - "docs/strategy/002-north-star-v2.md#SD-04（补注十——Q1 裁定，追加不回改）"
touched_goals: []
---

# [PLAN-008] M2-01：UTF-8 面 + 行尾语义（文件字节保真）

## 0. 变更摘要

M2（Notepad++ 对位，战略 §2.2）首件：**打开→编辑→保存链路的字节保真契约**首次
成文并落测——① UTF-8 面：BOM 形态保留（含/不含均往返保真）+ 非法 UTF-8 无损
兜底（提示 + 只读 + 保存拦截，绝不静默转码落盘）；② 行尾语义：CRLF/LF/CR
识别、状态栏显示、转换命令、保存保留原形态。核心洞察：**BOM 与 EOL 在 str
字符域即可解**（U+FEFF 前缀字符 / \r\n 字符替换），预期零新 back 端点、零
内核改动；唯一预期上游件=非法 UTF-8 的替换符查看（lossy 读端点，登记不实做）。
附带两件规范动作：**Q1 裁定战略落账（补注十）** + upstream §10 增补。
前置：M1 全收官（tag `v0.1-M1` @ ceaeaad，账本 P004-1..P007-1），无未收账。

## 1. 目标

- **G-1 BOM 保真**：BOM 文件打开后编辑器正文无 BOM 字符、tab 记
  `bom=true`、保存后磁盘首三字节 EF BB BF 保留；无 BOM 文件保存不引入 BOM。
- **G-2 EOL 保真**：CRLF/LF 文件各自打开→编辑→保存，磁盘行尾形态字节级
  保留；状态栏显示行尾形态。
- **G-3 EOL 识别与转换**：混合行尾识别为 mixed（状态栏如实显示）；转换
  命令（转 CRLF / 转 LF / 转 CR）生效——转换后磁盘全目标形态 + 元数据更新。
- **G-4 非法 UTF-8 无损兜底**：打开非法 UTF-8 文件不再静默空 tab——错误
  提示（tab 标题/状态栏）+ 只读态 + save 拦截；原文件字节零触碰（哈希
  断言）。替换符查看（U+FFFD 渲染）为上游 lossy 端点 want，本期非目标。
- **G-5 规范与战略落账**：editor-store/back-api 模块册字节保真节 + 战略
  补注十（Q1 裁定原文）+ upstream §10 登记。

### 非目标

- 查找替换 / find-in-files（M2 后续件候选）。
- 会话恢复（热启动 ≤120ms 懒装载——M2 后续件）。
- 大文件模式（>50MB 关折行/懒语法/分块解码——独立件）。
- GBK/GB18030 传统编码（战略 §2.2 明确非目标）。
- 替换符查看 / 二进制只读视图的完整形态（依赖上游 lossy 读端点）。
- auto-lang 侧任何改动（上游 want 走 docs/upstream 供料登记）。

## 2. 架构方案

分层落点（依 T-00 勘定微调，下为预判形态）：

| 面 | 现状 | 本期形态 | 依据 |
|---|---|---|---|
| BOM | 内核无处理（a2r_std/vm stdlib grep 无 strip_bom/FEFF 命中）；U+FEFF 随正文进编辑器 | 装载链首块探测 U+FEFF 前缀字符→剥离+`bom=true` 元数据；save 位回写前缀 | BOM 在 str 域即普通字符，.at 层完备 |
| EOL 识别 | 无 | 装载后单趟扫描（现单块直载形态下 O(全文) 一次，同装载量级）→`eol: "crlf"/"lf"/"cr"/"mixed"` | store 派生标量惯例（handler 重算） |
| EOL 保留 | 未知 core 是否规范化（T-00③④勘） | 若 core 保留：零动作；若规范化：save 位按 `eol` 元数据重写（瞬态 O(n)，同 save 全文读口径） | 混合保真若需内核→上游 want + 本期降级（§10） |
| EOL 转换 | 无 | actions DSL 三命令→store handler 全文重写；**检测器白名单显式扩**（见下） | 全量读检测器铁律 |
| 非法 UTF-8 | from_utf8 err→envelope `total:-1`→静默空 tab（editor-store.md 装载协议第 3 条） | 错误分支升级：错误提示 tab（标题后缀/状态栏标注）+`readonly=true`+save 拦截 | 无损=不触碰字节；替换符查看=上游 lossy want |
| back 面 | 七端点（read_text_range 为 PLAN-007 增） | 预期零新端点 | BOM/EOL 皆 front 字符域 |
| 双轨 | vue 经 HTTP 同 back | 语义天然一致；矩阵主面=vm 轨（vue 装载位断点在案，不扩面） | upstream §10 vue 673 端点缺口 |

**检测器口径（关键约束）**：tools/bench「编辑路径全量读检测器」白名单现为
ActSave/QuitSaveClose 两 save 位——EOL 转换命令是显式全文操作，白名单扩为
「save 位 + 登记的转换 handler」（白名单仍是封闭集，登记制不变）。

## 3. 技术栈

.at（editor_store.at 装载链/handler、actions DSL）、desktop_mcp 矩阵
（specs/auto-edit/tests/desktop_mcp.py）、python 字节断言（hashlib/前缀字节
检查，fixture 构造）、tools/bench 检测器口径。无新依赖、无新端点（预判）。

## 4. 需求分析与背景调查

- **授权记录**：用户 2026-09-22 指令——M1 收官打 tag（`v0.1-M1` 已落
  ceaeaad）+ 规划 M2 首个计划（本件）；Q1 裁定同日口述原文在案（jade/auto
  两产品长期并存、auto-edit 保持轻量编辑器、jade 向知识库发展、组件尽量
  共用/未来插件级共用）。范围=auto-edit 仓源码与 docs；auto-lang 零改动。
- **规范基线**：docs/specs/modules/editor-store.md（装载协议四件：探针/
  对齐/块位推进/drain-弃；save 过渡位与白名单铁律）、back-api.md（「六
  #[api]」表述已陈旧——实为七端点，PLAN-007 增 read_text_range 未同步
  计数，SD-02 顺带勘正）。
- **代码锚**：`specs/auto-edit/src/back/fsys.at:25-42`（read_all/
  read_range/write_all 直通内建）、`specs/auto-edit/src/back/api.at`
  （七 #[api]）、`specs/auto-edit/src/front/editor_store.at:367-386`
  （AUTO_OPEN_PATH/AUTO_SAVE_PATH 矩阵旁路——新检查组挂点）、
  RunPendingLoad/OpenPath 收口 helper（editor-store.md §收口）。
- **内核现状证据**：供料包 §10 观察 B——`shim_file_read_text_range`
  （auto-lang stdlib.rs:367）与 `a2r_std::fs::read_text_range`（fs.rs:129）
  均 `fs::read` 全量读 + `from_utf8` 全文验证 + 切片，非法字节→err→
  envelope `total:-1`；两文件 grep 无 BOM 处理（2026-09-22 勘，T-00 复核）。
- **矩阵口径**：完成态 50/0（PLAN-007 收官态，45/3 menu-flake 复跑口径
  在案）；判绿=完成态 ≥N/0，N 随新检查组递增。
- **战略验收面原文**（§2.2 前两行）：编码=「UTF-8 为唯一支持面……含/不含
  BOM 读写、保留原 BOM 形态；对非法 UTF-8 文件无损兜底（提示后以替换符
  查看或只读二进制态，绝不静默转码落盘破坏原文件）」；行尾=「CRLF/LF/CR
  识别、状态栏显示、转换命令；保留原行尾保存」。

## 5. 详细设计

### T-00 内核行为勘（决策件，先行） [x]

python 构造字节 fixture × vm merged 实例四组探针：
① BOM 文件（EF BB BF + 正文）装载→`code_editor_delta/text` 回读是否含
U+FEFF；② 非法 UTF-8（含 0xFF 字节）→ read_text/read_text_range 错误
形态实测（err 路径与 envelope 形）；③ CRLF 文件装载→回读行尾形态
（core 规范化与否）；④ CR-only 文件同③。
**产出=§10 决策记录**：每面标注「仓内字符域可解 / 上游 want」+ 依据；
EOL 保留与 mixed 保真的实现路径在此裁定（若 core 规范化且逐行保真需
内核→登记上游 want，本期按主 EOL 语义）。

- **[✅ 已完成]** 探针 `tests/probe_bytefidelity.py`（worktree，Phase A
  back HTTP 形态 + Phase B merged UI 全链 + 磁盘 census/sha256 断言），
  工具链 1893-g00e56202d，报告详 §10 T-00 决策记录。四组结论：① BOM
  无编辑往返 sha256 等值（U+FEFF 驻留 rope，save 直写即保真）；② 非法
  UTF-8 → read_text 静默空串 / range envelope `total:-1` / load_file
  返 -1（loaded_bytes=0），**save 会把原文件清写为 0 字节（实测
  32B→0B，T-04 拦截的危害实锤）**；③ CRLF 无编辑往返保真，**编辑
  （全选 cut→undo）后归一 LF（crlf=3→lf=3 实测，buffer 漏斗丢
  cosmic LineEnding）**；④ CR-only 无编辑往返保真。

### T-01 tab 元数据扩展（editor_store） [x]

`tabs[i]` 增三标量：`bom: bool` / `eol: str`（"crlf"/"lf"/"cr"/"mixed"）/
`readonly: bool`。OpenPath 初始化（readonly=false；错误形分支 T-04 置位）；
RunPendingLoad 首块探测（U+FEFF 前缀剥离→bom=true；行尾扫描→eol）。
矩阵断言面沿用 loaded_bytes 惯例不扩。

- **[✅ 已完成]** worktree 1ce7e52：三标量落 tabs（种子+OpenPath 推入）；
  探测实现为 `ProbeByteMeta(key,path)` 收口 helper——采样窗单次
  `read_text_range(path,0,65536)` + `char_at(0)==65279` 检出 + `edit(0,3,"")`
  rope 剥离 + 前缀字符运行期捕获（语言面无 \u 转义/无码点→字符内建，
  T-00 勘定）；烟测 eol=crlf/mixed 分类正确、非 BOM 前缀字符不误报。

### T-02 save 位保真回写 [x]

ActSave/QuitSaveClose：按 `bom` 回写 U+FEFF 前缀；按 T-00 裁定的 EOL
路径（core 保留=零动作；core 规范化=按 `eol` 元数据重写）。检测器白名单
注释同步（白名单语义不变，转换 handler 登记 T-03 落）。

- **[✅ 已完成]** worktree 1ce7e52：`WriteFidelity(i)` 收口（两 save 位
  改道，`code_editor_text` 唯一读出位）——BOM 前缀回写 + EOL 主形态
  重写（"\r\n"→"\n" 幂等归一再 "\n"→目标，补偿 buffer 编辑即归一 LF）
  + readonly 拦截位（T-04 置位）；白名单扩
  WriteFidelity/EolConvert（bench.py，红证自检 PASS）。探针实证（钉版
  工具链 1914）：BOM/CRLF/LF/CR/mixed 无编辑往返 sha256 全等；BOM/CRLF
  **编辑后**往返 sha256 复原（重写补偿生效）。

### T-03 状态栏显示 + EOL 转换命令 [x]

- 状态栏：line/col/sel 邻位增「eol 形态 / BOM 标记 / 只读标记」显示位
  （store 派生标量，模板只读惯例）。
- actions DSL 三命令：转 CRLF / 转 LF / 转 CR（Edit 菜单「行尾」子组）；
  handler=全文替换重写（code_editor_text 读 + set_text 写——**登记进
  检测器白名单**，登记名=EOL 转换 handler）；mixed 转换前确认弹层
  （alert-dialog 先例）；转换后 `eol` 元数据与状态栏同步。

- **[✅ 已完成]** worktree 0c26484：SyncByteMeta 派生标量
  （eol_label/bom_active/readonly_active——TabActivate/RemoveAt/
  OpenPath/ProbeByteMeta/ActNew 五挂点重算）；状态栏三显示位；编辑
  菜单「行尾」组=menubar-label 平铺三命令（**族无子菜单，偏差在案**）
  + actions 三声明；mixed 确认 alert-dialog（EolConvertRequest 门）；
  EolConvert 本体=code_editor_text 读+归一替换+**结构化 edit(0,字节
  全长) 重写**（T-03 执行期修正：set_text 触 last_external 会被下轮
  绑定推送清场——装载协议②同款防御面；VM str.len()=字节语义勘定）；
  白名单 EolConvert 登记（T-02 已同步）。实证：mixed→LF 经确认弹层
  磁盘零 \r\n + eol_label 同步；crlf→LF/lf→CR 直转落盘字节正确。

### T-04 非法 UTF-8 无损兜底 [x]

装载链错误形分支（envelope `total:-1`）从「静默空 tab」升级：tab 标题
后缀（如「（编码错误-只读）」）+ 状态栏标注 + `readonly=true` + save 位
拦截（提示不落盘）。编辑器禁编面（widget readonly 能力）T-00 顺带勘，
无则本期以 save 拦截 + 显著标注为界（§10 记录边界）。

- **[✅ 已完成]** worktree 0c26484：RunPendingLoad 错误分支（load_file
  返 -1）——exists 前置判定区分「文件缺失」（维持旧静默语义+console
  记录）与「编码错误」（readonly 置位+标题后缀「（编码错误-只读）」+
  状态栏只读标注）；WriteFidelity readonly 拦截（T-02 预埋位）。
  实证：非法 UTF-8 打开→title 后缀+readonly_active=true→save 尝试→
  **磁盘 sha256 打开前后零变**（旧行为 32B→0B 清写的拦截实锤）。

### T-05 矩阵新检查组 + 口径更新 [x]

tests/fixtures/ 五件（BOM_UTF8.txt / CRLF.txt / LF.txt / CR.txt /
INVALID_UTF8.bin——二进制 fixture 注意 git 与 .gitignore 处理）。检查组
四条（desktop_mcp 检查单扩组，AUTO_OPEN_PATH/AUTO_SAVE_PATH 旁路挂点）：
- BOM 往返：打开→编辑→保存→磁盘首三字节 EF BB BF + 正文断言；无 BOM
  文件保存后首三字节非 EF BB BF（负向）。
- EOL 往返：CRLF/LF 各打开→编辑→保存→字节级行尾断言（python 比对）。
- 转换：mixed fixture 打开→转 LF→磁盘零 \r\n + 状态栏断言。
- 兜底：INVALID_UTF8.bin 打开→提示/只读断言→尝试 save→拦截 + 磁盘
  sha256 前后零变。
判绿口径更新（完成态 50/0→54/0 预期，数值执行期定谳）+ README 运行
矩阵行同步。

- **[✅ 已完成]** worktree 6f827c9 + 7f17034：fixtures **六件**（计划
  五件 + MIXED.txt——转换检查的 mixed fixture 计划列举遗漏，补件在案；
  **.gitattributes `fixtures/* -text` 补件**：autocrlf=input 在 checkin
  把 CRLF.txt/MIXED.txt 的 \r\n 归一毁伤（blob od 实勘），renormalize
  后逐字节入库）；T12 检查组七条（BOM 正/负向、CRLF/LF 编辑后字节
  往返、CR 无编辑+label、mixed→LF 确认弹层、非法 UTF-8 兜底+哈希零
  变；每检查独立进程+fixture 临时拷贝保仓内 pristine）；**完成态
  57/0**（50+7，判绿下限 README ≥49→≥56）；检测器**构造性红证三腿
  PASS**（登记绿/摘登记红/复原绿+自检）——暴露并修复扫描器正则不认
  带参 handler 头（`.Name(args) ->`）使白名单登记失效的真缺陷；
  bench 对照行 JSONL 双份在档（见 §10-⑤ 工具链回归观察）。

### T-06 规范落账 [x]

SD-01..04（见规范增量表）+ upstream §10 增补：lossy 读端点 want（期望
形态=read_text_range 增 lossy 形或独立端点，非法→U+FFFD+flag，下游可做
替换符查看与只读二进制态收口）；EOL 内核保真 want（仅当 T-00 判 core
规范化且 mixed 逐行保真需内核）。

- **[✅ 已完成]** worktree 2581972 + c3547e3：SD-01 editor-store.md
  追加「字节保真元数据与装载/save 协议」节；SD-02 back-api.md 七端点
  勘正 + IO 字节语义节；SD-03 00-overview.md M2 开篇注记 + Q1 摘要
  （jade 侧已落账不重复）；SD-04 战略**补注十** Q1 裁定原文（两产品
  并存/组件尽量共用，§9-Q1 收口，交付形态归 Q4 另裁）；upstream 供料
  **§11 PLAN-008 增量**四件（lossy 读 want / EOL LineEnding 漏斗 want /
  快照竞态观察 / 1914-dirty load_file 回归观察）。**vue 轨 build-green
  路由修复**（c3547e3）：ProbeByteMeta 改双轨映射面方法（match_count→
  len+replace 算术、char_at→.str() 字串化）——`regen_vue.py --build`
  exit 0（vue-tsc+vite 绿，装载位断点语义不变）；vm 轨全探针等价复验
  + 矩阵**首跑 57/0** 终态收据。

### 规范增量

| delta_id | add/modify/retire | docs/specs/... target | before/after rule | rationale | acceptance IDs |
|---|---|---|---|---|---|
| SD-01 | add | docs/specs/modules/editor-store.md（追加节） | before：tab 无字节保真元数据，装载错误形=静默空 tab / after：bom/eol/readonly 三标量契约 + 装载探测协议 + save 保真回写 + 错误形兜底语义 | 字节保真契约进规范层（追加+来源注记惯例） | AC-01..04 |
| SD-02 | modify | docs/specs/modules/back-api.md | before：「六 #[api]」 / after：七端点勘正 + IO 字节语义注记（BOM/EOL front 字符域处理，非法 UTF-8 错误形直通） | 计数陈旧勘正 + 本期边界成文 | AC-05 |
| SD-03 | add | docs/specs/00-overview.md（追加节） | before：无 M2 面注记 / after：M2 启动注记 + 兄弟仓 Q1 裁定摘要（两产品并存/组件尽量共用） | M2 开篇与 Q1 摘要进总览 | AC-06 |
| SD-04 | add | docs/strategy/002-north-star-v2.md（追加补注十，不回改） | before：§9-Q1 悬置「建议 M1 结束前裁定」 / after：补注十——Q1 裁定原文（2026-09-22）+ jade 侧已自行落账注记 | 用户裁定原文进战略层（补注九先例） | AC-06 |

## 6. 测试设计

- **矩阵主面**：desktop_mcp 检查单扩四条（T-05），断言域纪律不变（结构/
  文本/磁盘字节，非像素）；字节断言经 python（sha256/前缀/逐行形态比对，
  断言脚本随检查单入库）。
- **回归面**：既有 50 检查零回归（完成态判绿口径，menu-flake 复跑条款
  沿用）。
- **检测器**：白名单扩后构造性红证一次（临时移除登记→检测器红→复原绿）。
- **vue 轨**：back 语义经 HTTP 天然同（零新端点）；装载位断点在案，本件
  不扩 vue 面——记录于 §9 执行记录。
- **bench**：装载预算行对照（BOM/EOL 探测的 O(n) 单趟——预期淹没在装载
  IO 内，JSONL 对照行留证）。

## 7. 验收标准

- **AC-01（BOM 往返）**：BOM fixture 打开→编辑→保存，磁盘首三字节
  EF BB BF 且正文等值；无 BOM fixture 同链路保存不引入 BOM。验证：
  矩阵 BOM 检查（字节断言）双路通过。
- **AC-02（EOL 往返）**：CRLF/LF fixture 各自打开→编辑→保存，磁盘行尾
  形态字节级保留；状态栏显示与磁盘形态一致。验证：矩阵 EOL 检查。
- **AC-03（识别+转换）**：mixed fixture 打开状态栏显示 mixed；转 LF 后
  磁盘零 \r\n、元数据/状态栏更新。验证：矩阵转换检查。
- **AC-04（无损兜底）**：INVALID_UTF8.bin 打开→非空错误提示 tab + 只读
  标注；save 被拦截；磁盘 sha256 打开前后零变。验证：矩阵兜底检查 +
  哈希断言。
- **AC-05（矩阵回归）**：新口径完成态判绿（预期 54/0，数值执行期定谳）；
  旧检查零回归；检测器白名单扩后构造性红证在档。
- **AC-06（Q1 落账）**：strategy 补注十含 Q1 裁定原文与日期；00-overview
  兄弟仓摘要同步；jade 侧已落账注记（勿双边重复）。
- **AC-07（上游登记）**：upstream §10 增补 lossy 读 want（+T-00 裁定衍生
  件）；若 T-00 判零上游件，记录该结论及依据。

## 8. 执行步骤

T-00（决策件，先行）→ T-01 → T-02 ∥ T-03 → T-04 → T-05 → T-06。
依赖：T-02/T-03 依赖 T-00 的 EOL 裁定；T-05 依赖 T-01..04 全落；
T-06 收口。current_step=0。

## 9. 复审记录

- **r0 draft handoff（2026-09-22）**：stage=new；接地完成（back 七端点/
  装载协议/内核证据/矩阵口径实勘）；outcome=pass——授权在案（用户当日
  指令），无阻塞性待决；next=work（/auto-plan:work 起 T-00）。
- **work 进入记录（2026-09-22）**：stage=work；worktree 组建立——
  `D:/autostack/.wt/edit-008/auto-edit`（branch `plan-008-dev`，base
  ceaeaad=main tip）+ 兄弟树 `.wt/edit-008/auto-lang`（detach 94774f2f7
  = auto-lang main tip，bps 供料，零改动）；工具链
  `auto 0.1.0+v0.4.2-1893-g00e56202d`（PATH 解析 auto-lang 主检出
  target/debug）。
- **work 执行记录（2026-09-22）**：工具链中途被并行会话刷新（1893→
  1914-dirty）——按 PLAN-007 保出件惯例钉版
  `.wt/edit-008/auto-008.exe`（1914-g56bfaf1fc-dirty），后续全部跑次
  以钉版为准。vue 轨零扩面（back 语义经 HTTP 天然同，零新端点；装载位
  断点在案），build-green 经 c3547e3 路由修复维持。T-00..T-06 七任务
  全落（证据见各任务节 + §10 决策记录）。

- **work handoff（2026-09-22T21:05）**：stage=work | PLAN-008 | r1 |
  **pass** | code_commit=c3547e3（plan-008-dev tip，7 commits
  1829525..c3547e3） | T-00..T-06 全部 | 证据：矩阵完成态 **57/0**
  （首跑，钉版 1914；判绿下限 ≥56 README 同步）+ 全探针 sha256 全等
  （BOM/CRLF/LF/CR/mixed 无编辑往返、BOM/CRLF 编辑后往返复原、invalid
  32B→32B 拦截）+ 检测器构造性红证三腿 PASS + vue build exit 0 +
  bench 对照 JSONL 双份在档 | blockers=无 | next=review
  （/auto-plan:review；AC-01..07 逐条面见 §7，AC-05 复跑条款沿用，
  AC-07 上游件=upstream §11 四件）

## 10. 待澄清事项

### T-00 决策记录（2026-09-22，探针 probe_bytefidelity.py + 源码静态证据）

**① BOM——仓内字符域可解，零新端点**：
- 装载形态：`code_editor_load_file` = `read_to_string`（U+FEFF 驻留）+
  `core.set_text` → rope 原文含 BOM 字符；无编辑 save 直写即往返保真
  （实测 sha256 等值）。
- 探测：`read_text_range(path, 0, 3)` envelope text=`"\ufeff"`（Phase A
  实测；687 真分块 IO，磁盘窗口 ~7 字节）。
- 剥离：`code_editor_edit(key, 0, 3, "")`——**byte 边界**（U+FEFF=3
  字节，edit 的 is_char_boundary 校验按字节）；`core.edit` 为纯 rope 侧
  拼接（不经 buffer 漏斗，EOL 安全——源码 core/mod.rs:652-687）。
- 回写：save 位按 `bom` 元数据前缀 `"\u{feff}"`。
- 已知角落：BOM+mixed 文件的剥离 edit 触发 rope 拼接（mixed 保形，非
  归一路径）——无损失；undo 栈不含剥离步（rewrite 路径不进 buffer
  undo 史）。

**② EOL 识别——仓内字符域可解（采样窗），零新端点**：
- 探测：装载后 `read_text_range(path, 0, 65536)` 单窗 envelope →
  `json.to_value` 解析 → `Str.match_count` 计数 `\r\n`/`\n`/`\r` →
  crlf/lf/cr/mixed 分类（窗内无行尾→lf）。
- 边界：**全文件 census 禁止**——envelope 全文过 VM 字符串池 = PLAN-007
  观察 B③ 的机构性滞留（100MB→RSS 1315MB 实测在档），采样窗为常数界
  （~3×64KB 池驻留/次开文件）。
- 采样语义：>64KB 文件行尾形态按窗口判定（混合形态在窗后不可见时按
  窗内形态报告）——状态栏显示语义，不影响保真（见③）。

**③ EOL 保留——save 位按元数据重写（core 编辑即归一路径的补偿）**：
- 实测：无编辑往返 CRLF/LF/CR/mixed 全部 sha256 等值（rope 原文保真）；
  **首次 buffer 编辑（键入/cut/paste/undo）即全文归一 LF**——
  `push_delta_from_texts(old=rope, new=buffer_text())` 而 buffer_text =
  `lines.join("\n")` 丢弃 cosmic-text 逐行 LineEnding（core/mod.rs:626/
  787-794，实测 crlf=3→lf=3）。
- 裁定：save 位按 `eol` 元数据重写——crlf：`"\r\n"→"\n"` 幂等归一后
  `"\n"→"\r\n"`；cr 同型；lf/mixed 零动作。无编辑保存=rope 原文直写
  （保真）；编辑后保存=归一 LF 经重写还原主形态。
- **mixed 保真降级（§10 原待决项①收口）**：混合文件编辑后逐行形态
  不可还原（漏斗已归一）——默认处置生效：登记上游 want（buffer_text
  漏斗经 `line.ending()` 重建行尾）+ 本期按主 EOL 语义（mixed 显示
  如实、无编辑保存逐字保真、编辑后保存归一 LF、转换命令统一）。
  与 NP++ 偏差=编辑后混合行尾变 LF（用户可感知度低，不升裁定）。

**④ 非法 UTF-8——T-04 兜底路径与危害实锤**：
- 端点形态（Phase A）：read_text → HTTP 200 `""`（unwrap_or_default
  静默空）；read_text_range → `{"text":"","total":-1,"next_offset":
  null}`；load_file → 返 -1（loaded_bytes=0）。
- **危害实锤（Phase B）**：当前 ActSave 把空编辑器内容直写原路径——
  非法 UTF-8 文件被清写 0 字节（32B→0B 实测）。「绝不静默转码落盘」
  的拦截对象即此路径。
- widget 禁编面（§10 原待决项②收口）：code_editor widget 无 readonly
  能力（ui_gen/源码 grep 零命中）——本期边界=save 拦截 + tab 标题后缀
  + 状态栏标注；NP++「只读二进制态」完整形态随上游 lossy 件收口。

**⑤ 工具链与矩阵基线（T-00 期=1893-g00e56202d；执行期钉版
1914-g56bfaf1fc-dirty，`.wt/edit-008/auto-008.exe` 保出件——auto-lang
主检出被并行会话活跃重建，漂移隔离）**：
- 矩阵非确定 flake 扩散：多轮 48/2、46/3、56/1（T4 ActNew/T3 about/
  T3b fold/T6 paste，失败点逐轮漂移，隔离复现即绿）——菜单 id 漂移/
  焦点类 flake 家族（F-RV6 同族），README menu-flake 复跑条款沿用
  （本件完成态 57/0 为复跑后绿）。
- **1914-dirty 工具链 load_file 回归（新观察，上游件）**：100MB 装载
  RSS 219MB（1855 锚点）→ **1014-1016MB**、时长 <25ms 量级→**4.5-5.7s**
  ——ceaeaad 基线代码同工具链复现（对照 JSONL 对
  `results/20260922-201227`（P008 代码）vs `201301/201338`（基线），
  归因工具链非本件；本件探测链开销在噪声内：1MB 档 51→77ms、
  100MB 档基线反更慢）。疑向上游 rewrite/shaping 路径；登记 upstream
  §10。
- 新观察（登记 upstream §10）：`autoui_snapshot` styled_vtree 克隆可
  短暂命中 computed-events 未填充的退化态（结构在、事件体/PUA 图标
  标注缺失，自愈 <1.5s）——探针/矩阵定位辅助需等事件体出现。

**⑥ 上游件清单（T-06 落 upstream §10 增补）**：
- lossy 读端点 want（计划内原案）：`read_text_range` 增 lossy 形或独立
  端点，非法字节→U+FFFD+flag。
- EOL LineEnding 漏斗 want（T-00 衍生新增）：`buffer_text()`/delta
  漏斗按 cosmic-text `line.ending()` 重建行尾，编辑不归一——下游可
  收口 mixed 逐行保真与「编辑后主形态重写」补偿层的退役。
- 快照 computed-events 竞态（⑤新观察，随查随登）。

### 原待决项（已由 T-00 收口，留档）

- **mixed EOL 保真降级口径**：已裁定（见上③）。
- **只读态边界**：已裁定（见上④）。
