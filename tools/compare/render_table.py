#!/usr/bin/env python3
"""render_table.py — PLAN-020 T-04 公开对比表生成器（数据驱动 markdown）。

输入：results/compare-*.jsonl（竞品基线——每 对象×档 取最新有效文件）
     + results/anchors.json（我方三态锚点，anchors.py 产物）。
输出：results/table.md（独立件）+ specs/auto-edit/README.md「公开对比表」
     节标记区间（BEGIN/END 注释间——**生成区间禁手改**，AC-05 以
     --check 复现一致断言）。

纪律（frozen，PLAN-020 §2）：
① 我方列三态+L2 分层（列元数据非自由文本）——l2-pending 态**禁止出数**
  （渲染断言）；l2 态**必出数**（判定谱直读）；anchor/surface/release-judged
  随行注记防冒领。
② 三要素门——竞品单元格只在 {版本钉版, 环境指纹, 跑谱+离散} 齐备时
  出数（复用 compare.py report 同款判据，缺一渲染 pending 拒出）。
③ 跨对象计时语义不同（METHODOLOGY §2）——表内附「语义」列，直比禁则。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
ROOT = HERE.parent.parent
README = ROOT / "specs/auto-edit/README.md"

BEGIN = "<!-- COMPARE-TABLE:BEGIN（tools/compare/render_table.py 生成——禁手改） -->"
END = "<!-- COMPARE-TABLE:END -->"

TARGET_LABEL = {"vscode": "VS Code", "zed": "Zed", "bc5": "Beyond Compare 5",
                "nppp": "Notepad++"}


def _load_latest(pattern_prefix: str) -> dict | None:
    """取该 前缀（compare-<target>-<tier>）最新有效文件的头+摘要。"""
    files = sorted(RESULTS.glob(f"{pattern_prefix}-*.jsonl"))
    for f in reversed(files):
        head = summary = None
        for line in f.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            if r["type"] == "compare_head":
                head = r
            elif r["type"] == "summary":
                summary = r
        if head and summary and summary.get("runs_ms"):
            return {"file": f.name, **head, "summary": summary}
    return None


def _load_anchors() -> list[dict]:
    return json.loads((RESULTS / "anchors.json").read_text(encoding="utf-8"))["states"]


def _nppp_present() -> bool:
    sys.path.insert(0, str(HERE))
    import compare
    return compare.TARGETS["nppp"]["exe"]().exists()


def _competitor_cell(data: dict | None) -> str:
    """竞品单元格（三要素门内建——缺一拒出数）。"""
    if not data:
        return "—"
    s = data["summary"]
    if not data.get("version") or not data.get("fingerprint") or not s.get("runs_ms"):
        return "拒出数（三要素缺）"
    n = len(s["runs_ms"])
    return (f"{s['median_ms']:,.1f} ms（N={n}，"
            f"{s['min_ms']:,.1f}–{s['max_ms']:,.1f}）")


def _our_cell(anchors: list[dict], metric: str) -> str:
    """我方单元格：三态列元数据渲染。l2-pending 禁止出数（断言）。"""
    parts = []
    for a in anchors:
        if a["metric"] != metric:
            continue
        st = a["state"]
        if st == "l2-pending":
            assert a["median_ms"] is None, f"l2-pending 态不得出数：{a}"
            note = a.get("note") or "待残余面清偿（位虚席）"
            parts.append(f"pending（{note}）")
        elif st == "l2":
            assert a["median_ms"] is not None, f"l2 态必出数：{a}"
            verdict = a.get("verdict", "")
            if a.get("unit") == "fps":
                # PLAN-022：帧率行（unit=fps——非 ms 语义，runs_ms 缺席，
                # 谱面=distinct/window 随行）
                note = ("armed PASS——判定绿" if verdict == "pass"
                        else "armed FAIL（首基线锚点）——归因随行")
                parts.append(f"{a['median_ms']:,.1f} fps"
                             f"〔**L2 直拉判定·{note}**——窗 "
                             f"{a.get('window_ms', 0):,.0f} ms vs 阈 "
                             f"{a.get('budget', 0):,.1f}〕")
                continue
            mark = "**" if verdict == "pass" else ""
            note = ("armed PASS——硬门禁正式判定绿" if verdict == "pass"
                    else "armed FAIL（记录性）——归因随行")
            parts.append(f"{mark}{a['median_ms']:,.1f} ms{mark}"
                         f"〔**L2 直拉判定·{note}**——N={len(a['runs_ms'])}，"
                         f"{min(a['runs_ms']):,.1f}–{max(a['runs_ms']):,.1f}〕")
        elif st == "anchor":
            parts.append(f"**{a['median_ms']:,.1f} ms**〔锚点·VM 形态——非 L2〕")
        elif st == "surface":
            parts.append(f"{a['median_ms']:,.1f} ms〔产物面·last-good 基面——非 L2〕")
        elif st == "release-judged":
            parts.append(f"**{a['median_ms']:,.1f} ms**〔release 全链判定先例"
                         f"（016，仅限 diff）〕")
    return "；".join(parts) if parts else "—（无在档谱）"


def build_table() -> str:
    sys.path.insert(0, str(HERE))
    import compare  # noqa: E402  目标注册表复用（含版本/在位探针）
    data = {f"{t}_{tier}": _load_latest(f"compare-{t}-{tier}")
            for t in ("vscode", "zed", "bc5")
            for tier in ("5mb", "100mb")}
    anchors = _load_anchors()
    fp = compare._fingerprint()
    lines = []
    ap = lines.append
    ap("### 公开对比表（竞品侧先行件——PLAN-020）")
    ap("")
    ap("同机测量（数据驱动生成，下方区间禁手改；方法论/计时点定义/通道结论见"
       "[tools/compare/METHODOLOGY.md](../../../tools/compare/METHODOLOGY.md)）。"
       "**可复现三要素**：每数字附 {版本钉版, 环境指纹, 跑谱+离散}"
       "（JSONL 在 `tools/compare/results/` 入仓）。"
       "**语义注记（直比禁则）**：各对象 t_ready 判据不同——VS Code=renderer"
       " RSS 平台（文本模型物化）、Zed=首帧渲染（rope 视口惰性装载，非全量）、"
       "BC5=diff 结果产出、auto-edit open=全量装载完成（BENCH 标记包夹）——"
       "跨对象数字不可径直排序，语义列随行。")
    ap("")
    ap(f"环境：{fp['os']} · {fp['machine']} · {fp['cpu_cores']} 核 · "
       f"{fp['ram_gb']}GB（JSONL 头行含全指纹）")
    ap("")
    ap("| 指标（档） | 计时语义 | VS Code | Zed | Notepad++ | Beyond Compare 5 | auto-edit（本仓） |")
    ap("|---|---|---|---|---|---|---|")
    ap(f"| 打开 5 MB | 各对象 t_ready（语义列同左口径） "
       f"| {_competitor_cell(data['vscode_5mb'])} "
       f"| {_competitor_cell(data['zed_5mb'])} "
       f"| {'pending（未装——Q-1）' if not _nppp_present() else '—'} "
       f"| —（diff 对象不适用） "
       f"| —（无同档在档谱） |")
    ap(f"| 打开 100 MB | VS Code=RSS 物化；Zed=首帧（rope 惰性）；本仓=全量装载 "
       f"| {_competitor_cell(data['vscode_100mb'])} "
       f"| {_competitor_cell(data['zed_100mb'])} "
       f"| {'pending（未装——Q-1）' if not _nppp_present() else '—'} "
       f"| —（diff 对象不适用） "
       f"| {_our_cell(anchors, 'open_100mb')} |")
    ap(f"| diff 100 MB（文件对） | BC=report 产出；本仓=diff 端点全链墙钟 "
       f"（022 起=窗口形判定，全量对照在档） "
       f"| —（未测） | —（未测） | — "
       f"| {_competitor_cell(data['bc5_100mb'])} "
       f"| {_our_cell(anchors, 'diff_100mb')} |")
    ap(f"| 滚动帧率 | 各对象=编辑器滚动帧率（语义随行：本仓=present 频率"
       f"采样，面板率×0.9 判据——PLAN-022 协议在档） "
       f"| pending（未测——020 Q-2 捕获自动化双缺陷） "
       f"| pending（未测——020 Q-2 同） "
       f"| pending（未装——Q-1） "
       f"| —（diff 对象不适用） "
       f"| {_our_cell(anchors, 'scroll_fps')} |")
    ap("")
    ap("Notepad++ 缺位=安装属用户面（PLAN-020 §10 Q-1），装后 harness 补跑"
       "即得列（通道与 VS Code 同形）。**M4 收口口径（PLAN-024 Q-3 默认）**"
       "：竞品列完整性=对比表后续补列域，**非里程碑判定门——v0.1-M4 tag "
       "不等待 NP++**（三家竞品实数已足表位成立；2026-10-02 探测四路全空"
       "=未装在案）。**我方 L2 正式列=PLAN-021 直拉判定"
       "谱**（steady/open——armed 判定随格；diff 行=PLAN-022 窗口形清偿"
       "重判 PASS+021 全量形 FAIL 对照并陈；scroll 行=PLAN-022 首判 FAIL"
       "+PLAN-024 重判 FAIL 并陈——725 帧管线增量后同机复判，中位改善而 "
       "S5 残差[layout/shaping/draw]维持红，归因回执在档；未入表行 "
       "warm/idle 判定谱=budgets.json "
       "validity）。锚点/产物面数字不冒领（018 分层纪律表内延伸）。"
       "发布动作（对外宣传/链接分发）=数字齐后另行；本节=战略 §5 指定表位。")
    return "\n".join(lines)


def render_readme_section(table: str) -> str:
    """生成区间=[BEGIN..END]（仅表格本体）；节引言=README 静态面
    （仅在标记缺席的首次落位时一并写入，--check 不比对引言）。"""
    intro = ("## 公开对比表\n\n"
             "> 战略 §5 指定表位（M4 关键产出之三——竞品侧先行半件，PLAN-020）。\n"
             "> 本节表格由 `tools/compare/render_table.py` 数据驱动生成：\n"
             "> **手改禁则**——复跑生成器再提交（`--check` 断言复现一致）。\n\n")
    return intro + BEGIN + "\n" + table + "\n" + END + "\n"


def patch_readme(table: str) -> bool:
    """README 标记区间替换（只动 [BEGIN..END]，引言不属生成面）；
    无区间则连引言一并落位。返回是否改动。"""
    managed = BEGIN + "\n" + table + "\n" + END
    text = README.read_text(encoding="utf-8")
    if BEGIN in text and END in text:
        new = text[:text.index(BEGIN)] + managed + \
            text[text.index(END) + len(END):]
    else:
        new = text.rstrip("\n") + "\n\n" + render_readme_section(table)
    if new == text:
        return False
    README.write_text(new, encoding="utf-8", newline="")
    return True


def main() -> int:
    table = build_table()
    out = RESULTS / "table.md"
    out.write_text(table + "\n", encoding="utf-8")
    print(f"表格 → {out}")
    if "--check" in sys.argv:
        text = README.read_text(encoding="utf-8")
        want = BEGIN + "\n" + table + "\n" + END
        if BEGIN in text and END in text:
            cur = text[text.index(BEGIN):text.index(END) + len(END)]
            if cur == want:
                print("README 区间与生成器复现一致（--check 绿）")
                return 0
            print("FATAL: README 区间与生成器输出漂移（手改禁则）")
            return 1
        print("FATAL: README 无生成区间标记")
        return 1
    changed = patch_readme(table)
    print(f"README 区间{'已更新' if changed else '未变'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
