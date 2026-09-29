# tools/compare — 公开对比表竞品测量（PLAN-020）

同机测量四对象（VS Code / Zed / Beyond Compare 5 / Notepad++[pending]），
方法论与计时点定义定案见 **[METHODOLOGY.md](METHODOLOGY.md)**（T-00
决策件——通道结论/探针证据/降级清单/环境干扰条款）。

## 用法

```bash
python tools/compare/compare.py check                    # 在位性+版本+指纹
python tools/compare/compare.py run <对象> <5mb|100mb> [-n N]   # 基线跑谱
python tools/compare/compare.py report                   # median+离散表
python tools/compare/anchors.py [--verify]               # 我方三态锚点（直读零重算）
python tools/compare/render_table.py [--check]           # README 表位生成
```

对象：`vscode`/`zed`/`bc5`/`nppp`。档位：`5mb`（四对象可比小档）/
`100mb`（战略档；bc5=diff 对档）。exe 路径可用 `CMP_<对象>_EXE` 覆盖。

## 纪律（frozen）

- **三要素门**：数字入表必附 {版本钉版, 环境指纹, 跑谱+离散}——report/
  render_table 缺一拒出数。
- **我方列三态分层**：anchor[VM 形态]/surface[last-good]/release-judged
  [仅限 diff，016 先例]/l2-pending[禁出数]——防冒领（018 纪律表内延伸）。
- **跨对象计时语义不同**（直比禁则）——语义列随行。
- fresh profile per run；沉降窗 5s；taskkill 按 PID 树（禁 `/IM`）；
  竞品纯黑盒（零安装域写入）。
- invalid-run 单次重跑（VS Code 间歇自退现象谱在案；连续两跑无效
  abort——014 F-RV6 归因纪律：先查并行会话清扫）。

## 布局

- `results/`：基线 JSONL + anchors.json + table.md（**入仓追踪**）
- `fixtures/`、`logs/`：gitignored（可再生）
- `probe_channels.py`：T-00 通道实证探针（决策证据，非基线面）
