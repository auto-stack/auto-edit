#!/usr/bin/env python3
"""compare.py — PLAN-020 竞品同机测量 harness（G-2）。

bench.py 先例形态复用（环境指纹/JSONL/报告器）。四对象计时通道按
tools/compare/METHODOLOGY.md §2 定案：

  vscode  t_ready=renderer RSS 平台（文本模型物化）  备=窗标题（tab 建立）
  zed     t_ready=Zed.log "Rendered first frame"     备=窗标题
  bc5     t_ready=file-report 非空（结果产出）        备=进程退出
  nppp    缺位 pending（装后同 vscode 形——§10 Q-1）

用法：
  python tools/compare/compare.py check              # 在位性+版本+通道自检
  python tools/compare/compare.py run <对象> <档> [-n N]
      对象: vscode|zed|bc5|nppp    档: 5mb|100mb（bc5=diff 对档）
  python tools/compare/compare.py report [结果glob]  # median+离散表（三要素门）

纪律：fresh profile per run；沉降窗 5s（fixture 生成后）；taskkill 按
PID 树（禁 /IM，014 教训）；竞品纯黑盒（自建 temp，零安装域写入）。
数字入表三要素={版本钉版, 环境指纹, 跑谱+离散}——report 缺一拒出数。
"""
from __future__ import annotations

import argparse
import ctypes
import ctypes.wintypes as wt
import json
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from collections import deque
from datetime import datetime
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
FIXTURES = HERE / "fixtures"
RESULTS = HERE / "results"

EXIT_OK, EXIT_FAIL = 0, 1

ZED_FRAME_LINE = "Rendered first frame"


def _log(msg: str) -> None:
    print(f"[compare {datetime.now():%H:%M:%S}] {msg}", flush=True)


def _ts() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


# ---------------------------------------------------------------- 对象注册表

def _vscode_exe() -> Path:
    return Path(os.environ.get("CMP_VSCODE_EXE") or
                Path(os.environ["LOCALAPPDATA"]) / "Programs/Microsoft VS Code/Code.exe")


def _zed_exe() -> Path:
    return Path(os.environ.get("CMP_ZED_EXE") or r"D:\soft\zed\Zed.exe")


def _bc5_exe() -> Path:
    return Path(os.environ.get("CMP_BC5_EXE") or
                r"C:\Program Files\Beyond Compare 5\BCompare.exe")


def _nppp_exe() -> Path:
    for cand in (os.environ.get("CMP_NPPP_EXE"),
                 r"C:\Program Files\Notepad++\notepad++.exe",
                 str(Path(os.environ.get("LOCALAPPDATA", "")) / "Programs/Notepad++/notepad++.exe")):
        if cand and Path(cand).exists():
            return Path(cand)
    return Path(r"C:\Program Files\Notepad++\notepad++.exe")


def _ver_from_powershell(path: Path, prop: str = "ProductVersion") -> str | None:
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             f"(Get-Item '{path}').VersionInfo.{prop}"],
            capture_output=True, text=True, timeout=30).stdout.strip()
        return out or None
    except Exception:  # noqa: BLE001
        return None


TARGETS = {
    "vscode": {"label": "Visual Studio Code", "exe": _vscode_exe,
               "tiers": ("5mb", "100mb")},
    "zed": {"label": "Zed", "exe": _zed_exe, "tiers": ("5mb", "100mb")},
    "bc5": {"label": "Beyond Compare 5", "exe": _bc5_exe, "tiers": ("5mb", "100mb")},
    "nppp": {"label": "Notepad++", "exe": _nppp_exe, "tiers": ("5mb", "100mb")},
}


def _probe_version(target: str) -> str | None:
    """版本钉版通道：VS Code/Zed/BC5=exe 文件元数据（ProductVersion/
    FileVersion）；**VS Code 禁 CLI `--version` 通道**——直启 GUI 臂
    挂起 63s 实勘（2026-09-29），且 bash 包装器在自更新中间态报陈旧
    版本（1.138.0 vs 实际 1.139.1——METHODOLOGY §1 注记）。"""
    exe = TARGETS[target]["exe"]()
    if not exe.exists():
        return None
    if target == "zed":
        return _ver_from_powershell(exe, "ProductVersion")
    return _ver_from_powershell(exe, "FileVersion")


# ---------------------------------------------------------------- 环境指纹

def _fingerprint() -> dict:
    try:
        cpu = platform.processor() or "unknown"
    except Exception:  # noqa: BLE001
        cpu = "unknown"
    return {"os": f"{platform.system()} {platform.release()} build {platform.version()}",
            "machine": socket.gethostname(),
            "cpu": cpu, "cpu_cores": os.cpu_count(),
            "ram_gb": round(psutil.virtual_memory().total / 2**30, 1),
            "python": platform.python_version()}


# ---------------------------------------------------------------- fixture（018 同源参数）

def _gen_fixture(path: Path, mb: int) -> float:
    """018 bench open 档同参数生成式：重复行行体唯一化+每 100 行 1 行
    CHANGED 散点（1% 散布）；UTF-8 LF。行体标识字串 p020（载荷字面
    差异对 plain 旁路臂装载零影响——METHODOLOGY §4 注记）。"""
    t0 = time.perf_counter()
    target = mb * 1024 * 1024
    n = written = 0
    with open(path, "w", encoding="utf-8", newline="") as f:
        while written < target:
            for k in range(100):
                line = (f"line {n + k:08d} of p020 compare payload"
                        + (" CHANGED" if k == 0 else ""))
                f.write(line + "\n")
                written += len(line) + 1
            n += 100
    return time.perf_counter() - t0


def _ensure_fixtures(tier: str, target: str) -> dict:
    """档位 fixture 就位+沉降窗 5s（writeback 计时卫生，016/018 纪律）。
    bc5=diff 对（b 侧=CHANGED→CHANGED2 全替换，同 1% 散点谱）。
    返回值全 JSON 可序列化（路径=str——头行直写）。"""
    FIXTURES.mkdir(exist_ok=True)
    mb = int(tier.replace("mb", ""))
    a = FIXTURES / f"compare-open-{tier}.txt"
    meta = {"tier": tier, "mb": mb, "path": str(a),
            "params": "重复行唯一化+1% CHANGED 散点；UTF-8 LF（018 同源参数）"}
    gen = False
    if not a.exists() or abs(a.stat().st_size - mb * 2**20) > 2**20:
        gen = True
        _gen_fixture(a, mb)
    if target == "bc5":
        b = FIXTURES / f"compare-diff-{tier}-b.txt"
        if gen or not b.exists() or abs(b.stat().st_size - mb * 2**20) > 2**20:
            b.write_text(a.read_text(encoding="utf-8").replace("CHANGED", "CHANGED2"),
                         encoding="utf-8", newline="")
            gen = True
        meta["b_side"] = str(b)
        meta["diff_spec"] = "b=a 且 CHANGED→CHANGED2（1% 散点差异谱）"
        if gen:
            _log(f"fixture 对生成（{tier}）——沉降窗 5s")
            time.sleep(5.0)
        return meta
    if gen:
        _log(f"fixture 生成（{tier}）——沉降窗 5s")
        time.sleep(5.0)
    return meta


# ---------------------------------------------------------------- 窗口/进程通道

user32 = ctypes.windll.user32


def _titles_of_pids(pids: set[int]) -> dict[int, str]:
    out: dict[int, str] = {}

    TCB = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

    @TCB
    def cb(hwnd, _l):
        pid = wt.DWORD()
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


def _tree(root_pid: int) -> set[int]:
    pids = {root_pid}
    try:
        for c in psutil.Process(root_pid).children(recursive=True):
            pids.add(c.pid)
    except psutil.Error:
        pass
    return pids


def _kill_tree(pid: int) -> None:
    subprocess.run(["taskkill", "/PID", str(pid), "/F", "/T"],
                   capture_output=True)
    for _ in range(50):
        try:
            if not psutil.Process(pid).is_running():
                return
        except psutil.Error:
            return
        time.sleep(0.1)


def _renderer_rss_mb(root: psutil.Process) -> tuple[int, bool]:
    """(renderer RSS MB, renderer_found)；无 renderer 退化全树和。"""
    total = 0
    found = False
    try:
        for c in root.children(recursive=True):
            try:
                cl = " ".join(c.cmdline() or [])
            except (psutil.Error, OSError):
                continue
            if "type=renderer" in cl:
                found = True
                total += c.memory_info().rss
    except psutil.Error:
        pass
    if total == 0:
        try:
            total = root.memory_info().rss
        except psutil.Error:
            pass
    return total // 2**20, found


# ---------------------------------------------------------------- 对象跑法

def _run_editor(target: str, fixture: Path, timeout_s: float,
                tier: str = "5mb") -> dict:
    """VS Code/Zed/NP++ 打开计时：fresh profile per run，通道轮询 ~5ms。"""
    exe = TARGETS[target]["exe"]()
    ud = Path(tempfile.mkdtemp(prefix=f"cmp-{target}-"))
    t_ready = t_backup = None
    notes: list[str] = []
    rss_series: deque[tuple[float, int]] = deque()  # 时间窗 1.5s（按时刻裁剪）
    RSS_WINDOW_MS = 1500.0
    # 确认窗分档：100MB 档装载爬升中段存在 >3s 平坦段（会骗过 3s 确认
    # ——首测 run0 假命中 4.7s vs 实续爬升 ~12s，2026-09-29 勘定），
    # 取 6s；5MB 档 3s。判据语义整体偏竞品有利侧（假平台只会低估竞品
    # 打开时长——公开对比保守侧，方法论 §2 注记）。
    PLATEAU_CONFIRM_MS = 6000.0 if tier == "100mb" else 3000.0
    plateau_start: float | None = None
    plateau_rss = 0
    renderer_found = False
    try:
        if target == "vscode":
            cmd = [str(exe), "--user-data-dir", str(ud), "--disable-extensions",
                   "--disable-crash-reporter", str(fixture)]
        elif target == "zed":
            cmd = [str(exe), "--user-data-dir", str(ud), str(fixture)]
        else:  # nppp（装后勘定形——同 vscode 形注记）
            cmd = [str(exe), str(fixture)]
        t0 = time.perf_counter()
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)
        try:
            root = psutil.Process(proc.pid)
        except psutil.Error:
            root = None
        prev_rss = None
        prev_cpu: dict[int, float] = {}
        cpu_peak = 0.0
        deadline = t0 + timeout_s
        while time.perf_counter() < deadline and proc.poll() is None:
            time.sleep(0.005)
            el = (time.perf_counter() - t0) * 1000.0
            pids = _tree(proc.pid) if root else set()
            # 备通道：窗标题含文件名
            if t_backup is None and fixture.stem.lower() in str(
                    _titles_of_pids(pids)).lower():
                t_backup = el
            if target == "vscode":
                # 主通道：renderer RSS 平台（METHODOLOGY §2）。
                # 判据=1.5s 滑窗极差达标（平台候选）+ **3s 确认窗无再增长**
                # （分块装载的间歇停顿会制造假平台——100MB 首测 6.5s 假
                # 命中 vs 手工探针爬升实续至 ~12s，2026-09-29 勘定；
                # 再增长超阈值=装载恢复→候选作废重来）。窗口裁剪留
                # 1.2× 余量防 >= 判据永假（两连 miss 实勘同日）。
                if root:
                    rss, renderer_found = _renderer_rss_mb(root)
                    rss_series.append((el, rss))
                    while rss_series and el - rss_series[0][0] > RSS_WINDOW_MS * 1.2:
                        rss_series.popleft()
                    peak = max(r for _, r in rss_series)
                    lo = min(r for _, r in rss_series)
                    window_ok = (peak - lo < max(8, peak * 0.02)
                                 and len(rss_series) >= 2
                                 and (el - rss_series[0][0]) >= RSS_WINDOW_MS)
                    tol = max(8, peak * 0.02)
                    if window_ok:
                        if plateau_start is None:
                            plateau_start = rss_series[0][0]
                            plateau_rss = lo
                        if rss > plateau_rss + tol:
                            plateau_start = rss_series[0][0]  # 再增长=装载恢复
                            plateau_rss = lo
                        elif (t_ready is None
                              and el - plateau_start >= PLATEAU_CONFIRM_MS):
                            t_ready = plateau_start
                    else:
                        plateau_start = None
            elif target == "zed":
                # 主通道：Zed.log 帧行到达
                lf = ud / "logs" / "Zed.log"
                if t_ready is None and lf.exists():
                    try:
                        if ZED_FRAME_LINE in lf.read_text(encoding="utf-8",
                                                           errors="replace"):
                            t_ready = el
                    except OSError:
                        pass
            else:  # nppp：装后勘定——暂以标题为主通道占位
                if t_ready is None and t_backup is not None:
                    t_ready = el
            # 诊断对照：CPU 沉降（METHODOLOGY §2——不作计时）
            try:
                c = 0.0
                for pid in pids:
                    try:
                        p = psutil.Process(pid)
                        if pid not in prev_cpu:
                            p.cpu_percent(interval=None)
                            prev_cpu[pid] = el
                            continue
                        c += p.cpu_percent(interval=None)
                        prev_cpu[pid] = el
                    except (psutil.Error, OSError):
                        continue
                cpu_peak = max(cpu_peak, c)
            except (psutil.Error, OSError):
                pass
            # 采齐早停：主+备双命中再保温 1s（RSS 窗需要后续样本）
            if (t_ready is not None and t_backup is not None
                    and el - max(t_ready, t_backup) > 1000):
                break
        rc = proc.poll()
        rss_end = _renderer_rss_mb(root)[0] if root else None
    finally:
        _kill_tree(proc.pid)
        for _ in range(5):
            try:
                shutil.rmtree(ud)
                break
            except OSError:
                time.sleep(0.4)
    return {"t_ready_ms": round(t_ready, 1) if t_ready is not None else None,
            "t_backup_ms": round(t_backup, 1) if t_backup is not None else None,
            "rss_end_mb": rss_end, "renderer_found": renderer_found,
            "cpu_peak_pct": round(cpu_peak, 1), "rc": rc,
            "notes": notes}


def _run_bc5(a: Path, b: Path, timeout_s: float) -> dict:
    """BC5 diff 计时：file-report 脚本通道（`&` 续行+/silent）。"""
    exe = TARGETS["bc5"]["exe"]()
    td = Path(tempfile.mkdtemp(prefix="cmp-bc5-"))
    t_ready = None
    try:
        report = td / "report.txt"
        script = td / "cmp.txt"
        script.write_text(
            f'file-report layout:summary options:line-numbers &\n'
            f'  output-to:"{report}" &\n'
            f'  "{a}" "{b}"\n', encoding="utf-8")
        t0 = time.perf_counter()
        proc = subprocess.Popen([str(exe), "/silent", f"@{script}"],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        while proc.poll() is None and time.perf_counter() - t0 < timeout_s:
            time.sleep(0.005)
            el = (time.perf_counter() - t0) * 1000.0
            if t_ready is None and report.exists() and report.stat().st_size > 0:
                t_ready = el
        rc = proc.returncode if proc.poll() is not None else None
        t_exit = round((time.perf_counter() - t0) * 1000.0, 1)
    finally:
        _kill_tree(proc.pid)
        for _ in range(5):
            try:
                shutil.rmtree(td)
                break
            except OSError:
                time.sleep(0.4)
    return {"t_ready_ms": round(t_ready, 1) if t_ready is not None else None,
            "t_backup_ms": t_exit, "rc": rc,
            "notes": [] if rc == 0 else [f"rc={rc}（0=脚本完成）"]}


# ---------------------------------------------------------------- run/report/check

TIMEOUT_S = {("vscode", "5mb"): 60.0, ("vscode", "100mb"): 90.0,
             ("zed", "5mb"): 45.0, ("zed", "100mb"): 60.0,
             ("bc5", "5mb"): 120.0, ("bc5", "100mb"): 600.0,
             ("nppp", "5mb"): 60.0, ("nppp", "100mb"): 90.0}

TIMING_POINT_ID = {
    "vscode": "t_ready=renderer_rss_plateau（文本模型物化——METHODOLOGY §2）",
    "zed": "t_ready=zed_log_first_frame（首帧渲染）",
    "bc5": "t_ready=report_nonempty（diff 结果产出）",
    "nppp": "t_ready=title（pending——装后勘定形）",
}


def stage_check() -> int:
    fp = _fingerprint()
    _log(f"环境指纹：{json.dumps(fp, ensure_ascii=False)}")
    bad = []
    for t in TARGETS:
        exe = TARGETS[t]["exe"]()
        present = exe.exists()
        ver = _probe_version(t) if present else None
        tiers = ",".join(TARGETS[t]["tiers"])
        _log(f"  {t:6} present={present} version={ver} exe={exe} tiers={tiers}")
        if t == "nppp":
            _log("         注记：NP++ 缺位=pending 列（§10 Q-1 用户面），不阻塞判绿")
        elif not present:
            bad.append(t)
    if bad:
        _log(f"FATAL: 必需对象缺位：{bad}")
        return EXIT_FAIL
    return EXIT_OK


def stage_run(target: str, tier: str, runs: int) -> int:
    if target not in TARGETS:
        _log(f"FATAL: 未知对象 {target}")
        return EXIT_FAIL
    if tier not in TARGETS[target]["tiers"]:
        _log(f"FATAL: {target} 无档 {tier}（可用 {TARGETS[target]['tiers']}）")
        return EXIT_FAIL
    if runs < 2:
        _log("FATAL: --runs 至少 2（首跑弃暖机语义，018 纪律）")
        return EXIT_FAIL
    exe = TARGETS[target]["exe"]()
    if not exe.exists():
        _log(f"FATAL: {target} 缺位（{exe}）——NP++ 安装=用户面 §10 Q-1")
        return EXIT_FAIL
    version = _probe_version(target)
    if not version:
        _log("FATAL: 版本钉版读取失败（三要素缺一）")
        return EXIT_FAIL
    RESULTS.mkdir(exist_ok=True)
    fx = _ensure_fixtures(tier, target)
    rows = []
    walls = []
    for i in range(runs):
        # invalid-run 重跑条款（014 F-RV6 纪律延展）：进程在通道命中前
        # 自退（VS Code 间歇 rc=0 自退出现象，2026-09-29 实勘谱）=该跑
        # 无效，换 fresh profile 立即重试一次；连续两跑无效=环境干扰
        # 升级，abort 示知（并行会话清扫嫌疑——F-RV6 归因条款）。
        for attempt in (0, 1):
            if target == "bc5":
                r = _run_bc5(Path(fx["path"]), Path(fx["b_side"]),
                             TIMEOUT_S[(target, tier)])
            else:
                r = _run_editor(target, Path(fx["path"]),
                                TIMEOUT_S[(target, tier)], tier=tier)
            ok = r["t_ready_ms"] is not None
            if ok or target == "bc5":
                break
            r["notes"] = r.get("notes", []) + [
                f"attempt{attempt}: 通道未命中即退出（rc={r.get('rc')}）——"
                "invalid-run 重跑条款" + ("；连续两跑无效=环境干扰升级"
                                          if attempt else "")]
            _log(f"  run{i} attempt{attempt}: 无效（rc={r.get('rc')}）——重试")
        if not ok:
            _log("FATAL: 连续两跑无效=环境干扰升级（F-RV6 归因：先查并行"
                 "会话清扫/watcher 双证，非盲重跑）——abort 示知用户")
            return EXIT_FAIL
        warmup = i == 0
        if ok and not warmup:
            walls.append(r["t_ready_ms"])
        rows.append({"type": "run", "run": i, "warmup": warmup,
                     "t_ready_ms": r["t_ready_ms"],
                     "t_backup_ms": r.get("t_backup_ms"),
                     "rss_end_mb": r.get("rss_end_mb"),
                     "renderer_found": r.get("renderer_found"),
                     "cpu_peak_pct": r.get("cpu_peak_pct"),
                     "rc": r.get("rc"), "notes": r["notes"]})
        _log(f"  run{i}{'(暖机弃)' if warmup else ''}: t_ready={r['t_ready_ms']}ms"
             f" 备={r.get('t_backup_ms')}ms")
        time.sleep(2.0)  # 跑间沉降（桌面态回稳）
    med = sorted(walls)[len(walls) // 2] if walls else None
    rows.append({"type": "summary", "runs_ms": walls, "median_ms": med,
                 "min_ms": min(walls) if walls else None,
                 "max_ms": max(walls) if walls else None,
                 "note": "首跑弃暖机；t_ready 语义见头行 timing_point；"
                         "median=N//2 上中位（METHODOLOGY §5 frozen 约定，"
                         "bench.py 家法）"})
    head = {"type": "compare_head", "target": target,
            "label": TARGETS[target]["label"], "version": version,
            "exe": str(TARGETS[target]["exe"]()),
            "tier": tier, "fixture": fx, "runs": runs,
            "timing_point": TIMING_POINT_ID[target],
            "fingerprint": _fingerprint(),
            "started": datetime.now().isoformat(timespec="seconds"),
            "tool_note": "fresh profile per run（编辑器）；竞品纯黑盒"}
    outfile = RESULTS / f"compare-{target}-{tier}-{_ts()}.jsonl"
    with open(outfile, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(head, ensure_ascii=False) + "\n")
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    _log(f"结果 JSONL → {outfile}")
    _log(f"{target} {tier} 谱：{walls} median={med}ms")
    bad = [r["run"] for r in rows if r["type"] == "run"
           and r["t_ready_ms"] is None]
    if bad:
        _log(f"FATAL: 通道未命中跑次：{bad}（METHODOLOGY §2 通道定义）")
        return EXIT_FAIL
    return EXIT_OK


def stage_report(pattern: str | None) -> int:
    """median+离散表；三要素门（版本+指纹+跑谱缺一拒出数）。"""
    RESULTS.mkdir(exist_ok=True)
    files = sorted(RESULTS.glob(pattern or "compare-*.jsonl"))
    if not files:
        _log("FATAL: results/ 无 compare JSONL——先 run")
        return EXIT_FAIL
    print("| 对象 | 版本 | 档 | N(计入) | median ms（N//2 上中位——"
          "METHODOLOGY §5 frozen 约定，bench.py 家法） | min–max ms | 离散注记 |")
    print("|---|---|---|---|---|---|---|")
    refused = []
    for fp_ in files:
        head = None
        runs, summary = [], None
        for line in open(fp_, encoding="utf-8"):
            r = json.loads(line)
            if r["type"] == "compare_head":
                head = r
            elif r["type"] == "summary":
                summary = r
            elif r["type"] == "run":
                runs.append(r)
        if not head or not summary:
            refused.append((fp_.name, "头/摘要行缺"))
            continue
        if not head.get("version") or not head.get("fingerprint") \
                or not summary.get("runs_ms"):
            refused.append((fp_.name, "三要素缺一（版本/指纹/跑谱）"))
            continue
        print(f"| {head['label']} | {head['version']} | {head['tier']} "
              f"| {len(summary['runs_ms'])} | {summary['median_ms']} "
              f"| {summary['min_ms']}–{summary['max_ms']} "
              f"| {'首跑弃暖机' if any(r['warmup'] for r in runs) else '—'} |")
    for name, why in refused:
        _log(f"  拒出数：{name}（{why}）")
    return EXIT_OK if not refused else EXIT_FAIL


def main() -> int:
    ap = argparse.ArgumentParser(description="PLAN-020 竞品同机测量 harness")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check")
    p_run = sub.add_parser("run")
    p_run.add_argument("target", choices=sorted(TARGETS))
    p_run.add_argument("tier", choices=["5mb", "100mb"])
    p_run.add_argument("-n", "--runs", type=int, default=5)
    p_rep = sub.add_parser("report")
    p_rep.add_argument("pattern", nargs="?", default=None)
    args = ap.parse_args()
    if args.cmd == "check":
        return stage_check()
    if args.cmd == "run":
        return stage_run(args.target, args.tier, args.runs)
    return stage_report(args.pattern)


if __name__ == "__main__":
    sys.exit(main())
