#!/usr/bin/env python3
r"""PLAN-025 T-00 消费探针（决策件）——大文件实例交互性与 1GB 四链可行性勘定.

背景：014 期登记「大文件实例 UI 线程硬卡死」（50MB 装载实例全部交互死
——T17 交互簇 17.2/17.3/17.4/17.8 blocked 三代在录，upstream m1-supply
§17）。728 后援分页 rope 交付后装载形态变化（全量物化→预扫页表+头窗
口）可能解除该症——本探针实证（前置决策门，不入矩阵计数）：

  ① freeze 探针：~100MB 装载后键盘派发应答性（导航键 Down/PageDown/
     Ctrl+End/Ctrl+Home + 字符键 x）——line/col 状态读回推进=交互活体；
     60s 无推进=死体（014 症状复现判定）。
  ② Ctrl+End 远跳=页表行数即答的下游观测（跳转墙钟+末行行号读回）。
  ③ 字符插入（autoui_keyboard "X"）→ toolbar save → byte-for-byte
     （期望="X"+原文字节流，md5 流式对照）+保存墙钟。
  ④ --full：1GB 全链同型（谱复现数据点——装载/远跳/保存墙钟 vs
     上游 p728-bench 4.0s/0.16ms/657ms 带外对照面）。

用法：cd specs/auto-edit/tests && python probe_p025_consume.py [--full]
前置：AUTO_BIN 指向含 728 的工具链（判据前核 auto --version）。
报告：stdout P025_* 标记 + probe_p025_consume_report.json。
退出码 0=勘定完成（判定值记录在报告；不改矩阵、零产品码触）。
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from desktop_mcp import (McpClient, _kill_proc_tree, find_button_by_icon,
                         pick_free_port, state_bool, state_int, state_str,
                         wait_for_server)

MB = 1024 * 1024
TESTS = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.normpath(os.path.join(TESTS, ".."))
AUTO_BIN = os.environ.get("AUTO_BIN") or "auto"


def make_fixture(path, target_bytes):
    """行体唯一化真内容 fixture（滚动/编辑真实负载形——生成式不入库）。"""
    n = 0
    written = 0
    with open(path, "w", encoding="utf-8", newline="") as f:
        while written < target_bytes:
            line = (f"line {n:08d} p025 probe payload for bigfile fixture "
                    "........................")
            f.write(line + "\n")
            written += len(line) + 1
            n += 1
    return n, written


def spawn(path):
    port = pick_free_port()
    env = {**os.environ, "AUTOUI_MCP_PORT": str(port),
           "APPDATA": tempfile.mkdtemp(prefix="p025_probe_"),
           "AUTO_OPEN_PATH": path, "AUTO_BENCH": "1"}
    proc = subprocess.Popen([AUTO_BIN, "run", "-r", "vm"], cwd=PROJECT,
                            env=env, stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)
    url = f"http://127.0.0.1:{port}/mcp"
    assert wait_for_server(url, 60), "P025 server never up"
    t = McpClient(url)
    for _ in range(20):
        s = t.snapshot()
        if "(rendered)" in s and s.count("onclick") > 0:
            break
        time.sleep(1)
    time.sleep(1.5)
    return proc, t


def wait_loaded(t, base, timeout=120):
    for _ in range(timeout * 4):
        c = state_str(t.state("console"), "console") or ""
        if "loaded: " in c and base in c:
            return True
        time.sleep(0.25)
    return False


def line_of(t):
    return state_int(t.state("line", "col"), "line")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true", help="追加 1GB 全链相")
    ap.add_argument("--skip-small", action="store_true")
    args = ap.parse_args()
    rpt = {"toolchain": subprocess.run([AUTO_BIN, "--version"],
                                       capture_output=True, text=True
                                       ).stdout.strip()}
    fx_dir = tempfile.mkdtemp(prefix="p025_fx_")
    cases = []
    if not args.skip_small:
        cases.append(("100mb", 100 * MB))
    if args.full:
        cases.append(("1gb", 1024 * MB))

    for tag, size in cases:
        fpath = os.path.join(fx_dir, f"p025_{tag}.txt")
        t0 = time.time()
        total_lines, total_bytes = make_fixture(fpath, size)
        gen_s = round(time.time() - t0, 2)
        time.sleep(3.0)  # 沉降窗（016 writeback 卫生）
        rec = {"tag": tag, "size": total_bytes, "lines": total_lines,
               "gen_s": gen_s}
        print(f"P025 {tag}: lines={total_lines} bytes={total_bytes} "
              f"gen={gen_s}s")
        proc, t = spawn(fpath)
        try:
            t0 = time.time()
            ok = wait_loaded(t, f"p025_{tag}.txt")
            rec["load_wall_s"] = round(time.time() - t0, 2)
            rec["loaded"] = ok
            st = t.state("big_active", "lang_active", "loaded_bytes",
                         "readonly_active", "console")
            rec["big_active"] = state_bool(st, "big_active")
            rec["readonly_active"] = state_bool(st, "readonly_active")
            rec["loaded_bytes"] = state_int(st, "loaded_bytes")
            print(f"P025 {tag} load: ok={ok} wall={rec['load_wall_s']}s "
                  f"big={rec['big_active']} ro={rec['readonly_active']} "
                  f"bytes={rec['loaded_bytes']}")

            # ① freeze 探针：交互应答性（Down ×3）
            l0 = line_of(t)
            t.call("autoui_keyboard", key="down")
            advanced = None
            for _ in range(20):
                time.sleep(0.25)
                l1 = line_of(t)
                if l1 > l0:
                    advanced = True
                    break
                advanced = False
            rec["down_dispatch"] = advanced
            print(f"P025 {tag} down: {l0} -> {line_of(t)} "
                  f"advanced={advanced}")

            # ② Ctrl+End 远跳（行数即答）
            t0 = time.time()
            t.call("autoui_keyboard", key="end", modifiers=["ctrl"])
            end_line = None
            for _ in range(80):
                time.sleep(0.25)
                cur = line_of(t)
                if cur > total_lines - 5:
                    end_line = cur
                    break
                end_line = cur
            rec["ctrl_end_s"] = round(time.time() - t0, 2)
            rec["ctrl_end_line"] = end_line
            rec["expected_last_line"] = total_lines
            print(f"P025 {tag} ctrl+end: line={end_line} "
                  f"(expect~{total_lines}) wall={rec['ctrl_end_s']}s")

            # Ctrl+Home 回起点
            t.call("autoui_keyboard", key="home", modifiers=["ctrl"])
            home_line = None
            for _ in range(20):
                time.sleep(0.25)
                if line_of(t) == 1:
                    home_line = 1
                    break
                home_line = line_of(t)
            rec["ctrl_home_line"] = home_line
            print(f"P025 {tag} ctrl+home: line={home_line}")

            # ③ 字符插入 + 保存 byte-for-byte
            # 期望流先算（save 覆写盘前）：md5(b"x" + 原文)
            h_exp = hashlib.md5()
            with open(fpath, "rb") as f:
                h_exp.update(b"x")
                while True:
                    chunk = f.read(1 << 20)
                    if not chunk:
                        break
                    h_exp.update(chunk)
            t.call("autoui_keyboard", key="x")
            time.sleep(0.6)
            snap = t.snapshot()
            sbtn = find_button_by_icon(snap, "save")
            t0 = time.time()
            saved = False
            if sbtn:
                t.click(sbtn)
                for _ in range(40):
                    c = state_str(t.state("console"), "console") or ""
                    if "saved (direct): " in c:
                        saved = True
                        break
                    time.sleep(0.25)
            rec["save_s"] = round(time.time() - t0, 2)
            rec["saved"] = saved
            size_after = os.path.getsize(fpath)
            rec["size_after"] = size_after
            rec["size_expect"] = total_bytes + 1
            h = hashlib.md5()
            with open(fpath, "rb") as f:
                while True:
                    chunk = f.read(1 << 20)
                    if not chunk:
                        break
                    h.update(chunk)
            rec["md5_saved"] = h.hexdigest()
            rec["md5_expect"] = h_exp.hexdigest()
            rec["byte_for_byte"] = (saved and size_after == total_bytes + 1
                                    and h.hexdigest() == h_exp.hexdigest())
            print(f"P025 {tag} save: ok={saved} wall={rec['save_s']}s "
                  f"size={size_after} (expect {total_bytes + 1}) "
                  f"b4b={rec['byte_for_byte']}")
        finally:
            _kill_proc_tree(proc)
        cases_done = rec
        rpt[tag] = cases_done

    out = os.path.join(TESTS, "probe_p025_consume_report.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(rpt, f, ensure_ascii=False, indent=1)
    print(f"P025 report -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
