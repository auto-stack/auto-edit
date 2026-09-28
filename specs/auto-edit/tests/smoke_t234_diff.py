#!/usr/bin/env python3
"""PLAN-011 T-02/T-03/T-04 烟测 + PLAN-015 T-04 内联视图断言族：env 旁路
开 diff → 状态断言 → 导航序列 → 内联切换（推导器对照/零重比/导航/回切）
→ 双 cap（big_reorder 现役 fixture）→ 关闭复原。独立进程+真实 app
（auto run -r vm merged）。"""

import json
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
    find_button_by_text, find_button_by_onclick, find_element_by_event,
    wait_console_line, state_str, state_int, state_bool,
)
from probe_diff import derive_inline, inline_shape_counts  # noqa: E402

AUTO_BIN = os.environ.get("AUTO_BIN") or shutil.which("auto") or ""
TESTS = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.normpath(os.path.join(TESTS, ".."))
FIX = os.path.abspath(os.path.join(TESTS, "fixtures", "diff"))

fails = []


def check(name, ok, detail=""):
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  [{detail}]" if not ok else ""))
    if not ok:
        fails.append(name)


def golden_rows(name):
    with open(os.path.join(FIX, f"{name}.golden.json"), encoding="utf-8") as f:
        g = json.load(f)
    return g["rows"]


def launch(port, env_extra):
    env = {**os.environ, **env_extra}
    # PLAN-017: APPDATA 隔离（矩阵 _t15_app 同款）——真实用户 APPDATA 的
    # auto-edit-session.json 会被会话恢复链读入（tab 集污染 → P17② tab
    # 计数假红；跨跑自毒循环）。隔离后零会话恢复，tab 集确定。
    env["APPDATA"] = tempfile.mkdtemp(prefix="auto011_smoke_ad_")
    return subprocess.Popen(
        [AUTO_BIN, "run", "-r", "vm"],
        cwd=PROJECT, env={**env, "AUTOUI_MCP_PORT": str(port)},
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main():
    port = pick_free_port(9380)
    proc = launch(port, {
        "AUTO_DIFF_A": os.path.join(FIX, "scattered.a.txt"),
        "AUTO_DIFF_B": os.path.join(FIX, "scattered.b.txt")})
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

        # ---- PLAN-015 T-04: 内联视图断言族①②③（scattered） ----
        # 零重比基线=envelope 派生面（切换前后必须逐字段不变——AC-02）。
        s_base = st("diff_rows_count", "diff_hunk_count", "diff_adds",
                    "diff_dels", "diff_dbg_pair", "diff_dbg_del",
                    "diff_dbg_add", "diff_dbg_ctx")
        base = {f: state_int(s_base, f) for f in
                ("diff_rows_count", "diff_hunk_count", "diff_adds",
                 "diff_dels", "diff_dbg_pair", "diff_dbg_del",
                 "diff_dbg_add", "diff_dbg_ctx")}
        snap = mcp.snapshot()
        b_inline = find_button_by_text(snap, "内联")
        check("P15 side 态切换钮在快照（内联）", bool(b_inline), str(b_inline))

        mcp.click(b_inline)
        time.sleep(0.8)
        s5 = st("diff_vmode", "diff_vmode_inline", "diff_irows_count",
                "diff_irows_truncated", "diff_dbg_idel", "diff_dbg_iadd",
                "diff_dbg_ictx", "diff_rows_count", "diff_hunk_count",
                "diff_adds", "diff_dels", "diff_dbg_pair", "diff_dbg_del",
                "diff_dbg_add", "diff_dbg_ctx")
        # ① 内联渲染语义：irows 计数/形状分布=golden 推导期望
        exp_irows, exp_trunc = derive_inline(golden_rows("scattered"))
        exp_cnts = inline_shape_counts(exp_irows)
        check("P15① vmode=inline（契约字段+旗标）",
              state_str(s5, "diff_vmode") == '"inline"' or
              state_str(s5, "diff_vmode") == "inline",
              state_str(s5, "diff_vmode"))
        check("P15① irows 计数=推导期望",
              state_int(s5, "diff_irows_count") == len(exp_irows),
              f"{state_int(s5, 'diff_irows_count')} vs {len(exp_irows)}")
        check("P15① 形状计数 idel/iadd/ictx=推导期望",
              state_int(s5, "diff_dbg_idel") == exp_cnts["del"] and
              state_int(s5, "diff_dbg_iadd") == exp_cnts["add"] and
              state_int(s5, "diff_dbg_ictx") == exp_cnts["ctx"],
              f"({state_int(s5, 'diff_dbg_idel')},{state_int(s5, 'diff_dbg_iadd')},"
              f"{state_int(s5, 'diff_dbg_ictx')}) vs {exp_cnts}")
        check("P15① 截断注记=false（scattered 小形态）",
              state_bool(s5, "diff_irows_truncated") is False)
        # ② 切换纯态零重比：envelope 派生面逐字段不变（AC-02）
        zero_ok = all(state_int(s5, f) == base[f] for f in base)
        check("P15② 切换零重比（envelope 派生面不变）", zero_ok,
              str({f: (base[f], state_int(s5, f)) for f in base
                   if state_int(s5, f) != base[f]}))
        snap = mcp.snapshot()
        check("P15② 钮文翻转（并排 在快照/内联 不在）",
              bool(find_button_by_text(snap, "并排")) and
              not find_button_by_text(snap, "内联"))
        # ③ 内联态 hunk 导航：两步下一处 2→回绕 0（idx 进入段=1；内联扫
        # irows 域，回绕语义与并排态同源）
        seq_i = []
        for _ in range(2):
            mcp.click(b_next)
            time.sleep(0.6)
            seq_i.append(state_int(st("diff_hunk_idx"), "diff_hunk_idx"))
        check("P15③ 内联态导航推进+回绕 [2,0]", seq_i == [2, 0], str(seq_i))
        s6 = st("diff_hunk_pos")
        check("P15③ 位次串随动（1/3）", state_str(s6, "diff_hunk_pos") in ("1/3", '"1/3"'),
              state_str(s6, "diff_hunk_pos"))
        # 回切并排：纯态清空投影+envelope 仍不变
        b_side = find_button_by_text(mcp.snapshot(), "并排")
        mcp.click(b_side)
        time.sleep(0.8)
        s7 = st("diff_vmode", "diff_vmode_inline", "diff_irows_count",
                "diff_irows_truncated", "diff_hunk_count", "diff_adds",
                "diff_dels")
        check("P15② 回切 side（vmode 复位+投影清空）",
              (state_str(s7, "diff_vmode") in ("side", '"side"')) and
              state_int(s7, "diff_irows_count") == 0 and
              state_bool(s7, "diff_irows_truncated") is False,
              state_str(s7, "diff_vmode"))
        check("P15② 回切零重比（hunks/adds/dels 不变）",
              state_int(s7, "diff_hunk_count") == base["diff_hunk_count"] and
              state_int(s7, "diff_adds") == base["diff_adds"] and
              state_int(s7, "diff_dels") == base["diff_dels"])
        # 再切回内联（重建幂等）
        mcp.click(find_button_by_text(mcp.snapshot(), "内联"))
        time.sleep(0.8)
        s8 = st("diff_irows_count", "diff_dbg_idel")
        check("P15① 重建幂等（再切 irows 同数）",
              state_int(s8, "diff_irows_count") == len(exp_irows) and
              state_int(s8, "diff_dbg_idel") == exp_cnts["del"],
              f"{state_int(s8, 'diff_irows_count')}")

        # ---- T-03: 关闭复原（tab 集零扰动）----
        tabs_before = state_int(st("tab_count"), "tab_count")
        mcp.click(b_close)
        time.sleep(0.8)
        s4 = st("diff_open", "tab_count", "diff_rows_count", "diff_hunk_count",
                "diff_vmode", "diff_vmode_inline", "diff_irows_count")
        check("T-03 关闭 diff_open=false", state_bool(s4, "diff_open") is False)
        check("T-03 tab 集零扰动", state_int(s4, "tab_count") == tabs_before,
              f"{state_int(s4, 'tab_count')} vs {tabs_before}")
        check("T-03 行/导航态清零", state_int(s4, "diff_rows_count") == 0 and
              state_int(s4, "diff_hunk_count") == 0)
        check("P15 关闭复位 vmode=side+投影清空",
              state_str(s4, "diff_vmode") in ("side", '"side"') and
              state_int(s4, "diff_irows_count") == 0,
              state_str(s4, "diff_vmode"))
    finally:
        _kill_proc_tree(proc)


def cap_instance():
    """PLAN-015 T-04 断言族④：双 cap（PLAN-016 修复轮改形：生成式 700
    全换 fixture——700 pair 行>600 双截断；原 big_reorder 形在引擎时代
    修复后=del/add 块分离换位，pair 展开 ×2 前提失效——改形与矩阵
    15.14 同款，fixtures 保 pristine）。"""
    port = pick_free_port(9385)
    dtmp = tempfile.mkdtemp(prefix="p015_cap_")
    pa = os.path.join(dtmp, "cap.a.txt")
    pb = os.path.join(dtmp, "cap.b.txt")
    with open(pa, "w", encoding="utf-8") as f:
        f.write(chr(10).join(f"old line {i} content" for i in range(700)))
    with open(pb, "w", encoding="utf-8") as f:
        f.write(chr(10).join(f"new line {i} content" for i in range(700)))
    proc = launch(port, {"AUTO_DIFF_A": pa, "AUTO_DIFF_B": pb})
    url = f"http://127.0.0.1:{port}/mcp"
    try:
        if not wait_for_server(url, 30):
            raise RuntimeError("MCP server did not start (cap instance)")
        mcp = McpClient(url)
        for _ in range(20):
            snap = mcp.snapshot()
            if "(rendered)" in snap and snap.count("onclick") > 0:
                break
            time.sleep(1)
        opened = False
        for _ in range(15):
            time.sleep(1)
            if state_bool(mcp.state("diff_open"), "diff_open"):
                opened = True
                break
        check("P15④ cap 实例自开", opened)
        s1 = mcp.state("diff_rows_count", "diff_rows_truncated",
                       "diff_degraded", "diff_hunk_count")
        check("P15④ 信封级截断（rows=600+truncated）",
              state_int(s1, "diff_rows_count") == 600 and
              state_bool(s1, "diff_rows_truncated") is True,
              f"rows={state_int(s1, 'diff_rows_count')} "
              f"trunc={state_bool(s1, 'diff_rows_truncated')}")
        b_inline = find_button_by_text(mcp.snapshot(), "内联")
        mcp.click(b_inline)
        time.sleep(1.2)
        s2 = mcp.state("diff_irows_count", "diff_irows_truncated",
                       "diff_vmode")
        check("P15④ 内联级截断（irows=600+truncated）",
              state_int(s2, "diff_irows_count") == 600 and
              state_bool(s2, "diff_irows_truncated") is True,
              f"irows={state_int(s2, 'diff_irows_count')} "
              f"trunc={state_bool(s2, 'diff_irows_truncated')}")
        snap = mcp.snapshot()
        check("P15④ 双注记并列在快照（渲染截断+内联截断）",
              "渲染截断" in snap and "内联截断" in snap)
        b_close = find_button_by_text(snap, "×")
        mcp.click(b_close)
        time.sleep(0.8)
        check("P15④ cap 实例关闭复原",
              state_bool(mcp.state("diff_open"), "diff_open") is False)
    finally:
        _kill_proc_tree(proc)


def edit_loop_instance():
    """PLAN-017 P17 断言族（开发期烟测，不入矩阵计数——015 惯例）：
    差异侧编辑回路主链——jumpB 落点读回→ReplaceAll 编辑（live mark）→
    保存→视图自动重开重比（vmode 保持+计数变形+重比行+落盘）→面板
    live 预览域零扰动（diff_buf 面板关态）。矩阵 15.20/15.21 同链
    E2E（子组全谱以矩阵为准，本烟测=开发期快速回归）。"""
    port = pick_free_port(9390)
    dtmp = tempfile.mkdtemp(prefix="p017_loop_")
    pa = os.path.join(dtmp, "loop.a.txt")
    pb = os.path.join(dtmp, "loop.b.txt")
    with open(pa, "w", encoding="utf-8", newline="") as f:
        f.write("\n".join(f"L{i}" for i in range(1, 9)) + "\n")
    with open(pb, "w", encoding="utf-8", newline="") as f:
        f.write("\n".join(
            f"L{i}" if i != 5 else "L5-CHANGED"
            for i in range(1, 9)) + "\n")
    proc = launch(port, {"AUTO_DIFF_A": pa, "AUTO_DIFF_B": pb})
    url = f"http://127.0.0.1:{port}/mcp"
    try:
        if not wait_for_server(url, 30):
            raise RuntimeError("MCP server did not start (edit loop instance)")
        mcp = McpClient(url)
        for _ in range(20):
            snap = mcp.snapshot()
            if "(rendered)" in snap and snap.count("onclick") > 0:
                break
            time.sleep(1)
        time.sleep(1.5)

        def st(*fields):
            return mcp.state(*fields)

        def click_text(label, tries=4):
            for _ in range(tries):
                b = find_button_by_text(mcp.snapshot(), label)
                if b:
                    mcp.click(b)
                    time.sleep(1.0)
                    return True
                time.sleep(0.6)
            return False

        s0 = st("diff_open", "diff_adds", "diff_dels", "diff_vmode")
        check("P17① 旁路自开（+1/-1 side）",
              state_bool(s0, "diff_open") is True and
              state_int(s0, "diff_adds") == 1 and
              state_int(s0, "diff_dels") == 1)
        # jumpB（新开 B tab+装载落点 line=2）
        ok_jump = click_text("编辑 B 侧")
        pend_clear = False
        for _ in range(20):
            if not state_bool(st("diff_edit_pend"), "diff_edit_pend"):
                pend_clear = True
                break
            time.sleep(0.5)
        s1 = st("diff_open", "tab_count", "diff_edit_return", "diff_edit_pend")
        check("P17② jumpB（视图藏+tab=3+return 旗标+pend 清）",
              ok_jump and pend_clear and
              state_bool(s1, "diff_open") is False and
              state_int(s1, "tab_count") == 3 and
              state_bool(s1, "diff_edit_return") is True,
              f"jump={ok_jump} pend_clear={pend_clear} "
              f"open={state_bool(s1, 'diff_open')} "
              f"tabs={state_int(s1, 'tab_count')} "
              f"ret={state_bool(s1, 'diff_edit_return')} "
              f"pend={state_bool(s1, 'diff_edit_pend')}")
        # 读回（切走切回 SyncCursor 面）
        seed = find_button_by_text(mcp.snapshot(), "main.at")
        if seed:
            mcp.click(seed)
            time.sleep(0.6)
        btab = find_button_by_text(mcp.snapshot(), "loop.b.txt")
        if btab:
            mcp.click(btab)
            time.sleep(0.6)
        check("P17③ 落点读回（hunk0 b1=1[ctx=3 窗] → line=2）",
              state_int(st("line"), "line") == 2,
              state_int(st("line"), "line"))
        # ReplaceAll L→Z（全行变形）
        m = find_button_by_text(mcp.snapshot(), "编辑")
        if m:
            mcp.click(m)
            time.sleep(0.8)
        ok_menu = click_text("替换…")
        snap = mcp.snapshot()
        qi = find_element_by_event(snap, "FindInput", attr="oninput")
        ri = find_element_by_event(snap, "FindReplaceInput", attr="oninput")
        typed = False
        if qi and ri:
            mcp.call("autoui_type", text="L", element_id=qi, clear_first=True)
            time.sleep(0.4)
            mcp.call("autoui_type", text="Z", element_id=ri, clear_first=True)
            time.sleep(0.4)
            typed = True
        ok_ra = click_text("全部替换")
        time.sleep(2.0)
        # 保存（工具栏 ActSave——B active）→钩子重开视图重比
        saved = False
        for _ in range(4):
            sb = find_button_by_onclick(mcp.snapshot(), "ActSave")
            if sb:
                mcp.click(sb)
                time.sleep(1.5)
                saved = True
                break
            time.sleep(0.8)
        time.sleep(1.0)
        s2 = st("diff_open", "diff_adds", "diff_dels", "diff_vmode",
                "diff_edit_return")
        con = wait_console_line(mcp, "已重比（保存触发") or ""
        disk = open(pb, encoding="utf-8").read()
        check("P17④ 保存自动重比（视图自动重开+8/8 变形+vmode 保持+"
              "return 清+重比行+落盘）",
              ok_menu and typed and ok_ra and saved and
              state_bool(s2, "diff_open") is True and
              state_int(s2, "diff_adds") == 8 and
              state_int(s2, "diff_dels") == 8 and
              state_str(s2, "diff_vmode") in ("side", '"side"') and
              state_bool(s2, "diff_edit_return") is False and
              "已重比（保存触发" in con and
              "Z1" in disk and "L5" not in disk,
              f"menu={ok_menu} typed={typed} ra={ok_ra} saved={saved} "
              f"s2={s2[:120]}")
    finally:
        _kill_proc_tree(proc)


if __name__ == "__main__":
    main()
    cap_instance()
    edit_loop_instance()
    print(f"\nRESULT: {'ALL PASS' if not fails else str(len(fails)) + ' FAILED: ' + ', '.join(fails)}")
    sys.exit(0 if not fails else 1)
