#!/usr/bin/env python3
"""PLAN-013 T-00 大文件模式探针（决策件）——50MB 档探测/命令风险/阈值/plain 旁路.

五项（计划 §5 T-00；决策记录落计划 §10 Q-1..Q-3）：
  ① wrap 现状：静态勘定（kernel builder 默认 wrap:false + 现视图未绑 wrap
     ——view.rs:1921/app.at 无绑定）=「关折行」零动作注记；报告记录，无活体项。
  ② 探测时点裁定：活体=50/100MB auto 载入基线（loaded_bytes+载入 ms+RSS）；
     静态=RunPendingLoad 同 handler 原子性（big 置位先于 load_file 完成 →
     装载后首帧即模式态）+ apply_config 逐字段 diff 热应用（lang/wrap prop
     更新生效，mod.rs apply_config_locked）——裁定 **pre-load**（RunPendingLoad
     装载前门 file_size：超大拒绝先于 rope 分配；OpenPath/恢复链统一单点）。
     Phase A=/api/file_size 端点形（T-01 后补验；--skip-a 跳过）。
  ③ 全文本命令风险：50MB fixture 上 ReplaceAll 全管线（code_editor_text 读出
     →back regex_replace→edit 回写）+ WriteFidelity（save：读出+包装+write_text）
     ——EolConvert 同形（读出+Str.replace+edit）传递注记（菜单项 menubar-sub
     MCP 失明=T12.6 已知上游缺，不可驱动）；观察步墙/超时/RSS——护栏实证。
  ④ 阈值：200MB 载入 RSS/时长 → 超大拒绝位定参（预判 512MB；687 锚
     100MB→219MB RSS ≈2.2× 外推 512MB→~1.1GB）。
  ⑤ plain 旁路：静态=lang_to_extension 白名单 plain/none/""→None（bypass
     syntect+syntax_by_extension 跳过；warm_language 兜底 warm txt=无害常数）
     + apply_config lang_changed 同 buffer 重建语义；活体=auto 基线计时
     （plain 侧对照=T-04 bench mode on/off 档）。

用法：cd specs/auto-edit/tests && python probe_bigfile.py [--skip-a] [--keep-fixtures]
前置同 desktop_mcp.py（requests、AUTO_BIN 或 PATH 的 auto；psutil 可选——
缺席时 RSS 字段记 None）。fixtures 生成于组目录 probe_fixtures/（不入库）。
报告：probe_bigfile_report.{json,txt}（probe_diff_report 同款惯例）。
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from desktop_mcp import (  # noqa: E402
    McpClient, wait_for_server, pick_free_port, _kill_proc_tree,
    find_button_by_text, state_int, state_str, state_bool,
)

AUTO_BIN = os.environ.get("AUTO_BIN") or shutil.which("auto") or ""
PROJECT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
# fixtures 落组目录（worktree 外、仓外——不入库面；merge 期随组目录清理）。
FIXDIR = os.path.abspath(os.path.join(PROJECT, "..", "..", "..", "probe_fixtures"))
MB = 1024 * 1024
THRESHOLD_BIG = 50 * MB          # 战略 §2.2 原文
THRESHOLD_REJECT_PRE = 512 * MB  # T-00④ 预判（本探针定参）

try:
    import psutil  # noqa: F401
    PSUTIL = True
except ImportError:
    PSUTIL = False


def _ps_tree_mb_ps(pid):
    """PowerShell 回退：按 PID 池采样 auto.exe 进程树工作集（psutil 缺席时；
    bench.py Get-Process 法扩展——加 -Filter Parent 链第一步近似：同名进程
    中 CommandLine 含本实例 MCP 端口者）。"""
    try:
        out = subprocess.run(
            ["powershell", "-Command",
             "Get-CimInstance Win32_Process -Filter \"Name='auto.exe'\" | "
             "ForEach-Object { $p = Get-Process -Id $_.ProcessId -ErrorAction "
             "SilentlyContinue; if ($p) { '{0} {1}' -f $_.ProcessId, $p.WorkingSet64 } }"],
            capture_output=True, text=True, timeout=10)
        total = 0
        for ln in out.stdout.splitlines():
            parts = ln.split()
            if len(parts) == 2:
                total += int(parts[1])
        return round(total / MB, 1) if total else None
    except Exception:  # noqa: BLE001
        return None


class RssPoller:
    """子进程树 RSS 峰值采样（psutil 优先，缺席回退 PowerShell 同名进程池
    ——bench.py 法；两者皆缺席=恒 None）。"""

    def __init__(self, pid):
        self.pid = pid
        self.peak = None
        self._stop = threading.Event()
        self._t = threading.Thread(target=self._run, daemon=True)
        self._t.start()

    def _run(self):
        while not self._stop.is_set():
            total = None
            if PSUTIL:
                try:
                    proc = psutil.Process(self.pid)
                    total = proc.memory_info().rss
                    for ch in proc.children(recursive=True):
                        try:
                            total += ch.memory_info().rss
                        except psutil.Error:
                            pass
                except psutil.Error:
                    total = None
            else:
                mb = _ps_tree_mb_ps(self.pid)
                total = None if mb is None else int(mb * MB)
            if total and (self.peak is None or total > self.peak):
                self.peak = total
            self._stop.wait(0.5)

    def stop_mb(self):
        self._stop.set()
        if self._t:
            self._t.join(timeout=2)
        return None if self.peak is None else round(self.peak / MB, 1)


def make_fixture(path, total_bytes, crlf=False):
    """生成确定性大文本：~32KB/块，每块首行一枚 NEEDLE（ReplaceAll 计数锚）。
    返回 NEEDLE 总数（=块数）。"""
    needle_line = "NEEDLE_QZ_7F marker line for probe replace anchor\n"
    if crlf:
        needle_line = needle_line.replace("\n", "\r\n")
    plain = "line %08d padding text for bigfile probe fixture ........\n"
    block_lines = []
    for i in range(500):
        block_lines.append(needle_line if i == 0 else plain % i)
    if crlf:
        block = "".join(block_lines).replace("\n", "\r\n")
    else:
        block = "".join(block_lines)
    per = len(block.encode("utf-8"))
    n_full = total_bytes // per
    tail = total_bytes - n_full * per
    with open(path, "wb") as f:
        for _ in range(n_full):
            f.write(block.encode("utf-8"))
        if tail > 0:
            f.write((b"x" * (tail - 1) + b"\n"))
    return n_full


def launch_app(env_extra, bench_log=None):
    """Start a fresh `auto run -r vm` instance; return (proc, mcp, log_path)."""
    port = pick_free_port()
    if bench_log:
        log = open(bench_log, "w", encoding="utf-8", errors="replace")
    else:
        log = tempfile.NamedTemporaryFile(
            prefix="p013_probe_", suffix=".log", delete=False, mode="w",
            encoding="utf-8", errors="replace")
    env = {**os.environ, "AUTOUI_MCP_PORT": str(port),
           "APPDATA": tempfile.mkdtemp(prefix="auto041_p013_ad_"),
           **env_extra}
    proc = subprocess.Popen(
        [AUTO_BIN, "run", "-r", "vm"],
        cwd=PROJECT, env=env, stdout=log, stderr=subprocess.STDOUT)
    url = f"http://127.0.0.1:{port}/mcp"
    if not wait_for_server(url, 30):
        _kill_proc_tree(proc)
        raise RuntimeError("MCP server did not start")
    mcp = McpClient(url)
    for _ in range(15):
        s = mcp.snapshot()
        if "(rendered)" in s and s.count("onclick") > 0:
            break
        time.sleep(1)
    time.sleep(1.0)
    return proc, mcp, log.name


def wait_console(mcp, needle, timeout=120):
    """Poll until console contains needle; return (found, console, elapsed_s)."""
    return wait_console_any(mcp, [needle], timeout)


def wait_console_any(mcp, needles, timeout=120):
    """Poll until console contains any needle; return (found, console, elapsed_s)."""
    t0 = time.time()
    while time.time() - t0 < timeout:
        c = state_str(mcp.state("console"), "console") or ""
        if any(n in c for n in needles):
            return True, c, round(time.time() - t0, 2)
        time.sleep(0.2)
    return False, state_str(mcp.state("console"), "console") or "", round(time.time() - t0, 2)


def open_big(mcp, path):
    """AUTO_BENCH+AUTO_OPEN_PATH 旁路开文件（ConsumeOpen 链），等 loaded 行。
    console 行=「loaded: <全路径> N bytes」——basename 子串匹配（全路径夹
    中间，T13 同款 `("loaded: " in c) and base in c` 形）。"""
    base = os.path.basename(path)
    t0 = time.time()
    found = False
    console = ""
    while time.time() - t0 < 180:
        console = state_str(mcp.state("console"), "console") or ""
        if "loaded: " in console and base in console:
            found = True
            break
        time.sleep(0.2)
    el = round(time.time() - t0, 2)
    lb = state_int(mcp.state("loaded_bytes"), "loaded_bytes")
    return found, el, lb, console


def phase_a(fixdir, out):
    """/api/file_size 端点形（T-01 后补验）。"""
    print("\n" + "=" * 60)
    print("Phase A: back HTTP file_size endpoint")
    print("=" * 60)
    port = pick_free_port(9360)
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
    try:
        cases = [
            ("file_size 50MB", "/api/file_size",
             {"path": os.path.join(fixdir, "big50_lf.txt")}, 50 * MB),
            ("file_size small", "/api/file_size",
             {"path": os.path.join(fixdir, "small.txt")}, 42),
            ("file_size missing", "/api/file_size",
             {"path": os.path.join(fixdir, "__absent__.txt")}, -1),
        ]
        for label, ep, params, want in cases:
            try:
                r = requests.get(base + ep, params=params, timeout=15)
                body = r.text.strip()
                print(f"  {label}: HTTP {r.status_code}  {body[:80]!r}")
                got = None
                try:
                    # HTTP 层把 str 返回再包一层 JSON 引号（双重编码——
                    # '"{\"size\":N}"'），二次 loads 到 dict。
                    obj = body
                    for _ in range(2):
                        try:
                            obj = json.loads(obj)
                        except (ValueError, TypeError):
                            break
                    if isinstance(obj, dict):
                        got = obj.get("size")
                except Exception:  # noqa: BLE001
                    got = None
                out["checks"].append(
                    ("A: " + label, got == want, f"http={r.status_code} got={got} want={want}"))
            except Exception as e:  # noqa: BLE001
                print(f"  {label}: EXC {e}")
                out["checks"].append(("A: " + label, False, repr(e)))
    finally:
        _kill_proc_tree(proc)


def phase_b(fixdir, out):
    """merged UI 活体（②③④⑤ 证据）。"""
    print("\n" + "=" * 60)
    print("Phase B: merged UI live probes")
    print("=" * 60)

    # ---- B-1/B-2/B-3: 50MB 基线 + ReplaceAll + save（同一实例顺序驱动：
    # 先基线观测，再替换管线，再 save——单实例降资源峰；步墙/超时即证据）。
    f50 = os.path.join(fixdir, "big50_lf.txt")
    needles = out["fixtures"]["big50_lf.txt"]
    env = {"AUTO_BENCH": "1", "AUTO_OPEN_PATH": f50}
    proc, mcp, log = launch_app(env)
    rss = RssPoller(proc.pid)
    try:
        found, el, lb, console = open_big(mcp, f50)
        mb_peak = rss.stop_mb()
        out["bench"]["b1_load_50mb"] = {
            "loaded": found, "wait_s": el, "loaded_bytes": lb, "rss_peak_mb": mb_peak}
        out["checks"].append((
            "B1: 50MB auto-load completes, loaded_bytes==size",
            found and lb == 50 * MB,
            f"found={found} loaded_bytes={lb} wait_s={el} rss_peak_mb={mb_peak}"))
        print(f"  B1 50MB load: found={found} wait={el}s loaded_bytes={lb} rss={mb_peak}MB")

        # ---- B-2 ReplaceAll 全管线（当前码无护栏——墙/超时/慢即护栏实证；
        # T-03 后本位变拦截行——观测记录两种形态）。快照韧性包裹：大 tab 上
        # 快照代价本身即观测面（>64MB 守卫 abort=证据）。开栏 keystroke 加
        # state 校验重试（首拍派发竞态——T13 _t13_open_find 同源卫生）。
        t0 = time.time()
        rss2 = RssPoller(proc.pid)
        opened = False
        for _ in range(3):
            mcp.call("autoui_keyboard", key="h", modifiers=["ctrl"])
            time.sleep(0.6)
            if state_bool(mcp.state("find_replace_mode"), "find_replace_mode"):
                opened = True
                break
            time.sleep(0.4)
        iid = None
        snap_note = ""
        for _ in range(4):
            try:
                m2 = re.search(r"input #(\w+)", mcp.snapshot())
            except RuntimeError as e:
                snap_note = f"snapshot guard: {e}"
                break
            iid = m2.group(1) if m2 else None
            if iid:
                break
            time.sleep(0.5)
        typed = False
        if iid:
            # 键入+effective 回读验证（T13 _t13_type_query 同款重试）。
            for _ in range(3):
                mcp.call("autoui_type", element_id=iid, text="NEEDLE_QZ_7F", clear_first=True)
                time.sleep(0.6)
                eff0 = state_str(mcp.state("find_effective"), "find_effective")
                if eff0 and "NEEDLE_QZ_7F" in eff0:
                    break
            # 替换行第二个 input（替换为）；"RX" 短于 needle——save 后尺寸
            # 收缩=下轮 --keep-fixtures 复用时强制再生。
            try:
                m2 = re.findall(r"input #(\w+)", mcp.snapshot())
            except RuntimeError as e:
                m2 = []
                snap_note = f"snapshot guard: {e}"
            if len(m2) >= 2:
                mcp.call("autoui_type", element_id=m2[1], text="RX", clear_first=True)
                time.sleep(0.6)
                typed = True
        eff = state_str(mcp.state("find_effective"), "find_effective")
        clicked = False
        for _ in range(3):
            try:
                btn = find_button_by_text(mcp.snapshot(), "全部替换")
            except RuntimeError as e:
                btn = None
                snap_note = f"snapshot guard: {e}"
            if btn:
                break
            time.sleep(0.5)
        if btn:
            mcp.click(btn)
            clicked = True
        if not opened:
            snap_note = (snap_note + " ctrl+h no-open").strip()
        ok, console, el2 = wait_console_any(
            mcp, ["replace all:", "replace: blocked"], timeout=60)
        mb_peak2 = rss2.stop_mb()
        m = re.search(r"replace all: (\d+)", console or "")
        rep_count = int(m.group(1)) if m else -1
        out["bench"]["b2_replaceall_50mb"] = {
            "typed": typed, "effective": eff, "clicked": clicked,
            "ok": ok, "wait_s": el2, "count": rep_count,
            "expected": needles, "rss_peak_mb": mb_peak2,
            "guarded": "blocked" in (console or ""), "note": snap_note}
        out["checks"].append((
            "B2: ReplaceAll 50MB drive chain + outcome captured",
            typed and clicked and (ok or el2 >= 50),
            f"typed={typed} clicked={clicked} ok={ok} count={rep_count}/{needles} "
            f"wait_s={el2} rss_peak_mb={mb_peak2} {snap_note}"))
        print(f"  B2 ReplaceAll: ok={ok} count={rep_count}/{needles} wait={el2}s rss={mb_peak2}MB")

        # ---- B-3 save（WriteFidelity：读出+包装+write_text 全过 VM）。
        # 落盘 E2E=源文件尺寸变化（"RX" 替换使 rope 收缩 48×needles 字节——
        # 写通证据）；T-03 后护栏拦截形=console 拦截行+尺寸零变（两形皆绿）。
        size_before = os.path.getsize(f50)
        t0 = time.time()
        rss3 = RssPoller(proc.pid)
        btn = find_button_by_icon_save(mcp)
        clicked = False
        if btn:
            mcp.click(btn)
            clicked = True
        ok, console, el3 = wait_console_any(
            mcp, ["saved: ", "save blocked"], timeout=60)
        mb_peak3 = rss3.stop_mb()
        size_after = os.path.getsize(f50)
        # 替换 pattern=find_effective=12 字符 query（regex_escape 无变换），
        # 替换串 "RX"=2——每处收缩 10 字节 ×needles。
        expected_after = size_before - (len("NEEDLE_QZ_7F") - 2) * needles
        wrote_through = size_after == expected_after
        intercepted = ("拦截" in (console or "")) or ("save blocked" in (console or ""))
        out["bench"]["b3_save_50mb"] = {
            "clicked": clicked, "ok": ok, "wait_s": el3,
            "size_before": size_before, "size_after": size_after,
            "expected_after": expected_after,
            "wrote_through": wrote_through, "rss_peak_mb": mb_peak3,
            "intercepted": intercepted,
        }
        out["checks"].append((
            "B3: save 50MB outcome (wrote-through E2E | guarded no-op)",
            clicked and (wrote_through or (intercepted and size_after == size_before)),
            f"clicked={clicked} ok={ok} wait_s={el3} size {size_before}->{size_after} "
            f"(expect {expected_after}) rss_peak_mb={mb_peak3} intercepted={intercepted}"))
        print(f"  B3 save: clicked={clicked} ok={ok} wait={el3}s size {size_before}->{size_after} rss={mb_peak3}MB")
    finally:
        rss.stop_mb()
        _kill_proc_tree(proc)

    # ---- B-4: 100MB 基线 + B-5: 200MB 阈值勘（各自独立实例）。
    for label, fname, size_mb in (("b4_load_100mb", "big100_lf.txt", 100),
                                  ("b5_load_200mb", "big200_lf.txt", 200)):
        fpath = os.path.join(fixdir, fname)
        env = {"AUTO_BENCH": "1", "AUTO_OPEN_PATH": fpath}
        proc, mcp, log = launch_app(env)
        rss = RssPoller(proc.pid)
        try:
            found, el, lb, console = open_big(mcp, fpath)
            mb_peak = rss.stop_mb()
            out["bench"][label] = {
                "loaded": found, "wait_s": el, "loaded_bytes": lb,
                "rss_peak_mb": mb_peak}
            out["checks"].append((
                f"{label.upper()}: {size_mb}MB load completes, loaded_bytes==size",
                found and lb == size_mb * MB,
                f"found={found} loaded_bytes={lb} wait_s={el} rss_peak_mb={mb_peak}"))
            print(f"  {label}: found={found} wait={el}s loaded_bytes={lb} rss={mb_peak}MB")
        finally:
            rss.stop_mb()
            _kill_proc_tree(proc)


def find_button_by_icon_save(mcp):
    """toolbar save 按钮（icon=save）——desktop_mcp 助手复用形。"""
    from desktop_mcp import find_button_by_icon
    return find_button_by_icon(mcp.snapshot(), "save")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-a", action="store_true", help="跳过 Phase A（T-01 前）")
    ap.add_argument("--keep-fixtures", action="store_true")
    args = ap.parse_args()

    if not AUTO_BIN:
        print("auto binary not found (AUTO_BIN or PATH)")
        return 2

    os.makedirs(FIXDIR, exist_ok=True)
    out = {"toolchain": subprocess.run([AUTO_BIN, "--version"], capture_output=True,
                                       text=True).stdout.strip(),
           "psutil": PSUTIL, "fixtures": {}, "bench": {}, "checks": []}

    specs = [("small.txt", 42), ("big50_lf.txt", 50 * MB),
             ("big100_lf.txt", 100 * MB), ("big200_lf.txt", 200 * MB)]
    for fname, size in specs:
        p = os.path.join(FIXDIR, fname)
        if fname == "small.txt":
            with open(p, "wb") as f:
                f.write(b"hello probe\n" + b"x" * 30)
            out["fixtures"][fname] = 0
        else:
            if not os.path.exists(p) or os.path.getsize(p) != size:
                print(f"  generating {fname} ({size // MB}MB)...")
                out["fixtures"][fname] = make_fixture(p, size)
            else:
                # NEEDLE 计数=块数（按 size 反推）。
                out["fixtures"][fname] = -1
        print(f"  fixture {fname}: {os.path.getsize(p)} bytes")

    if not args.skip_a:
        phase_a(FIXDIR, out)
    else:
        print("Phase A skipped (--skip-a)")
    phase_b(FIXDIR, out)

    passed = sum(1 for _, ok, _ in out["checks"] if ok)
    total = len(out["checks"])
    out["summary"] = f"{passed}/{total}"
    rep_json = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "probe_bigfile_report.json")
    rep_txt = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "probe_bigfile_report.txt")
    with open(rep_json, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    with open(rep_txt, "w", encoding="utf-8") as f:
        f.write(f"PLAN-013 T-00 probe_bigfile — {out['toolchain']}\n")
        f.write(f"psutil={PSUTIL}\n\n")
        for k, v in out["bench"].items():
            f.write(f"{k}: {json.dumps(v, ensure_ascii=False)}\n")
        f.write("\n")
        for name, ok, detail in out["checks"]:
            f.write(f"[{'PASS' if ok else 'FAIL'}] {name}  {detail}\n")
        f.write(f"\nSUMMARY {passed}/{total}\n")
    print(f"\nSUMMARY {passed}/{total}  (report: {rep_txt})")

    if not args.keep_fixtures:
        shutil.rmtree(FIXDIR, ignore_errors=True)
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
