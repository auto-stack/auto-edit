#!/usr/bin/env python3
"""probe_channels.py — PLAN-020 T-00 就绪通道实证探针（决策证据，非基线跑谱）。

对四对象（VS Code / Zed / BC5 / NP++）勘定「打开文件→就绪」的可自动化
通道，每对象双通道以上取离散对照。通道词表：

- ch_title  : 窗口标题含文件名（ctypes EnumWindows 轮询，~5ms 粒度）
- ch_log    : 应用日志行到达（隔离 user-data-dir 日志尾随）
- ch_cpu    : 进程树 CPU 沉降（psutil——峰值后回落 < 阈值）
- ch_exit   : 进程退出码（BC5 脚本/report 通道——退出即结果就绪）
- ch_report : report 文件出现且非空（BC5 file-report 通道）

用法：python probe_channels.py <vscode|zed|bc5|nppp> [--quick]
输出：通道结论行（各通道首命中 ms + 离散），证据落 tools/compare/logs/。

纪律：纯黑盒（仅进程级观察，无竞品安装域写入）；按 PID 树收编，
绝不 taskkill /IM（014 F-RV6 教训——跨会话 /IM 清扫误伤在案）。
"""
from __future__ import annotations

import argparse
import ctypes
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

import psutil
from ctypes import wintypes

HERE = Path(__file__).resolve().parent
LOGS = HERE / "logs"
FIXTURES = HERE / "fixtures"

TARGETS = {
    "vscode": {
        "exe": Path(os.environ["LOCALAPPDATA"]) / "Programs/Microsoft VS Code/Code.exe",
        "product": "Visual Studio Code",
        "version": "1.138.0",
    },
    "zed": {
        "exe": Path(r"D:\soft\zed\Zed.exe"),
        "product": "Zed",
        "version": "1.20.2 (stable.360)",
    },
    "bc5": {
        "exe": Path(r"C:\Program Files\Beyond Compare 5\BCompare.exe"),
        "product": "Beyond Compare 5",
        "version": "5.0.6.30713",
    },
    "nppp": {
        "exe": Path(r"C:\Program Files\Notepad++\notepad++.exe"),
        "product": "Notepad++",
        "version": None,
    },
}

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

ENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)


def _titles_of_pids(pids: set[int]) -> dict[int, str]:
    out: dict[int, str] = {}

    @ENUMPROC
    def cb(hwnd, _l):
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value in pids and user32.IsWindowVisible(hwnd):
            n = user32.GetWindowTextLengthW(hwnd)
            if n:
                buf = ctypes.create_unicode_buffer(n + 1)
                user32.GetWindowTextW(hwnd, buf, n + 1)
                out[pid.value] = buf.value
        return True

    user32.EnumWindows(cb, 0)
    return out


def _tree_pids(root: int) -> set[int]:
    """root 进程 + 后代（VS Code 多进程形态；不跨树）。"""
    pids = {root}
    try:
        for p in psutil.Process(root).children(recursive=True):
            pids.add(p.pid)
    except psutil.Error:
        pass
    return pids


def _kill_tree(pid: int) -> None:
    """按 PID 树收编并等待进程真正退出（taskkill 异步——立即 rmtree 会撞
    文件占用，WinError 32 实勘 2026-09-29）。"""
    subprocess.run(["taskkill", "/PID", str(pid), "/F", "/T"],
                   capture_output=True)
    for _ in range(50):
        if not psutil.pid_exists(pid):
            return
        try:
            if not psutil.Process(pid).is_running():
                return
        except psutil.Error:
            return
        time.sleep(0.1)


def _rm_retry(path: Path, tries: int = 5) -> None:
    for i in range(tries):
        try:
            shutil.rmtree(path)
            return
        except OSError:
            time.sleep(0.2 * (i + 1))
    # 末次：清只读位再试；仍失败则留给 OS temp（不阻塞测量）


def _tree_cpu_pct(pids: set[int], prev: dict[int, float], now: float) -> float:
    """进程树 CPU% 合计（psutil 自上次调用以来；pid 消亡只跳过该 pid——
    树内进程生灭频繁，整轮 except 会把采样面打空，017 探针勘误）。"""
    total = 0.0
    for pid in pids:
        try:
            p = psutil.Process(pid)
            if pid not in prev:
                p.cpu_percent(interval=None)  # 首见只建基线
                prev[pid] = now
                continue
            total += p.cpu_percent(interval=None)
            prev[pid] = now
        except (psutil.Error, OSError):
            continue
    return total


def _probe_open(app: str, fixture: Path, timeout_s: float = 60.0) -> dict:
    """启动 app 打开 fixture，三通道并行轮询，返回各通道首命中 ms。"""
    t = TARGETS[app]
    if not t["exe"].exists():
        return {"app": app, "present": False}
    hits: dict[str, float] = {}
    title_first: dict[str, float] = {}
    cpu_peak = 0.0
    ud = Path(tempfile.mkdtemp(prefix=f"cmp-p020-{app}-"))
    try:
        t0 = time.perf_counter()
        if app == "vscode":
            cmd = [str(t["exe"]), "--user-data-dir", ud, "--disable-extensions",
                   "--disable-crash-reporter", str(fixture)]
        elif app == "zed":
            cmd = [str(t["exe"]), "--user-data-dir", ud, str(fixture)]
        else:
            cmd = [str(t["exe"]), str(fixture)]
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)
        logdir = Path(ud) / "logs"
        prev_cpu: dict[int, float] = {}
        deadline = time.time() + timeout_s
        while time.time() < deadline and proc.poll() is None:
            time.sleep(0.005)
            el = (time.perf_counter() - t0) * 1000.0
            try:
                pids = _tree_pids(proc.pid)
            except psutil.Error:
                continue
            # ch_title
            for pid, title in _titles_of_pids(pids).items():
                if fixture.stem.lower() in title.lower() and "ch_title" not in hits:
                    hits["ch_title"] = el
                    title_first.setdefault(f"{pid}", title)
            # ch_cpu（树 CPU 沉降：峰值后回落）
            c = _tree_cpu_pct(pids, prev_cpu, el)
            cpu_peak = max(cpu_peak, c)
            if cpu_peak > 5.0 and c < cpu_peak * 0.25 and "ch_cpu" not in hits:
                hits["ch_cpu"] = el
            # ch_log（隔离 profile 日志面出现内容——进程树以内的日志落点）
            if "ch_log" not in hits and logdir.exists():
                for lg in logdir.rglob("*.log"):
                    try:
                        if lg.stat().st_size > 0:
                            hits["ch_log"] = el
                            hits["ch_log_file"] = str(lg.relative_to(ud))
                            break
                    except OSError:
                        pass
            # 采齐即停（ch_title 为「窗内见文件」语义主通道；+1 辅通道）
            if "ch_title" in hits and ("ch_log" in hits or "ch_cpu" in hits):
                break
        rc = proc.wait(timeout=5) if proc.poll() is not None else None
        el_end = (time.perf_counter() - t0) * 1000.0
        # 收编前记录末态标题（诊断用）
        end_titles = _titles_of_pids(_tree_pids(proc.pid)) if proc.pid else {}
        _kill_tree(proc.pid)
        # 日志快照留证（通道行词表勘定材料；清理前抢救）
        snap = LOGS / f"snapshot-{app}-{datetime.now():%Y%m%d-%H%M%S}"
        try:
            if logdir.exists():
                shutil.copytree(logdir, snap, dirs_exist_ok=True)
        except OSError:
            pass
        return {"app": app, "present": True, "rc": rc, "hits_ms":
                {k: round(v, 1) for k, v in hits.items() if not k.startswith("ch_log_file")},
                "ch_log_file": hits.get("ch_log_file"),
                "title_sample": title_first or end_titles,
                "cpu_peak_pct": round(cpu_peak, 1),
                "observed_ms": round(el_end, 1),
                "log_snapshot": str(snap) if snap.exists() else None}
    finally:
        _rm_retry(ud)


def _probe_bc(fixture_a: Path, fixture_b: Path) -> dict:
    """BC5 双通道：脚本 file-report（ch_exit+ch_report）与 /silent 交互形。"""
    t = TARGETS["bc5"]
    with tempfile.TemporaryDirectory(prefix="cmp-p020-bc5-") as td:
        report = Path(td) / "report.txt"
        bclog = Path(td) / "bc.log"
        script = Path(td) / "cmp.txt"
        # BC 脚本语法：一条逻辑命令用 & 续行（裸换行=独立命令——首探
        # report 未产出实勘 2026-09-29）；log 行抓 BC 侧自述错误。
        script.write_text(
            f'log verbose "{bclog}"\n'
            f'file-report layout:summary options:line-numbers &\n'
            f'  output-to:"{report}" &\n'
            f'  "{fixture_a}" "{fixture_b}"\n',
            encoding="utf-8")
        t0 = time.perf_counter()
        proc = subprocess.Popen([str(t["exe"]), "/silent", f"@{script}"],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        hits: dict[str, float] = {}
        while proc.poll() is None:
            time.sleep(0.005)
            el = (time.perf_counter() - t0) * 1000.0
            if "ch_report" not in hits and report.exists() and report.stat().st_size > 0:
                hits["ch_report"] = round(el, 1)
        rc = proc.returncode
        el = (time.perf_counter() - t0) * 1000.0
        hits["ch_exit"] = round(el, 1)
        out = {"app": "bc5", "present": True, "rc": rc, "hits_ms": hits,
               "report_present": report.exists()}
        if report.exists():
            out["report_bytes"] = report.stat().st_size
            out["report_head"] = report.read_text(encoding="utf-8",
                                                  errors="replace")[:200]
        if bclog.exists():
            out["bc_log_tail"] = bclog.read_text(encoding="utf-8",
                                                 errors="replace")[-400:]
        return out


def _gen_fixture(path: Path, mb: int) -> None:
    path.parent.mkdir(exist_ok=True)
    if path.exists() and abs(path.stat().st_size - mb * 1048576) < 4096:
        return
    n, written = 0, 0
    with open(path, "w", encoding="utf-8", newline="") as f:
        while written < mb * 1048576:
            for k in range(100):
                line = (f"line {n + k:08d} of p020 probe payload"
                        + (" CHANGED" if k == 0 else ""))
                f.write(line + "\n")
                written += len(line) + 1
            n += 100


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("target", choices=["vscode", "zed", "bc5", "nppp"])
    ap.add_argument("--quick", action="store_true", help="1MB 探针档（默认 5MB）")
    ap.add_argument("--mb", type=int, default=None, help="显式探针档大小 MB")
    args = ap.parse_args()
    LOGS.mkdir(exist_ok=True)
    t = TARGETS[args.target]
    if not t["exe"].exists():
        extra = [Path(os.environ["LOCALAPPDATA"]) / "Programs/Notepad++/notepad++.exe"]
        print(f"== {args.target}: 缺位（{t['exe']} 不存在"
              f"{'' if not any(e.exists() for e in extra) else '，备用位亦缺'}）")
        return 1
    mb = args.mb or (1 if args.quick else 5)
    if args.target == "bc5":
        a = FIXTURES / f"probe-{mb}mb-a.txt"
        b = FIXTURES / f"probe-{mb}mb-b.txt"
        _gen_fixture(a, mb)
        _gen_fixture(b, mb)
        b.write_text(b.read_text(encoding="utf-8").replace("CHANGED", "CHANGED2"),
                     encoding="utf-8", newline="")
        r = _probe_bc(a, b)
    else:
        fx = FIXTURES / f"probe-{mb}mb.txt"
        _gen_fixture(fx, mb)
        r = _probe_open(args.target, fx)
    print(json.dumps(r, ensure_ascii=False, indent=1))
    ev = LOGS / f"probe-{args.target}-{datetime.now():%Y%m%d-%H%M%S}.json"
    ev.write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"证据 → {ev}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
