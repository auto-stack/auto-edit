# diff 视图状态面与过渡计算层契约（modules/diff-view）

> 来源：PLAN-011 交付 + src/back/fsys.at `diff_files_json` +
> src/front/{editor_store.at, app.at} diff 段；上限三参数=PLAN-011 §10
> T-00 决策（probe_diff.py 五轮，r5 26/0 绿）。本册=M3 首件新面。
> **替换缝声明**：envelope 契约=计算层↔视图层唯一接口——内核 diff 引擎
> （供料包 docs/upstream/2026-09-diff-engine-supply.md）落地后仅换
> `fsys.diff_files_json` 实现体（Rust 直调或端点转发），envelope/
> 视图/矩阵零改动。

## envelope 契约（back `diff_files(path_a, path_b, ctx) str`）

GET `/api/diff_files?path_a=..&path_b=..&ctx=..` → JSON 字符串
（标量返回铁律：HTTP 层再包一层 JSON 引号串——merged 直调拿裸串，
单次 `json.to_value` 即解；HTTP 客户端需深解码两层）：

```json
{"hunks":[{"a1,a2,b1,b2"}], "rows":[{12 字段渲染就绪行}],
 "adds":int, "dels":int, "truncated":bool, "degraded":bool, "err":str}
```

- hunks 区间 **0 基半开** `[a1,a2)`，含 ctx 上下文扩张（默认 3，钳位
  文件界）；rows=逐 hunk 展开的渲染就绪行。
- rows 字段：`lo/ro`=1 基行号（**缺席侧 0**）+ `ln/rn`=全行文本 +
  `lk/rk` ∈ {ctx, del, add, ""}（双侧行 lk=del/rk=add；单侧行缺席侧
  空串）+ 三段标记 `lpre/lmid/lpost/rpre/rmid/rpost`（配对行公共前后
  缀裁剪——mid=着重段；ctx 行 lpre=全文本 mid 空；不成对行整行入 mid）。
- `truncated` v1 恒 false（保留字段——渲染截断在 front 侧，见下）；
  `degraded`=中段超上限走整块 replace；`err` 无错=""，错误形
  （缺文件/超限）hunks/rows 为空数组。
- **CR 容忍**：CRLF 行剥尾 `\r`（\r\n 与 \n 等价；与 golden 的
  universal-newlines 参考实现对齐）。
- 已知偏差（golden 集不覆盖 corner）：相邻 hunk 仅因 b 侧间距分组而
  b 窗交叠时，前组 add 行参考实现双渲染、本实现单渲染（视觉=同行只
  画一次）。

## 过渡计算定位（朴素分层，非 histogram/patience）

① 公共前后缀行裁剪 → ② 中间区 ≤200 行/侧 **DP-LCS**（O(N·M) 行级，
del 优先确定性回溯）→ ③ 大中段降级**整块 replace**（degraded=true，
视觉=一大段红绿无细粒度——内核引擎清偿后消失）→ ④ replace 区**索引
对齐配对**（i-th del 对 i-th add）+公共前后缀三段标记（全局字符预算
100k，超预算行退化整行 mid=Q-4 已接受形态）→ ⑤ ctx 窗切 hunk
（非 keep 间距 ≤2·ctx 归组）+ rows 流切片摊销展开。
选型依据：.at 无 sort/index_of/hash 原语（native_catalog 实勘）——
O(n²) 排序/hash 类算法出局；单 handler **10M VM steps 硬墙**
（engine.rs:2145，T-00 WARN[budget]×4 实证），全链 ~2.2M steps ✓。
三段数据恒在 envelope 供引擎时代 refine。

## 上限门（T-00 §10 保守定参，跨工具链稳健）

| 门 | 值 | 语义 |
|---|---|---|
| 尺寸 | **1MB**（pre-read，fs.metadata） | 即时拒防长等（1914 类解释器 split 0.52ms/行，50k 行=26s 冻结保护） |
| 行数 | **10k 行**（post-split） | 拒绝于读后 DP 前 |
| DP 中间区 | **200 行/侧** | 超出降级整块 replace |
| 渲染 cap | **600 行**（front store 侧） | 超出截断+truncated 注记（fif 面板 500 按钮先例量级） |

错误形注记均含「等待内核引擎 diff_snapshots（架构阻塞）」指引；
1/10/100MB 全文 diff=架构阻塞（供料 §5 时代清偿），bench diff 档
以门拒延迟证明即时性（tools/bench `diff` 子命令 JSONL）。

## front 状态面（EditorStore，SD-01 字段清单）

`diff_open/diff_a/diff_b`（开态与路径）、`diff_rows/diff_rows_count/
diff_rows_truncated`（渲染就绪**显示行**——store 侧预变换：`d_lo/
d_ro`=字符串行号缺席侧 ""（视图零条件格式化）+ `lo/ro` 整数（导航
归属判定）+ `sx_ctx/sx_pair/sx_del/sx_add` 形状旗标 + 六段文本字段）、
`diff_hunks/diff_hunk_count/diff_hunk_idx/diff_hunk_pos`（信封净形+
导航位+位次显示串）、`diff_adds/diff_dels/diff_degraded/diff_err`
（计数与边界态）、`diff_scroll`（controller 句柄 "diffctl"）、
`diff_title_a/b`（file_basename 派生）、`diff_bypass_done`（旁路防
重入）、`diff_dbg_ctx/pair/del/add`（形状计数——矩阵断言面）。

## 入口契约

- **手动**：「工具 → 比较文件…」静态 menubar item（010 menubar-content
  四边界内）+ actions `diff.compare`（Ctrl+Alt+D）→ `dialog_open`×2
  （rfd 阻塞式；任一取消=整链零动作 console 记 cancelled）。
- **矩阵旁路**：env `AUTO_DIFF_A/B` 双设 → **Tick 消费自开**（首拍
  一次，`diff_bypass_done` 防重入；desktop open_with ConsumeOpen 先例）。
  menubar 展开项 2044 不进 vtree + 键盘合成 AltGr 疑虑——双双不可作
  矩阵依赖（T-02 实勘）；单边 env 残缺 → console 记录零动作（防矩阵
  悬挂，不回退 dialog）。
- **关闭**：视图 × 按钮 / Esc（action diff.close）→ `DiffClose` 清态，
  tab 集零扰动（编辑区条件面复原）。

## 导航契约（G-4）

`DiffNext/DiffPrev`（F7/Shift+F7+按钮同源）：hunk_idx 推进/回绕 →
`DiffScrollToHunk`：遍历显示行找首条归属当前 hunk 的行（lo-1∈[a1,a2)
或 ro-1∈[b1,b2)）→ `scroll_to(handle,"y",target×24px)`（绝对像素，
T-00③ 实测行高 24.0=content_h÷行数；float 累加规避 int×float 混合
算术）。空 hunk 零动作（AC-04 disabled 语义=无操作——按钮无 enabled
面，handler 守卫达成）。双栏同步=单 scroll-pane 行对齐设计天然成立
（原双独立窗格联动 want 撤销，upstream §14 注记）。

## 视图与快照断言口径（矩阵/探针实证）

- 根视图全幅态 `if .store.diff_open` 条件替换编辑区（console_open
  同款形态；tab 集零扰动）。行形状四分支=**四个独立 for 循环 ×单
  bool 旗标 if**（同循环多兄弟 if 对 record 字段仅首个生效、嵌套 if+
  空串比较两种形态在 2044 有异常史——T-03 三度重构实录，final form
  为实证绿面；互斥由 store 侧构造保证）。
- **三段=分离 text 节点**：快照断言必须按分离节点口径（如 `"4-changed"`
  单独成节点），拼接串探针（"L4-changed"）=假阳性（T-03 教训入档）。
- for 动态行实例在 a11y 快照中**不携带 style 行**——着色断言归截图/
  人工视觉门（T-15 口径）。
- 模板插值：纯字段已证（`${r.x}`/`${.store.f}`）；**算术插值未证面**
  （曾致视图冻结嫌疑）——位次显示走 store 预计算 `diff_hunk_pos`。
