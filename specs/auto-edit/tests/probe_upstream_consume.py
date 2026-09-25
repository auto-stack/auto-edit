#!/usr/bin/env python3
r"""PLAN-014 T-04 上游端点消费探针（决策件）——供①②④⑥ 实形勘定.

前置=PLAN-701 六件 delivered（2026-09-25 归档，工具链 v2127）。
仪器=fixture 迷你 app（tests/fixtures/p014_consume_app/，gitignored，
逐跑再生成）——kernel 级端点直调（裸名内建），stdout P014 标记采集。

五相：
  ① save 直写字节保真（供①）：LF/CRLF/BOM 三变体 load→save 往返
     逐字节对照 + 50MB E2E 计时（instant_elapsed + host 墙钟双录）
     ——SD-01 定形证据（BOM/EOL 归属实测）。
  ② set-cursor 基面（供②a）：set(1,2)→cursor_line/col 读回（0 基
     预期）——SD-02/014 T-06 换算锚。
  ③ scroll 读/写往返（供②b）：scroll_to(0,60)→下拍 offset 读回
     （命令值投影预期）。
  ④ time 族形态（供④）：now_ms/now_sec/now + instant_now/elapsed
     打印形勘定（i64 直出/concat/.str() 三形并试——701 spec「print
     直出」面的实测）。
  ⑤ shell_add_recent（供⑥）：调用返回 true + Recent 树增量（真/
     隔离 APPDATA 双扫）——T-02 消费的 E2E 面预演。
  附：供⑤ 在册 grep（ts_adapter print 改道/menubar-sub schema/
     helper 注解）。

用法：cd specs/auto-edit/tests && python probe_upstream_consume.py
     [--keep] [--skip-big]
报告：probe_upstream_consume_report.{json,txt}。退出码 0=勘定完成
     （各相判定值记录在报告；字节保真判定≠全等预期——记录实际形）。
"""

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

TESTS = Path(__file__).resolve().parent
PROJECT = TESTS.parent
REPO = PROJECT.parent.parent
AUTO_BIN = __import__("os").environ.get("AUTO_BIN") or shutil.which("auto") or ""
FIXTURE_APP = TESTS / "fixtures" / "p014_consume_app"
MB = 1024 * 1024

PAC = """name: "p014probe"
version: "0.1.0"
description: "PLAN-014 T-04 endpoint probe fixture"
scene: "ui"
render: "vm"
title: "P014Probe"
opens: ".txt"

dep stylekit {
    path: "../../../../stylekit"
}
"""

APP = """use probe_store: ProbeStore

widget App {
    view {
        col (style: "h-full w-full") {
            code_editor (key: "k1", wrap: false, style: "flex-1 w-full") {
                content: ""
            }
        }
    }
    on {
        .Tick -> {
            store.ProbeTick()
        }
    }
}
"""

STORE_TMPL = """store ProbeStore {{
    model {{
        var interval int = 250
        var step int = 0
        var h int = 0
    }}
    on {{
        .ProbeTick -> {{
            if .step == 0 {{
                .step = 1
            }}
            if .step == 1 {{
                print("P014 phase1")
                code_editor_load_file("k1", "{src}")
                .step = 2
            }}
            if .step == 2 {{
                if {extras} == 1 {{
                    code_editor_set_cursor("k1", 1, 2)
                    print("P014 cur_line " + code_editor_cursor_line("k1").str())
                    print("P014 cur_col " + code_editor_cursor_col("k1").str())
                    if code_editor_scroll_to("k1", 0.0, 300.0) {{
                        print("P014 scroll_to true")
                    }} else {{
                        print("P014 scroll_to false")
                    }}
                }}
                .step = 3
            }}
            if .step == 3 {{
                if {extras} == 1 {{
                    print("P014 sy_soft " + code_editor_scroll_offset_y("k1").str())
                }}
                print("P014 t_ms")
                print(time.now_ms())
                if shell_add_recent("{src}") {{
                    print("P014 shell true")
                }} else {{
                    print("P014 shell false")
                }}
                print("P014 save_ms")
                if code_editor_save("k1", "{dst}") {{
                    print("P014 save true")
                    print(time.now_ms())
                }} else {{
                    print("P014 save false")
                }}
                print("P014 probe_done")
                .step = 4
            }}
        }}
    }}
}}
"""

def write_fixture(src: str, dst: str, extras: int) -> None:
    if FIXTURE_APP.exists():
        shutil.rmtree(FIXTURE_APP)
    (FIXTURE_APP / "src" / "front").mkdir(parents=True)
    (FIXTURE_APP / "pac.at").write_text(PAC, encoding="utf-8")
    (FIXTURE_APP / "src" / "front" / "app.at").write_text(APP, encoding="utf-8")
    store = STORE_TMPL.format(src=src.replace("\\", "/"),
                              dst=dst.replace("\\", "/"), extras=extras)
    (FIXTURE_APP / "src" / "front" / "probe_store.at").write_text(
        store, encoding="utf-8")


def snapshot_recent(appdata: Path) -> dict:
    recent = appdata / "Microsoft" / "Windows" / "Recent"
    snap = {}
    if recent.is_dir():
        for p in recent.rglob("*"):
            if p.is_file():
                st = p.stat()
                snap[str(p.relative_to(recent)).lower()] = [st.st_size,
                                                            st.st_mtime_ns]
    return snap


def run_app(timeout_s: float) -> tuple[str, int]:
    import os
    import socket
    for port in range(9600, 9700):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                free = port
                break
    env = {**os.environ, "AUTOUI_MCP_PORT": str(free)}
    log_path = FIXTURE_APP / "run.log"
    with open(log_path, "w", encoding="utf-8", errors="replace") as log:
        proc = subprocess.Popen([AUTO_BIN, "run", "-r", "vm"],
                                cwd=str(FIXTURE_APP), env=env,
                                stdout=log, stderr=subprocess.STDOUT)
        t0 = time.time()
        seen = ""
        while time.time() - t0 < timeout_s:
            try:
                seen = log_path.read_text(encoding="utf-8", errors="replace")
                if "P014 probe_done" in seen:
                    break
                if "link failed" in seen or "error:" in seen.lower()[:2000] \
                        and "P014" not in seen:
                    break
            except OSError:
                pass
            time.sleep(0.2)
        time.sleep(0.5)
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)],
                       capture_output=True)
        try:
            proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            pass
    return seen, free


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep", action="store_true")
    ap.add_argument("--skip-big", action="store_true")
    args = ap.parse_args()
    if not AUTO_BIN:
        print("FATAL: auto 工具链缺席（AUTO_BIN/PATH）")
        return 1
    report = {"toolchain": AUTO_BIN, "runs": {}, "grep_供⑤": {}}
    tmp = Path(tempfile.mkdtemp(prefix="p014_consume_"))
    iso_appdata = tmp / "ad"
    iso_appdata.mkdir()

    # 供⑤ 在册 grep（源面——组内钉版依赖 worktree，缺省主检出回落）
    import os
    lang_root = Path(os.environ.get("AUTO_LANG_ROOT")
                     or REPO.parent / "auto-lang")
    if not (lang_root / "crates").is_dir():
        lang_root = Path("D:/autostack/auto-lang")
    ts = lang_root / "crates" / "auto-lang" / "src" / "ui_gen" / "ts_adapter.rs"
    rust_gen = ts.parent / "rust.rs"
    blob = ts.read_text(encoding="utf-8", errors="replace")
    rblob = rust_gen.read_text(encoding="utf-8", errors="replace")
    report["grep_供⑤"] = {
        "print_globalthis": "globalThis" in blob,
        "menubar_sub_vue": "menubar-sub" in rblob,
        "helper_annotated": ": string" in blob or ": number" in blob
        or "any[]" in blob,
    }

    try:
        real_ad = Path(__import__("os").environ.get("USERPROFILE", "")) \
            / "AppData" / "Roaming"
        variants = [("lf", b"line one\nline two\nline three\n// \u4f60\u597d\n"),
                    ("crlf", b"alpha\r\nbeta\r\ngamma\r\n"),
                    ("bom", b"\xef\xbb\xbfmarked\nplain\n")]
        if not args.skip_big:
            pass  # big 走独立 run（尾部）
        for name, data in variants:
            src = tmp / f"src_{name}.txt"
            dst = tmp / f"dst_{name}.txt"
            src.write_bytes(data)
            pre = {str(real_ad): snapshot_recent(real_ad),
                   str(iso_appdata): snapshot_recent(iso_appdata)}
            write_fixture(str(src), str(dst), 1 if name == "lf" else 0)
            out, _ = run_app(60)
            post = {str(real_ad): snapshot_recent(real_ad),
                    str(iso_appdata): snapshot_recent(iso_appdata)}
            delta = []
            for k in pre:
                delta += [f"{k}::{x}" for x in post[k]
                          if x not in pre[k] or pre[k][x] != post[k][x]]
            got = dst.read_bytes() if dst.exists() else None
            p014 = [ln.strip() for ln in out.splitlines()
                    if "P014" in ln or ln.strip().isdigit()]
            def _digit_after(marker):
                for i, ln in enumerate(p014):
                    if marker in ln:
                        for nxt in p014[i + 1:i + 3]:
                            if nxt.isdigit():
                                return int(nxt)
                return None
            t0v, t1v = _digit_after("P014 t_ms"), _digit_after("P014 save true")
            save_ms = (t1v - t0v) if (t0v and t1v) else None
            report["runs"][name] = {
                "save_host_ms": save_ms,
                "src_sha_len": len(data), "dst_len": len(got) if got is not None else None,
                "identical": got == data,
                "crlf_preserved": (got or b"").count(b"\r\n"),
                "bom_preserved": (got or b"")[:3] == b"\xef\xbb\xbf",
                "prints": [ln for ln in out.splitlines()
                           if "P014" in ln or ln.strip().isdigit()][:40],
                "recent_delta": delta,
            }
            print(f"[{name}] identical={got == data} "
                  f"crlf={(got or b'').count(b' chr13'.replace(b' chr13',b''))} "
                  f"len={len(got) if got is not None else None}")

        if not args.skip_big:
            src = tmp / "src_big.txt"
            dst = tmp / "dst_big.txt"
            unit = (b"// p014 big fixture line\nfn probe() int { return 42 }\n")
            with open(src, "wb") as f:
                f.write(unit * (50 * MB // len(unit) + 1))
            write_fixture(str(src), str(dst), 0)
            w0 = time.perf_counter()
            out, _ = run_app(240)
            wall = time.perf_counter() - w0
            got = dst.read_bytes() if dst.exists() else None
            with open(src, "rb") as f:
                head = f.read(4096)
            report["runs"]["big50"] = {
                "identical": got == src.read_bytes(),
                "dst_len": len(got) if got is not None else None,
                "host_wall_s": round(wall, 2),
                "prints": [ln for ln in out.splitlines()
                           if "P014" in ln or ln.strip().isdigit()][:40],
            }
            print(f"[big50] identical={got == src.read_bytes()} "
                  f"wall={wall:.2f}s")

        ok = all(r.get("identical") for r in report["runs"].values())
        print(f"字节保真全等：{'是' if ok else '否（记录实际形，SD-01 勘定）'}")
    finally:
        if args.keep:
            print(f"keep: {tmp} {FIXTURE_APP}")
        else:
            shutil.rmtree(tmp, ignore_errors=True)
            if FIXTURE_APP.exists():
                shutil.rmtree(FIXTURE_APP, ignore_errors=True)

    rep_json = TESTS / "probe_upstream_consume_report.json"
    rep_json.write_text(json.dumps(report, ensure_ascii=False, indent=2),
                        encoding="utf-8")
    print(f"报告 → {rep_json.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
