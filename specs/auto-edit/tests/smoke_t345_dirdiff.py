#!/usr/bin/env python3
"""PLAN-012 T-03/T-04 烟测：env 旁路开 dirs 面板 → counts/视图断言 → 过滤
→ 下钻/返回 → 同步动作 E2E（复制直执行/确认链/删除确认链）→ 错误形。
独立进程+真实 app（auto run -r vm merged）。同步动作走 tmp 拷贝/生成树
（fixtures 保 pristine——008 先例）；动作场景用最小单状态树保证按钮唯一
定位（find_button_by_text 精确正则）。"""

import os
import shutil
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from desktop_mcp import (  # noqa: E402
    McpClient, wait_for_server, pick_free_port, _kill_proc_tree,
    find_button_by_text, state_str, state_int, state_bool,
)

AUTO_BIN = os.environ.get("AUTO_BIN") or shutil.which("auto") or ""
TESTS = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.normpath(os.path.join(TESTS, ".."))
FIX = os.path.abspath(os.path.join(TESTS, "fixtures", "dirdiff"))

fails = []


def check(name, ok, detail=""):
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  [{detail}]" if not ok else ""))
    if not ok:
        fails.append(name)


def write_file(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(data)


def spawn_app(extra, wait_secs=20):
    port = pick_free_port()
    env = {**os.environ, "AUTOUI_MCP_PORT": str(port),
           "APPDATA": tempfile.mkdtemp(prefix="auto012_smoke_"), **extra}
    proc = subprocess.Popen(
        [AUTO_BIN, "run", "-r", "vm"],
        cwd=PROJECT, env=env,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    url = f"http://127.0.0.1:{port}/mcp"
    if not wait_for_server(url, 30):
        _kill_proc_tree(proc)
        raise RuntimeError("MCP server did not start")
    mcp = McpClient(url)
    for _ in range(wait_secs):
        snap = mcp.snapshot()
        if "(rendered)" in snap and snap.count("onclick") > 0:
            break
        time.sleep(1)
    time.sleep(2.0)
    return proc, mcp


def wait_dir_mode(mcp, timeout=15):
    for _ in range(timeout * 2):
        if state_bool(mcp.state("dir_mode"), "dir_mode"):
            return True
        time.sleep(0.5)
    return False


def click_btn(mcp, label, snap=None):
    el = find_button_by_text(snap or mcp.snapshot(), label)
    if el:
        mcp.click(el)
        return True
    return False


def main():
    # ================= S1: fixtures 全形态（只读断言） =================
    print("\nS1: fixtures 五形态 golden（env 旁路+过滤）")
    ta = tempfile.mkdtemp(prefix="p012_s1_a_")
    tb = tempfile.mkdtemp(prefix="p012_s1_b_")
    shutil.copytree(os.path.join(FIX, "base"), ta, dirs_exist_ok=True)
    shutil.copytree(os.path.join(FIX, "rev"), tb, dirs_exist_ok=True)
    proc, mcp = spawn_app({"AUTO_DIRDIFF_A": ta, "AUTO_DIRDIFF_B": tb})
    try:
        ok = wait_dir_mode(mcp)
        check("T-03 env 旁路自开（dir_mode=true）", ok)
        s1 = mcp.state("dir_mode", "diff_open", "diff_mode", "dir_total",
                       "dir_n_same", "dir_n_added", "dir_n_deleted",
                       "dir_n_modified", "dir_n_binary", "dir_view_count",
                       "dir_truncated", "dir_has_err", "dir_filter")
        print("  state:", s1.replace("\n", " ")[:300])
        check("T-03 diff_mode=dirs（契约字段）",
              (state_str(s1, "diff_mode") or "").strip('"') == "dirs",
              state_str(s1, "diff_mode"))
        check("T-03 golden counts（4/2/2/1/1）",
              state_int(s1, "dir_n_same") == 4
              and state_int(s1, "dir_n_added") == 2
              and state_int(s1, "dir_n_deleted") == 2
              and state_int(s1, "dir_n_modified") == 1
              and state_int(s1, "dir_n_binary") == 1,
              f"{state_int(s1, 'dir_n_same')}/{state_int(s1, 'dir_n_added')}"
              f"/{state_int(s1, 'dir_n_deleted')}"
              f"/{state_int(s1, 'dir_n_modified')}"
              f"/{state_int(s1, 'dir_n_binary')}")
        check("T-03 视图 10 条（all 过滤）",
              state_int(s1, "dir_view_count") == 10
              and state_int(s1, "dir_total") == 10,
              f"view={state_int(s1, 'dir_view_count')}")
        snap = mcp.snapshot()
        for rel in ("same.txt", "modified.txt", "deleted.txt", "added.txt",
                    "binary.bin", "[目录] nested", "nested/old.txt",
                    "nested/new.txt"):
            check(f"T-03 快照含 {rel}", rel in snap, "")
        for badge in ("增", "删", "改", "二进"):
            check(f"T-03 徽标 {badge} 在快照", badge in snap, "")
        # 过滤：纯 front 态（计数不变）
        check("T-03 删过滤钮在快照", click_btn(mcp, "删", snap), "")
        time.sleep(0.8)
        s2 = mcp.state("dir_filter", "dir_f_deleted", "dir_view_count",
                       "dir_n_deleted", "dir_n_added")
        check("T-03 过滤=deleted（2 条）",
              (state_str(s2, "dir_filter") or "").strip('"') == "deleted"
              and state_bool(s2, "dir_f_deleted") is True
              and state_int(s2, "dir_view_count") == 2,
              s2.replace("\n", " ")[:160])
        check("T-03 过滤纯 front 态（计数零变）",
              state_int(s2, "dir_n_deleted") == 2
              and state_int(s2, "dir_n_added") == 2,
              "过滤后计数不得变化")
        check("T-03 过滤后快照只余删行",
              "deleted.txt" in mcp.snapshot()
              and "added.txt" not in mcp.snapshot(), "")
        check("T-03 全部钮回切", click_btn(mcp, "全部"), "")
        time.sleep(0.8)
        s3 = mcp.state("dir_filter", "dir_view_count")
        check("T-03 回 all（10 条）",
              state_int(s3, "dir_view_count") == 10,
              str(state_int(s3, "dir_view_count")))
    finally:
        _kill_proc_tree(proc)

    # ================= S2: 最小单状态树（下钻+同步 E2E） =================
    print("\nS2: 下钻 + 同步动作 E2E（单状态树=按钮唯一定位）")
    ta = tempfile.mkdtemp(prefix="p012_s2_a_")
    tb = tempfile.mkdtemp(prefix="p012_s2_b_")
    write_file(os.path.join(ta, "mod.txt"), "aaa\n")
    write_file(os.path.join(tb, "mod.txt"), "bbb-longer\n")
    write_file(os.path.join(ta, "gone.txt"), "gone\n")
    write_file(os.path.join(tb, "new.txt"), "new\n")
    write_file(os.path.join(ta, "same.txt"), "same\n")
    write_file(os.path.join(tb, "same.txt"), "same\n")
    proc, mcp = spawn_app({"AUTO_DIRDIFF_A": ta, "AUTO_DIRDIFF_B": tb})
    try:
        ok = wait_dir_mode(mcp)
        check("S2 面板开（counts 1/1/1/1/0）",
              ok and state_int(mcp.state("dir_n_modified"),
                               "dir_n_modified") == 1, "")
        snap = mcp.snapshot()
        # ---- 下钻：「改」条目点击 → file 模式（011 视图复用）----
        check("S2 改行钮在快照", click_btn(mcp, "mod.txt", snap), "")
        time.sleep(1.5)
        s4 = mcp.state("diff_mode", "dir_mode", "diff_open",
                       "diff_rows_count", "dir_from_dirs", "diff_hunk_count")
        check("T-04 下钻 file 模式（diff_mode=file/dir_mode=false）",
              (state_str(s4, "diff_mode") or "").strip('"') == "file"
              and state_bool(s4, "dir_mode") is False
              and state_bool(s4, "diff_open") is True,
              s4.replace("\n", " ")[:160])
        check("T-04 下钻 rows 到达（011 视图复用）",
              state_int(s4, "diff_rows_count") > 0
              and state_int(s4, "diff_hunk_count") > 0,
              f"rows={state_int(s4, 'diff_rows_count')}")
        snap4 = mcp.snapshot()
        check("T-04 返回目录钮在快照", "返回目录" in snap4, "")
        # ---- 返回目录：entries 保留不重比 ----
        check("S2 返回目录钮点击", click_btn(mcp, "返回目录", snap4), "")
        time.sleep(1.0)
        s5 = mcp.state("diff_mode", "dir_mode", "dir_view_count",
                       "dir_n_same", "dir_from_dirs")
        check("T-04 返回目录态（entries 保留）",
              (state_str(s5, "diff_mode") or "").strip('"') == "dirs"
              and state_bool(s5, "dir_mode") is True
              and state_int(s5, "dir_view_count") == 4
              and state_int(s5, "dir_n_same") == 1,
              s5.replace("\n", " ")[:160])
        # ---- 复制直执行（单侧恢复语义——无确认）：删过滤下唯一 → 钮 ----
        check("S2 删过滤", click_btn(mcp, "删"), "")
        time.sleep(0.8)
        snap = mcp.snapshot()
        check("S2 → 钮唯一定位", click_btn(mcp, "→", snap), "")
        time.sleep(1.5)
        check("T-05 复制直执行磁盘 E2E（gone.txt →右侧）",
              os.path.isfile(os.path.join(tb, "gone.txt")), "")
        s6 = mcp.state("dir_n_deleted", "dir_n_same", "dir_view_count",
                       "dir_filter", "dir_confirm_open", "dir_f_deleted")
        check("T-05 重比后计数（删 0/同 2）+过滤保持",
              state_int(s6, "dir_n_deleted") == 0
              and state_int(s6, "dir_n_same") == 2
              and state_bool(s6, "dir_f_deleted") is True
              and state_bool(s6, "dir_confirm_open") is False,
              s6.replace("\n", " ")[:160])
        # ---- 删除确认链：增过滤下唯一 ✕ 钮 ----
        check("S2 增过滤", click_btn(mcp, "增"), "")
        time.sleep(0.8)
        snap = mcp.snapshot()
        check("S2 ✕ 钮唯一定位", click_btn(mcp, "✕", snap), "")
        time.sleep(1.0)
        s7 = mcp.state("dir_confirm_open", "dir_pending_op")
        check("T-05 确认弹层出现（删除恒确认）",
              state_bool(s7, "dir_confirm_open") is True,
              s7.replace("\n", " ")[:120])
        check("S2 确认执行钮点击", click_btn(mcp, "确认执行"), "")
        time.sleep(1.5)
        check("T-05 删除磁盘 E2E（new.txt 消失）",
              not os.path.exists(os.path.join(tb, "new.txt")), "")
        s8 = mcp.state("dir_n_added", "dir_confirm_open")
        check("T-05 重比后计数（增 0）+弹层关",
              state_int(s8, "dir_n_added") == 0
              and state_bool(s8, "dir_confirm_open") is False,
              s8.replace("\n", " ")[:120])
        # ---- 复制确认链（双侧覆盖语义）：改过滤下 → 钮 ----
        check("S2 改过滤", click_btn(mcp, "改"), "")
        time.sleep(0.8)
        snap = mcp.snapshot()
        check("S2 改行 → 钮点击", click_btn(mcp, "→", snap), "")
        time.sleep(1.0)
        s9 = mcp.state("dir_confirm_open")
        check("T-05 覆盖复制恒确认（双侧条目）",
              state_bool(s9, "dir_confirm_open") is True, "")
        check("S2 确认执行（覆盖）", click_btn(mcp, "确认执行"), "")
        time.sleep(1.5)
        with open(os.path.join(tb, "mod.txt"), encoding="utf-8") as f:
            content = f.read()
        check("T-05 覆盖复制磁盘 E2E（mod.txt=左侧内容）",
              content == "aaa\n", repr(content))
        s10 = mcp.state("dir_n_modified", "dir_n_same")
        check("T-05 重比后计数（改 0/同 3）",
              state_int(s10, "dir_n_modified") == 0
              and state_int(s10, "dir_n_same") == 3,
              s10.replace("\n", " ")[:120])
        # ---- 关闭复原：面板 ×（整个 dirdiff 出口；tab 零扰动）----
        tabs_before = state_int(mcp.state("tab_count"), "tab_count")
        check("S2 面板 × 点击", click_btn(mcp, "×"), "")
        time.sleep(0.8)
        s11 = mcp.state("dir_mode", "diff_open", "dir_view_count", "tab_count",
                        "diff_mode")
        check("T-03 关闭复原（dir/diff 全清+tab 零扰动）",
              state_bool(s11, "dir_mode") is False
              and state_bool(s11, "diff_open") is False
              and state_int(s11, "dir_view_count") == 0
              and state_int(s11, "tab_count") == tabs_before,
              s11.replace("\n", " ")[:160])
    finally:
        _kill_proc_tree(proc)

    # ================= S3: 错误形（根缺失不静默） =================
    print("\nS3: 错误形（根缺失）")
    proc, mcp = spawn_app({
        "AUTO_DIRDIFF_A": "Z:/nonexistent_p012_smoke",
        "AUTO_DIRDIFF_B": os.environ.get("TEMP", "/tmp")})
    try:
        time.sleep(3)
        s12 = mcp.state("dir_mode", "diff_open", "dir_has_err", "console")
        console = state_str(s12, "console") or ""
        check("T-02 根缺失 err 形（面板不开+err 记录+console）",
              state_bool(s12, "dir_mode") is False
              and state_bool(s12, "diff_open") is False
              and state_bool(s12, "dir_has_err") is True
              and "dirdiff:" in console,
              f"err={state_str(s12, 'dir_err')} console={console[:80]!r}")
    finally:
        _kill_proc_tree(proc)

    print(f"\nRESULT: {'ALL PASS' if not fails else str(len(fails)) + ' FAILED: ' + ', '.join(fails)}")
    sys.exit(0 if not fails else 1)


if __name__ == "__main__":
    main()
