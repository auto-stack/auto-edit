#!/usr/bin/env python3
"""PLAN-010 T-00 会话链勘（决策件）——会话 IO 四端点 + 懒恢复协议 + 退出写盘时序探针.

载具 = tests/probe_session_app/（vm merged 最小 app：产品 back 契约两文件
verbatim 拷贝 + 恢复链预演 store），python autoui/HTTP 断言。五项勘定：
  ① 会话文件 IO 往返：env_str("APPDATA")（merged+split HTTP 两形）+
     根级 write_text → exists → read_text → json.to_value 字节往返
     （json_escape 双字符转义——marker 含引号/反斜杠/中文；中文路径
     fixture；python json.loads 独立复核转义正确性）。
  ② 恢复序预演：RestorePreview 注入三文件 tab（loaded=false ×3，
     active=1）→ 快照 textarea 计数==1（视图只实化 active）→ Tick
     RunPendingLoad 装载 active（loaded_bytes==文件字节）→ TabActivate
     切未装载 tab → 装载触发（load_key/path_active 联动实证，逐 tab）。
  ③ 非激活 tab 编辑器存留：装载 tab2 → 切 tab1（装载）→ 切回 tab2
     （loaded==true 不置 load_key）→ readback：内容在且 reload_count
     不推进 = registry 存留（免重装）；内容空或重装 = 重建即卸载
     （重装语义）——Q-1 定案判据。
  ④ 退出写盘时序：quitwrite（产品 CloseRequest 干净臂同构：write_text
     → Process.exit(0)）→ 进程退出后读盘断言内容（写盘先于退出的可靠
     性；产品三臂的全覆盖在矩阵 T14）。
  ⑤ 损坏 JSON：写垃圾串后 json.to_value——抛异常（catch=静默全新启动）
     or 容忍（null 形字段，ws 门兜底）——T-02 恢复门防御形态定案。

用法：cd specs/auto-edit/tests && python probe_session.py
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
PROBE_APP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "probe_session_app")


def unesc(s):
    """autoui_state 文本转义解码（探针 probe_find 同款 + 控制字符面）：
    反斜杠加倍与 \n/\\" 字面化——先保护双反斜杠，再译控制符。"""
    if s is None:
        return None
    return (s.replace("\\\\", "\x00").replace("\\n", "\n")
             .replace('\\\\"', '"').replace("\\\"", "\"").replace("\x00", "\\"))


def state_flag(state_text, field):
    """bool 断言宽收：true/false（字面量置位）与 1/0（back 端点返回的
    bool 经 FFI 到 VM 渲染为 int——exists_ok: 1 (int) 实勘）两形。"""
    m = re.search(rf"{field}:\s*(true|1|false|0)\b", state_text or "")
    if not m:
        return None
    return m.group(1) in ("true", "1")


def click_btn(mcp, label):
    btn = find_button_by_text(mcp.snapshot(), label)
    if btn is None:
        return False
    try:
        mcp.click(btn)
    except (requests.ConnectionError, requests.Timeout):
        pass
    time.sleep(0.5)
    return True


def launch(env_extra, server_split=False, http_port=None):
    port = pick_free_port()
    cmd = [AUTO_BIN, "run", "-r", "vm"]
    env = {**os.environ, "AUTOUI_MCP_PORT": str(port), **env_extra}
    if server_split:
        cmd.append("--server")
        cmd.append("vm")
        env["AUTO_HTTP_PORT"] = str(http_port)
    log = tempfile.NamedTemporaryFile(
        prefix="p010_probe_", suffix=".log", delete=False, mode="w",
        encoding="utf-8", errors="replace")
    proc = subprocess.Popen(cmd, cwd=PROBE_APP, env=env,
                            stdout=log, stderr=subprocess.STDOUT)
    return proc, f"http://127.0.0.1:{port}/mcp", log.name


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

    # ---- 工件：临时 APPDATA ×2 + 临时 ws 三 fixture（F1=中文文件名）----
    appdata_m = tempfile.mkdtemp(prefix="auto010_t00_appdata_")
    appdata_h = tempfile.mkdtemp(prefix="auto010_t00_appdata_http_")
    ws = tempfile.mkdtemp(prefix="auto010_t00_ws_")
    f1 = os.path.join(ws, "你好文件.at")
    f2 = os.path.join(ws, "two.at")
    f3 = os.path.join(ws, "three.md")
    c1 = "FILEONE alpha\n第二行\n"
    c2 = "FILETWO beta content\nrow two\n"
    c3 = "FILETHREE gamma\n"
    for p, c in ((f1, c1), (f2, c2), (f3, c3)):
        with open(p, "w", encoding="utf-8", newline="") as f:
            f.write(c)
    b1, b2, b3 = (len(c1.encode("utf-8")), len(c2.encode("utf-8")),
                  len(c3.encode("utf-8")))
    env_common = {
        "APPDATA": appdata_m,
        "AUTO_PROBE_WS": ws,
        "AUTO_PROBE_F1": f1, "AUTO_PROBE_F2": f2, "AUTO_PROBE_F3": f3,
    }

    # ================= Phase B：merged 恢复链预演（②③）=================
    print("\nPhase B: merged lazy-restore preview (inject -> active-only load)")
    proc, url, _log = launch(env_common)
    try:
        if not wait_for_server(url, 30):
            raise RuntimeError("MCP server did not start")
        mcp = McpClient(url)
        snap = ""
        for _ in range(15):
            snap = mcp.snapshot()
            if "(rendered)" in snap:
                break
            time.sleep(1)
        time.sleep(2.0)  # 首拍派发竞态窗定驻（009 T-00④ 卫生）
        _ = mcp.state("init_mark")

        # ② 注入：三 tab loaded=false ×3、active=1
        ok_restore = click_btn(mcp, "restore")
        st = mcp.state("init_mark", "tab_count", "appdata")
        check("② restore injected 3 tabs (active=idx1)",
              ok_restore and state_str(st, "init_mark") == "injected"
              and state_int(st, "tab_count") == 3, st[:160])
        # merged env_str("APPDATA") 通道：返回临时 APPDATA（隔离实证；
        # state 文本反斜杠加倍 → unesc 解码后比对）
        check("① env_str APPDATA reaches store (merged, isolated)",
              unesc(state_str(st, "appdata")) == appdata_m,
              f"got={state_str(st, 'appdata')!r} want={appdata_m!r}")

        # ② 视图只实化 active：3 tab 快照仅 1 个编辑器
        n_editor = mcp.snapshot().count("textarea")
        check("② only active editor materialized (textarea==1)",
              n_editor == 1, f"textarea count={n_editor}")

        # ② 仅 active 装载：Tick RunPendingLoad → tab2 字节到达
        lb = -1
        for _ in range(30):
            st = mcp.state("loaded_bytes", "last_load", "reload_count")
            lb = state_int(st, "loaded_bytes")
            if lb == b2 and "two.at" in (state_str(st, "last_load") or ""):
                break
            time.sleep(0.3)
        check("② active tab auto-loaded (loaded_bytes==two.at bytes)",
              lb == b2, f"loaded_bytes={lb} want={b2} last={state_str(st, 'last_load')!r}")
        rc_active = state_int(st, "reload_count")
        check("② reload_count==1 after active load", rc_active == 1, f"rc={rc_active}")

        # ② TabActivate 切未装载 tab → 装载触发（tab1，中文文件名）
        ok_tab1 = click_btn(mcp, "你好文件.at")
        lb1 = -1
        for _ in range(30):
            st = mcp.state("loaded_bytes", "last_load")
            lb1 = state_int(st, "loaded_bytes")
            if lb1 == b1:
                break
            time.sleep(0.3)
        check("② activate unloaded tab triggers load (tab1 bytes)",
              ok_tab1 and lb1 == b1, f"loaded_bytes={lb1} want={b1}")

        # ③ 切回已装载 tab2：loaded==true 不重装 + readback 内容在
        ok_tab2 = click_btn(mcp, "two.at")
        time.sleep(1.5)  # 数个 Tick 窗：若语义错误此处会出现重装
        st = mcp.state("reload_count", "loaded_bytes")
        rc_back = state_int(st, "reload_count")
        click_btn(mcp, "readback")
        head = unesc(state_str(mcp.state("back_head"), "back_head"))
        want_head = c2 if len(c2) <= 48 else c2[:48]
        retained = (rc_back == rc_active + 1) and head == want_head
        report["q1_registry_retention"] = "retained" if retained else "rebuilt"
        check("③ switch-back: no reload (reload_count stable)",
              ok_tab2 and rc_back == rc_active + 1,
              f"rc={rc_back} want={rc_active + 1}")
        check("③ switch-back: content retained in editor",
              head == want_head, f"head={head!r} want={want_head!r}")
        check("③ Q-1 verdict recorded", True, report["q1_registry_retention"])

        # ② 第三 tab 首次激活同样触发（逐 tab 懒装载完备性）
        ok_tab3 = click_btn(mcp, "three.md")
        lb3 = -1
        for _ in range(30):
            st = mcp.state("loaded_bytes")
            lb3 = state_int(st, "loaded_bytes")
            if lb3 == b3:
                break
            time.sleep(0.3)
        check("② third tab first-activation loads (tab3 bytes)",
              ok_tab3 and lb3 == b3, f"loaded_bytes={lb3} want={b3}")

        # ---- ① merged IO 往返（json_escape 转义 + python 独立解析复核）----
        print("\n① merged session IO roundtrip (escape + parse-back)")
        ok_io = click_btn(mcp, "io")
        st = mcp.state("write_ok", "exists_ok", "parse_ok",
                       "parsed_marker", "parsed_ws", "parsed_ccol")
        w_ok = state_flag(st, "write_ok")
        e_ok = state_flag(st, "exists_ok")
        p_ok = state_flag(st, "parse_ok")
        marker = unesc(state_str(st, "parsed_marker"))
        pws = unesc(state_str(st, "parsed_ws"))
        ccol = state_int(st, "parsed_ccol")
        check("① write_text + exists on APPDATA root (merged)",
              ok_io and w_ok is True and e_ok is True, f"w={w_ok} e={e_ok} raw={st[:200]!r}")
        want_marker = 'quote"back\\slash中文'
        check("① json_escape roundtrip: marker survives (quote/backslash/中文)",
              p_ok is True and marker == want_marker,
              f"parse={p_ok} marker={marker!r}")
        check("① parsed ws_dir + nested ccol",
              pws == ws and ccol == 7, f"ws={pws!r} ccol={ccol}")
        spath = os.path.join(appdata_m, "auto-edit-probe-session.json")
        disk_raw = open(spath, encoding="utf-8").read() if os.path.exists(spath) else ""
        py_parse = {}
        try:
            py_parse = json.loads(disk_raw)
        except Exception as ex:  # noqa: BLE001
            check("① python json.loads independent reparse", False, f"{ex}: {disk_raw[:120]!r}")
        else:
            check("① python json.loads independent reparse",
                  py_parse.get("marker") == want_marker and py_parse.get("ws_dir") == ws
                  and py_parse["tabs"][0]["ccol"] == 7,
                  f"keys={sorted(py_parse)[:6]}")
            check("① disk bytes carry escaped quote sequence",
                  '\\"' in disk_raw, disk_raw[:160])

        # ⑤ 损坏 JSON：抛 or 容忍，均不崩——定案 T-02 恢复门形态
        # （设计双兼容：抛→catch 全新启动；容忍→ws_dir ?? "" 匹配门拦下。
        # marker 读值仅记录，不作硬断言——容忍形下非对象取字段行为由
        # 产品侧 try 门兜底）。
        print("\n⑤ corrupted session JSON parse behavior")
        ok_re = click_btn(mcp, "reparse")
        time.sleep(0.5)
        st = mcp.state("corrupt_parse_ok", "corrupt_marker")
        c_ok = state_bool(st, "corrupt_parse_ok")
        c_marker = unesc(state_str(st, "corrupt_marker"))
        behavior = "throws" if c_ok is False else "tolerates"
        report["corrupt_json_behavior"] = behavior
        check("⑤ corrupted JSON: no crash (gate handles throw-or-tolerate)",
              ok_re and proc.poll() is None,
              f"behavior={behavior} marker={c_marker!r} raw={st[:120]!r}")

        # ④ 退出写盘时序：写盘 → exit(0) → 退出后读盘
        print("\n④ quit-write timing (write before Process.exit)")
        sp_before = os.path.getmtime(spath) if os.path.exists(spath) else 0
        click_btn(mcp, "quitwrite")
        exited = False
        for _ in range(20):
            if proc.poll() is not None:
                exited = True
                break
            time.sleep(0.5)
        check("④ process exited on quitwrite", exited, f"poll={proc.poll()}")
        quit_raw = open(spath, encoding="utf-8").read() if os.path.exists(spath) else ""
        check("④ session written before exit (disk content after exit)",
              quit_raw == '{"quit":"written-before-exit"}',
              f"raw={quit_raw[:80]!r} mtime_new={os.path.getmtime(spath) if os.path.exists(spath) else 0} > {sp_before}")
    except Exception as e:  # noqa: BLE001
        check("phase B run", False, repr(e))
    finally:
        if proc.poll() is None:
            _kill_proc_tree(proc)

    # ================= Phase A：split HTTP 四端点往返 =================
    print("\nPhase A: split HTTP endpoint roundtrip (--server vm)")
    http_port = pick_free_port(8600)
    env_http = {**env_common, "APPDATA": appdata_h}
    proc, _url, _log = launch(env_http, server_split=True, http_port=http_port)
    base = f"http://127.0.0.1:{http_port}"
    try:
        up = False
        r = None
        for _ in range(30):
            try:
                r = requests.get(f"{base}/api/exists", params={"path": f2}, timeout=2)
                if r.status_code == 200:
                    up = True
                    break
            except requests.RequestException:
                pass
            time.sleep(1)
        check("① split HTTP server up (/api/exists 200)", up,
              f"last={r.status_code if r is not None else 'no-response'}")
        if up:
            r = requests.get(f"{base}/api/env_str", params={"name": "APPDATA"}, timeout=5)
            got = r.text.replace('"', "").replace("\\\\", "\\")
            check("① env_str APPDATA over HTTP (isolated)",
                  r.status_code == 200 and appdata_h in got,
                  f"status={r.status_code} body={r.text[:120]!r}")
            r = requests.get(f"{base}/api/exists", params={"path": f2}, timeout=5)
            check("① exists over HTTP (fixture; bool 渲染 1/true 两形皆收)",
                  r.status_code == 200 and r.text.strip().lower() in ("1", "true"),
                  f"status={r.status_code} body={r.text[:80]!r}")
            sp2 = os.path.join(appdata_h, "http-session.json")
            payload = json.dumps({"path": sp2, "content": "{\"http\":\"roundtrip-010\"}"},
                                 ensure_ascii=False)
            r = requests.post(f"{base}/api/write_text", data=payload.encode("utf-8"),
                              headers={"Content-Type": "application/json"}, timeout=5)
            check("① write_text over HTTP (POST json body)",
                  r.status_code == 200, f"status={r.status_code} body={r.text[:80]!r}")
            r = requests.get(f"{base}/api/read_text", params={"path": sp2}, timeout=5)
            got = r.text
            check("① read_text over HTTP roundtrip",
                  r.status_code == 200 and "roundtrip-010" in got.replace('\\"', '"'),
                  f"status={r.status_code} body={r.text[:120]!r}")
    except Exception as e:  # noqa: BLE001
        check("phase A run", False, repr(e))
    finally:
        if proc.poll() is None:
            _kill_proc_tree(proc)

    # ---- 收尾 ----
    report["checks"] = checks
    report["pass"] = all(c["ok"] for c in checks)
    out = os.path.join(tempfile.gettempdir(), "probe_session_report.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\nreport: {out}")
    print(f"toolchain: {report['toolchain']}")
    print(f"decision Q-1 registry retention: {report.get('q1_registry_retention')}")
    print(f"decision corrupt-json: {report.get('corrupt_json_behavior')}")
    failed = [c for c in checks if not c["ok"]]
    print(f"RESULT: {len(checks) - len(failed)} passed, {len(failed)} failed")
    shutil.rmtree(ws, ignore_errors=True)
    sys.exit(0 if report["pass"] else 1)


if __name__ == "__main__":
    main()
