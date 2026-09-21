# tools/perf — 性能模式（L2）编排与模式矩阵

PLAN-004 T-02 实勘产物（2026-09-21；工具链 `v0.4.2-1631-ge82b95b22`）。
战略语义：`docs/strategy/002-north-star-v2.md` §5 测量模式阶梯——
L0 日常 / L1 结构探针 / L2 性能模式（唯一有预算效力）。

## 模式矩阵（实勘结论）

| 模式 | 启动命令（自 `specs/auto-edit/`） | 已知阻塞 | 验证状态 |
|---|---|---|---|
| L0：VM+merged（日常） | `auto run -r vm` | — | 绿（README 既有口径，2026-09-21 复验） |
| L0'：VM+split | `auto run -r vm --no-merge` | F-RV6（矩阵非确定，功能环曾绿） | split 功能环 2026-09-21 曾全绿 |
| **VM+RQ**（L1 探针可达） | 终端1 `auto rqhost`；终端2 `auto run -r vm -q` | — | **待 T-06 冒烟**（`-q` 官方注记支持 vm/rust 轨） |
| **a2r+RQ**（L2 性能模式主形态） | 终端1 `auto rqhost`；终端2 `auto run -r rust -q` | a2r 对本工程生成面待实跑验证；release 需 perf.py 直调 `cargo build --release` | 待 T-06/T-07 |
| a2r server（split 后端） | `auto run --server rust` | **F-R1：E0432 + 契约空体桩——blocked-on-upstream**（供料包 §4） | 复现于 PLAN-003 归档 L223 |

## RQ 模式机制（源码实勘）

来源：`crates/auto-lang/src/ui/desktop_protocol/rqhost.rs`（PLAN-031）。

- **守护**：`auto rqhost` = iced daemon，共享合成器（多 app 单实例），
  宿主 OS 原生窗渲染。
- **rendezvous**：well-known 命名管道 `autodesk-rqhost`（env
  `AUTO_RQHOST_WELLKNOWN` 可覆盖——perf.py 用它做隔离实例后缀）；
  客户端 `adopt␟<app_name>` → 分配 per-app 管道 → 直连。
- **单实例仲裁**：锁管道 `<wellknown>-lock`（FILE_FLAG_FIRST_PIPE_
  INSTANCE）——第二实例创建即 PermissionDenied，OS 级原子。
- **生命周期**：**末窗退出**——daemon 在最后一个客户端窗口关闭后退出；
  perf.py 的 rq-up 须按"每测量批次预热"语义设计，不能假设常驻。
- **清理**：daemon 是 `auto.exe rqhost` 进程——**按 PID 收**（.rq.json
  记录），不得 `taskkill //IM auto.exe`（会连坐 app 实例）。

## a2r 生成面（源码实勘）

来源：`crates/auto-man/src/rust_ui.rs`（L2615-2630 等）。

- 入口：`auto build -r rust`（生成）/ `auto run -r rust`（生成+跑）；
  仓外项目输出 `<project>/rust-workspace/`（本仓 .gitignore 已列）。
- 工具链对生成物的 cargo 调用为**默认 profile（debug）**（L3129
  `cargo build --manifest-path …`）——L2 的 release 编译由 perf.py 直调
  `cargo build --release --manifest-path <rust-workspace>/…/Cargo.toml`
  补足，产物路径/exe 名（pac `exe_name`）在 T-07 实跑时回填本表。
- **F-R1 只阻塞 `--server rust`（独立 axum 后端），不阻塞 merged rust
  轨**——L2 性能模式用 `-r rust -q`（进程内直调）即可，无需等 F-R1。

## 运维注记（T-06 待决/回填）

- **bps 依赖路径**：pac `dep bps` 为相对路径（`../../../auto-lang/
  blueprints`）——worktree 内跑 app 需组内 auto-lang 兄弟树或环境
  覆盖（是否存在待查）；临时方案 = 验证跑在主检出（零代码编辑，
  产物 gitignored，不违反 master-zero-WIP）。
- 探针输出一律落文件（`logs/`，防管道阻塞）；复跑前清 auto.exe 孤儿
  （`taskkill //F //IM auto.exe`，注意与 rqhost PID 收编的区分）。
- 工具链版本指纹：`auto --version`（须 ≥ 含 669 的构建）+ auto.exe
  mtime 核对，每次 smoke 记录入 `logs/env-<ts>.txt`。

## perf.py（T-05–T-07 交付）

`python tools/perf/perf.py <stage>`：`check / a2r / release / rq-up /
rq-down / run / smoke`；退出码 0=绿 / 3=blocked-on-upstream / 1=真失败。
详见 PLAN-004 §5.3。
