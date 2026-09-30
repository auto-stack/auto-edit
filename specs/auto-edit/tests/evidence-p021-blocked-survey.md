# PLAN-021 blocked 面实勘（2026-09-30，供① 消费复验）

> 结论先行：**供① 残余=一个根因两面缺口**——back 模块转译器缺语句级
> try 臂，经 `fsys.at:208` try（PLAN-012 find-in-files 兜底）同时打穿
> ①back crate 编译（E0432）与 ②front route-A 伴生嵌入（`.ok()?` 整体
> 回退→桩客户端→env/文件面功能死亡）。L2 直拉形态（本件主判定面）
> 两面全阻——按 Q-3 默认路由登记 upstream，不在本仓修生成物。
> 附：710 corpus 判据盲区=陈旧基面掩蔽（fresh worktree 首次暴露）。

## ① 现势 regen 双缺口实录

工具链=debug auto v0.4.2-2311-g7fcf913eb（clean，含 710 e81e0a1c3+
712+713；判据前核在档 plan §8 T-00）；项目=edit-021 worktree
（fresh——无陈旧 rust-workspace 掩蔽项）。

- a2r 生成：`perf.py a2r` **exit 0**（a2r-20260930-163740.log）；
  生成物 grep 三占位（`/* expr */`/`/* unhandled stmt */`/裸
  code_editor_delta）**零命中**——710 G-A/G-C 面在 front 生成物成立。
- **缺口一（back crate）**：`cargo check --workspace` 红——
  `error[E0432]: unresolved import crate::fsys`
  （auto-edit-back/src/api_impl.rs:3；release-20260930-164204.log:3858）。
  back/src/=api.rs+api_impl.rs+main.rs+types.rs，**fsys.rs 缺席**
  （api_impl 15 处 fsys:: 引用悬空）。a2r 日志根因行：
  `⚠ fsys.rs transpile failed (module skipped): Failed to transpile
  fsys.at: Rust Transpiler: unsupported statement: Try(...)`——
  fsys.at:208 try（find-in_files 读兜底，PLAN-012 引入；空 catch 体+
  for{if break} 体）命中通用转译器（crates/auto-lang/src/trans/rust.rs
  ~:12300 语句分派）**无 Stmt::Try 臂**——710 G-B 臂落点=
  crates/auto-lang/src/ui_gen/rust.rs（front UI 通路），
  back 模块通路（auto-man api_gen transpile_back_module_to_rs→
  transpile_rust）不在其覆盖。
- **缺口二（front 功能面）**：front main.rs 的 api 客户端族
  （env_str/read_text/exists/read_text_range/file_size/write_text/
  tree/ws_root）生成形态=**恒空桩**（D-7 收口形：
  `let _ = (args); API_DATA.push(json!({id})); String::new()`），
  API_DATA 全仓 16 引用**只写无读**、无 ureq/HTTP 客户端=死端。
  实证效应：`env_str("AUTO_BENCH")` 恒 ""→全部 BENCH 标记静默、
  `AUTO_OPEN_PATH` 恒 ""→打开链不可达、read_text/exists 恒空→
  会话恢复/工作区树/文件面全死。
- **同根因闭环**：旧基面 front（main@70c5c60 的 rust-workspace）
  同函数形态=`fn env_str(name:&str)->String{ return fsys::env_lookup(
  name); }`（route-A 伴生嵌入活跃——main.rs 内联 pub mod fsys+api_impl）。
  新生成器同路径 `merged_route_a_impl`（auto-man/src/rust_ui.rs:903）：
  `let rs = transpile_back_module_to_rs(&stem,..).ok()?`——fsys.at 转译
  失败→**整体 None**→front 回退桩客户端。即一个 Try 臂缺口同时造成
  back 缺模块与 front 桩化两面。

## ② 首跑收据（生成码首跑真实 app——最小面绿）

release front exe（40,421,888B，2026-09-30 16:46 构建）：零旗标直拉
+隔离 APPDATA——`Running with Iced backend` ✓ / `AutoUI MCP: listening`
✓（9247 占用自动回落 9251——**release exe 有 AutoUI MCP 面**，T-00⑤
「无 MCP 面」预判修正）/ 存活 10s ✓ / 零 panic ✓（tools/portable/logs/
gen-first-run-20260930.log）。编译零占位+进程面健康=「生成码可跑」；
功能面（env/文件流）受缺口二阻=壳态。

## ③ 710 corpus 判据盲区（掩蔽机制）

710 实机判据（33a5d56c3）：「corpus=auto-edit main@70c5c60 tmp 拷贝…
生成 workspace cargo check 过（56.55s 0 error）」。本件 fresh worktree
同源复验 back 红——差异=**tmp 拷贝携带陈旧 rust-workspace**（旧代生成
的 fsys.rs——现勘旧 fsys.rs 内零 find_in_files/re_case 引用=远早于
PLAN-012 的老生成，恰与旧 api_impl 自洽）满足 `use crate::fsys` 导入
→检查绿；front 桩化则本就编译绿（判据无运行时功能面）。即 corpus 的
「cargo check 过」与「三占位零命中」均为**掩蔽后真值**——生成器缺口的
暴露面（skip 警告行+缺文件）不在其判定集。判据增补建议见供料档 §6。

## ④ 对本件判定面的影响（不冒领纪律落点）

- L2 直拉形态五行判定（steady/warm/open/idle/diff）：无一面可产
  诚实数字（front env/文件面死；diff back exe 编不出）——budgets
  五行**不升级**（ledger/锚点态维持），018 锚点+019 产物面数字保留
  对照位。019 surface 数字（21.2/38.2ms）系旧基面（route-A 活跃代）
  产物——其「last-good 基面」注记语义现更名真：该代 front 功能完备，
  数字仍为对照面（非 L2）。
- `bench.py --l2`（本件新增 L2 化档）+`smoke_gen.py`（三域冒烟）=
  已备 harness，上游解阻后即跑（判据面成文在档）。
- build_portable regen 现势化（T-01 退役臂）：front 链不受缺口二影响
  （构建面），retirement 语义成立；`--skip-build --check-idempotent`
  自证在档。全量 portable 构建（cargo build workspace）现随缺口一红
  ——installer 行第二段收口件连带 blocked 注记。

## ⑤ 精准解锁动作（上游件建议——供用户裁定立项）

1. auto-lang 快速修订件（710 D-4..D-8 回补先例量级）：通用转译器
   （trans/rust.rs 语句分派路径）补 `Stmt::Try` 臂——镜像 ui_gen
   G-B 臂形（catch_unwind(AssertUnwindSafe)/Ok 丢弃/Err 进 catch/
   catch(e) 绑定=panic_message 载荷）。单臂落点两面全解（back
   fsys.rs 发射+front route-A 伴生嵌入恢复）。
2. 判据增补（可并入同件或 714 勘定件）：corpus regen 判定集增
   ①「⚠ … transpile failed (module skipped)」grep 零命中；
   ② fresh-copy regen 卫生（regen 前清 rust-workspace 或 dump
   文件清单 diff）——堵陈旧基面掩蔽。
3. 解阻后本件 T-02/T-03/T-04 按 §8 已备判据面补跑（zero 重设计）。

## ⑥ 解阻复验（2026-09-30 同日——PLAN-714 r2/r3 清偿后补跑实录）

r2（Try 臂 d22318fc5）fresh 复验暴露 route-A 深修层（26 错/8 类）→
needs_replan→r3 深修收口（29563c588——stdlib 面+内建分发器三处+Try
return 传播形+借位 clone 窄门）→delivered@acf653d3f（AC-R2-4 下游
确认在 r3 census §7）。本仓 edit-021 worktree 复验：

- **三重判据首度全绿**：a2r exit 0（a2r-20260930-203420.log，工具链
  v0.4.2-2366-gacf653d3f 组树 debug 构建）+零 skip 警告+三占位零命中
  +back fsys.rs 在位（api_impl 15 引用全解）+front route-A 实体形
  （env_str→fsys::env_lookup 与旧基面同形）+**fresh workspace
  cargo check 过**（47.4s，CHECK_RC=0——本档 §①的 E0432 反转绿）。
- **release 双产物**：sccache 堆损坏（0xc0000374）一度——019 旁路
  配方（RUSTC_WRAPPER=""）复用即绿（auto-edit.exe 40.7MB+
  auto-edit-back.exe 14.4MB）。
- **L2 直拉首判**：steady armed PASS 15.6ms（谱 14.3-16.1）/
  idle armed PASS 9.7MB/diff armed FAIL 5183.2ms（谱 4985.8-5412.4，
  back 直拉；016 VM 形态对照 1906ms）——数字入 budgets validity+
  compare anchors l2 行（--verify 绿+render --check 绿）。
- **三域冒烟 4/7 绿**：G-B①成功臂（restored@16.8ms）/G-A④投影链
  8s 存活/G-A⑤包络 golden 3/3+G-B②catch 臂语义（restored 缺席+存活
  ——「后续打开绿」半腿随 §7 blocked）。三 FAIL 全归 §7 缺陷。
- **残余缺陷（供料档 §7）**：a2r 形态 code_editor 注册断链——装载
  探测门永假（no editor registered for key __code_editor_tab-N 刷屏
  ——warm-0-20260930-204554.log/open-probe 实录）；VM 轨对照正常
  （open_done 触发）+旧 a2r 构建正常+新旧视图代码逐字节一致→ui 运行时
  回归（窗口 2205→2366）。open/warm 两行 L2 判定+装载/编辑回路冒烟
  随之 blocked；steady/idle/diff(back) 不受累。
- **干扰实录（F-RV6 纪律适用）**：open 档与 L0 矩阵首次启动重叠
  （本仓自扰——MCP 端口互踩+app 早退）——矩阵独占重跑在档；三个
  pre-session auto.exe 实例（14:08/16:10/16:26 起）按「不动他树实例」
  纪律保留。
