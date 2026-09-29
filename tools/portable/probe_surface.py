#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""probe_surface.py — PLAN-019 T-02：产物 exe 面 G-4 护栏探针。

动机（T-00③ 护栏定形）：018 锚点档（bench.py open/steady/warm）=
release 工具链 VM 轨——对产物 profile/deps 手段**不敏感**（手段只改
生成物构建，不改工具链二进制）。防「瘦体积肥延迟」的真护栏=产物 exe
直拉面——本探针经 bench.py 现役测量基元（run_release_tracked/_l2_suite
单源复用，零新方法学）测产物面三行：
  steady 代理（spawn→bench_ws_loaded，2 跑弃暖机）+ idle mem
  open 100MB（装载墙钟标记包夹）+ mem_loaded
a2r 门旁路注记：bench.py proxy --mode l2 前置 perf.py a2r（现上游
阻塞——供①）；本探针为 regen 阻塞期复用基面的记录性通道，供① 清偿
后回归 proxy --mode l2 标准链（本件不做武装判定，数字=对照面记账）。

用法：
  python tools/portable/probe_surface.py --variant <tag> [--runs 2]
  python tools/portable/probe_surface.py --list      # 汇总已有谱

退出码：0=数字齐；1=产物缺席/标记缺失/拓扑门红。
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
BENCH = HERE.parent / "bench"
sys.path.insert(0, str(BENCH))
import bench  # noqa: E402  （单源复用测量基元；副作用=常量初始化，无进程面）

RESULTS = HERE / "results"


def main() -> int:
    ap = argparse.ArgumentParser(description="产物 exe 面护栏探针（PLAN-019 T-02）")
    ap.add_argument("--variant", default="baseline", help="手段变体标签（入 JSONL）")
    ap.add_argument("--runs", type=int, default=2, help="启动分解跑数（首跑弃暖机）")
    ap.add_argument("--open-mb", type=int, default=100, help="打开计时档（MB）")
    ap.add_argument("--list", action="store_true", help="汇总已有谱后退出")
    args = ap.parse_args()

    if args.list:
        for p in sorted(RESULTS.glob("surface-*.jsonl")):
            for ln in p.read_text(encoding="utf-8").splitlines():
                d = json.loads(ln)
                if d.get("type") == "surface_summary":
                    print(f"{d['variant']:24s} steady={d['steady_mean_ms']}ms "
                          f"open{d['open_mb']}mb={d['open_ms']}ms "
                          f"idle={d['idle_mean_mb']}MB ({p.name})")
        return 0

    exe = bench._release_exe()
    if exe is None:
        bench._log("FATAL: 产物缺席（rust-workspace/target/release/auto-edit.exe）"
                   "——先 build_portable 或 cargo build --release")
        return 1
    fp = bench._fingerprint()
    bench._log(f"产物面探针 [{args.variant}]：{exe}（{exe.stat().st_size:,} B）")
    suite = bench._l2_suite(args.runs, [args.open_mb], fp)
    if suite is None:
        return 1

    steady = [r["steady_start_ms"] for r in suite["startup"] if not r["warmup"]]
    idle = [r["mem_idle"][0] for r in suite["startup"]
            if not r["warmup"] and r["mem_idle"] and r["mem_idle"][0]]
    opens = suite["opens"]
    summary = {
        "type": "surface_summary",
        "variant": args.variant,
        "ts": datetime.now().strftime("%Y%m%d-%H%M%S"),
        "exe_size_bytes": exe.stat().st_size,
        "steady_runs_ms": steady,
        "steady_mean_ms": round(sum(steady) / len(steady), 1) if steady else None,
        "open_mb": args.open_mb,
        "open_ms": opens[0]["open_ms"] if opens else None,
        "mem_loaded_mb": (round(opens[0]["mem_loaded"][0] / 1048576)
                          if opens and opens[0].get("mem_loaded")
                          and opens[0]["mem_loaded"][0] else None),
        "idle_mean_mb": round(sum(idle) / len(idle) / 1048576, 1) if idle else None,
        "toolchain": fp,
        "note": "产物面记录性通道（regen 上游阻塞期基面；非武装判定——"
                "供① 清偿后回归 proxy --mode l2 标准链）",
    }
    RESULTS.mkdir(exist_ok=True)
    out = RESULTS / f"surface-{summary['ts']}.jsonl"
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        for row in suite["startup"]:
            f.write(json.dumps({"type": "startup_run", "variant": args.variant,
                                **row}, ensure_ascii=False) + "\n")
        for row in opens:
            f.write(json.dumps({"type": "open_run", "variant": args.variant,
                                **row}, ensure_ascii=False) + "\n")
        f.write(json.dumps(summary, ensure_ascii=False) + "\n")
    bench._log(f"[{args.variant}] steady={summary['steady_mean_ms']}ms "
               f"open={summary['open_ms']}ms idle={summary['idle_mean_mb']}MB "
               f"→ {out.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
