#!/usr/bin/env python3
"""probe_diffwin.py — PLAN-022 T-01 back 窗口贯通探针（9920 消费面）。

断言族（716 SD-C 边界形对齐 + frozen③ 默认形零扰动）：
  ①默认形逐字节等价：/api/diff_files（9915）envelope 键集恒 8 字段——
    不增 rows_total（上游「不增字段——最严形」），hunks/counts 与窗口形
    全量域一致；
  ②窗口形字段族：/api/diff_files_window rows_total+truncated 激活+
    hunks 全量+rows 窗口物化=全量 rows[offset..offset+limit] 逐行等价；
  ③边界形：offset≥rows_total → rows:[]+truncated=true（total>0）；
    limit 0 → 空+truncated=true；跨 hunk 切片逐行等价。

用法：python tests/probe_diffwin.py   （AUTO_BIN 指 ≥716 工具链）
产出：tests/evidence-p022-t01.json（断言明细+端点原文摘要）。
"""
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)  # specs/auto-edit
AUTO_BIN = os.environ.get("AUTO_BIN") or "auto"


def pick_port(start=9470):
    for port in range(start, start + 60):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    raise RuntimeError("no free port")


def make_fixture(d):
    """散点改对（每 7 行 1 改——hunk 分组随 ctx 间距语义派生，不硬编码）。"""
    a = [f"line {i:03d} probe content" for i in range(30)]
    b = list(a)
    n_changed = 0
    for i in range(0, 30, 7):
        b[i] = f"line {i:03d} CHANGED"
        n_changed += 1
    pa = os.path.join(d, "w.a.txt")
    pb = os.path.join(d, "w.b.txt")
    open(pa, "w", encoding="utf-8", newline="").write("\n".join(a) + "\n")
    open(pb, "w", encoding="utf-8", newline="").write("\n".join(b) + "\n")
    return pa, pb, n_changed


def get(base, path, **params):
    q = urllib.parse.urlencode(params)
    with urllib.request.urlopen(f"{base}{path}?{q}", timeout=30) as resp:
        raw = resp.read().decode("utf-8")
    obj = json.loads(raw)
    if isinstance(obj, str):
        obj = json.loads(obj)
    return obj


def main():
    port = pick_port()
    ad = tempfile.mkdtemp(prefix="p022_t01_appdata_")
    fx = tempfile.mkdtemp(prefix="p022_t01_fx_")
    pa, pb, n_changed = make_fixture(fx)
    env = {**os.environ, "APPDATA": ad, "AUTO_PROJECT_DIR": PROJECT}
    app_log = os.path.join(ad, "app.log")
    log_f = open(app_log, "w")
    proc = subprocess.Popen(
        [AUTO_BIN, "run", "--server", "vm", "-B", str(port)],
        cwd=PROJECT, env=env,
        stdout=log_f, stderr=subprocess.STDOUT)
    checks = []

    def check(name, ok, detail):
        checks.append({"check": name, "ok": bool(ok), "detail": str(detail)[:220]})
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {str(detail)[:120]}")

    base = f"http://127.0.0.1:{port}"
    try:
        up = False
        for _ in range(40):
            try:
                urllib.request.urlopen(base + "/api/ws_root", timeout=2)
                up = True
                break
            except Exception:
                time.sleep(1)
        if not up:
            print("FATAL: app 未起")
            return 1

        full = get(base, "/api/diff_files", path_a=pa, path_b=pb, ctx=3)
        win0 = get(base, "/api/diff_files_window", path_a=pa, path_b=pb,
                   ctx=3, rows_offset=0, rows_limit=5)
        win_mid = get(base, "/api/diff_files_window", path_a=pa, path_b=pb,
                      ctx=3, rows_offset=3, rows_limit=8)
        win_over = get(base, "/api/diff_files_window", path_a=pa, path_b=pb,
                       ctx=3, rows_offset=9999, rows_limit=5)
        win_zero = get(base, "/api/diff_files_window", path_a=pa, path_b=pb,
                       ctx=3, rows_offset=0, rows_limit=0)

        # ① 默认形零扰动：键集恒 8 字段（不增 rows_total）
        n_rows = len(full["rows"])
        keys_full = sorted(full.keys())
        want_keys = sorted(["hunks", "rows", "adds", "dels", "truncated",
                            "degraded", "err"])
        check("①默认形键集恒 8（不增 rows_total）",
              keys_full == want_keys and "rows_total" not in full,
              f"keys={keys_full}")
        check("①默认形计数自洽（adds=dels=散点数+err 空）",
              full["adds"] == n_changed and full["dels"] == n_changed
              and full["err"] == "" and len(full["hunks"]) >= 1,
              f"hunks={len(full['hunks'])} rows={n_rows} "
              f"+{full['adds']}/-{full['dels']} err={full['err']!r}")

        # ② 窗口形字段族
        check("②窗口形键集+rows_total=全量行数+truncated 激活",
              sorted(win0.keys()) == sorted(want_keys + ["rows_total"])
              and win0["rows_total"] == n_rows and win0["truncated"] is True,
              f"keys={sorted(win0.keys())} rows_total={win0.get('rows_total')} "
              f"truncated={win0.get('truncated')}")
        check("②hunks 全量保持（与全量形逐字节等价）",
              win0["hunks"] == full["hunks"] and win0["adds"] == full["adds"]
              and win0["dels"] == full["dels"],
              "hunks/counts 全量域一致")
        check("②rows 窗口物化=全量[0:5] 逐行等价",
              win0["rows"] == full["rows"][0:5],
              f"len(win)={len(win0['rows'])}")
        check("②跨 hunk 切片=全量[3:11] 逐行等价",
              win_mid["rows"] == full["rows"][3:11]
              and win_mid["rows_total"] == n_rows
              and win_mid["truncated"] is True,
              f"len(win)={len(win_mid['rows'])}")

        # ③ 边界形（SD-C：净形+truncated 语义）
        check("③offset≥total → rows:[]+truncated=true",
              win_over["rows"] == [] and win_over["truncated"] is True
              and win_over["rows_total"] == n_rows,
              f"rows={len(win_over['rows'])} truncated={win_over['truncated']}")
        check("③limit 0 → 空+truncated=true（total>0）",
              win_zero["rows"] == [] and win_zero["truncated"] is True,
              f"rows={len(win_zero['rows'])} truncated={win_zero['truncated']}")
    finally:
        log_f.close()
        if proc.poll() is None:
            proc.kill()
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)],
                       capture_output=True)

    ev = {"type": "p022-t01-probe", "fixture": {"a": pa, "b": pb},
          "checks": checks}
    out = os.path.join(HERE, "evidence-p022-t01.json")
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(ev, f, ensure_ascii=False, indent=2)
        f.write("\n")
    bad = [c for c in checks if not c["ok"]]
    print(f"evidence → {out}; {len(checks) - len(bad)}/{len(checks)} PASS")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
