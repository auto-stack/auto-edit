#!/usr/bin/env python3
"""PLAN-011 T-02/T-03/T-04 烟测：env 旁路开 diff → 状态断言 → 导航序列
→ 关闭复原。独立进程+真实 app（auto run -r vm merged）。"""

import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from desktop_mcp import (  # noqa: E402
    McpClient, wait_for_server, pick_free_port, _kill_proc_tree,
    find_button_by_text, state_str, state_int, state_bool,
)

AUTO_BIN = os.environ.get("AUTO_BIN") or shutil.which("auto") or ""
TESTS = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.normpath(os.path.join(TESTS, ".."))
FIX = os.path.abspath(os.path.join(TESTS, "fixtures", "diff"))

fails = []


def check(name, ok, detail=""):
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  [{detail}]" if not ok else ""))
    if not ok:
        fails.append(name)


def main():
    port = pick_free_port(9380)
    env = {**os.environ,
           "AUTO_DIFF_A": os.path.join(FIX, "scattered.a.txt"),
           "AUTO_DIFF_B": os.path.join(FIX, "scattered.b.txt")}
    proc = subprocess.Popen(
        [AUTO_BIN, "run", "-r", "vm"],
        cwd=PROJECT, env={**env, "AUTOUI_MCP_PORT": str(port)},
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    url = f"http://127.0.0.1:{port}/mcp"
    try:
        if not wait_for_server(url, 30):
            raise RuntimeError("MCP server did not start")
        mcp = McpClient(url)
        for _ in range(20):
            snap = mcp.snapshot()
            if "(rendered)" in snap and snap.count("onclick") > 0:
                break
            time.sleep(1)
        time.sleep(2.0)

        def st(*fields):
            return mcp.state(*fields)

        # ---- T-02: env 旁路开链（Tick 自开=矩阵驱动面；Ctrl+Alt+D=
        # 人工快捷键面——autoui_keyboard 合成路径 AltGr 疑虑不做矩阵依赖）----
        opened = False
        for _ in range(15):
            time.sleep(1)
            if state_bool(st("diff_open"), "diff_open"):
                opened = True
                break
        check("T-02 env 旁路自开（Tick 消费）", opened)
        s1 = st("diff_open", "diff_rows_count", "diff_hunk_count",
                "diff_hunk_idx", "diff_adds", "diff_dels",
                "diff_rows_truncated", "diff_degraded", "diff_err",
                "diff_title_a", "diff_title_b")
        print("  state:", s1.replace("\n", " ")[:400])
        check("T-02 diff_open=true（env 旁路开）", state_bool(s1, "diff_open") is True)
        check("T-02 hunks=3（scattered 三处远距）", state_int(s1, "diff_hunk_count") == 3,
              str(state_int(s1, "diff_hunk_count")))
        check("T-02 rows=21（golden 行数）", state_int(s1, "diff_rows_count") == 21,
              str(state_int(s1, "diff_rows_count")))
        check("T-02 +3/-3", state_int(s1, "diff_adds") == 3 and state_int(s1, "diff_dels") == 3,
              f"+{state_int(s1, 'diff_adds')}/-{state_int(s1, 'diff_dels')}")
        check("T-02 hunk_idx=0 归零", state_int(s1, "diff_hunk_idx") == 0,
              str(state_int(s1, "diff_hunk_idx")))
        check("T-02 err 空", (state_str(s1, "diff_err") or '""') in ('""', "''", ""),
              state_str(s1, "diff_err"))
        check("T-02 标题派生", "scattered" in (state_str(s1, "diff_title_a") or ""),
              state_str(s1, "diff_title_a"))
        check("T-03 truncated=false", state_bool(s1, "diff_rows_truncated") is False)

        # ---- T-03: 快照定位锚（状态条文本/按钮在根视图快照可见）----
        snap = mcp.snapshot()
        check("T-03 DIFF 状态条在快照", "DIFF" in snap and "scattered" in snap)
        check("T-03 行渲染在快照（pair 段节点 4-changed）", '"4-changed"' in snap)
        check("T-03 行渲染在快照（pair 段节点 19-changed）", '"19-changed"' in snap)
        # 着色样式不入 a11y 快照（for 动态行 style 行省略实勘）——颜色
        # 断言归截图/人工视觉门（T-15 口径）。
        b_next = find_button_by_text(snap, "下一处")
        b_prev = find_button_by_text(snap, "上一处")
        b_close = find_button_by_text(snap, "×")
        check("T-03 导航/关闭按钮在快照", bool(b_next) and bool(b_prev) and bool(b_close),
              f"next={b_next} prev={b_prev} close={b_close}")

        # ---- T-04: 导航推进/回绕（按钮=F7 同源 handler）----
        seq = []
        for lbl, el in (("next", b_next), ("next", b_next), ("next", b_next),
                        ("next", b_next), ("prev", b_prev)):
            mcp.click(el)
            time.sleep(0.6)
            seq.append(state_int(st("diff_hunk_idx"), "diff_hunk_idx"))
        print("  nav seq:", seq)
        check("T-04 推进/回绕序列 1,2,0,1,0", seq == [1, 2, 0, 1, 0], str(seq))

        # scroll 副作用：scroll_to 后 controller 状态可读（offset_y>0 于
        # idx=1/2 档；回绕到 0 时归 0 附近）——仅状态面断言（T-00③ 口径）。
        mcp.click(b_next)
        time.sleep(0.8)
        s3 = st("diff_hunk_idx")
        check("T-04 导航后 idx 推进（序列尾 0 → 1）", state_int(s3, "diff_hunk_idx") == 1,
              str(state_int(s3, "diff_hunk_idx")))

        # ---- T-03: 关闭复原（tab 集零扰动）----
        tabs_before = state_int(st("tab_count"), "tab_count")
        mcp.click(b_close)
        time.sleep(0.8)
        s4 = st("diff_open", "tab_count", "diff_rows_count", "diff_hunk_count")
        check("T-03 关闭 diff_open=false", state_bool(s4, "diff_open") is False)
        check("T-03 tab 集零扰动", state_int(s4, "tab_count") == tabs_before,
              f"{state_int(s4, 'tab_count')} vs {tabs_before}")
        check("T-03 行/导航态清零", state_int(s4, "diff_rows_count") == 0 and
              state_int(s4, "diff_hunk_count") == 0)

        print(f"\nRESULT: {'ALL PASS' if not fails else str(len(fails)) + ' FAILED: ' + ', '.join(fails)}")
        sys.exit(0 if not fails else 1)
    finally:
        _kill_proc_tree(proc)


if __name__ == "__main__":
    main()
