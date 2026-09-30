#!/usr/bin/env python3
"""anchors.py — PLAN-020 T-03 我方锚点占位列（三态列数据，直读零重算）。

数据源=仓内在档 JSONL（直读——**不重跑不重算**，数字逐字对照）：

- state=anchor（锚点，VM 形态注记）：tools/bench/results/
  open-20260929-110820.jsonl（PLAN-018 首批锚点——open_100mb median
  841.0ms，release 工具链全链记账形态，非 L2 正式判定）；
- state=surface（产物面，last-good 基面注记）：tools/portable/results/
  surface-20260929-193232.jsonl（PLAN-019 probe_surface final-v2b——
  open 38.2ms/steady 21.2ms/idle 10.2MB，非 L2）；
- state=release-judged（diff 行专用——018 分层纪律「016 release 全链
  判定先例仅限 diff」）：tools/bench/results/diff-20260928-152047.jsonl
  （diff_100mb median 1906.0ms budget PASS；旁证 152015=1971.3ms）；
- state=l2（PLAN-021 起）：**L2 直拉判定实数**（供① 解阻后判定谱
  直读，verdict 随行——steady/diff[714 r3 工具链]+open[714 r4 工具链]）；
  state=l2-pending：**零数字**（机制保留——未判行虚席禁出数，冒领
  禁则=PLAN-020 §2 约束①）。

用法：
  python tools/compare/anchors.py            # 提取 → results/anchors.json
  python tools/compare/anchors.py --verify   # 逐字对照断言（AC-04）
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent          # 仓根（tools/compare/ → 上两级）
RESULTS = HERE / "results"

# 直读源（仓内相对路径——worktree/主检出同布局）
SRC_OPEN_018 = Path("tools/bench/results/open-20260929-110820.jsonl")
SRC_SURFACE_019 = Path("tools/portable/results/surface-20260929-193232.jsonl")
SRC_DIFF_016 = Path("tools/bench/results/diff-20260928-152047.jsonl")
SRC_DIFF_016_B = Path("tools/bench/results/diff-20260928-152015.jsonl")
# PLAN-021 L2 直拉判定谱（供① 解阻后判定——acf653d3f[714 r3]/
# e93a717da[714 r4 动态注册键贯通]工具链）
SRC_L2_STEADY = Path("tools/bench/results/steady-20260930-204546.jsonl")
SRC_L2_DIFF = Path("tools/bench/results/diff-20260930-205147.jsonl")
SRC_L2_OPEN = Path("tools/bench/results/open-20260930-230121.jsonl")


def _rows(rel: Path) -> list[dict]:
    p = ROOT / rel
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines()
            if l.strip()]


def extract() -> dict:
    open18 = _rows(SRC_OPEN_018)
    osum = next(r for r in open18 if r.get("id") == "open_100mb_summary")
    oruns = [r["open_ms"] for r in open18
             if r.get("id") == "open_100mb" and not r.get("warmup")]
    surf = _rows(SRC_SURFACE_019)
    ss = next(r for r in surf if r.get("type") == "surface_summary")
    diff = _rows(SRC_DIFF_016)
    dsum = next(r for r in diff if r.get("id") == "diff_100mb")
    diff_b = _rows(SRC_DIFF_016_B)
    dsum_b = next(r for r in diff_b if r.get("id") == "diff_100mb")
    # PLAN-021 L2 直拉判定谱直读
    steady_l2 = _rows(SRC_L2_STEADY)
    ssum = next(r for r in steady_l2 if r.get("id") == "steady_summary")
    l2diff = _rows(SRC_L2_DIFF)
    dl2 = next(r for r in l2diff if r.get("id") == "diff_100mb")
    l2open = _rows(SRC_L2_OPEN)
    ol2 = next(r for r in l2open if r.get("id") == "open_100mb_summary")
    return {
        "schema": "p020-our-anchors/1",
        "generated": "tools/compare/anchors.py 直读（零重算——AC-04 逐字对照）",
        "states": [
            {"state": "anchor", "metric": "open_100mb",
             "median_ms": osum["median_ms"], "runs_ms": oruns,
             "source": str(SRC_OPEN_018),
             "note": "PLAN-018 首批锚点——VM 形态（release 工具链全链记账）；"
                     "非 L2 正式判定（不冒领）"},
            {"state": "surface", "metric": "open_100mb",
             "median_ms": ss["open_ms"], "runs_ms": None,
             "source": str(SRC_SURFACE_019),
             "note": "PLAN-019 portable 产物面 probe_surface（final-v2b，"
                     "last-good 基面）；非 L2"},
            {"state": "surface", "metric": "steady_start",
             "median_ms": ss["steady_mean_ms"], "runs_ms": ss["steady_runs_ms"],
             "source": str(SRC_SURFACE_019),
             "note": "同上——产物面护栏数字（供① 阻塞期记录性通道）"},
            {"state": "release-judged", "metric": "diff_100mb",
             "median_ms": dsum["wall_ms_median"],
             "runs_ms": dsum["wall_ms_runs"],
             "source": str(SRC_DIFF_016),
             "note": "PLAN-016 release 全链判定先例（仅限 diff——018 分层"
                     "纪律）；budget PASS ≤2000ms；旁证 "
                     f"{SRC_DIFF_016_B.name}={dsum_b['wall_ms_median']}ms"},
            {"state": "l2", "metric": "steady_start",
             "median_ms": ssum["median_ms"], "runs_ms": ssum["runs_ms"],
             "mean_ms": ssum["mean_ms"], "budget_ms": ssum["budget_ms"],
             "verdict": "pass", "source": str(SRC_L2_STEADY),
             "note": "PLAN-021 L2 直拉形态正式判定（供① 解阻后首判，"
                     "工具链 v0.4.2-2366-gacf653d3f[714 r3]）：mean "
                     f"{ssum['mean_ms']}ms ≤{ssum['budget_ms']:.0f}ms → "
                     "armed PASS——硬门禁正式判定绿（L2 唯一预算效力"
                     "首次兑现；018 VM 形态 232.6ms 归因随形态消失）"},
            {"state": "l2", "metric": "diff_100mb",
             "median_ms": dl2["wall_ms_median"], "runs_ms": dl2["wall_ms_runs"],
             "budget_ms": 2000.0, "verdict": "fail", "source": str(SRC_L2_DIFF),
             "note": "PLAN-021 L2 直拉形态正式判定（back 面——release "
                     "auto-edit-back /api/diff_files，016 server 侧语义"
                     f"同型）：median {dl2['wall_ms_median']}ms >2000ms → "
                     "armed FAIL（记录性）；归因=包络 rows 全量投影+双层 "
                     "JSON 在 a2r back 形态放大（016 rows 惰性投影 want）"
                     "——016 VM 形态 1906ms 达标为形态对照"},
            {"state": "l2", "metric": "open_100mb",
             "median_ms": ol2["median_ms"], "runs_ms": ol2["runs_ms"],
             "budget_ms": ol2["budget_ms"], "verdict": "pass",
             "source": str(SRC_L2_OPEN),
             "note": "PLAN-021 L2 直拉形态正式判定（供① 全清偿[714 r4 "
                     f"e93a717da 动态注册键贯通]后补跑）：median "
                     f"{ol2['median_ms']}ms ≤{ol2['budget_ms']:.0f}ms → "
                     "armed PASS——硬门禁正式判定绿（018 记账形态 841.0ms "
                     "同量级复现）；「滚动不掉帧」半行=供② 解阻后"},
        ],
    }


def verify(data: dict) -> int:
    """逐字对照断言（AC-04）：anchors.json 数字==源文件当前直读数字。"""
    fresh = extract()
    bad = []
    for a, b in zip(data["states"], fresh["states"]):
        if a != b:
            bad.append((a.get("metric"), a.get("state")))
    if bad or len(data["states"]) != len(fresh["states"]):
        print(f"FATAL: 逐字对照失配：{bad or '行数漂移'}")
        return 1
    print(f"逐字对照绿：{len(fresh['states'])} 行三态数据与源 JSONL 全等")
    return 0


def main() -> int:
    RESULTS.mkdir(exist_ok=True)
    data = extract()
    if "--verify" in sys.argv:
        cur = json.loads((RESULTS / "anchors.json").read_text(encoding="utf-8"))
        return verify(cur)
    out = RESULTS / "anchors.json"
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8")
    print(f"三态锚点数据 → {out}")
    for s in data["states"]:
        print(f"  [{s['state']:14}] {s['metric']:12} = {s['median_ms']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
