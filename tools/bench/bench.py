#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bench.py — 测量套件（PLAN-005 B 段 L0；PLAN-006 L2 数字面 + 武装断言；
PLAN-007 L2 单 iced 化——Q2 中期裁定落账）。

战略语义（docs/strategy/002-north-star-v2.md §5 测量模式阶梯）：
  L0 = VM+merged（日常，无绝对性能效力——报告价值 = 启动链形状分解 +
       结构回归代理[编辑路径全量读检测] + 缓冲区类基线记账[rope 前禁调优]）
  L1 = VM+RQ（上游 §6 渲染臂覆盖缺口 blocked）
  L2 = a2r+release+**单 iced**（唯一有预算效力；PLAN-006 建成数字面，原为
       rqhost 预热拓扑；PLAN-007 随 Q2 中期裁定改独立渲染零旗标直拉——
       steady_start 武装，renderer_cold_start 过渡期 n/a 注记）

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

# ---------------- PLAN-007 L2 数字面（单 iced 直拉：Q2 中期拓扑）----------------
# Q2 中期裁定（2026-09-22，用户原文见 docs/strategy/002 补注九）：RQ 架构
# 重写中段（上游 PLAN-683 远程 renderer 路线），auto-edit 交付拓扑中期收敛
# 单 iced 自包含。L2 运行器随裁：release 产物**零旗标直拉**（PLAN-007 T-00
# 实锚——生成物 main.rs autodesk gate：--autodesk-render 三态属 client 臂，
# 带 launcher 无 rqhost 走 broker rendezvous 需宿主；零旗标 = run_app_
# devtools 纯独立 iced 窗）。rqhost 生命周期（rq-up/rq-down/daemon 采纳
# 双门）随拓扑退役；renderer_cold_start 过渡期 n/a（进程内无分离冷启面，
# pending 上游 683 重设计后重估）。
L2_POLL_S = 0.002              # L2 标记轮询粒度（80ms 级预算 → 2ms 档；L0 保持 25ms）
STEADY_BUDGET_MS = 80.0        # 战略 §2.1 steady_start 硬预算
# 拓扑有效性观测（替代 PLAN-006 的 daemon「window opened」双门）：app 日志
# 出现后端就绪行 + 进程存活（单 iced 无 adopt 握手，窗口创建即 iced 事件
# 循环启动；PLAN-007 T-00 探针实证该行与 BENCH 标记的到达序）。
BACKEND_READY_LINE = "Running with Iced backend"

EXIT_OK, EXIT_FAIL, EXIT_BLOCKED = 0, 1, 3

# 供料包归因（docs/upstream/2026-09-m1-supply.md）
BLOCK_L1 = ("VM+RQ 渲染臂 codeeditor 覆盖缺口（native_queue_set 缺 kind，"
            "实例死于「拒绝渲染，禁静默错绘」语义）——供料包 §6。")
BLOCK_L2 = ("L2 链上游阻塞：a2r 词汇门——PLAN-007 装载链新内建（code_editor_"
            "edit/delta、File.read_text_range）无 trans/ui_gen 映射（681 清偿"
            "面外，docs/upstream 登记；L2 锚点补跑随上游解阻另收）——"
            "perf.py 链 exit 3 归因透传。")

# 编辑路径全量读检测：code_editor_text 允许位 = editor_store.at 的 save
# 上下文 handler（A 段即其首个绿证）。
STORE_FILE = "editor_store.at"
# PLAN-008: 白名单扩为「save 位 + 登记的保真/转换 handler」（封闭集、登记制不变）——
# WriteFidelity=保真回写收口（ActSave/QuitSaveClose 改道，code_editor_text
# 唯一读出位）；EolConvert=行尾转换命令（显式全文操作，T-03 登记件）。
# PLAN-009: ReplaceAllRequest=全部替换命令（第三件显式全文操作——读出+
# 重写同 EolConvert 形态，读出经 back regex_replace 端点，T-03 登记件；
# 查找/下一处/find-in-files 路径零全文读——search prop 增量 diff 进内核
# + back 行级流式，不受检测器影响）。
ALLOWED_HANDLERS = {"ActSave", "QuitSaveClose", "WriteFidelity", "EolConvert",
                    "ReplaceAllRequest"}


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
    """yield (lineno, handler_name_or_None, line)——handler 归属按花括号深度。

    头行形态兼认 `.Name -> {` 与带参 `.Name(arg, ..) -> {`（PLAN-008 修正：
    白名单登记件 WriteFidelity/EolConvert 均为带参 handler，旧正则不认
    参数组、整段误归 <顶层> 使登记失效——构造性红证的登记→绿腿暴露）。
    """
    cur, depth = None, 0
    for i, line in enumerate(text.splitlines(), 1):
        if cur is None:
            m = re.match(r"\s*\.(\w+)(\([^)]*\))?\s*->", line)
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

    code_editor_text 的允许位 = editor_store.at 内登记的 save 上下文
    handler（ActSave/QuitSaveClose 两 save 位 + WriteFidelity 保真回写
    收口 + EolConvert 行尾转换命令——PLAN-008 白名单扩容，封闭集登记制
    不变）；其余任何 front 文件/handler 出现即红。注释行不计。
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
# L2 终态序（§5.2 表）：not-armed 位被 armed 顶替，余行保持记账语义但
# 携带 L2 实测数字（rope 前后对照锚点）。PLAN-007：单 iced 下
# renderer_cold_start 无分离观测面 → armed-record 位由 arch-blocked-note
# 顶替（armed-record 随 rqhost 拓扑退役，历史基线 JSONL 在档）。
_L2_STATE_ORDER = ["armed", "pending-feature", "arch-blocked",
                   "arch-blocked-note", "blocked-upstream", "ledger"]


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
                "blocked-upstream，观测缺席——§10-1 默认采用+注记）；单 iced "
                "口径（Q2 中期裁定 2026-09-22）：预热语义=进程内 iced 初始化"
                "含、系统暖机弃首跑；fail=记录性判定（首基线锚点，硬门禁"
                "「回归当天修」属 M4 门禁生效后，战略补注 6(d)）")
    if rid == "renderer_cold_start":
        entry["measured_ms"] = None
        return ("arch-blocked-note",
                "PLAN-007 单 iced 过渡期 n/a：进程内无分离冷启面（rqhost "
                "拓扑随 Q2 中期裁定退役）；pending 上游 683 重设计后重估"
                "（budgets.json validity 同步注记）")
    state, note = _L0_STATES[rid]
    if rid in ("open_100mb", "open_1gb"):
        mb = 100 if rid == "open_100mb" else 1024
        v = m.get("open_ms", {}).get(mb)
        if v is not None:
            entry["l2_open_ms"] = v       # rope 前后对照锚点（1gb 无 fixture 则缺省）
    if rid == "idle_mem":
        entry["l2_app_mem_bytes"] = m.get("idle_mean_bytes")
        note += "；L2 附 app 实测（单 iced 无守护单列；预算随 Q2）"
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


def _backend_ready_seen(log_path: Path, timeout_s: float = 8.0) -> bool:
    """app 日志是否出现后端就绪行（单 iced 拓扑有效性门之一，PLAN-007）。

    耐心轮询：进程引导（含依赖装载）先后于该行；给足 8s。"""
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            if BACKEND_READY_LINE in log_path.read_text(
                    encoding="utf-8", errors="replace"):
                return True
        except OSError:
            pass
        time.sleep(0.005)
    return False


def run_release_tracked(env_extra: dict, want_markers: list[str],
                        timeout_s: float, log_name: str,
                        mem_after: list[str] | None = None) -> dict:
    """L2 形状（PLAN-007 单 iced）：零旗标直拉 release 产物，2ms 轮询。
    每跑独立（自带渲染与窗口），跑毕按 PID 收编——无 daemon 序列保活。"""
    exe = _release_exe()
    if exe is None:
        _log("FATAL: release 产物缺席（rust-workspace/target/release/auto-edit.exe）")
        sys.exit(EXIT_FAIL)
    return _spawn_tracked([str(exe)], env_extra, want_markers, timeout_s,
                          log_name, mem_after, poll_s=L2_POLL_S)


def _l2_env_extra(fp: dict) -> dict:
    exe = _release_exe()
    mtime = (datetime.fromtimestamp(exe.stat().st_mtime).isoformat(timespec="minutes")
             if exe else "<absent>")
    return {"release_exe": str(exe) if exe else "<absent>",
            "release_exe_mtime": mtime,
            "topology": "single-iced（Q2 中期裁定 2026-09-22；零旗标直拉，"
                        "rqhost 生命周期随拓扑退役）"}


def _l2_topology_ok(r: dict) -> bool:
    """单 iced 拓扑有效性门：后端就绪行 + 进程存活（PLAN-007，替代
    PLAN-006 的 daemon「window opened」+ adopt 双门）。"""
    return bool(r["alive_at_end"]) and _backend_ready_seen(Path(r["log"]))


def _l2_suite(runs: int, sizes: list[int], fp: dict) -> dict | None:
    """L2 数字面（PLAN-007 单 iced 形态）：启动分解（零旗标直拉，steady_
    start=spawn→bench_ws_loaded 代理口径）+ 打开计时。每跑独立收编。

    a2r 门（perf.py a2r）在 stage_proxy 前置——PLAN-007 装载链新内建无
    trans 映射时整链 exit 3 归因（§10-2 降级口径：L0 承载内存锚点）。
    """
    exe = _release_exe()
    if exe is None:
        _log("FATAL: release 产物缺席——门控链应已编译，查 rust-workspace/target/release/")
        return None
    app_pids: list[int] = []
    try:
        _log(f"启动链分解（L2）：{runs} 跑（首跑弃暖机）——单 iced 零旗标直拉 {exe.name}")
        startup: list[dict] = []
        for i in range(runs):
            r = run_release_tracked(
                {"AUTO_BENCH": "1"},
                want_markers=["bench_vm_init", "bench_ws_loaded"],
                timeout_s=45.0, log_name=f"l2-startup-{i}",
                mem_after=["bench_ws_loaded"])
            app_pids.append(r["pid"])
            m = r["markers"]
            if "bench_vm_init" not in m or "bench_ws_loaded" not in m:
                _log(f"FATAL: L2 run{i} 标记缺失（得 {sorted(m)}，日志 {r['log']}）"
                     "——武装断言需数字，按真失败处理")
                return None
            if not _l2_topology_ok(r):
                _log(f"FATAL: L2 run{i} 拓扑无效（app 存活={r['alive_at_end']}，"
                     "后端就绪行未达——单 iced 门）——数字不纳入")
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
            _log(f"打开计时（L2）{mb}MB（fixture 生成 {gen_s:.2f}s，gitignored）")
            r = run_release_tracked(
                {"AUTO_BENCH": "1", "AUTO_OPEN_PATH": str(fixture)},
                want_markers=["bench_open_start", "bench_open_done"],
                timeout_s=_open_timeout_s(mb), log_name=f"l2-open-{mb}mb",
                mem_after=["bench_open_done"])
            app_pids.append(r["pid"])
            m = r["markers"]
            if "bench_open_start" not in m or "bench_open_done" not in m:
                _log(f"FATAL: L2 open {mb}MB 标记缺失（得 {sorted(m)}，日志 {r['log']}）")
                return None
            if not _l2_topology_ok(r):
                _log(f"FATAL: L2 open {mb}MB 拓扑无效（app 存活={r['alive_at_end']}，"
                     "后端就绪行未达——单 iced 门）")
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
        return {"startup": startup, "opens": opens}
    finally:
        for pid in app_pids:
            _kill_pid(pid)
        _log(f"app 实例统一收编（{len(app_pids)} 个，按 PID）")


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


def _open_timeout_s(mb: int) -> float:
    """打开计时超时按尺寸缩放（PLAN-007：分块装载的 edit O(n·k) 成本——
    S1 固有 S2 债，4MB 块下 100MB 曾超 120s 窗实测未捕获；16MB 块下
    100MB ~90s 量级，给 60s 引导 + 4s/MB 余量）。"""
    return max(120.0, 60.0 + mb * 4.0)


def _open_timing(sizes: list[int]) -> list[dict]:
    out = []
    for mb in sizes:
        fixture, gen_s = make_fixture(mb)
        _log(f"打开计时 {mb}MB（fixture 生成 {gen_s:.2f}s，gitignored）")
        r = run_app_tracked(
            {"AUTO_BENCH": "1", "AUTO_OPEN_PATH": str(fixture)},
            want_markers=["bench_open_start", "bench_open_done"],
            timeout_s=_open_timeout_s(mb), log_name=f"open-{mb}mb",
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
        _log("mode l2（a2r+release+单 iced）：perf.py a2r 起链")
        rc = subprocess.run([sys.executable, str(PERF_PY), "a2r"]).returncode
        if rc == EXIT_BLOCKED:
            _log(f"BLOCKED: {BLOCK_L2}")
            return EXIT_BLOCKED
        if rc != EXIT_OK:
            _log(f"FATAL: perf.py a2r 失败 rc={rc}")
            return EXIT_FAIL
        _log("a2r 绿——继续 release（PLAN-007：单 iced 无 rq-up 段）"
             "，proxy 数字面按 L2 评估（硬门禁武装）")
        rc = subprocess.run([sys.executable, str(PERF_PY), "release"]).returncode
        if rc != EXIT_OK:
            _log(f"BLOCKED/FATAL: perf.py release rc={rc}")
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
        lines.append({"type": "startup_runs", "warmup_discarded": True,
                      "runs": data["startup"]})
        lines.append({"type": "open_timing", "sizes": data["opens"]})
        steady = [r["steady_start_ms"] for r in data["startup"] if not r["warmup"]]
        idle = [r["mem_idle"][0] for r in data["startup"]
                if not r["warmup"] and r["mem_idle"] and r["mem_idle"][0]]
        metrics = {
            "steady_runs_ms": steady,
            "steady_mean_ms": round(sum(steady) / len(steady), 1) if steady else None,
            "open_ms": {r["size_mb"]: r["open_ms"] for r in data["opens"]},
            "idle_mean_bytes": round(sum(idle) / len(idle)) if idle else None,
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
                   if r["tier"] == "hard"
                   and str(r.get("state", "")).startswith("armed")
                   and r.get("measured_ms") is None]
        if unarmed:
            _log(f"FATAL: L2 武装行无实测数字：{unarmed}（武装断言缺数；"
                 "renderer_cold_start 单 iced 过渡期 n/a 不在武装位）")
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
    mode = "l0"
    for ln in path.read_text(encoding="utf-8").splitlines():
        d = json.loads(ln)
        if d.get("type") == "budget_assert":
            rows = d["rows"]
            mode = d.get("mode", "l0")
    if rows is None:
        _log("FATAL: 该结果文件无 budget_assert 记录")
        return EXIT_FAIL
    # PLAN-014 T-03（006 §F-01）：行序取自记录 mode 字段——l2 文件按
    # L2 终态序重放（not-armed 位在 L2 被 armed 顶替，缺省序会打出
    # 误导性「缺：not-armed」）；l0/l1 文件维持五态缺省序。
    _print_budget_table(rows,
                        order=_L2_STATE_ORDER if mode == "l2" else _STATE_ORDER)
    return EXIT_OK



# ═════════════════════════════════════════════════════════════════════
# PLAN-011 T-05: diff 计时档（G-5/AC-06）。
#
# 档位（T-00 §10 校准重定形——file_cap 10k 行/1MB 下原计划预判的
# 1/10/100MB 档全落上限外；AC-06 本质=计时框架+基线+blocked 标注，
# 档位按定参重铸，SD-02/§10 同步）：
#   diff_small      1000 行对·散点改（档内现实态）→ 基线墙钟
#   diff_mid        2500 行对·散点改（近上限）→ 基线墙钟
#   diff_over_size  1.2MB 对 → 尺寸门即时拒墙钟 + blocked-on-upstream
#   diff_over_lines 10500 行对 → 行数门拒墙钟 + blocked-on-upstream
# blocked 口径：档外全文大文件 diff=架构阻塞（AutoVM str split 上限，
# T-00 实测 0.01-0.52ms/行随工具链漂移）——引擎 diff_snapshots
# （docs/upstream/2026-09-diff-engine-supply.md §5）时代清偿；门拒
# 延迟证明上限门即时性（防长等语义，fsys.at 尺寸门 pre-read）。
# 退出码 0=记录性基线锚点（无硬预算行——过渡计算层，引擎时代作废）。

def _diff_fixture_pair(d: Path, name: str, n_lines: int, variant: str) -> dict:
    """生成 a/b fixture 对。variant=scatter（每 37 行改一处，行数同）/
    size（1.2MB 长行）/lines（10500 短行，仅 a 侧足量，b 短——门拒在
    读前，形态无关）。"""
    d.mkdir(parents=True, exist_ok=True)
    pa, pb = d / f"{name}.a.txt", d / f"{name}.b.txt"
    if variant == "size":
        blob = ("x" * 120 + chr(10)) * 10486  # ≈1.2MB
        pa.write_text(blob, encoding="utf-8")
        pb.write_text(blob, encoding="utf-8")
    elif variant == "lines":
        pa.write_text(chr(10).join(f"L{i}" for i in range(10500)), encoding="utf-8")
        pb.write_text("short" + chr(10), encoding="utf-8")
    else:
        a = [f"line {i:05d} of {name} content" for i in range(n_lines)]
        b = list(a)
        for i in range(0, n_lines, 37):
            b[i] = f"line {i:05d} CHANGED payload"
        pa.write_text(chr(10).join(a) + chr(10), encoding="utf-8")
        pb.write_text(chr(10).join(b) + chr(10), encoding="utf-8")
    return {"a": str(pa), "b": str(pb)}


def stage_diff() -> int:
    import urllib.request
    import urllib.parse
    import socket as _socket

    exe = _auto_exe()
    fp = _fingerprint()
    _log(f"diff 档（PLAN-011 T-05）toolchain: {fp.get('version', '?')}")

    fixdir = FIXTURES / "diff"
    tiers = [
        {"id": "diff_small", "fx": _diff_fixture_pair(fixdir, "small", 1000, "scatter"),
         "kind": "baseline"},
        {"id": "diff_mid", "fx": _diff_fixture_pair(fixdir, "mid", 2500, "scatter"),
         "kind": "baseline"},
        {"id": "diff_over_size", "fx": _diff_fixture_pair(fixdir, "oversize", 0, "size"),
         "kind": "gate-reject"},
        {"id": "diff_over_lines", "fx": _diff_fixture_pair(fixdir, "overlines", 0, "lines"),
         "kind": "gate-reject"},
    ]

    port = None
    for cand in range(9460, 9560):
        with _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", cand)) != 0:
                port = cand
                break
    env = {**os.environ, "AUTO_PROJECT_DIR": str(PROJECT)}
    proc = subprocess.Popen(
        [exe, "run", "--server", "vm", "-B", str(port)],
        cwd=PROJECT, env=env,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    base = f"http://127.0.0.1:{port}"
    try:
        up = False
        for _ in range(40):
            try:
                urllib.request.urlopen(base + "/api/ws_root", timeout=2)
                up = True
                break
            except Exception:  # noqa: BLE001
                time.sleep(1)
        if not up:
            _log("FATAL: diff 档 app 未起（--server vm）")
            return EXIT_FAIL

        rows = []
        for t in tiers:
            q = urllib.parse.urlencode({"path_a": t["fx"]["a"],
                                        "path_b": t["fx"]["b"], "ctx": 3})
            url = f"{base}/api/diff_files?{q}"
            walls = []
            err_seen = ""
            adds = dels = -1
            degraded = False
            for attempt in range(4):  # 首跑暖机弃
                t0 = time.perf_counter()
                try:
                    with urllib.request.urlopen(url, timeout=60) as resp:
                        import json as _json
                        env_obj = _json.loads(resp.read().decode("utf-8"))
                        if isinstance(env_obj, str):
                            env_obj = _json.loads(env_obj)
                    wall = (time.perf_counter() - t0) * 1000.0
                    err_seen = env_obj.get("err", "") or ""
                    adds, dels = env_obj.get("adds", -1), env_obj.get("dels", -1)
                    degraded = bool(env_obj.get("degraded", False))
                except Exception as e:  # noqa: BLE001
                    wall = (time.perf_counter() - t0) * 1000.0
                    err_seen = f"<http {e}>"
                if attempt > 0:
                    walls.append(round(wall, 1))
                time.sleep(0.2)
            med = sorted(walls)[len(walls) // 2] if walls else None
            verdict = ("baseline" if t["kind"] == "baseline"
                       else "gate-reject (blocked-on-upstream: 全文大文件 "
                            "diff 待引擎 diff_snapshots，供料 §5)")
            rows.append({"id": t["id"], "kind": t["kind"],
                         "wall_ms_runs": walls, "wall_ms_median": med,
                         "adds": adds, "dels": dels, "degraded": degraded,
                         "err": err_seen[:120], "verdict": verdict})
            _log(f"  {t['id']}: median={med}ms kind={t['kind']} "
                 f"+{adds}/-{dels} err={err_seen[:40]!r}")

        outfile = RESULTS / f"diff-{_ts()}.jsonl"
        with open(outfile, "w", encoding="utf-8", newline=chr(10)) as f:
            f.write(json.dumps({"type": "diff_timing", "toolchain": fp}, ensure_ascii=False) + chr(10))
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + chr(10))
        _log(f"结果 JSONL → {outfile}")
        bad = [r for r in rows if r["kind"] == "baseline"
               and r["wall_ms_median"] is None]
        if bad:
            _log(f"FATAL: 基线档无数字：{[r['id'] for r in bad]}")
            return EXIT_FAIL
        return EXIT_OK
    finally:
        if proc.poll() is None:
            proc.kill()
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)],
                       capture_output=True)


# PLAN-013 T-04: 大文件档（G-5/AC-05）——50MB 档 mode on/off 代理对照。
#   big49mb          49MB（<阈值——auto 高亮臂）open 链计时+RSS
#   big50mb          50MB（=阈值——plain 旁路臂）open 链计时+RSS
#   big100mb         100MB（plain 臂域内上探）
# 对照语义（代理口径，L0 无预算效力——注记成文）：mode 无独立开关面
# （big 由装载前探测派生，v1 契约）——mode 臂=**尺寸杠杆**（49MB auto
# vs 50MB plain），差值=旁路收益代理指标（load_file 原生同构下，差异
# 面=渲染高亮路径+VM 探测门+池驻留形态；RSS 峰值为进程树工作集，
# 687 锚 100MB→219MB 为 a2r release 域，本档=L0 vm merged debug 域
# 不可直比——只作档内对照与漂移哨兵）。退出码 0=记录性（无硬预算行）。

def _bigfile_fixture(path: Path, total: int) -> float:
    t0 = time.perf_counter()
    unit = b"".join(
        (b"line %08d bigfile bench fixture padding ........\n" % i)
        for i in range(512))
    per = len(unit)
    with open(path, "wb") as f:
        written = 0
        while written < total - per:
            f.write(unit)
            written += per
        if written < total:
            f.write(b"x" * (total - written - 1) + b"\n")
    return time.perf_counter() - t0


def stage_bigfile() -> int:
    exe = _auto_exe()
    fp = _fingerprint()
    _log(f"bigfile 档（PLAN-013 T-04）toolchain: {fp.get('version', '?')}")
    FIXTURES.mkdir(exist_ok=True)
    mb_unit = 1024 * 1024
    sizes = [(49, "auto 臂（阈值下）"), (50, "plain 臂（=阈值）"),
             (100, "plain 臂（域内上探）")]
    rows = []
    for mb, note in sizes:
        fx = FIXTURES / f"bigfile-{mb}mb.txt"
        gen_s = _bigfile_fixture(fx, mb * mb_unit)
        _log(f"bigfile {mb}MB（fixture 生成 {gen_s:.2f}s，gitignored）——{note}")
        r = run_app_tracked(
            {"AUTO_BENCH": "1", "AUTO_OPEN_PATH": str(fx)},
            want_markers=["bench_open_start", "bench_open_done"],
            timeout_s=max(180.0, 60.0 + mb * 4.0),
            log_name=f"bigfile-{mb}mb",
            mem_after=["bench_open_done"])
        m = r["markers"]
        mem = r["mem"].get("bench_open_done")
        rec = {"id": f"big{mb}mb", "size_mb": mb, "arm": note,
               "open_ms": (m["bench_open_done"] - m["bench_open_start"])
               if "bench_open_start" in m and "bench_open_done" in m else None,
               "spawn_to_open_ms": m.get("bench_open_start"),
               "mem_loaded_bytes": mem[0] if mem else None,
               "fixture_gen_s": round(gen_s, 3)}
        rows.append(rec)
        mem_mb = rec["mem_loaded_bytes"] and round(rec["mem_loaded_bytes"] / mb_unit)
        _log(f"  {rec['id']}: open={rec['open_ms'] and round(rec['open_ms'])}ms "
             f"mem={mem_mb}MB")
    outfile = RESULTS / f"bigfile-{_ts()}.jsonl"
    with open(outfile, "w", encoding="utf-8", newline=chr(10)) as f:
        f.write(json.dumps({"type": "bigfile_timing", "toolchain": fp,
                            "note": "mode on/off=尺寸杠杆代理对照（49 auto/50+100 plain）；"
                                    "L0 无预算效力"},
                           ensure_ascii=False) + chr(10))
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + chr(10))
    _log(f"结果 JSONL → {outfile}")
    bad = [r["id"] for r in rows if r["open_ms"] is None]
    if bad:
        _log(f"FATAL: 档无数字：{bad}")
        return EXIT_FAIL
    return EXIT_OK


def main() -> int:
    ap = argparse.ArgumentParser(description="auto-edit 测量套件（PLAN-005 B 段）")
    ap.add_argument("cmd", choices=["check", "proxy", "assert", "diff", "bigfile"])
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
    if args.cmd == "diff":
        return stage_diff()
    if args.cmd == "bigfile":
        return stage_bigfile()
    if args.cmd == "proxy":
        return stage_proxy(args.runs, args.full, args.mode)
    return stage_assert(args.results)


if __name__ == "__main__":
    sys.exit(main())
