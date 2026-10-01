#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_portable.py — PLAN-019 T-01：portable 单 exe 一键构建链（G-2）。

战略语义（docs/strategy/002-north-star-v2.md §2.1 installer 行）：≤15 MB
单 exe，无运行时依赖。Q3 裁定（2026-09-29 用户，PLAN-019 §4 授权记录）：
**a2r 原生化瘦身**（治本）+**纯 portable 形态**（winget/自动更新不入）。

链路（PLAN-019 §5 T-01；生成物 Cargo.toml 无 [profile] 节且 gitignored
——regen 覆盖，注入走 regen 后补丁通道=纯下游零上游依赖）：
  ensure  → rust-workspace 就位（--regen 现势直跑=PLAN-021 起主路径——
            供① 三类缺口已由上游 PLAN-710 清偿；缺 --regen 时复用现势
            生成物；regen 失败=真失败[exit 3/1]，**无快照回退**——019
            last-good 基面机制随供① 清偿退役，历史形态见 RETIRE_NOTE）
  patch   → [profile.release] 补丁注入（幂等：MARKER 注释检测跳过）
            + 依赖行 feature 面 patch（patches.json：仅 feature 子集面，
            不动版本/path——T-00③ 定形边界）
  build   → cargo build --release（生成物 manifest）
  stage   → 产物拷贝 dist/portable/auto-edit.exe + sha256
  assert  → 尺寸硬门 ≤15MB（超限 exit 1 + 差距数字）；JSONL 记录

strip 语义（T-00③ 裁定）：Windows/MSVC 产物经 [profile.release] strip=
true（Rust 1.59+ 稳态）在链接期剥离符号——外部 GNU strip 对 PE 有
校验和/签名面风险，不采用（T-01 注记）。

用法（自仓库根或任意目录；PERF_PROJECT/AUTO_BIN 与 perf.py 同语义）：
  python tools/portable/build_portable.py                 # 一键链（最终手段集）
  python tools/portable/build_portable.py --baseline      # 零手段基线（T-00 对照面）
  python tools/portable/build_portable.py --set lto=fat --set codegen-units=1 ...
  python tools/portable/build_portable.py --regen         # 现势重生成（PLAN-021 起主路径——710 解阻）
  python tools/portable/build_portable.py --check-idempotent  # patch 幂等自证

退出码：0=绿（链通+门内）；1=真失败（构建失败/超限红+差距数字）；
3=blocked-on-upstream（regen 命中上游特征——真阻塞如实报，无回退基面）。

Windows-only（产品 Win first，同 perf.py）；输出落 tools/portable/logs/
（防管道阻塞，PLAN-003 坑位）与 tools/portable/results/（入仓追踪，
bench 先例）。
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent          # tools/portable
ROOT = HERE.parents[1]                          # 仓库根
PROJECT = Path(os.environ.get("PERF_PROJECT")
               or ROOT / "specs" / "auto-edit")
LOGS = HERE / "logs"
RESULTS = HERE / "results"
PATCHES = HERE / "patches.json"
DIST = ROOT / "dist" / "portable"

BUDGET_BYTES = 15 * 1024 * 1024                 # 战略 §2.1 installer 行
EXE_NAME = "auto-edit.exe"                      # pac 包名（perf.py _release_exe 同锚）

# [profile.release] 注入 MARKER（幂等检测锚——重复注入跳过）。
PROFILE_MARKER = "# PLAN-019 portable build patch (idempotent marker)"

# 最终手段集（T-02 迭代定稿后回填；--baseline 置空——T-00 基线对照面）。
FINAL_PROFILE = {
    "lto": "fat",
    "codegen-units": "1",
    "strip": "true",
}

# regen 失败特征（018 §⑤/019 探针实录分类保留——失败归因机读面）。
# PLAN-021 退役注记（last-good 基面机制）：019 时代 regen 命中上述特征
# 时「删残件→还原快照→BLOCKED 复用现势生成物」（REGEN_BLOCKED_NOTE/
# 快照 rename 还原臂）——供① 三类缺口经上游 PLAN-710 清偿（corpus
# regen 133→0）后该绕行臂完成历史使命，随本件退役移除：regen 失败=
# 真失败如实红/_blocked（现势直跑纪律——基面复用语义仅存于缺 --regen
# 的 ensure 默认臂）。
REGEN_BLOCKED_PATTERNS = ("could not compile", "error[E", "Cargo build failed")
RETIRE_NOTE = ("PLAN-019 快照回退臂（regen 失败还原 last-good 基面复用）"
               "已随供① 清偿退役[PLAN-021 T-01]——历史机制见 019 归档件"
               "与本注记；regen 现势直跑，失败=真失败。")

# PLAN-022 T-05: ts 双形态载荷开关（716 组A highlight-treesitter feature
# 消费——ts-on=语法高亮完整形[21 语言+tail 路由；716 实测 +18.9MB]，
# ts-off=发布/installer 约束形[syntect 缩减集基线——默认形]）。
# 注入点=生成 ws 根 Cargo.toml 的 workspace auto-lang dep 行（features
# 追加面——019 patch 通道同边界：不动版本/路径/依赖增删；成员级
# features[ui/image-pipeline]与 workspace features 并集语义，双 member
# 一次性覆盖）。幂等=highlight-treesitter 在场检测。
TS_FEATURE = "highlight-treesitter"
TS_DEP_LINE_RE = re.compile(r'^(auto-lang = \{ path = "[^"]+")(\s*\})\s*$', re.M)


def stage_ts_patch(ws: Path, ts_on: bool) -> tuple[int, str]:
    manifest = ws / "Cargo.toml"
    if not ts_on:
        return EXIT_OK, "ts-off（发布约束形——零注入，syntect 缩减集基线）"
    text = manifest.read_text(encoding="utf-8")
    if TS_FEATURE not in text:
        new, n = TS_DEP_LINE_RE.subn(
            r'\1, features = ["' + TS_FEATURE + r'"]\2', text, count=1)
        if n == 0:
            return EXIT_FAIL, ("FATAL: workspace auto-lang dep 行未匹配"
                               "（生成器形变——基面演化）")
        manifest.write_text(new + ("" if new.endswith("\n") else "\n"),
                            encoding="utf-8", newline="\n")
    # PLAN-022 T-05→复工批：供⑪ 已清偿（上游 r3 T-17 零 diff——registry
    # 演进 tree-sitter-sequel 0.3.2→0.3.11〔cc ~1.0.90→~1.2.1 放宽〕，
    # 与 blake3 1.8.7〔cc ^1.1.12〕交集非空=现势 fresh 解析自然可建）。
    # 原 blake3 1.5.5 回避钉已撤（2026-10-01 撤钉回执——fresh 解析+
    # cargo check 实证在 plan 复工记录）；若未来 registry 回退再触
    # 夹缝，回避钉形见 git 史[600ba65 前的 stage_ts_patch]。

EXIT_OK, EXIT_FAIL, EXIT_BLOCKED = 0, 1, 3

# 大 crate 编译稳定性（本件执行期实录）：本机在编译高峰（auto-lang 30 万行
# 级/windows 全 Win32 面 crate）出现 rustc 0xc0000409 随机崩+提交内存耗尽
# （事件日志旁证 dwm 同窗崩溃——机器级负载不稳）。实证绿配方=sccache 旁路
# （RUSTC_WRAPPER 清空）+RUST_MIN_STACK=16MB+限并行 2+瞬态崩限次重试
# （增量编译每轮推进——崩点随机，重试有进展性依据，非盲试）。
BUILD_ENV = {"RUST_MIN_STACK": os.environ.get("RUST_MIN_STACK") or "16777216",
             "RUSTC_WRAPPER": ""}
BUILD_JOBS = os.environ.get("AUTO_PORTABLE_JOBS") or "2"
TRANSIENT_CRASH_PATTERNS = ("STATUS_STACK_BUFFER_OVERRUN",
                            "memory allocation of")
TRANSIENT_RETRIES = 3

# 依赖行 patch 缺省内容（T-02 定稿后由 patches.json 覆盖；缺省=profile+基面漂移适配）。
# 形态：[{"file": "<相对 ws 路径>", "find": "<原文片段>",
#         "replace": "<替换片段>", "why": "<一句话>"}]
#   ——deps 行仅 feature 子集面（T-00③ 边界：不动版本/路径/依赖增删）；
#   ——source 片段仅限「基面漂移适配」（reused-existing 基面晚于/早于依赖
#     钉版的字段级适配，如实注记；find 不在场=基面已演化，跳过）。
DEFAULT_PATCHES = {
    "profile": dict(FINAL_PROFILE),
    "deps": [
        {
            "file": "auto-edit/Cargo.toml",
            "find": 'ui-gpui = ["auto-lang/ui-gpui"]',
            "replace": ("# PLAN-019 补丁通道：ui-gpui 声明移除——依赖钉版"
                        " auto-lang@5bb3f53be 无此 feature（Sep22 后 feature"
                        " 重组）；默认构建路径（ui-iced）不受影响"),
            "why": "ui-gpui 声明漂移适配（feature 面边界内）",
        },
        {
            "file": "auto-edit-back/Cargo.toml",
            "find": 'tokio = { version = "1", features = ["full"] }',
            "replace": ('tokio = { version = "1", features = '
                        '["rt-multi-thread", "macros", "fs", "io-util", '
                        '"net", "time"] }'),
            "why": "tokio full→生成码实需子集（feature 面——T-02 V2b）",
        },
        {
            "file": "auto-edit/src/main.rs",
            "find": ("                frame_mode: __frame_mode,\n"
                     "                auto_downgraded: __downgraded,\n"
                     "            };"),
            "replace": ("                frame_mode: __frame_mode,\n"
                        "                auto_downgraded: __downgraded,\n"
                        "                // PLAN-019 基面漂移适配：remote 字段为基面"
                        "生成（Sep-22）之后\n                // 上游 PLAN-683 新增——"
                        "false=本地渲染（单 iced 语义不变）。\n"
                        "                remote: false,\n            };"),
            "why": "ClientOpts.remote 漂移适配（PLAN-683 后置字段；本地渲染默认）",
        },
    ],
}


def _log(msg: str) -> None:
    print(f"[portable {datetime.now():%H:%M:%S}] {msg}", flush=True)


def _ts() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def _auto_exe() -> str:
    cand = os.environ.get("AUTO_BIN") or shutil.which("auto") or shutil.which("auto.exe")
    return cand  # regen 段才必需；复用基面段允许缺席


def _fingerprint() -> dict:
    fp = {}
    exe = _auto_exe()
    if exe:
        try:
            fp["auto_version"] = subprocess.run(
                [exe, "--version"], capture_output=True, text=True,
                timeout=30).stdout.strip()
        except Exception as e:  # noqa: BLE001
            fp["auto_version"] = f"<probe failed: {e}>"
    else:
        fp["auto_version"] = "<absent（复用基面段不要求工具链）>"
    for tool in ("cargo", "rustc"):
        p = shutil.which(tool)
        fp[tool] = (subprocess.run([p, "--version"], capture_output=True,
                                   text=True, timeout=30).stdout.strip()
                    if p else "<absent>")
    return fp


def _capture(cmd, cwd, logfile, env_extra=None):
    """前台跑命令，stdout/stderr 全量落文件（防管道阻塞坑位，perf.py 同款）。"""
    env = {**os.environ, **BUILD_ENV, **(env_extra or {})}
    with open(logfile, "wb") as f:
        proc = subprocess.run(cmd, cwd=str(cwd), env=env, stdout=f,
                              stderr=subprocess.STDOUT, timeout=7200)
    return proc


# ---------------------------------------------------------------- ensure

def _ws() -> Path:
    return Path(os.environ.get("AUTO_RUST_WORKSPACE")
                or PROJECT / "rust-workspace")


def _ws_basis(ws: Path) -> str:
    """基面出处注记（复用语义的诚实记账面）。"""
    if (ws / "Cargo.toml").exists():
        return ("reused-existing（现势生成物复用——出处与年代见证据档；"
                "019 last-good 回退语义已退役[PLAN-021 T-01]）")
    return "absent"


def stage_ensure(regen: bool) -> tuple[int, dict]:
    ws = _ws()
    meta = {"ws": str(ws), "regen_requested": regen}
    if not regen and (ws / "Cargo.toml").exists():
        meta["basis"] = "reused-existing"
        meta["basis_note"] = _ws_basis(ws)
        _log(f"ensure：复用现势生成物 {ws}")
        return EXIT_OK, meta

    exe = _auto_exe()
    if not exe:
        _log("FATAL: rust-workspace 缺席且 auto 不在 PATH/未设 AUTO_BIN——"
             "无法 regen（设 AUTO_BIN 或先放置生成物）")
        return EXIT_FAIL, meta

    LOGS.mkdir(exist_ok=True)
    # 019 快照回退臂已退役（RETIRE_NOTE——供① 清偿后 regen 现势直跑）：
    # regen 前旧基面直接清除（gitignored 可再生），失败=真失败不还原。
    if (ws / "Cargo.toml").exists():
        _log(f"ensure：--regen 现势直跑——旧生成物清除（{RETIRE_NOTE[:36]}…）")
        shutil.rmtree(ws, ignore_errors=True)
    log = LOGS / f"regen-{_ts()}.log"
    _log(f"ensure：auto build -r rust → {log}")
    proc = _capture([exe, "build", "-r", "rust"], PROJECT, log)
    if proc.returncode != 0:
        text = log.read_text(encoding="utf-8", errors="replace")
        blocked = any(p in text for p in REGEN_BLOCKED_PATTERNS)
        if (ws / "Cargo.toml").exists():
            shutil.rmtree(ws, ignore_errors=True)  # 残缺生成物清除
        _log(f"{'BLOCKED' if blocked else 'FATAL'}: regen 失败——真失败如实红"
             f"（快照回退臂已退役[PLAN-021 T-01]；输出在 {log}）")
        return (EXIT_BLOCKED if blocked else EXIT_FAIL), meta
    meta["basis"] = "regen-fresh"
    _log(f"ensure：regen 绿 → {ws}")
    return EXIT_OK, meta


# ---------------------------------------------------------------- patch

def _render_profile(profile: dict) -> str:
    def _toml_val(v: str) -> str:
        if v in ("true", "false"):
            return v
        if re.fullmatch(r"-?\d+", v):
            return v
        return f'"{v}"'

    lines = ["", PROFILE_MARKER, "[profile.release]"]
    for k, v in profile.items():
        lines.append(f"{k} = {_toml_val(v)}")
    return "\n".join(lines) + "\n"


def stage_patch(profile: dict) -> tuple[int, dict]:
    """[profile.release] 块级替换注入 + deps/source 行 feature/漂移面 patch。

    幂等语义（frozen ②）：profile=MARKER 块整体替换——内容不变时字节
    等价（--check-idempotent 第二遍哈希判定）；内容变（手段迭代切换变体）
    =更新为新块。deps/source patch：replace 行已在场=已应用（跳过）；
    find 不在场且 replace 不在场=记警告跳过（基面演化自适应）。"""
    ws = _ws()
    manifest = ws / "Cargo.toml"
    if not manifest.exists():
        _log("FATAL: 生成物 Cargo.toml 缺席——ensure 段未绿")
        return EXIT_FAIL, {}
    applied, skipped = [], []
    before = manifest.read_bytes()
    if profile:
        text = before.decode("utf-8")
        if PROFILE_MARKER in text:
            start = text.index(PROFILE_MARKER)
            sec = text.index("[profile.release]", start)
            nxt = text.find("\n[", sec)   # 块尾=下一个节头（或 EOF）
            text = text[:start].rstrip() + "\n" \
                + (text[nxt + 1:] if nxt >= 0 else "")
        elif "[profile.release]" in text:
            # 无 MARKER 的既有节（孤儿/生成器未来原生节）——同样整体替换
            # （本仓生成器现势无 [profile] 节——T-00 实勘；此臂为演化自适应）。
            _log("WARN: 既有无 MARKER [profile.release] 节——整体替换")
            sec = text.index("[profile.release]")
            nxt = text.find("\n[", sec)
            text = text[:sec].rstrip() + "\n" \
                + (text[nxt + 1:] if nxt >= 0 else "")
        manifest.write_text(text.rstrip() + "\n" + _render_profile(profile),
                            encoding="utf-8", newline="\n")
        applied.append(f"profile（块替换 {profile}）")

    deps_spec = DEFAULT_PATCHES["deps"]
    if PATCHES.exists():
        try:
            spec = json.loads(PATCHES.read_text(encoding="utf-8"))
            deps_spec = spec.get("deps", deps_spec)
        except Exception as e:  # noqa: BLE001
            _log(f"WARN: patches.json 解析失败（{e}）——用内置缺省")
    for p in deps_spec:
        f = ws / p["file"]
        if not f.exists():
            skipped.append(f"{p['file']}（文件缺席）")
            continue
        t = f.read_text(encoding="utf-8")
        if p["replace"] in t:
            skipped.append(f"{p['file']}::{p.get('why', p['find'][:40])}（已应用）")
            continue
        if p["find"] not in t:
            skipped.append(f"{p['file']}::{p.get('why', p['find'][:40])}"
                           "（find 不在场——基面演化，跳过）")
            continue
        f.write_text(t.replace(p["find"], p["replace"], 1),
                     encoding="utf-8", newline="\n")
        applied.append(f"{p['file']}::{p.get('why', p['find'][:40])}")
    changed = before != manifest.read_bytes()
    _log(f"patch：applied={applied} skipped={len(skipped)} "
         f"manifest_changed={changed}")
    return EXIT_OK, {"applied": applied, "skipped": skipped,
                     "profile": profile, "manifest_changed": changed}


# ---------------------------------------------------------------- build/stage

def stage_build() -> tuple[int, dict]:
    ws = _ws()
    manifest = ws / "Cargo.toml"
    LOGS.mkdir(exist_ok=True)
    log = LOGS / f"release-{_ts()}.log"
    _log(f"build：cargo build --release -j {BUILD_JOBS}（sccache 旁路+瞬态崩"
         f"重试≤{TRANSIENT_RETRIES}）→ {log}")
    first_error = None
    for attempt in range(1 + TRANSIENT_RETRIES):
        proc = _capture(["cargo", "build", "--release", "-j", BUILD_JOBS,
                         "--manifest-path", str(manifest)], PROJECT, log)
        if proc.returncode == 0:
            break
        text = log.read_text(encoding="utf-8", errors="replace")
        if any(p in text for p in TRANSIENT_CRASH_PATTERNS) \
                and attempt < TRANSIENT_RETRIES:
            _log(f"WARN: 瞬态编译崩（attempt {attempt + 1}）——增量重试")
            time.sleep(5)
            continue
        first_error = next((ln for ln in text.splitlines()
                            if ln.startswith("error")), "<无首错行>")
        break
    if proc.returncode != 0:
        _log(f"FATAL: release 编译失败——首错 {first_error[:140]}（全量 {log}）")
        return EXIT_FAIL, {"build_log": str(log),
                           "first_error": first_error[:200]}
    exe = ws / "target" / "release" / EXE_NAME
    if not exe.exists():
        _log(f"FATAL: 构建绿但产物缺席（{exe}）")
        return EXIT_FAIL, {"build_log": str(log)}
    size = exe.stat().st_size
    _log(f"build 绿：{exe} = {size:,} B")
    return EXIT_OK, {"build_log": str(log), "size_bytes": size}


def stage_assert(ts_on: bool = False) -> tuple[int, dict]:
    ws = _ws()
    exe = ws / "target" / "release" / EXE_NAME
    size = exe.stat().st_size
    sha = hashlib.sha256(exe.read_bytes()).hexdigest()
    DIST.mkdir(parents=True, exist_ok=True)
    # PLAN-022 T-05: 产物双形态命名——ts-off=canonical auto-edit.exe
    # （installer 约束形，预算行判定域）；ts-on=auto-edit-ts-on.exe
    # （语法完整形——尺寸记录位，预算判定不适用[+18.9MB 预期形态]）。
    dest_name = "auto-edit-ts-on.exe" if ts_on else EXE_NAME
    dest = DIST / dest_name
    shutil.copy2(exe, dest)
    if ts_on:
        _log(f"assert：ts-on 形 {size:,} B（尺寸记录位——预算行不适用，"
             "installer 行判定域=ts-off 形）")
        _log(f"stage：{dest} sha256={sha[:16]}…")
        return EXIT_OK, {"size_bytes": size, "sha256": sha[:16],
                         "dest": str(dest), "verdict": "record-only(ts-on)"}
    verdict = "pass" if size <= BUDGET_BYTES else "fail"
    gap = BUDGET_BYTES - size
    _log(f"assert：{size:,} B vs ≤{BUDGET_BYTES:,} B → {verdict}"
         + (f"（余量 {gap:,} B）" if gap >= 0 else f"（超限 {-gap:,} B）"))
    _log(f"stage：{dest} sha256={sha[:16]}…")
    return (EXIT_OK if verdict == "pass" else EXIT_FAIL), {
        "size_bytes": size, "budget_bytes": BUDGET_BYTES,
        "verdict": verdict, "gap_bytes": gap,
        "sha256": sha, "dist": str(dest)}


# ---------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser(description="portable 单 exe 一键构建链（PLAN-019 T-01）")
    ap.add_argument("--regen", action="store_true",
                    help="先 auto build -r rust 重生成（上游阻塞时快照回退复用）")
    ap.add_argument("--baseline", action="store_true",
                    help="零手段基线（T-00 对照面——不注入 profile/deps patch）")
    ap.add_argument("--set", dest="overrides", action="append", default=[],
                    metavar="KEY=VALUE", help="profile 键覆盖（可多次）")
    ap.add_argument("--no-deps-patch", action="store_true",
                    help="跳过依赖行 patch（仅 profile 面）")
    ap.add_argument("--ts", choices=["on", "off"], default="off",
                    help="PLAN-022 T-05 载荷开关：ts-on=highlight-"
                         "treesitter 语法完整形（+18.9MB 预期——尺寸记录"
                         "位）；ts-off=发布/installer 约束形（默认，预算"
                         "判定域）")
    ap.add_argument("--skip-build", action="store_true",
                    help="跳过构建（patch/幂等自证用）")
    ap.add_argument("--check-idempotent", action="store_true",
                    help="patch 幂等自证：连续两次 patch，第二次必须全 skip")
    args = ap.parse_args()

    fp = _fingerprint()
    _log(f"环境：auto={fp.get('auto_version')} | {fp.get('cargo')}")
    m = re.search(r"-(\d+)-g[0-9a-f]+", fp.get("auto_version") or "")
    if m and int(m.group(1)) < 1588:
        _log(f"WARN: 工具链构建 {m.group(1)} < 1588（perf/bench 同门下限）——"
             "regen 段不可信；复用基面段不受扰（AUTO_BIN 指向 release 构建）")

    profile = {} if args.baseline else dict(FINAL_PROFILE)
    for ov in args.overrides:
        k, _, v = ov.partition("=")
        profile[k.strip()] = v.strip()

    rc, meta = stage_ensure(args.regen)
    rec = {"type": "portable_build", "ts": _ts(), "ensure": meta,
           "toolchain": fp, "baseline": args.baseline}
    if rc != EXIT_OK:
        _dump(rec, rc)
        return rc
    # regen 现势直跑纪律（PLAN-021）：BLOCKED/FAIL 无基面可复用——止步；
    # 绿后基面缺席（生成器行为漂移）同止步。
    if not (_ws() / "Cargo.toml").exists():
        rec["ensure"]["basis"] = "absent-after-ok"
        _dump(rec, EXIT_FAIL)
        return EXIT_FAIL

    rc_p, meta_p = stage_patch(profile)
    rec["patch"] = meta_p
    if rc_p != EXIT_OK:
        _dump(rec, rc_p)
        return rc_p
    ts_on = args.ts == "on"
    rec["ts_form"] = args.ts
    rc_t, meta_t = stage_ts_patch(_ws(), ts_on)
    rec["ts_patch"] = meta_t
    _log(f"ts patch：{meta_t}")
    if rc_t != EXIT_OK:
        _dump(rec, rc_t)
        return rc_t
    if args.check_idempotent:
        import hashlib as _h
        ws = _ws()
        h1 = _h.sha256((ws / "Cargo.toml").read_bytes()).hexdigest()
        stage_patch(profile)
        h2 = _h.sha256((ws / "Cargo.toml").read_bytes()).hexdigest()
        second_same = h1 == h2
        rec["idempotency"] = {"first_sha": h1[:16], "second_sha": h2[:16],
                              "verdict": "pass" if second_same else "fail"}
        _log(f"幂等自证：{'pass（第二遍字节等价）' if second_same else 'FAIL（第二遍仍写入）'}")
        if not second_same:
            _dump(rec, EXIT_FAIL)
            return EXIT_FAIL

    if args.skip_build:
        _dump(rec, EXIT_OK)
        return EXIT_OK
    rc_b, meta_b = stage_build()
    rec["build"] = meta_b
    if rc_b != EXIT_OK:
        _dump(rec, rc_b)
        return rc_b
    rc_a, meta_a = stage_assert(ts_on)
    rec["assert"] = meta_a
    _dump(rec, rc_a)
    if rc_a != EXIT_OK and not ts_on:
        _log(f"RED: 尺寸门超限——差距 {-meta_a['gap_bytes']:,} B"
             "（分阶段语义：差距数字入报告，手段迭代继续——非链失败）")
    return rc_a


def _dump(rec: dict, rc: int) -> None:
    RESULTS.mkdir(exist_ok=True)
    out = RESULTS / f"portable-{_ts()}.jsonl"
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    _log(f"记录 → {out}（exit={rc}）")


if __name__ == "__main__":
    sys.exit(main())
