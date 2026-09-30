#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""smoke_gen.py — PLAN-021 T-04：a2r 生成码三域冒烟族（G-4/AC-04）。

生成码（a2r release exe）首次跑真实 app 的最小断言面——019 probe_surface
形态扩展。观测通道勘定（T-00⑤）：release exe 无 MCP 自动化面
（run_app_devtools=F12 调试面板，AUTOUI_MCP_PORT 属 VM 宿主）；
console_log→ui_console_push（不落 stdout）——断言面=**BENCH 标记序列
（AUTO_BENCH=1 门控 stdout）+ 进程存活 + 单 iced 拓扑门 + back 包络
数据面（/api/diff_files JSON 字段/计数）**。三域：

  G-B 装载链域（try 块 trans 臂）——
    ① 会话恢复 try 成功臂：隔离 APPDATA 注入合法会话（ws_dir 匹配）
       → bench_session_restored 标记达+存活。
    ② 会话恢复 try catch 臂：坏 JSON 会话 → 无 restored 标记+存活+
       后续 AUTO_OPEN_PATH 打开 E2E 绿（catch 后正常运作）。
    ③ file_size 探测/装载错误形：缺文件 AUTO_OPEN_PATH → open_start
       达/open_done 缺（load_file 错误形承接）+存活。
    （513MB 拒绝形归 bench open --l2 档探针——同 exe 同门，不重复。）
  G-A diff 视图域（envelope 投影 `??` 族）——
    ④ front bypass：AUTO_DIFF_A/B golden 对（3 变更行）→ Tick 自开
       diff 视图 → bypass 窗后存活（投影链 panic=进程死——可观测）+
       后端就绪行。
    ⑤ back 包络数据面：release auto-edit-back /api/diff_files 同对
       → envelope JSON {adds,dels,err} 字段齐+计数==golden 真值
       （front 投影消费的同一包络形状）。
  G-C 编辑回路域（delta 臂）——
    ⑥ 装载 E2E：AUTO_OPEN_PATH 小 fixture → vm_init→ws_loaded→
       open_start→open_done 标记序（SrcChanged→code_editor_delta
       消费随装载链 on_change 执行——delta 臂断链=生成不编译[cargo
       check 已证]/运行 panic=进程死+done 缺——均可观测）。
    ⑦ badge 门探测 try①（:1637 file_size try）随④ diff bypass 执行
       （存活即证）；try②（dirty 预览 set_text try）env 不可驱——
       同内建形态由⑥装载链覆盖，如实注记。

用法：
  python tools/portable/smoke_gen.py                # 全域（①-⑥）
  python tools/portable/smoke_gen.py --list         # 汇总已有谱

退出码：0=全检查绿；1=任一红。JSONL 落 tools/portable/results/。
每轮按 PID 收（绝不 taskkill //IM——bench.py 纪律）。
"""
import argparse
import json
import os
import socket
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
PROJECT = Path(os.environ.get("PERF_PROJECT") or ROOT / "specs" / "auto-edit")
WS = Path(os.environ.get("AUTO_RUST_WORKSPACE") or PROJECT / "rust-workspace")
EXE = WS / "target" / "release" / "auto-edit.exe"
BACK = WS / "target" / "release" / "auto-edit-back.exe"
RESULTS = HERE / "results"
LOGS = HERE / "logs"
BACKEND_READY_LINE = "Running with Iced backend"

EXIT_OK, EXIT_FAIL = 0, 1

# golden 对（G-A）：A=10 行，B=同 10 行改 3 行 → hunks=3，adds=3，dels=3。
GOLDEN_LINES = [f"line {i:03d} of p021 smoke golden payload" for i in range(10)]
GOLDEN_CHANGED = {2, 5, 8}


def _log(msg: str) -> None:
    print(f"[smoke-gen {datetime.now():%H:%M:%S}] {msg}", flush=True)


def _ts() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def _kill_pid(pid: int) -> None:
    subprocess.run(["taskkill", "/PID", str(pid), "/F", "/T"],
                   capture_output=True, text=True)


def _free_port(start: int) -> int:
    for cand in range(start, start + 100):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", cand)) != 0:
                return cand
    raise RuntimeError("no free port")


def _golden_pair(d: Path) -> tuple[Path, Path]:
    d.mkdir(parents=True, exist_ok=True)
    pa, pb = d / "golden.a.txt", d / "golden.b.txt"
    pa.write_text("\n".join(GOLDEN_LINES) + "\n", encoding="utf-8")
    pb.write_text("\n".join(
        ln + " CHANGED" if i in GOLDEN_CHANGED else ln
        for i, ln in enumerate(GOLDEN_LINES)) + "\n", encoding="utf-8")
    return pa, pb


def _small_fixture(d: Path) -> Path:
    d.mkdir(parents=True, exist_ok=True)
    p = d / "smoke-small.txt"
    p.write_text("// p021 smoke small fixture\nfn probe() int { return 42 }\n"
                 * 8, encoding="utf-8")
    return p


def _run_exe(tag: str, env_extra: dict, want: list[str], timeout_s: float,
             appdata: Path | None, settle_after_markers: float = 0.0
             ) -> tuple[dict, subprocess.Popen, Path]:
    """spawn release exe（零旗标直拉），stdout 落文件轮询标记。
    返回 (观测, proc, log)。观测={markers, backend_ready, alive_at_end}。"""
    LOGS.mkdir(exist_ok=True)
    log = LOGS / f"gen-{tag}-{_ts()}.log"
    env = {**os.environ, "AUTO_BENCH": "1", "AUTO_PROJECT_DIR": str(PROJECT),
           **env_extra}
    if appdata is not None:
        env["APPDATA"] = str(appdata)
    t0 = time.perf_counter()
    with open(log, "wb") as f:
        proc = subprocess.Popen([str(EXE)], cwd=str(PROJECT), env=env,
                                stdout=f, stderr=subprocess.STDOUT)
    obs: dict = {"markers": {}, "backend_ready": False}
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        time.sleep(0.002)
        if proc.poll() is not None:
            break
        try:
            text = log.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if not obs["backend_ready"] and BACKEND_READY_LINE in text:
            obs["backend_ready"] = True
        for m in want:
            if m not in obs["markers"] and f"BENCH {m}" in text:
                obs["markers"][m] = round((time.perf_counter() - t0) * 1000.0, 1)
        if len(obs["markers"]) == len(want) and obs["backend_ready"]:
            if settle_after_markers > 0:
                time.sleep(settle_after_markers)
            break
    obs["alive_at_end"] = proc.poll() is None
    obs["log"] = str(log)
    obs["pid"] = proc.pid
    return obs, proc, log


def _check(recs: list[dict], cid: str, ok: bool, evidence: str) -> None:
    recs.append({"id": cid, "ok": bool(ok), "evidence": evidence})
    _log(f"  [{'PASS' if ok else 'FAIL'}] {cid}: {evidence}")


# ---------------------------------------------------------------- G-B

def domain_gb(recs: list[dict], tmp: Path) -> None:
    _log("G-B 装载链域（try 块 trans 臂）")
    small = _small_fixture(tmp)

    # ① 会话恢复成功臂
    with tempfile.TemporaryDirectory(prefix="p021-gen-gb1-") as ad:
        session = {"ws_dir": str(PROJECT), "active": 0,
                   "tabs": [{"path": str(small), "title": small.name,
                             "cline": 1, "ccol": 1}], "recents": []}
        (Path(ad) / "auto-edit-session.json").write_text(
            json.dumps(session), encoding="utf-8")
        obs, proc, _ = _run_exe("gb1-restore", {}, ["bench_vm_init",
                                "bench_ws_loaded", "bench_session_restored"],
                                30.0, Path(ad))
        ok = ("bench_session_restored" in obs["markers"]
              and obs["backend_ready"] and obs["alive_at_end"])
        _check(recs, "G-B1 会话恢复 try 成功臂", ok,
               f"restored@{obs['markers'].get('bench_session_restored')}ms "
               f"backend={obs['backend_ready']} alive={obs['alive_at_end']}")
        _kill_pid(proc.pid)

    # ② 会话恢复 catch 臂（坏 JSON）+ catch 后正常打开 E2E
    with tempfile.TemporaryDirectory(prefix="p021-gen-gb2-") as ad:
        (Path(ad) / "auto-edit-session.json").write_text(
            "{invalid json!! p021 catch-arm probe", encoding="utf-8")
        obs, proc, _ = _run_exe("gb2-catch", {"AUTO_OPEN_PATH": str(small)},
                                ["bench_ws_loaded", "bench_open_start",
                                 "bench_open_done"], 30.0, Path(ad))
        ok = ("bench_session_restored" not in obs["markers"]
              and "bench_open_done" in obs["markers"]
              and obs["alive_at_end"] and obs["backend_ready"])
        _check(recs, "G-B2 会话恢复 try catch 臂（坏 JSON→fresh start+后续打开绿）",
               ok, f"restored_absent={'bench_session_restored' not in obs['markers']} "
                   f"open_done@{obs['markers'].get('bench_open_done')}ms "
                   f"alive={obs['alive_at_end']}")
        _kill_pid(proc.pid)

    # ③ file_size 探测/装载错误形（缺文件）
    with tempfile.TemporaryDirectory(prefix="p021-gen-gb3-") as ad:
        missing = str(Path(ad) / "no-such-file.txt")
        obs, proc, _ = _run_exe("gb3-missing", {"AUTO_OPEN_PATH": missing},
                                ["bench_open_start"], 30.0, Path(ad))
        try:
            text = Path(obs["log"]).read_text(encoding="utf-8", errors="replace")
        except OSError:
            text = ""
        ok = ("bench_open_start" in obs["markers"]
              and "bench_open_done" not in obs["markers"]
              and obs["alive_at_end"])
        _check(recs, "G-B3 装载探测缺文件错误形（open_start 达/done 缺/存活）",
               ok, f"start@{obs['markers'].get('bench_open_start')}ms "
                   f"done_absent={'bench_open_done' not in obs['markers']} "
                   f"alive={obs['alive_at_end']} backend={obs['backend_ready']}")
        _kill_pid(proc.pid)


# ---------------------------------------------------------------- G-A

def domain_ga(recs: list[dict], tmp: Path) -> None:
    _log("G-A diff 视图域（envelope 投影族）")
    pa, pb = _golden_pair(tmp)

    # ④ front bypass 自开 diff 视图（投影链 panic=进程死——可观测）
    obs, proc, _ = _run_exe("ga1-bypass", {"AUTO_DIFF_A": str(pa),
                                            "AUTO_DIFF_B": str(pb)},
                            ["bench_ws_loaded"], 30.0, None,
                            settle_after_markers=8.0)
    ok = obs["backend_ready"] and obs["alive_at_end"]
    _check(recs, "G-A4 front diff bypass 自开（投影链执行 8s 存活窗）", ok,
           f"backend={obs['backend_ready']} alive={obs['alive_at_end']} "
           f"（envelope ?? 投影 panic 面=进程存活反证）")
    _kill_pid(proc.pid)

    # ⑤ back 包络数据面（front 投影消费的同一包络形状）
    port = _free_port(9660)
    env = {**os.environ, "AUTO_HTTP_PORT": str(port),
           "AUTO_PROJECT_DIR": str(PROJECT)}
    with open(LOGS / f"gen-ga2-back-{_ts()}.log", "wb") as f:
        srv = subprocess.Popen([str(BACK)], cwd=str(PROJECT), env=env,
                               stdout=f, stderr=subprocess.STDOUT)
    try:
        up = False
        base = f"http://127.0.0.1:{port}"
        for _ in range(20):
            try:
                urllib.request.urlopen(base + "/api/ws_root", timeout=2)
                up = True
                break
            except Exception:  # noqa: BLE001
                time.sleep(0.5)
        env_obj = None
        if up:
            q = urllib.parse.urlencode({"path_a": str(pa), "path_b": str(pb),
                                        "ctx": 3})
            with urllib.request.urlopen(f"{base}/api/diff_files?{q}",
                                        timeout=30) as resp:
                env_obj = json.loads(resp.read().decode("utf-8"))
                if isinstance(env_obj, str):
                    env_obj = json.loads(env_obj)
        ok = (up and isinstance(env_obj, dict)
              and env_obj.get("err", "?") == ""
              and env_obj.get("adds") == len(GOLDEN_CHANGED)
              and env_obj.get("dels") == len(GOLDEN_CHANGED))
        _check(recs, "G-A5 back diff_files 包络数据面（字段齐+计数==golden 3/3）",
               ok, f"up={up} env={ {k: env_obj.get(k) for k in ('err', 'adds', 'dels')} if env_obj else None }"
                   f" expect adds=dels={len(GOLDEN_CHANGED)}")
    finally:
        _kill_pid(srv.pid)


# ---------------------------------------------------------------- G-C

def domain_gc(recs: list[dict], tmp: Path) -> None:
    _log("G-C 编辑回路域（delta 臂——装载链 on_change 消费）")
    small = _small_fixture(tmp)
    obs, proc, _ = _run_exe("gc1-load", {"AUTO_OPEN_PATH": str(small)},
                            ["bench_vm_init", "bench_ws_loaded",
                             "bench_open_start", "bench_open_done"],
                            30.0, None)
    seq = ["bench_vm_init", "bench_ws_loaded", "bench_open_start",
           "bench_open_done"]
    marks = obs["markers"]
    in_order = all(k in marks for k in seq) and \
        all(marks[a] <= marks[b] for a, b in zip(seq, seq[1:]))
    ok = in_order and obs["alive_at_end"] and obs["backend_ready"]
    _check(recs, "G-C6 装载 E2E 标记序（SrcChanged→delta 消费在链）", ok,
           f"seq={'→'.join(f'{k.split(chr(95))[-1]}@{marks.get(k)}' for k in seq)}"
           f" alive={obs['alive_at_end']}")
    _check(recs, "G-C7 badge 门探测 try① 随 diff bypass（④ 存活即证；"
                 "try② dirty 预览 env 不可驱——同内建形态⑥覆盖）",
           ok, "gate-probe file_size try 在 DiffCompute 链（G-A4 同跑）；"
               "dirty-preview set_text try 注记如实")
    _kill_pid(proc.pid)


# ---------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser(description="a2r 生成码三域冒烟（PLAN-021 T-04）")
    ap.add_argument("--list", action="store_true", help="汇总已有谱后退出")
    args = ap.parse_args()
    if args.list:
        for p in sorted(RESULTS.glob("gen-smoke-*.jsonl")):
            for ln in p.read_text(encoding="utf-8").splitlines():
                d = json.loads(ln)
                if d.get("type") == "gen_smoke_summary":
                    print(f"{d['ts']} verdict={d['verdict']} "
                          f"checks={sum(1 for c in d['checks'] if c['ok'])}"
                          f"/{len(d['checks'])}")
        return 0
    if not EXE.exists():
        _log(f"FATAL: release exe 缺席（{EXE}）——先 perf.py release")
        return EXIT_FAIL
    recs: list[dict] = []
    with tempfile.TemporaryDirectory(prefix="p021-gen-smoke-") as tmp:
        t = Path(tmp)
        domain_gb(recs, t)
        domain_ga(recs, t)
        domain_gc(recs, t)
    ok = all(c["ok"] for c in recs)
    summary = {"type": "gen_smoke_summary", "ts": _ts(),
               "exe": str(EXE), "exe_size_bytes": EXE.stat().st_size,
               "checks": recs, "verdict": "pass" if ok else "fail"}
    RESULTS.mkdir(exist_ok=True)
    out = RESULTS / f"gen-smoke-{summary['ts']}.jsonl"
    out.write_text(json.dumps(summary, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    _log(f"{'绿' if ok else '红'}：{sum(1 for c in recs if c['ok'])}/"
         f"{len(recs)} 检查 → {out.name}")
    return EXIT_OK if ok else EXIT_FAIL


if __name__ == "__main__":
    sys.exit(main())
