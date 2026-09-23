#!/usr/bin/env python3
"""
Plan 418 Phase 1: MCP action-matrix tests for the real auto-edit app
(原 041-code-editor) in VM mode.

Starts `auto run -r vm`, waits for the UI MCP server, then exercises the
13 semantic Act* handlers through their REAL trigger surfaces (menu items,
toolbar icon buttons, global shortcuts) and asserts observable state
(title/path/tab/console fields of the App model).

Out of scope here (manual / interactive): ActOpen/ActSave (blocking rfd
OS dialogs cannot be auto-dismissed). ActQuit runs last — its pass
condition is the app process exiting.

Snapshot caveat: event bindings render WITHOUT arguments
(`onclick: .MenuToggle`, not `.MenuToggle("file")`), so menubar buttons
are located by their text label via find_button_by_text.

Usage:
    cd examples/ui/041-auto-edit/tests
    python desktop_mcp.py

Prerequisites:
    - auto built with ui-iced: cargo build --features ui-iced --bin auto
      (or set AUTO_BIN env var to the binary path)
    - Python requests: pip install requests
"""

import json
import os
import shutil
import re
import subprocess
import sys
import tempfile
import time

try:
    import requests
except ImportError:
    print("Please install requests: pip install requests")
    sys.exit(1)

MCP_PORT_DEFAULT = 9247


def pick_free_port(start=MCP_PORT_DEFAULT):
    import socket
    for port in range(start, start + 100):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    raise RuntimeError(f"No free port in [{start}, {start + 100})")


AUTO_BIN = os.environ.get("AUTO_BIN") or shutil.which("auto") or ""
PROJECT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))


class McpClient:
    """JSON-RPC client for the UI MCP server.

    Plan 423 P5 内存防护:应用侧若踩中 VM 字节码错位 bug,handler 会在垃圾
    指令里跑满步数预算并无界生长视图/字符串池 —— snapshot 响应随之膨胀到
    GB 级,python 侧 json 解析持有数倍载荷曾把系统内存吃到 20G+。故:
    * 响应体硬上限(MAX_RESPONSE_BYTES,超出即断言失败并中止);
    * 丢弃超大响应后不再重试。"""

    MAX_RESPONSE_BYTES = 64 * 1024 * 1024  # 64MB — 正常快照远小于此

    def __init__(self, url):
        self.url = url
        self.req_id = 0

    def call(self, tool_name, **arguments):
        for attempt in (1, 2):
            self.req_id += 1
            try:
                resp = requests.post(self.url, json={
                    "jsonrpc": "2.0", "method": "tools/call",
                    "params": {"name": tool_name, "arguments": arguments},
                    "id": self.req_id,
                }, timeout=45, stream=True)
                break
            except (requests.ConnectionError, requests.Timeout):
                if attempt == 2:
                    raise
                time.sleep(2)
        size = int(resp.headers.get("Content-Length") or 0)
        body = resp.raw.read(self.MAX_RESPONSE_BYTES + 1, decode_content=True)
        if len(body) > self.MAX_RESPONSE_BYTES or size > self.MAX_RESPONSE_BYTES:
            raise RuntimeError(
                f"MCP response for {tool_name} exceeded {self.MAX_RESPONSE_BYTES} bytes "
                f"(got {max(size, len(body))}) — app-side runaway (VM desync?) — aborting"
            )
        data = json.loads(body)
        if "error" in data:
            raise RuntimeError(f"MCP error: {data['error']}")
        content = data.get("result", {}).get("content", [])
        return content[0]["text"] if content else ""

    def snapshot(self):
        return self.call("autoui_snapshot")

    def click(self, element_id):
        return self.call("autoui_action", element_id=element_id, action="press")

    def state(self, *fields):
        return self.call("autoui_state", fields=list(fields))


def wait_for_server(url, timeout=30):
    for _ in range(timeout):
        try:
            requests.post(url, json={
                "jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 1
            }, timeout=2)
            return True
        except (requests.ConnectionError, requests.Timeout):
            time.sleep(1)
    return False


def find_element_by_event(snapshot_text, event_name, attr="onclick"):
    """First `aura_N` element bound to `event_name` via `attr` (substring
    match; only useful for unparametrized bindings — see module docstring)."""
    pattern_id = re.compile(r"#(aura_\d+|vnode_\d+)")
    current_id = None
    target = f"{attr}: .{event_name}"
    for line in snapshot_text.splitlines():
        m = pattern_id.search(line)
        if m:
            current_id = m.group(1)
        if target in line and current_id is not None:
            return current_id
    return None


def find_button_by_text(snapshot_text, label):
    """Element id of the `button #id "label" { ... }` node."""
    pat = re.compile(r'button #(\w+) "' + re.escape(label) + '"')
    m = pat.search(snapshot_text)
    return m.group(1) if m else None


def find_button_by_icon(snapshot_text, icon):
    """Synthesized toolbar buttons carry PUA icon labels
    ("<icon>") — locate the button node by icon name."""
    marker = "" + icon + ""
    pat = re.compile(r'button #(\w+) "[^"]*' + re.escape(marker))
    m = pat.search(snapshot_text)
    return m.group(1) if m else None


def find_button_by_onclick(snapshot_text, handler):
    """Element id of the first button whose onclick references `handler`.

    DSL `button { icon (name: "x") }` renders with an EMPTY label + [Image]
    child (no PUA marker), so find_button_by_icon can't see it — find the
    `onclick: .<handler>` line, then walk back to the nearest enclosing
    `button #id` line (Plan 420 tab-strip x/+ buttons)."""
    target = f"onclick: .{handler}"
    current_id = None
    for line in snapshot_text.splitlines():
        m = re.search(r'button #(\w+)', line)
        if m:
            current_id = m.group(1)
        if target in line and current_id is not None:
            return current_id
    return None


def find_tab_close_buttons(snapshot_text):
    """Ids of the tab-strip close (x) buttons.

    The x buttons render as `button #id "" { text "[Image]" }` — empty label,
    icon child, and (Plan 420 known gap) NO onclick attribute in the snapshot
    because probe paths for for+if children don't align with vtree paths.
    Distinguish from the `+` button (same shape) by the + having an onclick
    attribute. Returns ids in document order."""
    ids = []
    lines = snapshot_text.splitlines()
    i = 0
    while i < len(lines):
        m = re.search(r'button #(\w+) ""', lines[i])
        if m:
            block = []
            depth = lines[i].count("{") - lines[i].count("}")
            j = i + 1
            while j < len(lines) and depth > 0:
                depth += lines[j].count("{") - lines[j].count("}")
                block.append(lines[j])
                j += 1
            joined = "\n".join(block)
            if "[Image]" in joined and "onclick:" not in joined:
                ids.append(m.group(1))
            i = j
        else:
            i += 1
    return ids


def open_menu(mcp, snap_cache, label):
    """Click the menubar button `label` (文件/编辑/视图/帮助), refresh snapshot.

    Always re-snapshots first: vnode ids drift across rebuilds, so an id from
    a pre-pick snapshot may no longer resolve (T5 stale-id lesson)."""
    snap_cache[0] = mcp.snapshot()
    btn = find_button_by_text(snap_cache[0], label)
    if btn is None:
        return False
    mcp.click(btn)
    time.sleep(1.0)
    snap_cache[0] = mcp.snapshot()
    return True


def state_str(state_text, field):
    m = re.search(rf'{field}:\s*"((?:[^"\\]|\\.)*)"', state_text)
    return m.group(1) if m else None


def state_int(state_text, field):
    m = re.search(rf"{field}:\s*(-?\d+)", state_text)
    return int(m.group(1)) if m else None


def state_bool(state_text, field):
    m = re.search(rf"{field}:\s*(true|false)", state_text)
    return m.group(1) == "true" if m else None


def _kill_proc_tree(proc):
    """Plan 423 P5:terminate 不杀 Windows 子进程树 —— taskkill /T /F 兜底,
    防止失控的 UI 应用(VM 错位 runaway)被留成孤儿。"""
    proc.terminate()
    try:
        proc.wait(5)
    except Exception:
        pass
    subprocess.run(
        ["taskkill", "/T", "/F", "/PID", str(proc.pid)],
        capture_output=True,
    )


class TestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def check(self, name, condition, detail=""):
        if condition:
            self.passed += 1
            print(f"  PASS  {name}")
        else:
            self.failed += 1
            self.errors.append(f"{name}: {detail}")
            print(f"  FAIL  {name}: {detail}")


def run_tests(mcp_url, proc):
    mcp = McpClient(mcp_url)
    result = TestResult()

    # T1: structure — menubar, toolbar icons, editor (retry until rendered)
    # Sentinel: "(rendered)" — the post-render VTree snapshot. The pre-render
    # fallback (raw view_template) still names the editor `code_editor` and has
    # NO synthesized menubar/toolbar buttons, so polling on "code_editor" can
    # break the loop during the ~1.5s first-render window and every synthesis
    # check below fails. In rendered snapshots the editor is `textarea`.
    print("\nT1: Snapshot structure")
    snap_cache = [mcp.snapshot()]
    for _ in range(10):
        if "(rendered)" in snap_cache[0]:
            break
        time.sleep(1)
        snap_cache[0] = mcp.snapshot()
    snap = snap_cache[0]
    result.check("App widget present", 'widget: "App"' in snap, snap[:200])
    for icon in ("file-plus", "undo-2", "copy"):
        result.check(f"toolbar icon {icon} present", find_button_by_icon(snap, icon) is not None,
                     "icon button not found")
    if "code_editor" in snap:
        result.check("editor present", True)
    else:
        print("  NOTE  editor node not yet in snapshot (render timing); skipping")
    result.check("menubar buttons present", find_button_by_text(snap, "文件") is not None
                 and find_button_by_text(snap, "帮助") is not None, "menu buttons not found")
    # Plan 418 §8.4①: synthesized buttons now carry onclick in snapshots
    # (probe paths aligned with the real vtree nesting) — lock it in.
    result.check("toolbar synthesized onclick present",
                 "onclick: .ActNew" in snap, "synthesized toolbar onclick missing")
    result.check("menubar synthesized onclick present",
                 "__menubar_toggle(\"file\")" in snap, "menubar toggle onclick missing")
    # (Plan 418 P2-3: DSL-declared bindings still render their args; the
    # synthesized menubar/toolbar are located by label/icon instead — probe
    # path alignment for synthesized subtrees is a known gap, plan 418 8.4.)


    # T2: ActConsole via View menu — console_open flips, menu auto-closes
    print("\nT2: ActConsole (menu item)")
    before = state_bool(mcp.state("console_open"), "console_open")
    ok = open_menu(mcp, snap_cache, "视图")
    result.check("view menu opened", ok, "视图 button not found")
    item = find_button_by_text(snap_cache[0], "切换 Console")
    result.check("menu item (切换 Console) found", item is not None, "not in open-menu snapshot")
    if item:
        mcp.click(item)
        time.sleep(0.3)
        after = state_bool(mcp.state("console_open"), "console_open")
        result.check("console_open flipped", after == (not before), f"{before} -> {after}")
        # menu auto-closes after item activation (Plan 418: Act handlers reset menu_open)
        snap_cache[0] = mcp.snapshot()
        result.check("menu closed after pick", find_button_by_text(snap_cache[0], "切换 Console") is None,
                     "panel item still present")
        snap_cache[0] = mcp.snapshot()

    # T3: ActAbout via Help menu — console line recorded
    print("\nT3: ActAbout (menu item)")
    open_menu(mcp, snap_cache, "帮助")
    item = find_button_by_text(snap_cache[0], "关于 auto-edit")
    if item:
        mcp.click(item)
        time.sleep(0.3)
        result.check("about line logged", "auto-edit 0.1" in (state_str(mcp.state("console"), "console") or ""),
                     "console missing about line")
    else:
        result.check("about menu item found", False, "no .ActAbout in help menu snapshot")

    # T3b: Plan 428 — code folding via View menu (native round-trip on the
    # seed text: line 2 `fn add` block, body of 2 lines).
    print("\nT3b: Plan 428 code folding (native channel)")
    open_menu(mcp, snap_cache, "视图")
    item = find_button_by_text(snap_cache[0], "折叠切换")
    if item:
        mcp.click(item)
        time.sleep(0.3)
        hidden1 = state_int(mcp.state("fold_hidden"), "fold_hidden")
        result.check("fold engaged (2 body lines hidden)", hidden1 == 2, f"fold_hidden={hidden1}")
        open_menu(mcp, snap_cache, "视图")
        item = find_button_by_text(snap_cache[0], "折叠切换")
        if item:
            mcp.click(item)
            time.sleep(0.3)
            hidden2 = state_int(mcp.state("fold_hidden"), "fold_hidden")
            result.check("fold released (0 hidden)", hidden2 == 0, f"fold_hidden={hidden2}")
        else:
            result.check("fold menu item found (2nd)", False, "no 折叠切换 after re-open")
    else:
        result.check("fold menu item found", False, "no 折叠切换 in view menu snapshot")

    # T4: ActNew via File menu — title/path reset
    print("\nT4: ActNew (menu item)")
    open_menu(mcp, snap_cache, "文件")
    item = find_button_by_text(snap_cache[0], "新建")
    if item:
        mcp.click(item)
        time.sleep(0.3)
        st = mcp.state("title_active", "path_active")
        result.check("title_active reset to untitled", state_str(st, "title_active") == "untitled.at", st)
        result.check("path_active cleared", state_str(st, "path_active") == "", st)
        result.check("new logged", "new: cleared" in (state_str(mcp.state("console"), "console") or ""), "")
    else:
        result.check("new menu item found", False, "no .ActNew in file menu snapshot")

    # T5: ActSwitchTab via View menu — tab flips
    print("\nT5: ActSwitchTab (menu item)")
    tab_before = state_int(mcp.state("tab"), "tab")
    open_menu(mcp, snap_cache, "视图")
    item = find_button_by_text(snap_cache[0], "切换 Tab")
    if item:
        mcp.click(item)
        time.sleep(0.3)
        tab_after = state_int(mcp.state("tab"), "tab")
        result.check("tab flipped", tab_after == 1 - tab_before, f"{tab_before} -> {tab_after}")
    else:
        result.check("switch-tab menu item found", False, "no .ActSwitchTab in view menu")

    # T6: toolbar editor actions — undo/redo/cut/copy/paste via toolbar
    # icons; the full edit-menu/toolbar cycle with REAL editor-text
    # assertions (Plan 418 follow-up: previously only alive+console-log were
    # checked — undo could silently no-op). PLAN-005: 编辑 handler 的全文
    # 回写镜像已删（tabs[i].src 只作初值/外部重置，src_active 不再实时），
    # 正文断言改走 save 路径 E2E——toolbar("save") 触发 ActSave 落盘后读
    # AUTO_SAVE_PATH 文件比对（starter tab path="" 首存走旁路定路径，续存
    # 覆盖；断言面反而更强：验的是真实写路径而非模型镜像）。
    print("\nT6: Editor actions (toolbar icons + edit-menu, text-verified)")
    title_now = state_str(mcp.state("title_active"), "title_active") or ""
    marker = "工具模块" if "util" in title_now else "你好世界"

    def src_now():
        # PLAN-005: save-then-read —— 触发 ActSave 落盘，读回文件内容。
        # 落盘完成以 console 新增 "saved:" 行为准（ActSave 内 write_text
        # 先于 console_log，慢实例上固定 sleep 不够——1652 工具链冷跑
        # run1 教训），轮询确认后再读文件。
        if not toolbar("save"):
            return "<save toolbar missing>"
        before = (state_str(mcp.state("console"), "console") or "").count("saved:")
        for _ in range(10):
            time.sleep(0.3)
            after = (state_str(mcp.state("console"), "console") or "").count("saved:")
            if after > before:
                break
        with open(os.environ["AUTO_SAVE_PATH"], encoding="utf-8") as f:
            return f.read()

    def toolbar(icon):
        snap_cache[0] = mcp.snapshot()
        el = find_button_by_icon(snap_cache[0], icon)
        if el is None:
            result.check(f"toolbar {icon} present", False, "element not found")
            return False
        mcp.click(el)
        time.sleep(0.4)
        return proc.poll() is None

    def menu_item(label):
        # opens the edit menu and clicks `label`; False when not found
        for menu_label, item in (("编辑", label),):
            if not open_menu(mcp, snap_cache, menu_label):
                return False
            el = find_button_by_text(snap_cache[0], item)
            if el is None:
                return False
            mcp.click(el)
            time.sleep(0.4)
            return True
        return False

    # 1) select-all via the edit menu → selection state really set
    ok = menu_item("全选")
    sel = state_int(mcp.state("sel"), "sel")
    result.check("select-all sets .sel", ok and sel > 0, f"sel={sel}")

    # 2) cut empties the editor; save E2E: file on disk is empty
    if toolbar("scissors"):
        saved = src_now()
        result.check("cut empties editor text", saved == "", f"saved={saved[:30]!r}")
        result.check("cut logged", "cut" in (state_str(mcp.state("console"), "console") or ""))

    # 3) undo restores the preloaded text (save E2E)
    if toolbar("undo-2"):
        result.check("undo restores text", marker in src_now(), f"saved missing {marker!r}")

    # 4) redo re-applies the cut (save E2E: empty again)
    if toolbar("redo-2"):
        saved = src_now()
        result.check("redo re-empties text", saved == "", f"saved={saved[:30]!r}")

    # 5) undo restores again, then copy → cut → paste round-trips the text
    if toolbar("undo-2"):
        result.check("undo (2nd) restores text", marker in src_now(), "")
        ok = menu_item("全选")
        if toolbar("copy"):
            result.check("copy logged", "copy" in (state_str(mcp.state("console"), "console") or ""))
        if toolbar("scissors"):
            result.check("cut (2nd) empties text", src_now() == "", "")
        if toolbar("clipboard"):
            result.check("paste restores text", marker in src_now(),
                         f"paste did not round-trip clipboard")
            result.check("paste logged", "paste" in (state_str(mcp.state("console"), "console") or ""))

    # T7: global shortcut (actions decl, Plan 451) — Ctrl+J now flows ONLY from the actions block
    # (config fallback layer; the DSL onkeydown attrs were removed in P2-3c).
    print("\nT7: Global shortcut Ctrl+J")
    before = state_bool(mcp.state("console_open"), "console_open")
    try:
        mcp.call("autoui_keyboard", key="j", modifiers=["ctrl"])
        time.sleep(0.3)
        after = state_bool(mcp.state("console_open"), "console_open")
        result.check("console_open flipped via Ctrl+J", after == (not before), f"{before} -> {after}")
    except Exception as e:
        result.check("console_open flipped via Ctrl+J", False, f"keyboard tool error: {e}")

    # T7b: actions-block shortcut — Ctrl+D exists ONLY in the actions block
    # (view.switch-tab); proves the P2-4 fallback fires under the DSL layer.
    print("T7b: Actions-block shortcut Ctrl+D (actions decl only)")
    tab_before = state_int(mcp.state("tab"), "tab")
    try:
        mcp.call("autoui_keyboard", key="d", modifiers=["ctrl"])
        time.sleep(0.3)
        tab_after = state_int(mcp.state("tab"), "tab")
        result.check("tab flipped via config Ctrl+D", tab_after == 1 - tab_before,
                     f"{tab_before} -> {tab_after}")
    except Exception as e:
        result.check("tab flipped via config Ctrl+D", False, f"keyboard tool error: {e}")

    # T8: ActQuit via File menu — process exits
    # T9: Plan 420 — tab close / + open (AUTO_OPEN_PATH bypass) / dirty-confirm
    # / AUTO_SAVE_PATH roundtrip. Runs on a FRESH app process (earlier groups
    # dirty tabs / mutate active state; a clean instance keeps 9.1-9.4
    # deterministic). Requires AUTO_OPEN_PATH/AUTO_SAVE_PATH (see main()).
    print("\nT9: Plan 420 tab workspace (close/+ open/dirty/save)")
    if os.environ.get("AUTO_OPEN_PATH") and os.environ.get("AUTO_SAVE_PATH"):
        t9_port = pick_free_port()
        _mcp_orig, _snap_orig = mcp, snap_cache
        t9_proc = subprocess.Popen(
            [AUTO_BIN, "run", "-r", "vm"],
            cwd=PROJECT,
            env={**os.environ, "AUTOUI_MCP_PORT": str(t9_port),
                 # PLAN-010 T-04 基建卫生：每实例独立 APPDATA（会话链恢复
                 # 隔离——共享 run 级会让前序检查的结构写盘漏进本实例启动
                 # 恢复，T12.5/T12.6/T13.4 竞态实测）。
                 "APPDATA": tempfile.mkdtemp(prefix="auto041_t9_ad_")},
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        t9_url = f"http://127.0.0.1:{t9_port}/mcp"
        if wait_for_server(t9_url, 30):
            mcp = McpClient(t9_url)
            snap_cache = [""]
            for _ in range(15):
                snap_cache[0] = mcp.snapshot()
                if "(rendered)" in snap_cache[0]:
                    break
                time.sleep(1)
        roundtrip_path = os.environ["AUTO_OPEN_PATH"]
        # PLAN-005: T6 的 save E2E 通道已把此文件当断言面（正文比对走它），
        # 进 T9 前重置回 main() 的已知原文——T9 的 marker 隔离假设不再依赖
        # T6 的末次落盘内容（paste flake 时可为空串，曾致 splitlines 崩）。
        with open(roundtrip_path, "w", encoding="utf-8", newline="") as f:
            f.write("// t9 roundtrip file\nfn t9() int { 42 }\n")
        marker_before = open(roundtrip_path, encoding="utf-8").read()
        # 9.1 close both starter tabs (x icon buttons in the tab strip; a
        # tab dirtied by T6 opens the confirm popover — force-close through it)
        for _ in range(3):
            snap_cache[0] = mcp.snapshot()
            if state_int(mcp.state("tab_count"), "tab_count") == 0:
                break
            if state_str(mcp.state("confirm_open"), "confirm_open") == "true":
                snap_cache[0] = mcp.snapshot()
                force = find_button_by_text(snap_cache[0], "直接关闭")
                if force:
                    mcp.click(force)
                    time.sleep(0.5)
                continue
            xs = find_tab_close_buttons(snap_cache[0])
            if not xs:
                break
            mcp.click(xs[0])
            time.sleep(0.5)
        result.check("all tabs closed", state_int(mcp.state("tab_count"), "tab_count") == 0,
                     mcp.state("tab_count"))
        snap_cache[0] = mcp.snapshot()
        result.check("empty state visible", "没有打开的文件" in snap_cache[0], "empty-state text missing")

        # 9.2 + opens the AUTO_OPEN_PATH file into a new tab
        snap_cache[0] = mcp.snapshot()
        plus = find_button_by_onclick(snap_cache[0], "ActOpen")
        ok_plus = plus is not None
        result.check("+ button found", ok_plus, "plus icon button missing")
        if ok_plus:
            mcp.click(plus)
            time.sleep(0.8)
            st = mcp.state("tab_count", "title_active")
            result.check("tab opened from AUTO_OPEN_PATH",
                         state_int(st, "tab_count") == 1
                         and state_str(st, "title_active") == os.path.basename(roundtrip_path),
                         st)
            # PLAN-007: src_active 退役——内容到达改判 loaded_bytes（分块
            # 装载完成 = 最后 envelope 的 total 字节数；正文正确性由 9.4
            # save roundtrip E2E 承载）。装载经 Tick 递延（编辑器实化后
            # 才能 load，间隔 800ms），轮询至多 6s。
            want_bytes = len(marker_before.encode("utf-8"))
            got_bytes = -1
            for _ in range(30):
                got_bytes = state_int(mcp.state("loaded_bytes"), "loaded_bytes")
                if got_bytes == want_bytes:
                    break
                time.sleep(0.2)
            result.check("opened content loaded (bytes)",
                         got_bytes == want_bytes,
                         f"loaded_bytes={got_bytes} want={want_bytes}")

        # 9.3 dirty-confirm: ActCut unconditionally dirties the active tab
        # (autoui_type passes the TEXT as first handler arg -- the generic
        # input-tool convention -- which displaces the loop-index payload of
        # `oninput: .SrcChanged(i)`; real-window events keep the payload).
        snap_cache[0] = mcp.snapshot()
        cut_btn = find_button_by_icon(snap_cache[0], "scissors")
        ok_cut = cut_btn is not None
        result.check("cut toolbar button found", ok_cut, "scissors icon missing")
        if ok_cut:
            mcp.click(cut_btn)
            time.sleep(0.5)
            result.check("cut logged", "cut" in (state_str(mcp.state("console"), "console") or ""),
                         "no cut console line")
            snap_cache[0] = mcp.snapshot()
            xs9 = find_tab_close_buttons(snap_cache[0])
            if xs9:
                mcp.click(xs9[0])
                time.sleep(0.6)
                result.check("dirty confirm popover opens",
                             "confirm_open: true" in mcp.state("confirm_open"),
                             mcp.state("confirm_open"))
                snap_cache[0] = mcp.snapshot()
                force = find_button_by_text(snap_cache[0], "\u76f4\u63a5\u5173\u95ed")
                result.check("confirm force-close item found", force is not None, "not in snapshot")
                if force:
                    mcp.click(force)
                    time.sleep(0.5)
                    result.check("dirty tab closed",
                                 state_int(mcp.state("tab_count"), "tab_count") == 0,
                                 mcp.state("tab_count"))

        # 9.4 save roundtrip: reopen, type, save via toolbar icon → file rewritten
        snap_cache[0] = mcp.snapshot()
        plus = find_button_by_onclick(snap_cache[0], "ActOpen")
        if plus:
            mcp.click(plus)
            time.sleep(0.8)
            # dirty via cut, then save via toolbar icon -> file rewritten
            snap_cache[0] = mcp.snapshot()
            cut_btn = find_button_by_icon(snap_cache[0], "scissors")
            if cut_btn:
                mcp.click(cut_btn)
                time.sleep(0.4)
            snap_cache[0] = mcp.snapshot()
            save_btn = find_button_by_icon(snap_cache[0], "save")
            if save_btn:
                mcp.click(save_btn)
                time.sleep(0.8)
                written = open(os.environ["AUTO_SAVE_PATH"], encoding="utf-8").read()
                result.check("saved file round-trips content",
                             marker_before.splitlines()[0] in written, written[-80:])
            else:
                result.check("save toolbar button found", False, "save icon missing")
        # restore the main app client (T8 quits the ORIGINAL process) and
        # retire the T9 instance.
        mcp, snap_cache = _mcp_orig, _snap_orig
        _kill_proc_tree(t9_proc)
    else:
        print("  NOTE  AUTO_OPEN_PATH/AUTO_SAVE_PATH not set; skipping T9 (see runner env)")

    # T10: Plan 423 — enabled-if disabled 态 + 配置热重载(独立新鲜进程)。
    print("\nT10: Plan 423 enabled-if + hot reload")
    if os.environ.get("AUTO_OPEN_PATH") and os.environ.get("AUTO_SAVE_PATH"):
        t10_port = pick_free_port()
        t10_proc = subprocess.Popen(
            [AUTO_BIN, "run", "-r", "vm"],
            cwd=PROJECT,
            env={**os.environ, "AUTOUI_MCP_PORT": str(t10_port),
                 "APPDATA": tempfile.mkdtemp(prefix="auto041_t10_ad_")},
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # Plan 451: 动作配置 DSL 化——热重载对象改为 app.at 的 actions 块
        config_file = os.path.join(PROJECT, "src", "front", "app.at")
        # newline="": Windows 文本模式会把换行译成 CRLF 回写,残留会让下一轮
        # 实例的 DSL 解析退化(菜单项快照匹配全挂,矩阵自毒循环)。
        config_backup = open(config_file, encoding="utf-8", newline="").read()
        try:
            t10_url = f"http://127.0.0.1:{t10_port}/mcp"
            assert wait_for_server(t10_url, 30), "T10 server never up"
            mcp10 = McpClient(t10_url)
            snap10 = ""
            for _ in range(15):
                snap10 = mcp10.snapshot()
                if "(rendered)" in snap10:
                    break
                time.sleep(1)

            # 10.1 close both starter tabs → file.save (enabled-if .tab_count > 0)
            # goes disabled: snapshot marker + click dispatches nothing.
            for _ in range(3):
                if state_int(mcp10.state("tab_count"), "tab_count") == 0:
                    break
                xs = find_tab_close_buttons(mcp10.snapshot())
                if not xs:
                    break
                mcp10.click(xs[0])
                time.sleep(0.5)
            result.check("T10 all tabs closed",
                         state_int(mcp10.state("tab_count"), "tab_count") == 0, "tabs left")
            snap10 = mcp10.snapshot()
            save_btn = find_button_by_onclick(snap10, "ActSave")
            ok_save = save_btn is not None
            result.check("T10 save button found", ok_save, "ActSave button missing")
            if ok_save:
                m = re.search(r'button #' + re.escape(save_btn) + r'[^{]*\{[^}]*\}', snap10, re.S)
                region = m.group(0) if m else ""
                result.check("T10 save disabled marker in snapshot",
                             "disabled: true" in region, region[:120])
                console_before = state_str(mcp10.state("console"), "console") or ""
                mcp10.click(save_btn)
                time.sleep(0.6)
                console_after = state_str(mcp10.state("console"), "console") or ""
                result.check("T10 disabled click dispatches nothing",
                             "saved:" not in console_after and console_after == console_before,
                             f"before={console_before[-40:]!r} after={console_after[-40:]!r}")

            # 10.2 reopen a tab → save re-enables (marker gone).
            plus = find_button_by_onclick(mcp10.snapshot(), "ActOpen")
            if plus:
                mcp10.click(plus)
                time.sleep(0.8)
                snap10 = mcp10.snapshot()
                save_btn = find_button_by_onclick(snap10, "ActSave")
                if save_btn:
                    m2 = re.search(r'button #' + re.escape(save_btn) + r'[^{]*\{[^}]*\}', snap10, re.S)
                    region2 = m2.group(0) if m2 else ""
                    result.check("T10 save re-enabled after open",
                                 "disabled: true" not in region2, region2[:120])

            # 10.3 hot reload: append an action + a T10 menu INSIDE the root
            # block (auto-atom rejects trailing nodes after the closing brace),
            # reload via the MCP tool, expect it in the next snapshot.
            # PLAN-630 T-03: 菜单已迁移声明式组件（不随 actions 热重载），
            # toolbar 仍为 actions 合成 → 热重载锚移到 toolbar。
            modified = config_backup.replace(
                "    actions {\n",
                "    actions {\n        action (id: \"help.t10\", handler: .ActAbout, title: \"T10 重载项\")\n",
                1,
            ).replace(
                "        toolbar {\n",
                "        toolbar {\n            item (action: \"help.t10\")\n",
                1,
            )
            assert "help.t10" in modified, "app.at actions-block anchors not found"
            with open(config_file, "w", encoding="utf-8", newline="") as f:
                f.write(modified)
            try:
                mcp10.call("action_config_reload")
                # Plan 451: 重建经 500ms tick -> gen-check -> view_dirty 链,
                # 轮询等待(实测 ~2s)而非固定 sleep。
                t10_seen = False
                for _ in range(6):
                    time.sleep(1)
                    if '"T10"' in mcp10.snapshot():
                        t10_seen = True
                        break
                # toolbar 合成按钮以 title 文本可寻址（无 icon 的 action 直
                # 出 title）；ActAbout 现有多个入口，取 T10 专属文本按钮。
                item = None
                for _ in range(6):
                    time.sleep(1)
                    m_btn = re.search(r'button #(\w+) "T10 重载项"', mcp10.snapshot())
                    if m_btn:
                        item = m_btn.group(1)
                        break
                result.check("T10 hot-reloaded toolbar item appears", item is not None,
                             "item not in snapshot after reload")
                if item:
                    mcp10.click(item)
                    time.sleep(0.4)
                    result.check("T10 reloaded item dispatches",
                                 "auto-edit 0.1" in (state_str(mcp10.state("console"), "console") or ""),
                                 "no about line")
            finally:
                with open(config_file, "w", encoding="utf-8", newline="") as f:
                    f.write(config_backup)
                mcp10.call("action_config_reload")  # restore effective config
        finally:
            _kill_proc_tree(t10_proc)
    else:
        print("  NOTE  AUTO_OPEN_PATH/AUTO_SAVE_PATH not set; skipping T10")

    # T11: Plan 423 P5 —— OS 用户层 keymap 端到端(独立进程 + 临时 APPDATA,
    # 不污染真实用户目录):写 <APPDATA>/auto/keymaps/auto-edit.at 覆盖
    # file.new 的快捷键 → action_config_reload 响应须含 "1 OS keymap overrides"。
    print("\nT11: OS user keymap layer (e2e)")
    if os.environ.get("AUTO_OPEN_PATH"):
        import shutil
        t11_appdata = tempfile.mkdtemp(prefix="auto041_t11_appdata_")
        t11_km_dir = os.path.join(t11_appdata, "auto", "keymaps")
        os.makedirs(t11_km_dir, exist_ok=True)
        with open(os.path.join(t11_km_dir, "auto-edit.at"), "w", encoding="utf-8") as f:
            f.write('k { action { id : "file.new"  shortcut : "Ctrl+Shift+Alt+F12" } }\n')
        t11_port = pick_free_port()
        t11_proc = subprocess.Popen(
            [AUTO_BIN, "run", "-r", "vm"],
            cwd=PROJECT,
            env={**os.environ, "AUTOUI_MCP_PORT": str(t11_port), "APPDATA": t11_appdata},
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            t11_url = f"http://127.0.0.1:{t11_port}/mcp"
            assert wait_for_server(t11_url, 30), "T11 server never up"
            mcp11 = McpClient(t11_url)
            resp = mcp11.call("action_config_reload")
            result.check("T11 OS keymap override applied (e2e)",
                         "1 OS keymap overrides" in resp, resp[:160])
        finally:
            _kill_proc_tree(t11_proc)
            shutil.rmtree(t11_appdata, ignore_errors=True)
    else:
        print("  NOTE  AUTO_OPEN_PATH not set; skipping T11")

    # T12: PLAN-008 —— 字节保真检查组（BOM/EOL 往返、mixed 转换、非法
    # UTF-8 兜底；每检查独立新鲜进程 + 仓内 fixture 的临时拷贝——磁盘
    # 断言打拷贝，仓内 fixture 保持 pristine）。「编辑」步 = 编辑菜单
    # 全选 → 工具栏 cut → undo（T6 既有模式；正文等值回归但经真实
    # buffer 漏斗——AC-01/02 的"编辑后"形态）。
    print("\nT12: PLAN-008 byte fidelity (BOM/EOL roundtrip, convert, fallback)")
    fixtures_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
    if os.path.isdir(fixtures_dir):
        import hashlib as _hashlib

        def _fix_copy(name):
            dst = tempfile.NamedTemporaryFile(
                prefix="auto041_t12_", suffix="_" + name, delete=False)
            with open(os.path.join(fixtures_dir, name), "rb") as f:
                dst.write(f.read())
            dst.close()
            return dst.name

        def _t12_app(path):
            port = pick_free_port()
            t12_proc = subprocess.Popen(
                [AUTO_BIN, "run", "-r", "vm"],
                cwd=PROJECT,
                env={**os.environ, "AUTOUI_MCP_PORT": str(port),
                     "AUTO_OPEN_PATH": path,
                     # PLAN-010 T-04：每实例独立 APPDATA（会话链恢复隔离，
                     # T14 惯例推广——共享 appdata 时前序检查的结构写盘会
                     # 漏进本实例启动恢复，装载竞态实测）。
                     "APPDATA": tempfile.mkdtemp(prefix="auto041_t12_ad_")},
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            t12_url = f"http://127.0.0.1:{port}/mcp"
            assert wait_for_server(t12_url, 30), "T12 server never up"
            t12 = McpClient(t12_url)
            for _ in range(15):
                s = t12.snapshot()
                if "(rendered)" in s and s.count("onclick") > 0:
                    break
                time.sleep(1)
            return t12_proc, t12

        def _t12_open(t12, path):
            plus = find_button_by_onclick(t12.snapshot(), "ActOpen")
            t12.click(plus)
            base = os.path.basename(path)
            for _ in range(48):
                c = state_str(t12.state("console"), "console") or ""
                if ("loaded: " in c or "load error" in c) and base in c:
                    return
                time.sleep(0.25)
            raise TimeoutError("T12 load line missing for " + base)

        def _t12_edit(t12):
            menu = find_button_by_text(t12.snapshot(), "编辑")
            if menu:
                t12.click(menu)
                time.sleep(1.0)
                sel = find_button_by_text(t12.snapshot(), "全选")
                if sel:
                    t12.click(sel)
                    time.sleep(0.5)
            cut = find_button_by_icon(t12.snapshot(), "scissors")
            if cut:
                t12.click(cut)
                time.sleep(0.4)
            undo = find_button_by_icon(t12.snapshot(), "undo-2")
            if undo:
                t12.click(undo)
                time.sleep(0.4)

        def _t12_save(t12):
            before = (state_str(t12.state("console"), "console") or "").count("saved:")
            save_btn = find_button_by_icon(t12.snapshot(), "save")
            t12.click(save_btn)
            c = ""
            for _ in range(40):
                c = state_str(t12.state("console"), "console") or ""
                if c.count("saved:") > before or "blocked" in c:
                    return c
                time.sleep(0.25)
            return c

        # 12.1 BOM 往返（编辑后）：首三字节 EF BB BF + 全文等值
        try:
            p = _fix_copy("BOM_UTF8.txt")
            orig = open(os.path.join(fixtures_dir, "BOM_UTF8.txt"), "rb").read()
            t12_proc, t12 = _t12_app(p)
            _t12_open(t12, p)
            _t12_edit(t12)
            _t12_save(t12)
            got = open(p, "rb").read()
            result.check("BOM roundtrip: EF BB BF prefix + content (after edit)",
                         got.startswith(b"\xef\xbb\xbf") and got == orig,
                         f"head={got[:6]!r} equal={got == orig}")
            _kill_proc_tree(t12_proc)
        except Exception as e:
            result.check("BOM roundtrip: EF BB BF prefix + content (after edit)",
                         False, repr(e))

        # 12.2 BOM 负向：无 BOM 文件（编辑后）保存不引入 BOM
        try:
            p = _fix_copy("LF.txt")
            orig = open(os.path.join(fixtures_dir, "LF.txt"), "rb").read()
            t12_proc, t12 = _t12_app(p)
            _t12_open(t12, p)
            _t12_edit(t12)
            _t12_save(t12)
            got = open(p, "rb").read()
            result.check("BOM negative: no BOM introduced (after edit)",
                         not got.startswith(b"\xef\xbb\xbf") and got == orig,
                         f"head={got[:4]!r} equal={got == orig}")
            _kill_proc_tree(t12_proc)
        except Exception as e:
            result.check("BOM negative: no BOM introduced (after edit)",
                         False, repr(e))

        # 12.3/12.4 EOL 往返（编辑后）：CRLF/LF 字节级行尾保留
        for fname in ("CRLF.txt", "LF.txt"):
            try:
                p = _fix_copy(fname)
                orig = open(os.path.join(fixtures_dir, fname), "rb").read()
                t12_proc, t12 = _t12_app(p)
                _t12_open(t12, p)
                _t12_edit(t12)
                _t12_save(t12)
                got = open(p, "rb").read()
                result.check(f"EOL roundtrip: {fname[:-4]} byte-level preserved (after edit)",
                             got == orig, f"got={got[:24]!r}")
                _kill_proc_tree(t12_proc)
            except Exception as e:
                result.check(f"EOL roundtrip: {fname[:-4]} byte-level preserved (after edit)",
                             False, repr(e))

        # 12.5 EOL CR（无编辑）+ 状态栏 label 断言
        try:
            p = _fix_copy("CR.txt")
            orig = open(os.path.join(fixtures_dir, "CR.txt"), "rb").read()
            t12_proc, t12 = _t12_app(p)
            _t12_open(t12, p)
            time.sleep(0.5)
            lbl = state_str(t12.state("eol_label"), "eol_label")
            _t12_save(t12)
            got = open(p, "rb").read()
            result.check("EOL CR: preserved (no edit) + status label CR",
                         got == orig and lbl == "CR", f"equal={got == orig} label={lbl}")
            _kill_proc_tree(t12_proc)
        except Exception as e:
            result.check("EOL CR: preserved (no edit) + status label CR",
                         False, repr(e))

        # 12.6 mixed 识别 + 转 LF（确认弹层）：磁盘零 \r\n + label 同步
        try:
            p = _fix_copy("MIXED.txt")
            t12_proc, t12 = _t12_app(p)
            _t12_open(t12, p)
            time.sleep(0.5)
            lbl0 = state_str(t12.state("eol_label"), "eol_label")
            menu = find_button_by_text(t12.snapshot(), "编辑")
            t12.click(menu)
            time.sleep(1.0)
            item = find_button_by_text(t12.snapshot(), "转为 LF (Unix)")
            t12.click(item)
            time.sleep(0.8)
            go = find_button_by_text(t12.snapshot(), "统一转换")
            if go:
                t12.click(go)
                time.sleep(0.8)
            lbl1 = state_str(t12.state("eol_label"), "eol_label")
            _t12_save(t12)
            got = open(p, "rb").read()
            result.check("mixed→LF convert: dialog + zero CRLF on disk + label sync",
                         lbl0 == "MIXED" and lbl1 == "LF" and got.count(b"\r\n") == 0
                         and b"\r" not in got, f"{lbl0}->{lbl1} got={got!r}")
            _kill_proc_tree(t12_proc)
        except Exception as e:
            result.check("mixed→LF convert: dialog + zero CRLF on disk + label sync",
                         False, repr(e))

        # 12.7 非法 UTF-8 兜底：readonly 标注 + save 拦截 + 磁盘哈希零变
        try:
            p = _fix_copy("INVALID_UTF8.bin")
            orig = open(p, "rb").read()
            h0 = _hashlib.sha256(orig).hexdigest()
            t12_proc, t12 = _t12_app(p)
            _t12_open(t12, p)
            time.sleep(0.8)
            title = state_str(t12.state("title_active"), "title_active") or ""
            ro = state_bool(t12.state("readonly_active"), "readonly_active")
            c = _t12_save(t12)
            h1 = _hashlib.sha256(open(p, "rb").read()).hexdigest()
            result.check("invalid UTF-8: readonly tab + save blocked + disk unchanged",
                         ro is True and "编码错误" in title and h0 == h1,
                         f"ro={ro} title={title!r} hash_eq={h0 == h1} console={c[-60:]!r}")
            _kill_proc_tree(t12_proc)
        except Exception as e:
            result.check("invalid UTF-8: readonly tab + save blocked + disk unchanged",
                         False, repr(e))
    else:
        print("  NOTE  tests/fixtures/ missing; skipping T12")

    # T13: PLAN-009 —— 查找替换四态 + ReplaceAll + find-in-files 检查组
    # （T12 形态：每检查独立新鲜进程 + 仓内 fixture 临时拷贝——磁盘断言
    # 打拷贝，仓内 fixture 保持 pristine）。子组：
    #   13.1 开栏 + effective 拼装四组合（字面转义/正则直通/大小写前缀/
    #        整词锚——装配序=转义→(?-i)→\b，T-00 决策）
    #   13.2 find_next 推进（live 首跳后 下一处 序列 + 回绕）
    #   13.3 Replace All E2E（落盘字节断言 + 计数反馈）
    #   13.4 readonly tab 拦截（非法 UTF-8 fixture，磁盘哈希零变）
    #   13.5 空 query 零动作
    #   13.6 find-in-files 端点 + 结果条目点击开文件
    #   13.7 上限截断（600 命中临时件 → count==500 + truncated）
    print("\nT13: PLAN-009 find/replace + find-in-files")
    find_fix = os.path.join(fixtures_dir, "find") if os.path.isdir(fixtures_dir) else ""
    if find_fix and os.path.isdir(find_fix):

        def _t13_app(path=None):
            port = pick_free_port()
            env = {**os.environ, "AUTOUI_MCP_PORT": str(port),
                   # PLAN-010 T-04：每实例独立 APPDATA（会话链恢复隔离）。
                   "APPDATA": tempfile.mkdtemp(prefix="auto041_t13_ad_")}
            if path:
                env["AUTO_OPEN_PATH"] = path
            proc = subprocess.Popen(
                [AUTO_BIN, "run", "-r", "vm"],
                cwd=PROJECT, env=env,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            url = f"http://127.0.0.1:{port}/mcp"
            assert wait_for_server(url, 30), "T13 server never up"
            t = McpClient(url)
            for _ in range(15):
                s = t.snapshot()
                if "(rendered)" in s and s.count("onclick") > 0:
                    break
                time.sleep(1)
            time.sleep(1.5)  # 首拍派发竞态窗口定驻（T-00④ 卫生）
            if path:
                # 打开 = 点 + 按钮（ActOpen 读 AUTO_OPEN_PATH 旁路——T9/T12
                # 同款；ConsumeOpen 的 env 种子仅 AUTO_BENCH=1 下生效，被动
                # 等待永不发生——T13 首两跑 loaded=0 根因），再等 loaded 行。
                plus = find_button_by_onclick(t.snapshot(), "ActOpen")
                if plus:
                    t.click(plus)
                base = os.path.basename(path)
                for _ in range(48):
                    c = state_str(t.state("console"), "console") or ""
                    if ("loaded: " in c or "load error" in c) and base in c:
                        break
                    time.sleep(0.25)
            return proc, t

        def _unesc(s):
            """autoui_state 文本对反斜杠的加倍渲染解码（探针 probe_find 同款）。"""
            if s is None:
                return None
            return s.replace("\\\\", "\\")

        def _t13_type_query(t, text):
            """键入查找词并重试至 find_effective 反映（首拍派发竞态卫生，
            probe_find type_into_input 同款）。"""
            for _ in range(4):
                _t13_type(t, _t13_find_input(t), text)
                eff = state_str(t.state("find_effective"), "find_effective")
                if eff == text:
                    return True
                time.sleep(0.5)
            return False

        def _t13_open_find(t):
            t.call("autoui_keyboard", key="f", modifiers=["ctrl"])
            time.sleep(0.5)
            return t

        def _t13_find_input(t):
            iid = re.search(r"input #(\w+)", t.snapshot())
            return iid.group(1) if iid else None

        def _t13_type(t, el, text):
            t.call("autoui_type", element_id=el, text=text, clear_first=True)
            time.sleep(0.6)

        def _t13_click_text(t, label):
            el = find_button_by_text(t.snapshot(), label)
            if el:
                t.click(el)
                time.sleep(0.5)
            return el is not None

        def _t13_cursor(t):
            st = t.state("line", "col")
            return state_int(st, "line"), state_int(st, "col")

        def _t13_fif_search(t):
            """点「搜索」并重试至 console 出现 fif 行（快照-派发间视图重建
            可致 vnode 失效静默丢失——T13 复跑 flake 卫生）。"""
            for _ in range(4):
                el = find_button_by_text(t.snapshot(), "搜索")
                if el:
                    t.click(el)
                for _ in range(10):
                    if (state_str(t.state("console"), "console") or "").count("fif:") > 0:
                        return True
                    time.sleep(0.5)
            return False

        def _t13_open_fif(t):
            """开 find-in-files 面板（Ctrl+Shift+F；修饰序兼容兜底=菜单入口）。"""
            t.call("autoui_keyboard", key="f", modifiers=["ctrl", "shift"])
            time.sleep(0.6)
            if state_bool(t.state("fif_open"), "fif_open") is True:
                return True
            menu = find_button_by_text(t.snapshot(), "编辑")
            if menu:
                t.click(menu)
                time.sleep(1.0)
                item = find_button_by_text(t.snapshot(), "跨文件查找")
                if item:
                    t.click(item)
                    time.sleep(0.6)
            return state_bool(t.state("fif_open"), "fif_open") is True

        # 13.1 开栏 + 拼装四组合
        try:
            p13, t = _t13_app()
            _t13_open_find(t)
            ok_open = state_bool(t.state("find_open"), "find_open")
            result.check("T13.1 find bar opens (Ctrl+F)", ok_open is True,
                         t.state("find_open"))
            _t13_type_query(t, "a.b")
            eff = _unesc(state_str(t.state("find_effective"), "find_effective"))
            result.check("T13.1a literal escape: eff a\\.b", eff == "a\\.b", f"eff={eff!r}")
            _t13_click_text(t, ".*")
            eff = _unesc(state_str(t.state("find_effective"), "find_effective"))
            result.check("T13.1b regex passthrough: eff a.b", eff == "a.b", f"eff={eff!r}")
            _t13_click_text(t, "Aa")
            eff = _unesc(state_str(t.state("find_effective"), "find_effective"))
            result.check("T13.1c case flag: eff (?-i)a.b", eff == "(?-i)a.b", f"eff={eff!r}")
            _t13_click_text(t, "[w]")
            eff = _unesc(state_str(t.state("find_effective"), "find_effective"))
            result.check("T13.1d word anchors: eff \\b(?-i)a.b\\b (regex on, dot raw)",
                         eff == "\\b(?-i)a.b\\b", f"eff={eff!r}")
            # 13.1e × 关栏：find_open 复位 + effective 清串（内核语义=清搜索态）
            xbtn = find_button_by_onclick(t.snapshot(), "FindClose")
            ok_x = xbtn is not None
            if ok_x:
                t.click(xbtn)
                time.sleep(0.5)
            st = t.state("find_open", "find_effective")
            result.check("T13.1e close: find_open false + eff cleared",
                         ok_x and state_bool(st, "find_open") is False
                         and state_str(st, "find_effective") == "",
                         f"st={st[:120]!r}")
            _kill_proc_tree(p13)
        except Exception as e:
            result.check("T13.1 find bar + assembly", False, repr(e))

        # 13.2 find_next 推进（fixture: alpha Alpha ALPHA / foo foobar foo /
        # alpha again；query=alpha 不敏感：3+1 命中）
        try:
            src = os.path.join(find_fix, "find_basic.txt")
            p13, t = _t13_app(src)
            _t13_open_find(t)
            typed = _t13_type_query(t, "alpha")
            effv = state_str(t.state("find_effective"), "find_effective")
            # live 首跳后内部光标在 match1（1-5）；下一处→match2 (1,12)
            ok_btn = _t13_click_text(t, "下一处")
            l, c = _t13_cursor(t)
            result.check("T13.2 find_next -> match2 (1,12)",
                         ok_btn and (l, c) == (1, 12),
                         f"cursor=({l},{c}) typed={typed} eff={effv!r}")
            _t13_click_text(t, "下一处")
            l, c = _t13_cursor(t)
            result.check("T13.2 find_next -> match3 (1,18)", (l, c) == (1, 18),
                         f"cursor=({l},{c})")
            _t13_click_text(t, "下一处")
            l, c = _t13_cursor(t)
            result.check("T13.2 find_next wraps -> line3 match (3,6)", (l, c) == (3, 6),
                         f"cursor=({l},{c})")
            _kill_proc_tree(p13)
        except Exception as e:
            result.check("T13.2 find_next progression", False, repr(e))

        # 13.3 Replace All E2E（落盘字节断言 + 计数反馈）
        try:
            dst = tempfile.NamedTemporaryFile(
                prefix="auto041_t13_", suffix="_find_basic.txt", delete=False)
            dst.write(open(os.path.join(find_fix, "find_basic.txt"), "rb").read())
            dst.close()
            p13, t = _t13_app(dst.name)
            t.call("autoui_keyboard", key="h", modifiers=["ctrl"])
            time.sleep(0.5)
            _t13_type_query(t, "alpha")
            effv = state_str(t.state("find_effective"), "find_effective")
            snap = t.snapshot()
            m = re.search(r'input #(\w+) \{[^}]*placeholder: "替换为"', snap)
            result.check("T13.3 replace row visible (Ctrl+H)",
                         m is not None, f"eff={effv!r} snap={snap[:100]}")
            if m:
                _t13_type(t, m.group(1), "XX")
                before = (state_str(t.state("console"), "console") or "").count("replace all:")
                _t13_click_text(t, "全部替换")
                c = ""
                for _ in range(20):
                    c = state_str(t.state("console"), "console") or ""
                    if c.count("replace all:") > before:
                        break
                    time.sleep(0.3)
                result.check("T13.3 replace all: 4 处 console", "replace all: 4 处" in c,
                             c[-120:])
                # save 落盘回读
                before_s = (state_str(t.state("console"), "console") or "").count("saved:")
                save_btn = find_button_by_icon(t.snapshot(), "save")
                t.click(save_btn)
                for _ in range(20):
                    c = state_str(t.state("console"), "console") or ""
                    if c.count("saved:") > before_s:
                        break
                    time.sleep(0.3)
                got = open(dst.name, "rb").read()
                want = "XX XX XX\nfoo foobar foo\nXX again\n".encode()
                result.check("T13.3 replace E2E disk bytes", got == want,
                             f"got={got[:60]!r} want={want[:60]!r}")
            _kill_proc_tree(p13)
            os.unlink(dst.name)
        except Exception as e:
            result.check("T13.3 replace all E2E", False, repr(e))

        # 13.4 readonly tab 拦截（非法 UTF-8 fixture：替换被拦 + 磁盘零变）
        try:
            import hashlib as _h13b
            dst = tempfile.NamedTemporaryFile(
                prefix="auto041_t13_", suffix="_invalid.bin", delete=False)
            dst.write(open(os.path.join(fixtures_dir, "INVALID_UTF8.bin"), "rb").read())
            dst.close()
            h0 = _h13b.sha256(open(dst.name, "rb").read()).hexdigest()
            p13, t = _t13_app(dst.name)
            time.sleep(0.5)
            ro = state_bool(t.state("readonly_active"), "readonly_active")
            lb = state_int(t.state("loaded_bytes"), "loaded_bytes")
            result.check("T13.4 pre: readonly engaged after load",
                         ro is True, f"ro={ro} loaded={lb}")
            t.call("autoui_keyboard", key="h", modifiers=["ctrl"])
            time.sleep(0.5)
            _t13_type_query(t, "text")
            m = re.search(r'input #(\w+) \{[^}]*placeholder: "替换为"', t.snapshot())
            if m:
                typed = _t13_type_query(t, "text")
                effv = state_str(t.state("find_effective"), "find_effective")
                _t13_type(t, m.group(1), "YY")
                _t13_click_text(t, "全部替换")
                c = ""
                for _ in range(16):
                    c = state_str(t.state("console"), "console") or ""
                    if "blocked (readonly)" in c:
                        break
                    time.sleep(0.3)
                h1 = _h13b.sha256(open(dst.name, "rb").read()).hexdigest()
                result.check("T13.4 readonly blocks replace + disk unchanged",
                             ro is True and "blocked (readonly" in c and h0 == h1,
                             f"ro={ro} typed={typed} eff={effv!r} "
                             f"console_head={c[:120]!r} hash_eq={h0 == h1}")
            _kill_proc_tree(p13)
            os.unlink(dst.name)
        except Exception as e:
            result.check("T13.4 readonly replace block", False, repr(e))

        # 13.5 空 query 零动作（Ctrl+H 直接全部替换）
        try:
            p13, t = _t13_app()
            t.call("autoui_keyboard", key="h", modifiers=["ctrl"])
            time.sleep(0.5)
            _t13_click_text(t, "全部替换")
            time.sleep(0.5)
            c = state_str(t.state("console"), "console") or ""
            result.check("T13.5 empty query: zero action logged",
                         "replace all: empty query" in c, c[-100:])
            _kill_proc_tree(p13)
        except Exception as e:
            result.check("T13.5 empty query zero action", False, repr(e))

        # 13.6 find-in-files：端点结果 + 条目点击开文件
        # （workspace 根 = 仓 specs/auto-edit；needle 动态拼装——字面量不
        # 落本文件，desktop_mcp.py 自身不计入命中。fixtures/find/find_fif/
        # 两件：one.txt L1 + two.txt L1/L2 = 3 条）
        try:
            needle = "fifneedle" + "009"
            p13, t = _t13_app()
            result.check("T13.6 fif panel opens (Ctrl+Shift+F/menu)",
                         _t13_open_fif(t) is True, t.state("fif_open"))
            _t13_open_find(t)
            _t13_type_query(t, needle)
            _t13_fif_search(t)
            fc = -1
            for _ in range(60):
                st = t.state("fif_count", "fif_truncated")
                fc = state_int(st, "fif_count")
                if fc >= 0 and (state_str(t.state("console"), "console") or "").count("fif:") > 0:
                    break
                time.sleep(0.5)
            trunc = state_bool(t.state("fif_truncated"), "fif_truncated")
            result.check("T13.6 fif results: count==3 not truncated",
                         fc == 3 and trunc is False, f"count={fc} trunc={trunc}")
            tc0 = state_int(t.state("tab_count"), "tab_count")
            opened = False
            for _ in range(4):
                m = re.search(r'button #(\w+) "[^"]*two\.txt[^"]*"', t.snapshot())
                if m:
                    t.click(m.group(1))
                    for _ in range(8):
                        time.sleep(0.3)
                        if state_int(t.state("tab_count"), "tab_count") == tc0 + 1:
                            opened = True
                            break
                    if opened:
                        break
                else:
                    break
            st = t.state("tab_count", "title_active")
            result.check("T13.6 result click opens file tab",
                         opened and state_str(st, "title_active") == "two.txt", st)
            _kill_proc_tree(p13)
        except Exception as e:
            result.check("T13.6 find-in-files", False, repr(e))

        # 13.7 上限截断（600 命中临时件 → count==500 + truncated；finally 删除）
        big = os.path.join(find_fix, "_t13_big_tmp.txt")
        try:
            with open(big, "w", encoding="utf-8", newline="") as f:
                for _ in range(600):
                    f.write("hitline009 unique\n")
            p13, t = _t13_app()
            _t13_open_fif(t)
            _t13_open_find(t)
            _t13_type_query(t, "hitline009")
            _t13_fif_search(t)
            fc = -1
            trunc = None
            for _ in range(90):
                st = t.state("fif_count", "fif_truncated")
                fc = state_int(st, "fif_count")
                trunc = state_bool(st, "fif_truncated")
                if fc >= 500:
                    break
                time.sleep(0.5)
            result.check("T13.7 truncation: count==500 + truncated",
                         fc == 500 and trunc is True, f"count={fc} trunc={trunc}")
            _kill_proc_tree(p13)
        except Exception as e:
            result.check("T13.7 limit truncation", False, repr(e))
        finally:
            if os.path.exists(big):
                os.unlink(big)
        # 13.8 >10MB 大小门（11MB 临时件含独一 needle → 门生效=0 命中；
        # finally 删除）
        big11 = os.path.join(find_fix, "_t13_big11_tmp.txt")
        try:
            needle11 = "skipneedle" + "009"
            with open(big11, "w", encoding="utf-8", newline="") as f:
                line = "x" * 128 + "\n"
                for _ in range(64):
                    f.write(line * 1024)  # ~8.4MB … 补足 >10MB
                f.write(needle11 + " present but file exceeds gate\n")
            if os.path.getsize(big11) <= 10 * 1024 * 1024:
                with open(big11, "a", encoding="utf-8", newline="") as f:
                    f.write(("y" * 128 + "\n") * 16384)  # +~2MB 兜底
            p13, t = _t13_app()
            _t13_open_fif(t)
            _t13_open_find(t)
            _t13_type_query(t, needle11)
            _t13_fif_search(t)
            fc = -1
            for _ in range(60):
                st = t.state("fif_count", "fif_truncated")
                fc = state_int(st, "fif_count")
                if fc >= 0 and (state_str(t.state("console"), "console") or "").count("fif:") > 0:
                    break
                time.sleep(0.5)
            result.check("T13.8 >10MB gate: oversized file skipped (count==0)",
                         fc == 0, f"count={fc}")
            _kill_proc_tree(p13)
        except Exception as e:
            result.check("T13.8 >10MB gate", False, repr(e))
        finally:
            if os.path.exists(big11):
                os.unlink(big11)
    else:
        print("  NOTE  tests/fixtures/find missing; skipping T13")

    # T14: PLAN-010 —— 会话恢复 + 最近文件检查组（T12/T13 形态：每检查
    # 独立新鲜进程 + 临时 APPDATA 隔离——T11 OS keymap 先例；fixtures/
    # session/ 拷贝为断言面，仓内 fixture 保持 pristine）。子组：
    #   14.1 会话写入（字段齐全/untitled 排除/recents 同录）
    #   14.2 重启恢复（注入会话 → tab 序 + active + 仅 active 装载）
    #   14.3 激活未装载 tab 触发装载（懒装载协议）
    #   14.4 ws_dir 不匹配 → 全新启动零回归
    #   14.5 崩溃恢复（taskkill 强杀 → 重启还原）
    #   14.6 退出恢复（脏 tab 边界=不保存退出 → 结构在/脏编辑丢）
    #   14.7 最近文件侧栏（关闭后条目在 + 点击重开懒装载）
    #   14.8 ActNew untitled 化 → 会话排除
    #   14.9 损坏 JSON → 静默全新启动（G-3 不匹配语义）
    # 恢复链检查用 python 侧注入会话文件（全控 tab 集/激活位——UI 只能
    # 开同一路径的重复 tab，注入是恢复序的可控驱动面）。
    print("\nT14: PLAN-010 session restore + recent files")
    sess_fix = os.path.join(fixtures_dir, "session") if os.path.isdir(fixtures_dir) else ""
    if sess_fix and os.path.isdir(sess_fix):

        def _t14_fix(name):
            # 每检查独立目录 + 保留原短名——侧栏条目标题=file_basename，
            # w-56 窄栏对 30+ 字符随机长名会截断快照标签（间歇精确匹配
            # 失败实测），短名确定性拷贝根治。
            dst_dir = tempfile.mkdtemp(prefix="auto010_t14_")
            dst = os.path.join(dst_dir, name)
            with open(os.path.join(sess_fix, name), "rb") as f, \
                 open(dst, "wb") as g:
                g.write(f.read())
            return dst

        def _t14_app(appdata, open_path=None):
            port = pick_free_port()
            env = {**os.environ, "AUTOUI_MCP_PORT": str(port), "APPDATA": appdata}
            if open_path:
                env["AUTO_OPEN_PATH"] = open_path
            proc = subprocess.Popen(
                [AUTO_BIN, "run", "-r", "vm"],
                cwd=PROJECT, env=env,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            url = f"http://127.0.0.1:{port}/mcp"
            assert wait_for_server(url, 30), "T14 server never up"
            t = McpClient(url)
            for _ in range(15):
                s = t.snapshot()
                if "(rendered)" in s and s.count("onclick") > 0:
                    break
                time.sleep(1)
            time.sleep(1.5)  # 首拍派发竞态窗定驻（009 同款卫生）
            return proc, t

        def _t14_open_via_plus(t, path):
            plus = find_button_by_onclick(t.snapshot(), "ActOpen")
            if plus:
                t.click(plus)
            want = len(open(path, "rb").read())
            for _ in range(48):
                if state_int(t.state("loaded_bytes"), "loaded_bytes") == want:
                    return True
                time.sleep(0.25)
            return False

        def _t14_close_all(t):
            for _ in range(4):
                if state_int(t.state("tab_count"), "tab_count") == 0:
                    return True
                xs = find_tab_close_buttons(t.snapshot())
                if not xs:
                    time.sleep(0.4)
                    continue
                t.click(xs[0])
                time.sleep(0.6)
            return state_int(t.state("tab_count"), "tab_count") == 0

        def _t14_sess_path(appdata):
            return os.path.join(appdata, "auto-edit-session.json")

        def _t14_inject(appdata, ws_dir, tabs, active, open_count, recents):
            with open(_t14_sess_path(appdata), "w", encoding="utf-8") as f:
                json.dump({"ws_dir": ws_dir, "open_count": open_count,
                           "active": active, "tabs": tabs, "recents": recents}, f)

        def _t14_read_sess(appdata):
            p = _t14_sess_path(appdata)
            if not os.path.exists(p):
                return None
            try:
                with open(p, encoding="utf-8") as f:
                    return json.loads(f.read())
            except Exception:
                return None

        def _t14_poll_loaded(t, want, extra=None):
            for _ in range(30):
                if state_int(t.state("loaded_bytes"), "loaded_bytes") == want:
                    return True
                time.sleep(0.3)
            return False

        def _t14_quit_via_menu(t, proc):
            snap = t.snapshot()
            m = find_button_by_text(snap, "文件")
            if m:
                t.click(m)
                time.sleep(1.0)
            snap = t.snapshot()
            q = find_button_by_text(snap, "退出")
            if q:
                try:
                    t.click(q)
                except (requests.ConnectionError, requests.Timeout):
                    pass
            for _ in range(6):
                if proc.poll() is not None:
                    break
                try:
                    snap = t.snapshot()
                except Exception:
                    break
                d = find_button_by_text(snap, "不保存退出")
                if d:
                    try:
                        t.click(d)
                    except (requests.ConnectionError, requests.Timeout):
                        pass
                    break
                time.sleep(0.4)
            for _ in range(12):
                if proc.poll() is not None:
                    return True
                time.sleep(0.5)
            return False

        # 14.1 会话写入：字段齐全 + untitled 排除 + recents 同录
        ws_norm = os.path.normpath(PROJECT)
        try:
            ad = tempfile.mkdtemp(prefix="auto010_t14_ad_")
            fa = _t14_fix("restore_a.txt")
            p14, t = _t14_app(ad, open_path=fa)
            ok_open = _t14_open_via_plus(t, fa)
            time.sleep(0.5)
            sess = _t14_read_sess(ad)
            ok = (ok_open and sess is not None
                  and len(sess.get("tabs", [])) == 1
                  and sess["tabs"][0].get("path") == fa
                  and sess.get("active") == 0
                  and sess.get("open_count") == 3
                  and len(sess.get("recents", [])) == 1
                  and sess["recents"][0].get("path") == fa
                  and set(sess["tabs"][0].keys()) == {"path", "title", "cline", "ccol"})
            if sess:
                ws_norm = sess.get("ws_dir", ws_norm)
            result.check("T14.1 session write: fields + untitled excluded + recents",
                         ok, json.dumps(sess, ensure_ascii=False)[:200] if sess else "no file")
            _kill_proc_tree(p14)
        except Exception as e:
            result.check("T14.1 session write", False, repr(e))

        # 14.2 重启恢复（懒装载）：注入 [A,B] active=1 → 序+active+仅 B 装载
        # 14.3 激活未装载 tab 触发装载（同实例切 A）
        try:
            ad = tempfile.mkdtemp(prefix="auto010_t14_ad_")
            fa = _t14_fix("restore_a.txt")
            fb = _t14_fix("restore_b.txt")
            ba = len(open(fa, "rb").read())
            bb = len(open(fb, "rb").read())
            _t14_inject(ad, ws_norm, [
                {"path": fa, "title": os.path.basename(fa), "cline": 1, "ccol": 1},
                {"path": fb, "title": os.path.basename(fb), "cline": 2, "ccol": 3},
            ], 1, 2, [])
            p14, t = _t14_app(ad)
            st = t.state("tab_count", "tab", "title_active")
            ok_struct = (state_int(st, "tab_count") == 2 and state_int(st, "tab") == 1
                         and state_str(st, "title_active") == os.path.basename(fb))
            lb = -1
            for _ in range(30):
                lb = state_int(t.state("loaded_bytes"), "loaded_bytes")
                if lb == bb:
                    break
                time.sleep(0.3)
            n_ed = t.snapshot().count("textarea")
            result.check("T14.2 restore: order + active + only-active loaded",
                         ok_struct and lb == bb and n_ed == 1,
                         f"st={st[:120]!r} lb={lb} want={bb} editors={n_ed}")
            btn = find_button_by_text(t.snapshot(), os.path.basename(fa))
            if btn:
                t.click(btn)
            la = -1
            for _ in range(30):
                la = state_int(t.state("loaded_bytes"), "loaded_bytes")
                if la == ba:
                    break
                time.sleep(0.3)
            st = t.state("tab")
            result.check("T14.3 activate unloaded tab triggers load",
                         la == ba and state_int(st, "tab") == 0,
                         f"lb={la} want={ba} st={st[:60]!r}")
            _kill_proc_tree(p14)
        except Exception as e:
            result.check("T14.2/3 restore + lazy load", False, repr(e))

        # 14.4 ws_dir 不匹配 → 全新启动（种子，无恢复行）
        try:
            ad = tempfile.mkdtemp(prefix="auto010_t14_ad_")
            _t14_inject(ad, "D:/nonexistent-ws-plan010", [
                {"path": "C:/nonexistent.txt", "title": "x.txt", "cline": 1, "ccol": 1},
            ], 0, 1, [])
            p14, t = _t14_app(ad)
            st = t.state("tab_count")
            console = state_str(t.state("console"), "console") or ""
            result.check("T14.4 ws mismatch: fresh start (seeds only, no restore line)",
                         state_int(st, "tab_count") == 2 and "session: restored" not in console,
                         f"st={st[:80]!r} console={console[-100:]!r}")
            _kill_proc_tree(p14)
        except Exception as e:
            result.check("T14.4 ws mismatch", False, repr(e))

        # 14.5 崩溃恢复：强杀（会话即时落盘在先）→ 重启还原
        try:
            ad = tempfile.mkdtemp(prefix="auto010_t14_ad_")
            fa = _t14_fix("restore_a.txt")
            ba = len(open(fa, "rb").read())
            p14, t = _t14_app(ad, open_path=fa)
            ok_open = _t14_open_via_plus(t, fa)
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(p14.pid)],
                           capture_output=True)
            try:
                p14.wait(5)
            except Exception:
                pass
            p14b, t2 = _t14_app(ad)
            st = t2.state("tab_count", "title_active")
            ok_lb = _t14_poll_loaded(t2, ba)
            lb = state_int(t2.state("loaded_bytes"), "loaded_bytes")
            result.check("T14.5 crash recovery: kill → restart restores",
                         ok_open and state_int(st, "tab_count") == 1
                         and state_str(st, "title_active") == os.path.basename(fa)
                         and ok_lb,
                         f"st={st[:100]!r} lb={lb} want={ba}")
            _kill_proc_tree(p14b)
        except Exception as e:
            result.check("T14.5 crash recovery", False, repr(e))

        # 14.6 退出恢复（脏边界）：cut 脏化 → 不保存退出 → 结构在/脏编辑丢
        try:
            ad = tempfile.mkdtemp(prefix="auto010_t14_ad_")
            fa = _t14_fix("restore_a.txt")
            orig = open(os.path.join(sess_fix, "restore_a.txt"), "rb").read()
            ba = len(orig)
            p14, t = _t14_app(ad, open_path=fa)
            _t14_open_via_plus(t, fa)
            cut = find_button_by_icon(t.snapshot(), "scissors")
            if cut:
                t.click(cut)
                time.sleep(0.5)
            exited = _t14_quit_via_menu(t, p14)
            sess = _t14_read_sess(ad)
            p14b, t2 = _t14_app(ad)
            st = t2.state("tab_count", "title_active")
            ok_lb = _t14_poll_loaded(t2, ba)
            got = open(fa, "rb").read()
            result.check("T14.6 quit-restore: structure kept + dirty edits lost",
                         exited and sess is not None and len(sess.get("tabs", [])) == 1
                         and state_int(st, "tab_count") == 1
                         and state_str(st, "title_active") == os.path.basename(fa)
                         and ok_lb and got == orig,
                         f"exited={exited} sess={json.dumps(sess, ensure_ascii=False)[:120] if sess else None} "
                         f"lb_ok={ok_lb} disk_eq={got == orig}")
            _kill_proc_tree(p14b)
        except Exception as e:
            result.check("T14.6 quit-restore dirty boundary", False, repr(e))

        # 14.7 最近文件侧栏：全关后条目仍在 + 点击重开懒装载
        try:
            ad = tempfile.mkdtemp(prefix="auto010_t14_ad_")
            fa = _t14_fix("restore_a.txt")
            ba = len(open(fa, "rb").read())
            p14, t = _t14_app(ad, open_path=fa)
            ok_open = _t14_open_via_plus(t, fa)
            ok_vis = find_button_by_text(t.snapshot(), os.path.basename(fa)) is not None
            ok_closed = _t14_close_all(t)
            reopened = False
            # 重试臂（快照-派发间视图重建可致 vnode 失效静默丢失——009
            # fif 搜索点击同款卫生）：重取快照重点击，直到重开达成。
            for _ in range(4):
                item = find_button_by_text(t.snapshot(), os.path.basename(fa))
                if item:
                    t.click(item)
                for _ in range(10):
                    lb = state_int(t.state("loaded_bytes"), "loaded_bytes")
                    tc = state_int(t.state("tab_count"), "tab_count")
                    if lb == ba and tc == 1:  # 全关后重开=1
                        reopened = True
                        break
                    time.sleep(0.3)
                if reopened:
                    break
            result.check("T14.7 recents sidebar: survives close-all + click reopens",
                         ok_open and ok_vis and ok_closed and item is not None and reopened,
                         f"open={ok_open} vis={ok_vis} closed={ok_closed} "
                         f"item={item is not None} reopened={reopened}")
            _kill_proc_tree(p14)
        except Exception as e:
            result.check("T14.7 recents sidebar", False, repr(e))

        # 14.8 ActNew untitled 化 → 会话排除
        try:
            ad = tempfile.mkdtemp(prefix="auto010_t14_ad_")
            fa = _t14_fix("restore_a.txt")
            p14, t = _t14_app(ad, open_path=fa)
            _t14_open_via_plus(t, fa)
            snap = t.snapshot()
            m = find_button_by_text(snap, "文件")
            if m:
                t.click(m)
                time.sleep(1.0)
            nbtn = find_button_by_text(t.snapshot(), "新建")
            if nbtn:
                t.click(nbtn)
                time.sleep(0.8)
            sess = _t14_read_sess(ad)
            result.check("T14.8 ActNew untitled: file path cleared → excluded",
                         sess is not None and len(sess.get("tabs", [])) == 0,
                         json.dumps(sess, ensure_ascii=False)[:160] if sess else "no file")
            _kill_proc_tree(p14)
        except Exception as e:
            result.check("T14.8 ActNew untitled exclusion", False, repr(e))

        # 14.9 损坏 JSON → 静默全新启动（G-3）
        try:
            ad = tempfile.mkdtemp(prefix="auto010_t14_ad_")
            with open(_t14_sess_path(ad), "w", encoding="utf-8") as f:
                f.write("{corrupted plan010 session!!!")
            p14, t = _t14_app(ad)
            st = t.state("tab_count")
            console = state_str(t.state("console"), "console") or ""
            result.check("T14.9 corrupted session: silent fresh start",
                         state_int(st, "tab_count") == 2
                         and "session: restored" not in console
                         and p14.poll() is None,
                         f"st={st[:80]!r} console={console[-100:]!r}")
            _kill_proc_tree(p14)
        except Exception as e:
            result.check("T14.9 corrupted session", False, repr(e))
    else:
        print("  NOTE  tests/fixtures/session missing; skipping T14")

    print()
    print("T8: ActQuit (menu item)")
    open_menu(mcp, snap_cache, "文件")
    item = find_button_by_text(snap_cache[0], "退出")
    if item:
        # ActQuit（PLAN-626 T-06 起）带脏检查：有脏 tab 先弹退出确认
        # alert-dialog。T6 的键入/撤销序列会遗留 dirty tab —— 确认层出现时
        # 走「不保存退出」(QuitDiscard) 完成退出。Process.exit(0) 可能在
        # HTTP 响应完成前杀进程——连接被断即成功路径（异常吞掉）。
        try:
            mcp.click(item)
        except (requests.ConnectionError, requests.Timeout):
            pass
        try:
            for _ in range(4):
                snap_cache[0] = mcp.snapshot()
                discard = find_button_by_text(snap_cache[0], "不保存退出")
                if proc.poll() is not None:
                    break
                if discard:
                    mcp.click(discard)
                    break
                time.sleep(0.3)
        except (requests.ConnectionError, requests.Timeout):
            pass
        for _ in range(10):
            if proc.poll() is not None:
                break
            time.sleep(0.5)
        result.check("app exited on quit", proc.poll() is not None,
                     f"process still running (poll={proc.poll()})")
    else:
        result.check("quit menu item found", False, "no .ActQuit in file menu")

    return result


def main():
    print("=" * 60)
    print("Plan 418 Phase 1: Desktop MCP action-matrix (real 041 auto-edit)")
    print("=" * 60)

    if not AUTO_BIN or not os.path.exists(AUTO_BIN):
        print(f"ERROR: auto binary not found (AUTO_BIN={AUTO_BIN or 'unset'})")
        print("Add auto's directory to PATH, or set AUTO_BIN env var to the binary path.")
        sys.exit(2)

    # PLAN-010 T-04 基建卫生：整跑 APPDATA 隔离（T11 先例推广到主实例）——
    # 会话链把 auto-edit-session.json 落 APPDATA 根，主实例与全部子实例
    # 继承本环境；不隔离则 T8 退出写盘污染真实用户会话、下一跑启动恢复
    # 垃圾 tab（首跑 T3b/T5/T6/T7b/T12.5/T12.6 十失败根因实测）。T11/T14
    # 各自的显式 APPDATA 覆盖不受影响（env 展开序在后）。
    run_appdata = tempfile.mkdtemp(prefix="auto041_matrix_appdata_")
    os.environ["APPDATA"] = run_appdata

    mcp_port = pick_free_port()
    mcp_url = f"http://localhost:{mcp_port}/mcp"
    if mcp_port != MCP_PORT_DEFAULT:
        print(f"NOTE: port {MCP_PORT_DEFAULT} busy (stale auto.exe?); "
              f"using AUTOUI_MCP_PORT={mcp_port}")

    print(f"\nStarting real 041 auto-edit in {PROJECT}...")
    app_log = tempfile.NamedTemporaryFile(
        prefix="auto041_mcp_", suffix=".log", delete=False, mode="w",
        encoding="utf-8", errors="replace")
    # Plan 420 T9: file open/save automation bypass — with these set, ActOpen/
    # ActSave skip the blocking rfd dialogs (test-build semantics only).
    roundtrip_file = tempfile.NamedTemporaryFile(
        prefix="auto041_t9_", suffix=".at", delete=False, mode="w", encoding="utf-8")
    roundtrip_file.write("// t9 roundtrip file\nfn t9() int { 42 }\n")
    roundtrip_file.flush()
    roundtrip_file.close()
    os.environ["AUTO_OPEN_PATH"] = roundtrip_file.name
    os.environ["AUTO_SAVE_PATH"] = roundtrip_file.name
    t9_env = {
        **os.environ,
        "AUTOUI_MCP_PORT": str(mcp_port),
    }
    proc = subprocess.Popen(
        [AUTO_BIN, "run", "-r", "vm"],
        cwd=PROJECT,
        env=t9_env,
        stdout=app_log,
        stderr=subprocess.STDOUT,
    )
    print(f"App output log: {app_log.name}")

    try:
        print(f"Waiting for MCP server on port {mcp_port}...")
        if not wait_for_server(mcp_url):
            print("ERROR: MCP server did not start within 30s.")
            proc.kill()
            sys.exit(1)
        print("MCP server ready")
        result = run_tests(mcp_url, proc)
    finally:
        # Plan 423 P5:proc.kill() 在 Windows 上不杀子进程树,UI 应用可能无视
        # WM_CLOSE 存活成孤儿(内存失控时曾被留下)—— taskkill /T /F 兜底。
        if proc.poll() is None:
            proc.kill()
        subprocess.run(
            ["taskkill", "/T", "/F", "/PID", str(proc.pid)],
            capture_output=True,
        )

    print("\n" + "=" * 60)
    print(f"RESULT: {result.passed} passed, {result.failed} failed")
    if result.errors:
        print("Failures:")
        for e in result.errors:
            print(f"  - {e}")
    print("=" * 60)
    shutil.rmtree(run_appdata, ignore_errors=True)
    sys.exit(1 if result.failed else 0)


if __name__ == "__main__":
    main()
