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
import tempfile
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

    返回 {"markers": {name: ms_since_spawn}, "app_epoch": {name: epoch_ms},
          "mem": {name: (bytes, method)}, "log": path, "pid": pid,
          "alive_at_end": bool}。markers=host 侧 perf_counter（对照列）；
    app_epoch=app 内 epoch 毫秒（PLAN-014 T-07 供④ time 族接线——标记行
    下一裸数字行；host 时间戳自此降对照列，一跑双录）。
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
    app_epoch: dict[str, int] = {}
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
                    # PLAN-014 T-07: 标记行下一裸数字行=app 侧 epoch 毫秒
                    # （editor_store.at BENCH 面；缺席=None 零破坏）。
                    m2 = re.search(rf"BENCH {m}\r?\n(\d+)", text)
                    if m2:
                        app_epoch[m] = int(m2.group(1))
            for m in (mem_after or []):
                if m in markers and m not in mems:
                    mems[m] = _sample_mem(proc.pid)
            if len(markers) == len(want_markers) and \
                    all(m in mems for m in (mem_after or [])):
                if on_complete is not None:
                    on_complete()
                break
        return {"markers": markers, "app_epoch": app_epoch, "mem": mems,
                "log": str(log), "pid": proc.pid,
                "alive_at_end": proc.poll() is None}
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
    "steady_start": ("not-armed", "硬门禁仅在 L2 评估（战略 §5 阶梯）；M4 "
                     "门槛行——分解锚点在档（stage steady，PLAN-018 T-04）；"
                     "正式武装判定待供① 解阻（a2r release 直拉）"),
    "renderer_cold_start": ("not-armed", "硬门禁仅在 L2 评估；预算值待 Q2 "
                            "拓扑（上游 683 重设计 pending 维持）"),
    "warm_start": ("ledger", "锚点在档（PLAN-018 stage warm：20 tab 恢复懒"
                   "装载墙钟+不读盘面——M2 交付 PLAN-010）；断言化=供① 后 "
                   "L2 形态（M4 收口）"),
    "open_100mb": ("ledger", "解锁待测→锚点在档（PLAN-018 stage open：100MB "
                   "装载墙钟 N 跑谱 results/open-*.jsonl；big 态语义=fsize"
                   "≥50MB 探测门 plain 旁路臂）；禁调优随 rope[673]+分块读"
                   "[687] 交付解除；硬判定（≤1s+滚动不掉帧）待供① 后 L2 "
                   "正式评估"),
    "open_1gb": ("ledger", "解锁待测→拒绝位实证（PLAN-018 stage open：1GB"
                 ">512MB 超大拒绝位〔013 Q-3 定参〕——可打开待门放开重测；"
                 "513MB 边界对照在档）；战略 ledger 态记录"),
    "type_latency": ("blocked-upstream", "内核帧时间戳插桩（T-03 勘无 .at 层"
                     "通道）——供② 排队（docs/upstream/2026-09-m4-perf-"
                     "unblock-supply.md）"),
    "scroll_fps": ("blocked-upstream", "帧率测量需内核插桩；大文件满帧率另需 "
                   "rope——供② 排队（m4-perf-unblock-supply）"),
    "diff_100mb": ("ledger", "引擎时代实测判定在案（PLAN-016 修复轮 stage_diff "
                   "diff_100mb 档 ≤2000ms 全链墙钟，JSONL 在 results/）；L2 "
                   "硬门禁 M4 收口"),
    "idle_mem": ("ledger", "L0 采样记账不阻塞；锚点在档（PLAN-018 stage "
                 "warm：空窗/20tab 两形态采样）；预算断言 M4 收口"),
    "installer": ("ledger", "Q3 裁定+019 数字在档；PLAN-023 收口（2026-10-02 "
                  "用户重基线——独立渲染期 ≤50MB/RQHost 后回归 ≤20MB）：V2b "
                  "终态手段集 30,403,072B armed PASS（余量 22.0MB；abort 因 "
                  "catch_unwind×17 冲突面出局——evidence-p023-survey §③）；"
                  "构建通道 tools/portable/build_portable.py）——≤50MB 判定 "
                  "armed 绿"),
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
    """L2 语义逐行终态（§5.2 表）。entry 原位附加实测/判定字段。

    PLAN-021 判定升级：open_100mb/idle_mem 在 L2 数字在场时 armed
    （预算行判定生效——pass/fail 记录性语义同 steady）；warm_start/
    diff_100mb 的判定谱由专用档承载（bench warm/diff --l2），本面
    ledger 位+在档注记（本 suite 不测该两行——数字不冒领）。"""
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
    if rid == "open_100mb":
        v = m.get("open_ms", {}).get(100)
        if v is not None:
            entry["l2_open_ms"] = v
            entry["verdict"] = ("pass" if v <= 1000.0 else "fail")
            return ("armed",
                    "L2 武装（PLAN-021 判定升级）：全量装载墙钟（BENCH 标记"
                    "包夹，big 态语义）vs ≤1s；「滚动不掉帧」半行=供② 解阻"
                    "后；N≥4 判定谱=bench open --l2 专用档（budgets.json "
                    "validity——本行数字=proxy 单跑对照）")
    if rid == "idle_mem":
        v = m.get("idle_mean_bytes")
        entry["l2_app_mem_bytes"] = v
        if v is not None:
            # PLAN-023 重基线（2026-10-02 用户裁定）：≤60MB→≤150MB——语义
            # =独立渲染期渲染暖态预算（wgpu 缓存 ~100MB 级）；空窗测量位
            # 维持如实记录；RQHost 后回归 ≤10MB 级（budgets.json validity）。
            entry["verdict"] = ("pass" if v <= 150 * 1048576 else "fail")
            return ("armed",
                    "L2 武装（PLAN-021 判定升级；PLAN-023 重基线 ≤150MB）："
                    "空窗 app 工作集 mean vs ≤150MB（psutil/WorkingSet64，"
                    "单 iced 无守护单列）；N 跑谱=bench warm --l2 专用档")
        state, note = _L0_STATES[rid]
        return state, note + "；L2 附 app 实测（单 iced 无守护单列；预算随 Q2）"
    state, note = _L0_STATES[rid]
    if rid in ("open_100mb", "open_1gb"):
        mb = 100 if rid == "open_100mb" else 1024
        v = m.get("open_ms", {}).get(mb)
        if v is not None:
            entry["l2_open_ms"] = v       # rope 前后对照锚点（1gb 无 fixture 则缺省）
    if rid in ("warm_start", "diff_100mb"):
        note += "；L2 判定谱在档（PLAN-021 专用档 JSONL+budgets.json validity）"
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
            ae = r.get("app_epoch", {})
            rec = {"run": i, "warmup": i == 0,
                   "spawn_to_vm_init_ms": round(m["bench_vm_init"], 1),
                   "vm_init_to_ws_loaded_ms":
                       round(m["bench_ws_loaded"] - m["bench_vm_init"], 1),
                   "steady_start_ms": round(m["bench_ws_loaded"], 1),
                   "app_ws_load_ms": (ae.get("bench_ws_loaded")
                                      - ae.get("bench_vm_init")
                                      if ae.get("bench_vm_init")
                                      and ae.get("bench_ws_loaded") else None),
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
        ae = r.get("app_epoch", {})
        # PLAN-014 T-07: open_ms 改源 app 内 epoch 差（供④ time 族）——
        # host 侧 perf_counter 差降对照列（一跑双录）。
        app_open_ms = (ae.get("bench_open_done") - ae.get("bench_open_start")
                       if ae.get("bench_open_start")
                       and ae.get("bench_open_done") else None)
        host_open_ms = (round(m["bench_open_done"] - m["bench_open_start"], 1)
                        if "bench_open_start" in m
                        and "bench_open_done" in m else None)
        # T-07 勘定（2026-09-25）：app_epoch 面=上游供④ vue 映射缺口在册
        # （time.* 限定调用 vue 臂 TS2304——front ms 行撤回）；open_ms 先回
        # 落 host 源，供件落地后 app 源自动接管（双录字段在册）。
        rec = {"size_mb": mb,
               "open_ms": app_open_ms if app_open_ms is not None else host_open_ms,
               "open_ms_host": host_open_ms,
               "spawn_to_open_start_ms": m.get("bench_open_start"),
               "mem_loaded": r["mem"].get("bench_open_done"),
               "fixture_gen_s": round(gen_s, 3)}
        out.append(rec)
        _log(f"  {mb}MB: open={rec['open_ms'] and rec['open_ms']}ms(app) "
             f"host={rec['open_ms_host'] and round(rec['open_ms_host'])}ms "
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
        # PLAN-018: 默认目标过滤为含 budget_assert 记录的最新文件——
        # results/ 现含多档 JSONL（diff-/bigfile-/open-/steady-/warm-
        # 前缀，011/013/018 起），纯文件名序取最新会撞非 proxy 档
        # （无 budget_assert 记录→FATAL）。
        cands = sorted(RESULTS.glob("*.jsonl"))
        if not cands:
            _log("FATAL: 无既往 results 文件（先跑 proxy，或 --results 指定）")
            return EXIT_FAIL
        path = None
        for cand in reversed(cands):
            try:
                if any(json.loads(ln).get("type") == "budget_assert"
                       for ln in cand.read_text(encoding="utf-8")
                       .splitlines() if ln.strip()):
                    path = cand
                    break
            except (OSError, json.JSONDecodeError):
                continue
        if path is None:
            _log("FATAL: results/ 无含 budget_assert 记录的文件"
                 "（先跑 proxy，或 --results 指定）")
            return EXIT_FAIL
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
# PLAN-011 T-05: diff 计时档（G-5/AC-06）——PLAN-016 修复轮改造：
# 引擎时代（PLAN-703 供料+PLAN-704 缺陷修复）门退场，档位重铸。
#
# 档位：
#   diff_small        1000 行对·散点改（档内现实态）→ 基线墙钟
#   diff_mid          2500 行对·散点改（近上限）→ 基线墙钟
#   diff_over_size    1.2MB 全等对 → 通过延迟（trim 快路 0 hunk 实证）
#   diff_over_lines   10500 行对 → 通过延迟（门退场——超限正常出结果）
#   diff_100mb        ~100MB 散点改对（生成式，1% 散点=上游 T-04 基准
#                     形态对齐）→ **预算判定 ≤2000ms**（战略 §2.1 预算
#                     行——超限=红 EXIT_FAIL，性能是发布门槛）
#   diff_100mb_full   （PLAN-022 T-02，仅 --l2）全量形对照档——数字在档
#                     不判定（021 armed FAIL 5183.2ms 对照面）；判定档切
#                     窗口形（/api/diff_files_window limit=600 渲染 cap
#                     对齐「出结果」口径=全量 hunks/counts/rows_total+
#                     首窗 rows——016 消费面零改动 frozen③：L0 VM 形维持
#                     全量旧径；供⑧ 已清偿[上游 r3 改签 9921+裸名臂]——
#                     调用不可用）
# 计时口径=/api/diff_files 全链墙钟（app --server vm，debug 工具链——
# 保守上界形态：引擎 release 相对量 0.35-0.9s 在档，绝对量判定以此
# 全链数为准，703 Q-2 口径）。退出码 0=全档绿（基线有数+budget 判定
# ≤2s）。

def _diff_fixture_pair(d: Path, name: str, n_lines: int, variant: str) -> dict:
    """生成 a/b fixture 对。variant=scatter（每 37 行改一处，行数同）/
    size（1.2MB 长行全等）/lines（10500 短行 vs 短 b——门退场通过形）/
    mb100（~100MB 散点改对——生成式临时构造不入库，013 先例；每 100
    行改 1 处=1% 散布改，与上游 diff_bench 基准形态对齐）。"""
    d.mkdir(parents=True, exist_ok=True)
    pa, pb = d / f"{name}.a.txt", d / f"{name}.b.txt"
    if variant == "size":
        blob = ("x" * 120 + chr(10)) * 10486  # ≈1.2MB
        pa.write_text(blob, encoding="utf-8")
        pb.write_text(blob, encoding="utf-8")
    elif variant == "lines":
        pa.write_text(chr(10).join(f"L{i}" for i in range(10500)), encoding="utf-8")
        pb.write_text("short" + chr(10), encoding="utf-8")
    elif variant == "mb100":
        line_a = "line {0:07d} of p016-100mb diff benchmark payload content"
        n = 0
        written = 0
        target = 100 * 1024 * 1024
        with open(pa, "w", encoding="utf-8", newline="") as fa, \
                open(pb, "w", encoding="utf-8", newline="") as fb:
            while written < target:
                for k in range(100):
                    fa.write(line_a.format(n + k) + chr(10))
                    if k == 0:
                        fb.write(line_a.format(n + k) + " CHANGED" + chr(10))
                    else:
                        fb.write(line_a.format(n + k) + chr(10))
                    written += len(line_a.format(n + k)) + 1
                n += 100
        return {"a": str(pa), "b": str(pb)}
    else:
        a = [f"line {i:05d} of {name} content" for i in range(n_lines)]
        b = list(a)
        for i in range(0, n_lines, 37):
            b[i] = f"line {i:05d} CHANGED payload"
        pa.write_text(chr(10).join(a) + chr(10), encoding="utf-8")
        pb.write_text(chr(10).join(b) + chr(10), encoding="utf-8")
    return {"a": str(pa), "b": str(pb)}


def _workspace_back_exe() -> Path | None:
    """a2r 转译后端产物（PLAN-021 diff L2 直拉形态——axum 独立进程）。"""
    ws = Path(os.environ.get("AUTO_RUST_WORKSPACE") or PROJECT / "rust-workspace")
    exe = ws / "target" / "release" / "auto-edit-back.exe"
    return exe if exe.exists() else None


def stage_diff(l2: bool = False) -> int:
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
         "kind": "pass-latency"},
        {"id": "diff_over_lines", "fx": _diff_fixture_pair(fixdir, "overlines", 0, "lines"),
         "kind": "pass-latency"},
        {"id": "diff_100mb", "fx": _diff_fixture_pair(fixdir, "big100mb", 0, "mb100"),
         "kind": "budget"},
    ]
    if l2:
        # PLAN-022 T-02：判定档切窗口形（窗口端点 r3 改签 9921——rows_limit=600 对齐 front
        # 渲染 cap「出结果」口径=全量 hunks/counts/rows_total+首窗 rows），
        # 全量形保留为对照档（kind=full-ref——数字在档不判定）。
        tiers.append({"id": "diff_100mb_full",
                      "fx": tiers[-1]["fx"], "kind": "full-ref"})

    port = None
    for cand in range(9460, 9560):
        with _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", cand)) != 0:
                port = cand
                break
    env = {**os.environ, "AUTO_PROJECT_DIR": str(PROJECT)}
    back_exe = None
    if l2:
        back_exe = _workspace_back_exe()
        if back_exe is None:
            _log("FATAL: --l2 要求 release 后端产物在位（rust-workspace/target/"
                 "release/auto-edit-back.exe——先 perf.py release）")
            return EXIT_FAIL
        env["AUTO_HTTP_PORT"] = str(port)
        _log(f"diff L2 直拉形态：a2r 转译后端 {back_exe.name} @:{port}"
             "（016 server 侧计算主导语义同型——VM 解释器离场）")
        proc = subprocess.Popen([str(back_exe)], cwd=PROJECT, env=env,
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)
    else:
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
        # 计时卫生（PLAN-016 修复轮勘定）：fixture 生成（diff_100mb 档
        # ~200MB 落盘）与计时之间留 writeback 沉降窗——生成后立即计时
        # 会与 OS 脏页回写竞争文件读（实测 +600ms 失真：bench 2034ms vs
        # 静置分解同链 1437ms）。
        time.sleep(5.0)
        for t in tiers:
            # PLAN-022 T-02：L2 判定档 diff_100mb 切窗口形（窗口端点 9921 五参——
            # offset=0/limit=600）；L0 VM 形维持全量旧径（016 判定形态零
            # 扰动；供⑧ 已清偿后 VM 轨窗口贯通——L0 维持全量旧径=016 对照形态续用）。
            if l2 and t["id"] == "diff_100mb":
                q = urllib.parse.urlencode({"path_a": t["fx"]["a"],
                                            "path_b": t["fx"]["b"], "ctx": 3,
                                            "rows_offset": 0,
                                            "rows_limit": 600})
                url = f"{base}/api/diff_files_window?{q}"
            else:
                q = urllib.parse.urlencode({"path_a": t["fx"]["a"],
                                            "path_b": t["fx"]["b"], "ctx": 3})
                url = f"{base}/api/diff_files?{q}"
            walls = []
            err_seen = ""
            adds = dels = -1
            degraded = False
            rows_total = None
            # PLAN-022 T-02：重判谱 N≥4（021 谱 3 跑扩容——首跑弃暖机后
            # 4 个计时样本）。
            for attempt in range(5 if l2 else 4):  # 首跑暖机弃
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
                    rows_total = env_obj.get("rows_total")
                except Exception as e:  # noqa: BLE001
                    wall = (time.perf_counter() - t0) * 1000.0
                    err_seen = f"<http {e}>"
                if attempt > 0:
                    walls.append(round(wall, 1))
                time.sleep(0.2)
            med = sorted(walls)[len(walls) // 2] if walls else None
            if t["kind"] == "baseline":
                verdict = "baseline"
            elif t["kind"] == "pass-latency":
                verdict = ("pass-latency (引擎时代：门退场——超限文件正常出"
                           "结果 err=''；PLAN-704 修复轮改造)")
            elif t["kind"] == "full-ref":
                verdict = ("full-ref（全量形对照档——数字在档不判定；021 "
                           "armed FAIL 5183.2ms 在档[diff-20260930-205147]"
                           "——清偿前后对照面）")
            elif l2:
                ok_budget = (med is not None and err_seen == ""
                             and med <= 2000.0 and rows_total is not None)
                verdict = (f"budget {'PASS' if ok_budget else 'FAIL'} "
                           f"(≤2000ms 战略 §2.1 预算行——窗口形判定 "
                           f"rows_limit=600 渲染 cap 对齐「出结果」口径="
                           f"全量 hunks/counts/rows_total[{rows_total}]+"
                           f"首窗 rows)")
            else:
                ok_budget = med is not None and err_seen == "" and med <= 2000.0
                verdict = (f"budget {'PASS' if ok_budget else 'FAIL'} "
                           f"(≤2000ms 战略 §2.1 预算行——全链墙钟)")
            rows.append({"id": t["id"], "kind": t["kind"],
                         "wall_ms_runs": walls, "wall_ms_median": med,
                         "adds": adds, "dels": dels, "degraded": degraded,
                         "rows_total": rows_total,
                         "err": err_seen[:120], "verdict": verdict})
            _log(f"  {t['id']}: median={med}ms kind={t['kind']} "
                 f"+{adds}/-{dels} err={err_seen[:40]!r}")

        outfile = RESULTS / f"diff-{_ts()}.jsonl"
        with open(outfile, "w", encoding="utf-8", newline=chr(10)) as f:
            head = {"type": "diff_timing", "toolchain": fp,
                    "form": "l2-direct" if l2 else "l0-vm-server"}
            if l2:
                head["release_back"] = str(back_exe)
                head["form_note"] = _L2_FORM_NOTE
            else:
                head["toolchain_note"] = "VM server（auto run --server vm）——" \
                                         "016 判定形态（diff 专用先例）"
            f.write(json.dumps(head, ensure_ascii=False) + chr(10))
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + chr(10))
        _log(f"结果 JSONL → {outfile}")
        bad = [r for r in rows if r["kind"] == "baseline"
               and r["wall_ms_median"] is None]
        if bad:
            _log(f"FATAL: 基线档无数字：{[r['id'] for r in bad]}")
            return EXIT_FAIL
        budget_bad = [r for r in rows if r["kind"] == "budget"
                      and ("FAIL" in r["verdict"] or r["err"])]
        if budget_bad:
            _log(f"FATAL: 预算档超限/错误："
                 f"{[(r['id'], r['wall_ms_median'], r['err'][:40]) for r in budget_bad]}")
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


# ═════════════════════════════════════════════════════════════════════
# PLAN-018: M4 锚点档（G-3/G-4/G-5）——open/steady/warm 三档。
#
# 形态=「记账不阻塞」锚点（frozen 约束①）：release 工具链全链
# （AUTO_BIN 指 release 构建 auto——016 diff_100mb 判定先例），L0
# `run -r vm` 直拉；硬判定维持 L2 唯一预算效力（供① 解阻后切正主
# L2 形态——a2r 现势探针仍 blocked，tests/evidence-p018-survey.md
# §①-b/§⑤），本档数字入 budgets validity 注记位。
# 计时源=host perf_counter（app epoch 双录通道=供④ vue 映射缺口
# 在册 m1-supply §17，front ms 行撤回——open_ms 走 host 回退源，
# 如实注记）。启动级档 2ms 轮询（L2_POLL_S——tens-of-ms 锚点粒度），
# 装载级档 25ms（L0 形状粒度——秒级锚点足够）。
# APPDATA 卫生：锚点档一律隔离 APPDATA（tmpdir）——打开链
# SessionSave 与会话恢复链均锚 $APPDATA/auto-edit-session.json，
# 隔离保护用户真实会话且空目录=「全新启动」纯态（矩阵 T11 先例；
# 既有 proxy open 链未隔离=观察件 want，非本件面）。

def _probe_fixture(path: Path, total: int) -> float:
    """拒绝位探针 fixture（truncate 形）：逻辑尺寸达标、内容零填充——
    拒绝路径仅 file_size 元数据读零内容消费（T-00③ 裁定）；门放开
    后需真内容重造。"""
    t0 = time.perf_counter()
    with open(path, "wb") as f:
        f.seek(total - 1)
        f.write(b"\n")
    return time.perf_counter() - t0


def _open_fixture(path: Path, mb: int) -> float:
    """装载锚点 fixture（重复行+散点差异——滚动/高亮真实负载形，
    013/016 生成式先例不入库）：行号唯一化行体+每 100 行 1 行
    CHANGED 散点（1% 散布）。"""
    t0 = time.perf_counter()
    target = mb * 1024 * 1024
    n = 0
    written = 0
    with open(path, "w", encoding="utf-8", newline="") as f:
        while written < target:
            for k in range(100):
                line = (f"line {n + k:08d} of p018 open anchor payload"
                        + (" CHANGED" if k == 0 else ""))
                f.write(line + "\n")
                written += len(line) + 1
            n += 100
    return time.perf_counter() - t0


def _dump_rows(outfile: Path, head: dict, rows: list[dict]) -> None:
    with open(outfile, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(head, ensure_ascii=False) + "\n")
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    _log(f"结果 JSONL → {outfile}")


def stage_open(runs: int, l2: bool = False) -> int:
    """PLAN-018 T-03（G-3/AC-03）：open_100mb/open_1gb 锚点档。

    100MB 生成式文本装载墙钟 ×N（首跑弃暖机）+513MB 拒绝位对照
    +1GB 尝试（>512MB 同门拒绝=战略 ledger 态记录——「可打开」待
    门放开重测，不硬造假象；013 Q-3 定参 upstream §16）。big 态
    注记：100MB 必经 fsize≥50MB 探测门（plain 旁路臂）——装载
    墙钟=big 态语义数字。计时卫生=fixture 生成后沉降窗 5s（016
    writeback 教训）。退出码 0=锚点齐。PLAN-021 --l2：release 产物
    零旗标直拉=正式武装判定谱（≤1s 判定生效）。"""
    exe = _auto_exe()
    fp = _fingerprint()
    if runs < 2:
        _log("FATAL: --runs 至少 2（首跑弃暖机语义）")
        return EXIT_FAIL
    RESULTS.mkdir(exist_ok=True)
    FIXTURES.mkdir(exist_ok=True)
    rows: list[dict] = []

    fx100 = FIXTURES / "open-100mb.txt"
    gen_s = _open_fixture(fx100, 100)
    _log(f"open 100MB fixture 生成 {gen_s:.2f}s（gitignored）——沉降窗 5s"
         "（writeback 计时卫生，016 教训）")
    time.sleep(5.0)
    walls: list[float] = []
    for i in range(runs):
        with tempfile.TemporaryDirectory(prefix="bench-p018-appdata-") as ad:
            r = _spawn_tracked(
                _spawn_cmd(exe, l2),
                {"AUTO_BENCH": "1", "AUTO_OPEN_PATH": str(fx100),
                 "APPDATA": ad, "AUTO_PROJECT_DIR": str(PROJECT)},
                ["bench_open_start", "bench_open_done"],
                timeout_s=_open_timeout_s(100), log_name=f"open100-{i}",
                mem_after=["bench_open_done"])
        if l2 and not _l2_topology_ok(r):
            _log(f"FATAL: L2 open run{i} 拓扑无效（app 存活="
                 f"{r['alive_at_end']}，后端就绪行未达——单 iced 门）")
            return EXIT_FAIL
        m = r["markers"]
        ok = "bench_open_start" in m and "bench_open_done" in m
        wall = round(m["bench_open_done"] - m["bench_open_start"], 1) if ok else None
        rec = {"id": "open_100mb", "run": i, "warmup": i == 0, "open_ms": wall,
               "spawn_to_open_start_ms": m.get("bench_open_start"),
               "big_state": "on（fsize≥50MB 探测门——plain 旁路臂）",
               "mem_loaded": r["mem"].get("bench_open_done"),
               "log": r["log"]}
        rows.append(rec)
        if ok and i > 0:
            walls.append(wall)
        _log(f"  run{i}{'(暖机弃)' if i == 0 else ''}: open={wall}ms "
             f"mem={rec['mem_loaded'] and rec['mem_loaded'][0] // 1048576}MB")

    for label, mb, note in (("reject_513mb", 513, "拒绝位边界+1B 对照"),
                            ("open_1gb", 1024, "1GB 尝试——同门拒绝=ledger 态记录")):
        fxp = FIXTURES / f"open-{label}.txt"
        gen_s = _probe_fixture(fxp, mb * 1024 * 1024)
        _log(f"{label} 探针 fixture 生成 {gen_s:.2f}s（truncate 形——拒绝路径"
             "零内容消费）——沉降窗 2s")
        time.sleep(2.0)
        with tempfile.TemporaryDirectory(prefix="bench-p018-appdata-") as ad:
            r = _spawn_tracked(
                _spawn_cmd(exe, l2),
                {"AUTO_BENCH": "1", "AUTO_OPEN_PATH": str(fxp),
                 "APPDATA": ad, "AUTO_PROJECT_DIR": str(PROJECT)},
                ["bench_open_rejected"],
                timeout_s=120.0, log_name=f"open-{label}",
                mem_after=["bench_open_rejected"])
        rejected = "bench_open_rejected" in r["markers"]
        rows.append({"id": label, "size_mb": mb, "rejected": rejected,
                     "note": note, "log": r["log"]})
        _log(f"  {label}: rejected={rejected}")

    med = sorted(walls)[len(walls) // 2] if walls else None
    if l2:
        open_verdict = ("pass（L2 直拉形态武装判定：median ≤1s 预算行内——"
                        "硬门禁正式判定绿；滚动不掉帧半行=供② 解阻后）"
                        if med is not None and med <= 1000.0 else
                        "fail（L2 直拉形态 median >1s——归因+瘦身后续件，"
                        "本件不实施[018 Q-2 口径]）")
    else:
        open_verdict = ("记账注记：装载墙钟=纯装载时长（标记包夹）——big 态"
                        "语义；≤1s 硬判定待供① 后 L2 正式评估（本档=记账）")
    summary = {"id": "open_100mb_summary", "runs_ms": walls,
               "median_ms": med, "min_ms": min(walls) if walls else None,
               "max_ms": max(walls) if walls else None,
               "budget_ms": 1000.0, "verdict": open_verdict,
               "note": "装载墙钟=纯装载时长（标记包夹）——big 态语义；"
                       "判定谱口径见 verdict"}
    rows.append(summary)
    _log(f"open_100mb 谱：{walls} median={med}ms")
    _dump_rows(RESULTS / f"open-{_ts()}.jsonl",
               {"type": "open_anchor", "toolchain": fp,
                "form": "l2-direct" if l2 else "l0-vm",
                "toolchain_note": _L2_FORM_NOTE if l2 else _L0_FORM_NOTE},
               rows)
    bad = [r["id"] for r in rows if r["id"] == "open_100mb"
           and r["open_ms"] is None]
    bad += [r["id"] for r in rows if "rejected" in r and not r["rejected"]]
    if bad:
        _log(f"FATAL: 档缺数字/拒绝形未现：{bad}")
        return EXIT_FAIL
    return EXIT_OK


# ═════════════════════════════════════════════════════════════════════
# PLAN-021: L2 直拉形态档（G-2）——018 三锚点档+diff 档的 L2 化。
#
# 形态=战略 §5 L2（唯一预算效力）：a2r 转译+release 编译+单 iced 零旗标
# 直拉（PLAN-007 拓扑）；diff 档=release auto-edit-back（a2r 转译 axum
# 后端）打 /api/diff_files——016「server 侧计算主导」语义同型，VM 解释
# 器离场。018 锚点的「release 工具链全链记账形态」（`run -r vm`）保留为
# 对照谱（不冒领纪律随数字入 budgets validity 注记）。
# --l2 旗标共用 018 档全部测量卫生（APPDATA 隔离/AUTO_PROJECT_DIR 钉位/
# fixture 沉降窗/2ms 轮询/首跑弃暖机），仅换 spawn 目标+加单 iced 拓扑
# 有效性门（alive+后端就绪行——_l2_suite 同门）。

_L2_FORM_NOTE = "L2 直拉形态（PLAN-021：a2r release 零旗标——武装判定谱）"
_L0_FORM_NOTE = "release 工具链全链记账形态（016 先例）——非 L2 武装判定"


def _spawn_cmd(exe: str, l2: bool) -> list[str]:
    """spawn 目标形态：L0=`auto run -r vm`；L2=release 产物零旗标直拉。"""
    if l2:
        rel = _release_exe()
        if rel is None:
            _log("FATAL: --l2 要求 release 产物在位（rust-workspace/target/"
                 "release/auto-edit.exe——先 perf.py release）")
            sys.exit(EXIT_FAIL)
        return [str(rel)]
    return [exe, "run", "-r", "vm"]


def _startup_decomp(exe: str, tag: str, want: list[str],
                    timeout_s: float, l2: bool = False) -> dict | None:
    """单跑启动链分解（2ms 轮询，隔离 APPDATA）。返回 _spawn_tracked
    结果或 None（标记缺失/拓扑无效）。l2=True 加单 iced 拓扑门。"""
    with tempfile.TemporaryDirectory(prefix="bench-p018-appdata-") as ad:
        r = _spawn_tracked(_spawn_cmd(exe, l2),
                           {"AUTO_BENCH": "1", "APPDATA": ad,
                            # ws_root 显式钉位（stage_diff 先例）——会话
                            # 恢复 ws_dir 匹配门由构造保证。
                            "AUTO_PROJECT_DIR": str(PROJECT)},
                           want, timeout_s=timeout_s, log_name=tag,
                           mem_after=["bench_ws_loaded"], poll_s=L2_POLL_S)
    if l2 and not _l2_topology_ok(r):
        _log(f"FATAL: {tag} 拓扑无效（app 存活={r['alive_at_end']}，"
             "后端就绪行未达——单 iced 门）——数字不纳入")
        return None
    missing = [k for k in want if k not in r["markers"]]
    if missing:
        _log(f"FATAL: {tag} 标记缺失（得 {sorted(r['markers'])}，日志 {r['log']}）")
        return None
    return r


def stage_steady(runs: int, l2: bool = False) -> int:
    """PLAN-018 T-04（G-4/AC-04）：steady_start 启动链分解归因档。

    release 工具链全链形态分解数字表（进程起→逻辑 init→workspace）
    ×N（首跑弃暖机，2ms 轮询）+≤80ms 对表（达标=绿注记位；未达标=
    分段归因清单——瘦身实施=后续件，frozen 约束④）。空窗纯态（隔离
    APPDATA=无会话恢复）。PLAN-021 --l2：release 产物零旗标直拉=
    正式武装判定谱（VM boot 段离场——018 归因「spawn→vm_init 224.5ms
    主导」是否随形态消失=本档观察重点，Q-2 口径）。"""
    exe = _auto_exe()
    fp = _fingerprint()
    if runs < 2:
        _log("FATAL: --runs 至少 2（首跑弃暖机语义）")
        return EXIT_FAIL
    RESULTS.mkdir(exist_ok=True)
    recs: list[dict] = []
    for i in range(runs):
        r = _startup_decomp(exe, f"steady-{i}",
                            ["bench_vm_init", "bench_ws_loaded"], 45.0, l2=l2)
        if r is None:
            return EXIT_FAIL
        m = r["markers"]
        mem = r["mem"].get("bench_ws_loaded")
        rec = {"run": i, "warmup": i == 0,
               "spawn_to_vm_init_ms": round(m["bench_vm_init"], 1),
               "vm_init_to_ws_loaded_ms":
                   round(m["bench_ws_loaded"] - m["bench_vm_init"], 1),
               "steady_start_ms": round(m["bench_ws_loaded"], 1),
               "mem_idle": mem}
        recs.append(rec)
        _log(f"  run{i}{'(暖机弃)' if i == 0 else ''}: "
             f"steady={rec['steady_start_ms']}ms "
             f"(init={rec['spawn_to_vm_init_ms']} + "
             f"ws={rec['vm_init_to_ws_loaded_ms']}) "
             f"mem={mem and mem[0] // 1048576}MB")
    steady = [r["steady_start_ms"] for r in recs if not r["warmup"]]
    mean = round(sum(steady) / len(steady), 1) if steady else None
    init_mean = round(sum(r["spawn_to_vm_init_ms"] for r in recs
                          if not r["warmup"]) / len(steady), 1)
    ws_mean = round(sum(r["vm_init_to_ws_loaded_ms"] for r in recs
                        if not r["warmup"]) / len(steady), 1)
    med = sorted(steady)[len(steady) // 2] if steady else None
    if l2:
        verdict = ("pass（L2 直拉形态武装判定：mean ≤80ms 预算行内——"
                   "硬门禁正式判定绿）"
                   if mean is not None and mean <= STEADY_BUDGET_MS else
                   "fail（L2 直拉形态 >80ms——归因清单：见分段均值；"
                   "瘦身实施=后续件，本件不实施[frozen 约束④]）")
    else:
        verdict = ("pass（≤80ms 预算行内——绿注记位：M4 门槛行 release 工具链"
                   "记账形态达标；正式武装判定仍待供① 后 L2 形态）"
                   if mean is not None and mean <= STEADY_BUDGET_MS else
                   "fail（>80ms——归因清单：见分段均值；瘦身实施=后续件，"
                   "本件不实施[frozen 约束④]）")
    rows = [{"id": "steady_summary", "runs_ms": steady, "mean_ms": mean,
             "median_ms": med,
             "budget_ms": STEADY_BUDGET_MS, "verdict": verdict,
             "segments_mean_ms": {"spawn_to_vm_init": init_mean,
                                  "vm_init_to_ws_loaded": ws_mean},
             "note": "分解=进程起（host spawn）→逻辑 init（bench_vm_init）"
                     "→workspace（bench_ws_loaded）；首帧段=勘无通道"
                     "（供② 排队）；2ms 轮询粒度"}]
    _log(f"steady_start 对表：mean={mean}ms vs ≤{STEADY_BUDGET_MS:.0f}ms "
         f"→ {verdict[:40]}…")
    _dump_rows(RESULTS / f"steady-{_ts()}.jsonl",
               {"type": "steady_decomp", "toolchain": fp,
                "form": "l2-direct" if l2 else "l0-vm",
                "toolchain_note": _L2_FORM_NOTE if l2 else _L0_FORM_NOTE},
               recs + rows)
    if mean is None:
        return EXIT_FAIL
    return EXIT_OK


def stage_warm(runs: int, l2: bool = False) -> int:
    """PLAN-018 T-05（G-5/AC-05）：warm_start/idle_mem 锚点档。

    空窗纯态 ×N（idle_mem 空窗形）+20tab 会话恢复 ×N（warm_start
    墙钟=spawn→恢复链→active 装载完成；会话 20×10MB 生成式注入
    隔离 APPDATA）。不读盘断言=墙钟平坦+内存平坦双证：懒装载语义
    下非 active 19 tab 零装载——若全量装载，恢复墙钟应显 200MB 读
    盘量级且 RSS +20×内容量（013 拒绝位外推同法）。PLAN-021 --l2：
    release 产物零旗标直拉=正式武装判定谱。"""
    exe = _auto_exe()
    fp = _fingerprint()
    if runs < 2:
        _log("FATAL: --runs 至少 2（首跑弃暖机语义）")
        return EXIT_FAIL
    RESULTS.mkdir(exist_ok=True)
    rows: list[dict] = []

    # 空窗纯态
    empty_mem = []
    for i in range(runs):
        r = _startup_decomp(exe, f"warm-empty-{i}",
                            ["bench_vm_init", "bench_ws_loaded"], 45.0, l2=l2)
        if r is None:
            return EXIT_FAIL
        m = r["markers"]
        mem = r["mem"].get("bench_ws_loaded")
        rec = {"id": "idle_empty", "run": i, "warmup": i == 0,
               "spawn_to_ws_loaded_ms": round(m["bench_ws_loaded"], 1),
               "mem_idle": mem}
        rows.append(rec)
        if not rec["warmup"] and mem and mem[0]:
            empty_mem.append(mem[0])
        _log(f"  empty run{i}: ws={rec['spawn_to_ws_loaded_ms']}ms "
             f"mem={mem and mem[0] // 1048576}MB")

    # 20tab 会话注入（10MB×20=200MB 负载——不读盘断言的信号形）
    warm_dir = FIXTURES / "warm"
    warm_dir.mkdir(parents=True, exist_ok=True)
    files = []
    gen_s = 0.0
    for i in range(20):
        p = warm_dir / f"warm-{i:02d}.txt"
        gen_s += _open_fixture(p, 10)
        files.append(p)
    _log(f"20tab 会话 fixture 生成 {gen_s:.2f}s（10MB×20，gitignored）"
         "——沉降窗 5s")
    time.sleep(5.0)
    session = {"ws_dir": str(PROJECT), "active": 0,
               "tabs": [{"path": str(p), "title": p.name, "cline": 1,
                         "ccol": 1} for p in files],
               "recents": []}
    warm_ms: list[float] = []      # 恢复链（预算行锚点：spawn→恢复完成）
    load_ms: list[float] = []      # active 装载段（打开链域，单列）
    usable_ms: list[float] = []    # spawn→可输入（信息列）
    warm_mem = []
    for i in range(runs):
        with tempfile.TemporaryDirectory(prefix="bench-p018-appdata-") as ad:
            (Path(ad) / "auto-edit-session.json").write_text(
                json.dumps(session), encoding="utf-8")
            r = _spawn_tracked(_spawn_cmd(exe, l2),
                               {"AUTO_BENCH": "1", "APPDATA": ad,
                                "AUTO_PROJECT_DIR": str(PROJECT)},
                               ["bench_vm_init", "bench_ws_loaded",
                                "bench_session_restored",
                                "bench_open_start", "bench_open_done"],
                               timeout_s=60.0, log_name=f"warm-{i}",
                               mem_after=["bench_open_done"],
                               poll_s=L2_POLL_S)
        if l2 and not _l2_topology_ok(r):
            _log(f"FATAL: L2 warm run{i} 拓扑无效（app 存活="
                 f"{r['alive_at_end']}，后端就绪行未达——单 iced 门）")
            return EXIT_FAIL
        m = r["markers"]
        need = ["bench_session_restored", "bench_open_done"]
        if any(k not in m for k in need):
            _log(f"FATAL: warm run{i} 标记缺失（得 {sorted(m)}，日志 {r['log']}）")
            return EXIT_FAIL
        mem = r["mem"].get("bench_open_done")
        rec = {"id": "warm_20tab", "run": i, "warmup": i == 0,
               "spawn_to_vm_init_ms": round(m["bench_vm_init"], 1),
               "vm_init_to_ws_loaded_ms":
                   round(m["bench_ws_loaded"] - m["bench_vm_init"], 1),
               "restore_chain_ms":
                   round(m["bench_session_restored"], 1),
               "restore_net_ms":
                   round(m["bench_session_restored"]
                         - m["bench_ws_loaded"], 1),
               "active_load_ms":
                   round(m["bench_open_done"] - m["bench_session_restored"], 1),
               "usable_ms": round(m["bench_open_done"], 1),
               "mem_loaded": mem}
        rows.append(rec)
        if not rec["warmup"]:
            warm_ms.append(rec["restore_chain_ms"])
            load_ms.append(rec["active_load_ms"])
            usable_ms.append(rec["usable_ms"])
            if mem and mem[0]:
                warm_mem.append(mem[0])
        _log(f"  warm run{i}: restore={rec['restore_chain_ms']}ms "
             f"load={rec['active_load_ms']}ms "
             f"usable={rec['usable_ms']}ms "
             f"mem={mem and mem[0] // 1048576}MB")

    e_mean = round(sum(empty_mem) / len(empty_mem)) if empty_mem else None
    w_mean = round(sum(warm_mem) / len(warm_mem)) if warm_mem else None
    warm_mean = (round(sum(warm_ms) / len(warm_ms), 1)
                 if warm_ms else None)
    load_mean = (round(sum(load_ms) / len(load_ms), 1)
                 if load_ms else None)
    usable_mean = (round(sum(usable_ms) / len(usable_ms), 1)
                   if usable_ms else None)
    # 恢复净段（ws_loaded→session_restored，原始标记差——预算行真锚）：
    # 全链含进程/VM boot 段（≈steady_start 同源归因，供① 后 L2 形态
    # 自然消解），恢复操作本身=净段（2ms 轮询粒度下限）。
    net_ms = [r["restore_net_ms"] for r in rows
              if r["id"] == "warm_20tab" and not r["warmup"]]
    net_mean = round(sum(net_ms) / len(net_ms), 1) if net_ms else None
    delta_mem_mb = (round((w_mean - e_mean) / 1048576)
                    if e_mean and w_mean else None)
    if l2:
        restore_verdict = ("pass（L2 直拉形态武装判定：恢复净段 ≤120ms "
                           "预算行内——硬门禁正式判定绿）"
                           if net_mean is not None and net_mean <= 120.0 else
                           "fail（L2 直拉形态恢复净段 >120ms——归因见分段；"
                           "瘦身实施=后续件）")
    else:
        restore_verdict = ("pass（恢复净段 ≤120ms 预算行内——绿注记位；全链"
                           "含 boot 段归因=steady_start 同源，供① 后 L2 形态"
                           "自然消解）"
                           if net_mean is not None and net_mean <= 120.0 else
                           "fail（恢复净段 >120ms——归因见分段；瘦身实施="
                           "后续件）")
    verdict = (f"记账注记：恢复净段（ws_loaded→恢复完成，20 tab 结构重建"
               f"懒装载）mean={net_mean}ms vs ≤120ms → {restore_verdict}"
               f"全链（spawn→恢复）mean={warm_mean}ms 其中 boot≈"
               f"{round((warm_mean or 0) - (net_mean or 0), 1)}ms"
               "（steady_start 同源归因）；不读盘面=标记单对实证（每跑仅 "
               "1 次 open_start/done——非 active 19 tab 零装载，log 可复核）"
               "；active 装载段 mean="
               f"{load_mean}ms 单列（打开链域=open 行语义，不计入本行）；"
               f"Δmem(20tab-空窗)={delta_mem_mb}MB=active 单文件装载+语法臂"
               "成本记录（10MB<50MB 非 big 态全语法路径——放大归因注记，"
               "不作为不读盘判据）")
    rows.append({"id": "warm_summary",
                 "restore_chain_runs_ms": warm_ms,
                 "restore_chain_mean_ms": warm_mean,
                 "restore_net_runs_ms": net_ms,
                 "restore_net_mean_ms": net_mean, "budget_ms": 120.0,
                 "restore_verdict": restore_verdict,
                 "active_load_runs_ms": load_ms,
                 "active_load_mean_ms": load_mean,
                 "usable_runs_ms": usable_ms,
                 "usable_mean_ms": usable_mean,
                 "idle_mem_empty_mean_bytes": e_mean,
                 "idle_mem_20tab_mean_bytes": w_mean,
                 "idle_mem_delta_mb": delta_mem_mb,
                 "verdict": verdict})
    _log(f"恢复净段 mean={net_mean}ms vs ≤120ms；全链 mean={warm_mean}ms；"
         f"active 装载 mean={load_mean}ms；Δmem(20tab-空窗)={delta_mem_mb}MB")
    _dump_rows(RESULTS / f"warm-{_ts()}.jsonl",
               {"type": "warm_idle_anchor", "toolchain": fp,
                "form": "l2-direct" if l2 else "l0-vm",
                "toolchain_note": _L2_FORM_NOTE if l2 else _L0_FORM_NOTE},
               rows)
    if warm_mean is None:
        return EXIT_FAIL
    return EXIT_OK



# ═════════════════════════════════════════════════════════════════════
# PLAN-022 T-03: 帧两行档（G-3）——type_latency/scroll_fps 断言化+
# steady 首帧段。供⑨ 清偿后（716 r3 T-15 出口形 int lane）首判。
#
# 形态=L0 VM debug 工具链（`run -r vm` 单进程——iced 渲染器+VM+MCP
# 同进程；读回=MCP autoui_state 帧探针字段 fprobe_*〔editor_store.at
# 双门采样臂——AUTO_BENCH+AUTO_FRAME_BENCH〕+stdout 标记
# BENCH fprobe_first〔首帧值实录〕）。debug 解释段=保守上界
# （release/a2r 形态更快——保守方向判定：上界过判则快形必过）。
# 判定口径（SD-01 PLAN-022 节成文）：
#   type_latency=帧内（键入帧 begin→下一 present 差），P95 ≤1 帧
#     （1000/面板 Hz；面板率=host EnumDisplaySettings 读回）；
#   scroll_fps=PageDown 连发窗内 distinct present 计数/帧值窗时长
#     ≥面板率×0.9（MCP 轮询采样=下界测量——下界过判则真值必过）；
#   first_present=帧探针首拍非零值（时源=frame_bench 首触定格
#     ——SD-B §3b 坐标注记：不含 spawn→首触段，记账位非判定）。
# 驱动协议（执行期勘定修正）：autoui_keyboard 键入/PageDown 不达
# 编辑器〔edits 零增实证——矩阵时代亦无键盘直驱先例〕→等价通道=
# autoui_type 直达 textarea（SrcChanged+CursorMoved 双臂在场）：
# type_latency=单字符连发；scroll_fps=换行连发（cursor-follow 滚动
# ——光标推进视图跟随，滚动相关性如实注记）。MCP 端口钉位=P716-D1
# 处方同款 924x 带绕开。

_FRAME_MCP_PORT_BASE = 9360
NLCHAR = chr(10)  # 换行驱动字符（避开源码转义层）


def _panel_hz() -> float:
    """面板刷新率读回（host EnumDisplaySettings 主显；缺席兜底 60）。"""
    try:
        import ctypes
        from ctypes import wintypes

        dm = wintypes.DEVMODEW()
        dm.dmSize = int(dm.dmSize) if dm.dmSize else ctypes.sizeof(dm)
        if ctypes.windll.user32.EnumDisplaySettingsW(None, -1,
                                                     ctypes.byref(dm)):
            hz = float(dm.dmDisplayFrequency)
            if hz >= 20:
                return hz
    except Exception:  # noqa: BLE001——host 面缺席不阻断（兜底 60）
        pass
    return 60.0


def _mcp_call(url: str, name: str, args_json: str) -> str:
    import urllib.request

    body = json.dumps({"jsonrpc": "2.0", "method": "tools/call",
                       "params": {"name": name, "arguments": args_json},
                       "id": 1}).encode()
    req = urllib.request.Request(url, data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode())
    content = data.get("result", {}).get("content", [])
    return content[0]["text"] if content else ""


def _mcp_state(url: str, fields: list) -> dict:
    """autoui_state 读回——dict[int]（缺席键不计）。"""
    import re as _re

    txt = _mcp_call(url, "autoui_state", {"fields": list(fields)})
    out = {}
    for line in txt.splitlines():
        m = _re.match(r"\s*(\w+):\s*(-?\d+)", line)
        if m:
            out[m.group(1)] = int(m.group(2))
    return out


def stage_frame() -> int:
    import urllib.request

    exe = _auto_exe()
    fp = _fingerprint()
    panel_hz = _panel_hz()
    frame_budget_ms = 1000.0 / panel_hz
    fps_threshold = panel_hz * 0.9
    _log(f"帧两行档（PLAN-022 T-03）toolchain: {fp.get('version', '?')} "
         f"panel={panel_hz:.0f}Hz budget={frame_budget_ms:.1f}ms "
         f"fps_threshold={fps_threshold:.1f}")

    # 滚动/键入 fixture（~120 行——换行连发可推进光标入滚动域；
    # 生成式不入库 013/016 先例）。
    fdir = FIXTURES / "frame"
    fdir.mkdir(parents=True, exist_ok=True)
    fx = fdir / "frame_drive.txt"
    if not fx.exists() or fx.stat().st_size < 5000:
        with open(fx, "w", encoding="utf-8", newline="") as f:
            for i in range(120):
                f.write(f"line {i:05d} frame drive payload content"
                        f"{' CHANGED' if i % 97 == 0 else ''}\n")

    port = None
    import socket as _socket
    for cand in range(_FRAME_MCP_PORT_BASE, _FRAME_MCP_PORT_BASE + 60):
        with _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", cand)) != 0:
                port = cand
                break
    ad = tempfile.mkdtemp(prefix="bench-p022-frame-appdata-")
    env = {**os.environ, "AUTO_BENCH": "1", "AUTO_FRAME_BENCH": "1",
           "AUTOUI_MCP_PORT": str(port), "APPDATA": ad,
           "AUTO_OPEN_PATH": str(fx), "AUTO_PROJECT_DIR": str(PROJECT)}
    app_log_path = os.path.join(ad, "app.log")
    log_f = open(app_log_path, "w", encoding="utf-8")
    proc = subprocess.Popen([exe, "run", "-r", "vm"], cwd=PROJECT, env=env,
                            stdout=log_f, stderr=subprocess.STDOUT)
    base = f"http://127.0.0.1:{port}/mcp"

    # textarea 定位（snapshot 唯一 textarea=code editor——装载异步，
    # 轮询等待元素现身 ≤15s）。
    ta_id = None
    for _ in range(15):
        try:
            m = re.search(r"textarea #(\w+)",
                          _mcp_call(base, "autoui_snapshot", {}))
            ta_id = m.group(1) if m else None
            if ta_id:
                break
        except Exception:  # noqa: BLE001
            pass
        time.sleep(1)
    if not ta_id:
        _log("FATAL: textarea（编辑器）元素未定位")
        return EXIT_FAIL

    def _type(text: str) -> bool:
        try:
            _mcp_call(base, "autoui_type",
                      {"element_id": ta_id, "text": text,
                       "clear_first": False})
            return True
        except Exception:  # noqa: BLE001
            return False

    rows = []
    exit_code = EXIT_OK
    try:
        up = False
        for _ in range(60):
            try:
                _mcp_state(base, ["fprobe_n"])
                up = True
                break
            except Exception:  # noqa: BLE001
                time.sleep(1)
        if not up:
            _log("FATAL: 帧档 app/MCP 未起")
            return EXIT_FAIL
        # 装载 settle（AUTO_OPEN_PATH 装载链自带；Tick 臂在场即可驱动）。
        time.sleep(6.0)

        # ---- first_present（记账位——帧值时源坐标） ----
        st0 = _mcp_state(base, ["fprobe_begin", "fprobe_present", "fprobe_n"])
        first_present = st0.get("fprobe_present") or 0
        rows.append({"id": "first_present", "value_ms": first_present,
                     "coord": ("frame_bench 首触时源（SD-B §3b——不含 "
                               "spawn→首触段；记账位非判定）"),
                     "verdict": "record"})
        _log(f"  first_present≈{first_present}ms（帧值坐标）")

        # ---- type_latency：键入驱动（editor 焦点自证=fprobe_n 递增） ----
        samples = []
        edits_base = None
        for k in range(30):
            if not _type("x"):
                _log(f"  key{k} 派发败")
                continue
            time.sleep(0.06)
            try:
                st = _mcp_state(base, ["fprobe_begin", "fprobe_present",
                                       "fprobe_n"])
            except Exception:  # noqa: BLE001
                continue
            samples.append((st.get("fprobe_begin") or 0,
                            st.get("fprobe_present") or 0,
                            st.get("fprobe_n") or 0))
        st_e = _mcp_state(base, ["edits"]) if samples else {}
        focus_ok = (len(samples) >= 10 and st_e.get("edits", 0) >= 3)
        lat = []
        for (b0, _p0, _n0), (b1, p1, _n1) in zip(samples, samples[1:]):
            if b0 > 0 and p1 >= b0 and p1 > 0:
                lat.append(p1 - b0)
        lat_sorted = sorted(lat)
        p50 = lat_sorted[len(lat_sorted) // 2] if lat_sorted else None
        p95 = (lat_sorted[min(len(lat_sorted) - 1,
                              int(len(lat_sorted) * 0.95))]
               if lat_sorted else None)
        tl_pass = p95 is not None and focus_ok and p95 <= frame_budget_ms
        rows.append({"id": "type_latency", "samples": len(samples),
                     "valid_pairs": len(lat), "p50_ms": p50, "p95_ms": p95,
                     "budget_ms": round(frame_budget_ms, 2),
                     "panel_hz": panel_hz, "focus_ok": focus_ok,
                     "verdict": "PASS" if tl_pass else "FAIL"})
        _log(f"  type_latency: P50={p50}ms P95={p95}ms "
             f"(≤{frame_budget_ms:.1f}ms) samples={len(samples)} "
             f"valid={len(lat)} focus_ok={focus_ok} "
             f"→ {'PASS' if tl_pass else 'FAIL'}")

        # ---- scroll_fps：PageDown 连发 + 密集轮询（下界测量） ----
        presents = []
        t_end = time.perf_counter() + 3.0
        k_i = 0
        while time.perf_counter() < t_end:
            _type(NLCHAR)
            k_i += 1
            for _ in range(4):
                try:
                    pv = _mcp_state(base, ["fprobe_present"]).get(
                        "fprobe_present") or 0
                    if pv > 0:
                        presents.append(pv)
                except Exception:  # noqa: BLE001
                    pass
                if time.perf_counter() >= t_end:
                    break
                time.sleep(0.004)
        uniq = sorted(set(presents))
        if len(uniq) >= 2:
            win_ms = uniq[-1] - uniq[0]
            fps = (len(uniq) - 1) / win_ms * 1000.0 if win_ms > 0 else 0.0
        else:
            win_ms = fps = 0.0
        sf_pass = fps >= fps_threshold
        rows.append({"id": "scroll_fps", "distinct_present": len(uniq),
                     "window_ms": round(win_ms, 1), "fps": round(fps, 2),
                     "panel_hz": panel_hz,
                     "threshold": round(fps_threshold, 2),
                     "verdict": "PASS" if sf_pass else "FAIL"})
        _log(f"  scroll_fps: {fps:.1f}fps（distinct={len(uniq)} "
             f"win={win_ms:.0f}ms ≥{fps_threshold:.1f}）→ "
             f"{'PASS' if sf_pass else 'FAIL'}")

        if not tl_pass or not sf_pass:
            exit_code = EXIT_FAIL
    finally:
        log_f.close()
        if proc.poll() is None:
            proc.kill()
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)],
                       capture_output=True)

    outfile = RESULTS / f"frame-{_ts()}.jsonl"
    with open(outfile, "w", encoding="utf-8", newline=chr(10)) as f:
        head = {"type": "frame_timing", "toolchain": fp,
                "form": "l0-vm-debug（保守上界——解释段最慢形）",
                "panel_hz": panel_hz,
                "form_note": ("供⑨ 清偿后首判（716 r3 T-15 int lane）；"
                              "读回=MCP autoui_state 帧探针字段+首帧标记")}
        f.write(json.dumps(head, ensure_ascii=False) + chr(10))
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + chr(10))
    _log(f"结果 JSONL → {outfile}")
    return exit_code


def main() -> int:
    ap = argparse.ArgumentParser(description="auto-edit 测量套件（PLAN-005 B 段）")
    ap.add_argument("cmd", choices=["check", "proxy", "assert", "diff", "bigfile",
                                    "open", "steady", "warm", "frame"])
    ap.add_argument("--runs", type=int, default=DEFAULT_RUNS,
                    help=f"启动分解跑数（默认 {DEFAULT_RUNS}，首跑弃暖机）")
    ap.add_argument("--full", action="store_true",
                    help="fixture 集含 512 MB（默认 1/10/100）")
    ap.add_argument("--mode", default="l0", choices=["l0", "l1", "l2"],
                    help="测量模式阶梯（默认 l0；l1/l2 经 perf.py 链归因）")
    ap.add_argument("--results", default=None, help="assert 命令的结果文件")
    ap.add_argument("--l2", action="store_true",
                    help="L2 直拉形态（PLAN-021）：open/steady/warm 以 "
                         "release 产物零旗标直拉、diff 以 release 后端"
                         "服务——武装判定谱档（默认 L0 记账形态不变）")
    args = ap.parse_args()
    if args.cmd == "check":
        return stage_check()
    if args.cmd == "diff":
        return stage_diff(args.l2)
    if args.cmd == "bigfile":
        return stage_bigfile()
    if args.cmd == "frame":
        return stage_frame()
    if args.cmd == "open":
        return stage_open(args.runs, args.l2)
    if args.cmd == "steady":
        return stage_steady(args.runs, args.l2)
    if args.cmd == "warm":
        return stage_warm(args.runs, args.l2)
    if args.cmd == "proxy":
        return stage_proxy(args.runs, args.full, args.mode)
    return stage_assert(args.results)


if __name__ == "__main__":
    sys.exit(main())
