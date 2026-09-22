#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bench.py — 测量套件（PLAN-005 B 段 L0；PLAN-006 L2 数字面 + 武装断言）。

战略语义（docs/strategy/002-north-star-v2.md §5 测量模式阶梯）：
  L0 = VM+merged（日常，无绝对性能效力——报告价值 = 启动链形状分解 +
       结构回归代理[编辑路径全量读检测] + 缓冲区类基线记账[rope 前禁调优]）
  L1 = VM+RQ（上游 §6 渲染臂覆盖缺口 blocked）
  L2 = a2r+release+RQ（唯一有预算效力；上游解阻后 PLAN-006 建成数字面——
       release 产物直拉 + rqhost 预热，steady_start/renderer_cold_start 武装）

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
       （含编辑路径全量读检测红 = 结构回归）。--mode l2 的武装判定 fail
       是记录性的（首基线锚点，战略补注 6(d)：硬门禁「回归当天修」属
       M4 门禁生效后），不改退出码。

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

# ---------------- PLAN-006 L2 数字面（release 直拉 + rqhost 预热）----------------
# 隔离 well-known（同 perf.py 常量：后缀防与本机常驻实例串扰；锁管道 <wk>-lock）
L2_WELLKNOWN = "autodesk-rqhost-edit004"
# release 产物直拉的客户端旗标组合（T-00 勘定，镜像宿主 spawn_launcher_
# outproc 形 + 生成 main.rs autodesk gate L1190-1236 语义）：--autodesk-
# launcher 进 client 臂；--autodesk-rqhost 采纳 rendezvous；wellknown 经
# --autodesk-broker 传入（client 臂不读 AUTO_RQHOST_WELLKNOWN——该 env 只被
# daemon 读）；--autodesk-render=queue 钉死队列渲染（覆盖扫描制下 queue 优先）。
L2_CLIENT_FLAGS = ["--autodesk-launcher", "--autodesk-rqhost",
                   "--autodesk-render=queue"]
DETACHED = 0x00000008          # DETACHED_PROCESS（同 perf.py）
NEW_GROUP = 0x00000200         # CREATE_NEW_PROCESS_GROUP
L2_POLL_S = 0.002              # L2 标记轮询粒度（80ms 级预算 → 2ms 档；L0 保持 25ms）
STEADY_BUDGET_MS = 80.0        # 战略 §2.1 steady_start 硬预算

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
    mtime = ""
    if Path(exe).exists():
        mtime = datetime.fromtimestamp(
            Path(exe).stat().st_mtime).isoformat(timespec="minutes")
    try:
        import psutil  # noqa: F401
        psutil_ok = True
    except ImportError:
        psutil_ok = False
    return {"auto_path": exe, "auto_version": ver, "auto_mtime": mtime,
            "psutil": psutil_ok, "project": str(PROJECT), "os": sys.platform}


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


def _spawn_tracked(cmd: list[str], env_extra: dict, want_markers: list[str],
                   timeout_s: float, log_name: str,
                   mem_after: list[str] | None = None,
                   poll_s: float = 0.025,
                   on_complete=None, keep_alive: bool = False) -> dict:
    """spawn cmd（cwd=PROJECT），stdout 落文件，轮询 BENCH 标记行到达时刻。

    返回 {"markers": {name: ms_since_spawn}, "mem": {name: (bytes, method)},
          "log": path, "pid": pid, "alive_at_end": bool}。毫秒值全部 host 侧
    perf_counter 记（T-03 结论：VM 轨 time 族内建未接线，app 侧无可用毫秒钟）。
    结束按 PID 树收编，除非 keep_alive=True（L2：末窗退出语义下 daemon 随
    最后窗口自退——app 保活让 daemon 常驻整个测量序列，收编归 suite 末）。
    on_complete 在标记+内存齐时、收编前回调（此刻 app 与其依赖进程均
    存活——守护内存等在位采样的挂点）。
    """
    LOGS.mkdir(exist_ok=True)
    FIXTURES.mkdir(exist_ok=True)
    log = LOGS / f"{log_name}-{_ts()}.log"
    t0 = time.perf_counter()
    with open(log, "wb") as f:
        proc = subprocess.Popen(cmd, cwd=str(PROJECT),
                                env={**os.environ, **env_extra},
                                stdout=f, stderr=subprocess.STDOUT)
    markers: dict[str, float] = {}
    mems: dict[str, tuple] = {}
    try:
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            time.sleep(poll_s)
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
                if on_complete is not None:
                    on_complete()
                break
        return {"markers": markers, "mem": mems, "log": str(log),
                "pid": proc.pid, "alive_at_end": proc.poll() is None}
    finally:
        if not keep_alive:
            _kill_pid(proc.pid)


def run_app_tracked(env_extra: dict, want_markers: list[str],
                    timeout_s: float = 60.0, log_name: str = "run",
                    mem_after: list[str] | None = None) -> dict:
    """L0 形状：spawn `auto run -r vm`（25ms 轮询——形状分解粒度足够）。"""
    return _spawn_tracked([_auto_exe(), "run", "-r", "vm"], env_extra,
                          want_markers, timeout_s, log_name, mem_after)


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
# L2 终态序（§5.2 表）：not-armed 位被 armed / armed-record 顶替，余行
# 保持记账语义但携带 L2 实测数字（rope 前后对照锚点）。
_L2_STATE_ORDER = ["armed", "armed-record", "pending-feature",
                   "arch-blocked", "blocked-upstream", "ledger"]


def _l2_row(rid: str, entry: dict, m: dict | None) -> tuple[str, str]:
    """L2 语义逐行终态（§5.2 表）。entry 原位附加实测/判定字段。"""
    m = m or {}
    if rid == "steady_start":
        mean = m.get("steady_mean_ms")
        entry["measured_ms"] = mean
        entry["budget_ms"] = STEADY_BUDGET_MS
        entry["runs_ms"] = m.get("steady_runs_ms")
        entry["verdict"] = (None if mean is None
                            else ("pass" if mean <= STEADY_BUDGET_MS else "fail"))
        return ("armed",
                "L2 武装（hard）：spawn→bench_ws_loaded 代理口径（首帧通道 "
                "blocked-upstream，观测缺席——§10-1 默认采用+注记）；fail=记录性"
                "判定（首基线锚点，归因见启动链两段分解；硬门禁「回归当天修」"
                "属 M4 门禁生效后，战略补注 6(d)）")
    if rid == "renderer_cold_start":
        entry["measured_ms"] = m.get("renderer_cold_ms")
        entry["daemon_mem_bytes"] = m.get("rqhost_mem_bytes")
        return ("armed-record",
                "L2 武装记录：rqhost spawn→pipe-ready 单列数字（debug 构建形态，"
                "§10-2 默认）；预算值 pending-Q2 不判")
    state, note = _L0_STATES[rid]
    if rid in ("open_100mb", "open_1gb"):
        mb = 100 if rid == "open_100mb" else 1024
        v = m.get("open_ms", {}).get(mb)
        if v is not None:
            entry["l2_open_ms"] = v       # rope 前后对照锚点（1gb 无 fixture 则缺省）
    if rid == "idle_mem":
        entry["l2_app_mem_bytes"] = m.get("idle_mean_bytes")
        entry["rqhost_mem_bytes"] = m.get("rqhost_mem_bytes")
        note += "；L2 附 app 实测（rqhost 守护单列另记，预算随 Q2）"
    return state, note


def evaluate_budgets(mode: str, metrics: dict | None = None) -> list[dict]:
    rows = json.loads(BUDGETS.read_text(encoding="utf-8"))
    out = []
    for row in rows:
        entry = {"id": row["id"], "metric": row["metric"], "budget": row["budget"],
                 "tier": row["tier"]}
        if mode == "l2":
            entry["state"], entry["note"] = _l2_row(row["id"], entry, metrics)
        else:
            entry["state"], entry["note"] = _L0_STATES[row["id"]]
            if mode == "l1":
                entry["note"] += "（mode=l1：上游阻塞，硬门禁未武装——见退出码 3 归因）"
        out.append(entry)
    return out


def _print_budget_table(rows: list[dict], order: list[str] | None = None) -> None:
    order = order or _STATE_ORDER
    _log("预算断言报告（战略 §2.1 全表逐行终态，无静默缺席）：")
    for r in rows:
        armed = (f" measured={r['measured_ms']}ms"
                 if r.get("measured_ms") is not None else "")
        verdict = (f" verdict={r['verdict']}" if r.get("verdict") is not None else "")
        _log(f"  [{r['state']:>13}] {r['id']:<20} {r['budget']:<28}{armed}{verdict}"
             f" — {r['note']}")
    states = {r["state"] for r in rows}
    missing = [s for s in order if s not in states]
    label = "五类终态覆盖" if len(order) == 5 else "终态覆盖"
    _log(f"  {label}：{sorted(states)}"
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


# ---------------------------------------------------------------- L2 运行器

def _release_exe() -> Path | None:
    # 落点解析序对齐 perf.py _workspace_manifest：AUTO_RUST_WORKSPACE
    # （权威）→ <project>/rust-workspace；产物名 = pac exe_name（T-00 实锚）。
    ws = Path(os.environ.get("AUTO_RUST_WORKSPACE") or PROJECT / "rust-workspace")
    exe = ws / "target" / "release" / "auto-edit.exe"
    return exe if exe.exists() else None


def _perf_stage(stage: str) -> int:
    """转发 perf.py 阶段（环境原样继承——PERF_PROJECT 锚定随之透传）。"""
    return subprocess.run([sys.executable, str(PERF_PY), stage]).returncode


def _pipe_up(wellknown: str, timeout_s: float = 1.0) -> bool:
    """探测 well-known 管道在位（连上即关——serve 环吞探测 ping，同 perf.py）。

    注意：只作就绪信号，不作存活信号——daemon 服务环瞬时无实例时管道
    短暂不可连但进程仍在（实勘：误判死→重拉撞 -lock 锁）。存活判定用
    `_pid_alive`。"""
    try:
        f = open(rf"\\.\pipe\{wellknown}", "r+b", buffering=0)
        f.close()
        return True
    except PermissionError:
        return True          # 管道在位但忙（实例满）——daemon 已监听
    except OSError:
        return False


def _pid_alive(pid: int | None) -> bool:
    if not pid:
        return False
    out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
                         capture_output=True, text=True).stdout
    return str(pid) in out


def _rqhost_start(state: dict, measure: bool) -> bool:
    """（重）spawn rqhost daemon（debug 工具链，§10-2 默认；构建形态记档）。

    measure=True 记 spawn→pipe-ready 冷启动（renderer_cold_start 只记首测）。
    daemon 日志追加同文件。spawn 带锁竞态重试（前任实例 -lock 释放滞后/
    服务环暂空误连失败——3 次退避）。
    """
    LOGS.mkdir(exist_ok=True)
    log = Path(state["log"])
    env = {**os.environ, "AUTO_RQHOST_WELLKNOWN": L2_WELLKNOWN}
    ready = False
    for attempt in range(3):
        t0 = time.perf_counter()
        with open(log, "ab") as f:
            proc = subprocess.Popen([_auto_exe(), "rqhost"], cwd=str(PROJECT), env=env,
                                    stdout=f, stderr=subprocess.STDOUT,
                                    creationflags=DETACHED | NEW_GROUP)
        deadline = time.time() + 20.0
        while time.time() < deadline:
            if _pipe_up(L2_WELLKNOWN, 0.3):
                ready = True
                break
            if proc.poll() is not None:
                break        # 瞬死（如 -lock 被占第二实例退出）——重试
            time.sleep(L2_POLL_S)
        if ready:
            break
        _log(f"WARN: rqhost 启动未就绪（attempt {attempt + 1}，rc={proc.returncode}）"
             "——0.5s 后重试（锁释放竞态）")
        time.sleep(0.5)
    if not ready:
        _kill_pid(proc.pid)
        _log(f"FATAL: rqhost 3 次尝试未就绪（wellknown={L2_WELLKNOWN}，日志 {log}）")
        return False
    if measure:
        state["cold_start_ms"] = round((time.perf_counter() - t0) * 1000.0, 1)
        _log(f"rqhost 冷启动：spawn→pipe-ready {state['cold_start_ms']}ms"
             f"（pid={proc.pid}，debug 构建）")
    else:
        state["restarts"] = state.get("restarts", 0) + 1
        _log(f"rqhost 复活：pid={proc.pid}")
    state["rq_pid"] = proc.pid
    (PERF_PY.parent / ".rq.json").write_text(json.dumps(
        {"rq_pid": proc.pid, "wellknown": L2_WELLKNOWN,
         "started": _ts(), "apps": []}), encoding="utf-8")
    return True


def _window_opened_since(log_path: Path, offset: int, timeout_s: float = 8.0) -> bool:
    """daemon 日志自 offset 起是否出现「window opened」（采纳成立观测）。

    耐心轮询：标记先于 adopt 结果打印，窗开启在 adopt 握手后——给足
    8s（客户端 adopt 超时 5s + 余量）。"""
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            with open(log_path, "rb") as f:
                f.seek(offset)
                if b"window opened" in f.read():
                    return True
        except OSError:
            pass
        time.sleep(0.005)
    return False


def _window_opened_since(log_path: Path, offset: int, timeout_s: float = 8.0) -> bool:
    """daemon 日志自 offset 起是否出现「window opened」（采纳成立观测）。

    耐心轮询：标记先于 adopt 结果打印，窗开启在 adopt 握手后——给足
    8s（客户端 adopt 超时 5s + 余量）。"""
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            with open(log_path, "rb") as f:
                f.seek(offset)
                if b"window opened" in f.read():
                    return True
        except OSError:
            pass
        time.sleep(0.005)
    return False


def run_release_tracked(env_extra: dict, want_markers: list[str],
                        timeout_s: float, log_name: str,
                        mem_after: list[str] | None = None,
                        on_complete=None) -> dict:
    """L2 形状：直拉 release 产物（不经 auto.exe 宿主），2ms 轮询，保活
    （收编归 suite 末——daemon 末窗退出语义）。"""
    exe = _release_exe()
    if exe is None:
        _log("FATAL: release 产物缺席（rust-workspace/target/release/auto-edit.exe）")
        sys.exit(EXIT_FAIL)
    cmd = [str(exe), *L2_CLIENT_FLAGS, f"--autodesk-broker={L2_WELLKNOWN}"]
    return _spawn_tracked(cmd, env_extra, want_markers, timeout_s, log_name,
                          mem_after, poll_s=L2_POLL_S, on_complete=on_complete,
                          keep_alive=True)


def _l2_env_extra(fp: dict) -> dict:
    exe = _release_exe()
    mtime = (datetime.fromtimestamp(exe.stat().st_mtime).isoformat(timespec="minutes")
             if exe else "<absent>")
    return {"release_exe": str(exe) if exe else "<absent>",
            "release_exe_mtime": mtime,
            "renderer_daemon_build":
                f"debug（auto.exe rqhost，{fp['auto_version']}）",
            "rqhost_wellknown": L2_WELLKNOWN}


def _l2_suite(runs: int, sizes: list[int], fp: dict) -> dict | None:
    """L2 数字面（§5.1）：rqhost 冷启动单列 + 启动分解（release 直拉，
    steady_start=spawn→bench_ws_loaded 代理口径 §10-1）+ 打开计时 +
    守护内存（N 跑后稳态）。

    daemon 生命周期协议（顺设计，不与末窗退出语义对抗）：**单一 daemon
    服务整个测量序列**，app 全程保活（窗口累积——rqhost 本就是多 app
    共享合成器，smoke 双实例先例）→「RQ 渲染器已预热」语义成立且无
    重启竞态；suite 末统一收编全部 app + rq-down。

    拓扑有效性双门（首跑实勘：BENCH 标记先于 adopt 结果打印——死
    daemon 上标记照达但窗未建）：每跑断言 daemon 侧「window opened」
    + app 存活，任一不过 = 真失败。
    """
    exe = _release_exe()
    if exe is None:
        _log("FATAL: release 产物缺席——门控链应已编译，查 rust-workspace/target/release/")
        return None
    rc = _perf_stage("rq-down")
    if rc != EXIT_OK:
        _log(f"FATAL: 预清理 rq-down rc={rc}")
        return None
    time.sleep(0.3)             # rq-down 后锁句柄释放余量（spawn 重试兜底同在）
    daemon = {"rq_pid": None, "cold_start_ms": None, "restarts": 0,
              "wellknown": L2_WELLKNOWN,
              "log": str(LOGS / f"rqhost-l2-{_ts()}.log")}
    if not _rqhost_start(daemon, measure=True):
        return None
    daemon["daemon_build"] = _l2_env_extra(fp)["renderer_daemon_build"]
    dlog = Path(daemon["log"])
    app_pids: list[int] = []
    try:
        _log(f"启动链分解（L2）：{runs} 跑（首跑弃暖机）——release 直拉 {exe.name} + queue 渲染"
             "（单一 daemon 序列服务，app 保活累积窗口）")
        startup: list[dict] = []
        for i in range(runs):
            off = dlog.stat().st_size
            last = i == runs - 1
            r = run_release_tracked(
                {"AUTO_BENCH": "1"},
                want_markers=["bench_vm_init", "bench_ws_loaded"],
                timeout_s=45.0, log_name=f"l2-startup-{i}",
                mem_after=["bench_ws_loaded"],
                on_complete=(lambda: daemon.__setitem__(
                    "daemon_mem_steady", _sample_mem(daemon["rq_pid"]))
                    if last else None))
            app_pids.append(r["pid"])
            m = r["markers"]
            if "bench_vm_init" not in m or "bench_ws_loaded" not in m:
                _log(f"FATAL: L2 run{i} 标记缺失（得 {sorted(m)}，日志 {r['log']}）"
                     "——武装断言需数字，按真失败处理")
                return None
            if not r["alive_at_end"] or not _window_opened_since(dlog, off):
                _log(f"FATAL: L2 run{i} 拓扑无效（app 存活={r['alive_at_end']}，"
                     "daemon 未建窗——采纳未成立）——数字不纳入")
                return None
            rec = {"run": i, "warmup": i == 0,
                   "spawn_to_vm_init_ms": round(m["bench_vm_init"], 1),
                   "vm_init_to_ws_loaded_ms":
                       round(m["bench_ws_loaded"] - m["bench_vm_init"], 1),
                   "steady_start_ms": round(m["bench_ws_loaded"], 1),
                   "mem_idle": r["mem"].get("bench_ws_loaded")}
            startup.append(rec)
            mem_mb = (round(rec["mem_idle"][0] / 1048576)
                      if rec["mem_idle"] and rec["mem_idle"][0] else None)
            _log(f"  run{i}{'(暖机弃)' if i == 0 else ''}: "
                 f"steady={rec['steady_start_ms']}ms "
                 f"(init={rec['spawn_to_vm_init_ms']} + "
                 f"ws={rec['vm_init_to_ws_loaded_ms']}) mem={mem_mb}MB")
        opens: list[dict] = []
        for mb in sizes:
            fixture, gen_s = make_fixture(mb)
            off = dlog.stat().st_size
            _log(f"打开计时（L2）{mb}MB（fixture 生成 {gen_s:.2f}s，gitignored）")
            r = run_release_tracked(
                {"AUTO_BENCH": "1", "AUTO_OPEN_PATH": str(fixture)},
                want_markers=["bench_open_start", "bench_open_done"],
                timeout_s=120.0, log_name=f"l2-open-{mb}mb",
                mem_after=["bench_open_done"])
            app_pids.append(r["pid"])
            m = r["markers"]
            if "bench_open_start" not in m or "bench_open_done" not in m:
                _log(f"FATAL: L2 open {mb}MB 标记缺失（得 {sorted(m)}，日志 {r['log']}）")
                return None
            if not r["alive_at_end"] or not _window_opened_since(dlog, off):
                _log(f"FATAL: L2 open {mb}MB 拓扑无效（app 存活={r['alive_at_end']}，"
                     "daemon 未建窗）")
                return None
            rec = {"size_mb": mb,
                   "open_ms": round(m["bench_open_done"] - m["bench_open_start"], 1),
                   "spawn_to_open_start_ms": round(m["bench_open_start"], 1),
                   "mem_loaded": r["mem"].get("bench_open_done"),
                   "fixture_gen_s": round(gen_s, 3)}
            opens.append(rec)
            mem_mb = (round(rec["mem_loaded"][0] / 1048576)
                      if rec["mem_loaded"] and rec["mem_loaded"][0] else None)
            _log(f"  {mb}MB: open={rec['open_ms']}ms mem={mem_mb}MB")
        return {"startup": startup, "opens": opens, "rqhost": daemon}
    finally:
        for pid in app_pids:
            _kill_pid(pid)
        _log(f"app 实例统一收编（{len(app_pids)} 个，按 PID）")
        rc = _perf_stage("rq-down")
        _log(f"会话末 rq-down rc={rc}（按 .rq.json PID 收编，不留孤儿）")


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
    lines: list[dict] = [{"type": "env", "ts": _ts(), "mode": mode, **fp}]
    sizes = list(FULL_FIXTURE_MB if full else DEFAULT_FIXTURE_MB)
    metrics: dict | None = None

    if mode == "l2":
        data = _l2_suite(runs, sizes, fp)
        if data is None:
            return EXIT_FAIL
        lines[0].update(_l2_env_extra(fp))
        rq = data["rqhost"]
        lines.append({"type": "rqhost", "wellknown": rq["wellknown"],
                      "daemon_build": rq["daemon_build"],
                      "cold_start_ms": rq["cold_start_ms"],
                      "daemon_restarts": rq.get("restarts", 0),
                      "daemon_mem_steady": rq.get("daemon_mem_steady"),
                      "rq_pid": rq["rq_pid"]})
        lines.append({"type": "startup_runs", "warmup_discarded": True,
                      "runs": data["startup"]})
        lines.append({"type": "open_timing", "sizes": data["opens"]})
        steady = [r["steady_start_ms"] for r in data["startup"] if not r["warmup"]]
        idle = [r["mem_idle"][0] for r in data["startup"]
                if not r["warmup"] and r["mem_idle"] and r["mem_idle"][0]]
        metrics = {
            "steady_runs_ms": steady,
            "steady_mean_ms": round(sum(steady) / len(steady), 1) if steady else None,
            "renderer_cold_ms": rq["cold_start_ms"],
            "open_ms": {r["size_mb"]: r["open_ms"] for r in data["opens"]},
            "idle_mean_bytes": round(sum(idle) / len(idle)) if idle else None,
            "rqhost_mem_bytes": (rq.get("daemon_mem_steady") or (None,))[0],
        }
    else:
        startup = _startup_runs(runs)
        lines.append({"type": "startup_runs", "warmup_discarded": True, "runs": startup})
        opens = _open_timing(sizes)
        lines.append({"type": "open_timing", "sizes": opens})

    fr = check_full_read(PROJECT)
    lines.append({"type": "static_full_read", **fr})
    _log(f"全量读检测：{fr['status']}"
         + (f"——违例 {fr['violations']}" if fr["violations"]
            else f"（允许位 {fr['allowed']}）"))

    budgets = evaluate_budgets(mode, metrics)
    lines.append({"type": "budget_assert", "mode": mode, "rows": budgets})
    _print_budget_table(budgets,
                        order=_L2_STATE_ORDER if mode == "l2" else _STATE_ORDER)
    for r in budgets:
        if r.get("verdict") == "fail":
            _log(f"NOTE: {r['id']} 武装判定 fail（记录性——首基线锚点，不改退出码；"
                 "归因分解见启动链两段）")

    outfile = RESULTS / f"{_ts()}.jsonl"
    with open(outfile, "w", encoding="utf-8", newline="\n") as f:
        for ln in lines:
            f.write(json.dumps(ln, ensure_ascii=False) + "\n")
    _log(f"结果 JSONL → {outfile}")

    if fr["status"] == "red":
        _log("FATAL: 编辑路径全量读检测红——结构回归（镜像回读复活？）")
        return EXIT_FAIL
    if mode == "l2":
        unarmed = [r["id"] for r in budgets
                   if r["tier"] == "hard" and r.get("measured_ms") is None]
        if unarmed:
            _log(f"FATAL: L2 硬行无实测数字：{unarmed}（武装断言缺数）")
            return EXIT_FAIL
        # 武装 fail 是记录性判定（§5.2）：首基线锚点 + 归因分解，不触发调优
        # 也不改退出码——硬门禁「回归当天修」语义属 M4 门禁生效后。
    else:
        hard_bad = [r for r in budgets if r["tier"] == "hard"
                    and r["state"] not in ("not-armed",)]
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
