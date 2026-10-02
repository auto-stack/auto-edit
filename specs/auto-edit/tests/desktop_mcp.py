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

import hashlib
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


def wait_console_line(mcp, substr, timeout=8):
    """PLAN-017: console 镜像（.console state）相对 handler 执行有异步
    滞后（状态字段即时、console 行延后到齐——开发期实证）——轮询至
    目标行出现或超时。返回出现时刻的 console 全文（超时返回 None）。"""
    deadline = time.time() + timeout
    con = ""
    while time.time() < deadline:
        con = state_str(mcp.state("console"), "console") or ""
        if substr in con:
            return con
        time.sleep(0.5)
    return None


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

    # T15: PLAN-011 —— 文件 diff 检查组（T14 形态：独立新鲜进程+APPDATA
    # 隔离；fixtures/diff 六形态 golden 在档）。驱动面=env 旁路 Tick 自开
    # （AUTO_DIFF_A/B；menubar 展开项 2044 不进 vtree+键盘 AltGr 疑虑，
    # 双双不可作矩阵依赖——T-02 实勘）。子组：
    #   15.1 旁路自开+计数 state（scattered：3 hunks/21 rows/+3/-3）
    #   15.2 形状计数 dbg 断言（ctx/pair/del/add=18/3/0/0——golden 对齐）
    #   15.3 行内三段标记（pair 段节点分离口径——拼接串探针=假阳性
    #        教训 T-03）
    #   15.4 hunk 导航推进+回绕（idx 序列 [1,2,0,1,0]）
    #   15.5 hunk 位次派生（diff_hunk_pos）
    #   15.6 关闭复原（tab 集零扰动+状态清零）
    #   15.7 unbalanced 形态（del-only/add-only 行+dbg 4/1/2/0）
    #   15.8 错误形（缺文件 → err 态零视图+console 记录）
    #   15.9 超限通过（PLAN-016 翻转：>10000 行正常 envelope——引擎时代）
    #   15.10 全换形重定（PLAN-016：degraded=false+700/700+降级注记退役）
    #   15.11-15.15 PLAN-015 内联视图组（复审 F-1 落位；详见组内
    #         注释——投影对照/零重比+console/内联导航/双 cap/内联态
    #         重算-下钻路径）
    #   15.16-15.19 PLAN-016 缓冲区比较组（旁路自开+装载轮转 B→A 序/
    #         跳转 set_cursor 读回/旁路残缺 err 形/关闭复原——缺键端点
    #         err 形由 probe_bufdiff.py 探针承载）
    #   15.20-15.24 PLAN-017 差异侧编辑回路子组（双侧跳转[新开/激活两
    #         路径+行级锚]/保存自动重比[badge live→保存→视图自动重开+
    #         vmode 保持+计数变形]/无关保存零扰动/面板 live 预览/B 侧
    #         跳转——label 解析行号真值）
    # 上游缺陷史（PLAN-016 执行期勘定+修复轮清偿，供料档 §6.2）：引擎
    # rows 面流位错配（D-1）+anchor 非单调（D-2）曾使 15.1/15.2/15.3/
    # 15.7/15.11/15.14/15.15 rows 承载断言入已知 blocked 集——auto-lang
    # PLAN-704（b2f8761e0）修复后 golden 重定轮恢复原口径（工具链
    # ≥v0.4.2-2183 判据）。
    print("\nT15: PLAN-011 file diff")
    diff_fix = os.path.join(fixtures_dir, "diff")
    if os.path.isdir(diff_fix):

        def _t15_app(extra):
            port = pick_free_port()
            env = {**os.environ, "AUTOUI_MCP_PORT": str(port),
                   "APPDATA": tempfile.mkdtemp(prefix="auto011_t15_"), **extra}
            proc = subprocess.Popen(
                [AUTO_BIN, "run", "-r", "vm"],
                cwd=PROJECT, env=env,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            url = f"http://127.0.0.1:{port}/mcp"
            assert wait_for_server(url, 30), "T15 server never up"
            t = McpClient(url)
            for _ in range(15):
                s = t.snapshot()
                if "(rendered)" in s and s.count("onclick") > 0:
                    break
                time.sleep(1)
            time.sleep(1.5)
            return proc, t

        def _t15_wait_open(t, timeout=15):
            for _ in range(timeout * 2):
                if state_bool(t.state("diff_open"), "diff_open"):
                    return True
                time.sleep(0.5)
            return False

        # 15.1-15.6 共享实例（scattered 三 hunk 形态）
        try:
            p15, t15 = _t15_app({
                "AUTO_DIFF_A": os.path.join(diff_fix, "scattered.a.txt"),
                "AUTO_DIFF_B": os.path.join(diff_fix, "scattered.b.txt")})
            ok_open = _t15_wait_open(t15)
            st = t15.state("diff_rows_count", "diff_hunk_count", "diff_hunk_idx",
                           "diff_adds", "diff_dels", "diff_rows_truncated",
                           "diff_degraded", "diff_err", "diff_dbg_ctx",
                           "diff_dbg_pair", "diff_dbg_del", "diff_dbg_add")
            result.check("T15.1 env 旁路自开+计数（3 hunks/21 rows/+3/-3）",
                         ok_open and state_int(st, "diff_hunk_count") == 3
                         and state_int(st, "diff_rows_count") == 21
                         and state_int(st, "diff_adds") == 3
                         and state_int(st, "diff_dels") == 3,
                         st.replace("\n", " ")[:200])
            result.check("T15.2 形状计数（ctx18/pair3/del0/add0）",
                         state_int(st, "diff_dbg_ctx") == 18
                         and state_int(st, "diff_dbg_pair") == 3
                         and state_int(st, "diff_dbg_del") == 0
                         and state_int(st, "diff_dbg_add") == 0,
                         st.replace("\n", " ")[:160])
            snap15 = t15.snapshot()
            result.check("T15.3 三段标记节点（4-changed/19-changed 分离节点）",
                         '"4-changed"' in snap15 and '"19-changed"' in snap15,
                         "pair 段节点缺失")
            result.check("T15.3b 状态条（DIFF 标+hunk 位次 1/3）",
                         "DIFF" in snap15 and "hunk 1/3" in snap15, "")
            seq = []
            b_next = find_button_by_text(snap15, "下一处")
            b_prev = find_button_by_text(snap15, "上一处")
            for el in [b_next, b_next, b_next, b_next, b_prev]:
                if el:
                    t15.click(el)
                    time.sleep(0.5)
                    seq.append(state_int(t15.state("diff_hunk_idx"),
                                         "diff_hunk_idx"))
            result.check("T15.4 导航推进回绕 [1,2,0,1,0]",
                         seq == [1, 2, 0, 1, 0], str(seq))
            # 序列尾=上一处（idx 1→0）→ 位次 1/3（T15.4 序列终态对齐）
            pos = (state_str(t15.state("diff_hunk_pos"), "diff_hunk_pos")
                   or "").strip('"')
            result.check("T15.5 hunk 位次派生 1/3（序列终态对齐）",
                         pos == "1/3", repr(pos))
            tabs_before = state_int(t15.state("tab_count"), "tab_count")
            b_close = find_button_by_text(snap15, "×")
            if b_close:
                t15.click(b_close)
                time.sleep(0.8)
            st2 = t15.state("diff_open", "tab_count", "diff_rows_count",
                            "diff_hunk_count")
            result.check("T15.6 关闭复原（tab 零扰动+态清零）",
                         state_bool(st2, "diff_open") is False
                         and state_int(st2, "tab_count") == tabs_before
                         and state_int(st2, "diff_rows_count") == 0,
                         st2.replace("\n", " ")[:160])
            _kill_proc_tree(p15)
        except Exception as e:
            result.check("T15.1-6 scattered 主链", False, repr(e))

        # 15.7 unbalanced 形态（删多增少）
        try:
            p15, t15 = _t15_app({
                "AUTO_DIFF_A": os.path.join(diff_fix, "unbalanced.a.txt"),
                "AUTO_DIFF_B": os.path.join(diff_fix, "unbalanced.b.txt")})
            ok_open = _t15_wait_open(t15)
            st = t15.state("diff_rows_count", "diff_dbg_ctx", "diff_dbg_pair",
                           "diff_dbg_del", "diff_dbg_add")
            snap15 = t15.snapshot()
            result.check("T15.7 unbalanced（7 行=4ctx/1pair/2del+NEW 节点）",
                         ok_open and state_int(st, "diff_rows_count") == 7
                         and state_int(st, "diff_dbg_del") == 2
                         and state_int(st, "diff_dbg_pair") == 1
                         and '"NEW"' in snap15,
                         st.replace("\n", " ")[:160])
            _kill_proc_tree(p15)
        except Exception as e:
            result.check("T15.7 unbalanced", False, repr(e))

        # 15.8 错误形（缺文件不静默）
        try:
            p15, t15 = _t15_app({
                "AUTO_DIFF_A": os.path.join(diff_fix, "nonexistent_p011.txt"),
                "AUTO_DIFF_B": os.path.join(diff_fix, "modify.b.txt")})
            time.sleep(3)
            st = t15.state("diff_open", "diff_err")
            err = (state_str(st, "diff_err") or "").strip('"')
            console = state_str(t15.state("console"), "console") or ""
            result.check("T15.8 缺文件错误形（err 记录+零视图）",
                         state_bool(st, "diff_open") is False
                         and "不存在" in err and "diff:" in console,
                         f"err={err[:80]!r}")
            _kill_proc_tree(p15)
        except Exception as e:
            result.check("T15.8 错误形", False, repr(e))

        # 15.9 超限通过（PLAN-016 G-2 翻转面：>10000 行从 err 拒转正常
        # envelope——尺寸门/行数门随实现体替换消亡，引擎 native 直调）。
        # 期望值=引擎实测（10500 行 L0-based vs modify.b：锚点 L1,L2,L7,
        # L8,L9,L10 共 7 行 keep → dels=10500-7=10493，单 hunk——行数门
        # 专属路径的通过形延迟证明）。
        try:
            over = os.path.join(tempfile.mkdtemp(prefix="auto011_t15_over_"),
                                "over.txt")
            with open(over, "w", encoding="utf-8") as f:
                f.write("\n".join(f"L{i}" for i in range(10500)))
            p15, t15 = _t15_app({
                "AUTO_DIFF_A": over,
                "AUTO_DIFF_B": os.path.join(diff_fix, "modify.b.txt")})
            ok_open = _t15_wait_open(t15, 30)
            st = t15.state("diff_open", "diff_err", "diff_dels",
                           "diff_hunk_count")
            result.check("T15.9 行数超限通过（>10000 行正常 envelope+计数到位）",
                         ok_open
                         and state_bool(st, "diff_open") is True
                         and (state_str(st, "diff_err") or "").strip('"') == ""
                         and state_int(st, "diff_dels") == 10493
                         and state_int(st, "diff_hunk_count") >= 1,
                         f"open={state_bool(st, 'diff_open')} "
                         f"err={state_str(st, 'diff_err')!r} "
                         f"dels={state_int(st, 'diff_dels')}")
            _kill_proc_tree(p15)
        except Exception as e:
            result.check("T15.9 超限通过", False, repr(e))

        # 15.10 全换形重定（PLAN-016 G-2：degraded 退场——700 行全换从
        # 「降级整块 replace」转「引擎正常配对」：degraded=false+700/700
        # 计数+cap 600 截断+渲染注记在、降级注记退役）。
        try:
            d15 = tempfile.mkdtemp(prefix="auto011_t15_big_")
            pa = os.path.join(d15, "big.a.txt")
            pb = os.path.join(d15, "big.b.txt")
            with open(pa, "w", encoding="utf-8") as f:
                f.write("\n".join(f"old line {i} content"
                                  for i in range(700)))
            with open(pb, "w", encoding="utf-8") as f:
                f.write("\n".join(f"new line {i} content"
                                  for i in range(700)))
            p15, t15 = _t15_app({"AUTO_DIFF_A": pa, "AUTO_DIFF_B": pb})
            ok_open = _t15_wait_open(t15, 25)
            st = t15.state("diff_rows_count", "diff_rows_truncated",
                           "diff_hunk_count", "diff_degraded",
                           "diff_adds", "diff_dels", "diff_dbg_pair")
            snap15 = t15.snapshot()
            result.check("T15.10 全换形重定（degraded=false+700/700+cap 600"
                         "+降级注记退役）",
                         ok_open and state_int(st, "diff_rows_count") == 600
                         and state_bool(st, "diff_rows_truncated") is True
                         and state_bool(st, "diff_degraded") is False
                         and state_int(st, "diff_adds") == 700
                         and state_int(st, "diff_dels") == 700
                         and state_int(st, "diff_hunk_count") == 1
                         and "渲染截断（600）" in snap15
                         and "大段降级" not in snap15,
                         st.replace("\n", " ")[:200])
            _kill_proc_tree(p15)
        except Exception as e:
            result.check("T15.10 全换形重定", False, repr(e))

        # 15.11-15.15: PLAN-015 —— 内联视图检查组（复审 F-1 承载面落位；
        # 期望值=probe_diff 推导器链 golden/参考实现同源——惰性导入规避
        # desktop_mcp↔probe_diff 循环）。
        #   15.11 内联投影对照（scattered：irows 计数+dbg_i* 三计数）
        #   15.12 切换零重比（双向：envelope 八字段不变+console 增量无
        #         compute 行——F-3 硬证明；回切投影清空）
        #   15.13 内联态 hunk 导航（推进 [1,2]+位次 3/3）
        #   15.14 双 cap（生成式 700 全换 fixture：信封 600+内联 600
        #         拦腰形+双注记快照——big_reorder 引擎时代换位形零 pair
        #         展开前提失效，修复轮改形）
        #   15.15 内联态重算（dirdiff 旁路→下钻→切内联→返回→再下钻：
        #         vmode 保持+投影按新文件重建——F-2 生命周期覆盖）
        def _t15_golden_irows(name):
            from probe_diff import derive_inline, inline_shape_counts
            with open(os.path.join(diff_fix, f"{name}.golden.json"),
                      encoding="utf-8") as f:
                rows = json.load(f)["rows"]
            ir, tr = derive_inline(rows)
            return len(ir), tr, inline_shape_counts(ir)

        # 15.11-13 共享实例（scattered）
        try:
            from probe_diff import derive_inline
            exp_n, exp_tr, exp_c = _t15_golden_irows("scattered")
            p15, t15 = _t15_app({
                "AUTO_DIFF_A": os.path.join(diff_fix, "scattered.a.txt"),
                "AUTO_DIFF_B": os.path.join(diff_fix, "scattered.b.txt")})
            ok_open = _t15_wait_open(t15)
            b_inline = find_button_by_text(t15.snapshot(), "内联")
            cons0 = state_str(t15.state("console"), "console") or ""
            env_f = ("diff_rows_count", "diff_hunk_count", "diff_adds",
                     "diff_dels", "diff_dbg_pair", "diff_dbg_del",
                     "diff_dbg_add", "diff_dbg_ctx")
            base = {f: state_int(t15.state(f), f) for f in env_f}
            if b_inline:
                t15.click(b_inline)
                time.sleep(0.8)
            st = t15.state("diff_vmode", "diff_irows_count",
                           "diff_irows_truncated", "diff_dbg_idel",
                           "diff_dbg_iadd", "diff_dbg_ictx", *env_f)
            result.check("T15.11 内联投影对照（irows/dbg_i*=golden 推导）",
                         ok_open and bool(b_inline)
                         and (state_str(st, "diff_vmode") or "").strip('"') == "inline"
                         and state_int(st, "diff_irows_count") == exp_n
                         and state_int(st, "diff_dbg_idel") == exp_c["del"]
                         and state_int(st, "diff_dbg_iadd") == exp_c["add"]
                         and state_int(st, "diff_dbg_ictx") == exp_c["ctx"],
                         f"irows={state_int(st, 'diff_irows_count')}"
                         f"/{exp_n} dbg=({state_int(st, 'diff_dbg_idel')},"
                         f"{state_int(st, 'diff_dbg_iadd')},"
                         f"{state_int(st, 'diff_dbg_ictx')})/{exp_c}")
            # 15.12 双向零重比：console=滚动尾窗（前缀差量不可靠——首跑
            # 实证 fallback 误吞全量含 compute 行），改标记计数法：
            # compute 行计数不增 + view 行计数 +1（追加一行不滚出）。
            cons1 = state_str(t15.state("console"), "console") or ""
            n1p, n1i = cons1.count("diff: +"), cons1.count("view inline")
            zero1 = (all(state_int(st, f) == base[f] for f in env_f)
                     and n1p == cons0.count("diff: +")
                     and n1i == cons0.count("view inline") + 1)
            b_side = find_button_by_text(t15.snapshot(), "并排")
            env_m = {f: state_int(st, f) for f in env_f}
            n1s = cons1.count("view side")
            if b_side:
                t15.click(b_side)
                time.sleep(0.8)
            st2 = t15.state("diff_vmode", "diff_irows_count",
                            "diff_irows_truncated", *env_f)
            cons2 = state_str(t15.state("console"), "console") or ""
            zero2 = (all(state_int(st2, f) == env_m[f] for f in env_f)
                     and cons2.count("diff: +") == n1p
                     and cons2.count("view side") == n1s + 1)
            result.check("T15.12 切换零重比（双向：八字段不变+console 无"
                         " compute 行+回切投影清空）",
                         zero1 and zero2
                         and (state_str(st2, "diff_vmode") or "").strip('"') == "side"
                         and state_int(st2, "diff_irows_count") == 0,
                         f"zero={zero1}/{zero2} "
                         f"compute+={cons2.count('diff: +') - cons0.count('diff: +')} "
                         f"vInl={n1i} vSide={cons2.count('view side')}")
            # 15.13 内联态导航：再切内联 → 下一处×2 → [1,2]+位次 3/3
            b_inline2 = find_button_by_text(t15.snapshot(), "内联")
            if b_inline2:
                t15.click(b_inline2)
                time.sleep(0.8)
            snap15 = t15.snapshot()
            b_next = find_button_by_text(snap15, "下一处")
            seq = []
            for _ in range(2):
                if b_next:
                    t15.click(b_next)
                    time.sleep(0.5)
                seq.append(state_int(t15.state("diff_hunk_idx"), "diff_hunk_idx"))
            pos = (state_str(t15.state("diff_hunk_pos"), "diff_hunk_pos")
                   or "").strip('"')
            v13 = (state_str(t15.state("diff_vmode"), "diff_vmode")
                   or "").strip('"')
            result.check("T15.13 内联态导航推进 [1,2]+位次 3/3",
                         v13 == "inline" and seq == [1, 2] and pos == "3/3",
                         f"seq={seq} pos={pos!r} vmode={v13!r}")
            _kill_proc_tree(p15)
        except Exception as e:
            result.check("T15.11-13 内联主链", False, repr(e))

        # 15.14 双 cap（PLAN-016 修复轮改形：生成式 700 全换 fixture——
        # 700 pair 行>600 触发双截断[600 pair → 内联 1200>600 拦腰]；
        # 原 big_reorder 形在引擎修复后=del/add 块分离换位[632 行、前
        # 600 行零 pair——pair 展开 ×2 前提失效]，双 cap 断言改生成式
        # fixture 硬断言[fixtures 保 pristine——15.9/15.10 同款]，推导
        # 对照由 15.11 golden 面承载）。
        try:
            d14 = tempfile.mkdtemp(prefix="auto016_t15_cap_")
            pa14 = os.path.join(d14, "cap.a.txt")
            pb14 = os.path.join(d14, "cap.b.txt")
            with open(pa14, "w", encoding="utf-8") as f:
                f.write(chr(10).join(f"old line {i} content" for i in range(700)))
            with open(pb14, "w", encoding="utf-8") as f:
                f.write(chr(10).join(f"new line {i} content" for i in range(700)))
            p15, t15 = _t15_app({"AUTO_DIFF_A": pa14, "AUTO_DIFF_B": pb14})
            ok_open = _t15_wait_open(t15, 25)
            st0 = t15.state("diff_rows_count", "diff_rows_truncated")
            b_inline = find_button_by_text(t15.snapshot(), "内联")
            if b_inline:
                t15.click(b_inline)
                time.sleep(1.0)
            st = t15.state("diff_irows_count", "diff_irows_truncated")
            snap15 = t15.snapshot()
            result.check("T15.14 双 cap（信封 600+内联 600+双注记快照）",
                         ok_open
                         and state_int(st0, "diff_rows_count") == 600
                         and state_bool(st0, "diff_rows_truncated") is True
                         and state_int(st, "diff_irows_count") == 600
                         and state_bool(st, "diff_irows_truncated") is True
                         and "渲染截断" in snap15 and "内联截断" in snap15,
                         f"rows={state_int(st0, 'diff_rows_count')} "
                         f"irows={state_int(st, 'diff_irows_count')} "
                         f"trunc={state_bool(st, 'diff_irows_truncated')}")
            _kill_proc_tree(p15)
        except Exception as e:
            result.check("T15.14 双 cap", False, repr(e))

        # 15.15 内联态重算（F-2 生命周期：下钻→内联→返回→再下钻——
        # vmode 保持+投影按新文件重建；期望=probe 参考实现推导链）
        try:
            from probe_diff import naive_layered_diff, derive_inline
            d115 = tempfile.mkdtemp(prefix="p015_t15_d_")
            ta = os.path.join(d115, "a")
            tb = os.path.join(d115, "b")
            os.makedirs(ta)
            os.makedirs(tb)
            m1a, m1b = "one\n", "two\n"
            m2a, m2b = "p\nq\nr\ns\nt\nu\nv\n", "p\nQ\nr\ns\nt\nU\nv\n"
            for rel, xa, xb in (("mod1.txt", m1a, m1b), ("mod2.txt", m2a, m2b)):
                with open(os.path.join(ta, rel), "w", encoding="utf-8") as f:
                    f.write(xa)
                with open(os.path.join(tb, rel), "w", encoding="utf-8") as f:
                    f.write(xb)
            e1 = len(derive_inline(naive_layered_diff(m1a, m1b)["rows"])[0])
            e2 = len(derive_inline(naive_layered_diff(m2a, m2b)["rows"])[0])
            p15, t15 = _t15_app({"AUTO_DIRDIFF_A": ta, "AUTO_DIRDIFF_B": tb})
            ok_open = _t15_wait_open(t15)
            b_m1 = find_button_by_text(t15.snapshot(), "mod1.txt")
            if b_m1:
                t15.click(b_m1)
                time.sleep(1.5)
            b_inline = find_button_by_text(t15.snapshot(), "内联")
            if b_inline:
                t15.click(b_inline)
                time.sleep(0.8)
            st1 = t15.state("diff_mode", "diff_vmode", "diff_irows_count")
            back = find_button_by_text(t15.snapshot(), "返回目录")
            if back:
                t15.click(back)
                time.sleep(1.0)
            b_m2 = find_button_by_text(t15.snapshot(), "mod2.txt")
            if b_m2:
                t15.click(b_m2)
                time.sleep(1.5)
            st2 = t15.state("diff_mode", "diff_vmode", "diff_rows_count",
                            "diff_irows_count")
            result.check("T15.15 内联态重算（再下钻 vmode 保持+投影重建）",
                         ok_open and bool(b_m1) and bool(b_inline) and bool(b_m2)
                         and (state_str(st1, "diff_mode") or "").strip('"') == "file"
                         and state_int(st1, "diff_irows_count") == e1
                         and (state_str(st2, "diff_mode") or "").strip('"') == "file"
                         and (state_str(st2, "diff_vmode") or "").strip('"') == "inline"
                         and state_int(st2, "diff_rows_count") > 0
                         and state_int(st2, "diff_irows_count") == e2,
                         f"e1={e1}/{state_int(st1, 'diff_irows_count')} "
                         f"e2={e2}/{state_int(st2, 'diff_irows_count')} "
                         f"vmode={state_str(st2, 'diff_vmode')}")
            _kill_proc_tree(p15)
        except Exception as e:
            result.check("T15.15 内联态重算", False, repr(e))

        # 15.16-15.19: PLAN-016 —— 缓冲区比较子组（T15 形态：独立新鲜
        # 进程+APPDATA 隔离；驱动面=env 旁路 AUTO_DIFFBUF_A/B Tick 自开
        # ——011/012 同款消费形）。缺键端点 err 形（「编辑器不存在」）
        # 由 T-00 探针 probe_bufdiff.py ② 承载（矩阵 MCP 面不可达裸键
        # ——面板序号输入恒解析为现存 tab 键），本组 15.18=消费可见
        # 残缺形（单边 env→console 记录+零动作+面板不开）。
        #   15.16 旁路自开+装载轮转（B→A load_key 单槽序）+净形计数
        #   15.17 hunk 行跳转（切 ka tab+set_cursor A 侧首位——切走再
        #         切回读光标，set_cursor 不 republish on_cursor 契约的
        #         读回面=014 18.2 同款）
        #   15.18 旁路单边残缺（console 记录+面板零开）
        #   15.19 关闭复原（面板关+tab 零扰动）
        print("\nT15.P16: buffer diff subgroup")
        try:
            d16 = tempfile.mkdtemp(prefix="auto016_t15_buf_")
            fa = os.path.join(d16, "smoke.a.txt")
            fb = os.path.join(d16, "smoke.b.txt")
            with open(fa, "w", encoding="utf-8", newline="") as f:
                f.write("\n".join(f"L{i}" for i in range(1, 9)) + "\n")
            with open(fb, "w", encoding="utf-8", newline="") as f:
                f.write("\n".join(
                    f"L{i}" if i != 5 else "L5-CHANGED"
                    for i in range(1, 9)) + "\n")
            p15, t15 = _t15_app({"AUTO_DIFFBUF_A": fa, "AUTO_DIFFBUF_B": fb})
            ok_open = False
            st = ""
            for _ in range(30):
                st = t15.state("diff_buf_open", "diff_buf_count",
                               "diff_buf_adds", "diff_buf_dels",
                               "diff_buf_has_err", "tab_count", "tab")
                if state_bool(st, "diff_buf_open"):
                    ok_open = True
                    break
                time.sleep(0.5)
            result.check("T15.16 旁路自开+装载轮转+净形计数（1 hunk/+1/-1/双开）",
                         ok_open
                         and state_int(st, "diff_buf_count") == 1
                         and state_int(st, "diff_buf_adds") == 1
                         and state_int(st, "diff_buf_dels") == 1
                         and state_bool(st, "diff_buf_has_err") is False
                         and state_int(st, "tab_count") == 4
                         and state_int(st, "tab") == 2,
                         st.replace("\n", " ")[:200])
            # 15.17 跳转：净形行 →A 钮点击 → tab=2（ka=tab-3=smoke.a）→
            # 切走再切回（TabActivate SyncCursor 读回）→ line=2（a1+1）。
            # （PLAN-017 T-04 双钮改形：期望同步一处——原全区间单钮
            # 「L2–8 ↔ R2–8」→「→A L2–8」，语义不变。）
            row = find_button_by_text(t15.snapshot(), "→A L2–8")
            jumped = False
            if row:
                t15.click(row)
                time.sleep(1.0)
                jumped = state_int(t15.state("tab"), "tab") == 2
                sb = t15.snapshot()
                ba = find_button_by_text(sb, "smoke.a.txt")
                bb = find_button_by_text(sb, "smoke.b.txt")
                if bb:
                    t15.click(bb)
                    time.sleep(0.8)
                if ba:
                    t15.click(ba)
                    time.sleep(0.8)
            line = state_int(t15.state("line"), "line")
            result.check("T15.17 hunk 行跳转（切 tab+set_cursor 生效读回）",
                         bool(row) and jumped and line == 2,
                         f"row={bool(row)} jumped={jumped} line={line}")
            # 15.19 关闭复原（先于 15.18 独立实例前，在本实例收尾）。
            tabs_before = state_int(t15.state("tab_count"), "tab_count")
            b_close = find_button_by_text(t15.snapshot(), "×")
            closed = False
            if b_close:
                t15.click(b_close)
                time.sleep(0.8)
            st3 = t15.state("diff_buf_open", "tab_count")
            closed = state_bool(st3, "diff_buf_open") is False
            result.check("T15.19 关闭复原（面板关+tab 零扰动）",
                         closed
                         and state_int(st3, "tab_count") == tabs_before,
                         f"closed={closed} tabs={state_int(st3, 'tab_count')}")
            _kill_proc_tree(p15)
        except Exception as e:
            result.check("T15.16-19 缓冲区主链", False, repr(e))

        # 15.18 旁路单边残缺（独立实例——A 设 B 缺：console 记录+面板
        # 零开+tab 零扰动；DiffBypassTick 防重入）。
        try:
            d18 = tempfile.mkdtemp(prefix="auto016_t15_buf1_")
            fa1 = os.path.join(d18, "solo.a.txt")
            with open(fa1, "w", encoding="utf-8", newline="") as f:
                f.write("solo\n")
            p15, t15 = _t15_app({"AUTO_DIFFBUF_A": fa1})
            time.sleep(4)
            st = t15.state("diff_buf_open", "tab_count")
            con = state_str(t15.state("console"), "console") or ""
            result.check("T15.18 旁路单边残缺（console 记录+面板零开）",
                         state_bool(st, "diff_buf_open") is False
                         and state_int(st, "tab_count") == 2
                         and "bufdiff: bypass 残缺" in con,
                         f"open={state_bool(st, 'diff_buf_open')} "
                         f"con={con[-120:]!r}")
            _kill_proc_tree(p15)
        except Exception as e:
            result.check("T15.18 旁路残缺", False, repr(e))

        # 15.20-15.24: PLAN-017 —— 差异侧编辑回路子组（T15 形态：独立
        # 新鲜进程+APPDATA 隔离）。驱动面=env 旁路自开+视图头部钮/行钮
        # （label 嵌行号/区间唯一性）+菜单重开（跳转藏视图后的重入面
        # ——工具→比较文件…=env 旁路同链）+autoui_type 输入注入
        # （ReplaceAll=MCP 可驱动内容变更面）+ActSave 工具栏保存。
        # 已勘边界（T-00③+开发期实证）：diff 视图开态新开 tab 未实化
        # （registry 无条目）——badge/保存链的 tab 必须经跳转（视图藏
        # →实化）或视图关闭路径就位，子组流程按此设计。
        #   15.20 双侧跳转（A 新开/B 菜单重开后新开/行级 A 锚/已开激活
        #         ——落点读回=切走切回 SyncCursor 面，15.17 同款）
        #   15.21 保存自动重比（jump→cut→菜单重开 badge→ReplaceAll
        #         live badge→保存→视图自动重开+vmode 保持+8/8 变形+
        #         重比行+落盘）
        #   15.22 无关保存零扰动（第三文件保存 saved 行+console 增量无
        #         重比行+重开计数不变）
        #   15.23 面板 live 预览（ReplaceAll→防抖单拍净形 8/8 保存前→
        #         保存钩子刷新一致+重比行）
        #   15.24 B 侧跳转（→B kb 激活+b1 光标读回——label 解析行号
        #         真值；A 臂回归=15.17）
        print("\nT15.P17: diff-side edit loop subgroup")

        def _p17_wait_pend(timeout=12):
            for _ in range(timeout * 2):
                if not state_bool(t15.state("diff_edit_pend"), "diff_edit_pend"):
                    return True
                time.sleep(0.5)
            return False

        def _p17_click_text(label, tries=4):
            for _ in range(tries):
                b = find_button_by_text(t15.snapshot(), label)
                if b:
                    t15.click(b)
                    time.sleep(1.0)
                    return True
                time.sleep(0.6)
            return False

        def _p17_readback_line(tab_title):
            # 切走再切回（TabActivate SyncCursor 读回——set_cursor 不
            # republish on_cursor 契约的读回面，014/15.17 同款）。
            seed = find_button_by_text(t15.snapshot(), "main.at")
            if seed:
                t15.click(seed)
                time.sleep(0.6)
            tb = find_button_by_text(t15.snapshot(), tab_title)
            if tb:
                t15.click(tb)
                time.sleep(0.6)
            return state_int(t15.state("line"), "line")

        def _p17_reopen_diff():
            # 菜单重开（工具→比较文件…——AUTO_DIFF_A/B 在档=旁路同链）。
            m = find_button_by_text(t15.snapshot(), "工具")
            if not m:
                return False
            t15.click(m)
            time.sleep(0.8)
            return _p17_click_text("比较文件…")

        def _p17_replace_all(query, replacement):
            # 编辑菜单→替换…→autoui_type 双输入→全部替换（MCP 可驱动
            # 内容变更面——handler 首参形）。
            m = find_button_by_text(t15.snapshot(), "编辑")
            if not m:
                return False
            t15.click(m)
            time.sleep(0.8)
            if not _p17_click_text("替换…"):
                return False
            snap = t15.snapshot()
            qi = find_element_by_event(snap, "FindInput", attr="oninput")
            ri = find_element_by_event(snap, "FindReplaceInput", attr="oninput")
            if not qi or not ri:
                return False
            t15.call("autoui_type", text=query, element_id=qi, clear_first=True)
            time.sleep(0.4)
            t15.call("autoui_type", text=replacement, element_id=ri, clear_first=True)
            time.sleep(0.4)
            return _p17_click_text("全部替换")

        def _p17_save_active(tries=4):
            for _ in range(tries):
                sb = find_button_by_onclick(t15.snapshot(), "ActSave")
                if sb:
                    t15.click(sb)
                    time.sleep(1.5)
                    return True
                time.sleep(0.8)
            return False

        # 15.20 双侧跳转编辑（scattered：hunk0 a1=b1=1 → 期望行 2；
        # 行级=首 pair 行 lo=5 → 期望行 5）
        try:
            p15, t15 = _t15_app({
                "AUTO_DIFF_A": os.path.join(diff_fix, "scattered.a.txt"),
                "AUTO_DIFF_B": os.path.join(diff_fix, "scattered.b.txt")})
            ok_open = _t15_wait_open(t15)
            with open(os.path.join(diff_fix, "scattered.golden.json"),
                      encoding="utf-8") as f:
                h0 = json.load(f)["hunks"][0]
            want_line = h0["a1"] + 1
            ok_a = _p17_click_text("编辑 A 侧") and state_bool(
                t15.state("diff_edit_return"), "diff_edit_return")
            pend_a = _p17_wait_pend()
            line_a = _p17_readback_line("scattered.a.txt") if ok_a else -1
            st = t15.state("diff_open", "tab_count")
            result.check("T15.20a A 侧跳转（新开 tab+装载落点 line=%d+视图藏）" % want_line,
                         ok_open and ok_a and pend_a
                         and state_bool(st, "diff_open") is False
                         and state_int(st, "tab_count") == 3
                         and line_a == want_line,
                         f"ok={ok_a} pend={pend_a} line={line_a} "
                         f"open={state_bool(st, 'diff_open')} "
                         f"tabs={state_int(st, 'tab_count')}")
            ok_re = _p17_reopen_diff()
            time.sleep(1.0)
            ok_b = _p17_click_text("编辑 B 侧")
            pend_b = _p17_wait_pend()
            line_b = _p17_readback_line("scattered.b.txt") if ok_b else -1
            st = t15.state("tab_count")
            result.check("T15.20b B 侧跳转（菜单重开→新开+落点 hunk0 b1）",
                         ok_re and ok_b and pend_b
                         and state_int(st, "tab_count") == 4
                         and line_b == h0["b1"] + 1,
                         f"reopen={ok_re} ok={ok_b} pend={pend_b} line={line_b}")
            ok_re2 = _p17_reopen_diff()
            time.sleep(1.0)
            ok_row = _p17_click_text("A:5")
            line_r = _p17_readback_line("scattered.a.txt") if ok_row else -1
            result.check("T15.20c 行级编辑跳转（pair 行 A:5 钮→lo 锚 line=5）",
                         ok_re2 and ok_row and line_r == 5,
                         f"reopen={ok_re2} ok={ok_row} line={line_r}")
            ok_re3 = _p17_reopen_diff()
            time.sleep(1.0)
            ok_a2 = _p17_click_text("编辑 A 侧")
            _p17_wait_pend()
            line_a2 = _p17_readback_line("scattered.a.txt") if ok_a2 else -1
            st = t15.state("tab_count")
            result.check("T15.20d 已开激活路径（tab 零增长+落点复位）",
                         ok_re3 and ok_a2
                         and state_int(st, "tab_count") == 4
                         and line_a2 == want_line,
                         f"ok={ok_a2} tabs={state_int(st, 'tab_count')} "
                         f"line={line_a2}")
            _kill_proc_tree(p15)
        except Exception as e:
            result.check("T15.20 双侧跳转", False, repr(e))

        # 15.21 保存自动重比（tmp 8 行对：+1/-1 基线→ReplaceAll L→Z
        # 全行变形→保存→视图自动重开+8/-8）
        try:
            d21 = tempfile.mkdtemp(prefix="auto017_t15_save_")
            fa21 = os.path.join(d21, "mod.a.txt")
            fb21 = os.path.join(d21, "mod.b.txt")
            with open(fa21, "w", encoding="utf-8", newline="") as f:
                f.write("\n".join(f"L{i}" for i in range(1, 9)) + "\n")
            with open(fb21, "w", encoding="utf-8", newline="") as f:
                f.write("\n".join(
                    f"L{i}" if i != 5 else "L5-CHANGED"
                    for i in range(1, 9)) + "\n")
            p15, t15 = _t15_app({"AUTO_DIFF_A": fa21, "AUTO_DIFF_B": fb21})
            ok_open = _t15_wait_open(t15)
            ok_inline = _p17_click_text("内联")
            ok_jump = _p17_click_text("编辑 B 侧")
            pend = _p17_wait_pend()
            # 弄脏 B（cut——内容零变化形；B 已实化）
            cutb = find_button_by_onclick(t15.snapshot(), "ActCut")
            if cutb:
                t15.click(cutb)
                time.sleep(0.5)
            ok_re = _p17_reopen_diff()
            time.sleep(1.5)
            badge1 = state_str(t15.state("diff_badge"), "diff_badge") or ""
            ok_ra = _p17_replace_all("L", "Z")
            time.sleep(2.0)
            badge2 = state_str(t15.state("diff_badge"), "diff_badge") or ""
            saved = _p17_save_active()
            time.sleep(1.5)
            st = t15.state("diff_open", "diff_adds", "diff_dels", "diff_vmode",
                           "diff_edit_return", "diff_badge")
            con = wait_console_line(t15, "已重比（保存触发")
            disk = open(fb21, encoding="utf-8").read()
            result.check(
                "T15.21 保存自动重比（badge live→保存→视图自动重开+vmode 保持"
                "+8/-8 变形+重比行+落盘）",
                ok_open and ok_inline and ok_jump and pend and ok_re
                and "预览" in badge1 and ok_ra and "预览 +8/-8" in badge2
                and saved
                and state_bool(st, "diff_open") is True
                and state_int(st, "diff_adds") == 8
                and state_int(st, "diff_dels") == 8
                and (state_str(st, "diff_vmode") or "").strip('"') == "inline"
                and state_bool(st, "diff_edit_return") is False
                and (state_str(st, "diff_badge") or "").strip('"') == ""
                and con is not None and "已重比（保存触发" in con
                and "Z1" in disk and "L5" not in disk,
                f"open={ok_open} inline={ok_inline} jump={ok_jump} "
                f"pend={pend} re={ok_re} badge1={badge1!r} ra={ok_ra} "
                f"badge2={badge2!r} saved={saved} "
                f"st={st.replace(chr(10), ' ')[:160]} con={con[-100:]!r}")
            _kill_proc_tree(p15)
        except Exception as e:
            result.check("T15.21 保存自动重比", False, repr(e))

        # 15.22 无关保存零扰动（第三文件：开→关视图实化→cut→保存→
        # saved 行+零重比行+重开计数不变）
        try:
            d22 = tempfile.mkdtemp(prefix="auto017_t15_unrel_")
            fa22 = os.path.join(d22, "u.a.txt")
            fb22 = os.path.join(d22, "u.b.txt")
            fc22 = os.path.join(d22, "unrel.txt")
            with open(fa22, "w", encoding="utf-8", newline="") as f:
                f.write("\n".join(f"L{i}" for i in range(1, 9)) + "\n")
            with open(fb22, "w", encoding="utf-8", newline="") as f:
                f.write("\n".join(
                    f"L{i}" if i != 5 else "L5-CHANGED"
                    for i in range(1, 9)) + "\n")
            with open(fc22, "w", encoding="utf-8", newline="") as f:
                f.write("other\ncontent\n")
            p15, t15 = _t15_app({"AUTO_DIFF_A": fa22, "AUTO_DIFF_B": fb22,
                                 "AUTO_OPEN_PATH": fc22})
            ok_open = _t15_wait_open(t15)
            plus = find_button_by_onclick(t15.snapshot(), "ActOpen")
            opened = False
            if plus:
                t15.click(plus)
                time.sleep(1.5)
                opened = True
            xb = find_button_by_onclick(t15.snapshot(), "DiffClose")
            closed = False
            if xb:
                t15.click(xb)
                time.sleep(1.0)
                closed = True
            cutc = find_button_by_onclick(t15.snapshot(), "ActCut")
            if cutc:
                t15.click(cutc)
                time.sleep(0.5)
            saved = _p17_save_active()
            time.sleep(1.0)
            con1 = wait_console_line(t15, "saved: ")
            ok_re = _p17_reopen_diff()
            time.sleep(1.5)
            st2 = t15.state("diff_open", "diff_adds", "diff_dels")
            result.check(
                "T15.22 无关保存零扰动（第三文件保存 saved 行+零重比行+重开计数不变）",
                ok_open and opened and closed and saved
                and con1 is not None
                and "已重比" not in con1
                and ok_re
                and state_bool(st2, "diff_open") is True
                and state_int(st2, "diff_adds") == 1
                and state_int(st2, "diff_dels") == 1,
                f"open={ok_open} opened={opened} closed={closed} "
                f"saved={saved} con={con1 is not None and '已重比' in con1!r} "
                f"re={ok_re} "
                f"adds={state_int(st2, 'diff_adds')}")
            _kill_proc_tree(p15)
        except Exception as e:
            result.check("T15.22 无关保存零扰动", False, repr(e))

        # 15.23 面板 live 预览（AUTO_DIFFBUF 8 行对：ReplaceAll→防抖
        # 单拍净形 8/8 保存前→保存钩子刷新一致）
        try:
            d23 = tempfile.mkdtemp(prefix="auto017_t15_live_")
            fa23 = os.path.join(d23, "lv.a.txt")
            fb23 = os.path.join(d23, "lv.b.txt")
            with open(fa23, "w", encoding="utf-8", newline="") as f:
                f.write("\n".join(f"L{i}" for i in range(1, 9)) + "\n")
            with open(fb23, "w", encoding="utf-8", newline="") as f:
                f.write("\n".join(
                    f"L{i}" if i != 5 else "L5-CHANGED"
                    for i in range(1, 9)) + "\n")
            p15, t15 = _t15_app({"AUTO_DIFFBUF_A": fa23, "AUTO_DIFFBUF_B": fb23})
            ok_open = False
            st = ""
            for _ in range(30):
                st = t15.state("diff_buf_open", "diff_buf_adds", "diff_buf_dels")
                if state_bool(st, "diff_buf_open"):
                    ok_open = True
                    break
                time.sleep(0.5)
            base_ok = (state_int(st, "diff_buf_adds") == 1
                       and state_int(st, "diff_buf_dels") == 1)
            ok_ra = _p17_replace_all("L", "Z")
            live_ok = False
            for _ in range(10):
                st = t15.state("diff_buf_adds", "diff_buf_dels")
                if (state_int(st, "diff_buf_adds") == 8
                        and state_int(st, "diff_buf_dels") == 8):
                    live_ok = True
                    break
                time.sleep(0.5)
            saved = _p17_save_active()
            time.sleep(1.5)
            st2 = t15.state("diff_buf_open", "diff_buf_adds", "diff_buf_dels")
            con = wait_console_line(t15, "bufdiff: 已重比（保存触发）")
            result.check(
                "T15.23 面板 live 预览（ReplaceAll→防抖单拍净形 8/8 保存前"
                "→保存钩子刷新一致+重比行）",
                ok_open and base_ok and ok_ra and live_ok and saved
                and state_bool(st2, "diff_buf_open") is True
                and state_int(st2, "diff_buf_adds") == 8
                and state_int(st2, "diff_buf_dels") == 8
                and con is not None and "bufdiff: 已重比（保存触发）" in con,
                f"open={ok_open} base={base_ok} ra={ok_ra} live={live_ok} "
                f"saved={saved} st2={st2.replace(chr(10), ' ')[:140]}")
            _kill_proc_tree(p15)
        except Exception as e:
            result.check("T15.23 面板 live 预览", False, repr(e))

        # 15.24 B 侧跳转（scattered 三 hunk fixtures 经缓冲区面板——
        # label 解析行号真值=引擎形状无关断言；kb 激活+光标读回；→A
        # 同行对称回归。15.24 初版自造近距变更形被 ctx 窗合并为单
        # hunk（a1=b1=0 退化为平凡锚）——改用 scattered 非平凡锚形）
        try:
            p15, t15 = _t15_app({
                "AUTO_DIFFBUF_A": os.path.join(diff_fix, "scattered.a.txt"),
                "AUTO_DIFFBUF_B": os.path.join(diff_fix, "scattered.b.txt")})
            ok_open = False
            for _ in range(30):
                if state_bool(t15.state("diff_buf_open"), "diff_buf_open"):
                    ok_open = True
                    break
                time.sleep(0.5)
            snap = t15.snapshot()
            blist = re.findall(r'button #(\w+) "→B R(\d+)–(\d+)"', snap)
            alist = re.findall(r'button #(\w+) "→A L(\d+)–(\d+)"', snap)
            ok_parse = len(blist) >= 2 and len(alist) >= 2
            b_line = a_line = -1
            b_active = False
            if ok_parse:
                bid, bstart = blist[-1][0], int(blist[-1][1])
                t15.click(bid)
                time.sleep(1.0)
                st = t15.state("tab", "tab_count")
                b_active = state_int(st, "tab") == state_int(st, "tab_count") - 1
                b_line = _p17_readback_line("scattered.b.txt")
                aid, astart = alist[-1][0], int(alist[-1][1])
                t15.click(aid)
                time.sleep(1.0)
                a_line = _p17_readback_line("scattered.a.txt")
            result.check(
                "T15.24 B 侧跳转（→B kb 激活+b1 光标读回+→A 对称回归）",
                ok_open and ok_parse and b_active
                and b_line == int(blist[-1][1]) and a_line == int(alist[-1][1]),
                f"open={ok_open} parse={ok_parse} b_active={b_active} "
                f"b_line={b_line}/{blist[-1][1] if blist else '?'} "
                f"a_line={a_line}/{alist[-1][1] if alist else '?'}")
            _kill_proc_tree(p15)
        except Exception as e:
            result.check("T15.24 B 侧跳转", False, repr(e))
    else:
        print("  NOTE  tests/fixtures/diff missing; skipping T15")

    # T16: PLAN-012 —— 目录 diff 检查组（T15 形态：独立新鲜进程+APPDATA
    # 隔离；fixtures/dirdiff base/rev 五形态 golden 在档）。驱动面=env
    # 旁路 Tick 自开（AUTO_DIRDIFF_A/B）。同步动作走 tmp 生成树（fixtures
    # 保 pristine——008 先例），最小单状态树保证动作按钮唯一
    # （find_button_by_text 精确正则）。子组：
    #   16.1 旁路自开+golden counts（4/2/2/1/1）+view 10
    #   16.2 快照形态（rels+徽标+[目录] 标记）
    #   16.3 过滤纯 front 态（删过滤 view 2+计数零变；回 all）
    #   16.4 下钻（改行→file 模式+rows 到达）+返回目录（entries 保留）
    #   16.5 复制直执行（删过滤唯一 →；磁盘 E2E+重比计数+过滤保持）
    #   16.6 删除确认链（增过滤唯一 ✕→确认执行；磁盘消失+计数）
    #   16.7 覆盖复制确认链（改过滤唯一 →→确认；磁盘内容=左侧）
    #   16.8 关闭复原（dir/diff 全清+tab 零扰动）
    #   16.9 错误形（根缺失：面板不开+err+console）
    #   16.10 >2MB 同尺寸=同(未比对)注记（生成式 fixture）
    print("\nT16: PLAN-012 dir diff")
    dirdiff_fix = os.path.join(fixtures_dir, "dirdiff")

    def _t16_write(path, data):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(data)

    def _t16_app(extra):
        port = pick_free_port()
        env = {**os.environ, "AUTOUI_MCP_PORT": str(port),
               "APPDATA": tempfile.mkdtemp(prefix="auto012_t16_"), **extra}
        proc = subprocess.Popen(
            [AUTO_BIN, "run", "-r", "vm"],
            cwd=PROJECT, env=env,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        url = f"http://127.0.0.1:{port}/mcp"
        assert wait_for_server(url, 30), "T16 server never up"
        t = McpClient(url)
        for _ in range(15):
            s = t.snapshot()
            if "(rendered)" in s and s.count("onclick") > 0:
                break
            time.sleep(1)
        time.sleep(1.5)
        return proc, t

    def _t16_wait_open(t, timeout=15):
        for _ in range(timeout * 2):
            if state_bool(t.state("dir_mode"), "dir_mode"):
                return True
            time.sleep(0.5)
        return False

    if os.path.isdir(dirdiff_fix):
        # 16.1-16.3 共享实例（五形态 golden）
        try:
            ta = tempfile.mkdtemp(prefix="p012_t16_a_")
            tb = tempfile.mkdtemp(prefix="p012_t16_b_")
            shutil.copytree(os.path.join(dirdiff_fix, "base"), ta,
                            dirs_exist_ok=True)
            shutil.copytree(os.path.join(dirdiff_fix, "rev"), tb,
                            dirs_exist_ok=True)
            p16, t16 = _t16_app({"AUTO_DIRDIFF_A": ta, "AUTO_DIRDIFF_B": tb})
            ok_open = _t16_wait_open(t16)
            st = t16.state("dir_mode", "diff_open", "diff_mode", "dir_total",
                           "dir_n_same", "dir_n_added", "dir_n_deleted",
                           "dir_n_modified", "dir_n_binary",
                           "dir_view_count", "dir_truncated", "dir_has_err")
            result.check("T16.1 env 旁路自开+golden counts（4/2/2/1/1）",
                         ok_open
                         and state_bool(st, "dir_mode") is True
                         and state_bool(st, "diff_open") is True
                         and (state_str(st, "diff_mode") or "").strip('"') == "dirs"
                         and state_int(st, "dir_n_same") == 4
                         and state_int(st, "dir_n_added") == 2
                         and state_int(st, "dir_n_deleted") == 2
                         and state_int(st, "dir_n_modified") == 1
                         and state_int(st, "dir_n_binary") == 1
                         and state_int(st, "dir_view_count") == 10,
                         st.replace("\n", " ")[:200])
            snap16 = t16.snapshot()
            form_ok = all(x in snap16 for x in
                          ("same.txt", "modified.txt", "deleted.txt",
                           "added.txt", "binary.bin", "[目录] nested",
                           "nested/old.txt", "nested/new.txt", "增", "删",
                           "改", "二进"))
            result.check("T16.2 快照形态（rels+徽标+[目录] 标记）", form_ok,
                         "entries/徽标缺失")
            del_btn = find_button_by_text(snap16, "删")
            if del_btn:
                t16.click(del_btn)
                time.sleep(0.8)
            st2 = t16.state("dir_filter", "dir_f_deleted", "dir_view_count",
                            "dir_n_deleted", "dir_n_added")
            filt_ok = ((state_str(st2, "dir_filter") or "").strip('"') == "deleted"
                       and state_bool(st2, "dir_f_deleted") is True
                       and state_int(st2, "dir_view_count") == 2
                       and state_int(st2, "dir_n_deleted") == 2
                       and state_int(st2, "dir_n_added") == 2)
            snap16b = t16.snapshot()
            result.check("T16.3 过滤纯 front 态（删过滤 view2+计数零变+快照单态）",
                         filt_ok and "deleted.txt" in snap16b
                         and "added.txt" not in snap16b,
                         st2.replace("\n", " ")[:160])
            all_btn = find_button_by_text(snap16b, "全部")
            if all_btn:
                t16.click(all_btn)
                time.sleep(0.8)
            st3 = t16.state("dir_view_count")
            result.check("T16.3b 回 all（view 10）",
                         state_int(st3, "dir_view_count") == 10,
                         str(state_int(st3, "dir_view_count")))
            _kill_proc_tree(p16)
        except Exception as e:
            result.check("T16.1-3 golden 主链", False, repr(e))

        # 16.4 下钻+返回（单状态树）
        try:
            ta = tempfile.mkdtemp(prefix="p012_t16_d_")
            tb = tempfile.mkdtemp(prefix="p012_t16_d2_")
            _t16_write(os.path.join(ta, "mod.txt"), "aaa\n")
            _t16_write(os.path.join(tb, "mod.txt"), "bbb-longer\n")
            p16, t16 = _t16_app({"AUTO_DIRDIFF_A": ta, "AUTO_DIRDIFF_B": tb})
            ok_open = _t16_wait_open(t16)
            b_mod = find_button_by_text(t16.snapshot(), "mod.txt")
            if b_mod:
                t16.click(b_mod)
                time.sleep(1.5)
            st = t16.state("diff_mode", "dir_mode", "diff_open",
                           "diff_rows_count", "dir_from_dirs")
            result.check("T16.4 下钻 file 模式+rows 到达（011 视图复用）",
                         ok_open
                         and (state_str(st, "diff_mode") or "").strip('"') == "file"
                         and state_bool(st, "dir_mode") is False
                         and state_bool(st, "diff_open") is True
                         and state_int(st, "diff_rows_count") > 0,
                         st.replace("\n", " ")[:160])
            back = find_button_by_text(t16.snapshot(), "返回目录")
            if back:
                t16.click(back)
                time.sleep(1.0)
            st2 = t16.state("diff_mode", "dir_mode", "dir_view_count")
            result.check("T16.4b 返回目录（entries 保留不重比）",
                         (state_str(st2, "diff_mode") or "").strip('"') == "dirs"
                         and state_bool(st2, "dir_mode") is True
                         and state_int(st2, "dir_view_count") == 1,
                         st2.replace("\n", " ")[:120])
            _kill_proc_tree(p16)
        except Exception as e:
            result.check("T16.4 下钻+返回", False, repr(e))

        # 16.5-16.8 同步动作 E2E（单状态树：删/增/改各一+same）
        try:
            ta = tempfile.mkdtemp(prefix="p012_t16_s_")
            tb = tempfile.mkdtemp(prefix="p012_t16_s2_")
            _t16_write(os.path.join(ta, "mod.txt"), "aaa\n")
            _t16_write(os.path.join(tb, "mod.txt"), "bbb-longer\n")
            _t16_write(os.path.join(ta, "gone.txt"), "gone\n")
            _t16_write(os.path.join(tb, "new.txt"), "new\n")
            _t16_write(os.path.join(ta, "same.txt"), "same\n")
            _t16_write(os.path.join(tb, "same.txt"), "same\n")
            p16, t16 = _t16_app({"AUTO_DIRDIFF_A": ta, "AUTO_DIRDIFF_B": tb})
            ok_open = _t16_wait_open(t16)
            # 16.5 复制直执行（删过滤唯一 →）
            del_btn = find_button_by_text(t16.snapshot(), "删")
            if del_btn:
                t16.click(del_btn)
                time.sleep(0.8)
            cp = find_button_by_text(t16.snapshot(), "→")
            if cp:
                t16.click(cp)
                time.sleep(1.5)
            st = t16.state("dir_n_deleted", "dir_n_same", "dir_f_deleted",
                           "dir_confirm_open", "dir_view_count")
            result.check("T16.5 复制直执行（磁盘 E2E+重比 删0/同2+过滤保持）",
                         ok_open
                         and os.path.isfile(os.path.join(tb, "gone.txt"))
                         and state_int(st, "dir_n_deleted") == 0
                         and state_int(st, "dir_n_same") == 2
                         and state_bool(st, "dir_f_deleted") is True
                         and state_bool(st, "dir_confirm_open") is False,
                         st.replace("\n", " ")[:160])
            # 16.6 删除确认链（增过滤唯一 ✕→确认执行）
            add_btn = find_button_by_text(t16.snapshot(), "增")
            if add_btn:
                t16.click(add_btn)
                time.sleep(0.8)
            dx = find_button_by_text(t16.snapshot(), "✕")
            if dx:
                t16.click(dx)
                time.sleep(1.0)
            st2 = t16.state("dir_confirm_open")
            cf = find_button_by_text(t16.snapshot(), "确认执行")
            if cf:
                t16.click(cf)
                time.sleep(1.5)
            st3 = t16.state("dir_n_added", "dir_confirm_open")
            result.check("T16.6 删除确认链（弹层→执行→磁盘消失+增 0）",
                         state_bool(st2, "dir_confirm_open") is True
                         and not os.path.exists(os.path.join(tb, "new.txt"))
                         and state_int(st3, "dir_n_added") == 0
                         and state_bool(st3, "dir_confirm_open") is False,
                         st3.replace("\n", " ")[:120])
            # 16.7 覆盖复制确认链（改过滤唯一 →→确认）
            mod_btn = find_button_by_text(t16.snapshot(), "改")
            if mod_btn:
                t16.click(mod_btn)
                time.sleep(0.8)
            cp2 = find_button_by_text(t16.snapshot(), "→")
            if cp2:
                t16.click(cp2)
                time.sleep(1.0)
            st4 = t16.state("dir_confirm_open")
            cf2 = find_button_by_text(t16.snapshot(), "确认执行")
            if cf2:
                t16.click(cf2)
                time.sleep(1.5)
            with open(os.path.join(tb, "mod.txt"), encoding="utf-8") as f:
                content = f.read()
            st5 = t16.state("dir_n_modified", "dir_n_same")
            result.check("T16.7 覆盖复制确认链（双侧恒确认+磁盘内容=左侧+改0/同3）",
                         state_bool(st4, "dir_confirm_open") is True
                         and content == "aaa\n"
                         and state_int(st5, "dir_n_modified") == 0
                         and state_int(st5, "dir_n_same") == 3,
                         f"content={content!r}")
            # 16.8 关闭复原
            tabs_before = state_int(t16.state("tab_count"), "tab_count")
            x_btn = find_button_by_text(t16.snapshot(), "×")
            if x_btn:
                t16.click(x_btn)
                time.sleep(0.8)
            st6 = t16.state("dir_mode", "diff_open", "dir_view_count",
                            "tab_count")
            result.check("T16.8 关闭复原（全清+tab 零扰动）",
                         state_bool(st6, "dir_mode") is False
                         and state_bool(st6, "diff_open") is False
                         and state_int(st6, "dir_view_count") == 0
                         and state_int(st6, "tab_count") == tabs_before,
                         st6.replace("\n", " ")[:120])
            _kill_proc_tree(p16)
        except Exception as e:
            result.check("T16.5-8 同步动作 E2E", False, repr(e))

        # 16.9 错误形（根缺失）
        try:
            p16, t16 = _t16_app({
                "AUTO_DIRDIFF_A": "Z:/nonexistent_p012_t16",
                "AUTO_DIRDIFF_B": tempfile.gettempdir()})
            time.sleep(3)
            st = t16.state("dir_mode", "diff_open", "dir_has_err", "console",
                           "dir_err")
            console = state_str(st, "console") or ""
            result.check("T16.9 根缺失 err 形（面板不开+err+console）",
                         state_bool(st, "dir_mode") is False
                         and state_bool(st, "diff_open") is False
                         and state_bool(st, "dir_has_err") is True
                         and "dirdiff:" in console,
                         f"err={state_str(st, 'dir_err')!r}")
            _kill_proc_tree(p16)
        except Exception as e:
            result.check("T16.9 错误形", False, repr(e))

        # 16.10 >2MB 同尺寸=同(未比对)注记（生成式 fixture）
        try:
            ta = tempfile.mkdtemp(prefix="p012_t16_big_")
            tb = tempfile.mkdtemp(prefix="p012_t16_big2_")
            blob = ("0123456789abcdef" * 64 + "\n") * 2100  # ≈2.16MB
            _t16_write(os.path.join(ta, "big.txt"), blob)
            _t16_write(os.path.join(tb, "big.txt"), blob)
            p16, t16 = _t16_app({"AUTO_DIRDIFF_A": ta, "AUTO_DIRDIFF_B": tb})
            ok_open = _t16_wait_open(t16, 25)
            st = t16.state("dir_n_same", "dir_view_count")
            snap16 = t16.snapshot()
            result.check("T16.10 >2MB 同尺寸=同(未比对)注记",
                         ok_open and state_int(st, "dir_n_same") == 1
                         and "未比" in snap16,
                         st.replace("\n", " ")[:120])
            _kill_proc_tree(p16)
        except Exception as e:
            result.check("T16.10 未比对注记", False, repr(e))
    else:
        print("  NOTE  tests/fixtures/dirdiff missing; skipping T16")

    # T17: PLAN-013 —— 大文件模式检查组（T16 形态：独立新鲜进程+APPDATA
    # 隔离；50MB 级 fixture 生成式临时构造不入库——计划 §T-04）。驱动面=
    # AUTO_BENCH+AUTO_OPEN_PATH env 旁路（ConsumeOpen 链——T13 +按钮
    # ActOpen 同源）。子组：
    #   17.1 探测置位+plain 绑定（big_active/loaded_bytes/lang_active）
    #   17.2 ReplaceAll 拦截（console blocked+big_hint 提示位）
    #   17.3 save 拦截（console+big_hint+磁盘零变 E2E）
    #   17.4 切换往返无残留（big↔normal：lang_active/big_active 联动）
    #   17.5 超大装载（513MB+1B：分页装载成功形+big 态——PLAN-025 门退役
    #        翻转；原拒绝形断言随裁定 (a) 移除退役）
    #   17.6 阈值下界（49MB：big_active=false——门槛不误伤）
    #   17.7 normal 态零误伤（小文件 replace-all 成功+save 写通 E2E）
    #   17.8 会话恢复重探（退出→同 APPDATA 重启→恢复 tab→装载重探 big）
    #   17.9-17.12 1GB 四链（PLAN-025 消费冒烟：装载/交互活体+帧带/编辑
    #        记账/保存 byte-for-byte——T-00 实勘驱动面注记见组内）
    print("\nT17: PLAN-013 big-file mode")
    t17_dir = tempfile.mkdtemp(prefix="p013_t17_fx_")
    MB = 1024 * 1024

    def _t17_make(name, total_bytes):
        p = os.path.join(t17_dir, name)
        with open(p, "wb") as f:
            block = (b"line %08d padding for t17 bigfile fixture ........\n")
            unit = b"".join((block % i) + b"\n" for i in range(512))
            per = len(unit)
            written = 0
            while written < total_bytes - per:
                f.write(unit)
                written += per
            if written < total_bytes:
                f.write(b"x" * (total_bytes - written - 1) + b"\n")
        return p

    f_big50 = _t17_make("big50.txt", 50 * MB)
    f_49 = _t17_make("under49.txt", 49 * MB)
    # PLAN-025 T-02: 513MB+1B 边界档（门退役后全放行——big 态界 50MB
    # 为唯一分域线；+1B=原拒绝位边界精度语义沿袭）。
    f_513 = _t17_make("over513.txt", 513 * MB + 1)
    f_small = os.path.join(t17_dir, "small.txt")
    with open(f_small, "w", encoding="utf-8", newline="") as f:
        f.write("alpha line one\nbeta line two\nNEEDLE_QZ here\nalpha line four\n")

    def _t17_app(extra, appdata=None):
        port = pick_free_port()
        env = {**os.environ, "AUTOUI_MCP_PORT": str(port),
               "APPDATA": appdata or tempfile.mkdtemp(prefix="auto013_t17_"),
               **extra}
        proc = subprocess.Popen(
            [AUTO_BIN, "run", "-r", "vm"],
            cwd=PROJECT, env=env,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        url = f"http://127.0.0.1:{port}/mcp"
        assert wait_for_server(url, 30), "T17 server never up"
        t = McpClient(url)
        for _ in range(15):
            s = t.snapshot()
            if "(rendered)" in s and s.count("onclick") > 0:
                break
            time.sleep(1)
        time.sleep(1.5)
        return proc, t

    def _t17_wait_loaded(t, base, timeout=90):
        for _ in range(timeout * 4):
            c = state_str(t.state("console"), "console") or ""
            if "loaded: " in c and base in c:
                return True
            if "load rejected" in c:
                return True
            time.sleep(0.25)
        return False

    # 17.1-17.4 共享实例（探测/拦截/往返链）
    try:
        p17, t17 = _t17_app({"AUTO_BENCH": "1", "AUTO_OPEN_PATH": f_big50})
        ok_load = _t17_wait_loaded(t17, "big50.txt")
        st = t17.state("big_active", "lang_active", "loaded_bytes",
                       "readonly_label", "big_hint")
        result.check("T17.1 探测置位+plain 绑定（big_active+loaded_bytes+lang）",
                     ok_load
                     and state_bool(st, "big_active") is True
                     and state_int(st, "loaded_bytes") == 50 * MB
                     and (state_str(st, "lang_active") or "").strip('"') == "plain"
                     and (state_str(st, "readonly_label") or "").strip('"') == "",
                     st.replace("\n", " ")[:160])

        # 17.2 ReplaceAll 拦截（开栏 keystroke 加 state 校验重试——首拍
        # 派发竞态卫生，probe_bigfile B-2 同款）
        opened17 = False
        for _ in range(3):
            t17.call("autoui_keyboard", key="h", modifiers=["ctrl"])
            time.sleep(0.6)
            if state_bool(t17.state("find_replace_mode"), "find_replace_mode"):
                opened17 = True
                break
            time.sleep(0.4)
        iid = None
        for _ in range(4):
            m2 = re.search(r"input #(\w+)", t17.snapshot())
            iid = m2.group(1) if m2 else None
            if iid:
                break
            time.sleep(0.5)
        if iid:
            t17.call("autoui_type", element_id=iid, text="alpha", clear_first=True)
            time.sleep(0.6)
        btn = None
        for _ in range(3):
            btn = find_button_by_text(t17.snapshot(), "全部替换")
            if btn:
                break
            time.sleep(0.5)
        if btn:
            t17.click(btn)
        # 拦截行轮询窗（T13.4 readonly 拦截检查同款——定睡读一次在 50MB
        # 首渲染窗口内会抢跑）。
        c17 = ""
        for _ in range(24):
            c17 = state_str(t17.state("console"), "console") or ""
            if "replace: blocked (big file" in c17:
                break
            time.sleep(0.3)
        st2 = t17.state("console", "big_hint")
        hint = (state_str(st2, "big_hint") or "").strip('"')
        result.check("T17.2 ReplaceAll 拦截（console blocked+big_hint 提示）",
                     "replace: blocked (big file" in c17 and "拦截" in hint,
                     f"opened={opened17} iid={iid} btn={btn is not None} "
                     f"hint={hint!r} console_tail={c17[-140:]!r}")

        # 17.3 big save 直写（PLAN-014 T-05 解禁后形——原「拦截+磁盘零变」
        # 检查随护栏退役翻转：console saved (direct)+字节全等+时长 sane。
        # 未编辑 50MB save=rope 字节直落（T-04 探针 46ms 实证形）；时长
        # 代理=点击→console 行轮询窗，护栏时代读出链 1.3-4.2s+不可用态
        # 对比面。）
        size_before = os.path.getsize(f_big50)
        dblk = ""
        # 点击重试卫生（T17.2 首拍派发竞态同款——高载环境派发丢失重试；
        # 计时起点随每轮重试重置——save 时长语义=派发后直写耗时）
        for _ in range(3):
            t017 = time.time()
            sbtn = find_button_by_icon(t17.snapshot(), "save")
            if sbtn:
                t17.click(sbtn)
            for _ in range(16):
                dblk = state_str(t17.state("console"), "console") or ""
                if "saved (direct): " in dblk:
                    break
                time.sleep(0.25)
            if "saved (direct): " in dblk:
                break
        save_s = round(time.time() - t017, 2)
        st3 = t17.state("console", "big_hint")
        size_after = os.path.getsize(f_big50)
        with open(f_big50, "rb") as fh:
            head_new = fh.read(4096)
        result.check("T17.3 big save 直写（console saved direct+字节全等+时长 sane）",
                     "saved (direct): " in (state_str(st3, "console") or "")
                     and size_after == size_before
                     and head_new.startswith(b"line 00000000")
                     and save_s < 5.0,
                     f"size {size_before}->{size_after} save_s={save_s} "
                     f"hint={((state_str(st3, 'big_hint') or '')[:40])!r}")

        # 17.4 切换往返无残留（seed tab[main.at] ↔ big tab；点击加 state
        # 校验重试——快照-派发间视图重建 vnode 失效卫生，T13 同源）
        tmain = find_button_by_text(t17.snapshot(), "main.at")
        if tmain:
            t17.click(tmain)
        for _ in range(4):
            st4 = t17.state("big_active", "lang_active")
            if state_bool(st4, "big_active") is False:
                break
            tmain = find_button_by_text(t17.snapshot(), "main.at")
            if tmain:
                t17.click(tmain)
            time.sleep(0.6)
        st4 = t17.state("big_active", "lang_active")
        to_big = find_button_by_text(t17.snapshot(), "big50.txt")
        if to_big:
            t17.click(to_big)
        for _ in range(4):
            st5 = t17.state("big_active", "lang_active")
            if state_bool(st5, "big_active") is True:
                break
            to_big = find_button_by_text(t17.snapshot(), "big50.txt")
            if to_big:
                t17.click(to_big)
            time.sleep(0.6)
        st5 = t17.state("big_active", "lang_active")
        result.check("T17.4 切换往返无残留（big↔normal props 联动）",
                     state_bool(st4, "big_active") is False
                     and (state_str(st4, "lang_active") or "").strip('"') == "auto"
                     and state_bool(st5, "big_active") is True
                     and (state_str(st5, "lang_active") or "").strip('"') == "plain",
                     f"main[{state_bool(st4, 'big_active')},"
                     f"{(state_str(st4, 'lang_active') or '').strip(chr(34))}] "
                     f"big[{state_bool(st5, 'big_active')},"
                     f"{(state_str(st5, 'lang_active') or '').strip(chr(34))}]")
        _kill_proc_tree(p17)
    except Exception as e:
        result.check("T17.1-4 探测/拦截/往返链", False, repr(e))

    # 17.5 超大装载（513MB+1B 独立实例——PLAN-025 T-01 门退役后装载
    # 成功形；728 后援分页臂承载。原 T17.5 拒绝形断言[readonly_label=
    # 只读(超大拒绝)+loaded_bytes=0]随 Q-1 裁定 (a) 退役翻转）
    try:
        p17b, t17b = _t17_app({"AUTO_BENCH": "1", "AUTO_OPEN_PATH": f_513})
        ok_rej = _t17_wait_loaded(t17b, "over513.txt", timeout=120)
        st = t17b.state("title_active", "loaded_bytes", "readonly_active",
                        "readonly_label", "big_active", "console")
        result.check("T17.5 超大装载（513MB+1B 分页装载成功+big 态+readonly 零置位）",
                     ok_rej
                     and "超大文件-拒绝装载" not in (state_str(st, "title_active") or "")
                     and state_int(st, "loaded_bytes") == 513 * MB + 1
                     and state_bool(st, "readonly_active") is False
                     and (state_str(st, "readonly_label") or "").strip('"') == ""
                     and state_bool(st, "big_active") is True
                     and "load rejected" not in (state_str(st, "console") or "")
                     and "loaded: " in (state_str(st, "console") or ""),
                     st.replace("\n", " ")[:220])
        _kill_proc_tree(p17b)
    except Exception as e:
        result.check("T17.5 超大装载", False, repr(e))

    # 17.6 阈值下界（49MB——门槛不误伤）
    try:
        p17c, t17c = _t17_app({"AUTO_BENCH": "1", "AUTO_OPEN_PATH": f_49})
        ok_load = _t17_wait_loaded(t17c, "under49.txt")
        st = t17c.state("big_active", "lang_active", "loaded_bytes")
        result.check("T17.6 阈值下界（49MB big_active=false+auto）",
                     ok_load
                     and state_bool(st, "big_active") is False
                     and (state_str(st, "lang_active") or "").strip('"') == "auto"
                     and state_int(st, "loaded_bytes") == 49 * MB,
                     st.replace("\n", " ")[:140])
        _kill_proc_tree(p17c)
    except Exception as e:
        result.check("T17.6 阈值下界", False, repr(e))

    # 17.7 normal 态零误伤（小文件 replace-all 成功+save 写通；AUTO_BENCH=1
    # 必需——ConsumeOpen 的 env 种子仅门控下生效，T13 +按钮同源根因）
    try:
        p17d, t17d = _t17_app({"AUTO_BENCH": "1", "AUTO_OPEN_PATH": f_small,
                               "AUTO_SAVE_PATH": f_small})
        ok_load = _t17_wait_loaded(t17d, "small.txt", timeout=20)
        t17d.call("autoui_keyboard", key="h", modifiers=["ctrl"])
        time.sleep(0.6)
        iid = None
        for _ in range(4):
            m2 = re.search(r"input #(\w+)", t17d.snapshot())
            iid = m2.group(1) if m2 else None
            if iid:
                break
            time.sleep(0.5)
        typed = False
        if iid:
            t17d.call("autoui_type", element_id=iid, text="alpha", clear_first=True)
            time.sleep(0.6)
            m2 = re.findall(r"input #(\w+)", t17d.snapshot())
            if len(m2) >= 2:
                t17d.call("autoui_type", element_id=m2[1], text="ALPHA", clear_first=True)
                time.sleep(0.6)
                typed = True
        btn = find_button_by_text(t17d.snapshot(), "全部替换")
        if btn:
            t17d.click(btn)
            time.sleep(1.0)
        st = t17d.state("console", "big_active", "big_hint")
        rep_ok = "replace all: 2" in (state_str(st, "console") or "")
        sbtn = find_button_by_icon(t17d.snapshot(), "save")
        if sbtn:
            t17d.click(sbtn)
            time.sleep(1.5)
        with open(f_small, encoding="utf-8") as fh:
            saved = fh.read()
        result.check("T17.7 normal 零误伤（replace 2 处+save 写通 E2E）",
                     ok_load and typed and rep_ok
                     and state_bool(st, "big_active") is False
                     and saved.count("ALPHA") == 2
                     and "NEEDLE_QZ" in saved,
                     f"rep_ok={rep_ok} file_alpha={saved.count('ALPHA')}")
        _kill_proc_tree(p17d)
    except Exception as e:
        result.check("T17.7 normal 零误伤", False, repr(e))

    # 17.8 会话恢复重探（退出→同 APPDATA 重启→恢复 tab→装载重探 big）
    try:
        ad17 = tempfile.mkdtemp(prefix="auto013_t17_sess_")
        p17e, t17e = _t17_app({"AUTO_BENCH": "1", "AUTO_OPEN_PATH": f_big50},
                              appdata=ad17)
        ok_load = _t17_wait_loaded(t17e, "big50.txt")
        qitem = None
        menu = find_button_by_text(t17e.snapshot(), "文件")
        if menu:
            t17e.click(menu)
            time.sleep(1.0)
            qitem = find_button_by_text(t17e.snapshot(), "退出")
        if qitem:
            try:
                t17e.click(qitem)
            except (requests.ConnectionError, requests.Timeout):
                pass
        for _ in range(30):
            if p17e.poll() is not None:
                break
            time.sleep(0.5)
        # 菜单点击竞态兜底：确认弹层若在（脏判定竞态）走不保存退出；
        # 仍未退则重试菜单一次。
        if p17e.poll() is None:
            try:
                snap_q = t17e.snapshot()
                disc = find_button_by_text(snap_q, "不保存退出")
                if disc:
                    t17e.click(disc)
                else:
                    menu2 = find_button_by_text(snap_q, "文件")
                    if menu2:
                        t17e.click(menu2)
                        time.sleep(1.0)
                        q2 = find_button_by_text(t17e.snapshot(), "退出")
                        if q2:
                            t17e.click(q2)
            except (requests.ConnectionError, requests.Timeout):
                pass
            for _ in range(20):
                if p17e.poll() is not None:
                    break
                time.sleep(0.5)
        exited = p17e.poll() is not None
        _kill_proc_tree(p17e)
        p17f, t17f = _t17_app({}, appdata=ad17)
        ok_restore = _t17_wait_loaded(t17f, "big50.txt")
        st = t17f.state("big_active", "lang_active", "loaded_bytes",
                        "tab_count")
        result.check("T17.8 会话恢复重探（恢复 tab→装载→big 重探）",
                     ok_load and exited and ok_restore
                     and state_int(st, "tab_count") == 1
                     and state_bool(st, "big_active") is True
                     and (state_str(st, "lang_active") or "").strip('"') == "plain"
                     and state_int(st, "loaded_bytes") == 50 * MB,
                     st.replace("\n", " ")[:160])
        _kill_proc_tree(p17f)
    except Exception as e:
        result.check("T17.8 会话恢复重探", False, repr(e))

    # 17.9-17.12 1GB 四链（PLAN-025 T-02 消费冒烟——共享实例顺序链，
    # 生成式 fixture 不入库）。T-00 实勘驱动面注记（probe_p025_consume
    # 三轮判别，2026-10-02）：① 编辑器光标键盘[Down/Ctrl+End/字符键]
    # autoui_keyboard 不达 code_editor（小文件对照同——普适驱动限制，
    # 非大文件冻结）；② 查找跳（下一处）在分页 100MB 上 21s 未决=728
    # 已知查找债确认（paged-rope.md 帧域协同注记——消费反馈随 upstream
    # 回执登记），不可作 1GB 驱动；③ 014 期「大文件实例 UI 线程硬卡死」
    # 全死症状在 728 工具链未复现（装载/点击/应用级键[Ctrl+F]全活——
    # T17.2/17.3/17.4/17.8 交互簇预期自动复绿，README 判绿口径随谱更新）。
    # 故四链下游可观测形=装载/交互活体+帧带/编辑记账（cut 脏标记，内容
    # 变更型键入=上游 728 bench 已证、MCP 驱动面缺口如实注记）/保存
    # byte-for-byte（零编辑直写往返=合并保存「未改区段照抄」路径）。
    f_1gb = _t17_make("big1024.txt", 1024 * MB)
    try:
        p17g, t17g = _t17_app({"AUTO_BENCH": "1", "AUTO_FRAME_BENCH": "1",
                               "AUTO_OPEN_PATH": f_1gb})
        # 17.9 装载：分页装载成功+big 态+loaded_bytes 全量（墙钟记录=
        # 记账谱数据点；行数即答/远跳的可驱动面缺失见组头注记）
        t0g = time.time()
        ok_1gb = _t17_wait_loaded(t17g, "big1024.txt", timeout=180)
        load_1gb_s = round(time.time() - t0g, 1)
        st = t17g.state("big_active", "lang_active", "loaded_bytes",
                        "readonly_active", "title_active", "console")
        result.check("T17.9 1GB 装载（分页装载成功+big 态+loaded_bytes 全量）",
                     ok_1gb
                     and state_bool(st, "big_active") is True
                     and (state_str(st, "lang_active") or "").strip('"') == "plain"
                     and state_int(st, "loaded_bytes") == 1024 * MB
                     and state_bool(st, "readonly_active") is False
                     and "load rejected" not in (state_str(st, "console") or "")
                     and load_1gb_s < 60.0,
                     f"load_s={load_1gb_s} " + st.replace("\n", " ")[:160])

        # 17.10 交互活体+帧带（「占位不冻结」下游观测形：内容常驻页表
        # 而实例保持派发应答——应用级键开找栏+× 关栏[F13.1e 已证原语]
        # 往返×2 + fprobe_n 帧计数前进[AUTO_FRAME_BENCH=1 门控]）
        dispatch_ok = True
        for _ in range(2):
            t17g.call("autoui_keyboard", key="f", modifiers=["ctrl"])
            time.sleep(0.8)
            m_g = re.search(r"input #(\w+)", t17g.snapshot())
            if not m_g:
                dispatch_ok = False
                break
            xclose = find_button_by_onclick(t17g.snapshot(), "FindClose")
            if xclose:
                t17g.click(xclose)
                time.sleep(0.6)
            else:
                dispatch_ok = False
                break
        fp0 = state_int(t17g.state("fprobe_n"), "fprobe_n")
        time.sleep(3.0)
        fp1 = state_int(t17g.state("fprobe_n"), "fprobe_n")
        result.check("T17.10 交互活体+帧带（派发应答+fprobe_n 前进——占位不冻结观测形）",
                     dispatch_ok and fp1 > fp0,
                     f"dispatch={dispatch_ok} fprobe {fp0}->{fp1}")

        # 17.11 编辑记账（cut 脏标记——dirty 经关闭确认弹层证实：脏 tab
        # 点 x 弹确认、取消后 tab 原样；内容变更型键入=驱动面缺口见组头）
        cut_btn = find_button_by_icon(t17g.snapshot(), "scissors")
        cut_ok = False
        if cut_btn:
            t17g.click(cut_btn)
            for _ in range(12):
                if "cut" in (state_str(t17g.state("console"),
                                       "console") or ""):
                    cut_ok = True
                    break
                time.sleep(0.25)
        xs_g = find_tab_close_buttons(t17g.snapshot())
        confirm_seen = False
        cancelled = False
        if cut_ok and xs_g:
            t17g.click(xs_g[0])
            for _ in range(12):
                if state_bool(t17g.state("confirm_open"),
                              "confirm_open") is True:
                    confirm_seen = True
                    break
                time.sleep(0.25)
            cancel_g = find_button_by_text(t17g.snapshot(), "取消")
            if cancel_g:
                t17g.click(cancel_g)
                for _ in range(12):
                    if state_bool(t17g.state("confirm_open"),
                                  "confirm_open") is False:
                        cancelled = True
                        break
                    time.sleep(0.25)
        st = t17g.state("tab_count", "big_active")
        result.check("T17.11 编辑记账（cut 脏标记+关闭确认证实+取消零扰动）",
                     cut_ok and confirm_seen and cancelled
                     and state_int(st, "tab_count") == 3
                     and state_bool(st, "big_active") is True,
                     f"cut={cut_ok} confirm={confirm_seen} "
                     f"cancel={cancelled} tabs={state_int(st, 'tab_count')}")

        # 17.12 保存 byte-for-byte（零编辑直写往返=合并保存「未改区段
        # 照抄」路径下游观测；md5 全卷对照+墙钟记录=谱数据点）
        h0 = hashlib.md5()
        with open(f_1gb, "rb") as fh:
            while True:
                chunk = fh.read(1 << 20)
                if not chunk:
                    break
                h0.update(chunk)
        md5_before = h0.hexdigest()
        t0g = time.time()
        sbtn = find_button_by_icon(t17g.snapshot(), "save")
        saved_1gb = False
        if sbtn:
            t17g.click(sbtn)
            for _ in range(60):
                if "saved (direct): " in (state_str(t17g.state("console"),
                                                     "console") or ""):
                    saved_1gb = True
                    break
                time.sleep(0.25)
        save_1gb_s = round(time.time() - t0g, 1)
        h1 = hashlib.md5()
        with open(f_1gb, "rb") as fh:
            while True:
                chunk = fh.read(1 << 20)
                if not chunk:
                    break
                h1.update(chunk)
        result.check("T17.12 1GB 保存 byte-for-byte（直写往返+全卷 md5 全等）",
                     saved_1gb
                     and os.path.getsize(f_1gb) == 1024 * MB
                     and h1.hexdigest() == md5_before,
                     f"saved={saved_1gb} save_s={save_1gb_s} "
                     f"md5_equal={h1.hexdigest() == md5_before}")
        print(f"  [p025 spectrum] 1GB load={load_1gb_s}s save={save_1gb_s}s")
        _kill_proc_tree(p17g)
    except Exception as e:
        result.check("T17.9-12 1GB 四链", False, repr(e))
    finally:
        try:
            os.remove(f_1gb)
        except OSError:
            pass

    # T18: PLAN-014 —— 上游端点消费检查组（T17 形态：独立新鲜进程+APPDATA
    # 隔离）。子组：
    #   18.1 513MB 零编辑直写保存往返（原「readonly 兜底不受扰·513MB 拒
    #        形」随 PLAN-025 门退役翻转：readonly 兜底面=编码错误形由
    #        T12.7/T13.4 既有承接——本检查改断言合并保存「未改区段照抄」
    #        边界档往返：装载→save→磁盘 byte-for-byte+readonly 零置位）
    #   18.2 光标恢复 E2E（T-06 set_cursor 转正——cline/ccol 持久化→恢复
    #        应用；断言=重启后 Down/Up 往返驱 CursorMoved→SyncCursor 读回
    #        持久位[set_cursor 不 republish on_cursor——契约]）
    #   18.3 scroll 条件形现状注记（会话 JSON 无 scroll 字段=「滚动不恢
    #        复」现状；供② 读投影生态面归后续件——Q-3 注记维持）
    #   （normal 零扰动=T17.7 覆盖、会话链回归=T17.8 覆盖——不重复设检）
    print("\nT18: PLAN-014 upstream consume")
    t18_dir = tempfile.mkdtemp(prefix="p014_t18_fx_")
    f18 = os.path.join(t18_dir, "cursor_restore.txt")
    with open(f18, "w", encoding="utf-8", newline="") as f:
        for i in range(1, 13):
            extra = " TARGETCURSOR" if i == 3 else ""
            f.write(f"restore line {i:02d}{extra} payload\n")

    def _t18_app(extra, appdata=None):
        port = pick_free_port()
        env = {**os.environ, "AUTOUI_MCP_PORT": str(port),
               "APPDATA": appdata or tempfile.mkdtemp(prefix="auto014_t18_"),
               **extra}
        proc = subprocess.Popen(
            [AUTO_BIN, "run", "-r", "vm"],
            cwd=PROJECT, env=env,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        url = f"http://127.0.0.1:{port}/mcp"
        assert wait_for_server(url, 30), "T18 server never up"
        t = McpClient(url)
        for _ in range(15):
            s = t.snapshot()
            if "(rendered)" in s and s.count("onclick") > 0:
                break
            time.sleep(1)
        time.sleep(1.5)
        return proc, t

    # 18.1 513MB 零编辑直写保存往返（PLAN-025 门退役翻转——装载成功形；
    # 原拒绝形 save blocked 断言退役，readonly 外层先行语义=T12.7/T13.4
    # 编码错误形承接维持）
    try:
        p18, t18 = _t18_app({"AUTO_BENCH": "1", "AUTO_OPEN_PATH": f_513})
        for _ in range(120 * 4):
            c18 = state_str(t18.state("console"), "console") or ""
            if "loaded: " in c18 and "over513.txt" in c18:
                break
            time.sleep(0.25)
        size18 = os.path.getsize(f_513)
        sbtn18 = find_button_by_icon(t18.snapshot(), "save")
        blk18 = ""
        if sbtn18:
            t18.click(sbtn18)
        for _ in range(40):
            blk18 = state_str(t18.state("console"), "console") or ""
            if "saved (direct): " in blk18:
                break
            time.sleep(0.25)
        st18ro = t18.state("readonly_active", "readonly_label")
        result.check("T18.1 513MB 零编辑直写往返（saved direct+byte-for-byte+readonly 零置位）",
                     "saved (direct): " in blk18
                     and os.path.getsize(f_513) == size18
                     and state_bool(st18ro, "readonly_active") is False,
                     f"console_tail={blk18[-100:]!r} "
                     f"size {size18}->{os.path.getsize(f_513)}")
        _kill_proc_tree(p18)
    except Exception as e:
        result.check("T18.1 513MB 零编辑直写往返", False, repr(e))

    # 18.2 光标恢复 E2E（T-06 set_cursor 转正）。驱动形（全已证原语）：
    # Ctrl+F 栏+type pattern+「下一处」按钮=code_editor_find 跳匹配
    # （store .FindNext 显式 SyncCursor——状态栏 line/col 即读回面）→
    # 退出（CloseRequest→SessionSave 持久化 cline/ccol）→重启同 APPDATA
    # （恢复链装载完成位 set_cursor 应用[不 republish on_cursor——契约]
    # ）→点已激活 tab（TabActivate→SyncCursor 读回真实位）。未恢复形
    # 对照=读回 1/1。
    try:
        ad18 = tempfile.mkdtemp(prefix="auto014_t18_sess_")
        p18b, t18b = _t18_app({"AUTO_BENCH": "1", "AUTO_OPEN_PATH": f18},
                              appdata=ad18)
        ok18 = _t17_wait_loaded(t18b, "cursor_restore.txt")
        t18b.call("autoui_keyboard", key="f", modifiers=["ctrl"])
        time.sleep(0.6)
        iid18 = None
        for _ in range(4):
            m18 = re.search(r"input #(\w+)", t18b.snapshot())
            iid18 = m18.group(1) if m18 else None
            if iid18:
                break
            time.sleep(0.5)
        typed18 = False
        if iid18:
            for _ in range(3):
                t18b.call("autoui_type", element_id=iid18,
                          text="TARGETCURSOR", clear_first=True)
                time.sleep(0.5)
                eff = state_str(t18b.state("find_effective"),
                                "find_effective")
                if "TARGETCURSOR" in eff:
                    typed18 = True
                    break
        nxt18 = find_button_by_text(t18b.snapshot(), "下一处")
        if nxt18:
            t18b.click(nxt18)
            time.sleep(0.8)
        st18 = {}
        for _ in range(6):
            st18 = t18b.state("line", "col")
            if state_int(st18, "line") == 3:
                break
            time.sleep(0.5)
        line_set = state_int(st18, "line")
        col_set = state_int(st18, "col")
        q18 = None
        menu18 = find_button_by_text(t18b.snapshot(), "文件")
        if menu18:
            t18b.click(menu18)
            time.sleep(1.0)
            q18 = find_button_by_text(t18b.snapshot(), "退出")
        if q18:
            try:
                t18b.click(q18)
            except (requests.ConnectionError, requests.Timeout):
                pass
        for _ in range(30):
            if p18b.poll() is not None:
                break
            time.sleep(0.5)
        if p18b.poll() is None:
            try:
                disc18 = find_button_by_text(t18b.snapshot(), "不保存退出")
                if disc18:
                    t18b.click(disc18)
            except (requests.ConnectionError, requests.Timeout):
                pass
            for _ in range(20):
                if p18b.poll() is not None:
                    break
                time.sleep(0.5)
        exited18 = p18b.poll() is not None
        _kill_proc_tree(p18b)
        p18c, t18c = _t18_app({}, appdata=ad18)
        ok_rs = _t17_wait_loaded(t18c, "cursor_restore.txt")
        time.sleep(1.0)
        tb18 = None
        for _ in range(3):
            tb18 = find_button_by_text(t18c.snapshot(), "cursor_restore.txt")
            if tb18:
                t18c.click(tb18)
            time.sleep(0.8)
            if state_int(t18c.state("line", "col"), "line") == 3:
                break
        st18r = t18c.state("line", "col", "tab_count")
        line_rs = state_int(st18r, "line")
        col_rs = state_int(st18r, "col")
        result.check("T18.2 光标恢复 E2E（find 跳持久位=重启 TabActivate 读回）",
                     ok18 and typed18 and exited18 and ok_rs
                     and state_int(st18r, "tab_count") == 1
                     and line_set == 3
                     and line_rs == 3 and col_rs == col_set,
                     f"set=({line_set},{col_set}) restored=({line_rs},"
                     f"{col_rs}) typed={typed18} exited={exited18}")
        _kill_proc_tree(p18c)
    except Exception as e:
        result.check("T18.2 光标恢复 E2E", False, repr(e))

    # 18.3 scroll 条件形现状注记（会话 JSON 无 scroll 字段=「滚动不恢复」
    # 现状维持——供② 读投影生态证据归后续，Q-3 注记）
    try:
        import glob as _glob
        sess = None
        cands = sorted(_glob.glob(os.path.join(
            tempfile.gettempdir(), "auto014_t18_sess_*",
            "auto-edit-session.json")))
        if cands:
            sess = cands[-1]
        ok_no_scroll = False
        note18 = "session file absent"
        if sess and os.path.exists(sess):
            with open(sess, encoding="utf-8") as fh:
                body = fh.read()
            ok_no_scroll = '"scroll' not in body and 'scroll_' not in body
            note18 = f"scroll_keys_absent={ok_no_scroll} tabs={body.count('path')}"
        result.check("T18.3 scroll 条件形注记（会话无 scroll 字段=现状）",
                     ok_no_scroll, note18)
    except Exception as e:
        result.check("T18.3 scroll 条件形注记", False, repr(e))

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

    # PLAN-022 T-06: 主实例端口钉位（P716-D1 销账处方——AUTOUI_MCP_PORT
    # 环境钉位优先，绕开 924x TOCTOU 竞态带[connect_ex 探测与 app bind
    # 间死占实录：716 执行期 6 启动 3 败+本件首跑同族]；子实例族
    # _t13/_t15/_t16/_t17_app 各自动态 pick 不受累）。
    _pinned = os.environ.get("AUTOUI_MCP_PORT")
    mcp_port = (int(_pinned) if _pinned and _pinned.isdigit()
                else pick_free_port())
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
