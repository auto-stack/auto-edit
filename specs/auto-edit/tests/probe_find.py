#!/usr/bin/env python3
"""PLAN-009 T-00 内核行为勘（决策件）——查找替换四态 + 替换链探针.

载具 = tests/probe_find_app/（vm merged 最小 app：search prop Ident 绑定 +
input 写回面 + 内核 find/replace 直调），python autoui 断言。五项勘定：
  ① search prop Ident 绑定 live：eff 变更 → 高亮 + 非空首跳
     （eff="axb" 后 cursor 落 line3 匹配位——不经 find 按钮）
  ② (?-i) 内联旗标 vs 内核 builder case_insensitive(true)：
     "(?-i)Alpha" 首跳末位须 col12（大写 Alpha 7-11）非 col6
     （小写 alpha 1-5——builder 旗标压过内联的形态）；回绕单匹配。
  ③ 整词 \\b 锚："\\bfoo\\b" 首跳 line2 末位 col4 → find_next col15
     （foobar col5-10 跳过）
  ④ input 写回时机：显式 oninput 在 vm 轨无字段写回（r1 实证）——
     $event 载荷形态（036 先例）为正案：断言 .pattern/.eff 随键入更新
  ⑤ 替换链预演：code_editor_text → Regex.replace 'g'（(?-i) 前缀，
     计数 1）→ edit(0,len,out) 重写 → 读回首行断言
  + 转义例程：regex_escape("a.b") 光标语义断言（跳过 axb）
  + 计数勘定（DoCount）：Regex.match 'g' 已知命中数对照（foo=2 /
    (?i)alpha=3）
  + 负向："(?-i)zeta" 无匹配 → find_ok=false

光标断言约定（r1 勘定）：跳转后 cursor = 匹配末位（exclusive）。

用法：cd specs/auto-edit/tests && python probe_find.py
前置同 desktop_mcp.py（requests、AUTO_BIN 或 PATH 的 auto）。
退出码 = 勘定门（0 = 全 PASS）。
"""

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
    find_button_by_text, state_int, state_str, state_bool,
)

AUTO_BIN = os.environ.get("AUTO_BIN") or shutil.which("auto") or ""
PROBE_APP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "probe_find_app")


def find_input_id(snapshot_text):
    """First `input #id` element in the snapshot."""
    m = re.search(r"input #(\w+)", snapshot_text)
    return m.group(1) if m else None


def unesc(s):
    """Decode the state-text escaping seen in autoui_state values
    (\\\\ → \\; best-effort — cursor assertions are the semantic face)."""
    if s is None:
        return None
    return s.replace("\\\\", "\x00").replace("\x00", "\\")


def main():
    if not AUTO_BIN or not os.path.exists(AUTO_BIN):
        print(f"ERROR: auto binary not found (AUTO_BIN={AUTO_BIN or 'unset'})")
        sys.exit(2)

    report = {"toolchain": subprocess.run([AUTO_BIN, "--version"], capture_output=True,
                                          text=True).stdout.strip()}
    checks = []

    def check(name, ok, detail=""):
        checks.append({"name": name, "ok": bool(ok), "detail": str(detail)[:300]})
        print(f"  {'PASS' if ok else 'FAIL'}  {name}" + ("" if ok else f"  [{detail}]"))

    port = pick_free_port()
    log = tempfile.NamedTemporaryFile(
        prefix="p009_probe_", suffix=".log", delete=False, mode="w",
        encoding="utf-8", errors="replace")
    proc = subprocess.Popen(
        [AUTO_BIN, "run", "-r", "vm"],
        cwd=PROBE_APP, env={**os.environ, "AUTOUI_MCP_PORT": str(port)},
        stdout=log, stderr=subprocess.STDOUT)
    url = f"http://127.0.0.1:{port}/mcp"
    try:
        if not wait_for_server(url, 30):
            raise RuntimeError("MCP server did not start")
        mcp = McpClient(url)
        snap = ""
        for _ in range(15):
            snap = mcp.snapshot()
            if "(rendered)" in snap and find_input_id(snap):
                break
            time.sleep(1)

        def read_cursor():
            btn = find_button_by_text(mcp.snapshot(), "read")
            if btn:
                mcp.click(btn)
                time.sleep(0.4)
            st = mcp.state("line", "col")
            return state_int(st, "line"), state_int(st, "col")

        input_id = find_input_id(snap)
        check("probe app: input element present", input_id is not None, snap[:160])

        def type_into_input(text, field="pattern", want=None):
            """Type with settle+retry: the first type dispatch after launch can
            land in a pre-ready window and be dropped silently (r4 flake) —
            re-snapshot + retype until the field reads back `want`."""
            if want is None:
                want = text
            nonlocal input_id
            for _ in range(4):
                mcp.call("autoui_type", element_id=input_id, text=text, clear_first=True)
                time.sleep(0.7)
                got = state_str(mcp.state(field), field)
                if got == want:
                    return True
                snap2 = mcp.snapshot()
                input_id = find_input_id(snap2) or input_id
                time.sleep(0.5)
            return False

        # 热身定驻：首拍派发竞态窗口（启动后 ~2s 内事件静默丢弃——r4 实勘）。
        time.sleep(2.0)
        _ = mcp.state("edits")

        # ---- ④ 键入文本=handler 首参 + ① live 绑定首跳 ----
        # 定案（r4 三变体实验）：input oninput 派发把键入文本作 handler
        # 首参（015-notes SearchChanged(q) 形）——handler 显式赋值 store
        # 字段；框架写回对 store 子树字段不适用（input_state_map 写回
        # 仅根级字段），裸 value 不生成 type handler（mint 条件=直接字段）。
        # edits 断言用 >=：autoui_type clear_first=True 触发 clear+type
        # 双发（探针工件；真实键入每击单发）。
        print("\n④① type 'axb' (handler-arg payload + live first jump)")
        ok_typed = type_into_input("axb")
        st = mcp.state("pattern", "eff", "edits")
        pat = state_str(st, "pattern")
        eff = state_str(st, "eff")
        edits = state_int(st, "edits")
        check("T4 handler-arg payload: .pattern updated", ok_typed and pat == "axb",
              f"pattern={pat!r} raw={st[:120]!r}")
        check("T4 .eff recomputed", eff == "axb", f"eff={eff!r}")
        check("T4 handler fired: edits bumped", edits is not None and edits >= 1, f"edits={edits}")
        line, col = read_cursor()
        check("T1 live binding: first jump to (3,8) without find",
              (line, col) == (3, 8), f"cursor=({line},{col})")

        # ---- ② (?-i) 内联旗标 ----
        print("\n② caseflag: '(?-i)Alpha' — first jump end (1,12)")
        btn = find_button_by_text(mcp.snapshot(), "caseflag")
        check("caseflag button present", btn is not None, "not in snapshot")
        if btn:
            mcp.click(btn)
            time.sleep(0.8)
            line, col = read_cursor()
            check("T2 (?-i) overrides builder: first jump (1,12)",
                  (line, col) == (1, 12), f"cursor=({line},{col})")
            fbtn = find_button_by_text(mcp.snapshot(), "findnext")
            mcp.click(fbtn)
            time.sleep(0.6)
            line, col = read_cursor()
            check("T2 single match wraps → (1,12)",
                  (line, col) == (1, 12), f"cursor=({line},{col})")

        # ---- ③ 整词 \b 锚 ----
        print("\n③ wordanchor: '\\bfoo\\b' — (2,4) then (2,15), foobar skipped")
        btn = find_button_by_text(mcp.snapshot(), "wordanchor")
        check("wordanchor button present", btn is not None, "not in snapshot")
        if btn:
            mcp.click(btn)
            time.sleep(0.8)
            line, col = read_cursor()
            check("T3 \\b first jump (2,4)", (line, col) == (2, 4), f"cursor=({line},{col})")
            fbtn = find_button_by_text(mcp.snapshot(), "findnext")
            mcp.click(fbtn)
            time.sleep(0.6)
            line, col = read_cursor()
            check("T3 \\b skips foobar → (2,15)", (line, col) == (2, 15),
                  f"cursor=({line},{col})")

        # ---- 转义例程 + 字面语义 ----
        print("\nE litesc: regex_escape('a.b') — literal dot, axb skipped")
        btn = find_button_by_text(mcp.snapshot(), "litesc")
        check("litesc button present", btn is not None, "not in snapshot")
        if btn:
            mcp.click(btn)
            time.sleep(0.8)
            st = mcp.state("eff")
            eff = unesc(state_str(st, "eff"))
            check("esc routine: eff == 'a\\.b'", eff == "a\\.b",
                  f"eff={state_str(st, 'eff')!r}")
            line, col = read_cursor()
            check("esc literal first jump (3,4)", (line, col) == (3, 4),
                  f"cursor=({line},{col})")
            fbtn = find_button_by_text(mcp.snapshot(), "findnext")
            mcp.click(fbtn)
            time.sleep(0.6)
            line, col = read_cursor()
            check("esc literal skips axb → (3,12)", (line, col) == (3, 12),
                  f"cursor=({line},{col})")

        # ---- 计数勘定 ----
        print("\nC count: Regex.match 'g' known-count shapes")
        btn = find_button_by_text(mcp.snapshot(), "count")
        check("count button present", btn is not None, "not in snapshot")
        if btn:
            mcp.click(btn)
            time.sleep(0.6)
            st = mcp.state("rcount", "rcount3")
            rc = state_int(st, "rcount")
            rc3 = state_int(st, "rcount3")
            check("C 'foo' 'g' count == 3 (含 foobar 词中)", rc == 3, f"rcount={rc} raw={st[:120]!r}")
            check("C '(?i)alpha' 'g' count == 3", rc3 == 3, f"rcount3={rc3}")

        # ---- ⑤ 替换链预演 ----
        print("\n⑤ replace: Regex.replace 'g' + edit rewrite + read-back")
        btn = find_button_by_text(mcp.snapshot(), "replace")
        check("replace button present", btn is not None, "not in snapshot")
        if btn:
            mcp.click(btn)
            time.sleep(0.8)
            st = mcp.state("rcount2", "rhead", "edits")
            rc2 = state_int(st, "rcount2")
            head = state_str(st, "rhead")
            edits = state_int(st, "edits")
            check("T5 (?-i)Alpha 'g' count == 1", rc2 == 1, f"rcount2={rc2} raw={st[:120]!r}")
            check("T5 rewrite read-back: head starts 'alpha YY ALPHA'",
                  head is not None and head.startswith("alpha YY ALPHA"),
                  f"rhead={head!r}")
            check("T5 handler fired (edits)", edits is not None and edits >= 2, f"edits={edits}")

        # ---- 负向：无匹配 find_ok=false ----
        print("\nN negative: '(?-i)zeta' — find returns false")
        type_into_input("(?-i)zeta")
        time.sleep(0.4)
        st = mcp.state("eff")
        eff = state_str(st, "eff")
        fbtn = find_button_by_text(mcp.snapshot(), "findnext")
        mcp.click(fbtn)
        time.sleep(0.6)
        st = mcp.state("find_ok")
        ok = state_bool(st, "find_ok")
        check("N no-match: find_ok false, eff passthrough",
              ok is False and eff == "(?-i)zeta", f"find_ok={ok} eff={eff!r}")

    except Exception as e:  # noqa: BLE001
        check("probe run", False, repr(e))
    finally:
        _kill_proc_tree(proc)
        report["checks"] = checks
        report["pass"] = all(c["ok"] for c in checks)
        out = os.path.join(tempfile.gettempdir(), "probe_find_report.json")
        with open(out, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\nreport: {out}")
        print(f"toolchain: {report['toolchain']}")
        failed = [c for c in checks if not c["ok"]]
        print(f"RESULT: {len(checks) - len(failed)} passed, {len(failed)} failed")
        sys.exit(0 if report["pass"] else 1)


if __name__ == "__main__":
    main()
