#!/usr/bin/env python3
r"""PLAN-014 T-01 任务栏跳转列表勘定探针（决策件）——壳自动 Recent 已备度五面.

五项（计划 §5 T-01；决策记录落计划 §10 Q-1）：
  ① 源面：两仓代码树 grep（SHAddToRecentDocs/ICustomDestinationList/
     RecentDocs/AppUserModelID/Software\Classes）——auto-edit .at 全树 +
     auto-lang crates .rs 全树（就地 re-grep，不信任计划期数）。
  ② 二进制面：auto-edit.exe（释放产物）+ auto.exe（工具链宿主，vm 模式窗
     主进程）字节扫描记账 API 名（SHAddToRecentDocs 为 shell32 直接导入
     可见；COM ICustomDestinationList 走 vtable 无导入名——由①③④合围）。
  ③ 关联注册面：本机注册表实况（HKCR\.txt 缺省值 / FileExts UserChoice
     ProgId / Classes 树 auto-edit 键检索）——产品零注册预期；pac `opens`
     是 auto 桌面壳内部注册（session.rs OpenWith 动词），不触 Windows 注册表。
  ④ 动态面：释放 exe + AUTO_OPEN_PATH fixture（隔离 APPDATA，AUTO_BENCH=1
     标记门）装载确认（BENCH bench_open_done）→ 前后 diff 真/隔离两处
     Recent 树（*.lnk/AutomaticDestinations/CustomDestinations 增量+全
     .automaticDestinations-ms UTF-16LE fixture 名扫描）——壳自动记账预期零。
  ⑤ 裁定：(a) 已备（③ 关联命中 auto-edit 或 ④ 记账增量）/(b) shim（全零
     ——供料段内核 native：SHAddToRecentDocs(SHARD_PATHW) 一调用形，recents
     落盘挂点直调；ICustomDestinationList 自定义任务类=非目标）。

用法：cd specs/auto-edit/tests && python probe_jumplist.py [--exe <path>]
     [--auto-exe <path>] [--keep]
报告：probe_jumplist_report.{json,txt}（probe_bigfile 同款惯例）。
退出码：0=勘定有效（裁定已形成，(a)/(b) 均为有效产出）；1=环境失效
     （exe 缺席/装载超时——裁定不可信）。
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

TESTS = Path(__file__).resolve().parent
PROJECT = TESTS.parent                      # specs/auto-edit
REPO = PROJECT.parent.parent                # auto-edit checkout root
AUTO_LANG = Path(os.environ.get("AUTO_LANG_ROOT")
                 or REPO.parent / "auto-lang")
MB = 1024 * 1024

PATTERNS = ["SHAddToRecentDocs", "ICustomDestinationList", "RecentDocs",
            "AppUserModelID", "Software\\Classes"]
BINARY_NAMES = [b"SHAddToRecentDocs", b"SetCurrentProcessExplicitAppUserModelID",
                b"ICustomDestinationList"]


def scan_source(root: Path, suffix: str, skip_parts: set[str]) -> list[str]:
    hits = []
    if not root.is_dir():
        return hits
    for p in root.rglob(f"*{suffix}"):
        if any(part in skip_parts for part in p.parts):
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for i, ln in enumerate(text.splitlines(), 1):
            for pat in PATTERNS:
                if pat.lower() in ln.lower():
                    hits.append(f"{p.relative_to(root)}:{i}: {pat}")
    return hits


def scan_binary(exe: Path) -> dict:
    out = {"path": str(exe), "exists": exe.exists(),
           "size": None, "mtime": None, "hits": []}
    if not exe.exists():
        return out
    st = exe.stat()
    out["size"], out["mtime"] = st.st_size, time.strftime(
        "%Y-%m-%d %H:%M", time.localtime(st.st_mtime))
    blob = exe.read_bytes()
    for name in BINARY_NAMES:
        if name in blob:
            out["hits"].append(name.decode())
    return out


def reg_query(args: list[str]) -> str:
    try:
        r = subprocess.run(["reg", *args], capture_output=True, text=True,
                           timeout=60, encoding="utf-8", errors="replace")
        return (r.stdout or "") + (r.stderr or "")
    except (OSError, subprocess.TimeoutExpired) as e:
        return f"<reg-error {e}>"


def phase3_registry() -> dict:
    out = {"queries": {}, "auto_edit_assoc": False}
    qs = {
        "hkcr_txt_default": ["query", r"HKCR\.txt", "/ve"],
        "txt_user_choice": ["query",
                            r"HKCU\Software\Microsoft\Windows\CurrentVersion"
                            r"\Explorer\FileExts\.txt\UserChoice", "/v", "ProgId"],
        "hkcu_classes_search": ["query", r"HKCU\Software\Classes",
                                "/f", "auto-edit", "/k"],
        "hkcu_app_key": ["query", r"HKCU\Software\Classes\auto-edit"],
        "hkcu_applications_exe": ["query",
                                  r"HKCU\Software\Classes\Applications\auto-edit.exe"],
    }
    for label, args in qs.items():
        body = reg_query(args)
        out["queries"][label] = body.strip()
        low = body.lower()
        if "auto-edit" in low and "unable to find" not in low and "検索" not in low:
            if label in ("hkcu_classes_search", "hkcu_app_key",
                         "hkcu_applications_exe"):
                out["auto_edit_assoc"] = True
    return out


def snapshot_recent(recent_dir: Path) -> dict:
    snap = {}
    if not recent_dir.is_dir():
        return snap
    for p in recent_dir.rglob("*"):
        if p.is_file():
            st = p.stat()
            snap[str(p.relative_to(recent_dir)).lower()] = [st.st_size, st.st_mtime_ns]
    return snap


def scan_dest_for(fixture_base: str, recent_dir: Path) -> list[str]:
    """全 .automaticDestinations-ms / CustomDestinations UTF-16LE+ANSI 扫描。"""
    hits = []
    if not recent_dir.is_dir():
        return hits
    needles = [fixture_base.encode("utf-16-le"), fixture_base.encode("utf-8")]
    for p in recent_dir.rglob("*.ms"):
        try:
            blob = p.read_bytes()
        except OSError:
            continue
        if any(n in blob for n in needles):
            hits.append(p.name)
    for p in recent_dir.rglob("*.lnk"):
        try:
            blob = p.read_bytes()
        except OSError:
            continue
        if any(n in blob for n in needles):
            hits.append(p.name)
    return hits


def diff_recent(before: dict, after: dict) -> list[str]:
    changed = [k for k in after
               if k not in before or before[k] != after[k]]
    return sorted(changed)


def default_exe() -> str:
    """释放 exe 解析序：本检出 rust-workspace → 主检出构建产物（worktree
    不带构建物；exe=构建产物非源，回落合法——bench _release_exe 同形）。"""
    local = PROJECT / "rust-workspace" / "target" / "release" / "auto-edit.exe"
    if local.exists():
        return str(local)
    try:
        common = subprocess.run(
            ["git", "rev-parse", "--path-format=absolute",
             "--git-common-dir"], cwd=PROJECT, capture_output=True, text=True,
            timeout=10).stdout.strip()
        main_repo = Path(common).parent if common else None
        if main_repo:
            cand = main_repo / "specs" / "auto-edit" / "rust-workspace" / \
                "target" / "release" / "auto-edit.exe"
            if cand.exists():
                return str(cand)
    except (OSError, subprocess.TimeoutExpired):
        pass
    return str(local)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", default=default_exe())
    ap.add_argument("--auto-exe", default=os.environ.get("AUTO_BIN")
                    or shutil.which("auto") or "")
    ap.add_argument("--keep", action="store_true")
    args = ap.parse_args()

    report = {"plan": "PLAN-014 T-01", "toolchain_auto": "", "phases": {}}
    exe, auto_exe = Path(args.exe), Path(args.auto_exe)
    if not exe.exists():
        print(f"FATAL: release exe 缺席：{exe}（--exe 或先 cargo build）")
        return 1

    # ① 源面
    skip = {"target", "node_modules", "dist", "gen", ".git", "results",
            "fixtures", "probe_jumplist_app"}
    src_hits = (scan_source(PROJECT, ".at", skip)
                + scan_source(AUTO_LANG / "crates", ".rs", skip))
    report["phases"]["1_source"] = {"patterns": PATTERNS, "hits": src_hits,
                                    "auto_lang_root": str(AUTO_LANG)}
    print(f"① 源面：{len(src_hits)} 命中{'' if not src_hits else ' ← 详报'}")

    # ② 二进制面
    b_exe, b_auto = scan_binary(exe), scan_binary(auto_exe)
    report["phases"]["2_binary"] = {"auto_edit_exe": b_exe, "auto_exe": b_auto}
    report["toolchain_auto"] = f"{auto_exe} exists={auto_exe.exists()}"
    print(f"② 二进制面：auto-edit.exe hits={b_exe['hits']}；"
          f"auto.exe({auto_exe}) hits={b_auto['hits']}")

    # ③ 关联注册面
    reg = phase3_registry()
    report["phases"]["3_registry"] = reg
    print(f"③ 关联注册面：auto-edit 注册命中={reg['auto_edit_assoc']}")

    # ④ 动态面
    dyn = {"launched": False, "loaded": False, "deltas": {}, "fixture_hits": []}
    tmp = Path(tempfile.mkdtemp(prefix="p014_jumplist_"))
    iso_recent = tmp / "Microsoft" / "Windows" / "Recent"
    real_appdata = Path(os.environ.get("USERPROFILE", "")) / "AppData" / "Roaming"
    real_recent = real_appdata / "Microsoft" / "Windows" / "Recent"
    fixdir = tmp / "fix"
    fixdir.mkdir(parents=True, exist_ok=True)
    fixture = fixdir / f"probe_jumplist_{int(time.time())}.txt"
    fixture.write_text("// PLAN-014 T-01 jumplist probe fixture\n", encoding="utf-8")
    try:
        pre = {str(real_recent): snapshot_recent(real_recent),
               str(iso_recent): snapshot_recent(iso_recent)}
        pre_scan = scan_dest_for(fixture.name, real_recent) + \
            scan_dest_for(fixture.name, iso_recent)
        log_path = tmp / "app.log"
        env = {**os.environ, "APPDATA": str(tmp), "AUTO_BENCH": "1",
               "AUTO_OPEN_PATH": str(fixture)}
        with open(log_path, "w", encoding="utf-8", errors="replace") as log:
            proc = subprocess.Popen([str(exe)], cwd=str(PROJECT), env=env,
                                    stdout=log, stderr=subprocess.STDOUT)
            t0 = time.time()
            loaded = False
            while time.time() - t0 < 30 and not loaded:
                try:
                    loaded = "BENCH bench_open_done" in log_path.read_text(
                        encoding="utf-8", errors="replace")
                except OSError:
                    pass
                time.sleep(0.2)
            time.sleep(2.0)  # 壳侧落账宽限
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)],
                           capture_output=True)
            proc.wait(timeout=15)
        dyn["launched"] = True
        dyn["loaded"] = loaded
        time.sleep(1.5)
        post = {str(real_recent): snapshot_recent(real_recent),
                str(iso_recent): snapshot_recent(iso_recent)}
        for root_s in pre:
            d = diff_recent(pre[root_s], post[root_s])
            if d:
                dyn["deltas"][root_s] = d
        post_scan = scan_dest_for(fixture.name, real_recent) + \
            scan_dest_for(fixture.name, iso_recent)
        dyn["fixture_hits"] = sorted(set(post_scan) - set(pre_scan))
        dyn["log_tail"] = log_path.read_text(encoding="utf-8",
                                             errors="replace")[-400:]
    finally:
        if args.keep:
            print(f"  keep: {tmp}")
        else:
            shutil.rmtree(tmp, ignore_errors=True)
    report["phases"]["4_dynamic"] = dyn
    print(f"④ 动态面：launched={dyn['launched']} loaded={dyn['loaded']} "
          f"记账增量={dyn['deltas'] or '无'} fixture 记账命中={dyn['fixture_hits'] or '无'}")

    # ⑤ 裁定
    accountinged = bool(dyn["deltas"]) or bool(dyn["fixture_hits"])
    ruling = ("a" if (reg["auto_edit_assoc"] or accountinged) else "b")
    report["ruling"] = ruling
    report["ruling_note"] = {
        "a": "壳自动 Recent 已备（零改动+SD-03 注记即毕）",
        "b": "内核零 shell 面（源/二进制/注册/动态四层全零）——SHAddToRecentDocs "
             "shim=供料段扩件（auto-lang native 一调用形），消费位=recents 落盘挂点"
             "直调；G-1 部分改道供料段须用户确认（Q-1）；ICustomDestinationList "
             "自定义任务类=非目标",
    }[ruling]
    print(f"⑤ 裁定：({ruling}) —— {report['ruling_note']}")

    ok = dyn["launched"] and dyn["loaded"]
    rep_json = TESTS / "probe_jumplist_report.json"
    rep_txt = TESTS / "probe_jumplist_report.txt"
    rep_json.write_text(json.dumps(report, ensure_ascii=False, indent=2),
                        encoding="utf-8")
    lines = [f"PLAN-014 T-01 jumplist 勘定 — ruling=({ruling})", ""]
    for k, v in report["phases"].items():
        lines.append(f"[{k}] {json.dumps(v, ensure_ascii=False)[:600]}")
    lines.append("")
    lines.append(f"ruling_note: {report['ruling_note']}")
    rep_txt.write_text("\n".join(lines), encoding="utf-8")
    print(f"报告 → {rep_json.name} / {rep_txt.name}")
    if not ok:
        print("FATAL: 动态面未达装载确认（裁定不可信）")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
