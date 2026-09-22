#!/usr/bin/env python3
"""PLAN-008 T-00 内核行为勘（决策件）——BOM/EOL/非法 UTF-8 字节形态探针.

四组探针（vm merged 实例，真实 auto-edit 应用）：
  ① BOM：EF BB BF + 正文 → 装载 → save 落盘回读（U+FEFF 是否驻留 text；
     write_text 直写语义下，落盘首三字节保留 == text 含 U+FEFF 前缀字符）
  ② 非法 UTF-8（0xFF/0x80 字节）→ Phase A: read_text/read_text_range
     HTTP 错误形态；Phase B: load_file 返回值/装载后状态/save 尝试是否
     清写原文件（T-04 的危害基线证据）
  ③ CRLF：装载→save 回读（core 规范化与否）；再开一份做编辑步
     （编辑菜单全选→工具栏 cut→undo）→save 回读（buffer 漏斗归一化与否）
  ④ CR-only：同③无编辑步
Phase A = back HTTP（auto run --server vm）端点形态；
Phase B = vm merged UI 全链（AUTO_OPEN_PATH 打开 + 工具栏 save 落盘），
磁盘字节 census（\r\n / \n / \r 计数、BOM 前缀、sha256）。

用法：cd specs/auto-edit/tests && python probe_bytefidelity.py
前置同 desktop_mcp.py（requests、AUTO_BIN 或 PATH 的 auto）。
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from desktop_mcp import (  # noqa: E402
    McpClient, wait_for_server, pick_free_port, _kill_proc_tree,
    find_button_by_icon, find_button_by_onclick, find_button_by_text,
    state_int, state_str,
)

AUTO_BIN = os.environ.get("AUTO_BIN") or shutil.which("auto") or ""
PROJECT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def census(data: bytes):
    """Byte-form census of a file's content."""
    crlf = data.count(b"\r\n")
    nl = data.count(b"\n") - crlf
    cr = data.count(b"\r") - crlf
    return {
        "bytes": len(data), "bom": data.startswith(b"\xef\xbb\xbf"),
        "crlf": crlf, "lf": nl, "cr": cr,
        "sha256": hashlib.sha256(data).hexdigest()[:16],
    }


def wait_console(mcp, needle, count, timeout=12):
    """Poll until the console field contains `needle` at least `count` times."""
    for _ in range(int(timeout / 0.25)):
        c = state_str(mcp.state("console"), "console") or ""
        if c.count(needle) >= count:
            return c
        time.sleep(0.25)
    return state_str(mcp.state("console"), "console") or ""


def click_toolbar(mcp, icon):
    snap = mcp.snapshot()
    el = find_button_by_icon(snap, icon)
    if el is None:
        return False
    mcp.click(el)
    time.sleep(0.5)
    return True


def launch_app(env_extra):
    """Start a fresh `auto run -r vm` instance; return (proc, url, log_path)."""
    port = pick_free_port()
    log = tempfile.NamedTemporaryFile(
        prefix="p008_probe_", suffix=".log", delete=False, mode="w",
        encoding="utf-8", errors="replace")
    proc = subprocess.Popen(
        [AUTO_BIN, "run", "-r", "vm"],
        cwd=PROJECT, env={**os.environ, "AUTOUI_MCP_PORT": str(port), **env_extra},
        stdout=log, stderr=subprocess.STDOUT)
    url = f"http://127.0.0.1:{port}/mcp"
    if not wait_for_server(url, 30):
        _kill_proc_tree(proc)
        raise RuntimeError("MCP server did not start")
    mcp = McpClient(url)
    # Wait for the rendered snapshot AND its computed-events pass: the
    # styled_vtree clone can briefly surface without event bodies (upstream
    # race, self-heals) — an events-less snapshot breaks button location.
    for _ in range(15):
        s = mcp.snapshot()
        if "(rendered)" in s and s.count("onclick") > 0:
            break
        time.sleep(1)
    return proc, mcp, log.name


def phase_a(fixdir):
    """Back-HTTP endpoint shapes (error/envelope forms)."""
    print("\n" + "=" * 60)
    print("Phase A: back HTTP endpoint shapes (--server vm)")
    print("=" * 60)
    port = pick_free_port(9350)
    proc = subprocess.Popen(
        [AUTO_BIN, "run", "--server", "vm", "-B", str(port)],
        cwd=PROJECT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    base = f"http://127.0.0.1:{port}"
    for _ in range(30):
        try:
            requests.get(base + "/api/ws_root", timeout=2)
            break
        except requests.ConnectionError:
            time.sleep(1)
    out = {}
    try:
        cases = [
            ("read_text BOM", "/api/read_text", {"path": os.path.join(fixdir, "bom_utf8.at")}),
            ("read_text invalid", "/api/read_text", {"path": os.path.join(fixdir, "invalid_utf8.bin")}),
            ("range BOM w3", "/api/read_text_range", {"path": os.path.join(fixdir, "bom_utf8.at"), "offset": 0, "limit": 3}),
            ("range invalid", "/api/read_text_range", {"path": os.path.join(fixdir, "invalid_utf8.bin"), "offset": 0, "limit": 16}),
            ("range crlf w10", "/api/read_text_range", {"path": os.path.join(fixdir, "crlf.at"), "offset": 0, "limit": 10}),
        ]
        for label, ep, params in cases:
            r = requests.get(base + ep, params=params, timeout=10)
            body = r.text
            out[label] = {"status": r.status_code, "body_head": body[:120]}
            print(f"  {label}: HTTP {r.status_code}  {body[:120]!r}")
    finally:
        _kill_proc_tree(proc)
    return out


def open_fixture(mcp, path, size):
    """Click '+' (ActOpen reads AUTO_OPEN_PATH) and wait for the load line."""
    snap = mcp.snapshot()
    plus = find_button_by_onclick(snap, "ActOpen")
    if plus is None:
        raise RuntimeError("ActOpen (+) button not found")
    mcp.click(plus)
    base = os.path.basename(path)
    for _ in range(48):
        c = state_str(mcp.state("console"), "console") or ""
        if f"loaded: " in c and base in c:
            return c
        time.sleep(0.25)
    raise TimeoutError(f"load line for {base} never appeared")


def save_fixture(mcp, path):
    """Click the save toolbar icon and wait for the 'saved:' console line."""
    before = (state_str(mcp.state("console"), "console") or "").count("saved:")
    if not click_toolbar(mcp, "save"):
        raise RuntimeError("save toolbar button not found")
    for _ in range(40):
        c = state_str(mcp.state("console"), "console") or ""
        if c.count("saved:") > before:
            return
        time.sleep(0.25)
    raise TimeoutError(f"saved: line for {path} never appeared")


def phase_b_roundtrip(fixdir, name, src_bytes):
    """Open→(no edit)→save roundtrip census; returns (before, after, state)."""
    path = os.path.join(fixdir, name)
    with open(path, "wb") as f:
        f.write(src_bytes)
    before = open(path, "rb").read()
    proc, mcp, log = launch_app({"AUTO_OPEN_PATH": path})
    try:
        c = open_fixture(mcp, path, len(before))
        st = {
            "loaded_bytes": state_int(mcp.state("loaded_bytes"), "loaded_bytes"),
            "title": state_str(mcp.state("title_active"), "title_active"),
            "console_tail": c[-160:],
        }
        save_fixture(mcp, path)
        after = open(path, "rb").read()
        return census(before), census(after), st, log
    finally:
        _kill_proc_tree(proc)


def phase_b_edit(fixdir, name, src_bytes):
    """Open→edit (menu 全选 → cut → undo) →save census."""
    path = os.path.join(fixdir, name)
    with open(path, "wb") as f:
        f.write(src_bytes)
    before = open(path, "rb").read()
    proc, mcp, log = launch_app({"AUTO_OPEN_PATH": path})
    try:
        open_fixture(mcp, path, len(before))
        # 编辑步：编辑菜单「全选」→ 工具栏 scissors(cut) → undo-2(undo)
        snap = mcp.snapshot()
        menu = find_button_by_text(snap, "编辑")
        ok = menu is not None
        if ok:
            mcp.click(menu)
            time.sleep(0.8)
            snap = mcp.snapshot()
            item = find_button_by_text(snap, "全选")
            ok = item is not None
            if ok:
                mcp.click(item)
                time.sleep(0.5)
        if not click_toolbar(mcp, "scissors"):
            raise RuntimeError("cut button missing")
        if not click_toolbar(mcp, "undo-2"):
            raise RuntimeError("undo button missing")
        save_fixture(mcp, path)
        after = open(path, "rb").read()
        return census(before), census(after), ok, log
    finally:
        _kill_proc_tree(proc)


def phase_b_invalid(fixdir, name, src_bytes):
    """Invalid UTF-8: load shape + save attempt (disk clobber baseline?)."""
    path = os.path.join(fixdir, name)
    with open(path, "wb") as f:
        f.write(src_bytes)
    before = open(path, "rb").read()
    proc, mcp, log = launch_app({"AUTO_OPEN_PATH": path})
    try:
        c = open_fixture(mcp, path, -1)
        st = {
            "loaded_bytes": state_int(mcp.state("loaded_bytes"), "loaded_bytes"),
            "title": state_str(mcp.state("title_active"), "title_active"),
            "edits": state_int(mcp.state("edits"), "edits"),
            "console_tail": c[-160:],
        }
        # save 尝试（path_active 非空 → 直写原路径——观察是否清写）
        click_toolbar(mcp, "save")
        time.sleep(1.5)
        c2 = state_str(mcp.state("console"), "console") or ""
        after = open(path, "rb").read()
        st["save_console_tail"] = c2[-160:]
        return census(before), census(after), st, log
    finally:
        _kill_proc_tree(proc)


def main():
    if not AUTO_BIN or not os.path.exists(AUTO_BIN):
        print(f"ERROR: auto binary not found (AUTO_BIN={AUTO_BIN or 'unset'})")
        sys.exit(2)

    fixdir = tempfile.mkdtemp(prefix="p008_fix_")
    fixtures = {
        "bom_utf8.at": b"\xef\xbb\xbf" + "fn a() int { 1 }\nfn b() int { 2 }\n".encode(),
        "crlf.at": "one\r\ntwo\r\nthree\r\n".encode(),
        "lf.at": "one\ntwo\nthree\n".encode(),
        "cr.at": "one\rtwo\rthree\r".encode(),
        "mixed.at": "one\r\ntwo\nthree\r\nfour\n".encode(),
        "invalid_utf8.bin": b"ok text\n\xff\xfe bad bytes\nmore\x80 tail\n",
    }
    for n, b in fixtures.items():
        with open(os.path.join(fixdir, n), "wb") as f:
            f.write(b)

    report = {"toolchain": subprocess.run([AUTO_BIN, "--version"], capture_output=True,
                                          text=True).stdout.strip(),
              "fixtures": {n: census(b) for n, b in fixtures.items()}}

    report["phase_a"] = phase_a(fixdir)

    print("\n" + "=" * 60)
    print("Phase B: merged UI roundtrips (open → save; no edit)")
    print("=" * 60)
    report["roundtrip"] = {}
    for n in ("bom_utf8.at", "crlf.at", "lf.at", "cr.at", "mixed.at"):
        b, a, st, log = phase_b_roundtrip(fixdir, n, fixtures[n])
        report["roundtrip"][n] = {"before": b, "after": a, "state": st}
        print(f"  {n}: before={b}")
        print(f"  {' ' * len(n)}  after ={a}  loaded={st['loaded_bytes']}")

    print("\n" + "=" * 60)
    print("Phase B-edit: open → 全选+cut+undo → save (crlf)")
    print("=" * 60)
    b, a, ok, log = phase_b_edit(fixdir, "crlf.at", fixtures["crlf.at"])
    report["edit_crlf"] = {"before": b, "after": a, "menu_ok": ok}
    print(f"  before={b}\n  after ={a}  menu_ok={ok}")

    print("\n" + "=" * 60)
    print("Phase B-invalid: invalid UTF-8 open + save attempt")
    print("=" * 60)
    b, a, st, log = phase_b_invalid(fixdir, "invalid_utf8.bin", fixtures["invalid_utf8.bin"])
    report["invalid"] = {"before": b, "after": a, "state": st}
    print(f"  before={b}\n  after ={a}")
    print(f"  state={json.dumps(st, ensure_ascii=False, indent=2)}")

    out = os.path.join(fixdir, "probe_report.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\nreport: {out}")
    print("fixtures:", fixdir)


if __name__ == "__main__":
    main()
