#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""probe_frame_channel.py — PLAN-027 T-00 帧通道勘定探针（Q-1 材料）。

735 回执 v2（auto-lang docs/plans/evidence/735/downstream-handoff-v2.md）
§3/§4 建议的下游校准——测量实施修订案的数字底座（判定阈值/语义零变更，
修订仅测量实施面：读回通道+驱动节拍，Q-1 用户裁定件）：

  A. 通道新鲜度勘定——fprobe_present（9919=auto.frame.present_ms，泵通知
     消费时刻）vs 行通道 present（[P725-FRAME] 行列，735 配对修复后
     =draw_end 优先真值）逐键对照。|Δ| 小（≈消费即呈现）=带内→本件零
     上游依赖（9920 不接线）；带外→9920 微件路由 upstream（条件位）。
  B. 驱动节拍校准——
     B1 MCP 调用地板：背靠背 autoui_type 无 sleep（每调用墙钟——驱动
        率上限 = 1/call_floor）；
     B2 16ms 节拍键入窗（30 键）：行通道 total_ms（present−begin，键入
        帧真帧时）P50/P95 预演 + 窗内 distinct draw_end 率；
     B3 16ms 节拍换行窗（3s，022 窗长）：窗内 distinct draw_end 率
        （scroll 判定面预演——阈值=面板×0.9）。
  双读法并录（fprobe 快照差分对照列+行通道主读）——Q-1 材料双态如实。

用法：python probe_frame_channel.py --auto-bin <auto.exe> --out <jsonl>
退出码：0=探针完成（判定材料落盘）；1=探针自身失败（app/MCP 未起）。
行通道解析复用 ladder735.py 同款 [P725-FRAME] 正则（draw_end 可选列——
735 前工具链该列缺席=present 列语义不同，本探针要求 735 后工具链）。
"""
import argparse
import json
import os
import re
import socket
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent          # tools/bench
ROOT = HERE.parents[1]
PROJECT = Path(os.environ.get("PERF_PROJECT") or ROOT / "specs" / "auto-edit")
PORT_BASE = 9360
NLCHAR = chr(10)

# 与 auto-lang ladder735.py 全同（[P725-FRAME] 行——735 后含可选 draw_end_ms）。
FRAME_RE = re.compile(
    r"\[P725-FRAME\] begin=(-?\d+) present=(-?\d+) s1_payload_us=(\d+) "
    r"s2_vm_us=(\d+) s3a_mcp_us=(\d+) s3b_build_us=(\d+) s4_element_us=(\d+) "
    r"s5_layout_us=(\d+) s5_shaping_us=(\d+) s5_draw_us=(\d+) "
    r"builds=(\d+) dirty=(-?\d+)(?: draw_end_ms=(-?\d+))?"
)


def _ts() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def _log(msg: str) -> None:
    print(f"[probe {_ts()[-6:]}] {msg}", flush=True)


def parse_row(line: str):
    m = FRAME_RE.search(line)
    if not m:
        return None
    g = m.groups()
    return {
        "begin": int(g[0]), "present": int(g[1]),
        "s2_us": int(g[3]), "s3b_us": int(g[5]), "s4_us": int(g[6]),
        "s5_layout_us": int(g[7]), "s5_shaping_us": int(g[8]),
        "s5_draw_us": int(g[9]),
        "builds": int(g[10]), "dirty": int(g[11]),
        "draw_end_ms": int(g[12]) if g[12] is not None else -1,
    }


def mcp_call(url: str, name: str, args_json: str, timeout: int = 10) -> str:
    import urllib.request
    body = json.dumps({"jsonrpc": "2.0", "method": "tools/call",
                       "params": {"name": name, "arguments": args_json},
                       "id": 1}).encode()
    req = urllib.request.Request(url, data=body,
                                 headers={"Content-Type": "application/json"})
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode())
    dt_ms = (time.perf_counter() - t0) * 1000.0
    content = data.get("result", {}).get("content", [])
    return (content[0]["text"] if content else ""), dt_ms


def mcp_state(url: str, fields: list):
    txt, dt = mcp_call(url, "autoui_state", {"fields": list(fields)})
    out = {}
    for line in txt.splitlines():
        m = re.match(r"\s*(\w+):\s*(-?\d+)", line)
        if m:
            out[m.group(1)] = int(m.group(2))
    return out, dt


def read_log_tail(path: Path, start_line: int) -> list:
    rows = []
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for i, line in enumerate(f):
                if i < start_line:
                    continue
                r = parse_row(line)
                if r:
                    rows.append(r)
    except OSError:
        pass
    return rows


def count_lines(path: Path) -> int:
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return sum(1 for _ in f)
    except OSError:
        return 0


def pct(sorted_vals, q):
    if not sorted_vals:
        return None
    return sorted_vals[min(len(sorted_vals) - 1, int(len(sorted_vals) * q))]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--auto-bin", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--freshness-keys", type=int, default=10)
    ap.add_argument("--type-keys", type=int, default=60)
    ap.add_argument("--window-s", type=float, default=3.0)
    args = ap.parse_args()

    fp_exe = args.auto_bin
    try:
        ver = subprocess.run([fp_exe, "--version"], capture_output=True,
                             text=True, timeout=30).stdout.strip()
    except Exception as e:  # noqa: BLE001
        _log(f"FATAL: --version 败: {e}")
        return 1
    _log(f"toolchain: {ver}")

    fdir = HERE / "fixtures" / "frame"
    fdir.mkdir(parents=True, exist_ok=True)
    fx = fdir / "frame_drive.txt"
    if not fx.exists() or fx.stat().st_size < 5000:
        with open(fx, "w", encoding="utf-8", newline="") as f:
            for i in range(120):
                f.write(f"line {i:05d} frame drive payload content"
                        f"{' CHANGED' if i % 97 == 0 else ''}\n")

    port = None
    for cand in range(PORT_BASE, PORT_BASE + 60):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", cand)) != 0:
                port = cand
                break
    ad = tempfile.mkdtemp(prefix="bench-p027-probe-appdata-")
    env = {**os.environ, "AUTO_BENCH": "1", "AUTO_FRAME_BENCH": "1",
           "AUTOUI_MCP_PORT": str(port), "APPDATA": ad,
           "AUTO_OPEN_PATH": str(fx), "AUTO_PROJECT_DIR": str(PROJECT)}
    log_path = Path(ad) / "app.log"
    log_f = open(log_path, "w", encoding="utf-8")
    proc = subprocess.Popen([fp_exe, "run", "-r", "vm"], cwd=PROJECT, env=env,
                            stdout=log_f, stderr=subprocess.STDOUT)
    base = f"http://127.0.0.1:{port}/mcp"
    out_rows = [{"type": "meta", "time": _ts(), "toolchain": ver,
                 "auto_bin": fp_exe, "app_log": str(log_path),
                 "freshness_keys": args.freshness_keys,
                 "type_keys": args.type_keys,
                 "window_s": args.window_s}]

    def write_out():
        with open(args.out, "w", encoding="utf-8", newline="\n") as f:
            for r in out_rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    exit_code = 0
    try:
        ta_id = None
        for _ in range(15):
            try:
                txt, _ = mcp_call(base, "autoui_snapshot", {})
                m = re.search(r"textarea #(\w+)", txt)
                ta_id = m.group(1) if m else None
                if ta_id:
                    break
            except Exception:  # noqa: BLE001
                pass
            time.sleep(1)
        if not ta_id:
            _log("FATAL: textarea 未定位")
            return 1

        def type_key(text: str):
            try:
                _, dt = mcp_call(base, "autoui_type",
                                 {"element_id": ta_id, "text": text,
                                  "clear_first": False})
                return True, dt
            except Exception:  # noqa: BLE001
                return False, None

        up = False
        for _ in range(60):
            try:
                mcp_state(base, ["fprobe_n"])
                up = True
                break
            except Exception:  # noqa: BLE001
                time.sleep(1)
        if not up:
            _log("FATAL: MCP fprobe 未起")
            return 1
        time.sleep(6.0)

        # ---- A. 通道新鲜度：逐键长窗读回+值域对齐（首键弃——首建域） ----
        # 行发射点=下一帧 begin（旋转）——逐键读回时末帧行未发射，直接
        # 逐键配对会差一帧。fprobe 值与行 draw_end 同 frame_bench 时基
        # （进程毫秒单调），改值域对齐：Δ_i = V_i − max{draw_end ≤ V_i}
        # =泵消费滞后（R-1 序障：消费 ≥ 同帧呈现，Δ≥0 带内=新鲜）。
        fp_reads = []
        for k in range(args.freshness_keys):
            ok, _ = type_key("x")
            if not ok:
                continue
            time.sleep(0.35)
            st, _ = mcp_state(base, ["fprobe_begin", "fprobe_present",
                                     "fprobe_n"])
            fp_reads.append({"key": k, "fp_present": st.get("fprobe_present")
                             or 0})
        # 旋转尾帧：追加两键强制行发射，再整体解析行通道。
        type_key("x")
        time.sleep(0.2)
        type_key("x")
        time.sleep(0.5)
        all_rows = read_log_tail(log_path, 0)
        dirty_rows = [r for r in all_rows if r["dirty"] == 1 and r["s2_us"] > 0
                      and r["present"] > 0]
        paired = sum(1 for r in dirty_rows if r["draw_end_ms"] > 0
                     and r["present"] == r["draw_end_ms"])
        de_seq = sorted(r["draw_end_ms"] for r in dirty_rows
                        if r["draw_end_ms"] > 0)
        import bisect
        freshness = []
        for rd in fp_reads:
            v = rd["fp_present"]
            i = bisect.bisect_right(de_seq, v)
            if i == 0:
                continue
            truth = de_seq[i - 1]
            freshness.append({
                "type": "freshness", "key": rd["key"],
                "fp_present": v, "matched_draw_end": truth,
                "delta_consumption_vs_truth_ms": v - truth,
            })
        rec = {"type": "freshness_summary",
               "reads": len(fp_reads), "matched": len(freshness),
               "dirty_rows": len(dirty_rows),
               "row_pairing_pct": round(100.0 * paired / len(dirty_rows), 1)
               if dirty_rows else None,
               "deltas_ms": [r["delta_consumption_vs_truth_ms"]
                             for r in freshness]}
        out_rows.append(rec)
        if rec["deltas_ms"]:
            ds = sorted(rec["deltas_ms"])
            _log(f"A 通道新鲜度: reads={rec['reads']} matched={rec['matched']} "
                 f"行配对={rec['row_pairing_pct']}% "
                 f"Δ(消费−呈现) P50={pct(ds, 0.5)}ms max={ds[-1]}ms "
                 f"min={ds[0]}ms")
        else:
            _log("A 通道新鲜度: 无匹配样本")

        # ---- B1. MCP 调用地板（背靠背无 sleep） ----
        floors = []
        for _ in range(15):
            ok, dt = type_key("x")
            if ok and dt is not None:
                floors.append(round(dt, 1))
        floors_sorted = sorted(floors)
        rec = {"type": "call_floor", "n": len(floors_sorted),
               "p50_ms": pct(floors_sorted, 0.5),
               "min_ms": floors_sorted[0] if floors_sorted else None,
               "max_ms": floors_sorted[-1] if floors_sorted else None,
               "drive_rate_ceiling_hz": round(1000.0 / pct(floors_sorted, 0.5), 1)
               if floors_sorted else None}
        out_rows.append(rec)
        _log(f"B1 调用地板: n={rec['n']} p50={rec['p50_ms']}ms "
             f"min={rec['min_ms']}ms max={rec['max_ms']}ms "
             f"→ 驱动率上限≈{rec['drive_rate_ceiling_hz']}Hz")
        time.sleep(1.0)

        # ---- B2. 16ms 节拍键入窗（type 判定面预演） ----
        mark = count_lines(log_path)
        t0w = time.perf_counter()
        for _ in range(args.type_keys):
            type_key("x")
            time.sleep(0.016)
        time.sleep(0.5)
        t1w = time.perf_counter()
        rows = read_log_tail(log_path, mark)
        dirty = [r for r in rows if r["dirty"] == 1 and r["s2_us"] > 0
                 and r["present"] > 0]
        dirty = dirty[1:]  # 首帧弃暖机（首建域）
        totals = sorted((r["present"] - r["begin"]) for r in dirty)
        draw_ends = sorted({r["draw_end_ms"] for r in dirty
                            if r["draw_end_ms"] > 0})
        win_s = t1w - t0w
        rec = {"type": "type_window", "keys": args.type_keys,
               "win_s": round(win_s, 2), "dirty_frames": len(dirty),
               "total_p50_ms": pct(totals, 0.5),
               "total_p95_ms": pct(totals, 0.95),
               "total_max_ms": totals[-1] if totals else None,
               "distinct_draw_end": len(draw_ends),
               "draw_end_per_sec": round(len(draw_ends) / win_s, 2)
               if win_s > 0 else None}
        out_rows.append(rec)
        _log(f"B2 键入窗(16ms 节拍): dirty={len(dirty)} "
             f"total P50={rec['total_p50_ms']}ms P95={rec['total_p95_ms']}ms "
             f"max={rec['total_max_ms']}ms "
             f"draw_end/s={rec['draw_end_per_sec']}")
        time.sleep(1.0)

        # ---- B3. 16ms 节拍换行窗（scroll 判定面预演，022 窗长 3s） ----
        mark = count_lines(log_path)
        t0w = time.perf_counter()
        n_drive = 0
        while time.perf_counter() - t0w < args.window_s:
            type_key(NLCHAR)
            n_drive += 1
            time.sleep(0.016)
        time.sleep(0.5)
        t1w = time.perf_counter()
        rows = read_log_tail(log_path, mark)
        draw_ends = sorted({r["draw_end_ms"] for r in rows
                            if r["draw_end_ms"] > 0})
        win_s = t1w - t0w
        rec = {"type": "scroll_window", "drive_calls": n_drive,
               "win_s": round(win_s, 2), "distinct_draw_end": len(draw_ends),
               "draw_end_per_sec": round(len(draw_ends) / win_s, 2)
               if win_s > 0 else None}
        out_rows.append(rec)
        _log(f"B3 换行窗(16ms 节拍): drive={n_drive} 次 "
             f"distinct_draw_end={len(draw_ends)} "
             f"→ {rec['draw_end_per_sec']}/s")
        write_out()
        _log(f"JSONL → {args.out}")
    finally:
        log_f.close()
        if proc.poll() is None:
            proc.kill()
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)],
                       capture_output=True)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
