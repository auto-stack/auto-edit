# auto-edit → auto-lang 上游供料包：M4 性能解阻（2026-09-29）

> 来源：PLAN-018（M4-01 性能预算门开篇——M1「供料先行+本仓并行」
> 开篇模式复用，战略补注三(c)；路线图 §6 M4「速度王座与发布」四产出
> 全部门控于上游解阻或用户裁定，本包=解阻件归口）。
> 战略依据 `docs/strategy/002-north-star-v2.md`：§2.1（性能预算表
> 「预算未达标不发布」M4 生效）/§4.2（内核路线 tree-sitter 化）/
> §5（测量模式阶梯）/§6（M4 关键产出）。
> 证据基：auto-edit main@f4e34c1（worktree plan-018-dev 执行）；auto-lang
> master@5bb3f53be（组 worktree 钉版，工具链 v0.4.2-2205-g5bb3f53be）。
> 勘定报告：auto-edit `specs/auto-edit/tests/evidence-p018-survey.md`
> （2026-09-29 实勘——本包 §1 三类缺口的逐行证据在彼）。
> 上游实勘（2026-09-29 @5bb3f53be）：ui_gen/rust.rs
> `vm_builtin_host_call` 单源表 19 内建 18 已映射（code_editor_edit
> L9716 实锚）、trans/rust.rs `File.read_text_range` 臂在（L6596，
> PLAN-687）；`a2r 探针`（auto build -r rust）exit 3——生成物三类
> 缺口见 §1。语法面 syntect 5/two-face 0.4（code-editor feature，
> Cargo.toml:69/255-257）、零 tree-sitter。plan046/047（memo/keyed
> 渲染域+依赖录制）在途——与本包无路径冲突（供④ 渲染性能域协同
> 注记见 §4）。

## 1. a2r 生成缺口残余清偿（L2 主形态解阻——三子件）

- **诉求**：`auto build -r rust` 生成物零占位零裸调（exit 0 机读
  判据）。三类：
  - **G-C `code_editor_delta` ui_gen 臂**（唯一名字解析错 E0425，
    生成物 3 裸调用点）：`vm_builtin_host_call` 单源表增
    `"code_editor_delta"` 臂，镜像 `code_editor_edit` 臂同款直调
    形态 `auto_lang::ui::code_editor::code_editor_delta(&({a0}))`
    （返回 String——VM shim native.rs:709 同源语义：destructive
    read，Plan 673 §4.2；未注册键错误形同源）。
  - **G-B try/catch 块 trans 臂**（生成物 4 处 `/* unhandled
    stmt */`）：`.at` try/catch 映射 Rust 形态（异常兜底走 catch
    块）。实例=会话恢复链 try（editor_store.at:499——PLAN-010）/
    file_size 装载探测 try（:897——PLAN-013）/badge probe try ×2
    （PLAN-017）。
  - **G-A envelope 成员访问投影**（生成物 17 行 `/* expr */`）：
    `json.to_value` 结果的成员访问 `v.field ?? default` 臂
    （serde_json::Value 字段读取+缺省回退）。实例=diff envelope
    全族 `v.err ?? ""`/`v.hunks ?? []`/`r.lo ?? 0`/`h.a1 ?? 0`
    （011/015/016/017 diff 视图面）。
- **动机**：L2 主形态（a2r release 直拉——唯一预算效力形态，战略
  §5）自 PLAN-007 装载链引入起 blocked（perf README 在册）；上游
  已分批清偿大半（PLAN-687 read_text_range trans 臂/code_editor_edit
  ui_gen 臂等 18/19 内建），残余三类为全预算行正式判定的最后一公里：
  steady_start/warm_start/open_100mb/open_1gb/idle_mem 的 L2 断言化、
  diff_100mb 的 L2 硬门禁收口（现为 stage_diff server 侧记账形态）
  全部以 L2 链打通为前提。「预算未达标不发布」（M4 生效）需要可判。
- **期望形态**：三类清偿后 `auto build -r rust` exit 0；生成物
  grep 零 `/* expr */`/`/* unhandled stmt */`/裸 `code_editor_delta`。
  语义同源纪律：G-C 直调 core 实现（不绕 VM shim）；G-A/G-B 与
  VM 轨语义逐形对拍（envelope 缺省=?? 右值；try 异常=catch 块承接）。
- **验收形态建议**：上游单测（三类各构造用例：try 成功/异常两臂、
  envelope 嵌套成员+缺省、delta 未注册键错误形）；下游验收=auto-edit
  `perf.py a2r` exit 0 + L2 锚点补跑（bench `--mode l2` 全链）——
  装载链（G-B×G-C）与 diff 视图面（G-A）两域矩阵回归由下游承担。

## 2. 内核帧时间戳插桩（type_latency/scroll_fps 测量解锁）

- **诉求**：内核提供帧生命周期观测通道（最小面）：帧开始/呈现完成
  时间戳可从 .at 层读到（BENCH 标记族同款 stdout 形态或 .at 可调
  只读内建），或等价的事件订阅点。
- **动机**：战略 §2.1 两行测量面缺通道（PLAN-005 T-03 勘无——.at
  层无帧时间戳观测通道，框架合成生命周期仅 Init/Tick/CloseRequest
  三者，"rendered" 标记仅存在于 MCP 快照面）：type_latency（键入到
  上屏 ≤1 帧）与 scroll_fps（满刷新率）无法测量；steady_start 首帧
  段分解（现=spawn→ws_loaded 三段，首帧段缺席）同需此件。
- **期望形态**：观测零行为差异（未订阅/未标记时无额外开销——
  PLAN-005 AUTO_BENCH 门控纪律同款）；时间源单调、可换算毫秒；
  .at 侧可达（VM 与 a2r 两轨同源——G-A/G-B 清偿后 a2r 轨可达性
  同步成立）。
- **验收形态建议**：上游探针（标记到达序+开销测量）；下游
  bench type_latency/scroll_fps 档建立+budgets 两行断言化（供②
  排队注记位现挂 m4-perf-unblock-supply）。

## 3. 大文件实例 UI 硬卡死回归清偿（T17 blocked 族）

- **诉求**：清偿 2046→83c4621b5 窗引入的大文件实例 UI 硬卡死回归
  （m1-supply §17 在册：二分边界+消费面全摘实证非 701/非下游面）。
  **2026-09-29 现势更新（PLAN-018 执行期）**：下游全矩阵单跑
  （v0.4.2-2205 release 工具链）T17.2/17.3/17.8 **三检查全绿**
  （136/1，唯一败=T17.4 轮换 flake 在录成员）——**疑似已解阻**
  （归因候选=上游 plan046/047 渲染域窗/release 工具链形态；单跑
  不定案）。本件定性改「确认复核件」：上游确认清偿 commit（或
  勘定回归已消）+下游多跑复核持续绿后本件核销；若复现则原诉求
  恢复。
- **动机**：下游矩阵 T17.2/17.3/17.8 三检查 blocked（017 执行谱
  133/4 已知族全中——README PLAN-017 口径节）；大文件交互面（打开
  50MB+ 实例的 UI 响应）=M4 open_100mb「滚动不掉帧」半行的前置面；
  清偿后自动复绿（014 口径原文）。
- **期望形态**：大文件实例打开→交互（滚动/激活切换）不冻结 UI
  线程；卡死族三检查复绿。
- **验收形态建议**：上游最小复现探针（50MB fixture 实例交互序列）；
  下游矩阵 T17 族自动复绿即验收（判绿口径恢复全检查计入）。

## 4. tree-sitter 首批（语法高亮 M4 件——勘定+实施两段式）

- **诉求**：内核语法高亮面 tree-sitter 化首批（常见 20 语言起步）
  ——§4.2 内核路线（学 Zed 三课）。**建议两段式**：先勘定件
  （语言集定界/管线选型[tree-sitter crate 版本与 grammar 分发形]/
  与 syntect 共存策略[迁移期双轨或切换]），实施件另立。
- **动机**：M4 产出「语法高亮首批」；M3 收口注记（overview M3
  第五件）尾行=「剩余语法高亮联动=M4 首批 tree-sitter——供料驱动」。
  现势=code-editor feature 全 syntect 5/two-face 0.4（Cargo.toml
  实勘）、零 tree-sitter 依赖。供①/供③/供② 解阻前不阻塞——
  最大件先勘定后供。
- **期望形态**：增量高亮（编辑路径增量重高亮，非全量重算——
  rope 快照隔离消费形态同 diff 后台任务先例）；大文件模式 big 态
  旁路语义保持（plain 臂不受扰）；体积影响评估（two-face 全语言
  内嵌集退役=installer 预算行联动收益，Q2/Q3 材料注记）。
- **验收形态建议**：上游基准（首批语言集高亮正确性+增量重高亮
  延迟）；下游矩阵语法面回归+bench 大文件装载墙钟不回退（plain
  旁路域不变）。
- **协同注记**：plan046/047（memo/keyed 渲染域+依赖录制）在途——
  高亮重算面与其缓存域正交（高亮=文本域派生，memo=视图域），无
  路径冲突；tree-sitter 增量面若消费 memo 依赖录制通道（047 基建）
  属实施件选型空间，勘定件注记即可。

---

## 5. two-face 语法集子集/lazy 装载 feature 粒度（installer 瘦身第二段——PLAN-019 条件触发）

- **诉求**：code-editor 的 syntect/two-face 高亮面获得**语法集子集或
  lazy 装载 feature 粒度**——common 集起步（类似供④ tree-sitter
  「常见 20 语言」口径），全量集退为 opt-in feature。
- **触发证据（PLAN-019 T-00 构成精测，2026-09-29）**：portable 产物
  39.4MB 基线的 **.rdata 数据节 12.4MB**——two-face 全量语法定义集
  内嵌为主体（`two_face::syntax::extra_no_newlines()` 全量构造实锚
  auto-lang `crates/auto-lang/src/ui/code_editor/core/highlight.rs:135`，
  @5bb3f53be 复核在位）；two-face .text 仅 ~65KB——**重量全在数据节**，
  本仓 profile/feature 通道不可达（终态手段集 29.8MB / 门控组合实测
  16.46MB 距 ≤15MB 门 714KB——installer 行第二段收口的定量依据，
  budgets.json installer 行 validity 同源）。
- **期望形态**：子集 feature（如 `syntax-common`）或运行时按需装载
  （lazy 反序列化）；大文件 big 态 plain 旁路臂语义保持（013 定参
  域不受扰）；与 code-editor feature 的启用关系沿现状（ui-iced 路径
  不回退）。
- **验收形态建议**：尺寸差值（two-face 全量→common 的产物数据节差）+
  矩阵语法面回归（高亮正确性抽查档）+ code_editor 装载链不回退。
- **与供④ 协同（want 生命周期注记）**：供④ tree-sitter 化落地后
  syntect/two-face 整体退役——本 want 的生命周期可能止于供④（子集
  粒度若先行落地，其价值=供④ 交付前的过渡期瘦身；两件不冲突，
  先后由上游排程）。

**优先级建议（auto-edit 视角）**：**§1 最先**（L2 主形态解阻——
全预算行正式判定前提；三子件可分批，G-C 最小先落）→ §3（交互面
blocked 族清偿，下游判绿口径恢复全检查）→ §2（两行测量解锁+首帧
分解补全）→ §4（最大件，勘定先行两段式）→ §5（installer 第二段，
随供④/用户裁定排程——PLAN-019 条件触发件）。

**回执方式**：同 M1/diff-engine 两包——各件落地落上游 plan 后，
auto-edit 侧以零改动或最小改动复验解阻（669 先例；供① 回执=
`perf.py a2r` exit 0 + L2 锚点补跑；供③ 回执=矩阵 T17 族复绿），
并在本仓 budgets.json 对应行 unlock/validity 注记更新（§2.1 预算
表 M4 收口路径）。
