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
  PLAN-022 增 diff_100mb **窗口形清偿重判**行（verdict=pass——判定
  口径切窗口形，全量形 FAIL 行保留为对照，两行并陈对照不删）；
  state=l2-pending：**零数字**（机制保留——未判行虚席禁出数，冒领
  禁则=PLAN-020 §2 约束①）；PLAN-022 scroll_fps 行入列
  l2-pending 形（供⑨ 上游 i64 桥缺口——T-03 blocked 实证，零数字
  虚席位）。

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
# PLAN-022 窗口形清偿重判谱（9920 消费——判定口径切换；全量对照档
# 同谱在档 full-ref 行）
SRC_L2_DIFF_022 = Path("tools/bench/results/diff-20261001-144526.jsonl")
# PLAN-022 帧两行首判谱（供② 清偿后——scroll_fps armed FAIL 实数）
SRC_FRAME_022 = Path("tools/bench/results/frame-20261001-230957.jsonl")
# PLAN-024 帧两行重判谱（725 帧管线增量交付后同机复判——armed FAIL
# 维持；终跑谱=行值源，N=4 有效谱带随行注记）
SRC_FRAME_024 = Path("tools/bench/results/frame-20261002-141631.jsonl")
# PLAN-026 帧两行终判谱（731 S5 帧尾段增量化交付后同机下游重判——
# armed FAIL 维持（泵呈现交付通道归因）；终跑谱=行值源，N=4 全有效
# 谱带随行注记）
SRC_FRAME_026 = Path("tools/bench/results/frame-20261003-004030.jsonl")
# PLAN-027 帧两行终裁谱（735 消费+Q-1 双修修订协议〔读回切呈现面行通
# 道+16ms 节拍〕后同机下游终裁——type_latency armed PASS 首绿/
# scroll_fps armed FAIL 维持（帧泵回环吞吐上限定责）；终跑谱=行值
# 源，N=4 全有效谱带随行注记）
SRC_FRAME_027 = Path("tools/bench/results/frame-20261003-114158.jsonl")
# PLAN-028 帧两行复判终态谱（740 消费+Q-1 驱动通道裁定〔pipelined-
# paced k2@60Hz〕后同机下游终判——scroll_fps armed PASS 首绿转绿/
# type 复证维持；终跑谱=行值源，N=4 全有效谱带随行注记）
SRC_FRAME_028 = Path("tools/bench/results/frame-20261008-215117.jsonl")


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
    # PLAN-022 窗口形清偿重判直读
    l2diff22 = _rows(SRC_L2_DIFF_022)
    dl22 = next(r for r in l2diff22 if r.get("id") == "diff_100mb")
    # PLAN-022 帧两行首判直读（供② 清偿后——armed FAIL 实数）
    frame22 = _rows(SRC_FRAME_022)
    sf22 = next(r for r in frame22 if r.get("id") == "scroll_fps")
    # PLAN-024 帧两行重判直读（725 管线增量后同机复判——FAIL 维持）
    frame24 = _rows(SRC_FRAME_024)
    sf24 = next(r for r in frame24 if r.get("id") == "scroll_fps")
    # PLAN-026 帧两行终判直读（731 S5 增量化后同机下游重判——FAIL 维持）
    frame26 = _rows(SRC_FRAME_026)
    sf26 = next(r for r in frame26 if r.get("id") == "scroll_fps")
    # PLAN-027 帧两行终裁直读（735 消费+Q-1 双修修订协议——type 首绿/
    # scroll FAIL 维持；行通道主读行值源）
    frame27 = _rows(SRC_FRAME_027)
    sf27 = next(r for r in frame27 if r.get("id") == "scroll_fps")
    # PLAN-028 帧两行复判终态直读（740 消费+Q-1 驱动通道——scroll
    # 首绿转绿/type 复证；行通道主读行值源）
    frame28 = _rows(SRC_FRAME_028)
    sf28 = next(r for r in frame28 if r.get("id") == "scroll_fps")
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
            {"state": "l2", "metric": "diff_100mb",
             "median_ms": dl22["wall_ms_median"], "runs_ms": dl22["wall_ms_runs"],
             "budget_ms": 2000.0, "verdict": "pass",
             "source": str(SRC_L2_DIFF_022),
             "note": "PLAN-022 窗口形清偿重判（判定口径切换——9920 "
                     "/api/diff_files_window offset=0/limit=600 渲染 cap "
                     f"对齐「出结果」口径=全量 hunks/counts/rows_total["
                     f"{dl22.get('rows_total')}]+首窗 rows）：median "
                     f"{dl22['wall_ms_median']}ms ≤2000ms → armed PASS"
                     "——021 FAIL 清偿（6.5× 倍率；全量对照 5078.2ms 同谱"
                     "在档 diff_100mb_full 行）；工具链 "
                     "v0.4.2-2474-g95dcfb55b[含 716]"},
            {"state": "l2", "metric": "scroll_fps",
             "median_ms": sf22["fps"], "unit": "fps",
             "runs_ms": None, "window_ms": sf22.get("window_ms"),
             "budget": sf22.get("threshold"),
             "verdict": "fail", "source": str(SRC_FRAME_022),
             "note": "PLAN-022 T-03 供② 清偿后首判 armed FAIL（换行"
                     "连发 cursor-follow 滚动驱动）："
                     f"{sf22['fps']}fps vs ≥{sf22['threshold']}（面板"
                     "×0.9@60Hz）→ FAIL——键入帧全量重建管线容率上限"
                     "（~110ms/帧，type_latency 同根因；debug 对照谱"
                     " 11.4fps 同量级）；下界测量（MCP 轮询≤真值——"
                     "下界不过阈=FAIL 成立）；管线优化=725 已交付"
                     "（2026-10-02），重判见次行；"
                     "工具链 v0.4.2-2533-g9a71a5212（供⑨ 清偿后）"},
            {"state": "l2", "metric": "scroll_fps",
             "median_ms": sf24["fps"], "unit": "fps",
             "runs_ms": None, "window_ms": sf24.get("window_ms"),
             "budget": sf24.get("threshold"),
             "verdict": "fail", "source": str(SRC_FRAME_024),
             "note": "PLAN-024 T-01 重判（725 帧管线增量交付"
                     "[d7e48e8b5]后同机复判，release 工具链 "
                     "v0.4.2-2579-gb385534d7，N=4 有效谱）：终跑谱 "
                     f"{sf24['fps']}fps vs ≥{sf24['threshold']} → "
                     "FAIL 维持——四谱带 6.7/7.0/7.5/8.8fps 与 022 "
                     "首判 8.0fps 同带（滚动帧 begin→begin ~108ms/"
                     "帧：视口推进→新暴露行整形=S5 域主导，725 增量"
                     "管线对该域零效果=预期内；type_latency 中位 "
                     "1-4ms 大幅改善而尾部帧段外 ~110ms 同域——"
                     "归因回执 evidence-p024-frame-rejudge.md）；"
                     "下界测量口径不变；S5 增量化=auto-lang 余题"},
            {"state": "l2", "metric": "scroll_fps",
             "median_ms": sf26["fps"], "unit": "fps",
             "runs_ms": None, "window_ms": sf26.get("window_ms"),
             "budget": sf26.get("threshold"),
             "verdict": "fail", "source": str(SRC_FRAME_026),
             "note": "PLAN-026 T-01 终判（731 S5 帧尾段增量化交付"
                     "[30bda6831]后同机下游重判，release 工具链 "
                     "v0.4.2-2640-gcb2da5fba，N=4 全有效谱）：终跑谱 "
                     f"{sf26['fps']}fps vs ≥{sf26['threshold']} → "
                     "FAIL 维持——四谱带 8.1/8.4/8.8/9.5fps 三代同带"
                     "（022 8.0/024 6.7-8.8/026 8.1-9.5）；归因换代="
                     "S5 整形域清偿后的帧泵呈现交付节奏（024 ~108ms/"
                     "帧整形节奏消散→s5 子段 0.1-0.2ms——帧工作面全绿"
                     "实证；`__frame_pump` 消费滞后/合并→交付率实测 "
                     "8-9.5fps 双读法 FAIL 稳健）——呈现交付节奏+判定"
                     "通道语义适配=上游域余题第二段（归因回执 "
                     "evidence-p026-frame-rejudge.md）；下界测量口径"
                     "不变；Q-2 双态如实臂=发布门不解锁"},
            {"state": "l2", "metric": "scroll_fps",
             "median_ms": sf27["fps"], "unit": "fps",
             "runs_ms": None, "window_ms": sf27.get("window_ms"),
             "budget": sf27.get("threshold"),
             "verdict": "fail", "source": str(SRC_FRAME_027),
             "note": "PLAN-027 T-01 终裁（735 消费 delivered@4195f7af9"
                     "+Q-1 测量实施修订〔用户裁定双修：读回切呈现面行通"
                     "道+16ms 节拍〕后同机下游终裁，release 工具链 "
                     "v0.4.2-2704-gde3a64353，N=4 全有效谱）：终跑谱 "
                     f"{sf27['fps']}fps vs ≥{sf27['threshold']} → "
                     "FAIL 维持——四谱带 9.6-10.0fps（fprobe 对照列 "
                     "5.4-8.8fps 同带并陈）；红面定责=帧泵回环吞吐上限"
                     "（~95ms/圈→~10/s 与驱动节拍无关——16ms 节拍下"
                     "draw_end 间隔 91-95ms 恒定+突发内 0-1ms 连建+帧"
                     "工作面 2-3ms 全绿〔type_latency 027 首绿同谱实证"
                     "〕=735 §4 机制候选 (b) 下游定责）；四代谱系 022 "
                     "8.0/024 6.7-8.8/026 8.1-9.5/027 9.6-10.0 同带—"
                     "一泵上限主导；解锁前置=上游泵域清偿（复判通道已"
                     "备=修订协议即终态协议）；下界测量口径不变（值域"
                     "锚点切片）"},
            {"state": "l2", "metric": "scroll_fps",
             "median_ms": sf28["fps"], "unit": "fps",
             "runs_ms": None, "window_ms": sf28.get("window_ms"),
             "budget": sf28.get("threshold"),
             "verdict": "pass", "source": str(SRC_FRAME_028),
             "note": "PLAN-028 T-02 终判（740 消费 delivered@ab7a650bd"
                     "+Q-1 驱动通道裁定〔pipelined-paced k2@60Hz "
                     "fire-ahead——标定前置达成背书，阈值/语义 frozen〕"
                     "后同机下游终判，release 工具链 "
                     "v0.4.2-2769-g85f7159c2，N=4 全有效谱）：终跑谱 "
                     f"{sf28['fps']}fps vs ≥{sf28['threshold']} → "
                     "armed PASS 首绿——四代红谱收口（五谱带 "
                     "61.0-61.7+冒烟 61.0；drive 180@60Hz follow "
                     "1.017-1.028 交付随驱=740 §4d 契约下游复现）；"
                     "红面清偿=740 push 通道（027 泵回环 ~10/s 上限随"
                     "到达即投递+drain-to-empty 消解——T-00 标定 "
                     "evidence-p028-drive-channel：交付顶 ~55-61fps "
                     "全通道同顶+span 口径 55-57 对 54 薄余量带如实"
                     "注记）；五代谱系 022 8.0/024 6.7-8.8/026 "
                     "8.1-9.5/027 9.6-10.0/028 61.0-61.7；发布门解锁"
                     "注记=SD-01 PLAN-028 节（战略 §2.1 兑现时点）"},
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
