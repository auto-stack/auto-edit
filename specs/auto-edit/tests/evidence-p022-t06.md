# PLAN-022 T-06 供③ P716-D1 复试证据（2026-10-01）

## 结论

**销账未达——P716-D1 维持「确认复核件」挂账**（不假销账）。
工具链 v0.4.2-2474-g95dcfb55b（组树 debug 构建@95dcfb55b detached，
含 716 ec45f911c+719/720）。全矩阵 ×3（`tests/run_matrix_x3.sh`），
主实例 MCP 端口高带钉位（P716-D1 处方 part-1 已落实——
desktop_mcp.py 主实例 AUTOUI_MCP_PORT 钉位臂+runner 逐跑 93xx 带拣位）。

## ×3 谱

| run | 钉位端口 | 深度 | PASS/FAIL | 终态 |
|---|---|---|---|---|
| 1 | 9337 | T9（关 tab 循环中） | 30/0 | app 进程净退（`vm interpreter returned ok=true`）→ MCP ConnectionRefused |
| 2 | 9328 | T6（redo/undo 面） | 22/0 | 同上（净退） |
| 3 | 9331 | T9 过→T10 子实例 spawn | 41/0 | T10 server never up（子实例 spawn 败） |

- **矩阵检查面 0 FAIL**（93 PASS 累计，wherever ran 全绿——含 T15.1-3
  diff 主链绿=016 消费面零扰动哨随跑复证）。
- **T17 不可达**（三跑均未达 T17 簇）→ T17.2/17.3/17.8 复验位未达，
  销账判据（T17 全绿×3）不满足。

## 归因面（证据链）

1. **退出=驱动动作相关，非自退定时器**：空闲对照实验（同 env 隔离
   APPDATA+AUTO_OPEN_PATH，零驱动）**420s 存活**（13 心跳、零
   returned-ok）——app 净退仅发生于矩阵动作序列中（T6/T9 深度）。
2. **净退形态**=`[X9] vm interpreter returned ok=true`（干净解释器
   返回——非 panic[X9-PANIC 钩子在岗未触发]、非 taskkill 强杀
   [强杀无此行]）——与 P716-D1「app 楔死」亚型不同（本次=事件循环
   正常结束=窗口被正常关闭路径，嫌疑=动作派发 vnode 漂移误击
   退出族入口[矩阵多处「点击重试卫生」注记同族竞态]），机器态相关
   非确定性=P716-D1 原录口径。
3. **共栖环境**：PLAN-721 desktop 会话今日在途（desktop-721i 实例，
   auto-lang KNOWN-DEBT P712-D1 推进中）——P716-D1 处方「共栖负载
   空闲窗口期」前提今日不成立。
4. **处方 part-1 正面应验**：主实例 3/3 boot 成功（P716-D1 时代
   924x 带 TOCTOU 死占 3/6 → 本轮 0/3）。

## KNOWN-DEBT 回写建议（跨仓注记——auto-lang docs/plans/KNOWN-DEBT-AND-RISKS.md P716-D1 行）

> 2026-10-01 下游复试（auto-edit PLAN-022 T-06，工具链
> v0.4.2-2474-g95dcfb55b）：主实例端口钉位处方已落实（924x TOCTOU
> 点位清零，3/3 boot）；全矩阵 ×3=93 PASS/0 FAIL（T1-T9 深度全绿，
> T15 diff 主链随跑复证）但 T17 不可达——app 动作相关净退 ×2
> （空闲对照 420s 存活排除自退）+子实例 spawn 败 ×1；共栖 721
> desktop 会话在途，空闲窗口期前提不成立。**维持挂账**（不假销账），
> 销账判据不变（空闲窗口期 ×3 T17 全绿）；下次窗口期按
> auto-edit tests/run_matrix_x3.sh 复跑。evidence=auto-edit
> tests/evidence-p022-t06.md+matrix-p022-run{1,2,3}.txt。
