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
- state=l2-pending：**零数字**（正式判定位虚席——供① 解阻后 L2 形态
  重测补列；冒领禁则=PLAN-020 §2 约束①）。

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
                     "last-good 基面——regen 现势化=供① 维持）；非 L2"},
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
            {"state": "l2-pending", "metric": "open_100mb",
             "median_ms": None, "runs_ms": None, "source": None,
             "note": "L2 正式判定位虚席——供①（a2r 生成缺口三类残余）解阻"
                     "后 L2 形态重测补列"},
            {"state": "l2-pending", "metric": "steady_start",
             "median_ms": None, "runs_ms": None, "source": None,
             "note": "同上"},
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
