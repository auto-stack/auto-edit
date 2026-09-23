# diff 视图状态面与过渡计算层契约（modules/diff-view）

> 来源：PLAN-011 交付 + src/back/fsys.at `diff_files_json` +
> src/front/{editor_store.at, app.at} diff 段；上限三参数=PLAN-011 §10
> T-00 决策（probe_diff.py 五轮，r5 26/0 绿）。本册=M3 首件新面。
> **替换缝声明**：envelope 契约=计算层↔视图层唯一接口——内核 diff 引擎
> （供料包 docs/upstream/2026-09-diff-engine-supply.md）落地后仅换
> `fsys.diff_files_json` 实现体（Rust 直调或端点转发），envelope/
> 视图/矩阵零改动。
> PLAN-012 追加「目录 diff」节（M3-02——同一视图态族同册归口；
> 来源=PLAN-012 交付 + `diff_dirs_json` + editor_store/app dirs 段 +
> probe_dirdiff.py 27/0 决策，T-00 定案见 §10）。

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

## 目录 diff（PLAN-012 SD-01 追加，M3-02）

### envelope 契约（back `diff_dirs(path_a, path_b) str`）

GET `/api/diff_dirs?path_a=..&path_b=..` → JSON 字符串（标量返回铁律
同上）：

```json
{"entries":[{"rel,str status,size_a,size_b,is_dir,note}],
 "counts":{"same,added,deleted,modified,binary"}, "truncated":bool,
 "err":str}
```

- **左右语义（BC 同款）**：左=path_a=旧（`deleted`=只在左）、右=
  path_b=新（`added`=只在右）。
- **五态分类序**：①存在性（单侧→deleted/added）→②kind 冲突
  （dir↔file→modified）→③**二进制启发式**（size>0 且
  `File.read_text==""`——非法 UTF-8 即二进制近似；**判定域=≤2MB
  全文读**，启发式读与全等比对读共用零双读；>2MB 不读）→④尺寸差
  →⑤≤2MB 全等（`Str ==`）→>2MB 同尺寸=`same`+`note="uncompared"`
  （「同(未比对)」注记态——字节级 hash=上游 want 清偿前形态）。任一
  侧二进制命中→整条 `binary`（尺寸差在 size 列可见；双侧同尺寸二进
  制亦归 binary，未比对语义）。
- `counts` 与 `entries` **同域**（截断后计数=已处理域——AC-03 计数
  一致性）；条目上限 **5000**（超限 `truncated=true` 不静默）。
- 遍历=`fs.list_dir` 递归扁平（search_files 先例）；**skip-list=
  fif_skipped 同语义**（隐藏段/target/node_modules/gen/dist/build/
  __pycache__——Explorer 与 find 口径一致）；rel 统一 `/` 分隔剥根；
  元数据采集 try 包裹（竞态删除跳过条目不炸端点）。**边界：空目录不
  产生条目**（仅经 `is_dir` 条目参与同步；deep 空树不可见——v1 口径）。
- **对齐=长度桶**：rels 按 `len()` 直索引 256 桶+桶内等值扫（.at 无
  sort/hash 原语的面内解）。**桶积护栏 Σk²≤700k**：同长分布过密超
  VM per-handler 10M steps 墙（定标 N=600 单桶 0.40s ✓/N=800 0.94s ✓
  /N=1000 WARN[budget] 死）→ 超限 err 形「对齐超限（同长桶积 >700k
  ……）——等待内核 sort/hash（架构阻塞）」（011 上限门同款；正解=
  sort/hash 原语，upstream §15 want）。
- **错误形**：根缺失 → err 不静默（entries 空数组）；读竞态/锁定
  →端点错误响应（响亮失败，v1 不吞）。

### 同步动作端点（back，PLAN-012 T-02）

- **`sync_copy(src, dst, is_dir) bool`**（POST）：文件=**字节往返**
  `File.read_bytes`→`File.write_bytes`（1005/1006 原生 shim
  Vec<i32>↔VM list 零 VM 步循环）——**fs.copy(1007) 表面被 `copy`
  保留字阻断**（Plan 122 废弃 ParamMode token 词法全局收编，T-00①a
  迷你 app 复现）的替代面；**≤2MB 预算域**（与内容比对同域，超限
  false+front 注记）；目录=`fs.copy_recursive`（嵌套 E2E 实证）。
  **覆盖语义=静默覆盖**（fs::write truncate / copy_recursive 合并
  覆盖，Q-2 定案）——front 确认链管目标存在形。
- **`sync_delete(path, is_dir) bool`**（POST）：文件=`fs.delete`；
  目录=**仅空目录** `fs.remove_dir`（非空原生失败=T-00 护栏实证；
  **递归删除 v1 不提供**——remove_dir_all 在册不暴露）。空路径/
  根路径（`/`、`\`、盘根）/缺失→false（护栏三条；空串在 HTTP 层即
  missing-param 错误包）。bool 返回=动作后 `exists` 磁盘 E2E 终判。
- **安全注记**：①动作仅对已完成一次比对的 entries 态开放（无比对
  无动作）；②破坏性动作（覆盖复制/删除）alert-dialog 确认链；③back
  端点空路径拒绝。**删除域=单侧条目**（deleted 删 A 侧/added 删 B 侧
  ——双侧条目删除不提供，copy 已覆盖同步意图）。

### front 状态面（SD-01 字段追加）

`diff_mode`（契约字段 "file"/"dirs"，矩阵断言面）+ `dir_mode`
（视图旗标——**dir_mode ⟺ diff_open 由 handler 组维护**：dirs 面板
=顶层面板条件、文件 diff 视图增 `!dir_mode` 内卫、编辑区 `!diff_open`
条件零改动）、`dir_from_dirs`（下钻来源门——DiffCompute err/DiffClose
双外科归位点，011 路径零扰动）、`dir_a/dir_b`（输入绑定）、
`dir_entries`（envelope 全量在 store——**过滤=front 纯态零重比**，
AC-03）、五 `dir_n_*` 计数、`dir_truncated/dir_err/dir_has_err`
（err 行视图条件走 bool 旗标——空串比较禁面）、五 `dir_f_*` 过滤钮
旗标、`dir_view/dir_view_count/dir_view_truncated`（过滤投影渲染
就绪行 cap 600：徽标/尺寸串/`[目录]` 标记/未比对注记全 store 预变换）、
`dir_confirm_*`+`dir_pending_*`（确认链冻结意图，op ∈
copy_r/copy_l/del_a/del_b）、`dir_bypass_done`。

### 入口/下钻/刷新协议

- **入口**：「工具 → 比较目录…」静态 menubar item → 双路径输入框+
  比较钮（**v1 无 folder picker**——dialog_open=rfd pick_file 文件
  专用，T-00④ 静态勘定；输入路径=人工面）；矩阵旁路 env
  `AUTO_DIRDIFF_A/B`（Tick 自开臂，011 同款）。
- **下钻（BC 工作流闭环）**：「改」条目点击 → 拼 abs → 011
  `DiffCompute` 复用（diff_mode 切 "file"+并排视图+hunk 导航全套）；
  「返回目录」钮/Esc（dir_from_dirs 门）→ 回目录态 **entries 保留
  不重比**；下钻失败（>1MB 超限/错误形）自动归位目录面板。其余条目
  点击 → OpenPath（fif 先例）。
- **刷新**：同步动作成功 → `DirDiffRefresh` 重调 diff_dirs（磁盘
  E2E 断言面）；过滤态保持（dir_filter 不动，DirApplyFilter 重放）。

### 视图断言口径（T16 实证）

- 行渲染=**五状态五独立 for 循环×单 bool 旗标 if**（011 四循环同款
  规避）；同步动作钮按行形状分布（改/二进=→←、增=←✕、删=→✕、
  同=无钮）。矩阵动作定位=**过滤先行走最小单状态树**（单状态=按钮
  find 唯一）。
- 同步动作走 tmp 生成树（fixtures 保 pristine——008 先例）；
  >2MB 未比对注记=生成式 fixture+快照「未比」断言。
