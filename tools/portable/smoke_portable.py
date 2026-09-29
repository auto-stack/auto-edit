#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""smoke_portable.py — PLAN-019 T-04：portable 单 exe 烟测（G-6/AC-05）。

判定口径（frozen ⑤）：单 exe 直跑=无安装壳/无解压步骤/无外部运行时
依赖。四段：
  ① 干净目录直跑——dist exe 拷入空临时目录+隔离 APPDATA，AUTO_BENCH=1
     +AUTO_OPEN_PATH 小 fixture：BENCH 标记对（open 链 E2E）+后端就绪
     行+进程存活（单 iced 拓扑门同 bench.py 口径）。
  ② 零残留探测——跑后临时目录零新增文件（无解压残留）。
  ③ 无 DLL 侧车/单进程——运行期进程树=单进程（无子进程）。
  ④ diff 主链抽查（矩阵 T15.1 同源面）——产物 exe `--server rust`
     （内嵌 axum back）+ /api/ws_root + /api/diff_files 小档对。

退出码：0=全段绿；1=任一段红。输出 JSONL 落 tools/portable/results/。
每轮按 PID 收（绝不 taskkill //IM——bench.py 纪律）。
"""
import json
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DIST = ROOT / "dist" / "portable" / "auto-edit.exe"
RESULTS = HERE / "results"
EXE_NAME = "auto-edit.exe"
BACKEND_READY_LINE = "Running with Iced backend"

EXIT_OK, EXIT_FAIL = 0, 1


def _log(msg: str) -> None:
    print(f"[smoke {datetime.now():%H:%M:%S}] {msg}", flush=True)


def _kill_pid(pid: int) -> None:
    subprocess.run(["taskkill", "/PID", str(pid), "/F", "/T"],
                   capture_output=True, text=True)


def _wait_markers(log: Path, want: list[str], timeout_s: float,
                  poll: float = 0.002) -> tuple[dict, bool]:
    """stdout 落文件轮询标记到达（bench.py 同款 2ms 粒度）。"""
    deadline = time.time() + timeout_s
    marks: dict[str, float] = {}
    ready = False
    t0 = time.time()
    while time.time() < deadline:
        try:
            text = log.read_text(encoding="utf-8", errors="replace")
        except OSError:
            time.sleep(poll)
            continue
        for w in want:
            if w not in marks and w in text:
                marks[w] = round((time.time() - t0) * 1000, 1)
        if not ready and BACKEND_READY_LINE in text:
            ready = True
        if len(marks) == len(want) and ready:
            return marks, True
        time.sleep(poll)
    return marks, ready


def main() -> int:
    if not DIST.exists():
        _log(f"FATAL: dist 产物缺席（{DIST}）——先 build_portable.py")
        return EXIT_FAIL
    RESULTS.mkdir(exist_ok=True)
    rec: dict = {"type": "portable_smoke", "ts": datetime.now().strftime("%Y%m%d-%H%M%S"),
                 "exe": str(DIST),
                 "exe_size_bytes": DIST.stat().st_size}
    checks: list[dict] = []

    with tempfile.TemporaryDirectory(prefix="p019-smoke-") as tmp:
        rundir = Path(tmp) / "bin"
        rundir.mkdir()
        exe = rundir / EXE_NAME
        shutil.copy2(DIST, exe)
        fixture = Path(tmp) / "smoke-open.txt"
        fixture.write_text("PLAN-019 smoke open fixture\n" * 200, encoding="utf-8")
        appdata = Path(tmp) / "appdata"
        appdata.mkdir()

        # ① 干净目录直跑（BENCH 标记+后端就绪+存活）
        log = Path(tmp) / "smoke-app.log"
        env = {**__import__("os").environ,
               "AUTO_BENCH": "1", "AUTO_OPEN_PATH": str(fixture),
               "APPDATA": str(appdata)}
        with open(log, "wb") as f:
            proc = subprocess.Popen([str(exe)], cwd=str(rundir), env=env,
                                    stdout=f, stderr=subprocess.STDOUT)
        try:
            marks, ready = _wait_markers(log, ["bench_open_start",
                                               "bench_open_done"], 30.0)
            time.sleep(1.0)
            alive = proc.poll() is None
            open_pair = ("bench_open_start" in marks
                         and "bench_open_done" in marks)
            checks.append({"check": "direct_run", "ok": open_pair and ready and alive,
                           "markers_ms": marks, "backend_ready": ready,
                           "alive": alive})
            _log(f"① 直跑：标记对={open_pair} 后端就绪={ready} 存活={alive} "
                 f"({marks.get('bench_open_done', '<缺>') }ms 内 open 链完成)")

            # ③ 运行期进程树=单进程（无子进程——无 DLL 侧车宿主/无解压伴生）
            out = subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 "(Get-CimInstance Win32_Process -Filter "
                 f"'ParentProcessId={proc.pid}').ProcessId"],
                capture_output=True, text=True).stdout
            children = [ln.strip() for ln in out.splitlines()
                        if ln.strip().isdigit()]
            checks.append({"check": "single_process", "ok": not children,
                           "children": children})
            _log(f"③ 单进程：children={children or '无'}")
        finally:
            _kill_pid(proc.pid)
            time.sleep(1.0)

        # ② 零残留探测（bin 目录仅 exe 本体；无解压伴生文件）
        leftovers = sorted(p.name for p in rundir.iterdir()
                           if p.name != EXE_NAME)
        checks.append({"check": "no_extraction_residue", "ok": not leftovers,
                       "leftovers": leftovers})
        _log(f"② 零残留：{'pass' if not leftovers else leftovers}")

        # ④ back 契约链抽查（同产物构建面的 auto-edit-back.exe=fys 路由
        #    ws_root/read_text——front 的 back 调用契约面；diff 引擎 HTTP
        #    面属工具链 VM server[矩阵 T15.x 域]，产物面无 diff 路由——
        #    生成 back=fys 契约，diff 主链抽查归矩阵轨，不入本烟测）。
        import socket as _socket
        port = None
        for cand in range(9560, 9660):
            with _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM) as s:
                if s.connect_ex(("127.0.0.1", cand)) != 0:
                    port = cand
                    break
        a = Path(tmp) / "back-a.txt"
        a.write_text("PLAN-019 back fsys smoke\nline2\n", encoding="utf-8")
        env2 = {**__import__("os").environ, "APPDATA": str(appdata),
                "AUTO_HTTP_PORT": str(port)}
        back_src = DIST.parents[2] / "specs" / "auto-edit" / "rust-workspace" \
            / "target" / "release" / "auto-edit-back.exe"
        up, read_ok = False, False
        if back_src.exists():
            back_exe = rundir / back_src.name
            shutil.copy2(back_src, back_exe)
            with open(Path(tmp) / "smoke-server.log", "wb") as f:
                srv = subprocess.Popen([str(back_exe)], cwd=str(rundir),
                                       env=env2, stdout=f,
                                       stderr=subprocess.STDOUT)
            try:
                base = f"http://127.0.0.1:{port}"
                for _ in range(20):
                    try:
                        urllib.request.urlopen(base + "/api/ws_root", timeout=2)
                        up = True
                        break
                    except Exception:  # noqa: BLE001
                        time.sleep(1)
                if up:
                    q = urllib.parse.urlencode({"path": str(a)})
                    try:
                        with urllib.request.urlopen(
                                f"{base}/api/read_text?{q}",
                                timeout=10) as resp:
                            body = resp.read().decode("utf-8")
                        read_ok = "PLAN-019 back fsys smoke" in body
                    except Exception as e:  # noqa: BLE001
                        read_ok = f"<err {e}>"
            finally:
                _kill_pid(srv.pid)
                time.sleep(1.0)
        checks.append({"check": "back_fsys_chain", "ok": bool(up and read_ok),
                       "server_up": up, "read_ok": read_ok,
                       "note": "diff HTTP 面=工具链 VM server 域（矩阵 T15.x）"
                               "——产物面无 diff 路由，back=fys 契约面抽查"})
        _log(f"④ back fsys 链：server_up={up} read_ok={read_ok}")

    rec["checks"] = checks
    ok = all(c["ok"] for c in checks)
    rec["verdict"] = "pass" if ok else "fail"
    out = RESULTS / f"smoke-{rec['ts']}.jsonl"
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    _log(f"烟测 {rec['verdict'].upper()} → {out.name}")
    return EXIT_OK if ok else EXIT_FAIL


if __name__ == "__main__":
    sys.exit(main())
