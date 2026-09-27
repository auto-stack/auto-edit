# auto-edit → auto-lang 上游供料包：diff 引擎（M3，2026-09-23）

> 来源：用户 2026-09-23 裁定「按推荐来」=**供料先行**（diff 提前路径
> 第一步——上游前置时间最长，M1「供料包立即发、本仓并行干别的」成功
> 模式复用，战略补注三(c)；§8 亦早注「diff 引擎供料是下一件」）。
> 战略依据 `docs/strategy/002-north-star-v2.md`：§2.3（M3 验收面）/
> §2.1（100MB diff ≤2s 预算行，解锁条件=diff 引擎）/§4.1（diff 引擎入
> 内核，文件比对与 agent 审阅面共用同一引擎）/§4.2（增量一切——diff
> 增量重比）/§5（bench diff 计时 1/10/100MB）。
> M1 供料包及后续下游计划增量见 `2026-09-m1-supply.md`（本件独立成包，
> 不占其节号；下游 PLAN 增量继续追加该文件）。
> 证据基：auto-lang 1914 主检出；auto-edit main@fda9cdb（PLAN-009 在途
> plan-009-dev d6a2a9f 并行——本供料件不涉其路径，零 merge 摩擦）。
> 上游实勘（2026-09-23）：**auto-lang 现无任何 diff 引擎**——
> Cargo.toml 无 similar/imara-diff 类依赖，crates 全树无 diff 模块；
> M3 属全新立项（本仓供料，上游走自己的 plan 流程）。

## 1. diff 引擎本体（行级 histogram/patience + 行内字符级）

- **诉求**：内核新增 diff 计算模块（建议 `crates/auto-lang/src/ui/`
  code_editor 同级或独立 diff/ 目录）：**行级 diff**（histogram 优先、
  patience 备选——对齐行移动识别，语义贴近 Beyond Compare 使用感，
  §2.3 算法行原文）+ **行内字符级 refinement**（hunk 内逐行字符区间
  对，供行内高亮）。
- **动机**：§2.1 预算行「100 MB 文件全量 diff 出结果 ≤2s（BC 同量级或
  更快）」；§4.1 分层——热路径下沉内核 Rust，应用层只编排；auto-edit
  侧 M3 全部视图件（并排/内联两视图、hunk 导航、双栏同步滚动、差异侧
  直接编辑）均只是该引擎的编排面，不在供料件内——但引擎 API 需支撑
  其所需（区间限定查询、编辑后重比，见 §2）。
- **期望形态**：纯计算 API（与应用层解耦）：输入=两文本（&str 或两
  rope snapshot/行区间），输出=结构化 diff（hunks：行级区间对 + 行内
  字符级区间对；确定性输出）；支持**区间限定调用**（下游滚动联动/
  hunk 惰性计算的基础）。
- **验收形态建议**：上游单测基准（fixture 族：纯增/纯删/改/行移动/
  空文件/单行大文件/全等）；auto-edit 矩阵为下游验收面；bench diff
  计时框架为性能验收面。

## 2. rope 摘要扩展：子树内容哈希（增量重比地基；可独立先行交付）

- **诉求**：`core/rope.rs` 节点摘要（现仅 chars/newlines 等计量字段）
  增**子树内容哈希**（或等价摘要量），使「两 rope 子树全等」判定达
  O(1)/O(log n)；配套查询面（如 `subtree_equal(a, b)` / 区间哈希）。
- **动机**：§2.3「差异侧直接编辑（编辑后即时重比）」+ §4.2「增量一切：
  diff 增量重比」——两版 rope 结构共享，公共子树=文本全等段；摘要带
  哈希后，公共前后缀与全等大块剪枝 O(log n) 级，只对真差异区跑
  histogram。这是 rope 相对扁平结构的独有算法红利，也是 100MB 预算行
  的现实路径（先剪后算）。
- **证据（下游现状实勘，2026-09-23）**：
  `crates/auto-lang/src/ui/code_editor/core/rope.rs` 的 Rope API 面
  已齐（snapshot/len_bytes/len_chars/line_count/byte_to_point/
  point_to_byte/line_start_byte/line_end_byte/slice_bytes/line/lines，
  L465-524）——快照（Arc 持久化，Send+Sync）与区间访问面即取即用；
  但节点摘要**无内容哈希**（Node::Leaf{text, chars, newlines}，L40-42
  实勘），全等判定现为内容比较 O(区间长)。快照隔离模式内核已现役
  （core/mod.rs find_next 于 rope snapshot 上跑，Plan 673 T-05 先例）
  ——diff 后台任务同款消费形态。
- **期望形态**：摘要字段扩展 + **增量维护**（insert/delete/replace 的
  摘要更新不降级编辑路径——现 O(log n) 编辑复杂度维持）；**本件不依赖
  §1，可独立先行交付**（引擎未定时地基先落，其他消费面同受益）。
- **验收形态建议**：编辑路径基准不回退（对照现有 rope 单测族）；全等
  判定正确性（构造共享/分叉 snapshot 对照用例）。

## 3. 大文件分块并行

- **诉求**：100MB 级全量 diff 的分块并行执行（行 hash 化预处理 +
  分块调度 + join）。
- **依据**：§2.3 算法行「大文件走分块并行」；§2.1 该预算行解锁条件=
  diff 引擎。
- **期望形态**：与 §2 剪枝协同（先剪全等块，再对差异区分块并行）；
  重活出主线程（§4.4——单写者 + 快照隔离，diff 任务只读 snapshot，
  不与编辑竞争锁）。
- **验收形态建议**：100MB 同比对基准计时（下游 tools/bench diff 计时
  框架为测量面——1/10/100MB 三档，§5 已列）。

## 4. 目录比对 v1

- **诉求**：递归目录比对，状态分类（新增/改/删/二进制）——两级：元
  数据级（size/mtime）预筛 + 内容级（调 §1 引擎，惰性）。
- **依据**：§2.3 目录 diff v1（递归比对、按状态过滤；基础同步动作=
  应用层实现，引擎只出比对结果）。**边界：双向同步向导与 3-way
  merge=战略 §9-Q5 开放问题，非本供料件**（M3 收口时按使用反馈另裁）。
- **期望形态**：流式/分批产出（大目录增量返回）；输出结构
  path→status→（惰性）hunks。
- **验收形态建议**：多形态目录 fixture（嵌套/重命名相似/二进制混合）
  状态分类基准。

## 5. VM/back 消费端点（随引擎定型，669 模式小件）

- **诉求**：引擎定型后 `.at` 可调用面：`diff(path_a, path_b)` /
  `diff_snapshots(key_a, key_b)` / `diff_dirs(...)` → 结构化结果。
- **依据**：669 模式（下游供料→上游立 plan→下游零/最小改动消费）；
  消费形态对齐既有端点族惯例：JSON envelope 直通（read_text_range
  先例）+ 错误形值不 raise（code_editor_load_file 返 -1 先例）。
- **期望形态**：与 PLAN-673/687 端点族同风格；merged=进程内 CALL、
  split/vue 经 HTTP 同 back（auto-edit back-api.md 契约面）。

---

**优先级建议（auto-edit 视角）**：**§2 最先**（可独立交付、实现面
最小、是 §1/§3「先剪后算」路径的地基）；§1 次之（引擎本体，M3 全链
前置）；§3 随 §1；§4 可分段（元数据级先行）；§5 随引擎定型后小件。

**回执方式**：同 M1 供料包——各件落地落上游 plan 后，auto-edit 侧以
零改动或最小改动复验解阻（669 先例），并在本仓 README/战略文档更新
对应「解锁条件」注记（§2.1 预算表 diff 行）。

---

**登记侧注记（2026-09-23）**：~~M2 内部重排（大文件模式压后、M3 diff
提前开工）截至本件落档**未经用户裁定**~~——**同日稍后已裁定**（战略
补注十一，`docs/strategy/002-north-star-v2.md` 变更记录 11）：PLAN-010
收口后 M3 diff 提前开工、大文件模式压后（与 M3 并行/随后收口）。本件
「供料先行」路径与供料面（五件）不变，重排裁定使其从「不改路线图」
升级为「路线图重排的第一步」。

---

## 6. PLAN-016 增量：消费回执 + 双缺陷登记（2026-09-27，执行期勘定）

PLAN-016（M3-04 diff 引擎消费件，形态 B 消费件；供料=auto-lang
PLAN-703 五件供料包，delivery 46efa926a，2026-09-27 delivered 归档）
替换缝兑现执行期（worktree plan-016-dev，消费侧探针+产品仓全量对账）
回执。**六供件逐项核销 + 两枚上游缺陷（D-1/D-2，rows 面与 anchor 分
块面——消费侧实证，根因已定位到源码行级）**。

### 6.1 六供件逐项核销

- **供①a 行级引擎——rows 面缺陷在案（D-1，见 6.2），hunks/counts 面
  核销**：native 裸名 `diff_files`（9915）直调替换 `fsys.diff_files_json`
  过渡实现体（~520 行三门+朴素分层整体退役——1MB 尺寸门/10k 行门/
  DP-200 降级/「等待内核引擎」err 文案族全退场）；hunks/counts 面
  六形态探针对账全等（modify 逐字段零漂移；>10k 行/1MB 超限文件正常
  出结果=门退场实证；全等 1.2MB 对 trim 快路 0 hunk）。degraded 恒
  false（引擎时代无降级语义——上游成文兑现）。
- **供①b refinement（三段标记 refine 恒开）——核销**：modify 形配对
  行三段逐字段全等（`let x = <1>/<2>` 形在档）；100k 字符预算随 VM 步
  墙退场（引擎侧无预算——refine 恒开实证）。
- **供② rope 哈希——间接核销**：快照快路消费面=供⑤ diff_snapshots
  （缓冲区比较 v1 落位——PLAN-011 边界注记「零全文 tab 铁律正解」；
  merged 臂 tab.key registry 直读净形 envelope，probe_bufdiff 8/0）。
- **供③ 分块并行——核销受阻（D-1 连带）**：bench diff_100mb 档判定
  **blocked**——D-1 rows 面在多 hunk 大文件上切片错位放大（rows 数
  随 hunk 数二次方积累），envelope 体量失真，≤2s 预算判定不可测；
  上游 release 档 0.35-0.9s 相对量在档（SD 文档基准节），绝对量判定
  待 D-1 修复后下游 L2 重推（703 Q-2 口径不变）。
- **供④ 目录比对——核销（语义零漂移）**：`diff_dirs`（9917）直调
  替换 `fsys.diff_dirs_json` 过渡实现体（长度桶对齐+桶积 700k 护栏+
  「对齐超限」err 形退役）；dirdiff 五形态 golden 语义零漂移
  （entries statuses/counts/note 逐字段全等；同长 900 文件巨桶正常出
  结果=护栏退场实证；>2MB 同尺寸 uncompared 注记保持；条目**序**漂移
  =引擎每目录排序定序 vs 过渡遍历序——断言面序不敏感，证据在档）。
- **供⑤ 端点——核销**：三 natives 五面注册实勘在册
  （native_catalog.rs:58-60/codegen.rs:556-558/ui_gen rust 臂）；裸名
  解析探针 split 臂 6/6（df/dd 正路径+ctx=0 钳 3 逐字节同形+缺文件/
  缺目录/缺键 err 形=非 Undefined 绑定证明）；第 15 端点
  `diff_buffers` 落位（净形 rows:[]+缺键 err 形「编辑器不存在: …」+
  tab.key 键语义）。

### 6.2 缺陷登记（消费侧实证，本仓不修——upstream 修订件清偿）

**D-1 rows 面流位错配（`build_rows` × `group_hunks_annotated` 单位
不一致）**：`group_hunks_annotated`（diff/mod.rs:348 起）向
`GroupedHunk.fc/lc` 写入的是**changes 向量下标**（`fc: idx, lc: idx`
——`changes.iter().enumerate()` 的 idx），而 `build_rows`
（diff/envelope.rs:178 起）按**keep+change 流下标**消费（`lo = fc -
(fi - a1)`、`hi = lc + 1` 后沿流跳 keep——011 下游实现的 fc/lc 契约=
流位「si」）。凡变更前存在 keep 域的形状，两套下标错位：

- 纯增/纯删/删多增少形**变更行整块丢失**（add_only：adds=3 而 rows
  仅 5 条 ctx——变更行零投影；unbalanced：rows 6 vs 参考 7，pair/
  del 行丢失；视图层=用户看不到增删内容——功能性破坏，非显示偏好）。
- 多 hunk 形**前导 ctx 重复**（scattered：rows 41 vs 参考 21——每
  hunk 切片 lo 饱和回 0，重复渲染先前 hunk 的上下文行，且越界 hunk
  窗）。
- 大文件多 hunk 形 rows 数随 hunk 数二次方积累（1% 散布改 100MB 形
  估算 O(H²)≈10^10 行量级）——**供③ bench 判定连带阻塞**。

最小复现：`diff_files_envelope("L1\n…L10\n", "L1\n…L5\nE1\nE2\nE3\n
L6\n…L10\n", 3)`（fixtures add_only）→ adds=3、rows 全 ctx。修法
建议：fc/lc 改携流下标（分组期记录流位），或 build_rows 改由 changes
直接推导切片域（两处任一单源化即可）。

**D-2 anchor 分块非单调（`anchor_partition` 缺单调过滤）**：
`anchor_partition`（diff/mod.rs:180 起）收集「双侧恰一次」行后仅
`sort_unstable()`（a 位升序），**未过滤出 b 位也单调的子序列**——
换位/移动族形状（中段 ≥512 行）锚集 b 位往返非单调，
`engine_changes` 段构建把锚当单调走（`cursor = (ai+1, bj+1)` 倒退）
→ 退化段（空 a 段/空 b 段错置）→ **编辑脚本本身错误**（counts 面）。

最小复现：620 行全换位（P5+A300+M10+B300+S5 vs P5+B300+M10+A300+S5，
fixtures big_reorder）→ **adds=620/dels=0 双向对称**（b→a 同 +620/-
0；等长文件双向纯增=内部不一致实证；参考实现+上游自身 golden 面语
义=300/300 或 310/310 配对形）。703 探针面未覆盖此形（八形态 golden
走 `diff_lines` 的 hunks/counts——恰好此形 counts 即错；探针 7 项断
言的 rows 面用 modify 形——恰为 D-1 不触发形），两缺陷自交付即在。
修法建议：anchor_partition 尾部增最长单调递增子序列（a、b 双坐标）
过滤——锚点内容决定性保持（同输入必同锚），O(n log n)。

**消费面影响矩阵（PLAN-016 矩阵注记同步）**：hunks/counts 正确面
（小中段 <512 形）不受累；rows 面（除「变更前零 keep 域」形）与
换位族 counts 面在上游修复前=已知 blocked 集（不 golden 化缺陷输出，
golden 保持过渡时代原样——同步≠放宽）。

### 6.3 残留 want（执行期勘定，非缺陷）

- **全异形 envelope 体量治理**：rows 全量投影在 100% 全换形=巨串
  （上游 v1 形）——观察件在案（PLAN-016 §10 Q-2），体量治理属后续件。
- **快照面尾行语义**：buffer 快照切行保尾空行（3 行+尾换行文件出
  [0,4) 窗）vs 文件面尾空吸收（[0,3)）——两面差异=上游内部行为，
  下游按实测真值断言；如需两面同形请随修订件裁定（非阻塞）。
- **bench diff 档解锁**：D-1 修复后下游重推（diff_100mb 生成式散点
  改档+门拒档通过形改造+budgets.json 实测回填——PLAN-016 blocked
  尾巴，修复轮一并清偿）。
