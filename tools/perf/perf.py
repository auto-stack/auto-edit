#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""perf.py — PLAN-004 T-05..T-07：性能模式（L2）一键化编排。

战略语义（docs/strategy/002-north-star-v2.md §5 测量模式阶梯）：
  L0 = VM+merged（日常，无绝对性能效力）
  L2 = a2r + release + RQ（唯一有预算效力）——本工具的编排对象。

用法（自仓库根或任意目录）：
  python tools/perf/perf.py check           # 依赖自检 + 环境指纹（不启进程面）
  python tools/perf/perf.py a2r             # auto build -r rust 生成 rust-workspace
  python tools/perf/perf.py release         # cargo build --release（生成物）
  python tools/perf/perf.py rq-up           # 预热 rqhost 共享合成器（隔离实例）
  python tools/perf/perf.py rq-down         # 按 PID 收掉 rqhost
  python tools/perf/perf.py run [--track vm|rust]   # RQ 模式起一个 app 实例
  python tools/perf/perf.py smoke           # check→rq-up→双实例→验证→清理

退出码：0=绿；3=blocked-on-upstream（F-R1 / 工具链陈旧等）；1=真失败。

Windows-only（产品 Win first；命名管道/creationflags 均为 Win32 面）。
所有外部进程输出落 tools/perf/logs/（防管道阻塞，PLAN-003 坑位）。
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

HERE = Path(__file__).resolve().parent          # tools/perf
ROOT = HERE.parents[1]                          # 仓库根
# 目标工程：默认本仓 specs/auto-edit；PERF_PROJECT 可锚到主检出同路径
# （验证跑不污染 worktree——生成物 rust-workspace/ 等落主检出 gitignored 区，
# 分支与 main 在 app 代码零差异时等价）。
PROJECT = Path(os.environ.get("PERF_PROJECT")
               or ROOT / "specs" / "auto-edit")
LOGS = HERE / "logs"
RQ_JSON = HERE / ".rq.json"

# 隔离 well-known（生产常量为 autodesk-rqhost；后缀防与本机常驻实例串扰，
# 同 rqhost.rs RQHOST_WELLKNOWN_ENV 测试缝语义）。锁管道 = <wk>-lock。
WELLKNOWN = "autodesk-rqhost-edit004"

# 工具链版本门：含上游 PLAN-669 的最低构建号（v0.4.2-1588-g…）。
MIN_TOOLCHAIN_BUILD = 1588

# F-R1 特征（a2r server 生成器双缺口；供料包 docs/upstream/ §4）。
FR1_PATTERNS = ("E0432", "api::Db", "空体桩")

# RQ 渲染臂覆盖缺口特征（VM UI native-queue 臂拒绝渲染；供料包 §6）。
UNCOVERED_PATTERNS = ("臂视图未覆盖",)

EXIT_OK, EXIT_FAIL, EXIT_BLOCKED = 0, 1, 3

DETACHED = 0x00000008          # DETACHED_PROCESS
NEW_GROUP = 0x00000200         # CREATE_NEW_PROCESS_GROUP


def _log(msg: str) -> None:
    line = f"[perf {datetime.now():%H:%M:%S}] {msg}"
    print(line, flush=True)


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
    p = Path(exe)
    if p.exists():
        mtime = datetime.fromtimestamp(p.stat().st_mtime).isoformat(timespec="minutes")
    cargo = shutil.which("cargo")
    cargo_ver = subprocess.run([cargo, "--version"], capture_output=True, text=True,
                               timeout=30).stdout.strip() if cargo else "<absent>"
    pnpm = shutil.which("pnpm")
    pnpm_ver = (subprocess.run([pnpm, "--version"], capture_output=True, text=True,
                               timeout=30).stdout.strip() if pnpm else "<absent>")
    return {"auto_path": exe, "auto_version": ver, "auto_mtime": mtime,
            "cargo": cargo_ver, "pnpm": pnpm_ver}


def _build_number(version: str):
    m = re.search(r"-(\d+)-g[0-9a-f]+", version)
    return int(m.group(1)) if m else None


def stage_check() -> int:
    LOGS.mkdir(exist_ok=True)
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
        _log(f"BLOCKED: 工具链构建 {build} < {MIN_TOOLCHAIN_BUILD}（须含上游 PLAN-669）。"
             f"修复：auto-lang 内 cargo build --features ui-iced --bin auto 重建后重试。")
        return EXIT_BLOCKED
    if fp["cargo"].startswith("<absent>"):
        _log("WARN: cargo 缺席——a2r/release 段不可用（check 本身放行）")
    if fp["pnpm"].startswith("<absent>"):
        _log("WARN: pnpm 缺席——vue 段不可用（不影响本链）")
    _log(f"check 绿：构建 {build} ≥ {MIN_TOOLCHAIN_BUILD}")
    return EXIT_OK


def _capture(cmd, cwd, logfile, env_extra=None):
    """前台跑命令，stdout/stderr 全量落文件（防管道阻塞坑位）。"""
    env = {**os.environ, **(env_extra or {})}
    with open(logfile, "wb") as f:
        proc = subprocess.run(cmd, cwd=str(cwd), env=env, stdout=f,
                              stderr=subprocess.STDOUT, timeout=1800)
    return proc


def stage_a2r() -> int:
    LOGS.mkdir(exist_ok=True)
    exe = _auto_exe()
    log = LOGS / f"a2r-{_ts()}.log"
    _log(f"a2r 生成：auto build -r rust → {log}")
    proc = _capture([exe, "build", "-r", "rust"], PROJECT, log)
    if proc.returncode != 0:
        text = log.read_text(encoding="utf-8", errors="replace")
        if any(p in text for p in FR1_PATTERNS):
            _log("BLOCKED: a2r 生成失败且命中 F-R1 特征（api::Db/E0432/空体桩）。"
                 "供料登记见 docs/upstream/2026-09-m1-supply.md §4。")
            return EXIT_BLOCKED
        if "a2r codegen" in text or "could not compile" in text:
            first = next((ln for ln in text.splitlines()
                          if ln.startswith("error")), "<无首错行>")
            _log(f"BLOCKED: a2r 生成物编译失败——生成器缺口（上游，供料 §7）。"
                 f"首错：{first[:120]}")
            return EXIT_BLOCKED
        _log(f"FATAL: a2r 生成失败（未识别形态——输出在 {log}）")
        return EXIT_FAIL
    ws = PROJECT / "rust-workspace"
    _log(f"a2r 绿：生成物 → {ws}")
    return EXIT_OK


def _workspace_manifest() -> Path | None:
    # 落点解析序对齐 rust_ui.rs resolve_rust_workspace_dir：
    # AUTO_RUST_WORKSPACE（权威）→ <project>/rust-workspace。
    ws = Path(os.environ.get("AUTO_RUST_WORKSPACE")
              or PROJECT / "rust-workspace")
    if not ws.exists():
        return None
    root = ws / "Cargo.toml"           # 虚拟 manifest（members）优先
    if root.exists():
        return root
    cargos = sorted(ws.rglob("Cargo.toml"))
    return cargos[0] if cargos else None


def stage_release() -> int:
    manifest = _workspace_manifest()
    if manifest is None:
        _log("FATAL: rust-workspace 缺席——先跑 `perf.py a2r`")
        return EXIT_FAIL
    log = LOGS / f"release-{_ts()}.log"
    _log(f"release：cargo build --release（{manifest}）→ {log}")
    proc = _capture(["cargo", "build", "--release",
                     "--manifest-path", str(manifest)], PROJECT, log)
    if proc.returncode != 0:
        _log(f"FATAL: release 编译失败（输出在 {log}）")
        return EXIT_FAIL
    _log("release 绿")
    return EXIT_OK


def _pipe_up(wellknown: str, timeout_s: float = 15.0) -> bool:
    """探测 well-known 管道在位（连上即关——rqhost 官方吞掉探测 ping）。"""
    path = rf"\\.\pipe\{wellknown}"
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            f = open(path, "r+b", buffering=0)
            f.close()
            return True
        except PermissionError:
            return True   # 管道在位但忙（实例满）——daemon 已监听
        except OSError:
            time.sleep(0.3)
    return False


def _pid_alive(pid: int) -> bool:
    out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
                         capture_output=True, text=True).stdout
    return str(pid) in out


def _kill_pid(pid: int) -> None:
    subprocess.run(["taskkill", "/PID", str(pid), "/F", "/T"],
                   capture_output=True, text=True)


def stage_rq_up() -> int:
    LOGS.mkdir(exist_ok=True)
    if RQ_JSON.exists():
        state = json.loads(RQ_JSON.read_text(encoding="utf-8"))
        pid = state.get("rq_pid")
        if pid and _pid_alive(pid) and _pipe_up(state["wellknown"], 3.0):
            _log(f"rq-up：复用在位实例 pid={pid}")
            return EXIT_OK
        _log("rq-up：记录的实例已死（末窗退出语义），重启")
        RQ_JSON.unlink(missing_ok=True)
    exe = _auto_exe()
    log = LOGS / "rqhost.log"
    env = {**os.environ, "AUTO_RQHOST_WELLKNOWN": WELLKNOWN}
    with open(log, "ab") as f:
        proc = subprocess.Popen([exe, "rqhost"], cwd=str(PROJECT), env=env,
                                stdout=f, stderr=subprocess.STDOUT,
                                creationflags=DETACHED | NEW_GROUP)
    if not _pipe_up(WELLKNOWN, 20.0):
        _kill_pid(proc.pid)
        _log(f"FATAL: rqhost 管道 {WELLKNOWN} 20s 未就绪（日志 {log}）")
        return EXIT_FAIL
    RQ_JSON.write_text(json.dumps({"rq_pid": proc.pid, "wellknown": WELLKNOWN,
                                   "started": _ts(), "apps": []}),
                       encoding="utf-8")
    _log(f"rq-up 绿：pid={proc.pid} wellknown={WELLKNOWN}")
    return EXIT_OK


def stage_rq_down() -> int:
    if not RQ_JSON.exists():
        _log("rq-down：无在位记录（幂等绿）")
        return EXIT_OK
    state = json.loads(RQ_JSON.read_text(encoding="utf-8"))
    for pid in state.get("apps", []):
        if _pid_alive(pid):
            _kill_pid(pid)
            _log(f"rq-down：app 实例 pid={pid} 已收")
    pid = state.get("rq_pid")
    if pid and _pid_alive(pid):
        _kill_pid(pid)   # 按 PID 收——绝不 taskkill //IM auto.exe（连坐矩阵实例）
        _log(f"rq-down：rqhost pid={pid} 已收")
    else:
        _log(f"rq-down：rqhost pid={pid} 已不在（末窗退出，正常）")
    RQ_JSON.unlink(missing_ok=True)
    return EXIT_OK


def stage_run(track: str) -> int:
    if not RQ_JSON.exists():
        _log("FATAL: rqhost 未预热——先 `perf.py rq-up`")
        return EXIT_FAIL
    exe = _auto_exe()
    log = LOGS / f"app-{track}-{_ts()}.log"
    env = {**os.environ, "AUTO_RQHOST_WELLKNOWN": WELLKNOWN}
    with open(log, "ab") as f:
        proc = subprocess.Popen([exe, "run", "-r", track, "-q"], cwd=str(PROJECT),
                                env=env, stdout=f, stderr=subprocess.STDOUT,
                                creationflags=DETACHED | NEW_GROUP)
    state = json.loads(RQ_JSON.read_text(encoding="utf-8"))
    state.setdefault("apps", []).append(proc.pid)
    RQ_JSON.write_text(json.dumps(state), encoding="utf-8")
    _log(f"run({track})：pid={proc.pid} 日志 {log.name}")
    return EXIT_OK


def stage_smoke() -> int:
    rc = stage_check()
    if rc != EXIT_OK:
        return rc
    try:
        rc = stage_rq_up()
        if rc != EXIT_OK:
            return rc
        for _ in range(2):
            rc = stage_run("vm")
            if rc != EXIT_OK:
                return rc
        time.sleep(10)   # adopt + 首帧 + 稳态窗口
        state = json.loads(RQ_JSON.read_text(encoding="utf-8"))
        alive = [p for p in state.get("apps", []) if _pid_alive(p)]
        _log(f"smoke：双实例存活 {len(alive)}/2（pids={alive}）")
        if len(alive) < 2:
            logs = sorted(LOGS.glob("app-*.log"))[-2:]
            text = "".join(p.read_text(encoding="utf-8", errors="replace")
                           for p in logs)
            if any(u in text for u in UNCOVERED_PATTERNS):
                _log("BLOCKED: VM+RQ 渲染臂未覆盖（coverage::native_queue_set "
                     "缺 kind——上游缺口，供料包 docs/upstream §6）。实例死于"
                     "「拒绝渲染，禁静默错绘」语义，编排链本身（rq-up/run/"
                     "rq-down/清理）已验证在位。")
                return EXIT_BLOCKED
            _log("FATAL: VM+RQ 实例未全部存活——见 logs/app-*.log")
            return EXIT_FAIL
        _log("smoke 绿：check + rq-up + VM+RQ 双实例 + 验证")
        return EXIT_OK
    finally:
        stage_rq_down()


def main() -> int:
    ap = argparse.ArgumentParser(description="auto-edit 性能模式（L2）一键链")
    ap.add_argument("stage", choices=["check", "a2r", "release", "rq-up",
                                      "rq-down", "run", "smoke"])
    ap.add_argument("--track", default="vm", choices=["vm", "rust"],
                    help="run 阶段的渲染轨（默认 vm；rust=a2r 生成物）")
    args = ap.parse_args()
    if args.stage == "check":
        return stage_check()
    if args.stage == "a2r":
        return stage_a2r()
    if args.stage == "release":
        return stage_release()
    if args.stage == "rq-up":
        return stage_rq_up()
    if args.stage == "rq-down":
        return stage_rq_down()
    if args.stage == "run":
        return stage_run(args.track)
    return stage_smoke()


if __name__ == "__main__":
    sys.exit(main())
