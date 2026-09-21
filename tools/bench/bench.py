#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bench.py — PLAN-005 B 段：测量套件（L0 proxy 报告 + 预算断言）。

战略语义（docs/strategy/002-north-star-v2.md §5 测量模式阶梯）：
  L0 = VM+merged（日常，无绝对性能效力——报告价值 = 启动链形状分解 +
       结构回归代理[编辑路径全量读检测] + 缓冲区类基线记账[rope 前禁调优]）
  L1 = VM+RQ（上游 §6 渲染臂覆盖缺口 blocked）
  L2 = a2r+release+RQ（唯一有预算效力；上游 §7 a2r 词汇门 / §6 blocked）

与 tools/perf/perf.py 分工：perf.py = 模式**切换**编排（L2 机构）；
bench.py = 测量**套件**（跑数与断言）。--mode l1/l2 经 perf.py 链取归因，
不复制其实现。

观测通道（T-03 实勘结论，tools/bench/README.md 探针矩阵）：
  host 面——spawn 计时 + stdout 落文件轮询（BENCH 裸标记行的到达时刻，
  毫秒值一律 host 侧记；VM 轨 time 族内建未接线，四探针实证）+ 内存采样
  （psutil 优先，缺席回退 PowerShell Get-Process WorkingSet64，方法记入结果）。
  app 面——AUTO_BENCH=1 门控的 BENCH 标记行（editor_store.at §PLAN-005 T-04；
  未设门 = 零行为差异，矩阵回归保证）。

用法（自仓库根或任意目录）：
  python tools/bench/bench.py check                       # 自检+指纹+检测器红证
  python tools/bench/bench.py proxy [--runs N] [--full] [--mode l0|l1|l2]
  python tools/bench/bench.py assert [--results <file>]  # 仅预算断言

退出码：0=绿；3=blocked-on-upstream（--mode l1/l2 归因）；1=真失败
       （含编辑路径全量读检测红 = 结构回归）。

Windows-only（进程面同 perf.py）；所有 app 输出落 tools/bench/logs/
（防管道阻塞，PLAN-003 坑位）；每轮按 PID 收（绝不 taskkill //IM）。
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent          # tools/bench
ROOT = HERE.parents[1]                          # 仓库根
PROJECT = Path(os.environ.get("PERF_PROJECT") or ROOT / "specs" / "auto-edit")
LOGS = HERE / "logs"
FIXTURES = HERE / "fixtures"
RESULTS = HERE / "results"
BUDGETS = HERE / "budgets.json"
PERF_PY = ROOT / "tools" / "perf" / "perf.py"

MIN_TOOLCHAIN_BUILD = 1588          # 与 perf.py 同门（含上游 PLAN-669）
DEFAULT_RUNS = 5                     # 启动分解跑数（首跑弃暖机）
DEFAULT_FIXTURE_MB = (1, 10, 100)    # 默认集；--full 加 512（T-03 Q4 裁定）
FULL_FIXTURE_MB = (1, 10, 100, 512)

EXIT_OK, EXIT_FAIL, EXIT_BLOCKED = 0, 1, 3

# 供料包归因（docs/upstream/2026-09-m1-supply.md）
BLOCK_L1 = ("VM+RQ 渲染臂 codeeditor 覆盖缺口（native_queue_set 缺 kind，"
            "实例死于「拒绝渲染，禁静默错绘」语义）——供料包 §6。")
BLOCK_L2 = ("L2 链上游阻塞：a2r 词汇门（§7）/ RQ 渲染臂覆盖（§6）——"
            "perf.py 链 exit 3 归因透传。")

# 编辑路径全量读检测：code_editor_text 允许位 = editor_store.at 的 save
# 上下文 handler（A 段即其首个绿证）。
STORE_FILE = "editor_store.at"
ALLOWED_HANDLERS = {"ActSave", "QuitSaveClose"}


def _log(msg: str) -> None:
    print(f"[bench {datetime.now():%H:%M:%S}] {msg}", flush=True)


def _ts() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def _auto_exe() -> str:
    cand = os.environ.get("AUTO_BIN") or shutil.which("auto") or shutil.which("auto.exe")
    if not cand:
        _log("FATAL: auto 不在 PATH 且未设 AUTO_BIN")
        sys.exit(EXIT_FAIL)
    return cand


def _fingerprint() -> dict:
    exe = _auto_exe()
    try:
        ver = subprocess.run([exe, "--version"], capture_output=True, text=True,
                             timeout=30).stdout.strip()
    except Exception as e:  # noqa: BLE001
        ver = f"<version probe failed: {e}>"
    try:
        import psutil  # noqa: F401
        psutil_ok = True
    except ImportError:
        psutil_ok = False
    return {"auto_path": exe, "auto_version": ver, "psutil": psutil_ok,
            "project": str(PROJECT), "os": sys.platform}


def _build_number(version: str):
    m = re.search(r"-(\d+)-g[0-9a-f]+", version)
    return int(m.group(1)) if m else None


# ---------------------------------------------------------------- 内存采样

def _sample_mem(pid: int) -> tuple[int | None, str]:
    """按 PID 采样工作集（字节）。返回 (值, 方法名)——方法记入结果 JSON。"""
    try:
        import psutil
        return psutil.Process(pid).memory_info().rss, "psutil.Process.rss"
    except ImportError:
        pass
    except Exception:  # noqa: BLE001
        pass
    out = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         f"(Get-Process -Id {pid}).WorkingSet64"],
        capture_output=True, text=True, timeout=20)
    try:
        return int(out.stdout.strip()), "powershell.Get-Process.WorkingSet64"
    except ValueError:
        return None, "unavailable"


# ---------------------------------------------------------------- app 驱动

def _kill_pid(pid: int) -> None:
    subprocess.run(["taskkill", "/PID", str(pid), "/F", "/T"],
                   capture_output=True, text=True)


def run_app_tracked(env_extra: dict, want_markers: list[str],
                    timeout_s: float = 60.0, log_name: str = "run",
                    mem_after: list[str] | None = None) -> dict:
    """spawn `auto run -r vm`，stdout 落文件，轮询 BENCH 标记行到达时刻。

    返回 {"markers": {name: ms_since_spawn}, "mem": {name: (bytes, method)},
          "log": path}。毫秒值全部 host 侧 perf_counter 记（T-03 结论：
    VM 轨 time 族内建未接线，app 侧无可用毫秒钟）。结束按 PID 树收编。
    """
    LOGS.mkdir(exist_ok=True)
    FIXTURES.mkdir(exist_ok=True)
    log = LOGS / f"{log_name}-{_ts()}.log"
    t0 = time.perf_counter()
    with open(log, "wb") as f:
        proc = subprocess.Popen([_auto_exe(), "run", "-r", "vm"], cwd=str(PROJECT),
                                env={**os.environ, **env_extra},
                                stdout=f, stderr=subprocess.STDOUT)
    markers: dict[str, float] = {}
    mems: dict[str, tuple] = {}
    try:
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            time.sleep(0.025)
            if proc.poll() is not None:
                _log(f"WARN: app 提前退出（{log.name}）")
                break
            try:
                text = log.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for m in want_markers:
                if m not in markers and f"BENCH {m}" in text:
                    markers[m] = (time.perf_counter() - t0) * 1000.0
            for m in (mem_after or []):
                if m in markers and m not in mems:
                    mems[m] = _sample_mem(proc.pid)
            if len(markers) == len(want_markers) and \
                    all(m in mems for m in (mem_after or [])):
                break
        return {"markers": markers, "mem": mems, "log": str(log),
                "alive_at_end": proc.poll() is None}
    finally:
        _kill_pid(proc.pid)


# ---------------------------------------------------------------- 全量读检测

def _scan_store_handlers(text: str):
    """yield (lineno, handler_name_or_None, line)——handler 归属按花括号深度。"""
    cur, depth = None, 0
    for i, line in enumerate(text.splitlines(), 1):
        if cur is None:
            m = re.match(r"\s*\.(\w+)\s*->", line)
            if m:
                cur = m.group(1)
                depth = line.count("{") - line.count("}")
                yield i, cur, line
                continue
            yield i, None, line
        else:
            depth += line.count("{") - line.count("}")
            yield i, cur, line
            if depth <= 0:
                cur = None


def check_full_read(project_root: Path) -> dict:
    """编辑路径全量读检测（战略 §5 代理指标三件之一）。

    code_editor_text 的允许位 = editor_store.at 内 ActSave/QuitSaveClose
    两个 save 上下文 handler；其余任何 front 文件/handler 出现即红。
    注释行不计。
    """
    reds: list[str] = []
    greens: list[str] = []
    front = project_root / "src" / "front"
    for path in sorted(front.glob("*.at")):
        text = path.read_text(encoding="utf-8", errors="replace")
        if path.name == STORE_FILE:
            for i, handler, line in _scan_store_handlers(text):
                s = line.strip()
                if s.startswith("//") or "code_editor_text" not in s:
                    continue
                loc = f"{path.name}:{i} ({handler or '<顶层>'})"
                (greens if handler in ALLOWED_HANDLERS else reds).append(loc)
        else:
            for i, line in enumerate(text.splitlines(), 1):
                s = line.strip()
                if s.startswith("//") or "code_editor_text" not in s:
                    continue
                reds.append(f"{path.name}:{i} (<非 store 文件>)")
    return {"status": "red" if reds else "green",
            "allowed": greens, "violations": reds}


# 检测器构造性红证（AC-07）：镜像形态样例必须判红、save 位样例不误报。
_RED_SAMPLE = """store Fake {
    on {
        .ActCut -> {
            code_editor_cut("k")
            .tabs[0].src = code_editor_text("k")
        }
        .ActSave -> {
            write_text("p", code_editor_text("k"))
        }
    }
}
"""


def _detector_selftest() -> bool:
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        front = Path(td) / "src" / "front"
        front.mkdir(parents=True)
        (front / STORE_FILE).write_text(_RED_SAMPLE, encoding="utf-8")
        (front / "other.at").write_text(
            '// 样例\nfn f() { let s = code_editor_text("k") }\n', encoding="utf-8")
        r = check_full_read(Path(td))
    ok = (r["status"] == "red"
          and len(r["violations"]) == 2
          and any("ActCut" in v for v in r["violations"])
          and any("非 store" in v for v in r["violations"])
          and len(r["allowed"]) == 1)
    _log(f"检测器红证自检：{'PASS' if ok else 'FAIL'} "
         f"(violations={r['violations']}, allowed={r['allowed']})")
    return ok


# ---------------------------------------------------------------- 预算断言

# L0 断言报告的逐行终态（五类；plan §5.4）。L2 完整跑通后 hard 行才进入
# 数字评估（当前上游 §6/§7 阻塞，--mode l2 exit 3 归因，不达评估）。
_L0_STATES = {
    "steady_start": ("not-armed", "硬门禁仅在 L2 评估（战略 §5 阶梯）"),
    "renderer_cold_start": ("not-armed", "硬门禁仅在 L2 评估；预算值待 Q2 拓扑"),
    "warm_start": ("pending-feature", "需 M2 会话恢复（懒装载）"),
    "open_100mb": ("arch-blocked", "rope 前架构性不可达，禁调优，只记基线"),
    "open_1gb": ("arch-blocked", "rope 前架构性不可达，禁调优，只记基线"),
    "type_latency": ("blocked-upstream", "内核帧时间戳插桩（T-03 勘无 .at 层通道）"),
    "scroll_fps": ("blocked-upstream", "帧率测量需内核插桩；大文件满帧率另需 rope"),
    "diff_100mb": ("blocked-upstream", "M3 diff 引擎"),
    "idle_mem": ("ledger", "L0 采样记账不阻塞；预算断言 M4 收口"),
    "installer": ("pending-feature", "Q2 独立 exe 打包路径"),
}
_STATE_ORDER = ["not-armed", "pending-feature", "arch-blocked",
                "blocked-upstream", "ledger"]


def evaluate_budgets(mode: str) -> list[dict]:
    rows = json.loads(BUDGETS.read_text(encoding="utf-8"))
    out = []
    for row in rows:
        state, note = _L0_STATES[row["id"]]
        entry = {"id": row["id"], "metric": row["metric"], "budget": row["budget"],
                 "tier": row["tier"], "state": state, "note": note}
        if mode != "l0":
            entry["note"] += f"（mode={mode}：上游阻塞，硬门禁未武装——见退出码 3 归因）"
        out.append(entry)
    return out


def _print_budget_table(rows: list[dict]) -> None:
    _log("预算断言报告（战略 §2.1 全表逐行终态，无静默缺席）：")
    for r in rows:
        _log(f"  [{r['state']:>15}] {r['id']:<20} {r['budget']:<28} — {r['note']}")
    states = {r["state"] for r in rows}
    missing = [s for s in _STATE_ORDER if s not in states]
    _log(f"  五类终态覆盖：{sorted(states)}"
         f"{'（缺：' + ','.join(missing) + '）' if missing else '——齐'}")


# ---------------------------------------------------------------- fixtures

def make_fixture(mb: int) -> tuple[Path, float]:
    FIXTURES.mkdir(exist_ok=True)
    p = FIXTURES / f"fixture-{mb}mb.at"
    t0 = time.perf_counter()
    unit = ("// bench fixture line — auto-edit PLAN-005 open-timing fixture\n"
            "fn probe() int { return 42 }\n").encode()
    target = mb * 1024 * 1024
    with open(p, "wb") as f:
        chunk = unit * (target // len(unit) + 1)
        f.write(chunk[:target])
    return p, time.perf_counter() - t0


# ---------------------------------------------------------------- 阶段

def stage_check() -> int:
    LOGS.mkdir(exist_ok=True)
    RESULTS.mkdir(exist_ok=True)
    fp = _fingerprint()
    envfile = LOGS / f"env-{_ts()}.txt"
    envfile.write_text(json.dumps(fp, indent=2, ensure_ascii=False), encoding="utf-8")
    _log(f"环境指纹 → {envfile}")
    for k, v in fp.items():
        _log(f"  {k}: {v}")
    build = _build_number(fp["auto_version"])
    if build is None:
        _log(f"FATAL: 无法解析工具链构建号：{fp['auto_version']}")
        return EXIT_FAIL
    if build < MIN_TOOLCHAIN_BUILD:
        _log(f"BLOCKED: 工具链构建 {build} < {MIN_TOOLCHAIN_BUILD}。"
             f"修复：auto-lang 内 cargo build --features ui-iced --bin auto。")
        return EXIT_BLOCKED
    if not fp["psutil"]:
        _log("NOTE: psutil 缺席——内存采样回退 PowerShell Get-Process（方法记入结果）")
    if not _detector_selftest():
        _log("FATAL: 全量读检测器红证自检失败（检测器本身坏了）")
        return EXIT_FAIL
    _log(f"check 绿：构建 {build} ≥ {MIN_TOOLCHAIN_BUILD}")
    return EXIT_OK


def _startup_runs(runs: int) -> list[dict]:
    _log(f"启动链分解：{runs} 跑（首跑弃暖机）——AUTO_BENCH=1 spawn vm")
    out = []
    for i in range(runs):
        r = run_app_tracked(
            {"AUTO_BENCH": "1"},
            want_markers=["bench_vm_init", "bench_ws_loaded"],
            timeout_s=45.0, log_name=f"startup-{i}",
            mem_after=["bench_ws_loaded"])
        m = r["markers"]
        rec = {"run": i, "warmup": i == 0,
               "spawn_to_vm_init_ms": m.get("bench_vm_init"),
               "vm_init_to_ws_loaded_ms":
                   (m["bench_ws_loaded"] - m["bench_vm_init"])
                   if "bench_vm_init" in m and "bench_ws_loaded" in m else None,
               "mem_idle": r["mem"].get("bench_ws_loaded")}
        out.append(rec)
        _log(f"  run{i}{'(暖机弃)' if i == 0 else ''}: "
             f"spawn→init={rec['spawn_to_vm_init_ms'] and round(rec['spawn_to_vm_init_ms'])}ms "
             f"init→ws={rec['vm_init_to_ws_loaded_ms'] and round(rec['vm_init_to_ws_loaded_ms'])}ms "
             f"mem={rec['mem_idle'][0] and round(rec['mem_idle'][0] / 1048576)}MB"
             if rec["mem_idle"] else "  (未捕获)")
    return out


def _open_timing(sizes: list[int]) -> list[dict]:
    out = []
    for mb in sizes:
        fixture, gen_s = make_fixture(mb)
        _log(f"打开计时 {mb}MB（fixture 生成 {gen_s:.2f}s，gitignored）")
        r = run_app_tracked(
            {"AUTO_BENCH": "1", "AUTO_OPEN_PATH": str(fixture)},
            want_markers=["bench_open_start", "bench_open_done"],
            timeout_s=120.0, log_name=f"open-{mb}mb",
            mem_after=["bench_open_done"])
        m = r["markers"]
        rec = {"size_mb": mb,
               "open_ms": (m["bench_open_done"] - m["bench_open_start"])
                          if "bench_open_start" in m and "bench_open_done" in m else None,
               "spawn_to_open_start_ms": m.get("bench_open_start"),
               "mem_loaded": r["mem"].get("bench_open_done"),
               "fixture_gen_s": round(gen_s, 3)}
        out.append(rec)
        _log(f"  {mb}MB: open={rec['open_ms'] and round(rec['open_ms'])}ms "
             f"mem={rec['mem_loaded'][0] and round(rec['mem_loaded'][0] / 1048576)}MB"
             if rec["mem_loaded"] else "  (未捕获)")
    return out


def _mode_gate(mode: str) -> int | None:
    """--mode l1/l2：经 perf.py 链取归因。返回退出码（None=l0 直通）。"""
    if mode == "l0":
        return None
    if mode == "l1":
        _log("mode l1（VM+RQ）：perf.py smoke 编排验证 + 归因")
        rc = subprocess.run([sys.executable, str(PERF_PY), "smoke"]).returncode
        if rc == EXIT_BLOCKED:
            _log(f"BLOCKED: {BLOCK_L1}")
            return EXIT_BLOCKED
        if rc != EXIT_OK:
            _log(f"FATAL: perf.py smoke 失败 rc={rc}")
            return EXIT_FAIL
        _log("l1 链意外打通（上游已解阻？）——硬门禁仍只认 L2，此处按归因口径返回")
        return EXIT_BLOCKED
    if mode == "l2":
        _log("mode l2（a2r+release+RQ）：perf.py a2r 起链")
        rc = subprocess.run([sys.executable, str(PERF_PY), "a2r"]).returncode
        if rc == EXIT_BLOCKED:
            _log(f"BLOCKED: {BLOCK_L2}")
            return EXIT_BLOCKED
        if rc != EXIT_OK:
            _log(f"FATAL: perf.py a2r 失败 rc={rc}")
            return EXIT_FAIL
        _log("a2r 绿——继续 release/rq-up/proxy 数字面（上游解阻后本分支生效）")
        for stage in ("release", "rq-up"):
            rc = subprocess.run([sys.executable, str(PERF_PY), stage]).returncode
            if rc != EXIT_OK:
                _log(f"BLOCKED/FATAL: perf.py {stage} rc={rc}——{BLOCK_L2}")
                return EXIT_BLOCKED if rc == EXIT_BLOCKED else EXIT_FAIL
        return None    # 链通，proxy 数字面按 L2 评估（硬门禁武装）
    _log(f"FATAL: 未知 mode {mode}")
    return EXIT_FAIL


def stage_proxy(runs: int, full: bool, mode: str) -> int:
    gate = _mode_gate(mode)
    if gate is not None:
        return gate
    RESULTS.mkdir(exist_ok=True)
    fp = _fingerprint()
    lines: list[dict] = [{"type": "env", "ts": _ts(), **fp}]

    startup = _startup_runs(runs)
    lines.append({"type": "startup_runs", "warmup_discarded": True, "runs": startup})

    sizes = list(FULL_FIXTURE_MB if full else DEFAULT_FIXTURE_MB)
    opens = _open_timing(sizes)
    lines.append({"type": "open_timing", "sizes": opens})

    fr = check_full_read(PROJECT)
    lines.append({"type": "static_full_read", **fr})
    _log(f"全量读检测：{fr['status']}"
         + (f"——违例 {fr['violations']}" if fr["violations"]
            else f"（允许位 {fr['allowed']}）"))

    budgets = evaluate_budgets(mode)
    lines.append({"type": "budget_assert", "mode": mode, "rows": budgets})
    _print_budget_table(budgets)

    outfile = RESULTS / f"{_ts()}.jsonl"
    with open(outfile, "w", encoding="utf-8", newline="\n") as f:
        for ln in lines:
            f.write(json.dumps(ln, ensure_ascii=False) + "\n")
    _log(f"结果 JSONL → {outfile}")

    hard_bad = [r for r in budgets if r["tier"] == "hard" and r["state"] not in
                ("not-armed",) and mode != "l2"]
    if fr["status"] == "red":
        _log("FATAL: 编辑路径全量读检测红——结构回归（镜像回读复活？）")
        return EXIT_FAIL
    if hard_bad:
        _log("FATAL: 硬门禁状态异常（非 L2 下 hard 行必须 not-armed）")
        return EXIT_FAIL
    return EXIT_OK


def stage_assert(results: str | None) -> int:
    if results:
        path = Path(results)
    else:
        cands = sorted(RESULTS.glob("*.jsonl"))
        if not cands:
            _log("FATAL: 无既往 results 文件（先跑 proxy，或 --results 指定）")
            return EXIT_FAIL
        path = cands[-1]
    _log(f"断言源：{path}")
    rows = None
    for ln in path.read_text(encoding="utf-8").splitlines():
        d = json.loads(ln)
        if d.get("type") == "budget_assert":
            rows = d["rows"]
    if rows is None:
        _log("FATAL: 该结果文件无 budget_assert 记录")
        return EXIT_FAIL
    _print_budget_table(rows)
    return EXIT_OK


def main() -> int:
    ap = argparse.ArgumentParser(description="auto-edit 测量套件（PLAN-005 B 段）")
    ap.add_argument("cmd", choices=["check", "proxy", "assert"])
    ap.add_argument("--runs", type=int, default=DEFAULT_RUNS,
                    help=f"启动分解跑数（默认 {DEFAULT_RUNS}，首跑弃暖机）")
    ap.add_argument("--full", action="store_true",
                    help="fixture 集含 512 MB（默认 1/10/100）")
    ap.add_argument("--mode", default="l0", choices=["l0", "l1", "l2"],
                    help="测量模式阶梯（默认 l0；l1/l2 经 perf.py 链归因）")
    ap.add_argument("--results", default=None, help="assert 命令的结果文件")
    args = ap.parse_args()
    if args.cmd == "check":
        return stage_check()
    if args.cmd == "proxy":
        return stage_proxy(args.runs, args.full, args.mode)
    return stage_assert(args.results)


if __name__ == "__main__":
    sys.exit(main())
