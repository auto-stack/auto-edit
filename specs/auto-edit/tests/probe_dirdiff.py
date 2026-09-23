#!/usr/bin/env python3
"""PLAN-012 T-00 探针勘定（决策件）—— M3-02 目录 diff v1 四项勘定 + Phase A
端点验证节（T-01/T-02 落地后重跑全绿）.

载具 = tests/probe_dirdiff_app/（vm merged 最小 app：back/papi.at 直呼
fs 同步五内建 + 二进制启发式 + 2MB 内容比对——front 零 fs/Env 铁律不破）
+ 真实 auto-edit 实例（Phase A split back HTTP）。

四项（决策记录落 PLAN-012 §10）：
  ① fs 同步五内建映射可用性（Q-1）：fs.copy/fs.delete/fs.remove_dir/
     fs.copy_recursive/fs.remove_dir_all 逐个独立 fn 实测（009 三案教训：
     catalog 在册≠codegen 映射正确）——verdict 串+磁盘 E2E 双证；覆盖
     语义（Q-2：文件/目录 copy 对已存在目标）同勘；remove_dir 非空护栏
     勘定（sync_delete 目录分支的安全前提）。
  ② 二进制启发式：invalid UTF-8（008 fixtures 同源形态）→ size>0 且
     read_text=="" → binary；空文件（0B）不误判（size 门）；valid 文本
     读出非空；read_text_range 前缀窗（8KB）total 字段形态同勘（>2MB
     大文件启发式的预算域备选面）。
  ③ 内容比对上限：2MB 同尺寸对 Str == 全等比对（同内容=eq/异内容=
     uneq 双形态）——墙钟 python 侧采样；进程 RSS 前后采样（观察注记，
     PLAN-007 观察 B 口径——非门）。
  ④ dialog_open 目录能力：rfd 阻塞式矩阵不可驱动——静态勘定（源码
     语义+人工步骤注记），定案 v1 路径输入框+env 旁路方案。

Phase A（端点存在时激活，否则 SKIP 注记——T-01/T-02 落地后重跑）：
  ⑤′ diff_dirs × dirdiff golden 逐字段对照（五形态：同/改/增/删/二进制
     +嵌套+空文件+dir 条目；entries 集合级+counts 精确+truncated）。
  ⑥′ sync_copy/sync_delete tmp E2E（复制/删除/空目录删/非空拒/空路径拒/
     缺失拒）+ 对齐算力定标（N=600/1500 同长名树——长度桶最坏形态墙钟）。

用法：cd specs/auto-edit/tests && AUTO_BIN=<钉版> python probe_dirdiff.py
退出码 = 勘定门（0 = 全 PASS；SKIP 不计败）。
"""

import ctypes
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from desktop_mcp import (  # noqa: E402
    McpClient, wait_for_server, pick_free_port, _kill_proc_tree,
    find_button_by_text,
)

AUTO_BIN = os.environ.get("AUTO_BIN") or shutil.which("auto") or ""
TESTS = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.normpath(os.path.join(TESTS, ".."))
PROBE_APP = os.path.join(TESTS, "probe_dirdiff_app")
FIXDIR = os.path.join(TESTS, "fixtures", "dirdiff")

CONTENT_CAP = 2 * 1024 * 1024   # 内容比对/启发式读预算域（≤2MB 全文）
ENTRY_CAP = 5000                # envelope 条目上限（计划预判；T-01 定参）

REPORT_PATH = os.path.join(TESTS, "probe_dirdiff_report.txt")

SKIP_LIST = ("/.", "/target/", "/node_modules/", "/gen/", "/dist/",
             "/build/", "/__pycache__/")


# ─────────────────────────────────────────────────────────────────────
# python 参考实现（目录 diff 分类语义=T-01 back 实现的对拍基准）
# ─────────────────────────────────────────────────────────────────────

def walk_tree(root):
    """目录树 → {rel: (size, is_dir)}；rel 剥根+"/"分隔；skip-list 同
    fif_skipped 语义（隐藏段/构建产物目录——段级判定）。"""
    out = {}
    norm_root = os.path.normpath(root)
    seg_skip = {"target", "node_modules", "gen", "dist", "build",
                "__pycache__"}
    for dirpath, dirnames, filenames in os.walk(root):
        for name in dirnames + filenames:
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, norm_root).replace("\\", "/")
            parts = rel.split("/")
            if any(p.startswith(".") for p in parts):
                continue
            if any(p in seg_skip for p in parts):
                continue
            is_dir = os.path.isdir(full)
            size = 0 if is_dir else os.path.getsize(full)
            out[rel] = (size, is_dir)
    return out


def is_binary_read(path, size):
    """启发式：size>0 且 read_text==""（非法 UTF-8 即二进制近似）。
    >2MB 全文不读（预算域）——返回 None=未知（走尺寸证据）。"""
    if size <= 0:
        return False
    if size > CONTENT_CAP:
        return None
    try:
        with open(path, "rb") as f:
            data = f.read()
        data.decode("utf-8")
        return False
    except (UnicodeDecodeError, OSError):
        return True


def read_text_lossy(path):
    try:
        with open(path, "rb") as f:
            return f.read().decode("utf-8")
    except (UnicodeDecodeError, OSError):
        return ""


def classify_tree(dir_a, dir_b):
    """目录 diff v1 分类（T-01 .at 实现的规范语义）：
    存在性 → dir-kind 冲突 → 二进制启发式（≤2MB 全文域；>2MB 前缀窗
    备选——本参考实现 >2MB 不读，走尺寸证据）→ 尺寸差 → ≤2MB 全等 →
    >2MB 同尺寸「同(未比对)」注记态。左=A=旧（删）、右=B=新（增）。"""
    A = walk_tree(dir_a)
    B = walk_tree(dir_b)
    entries = []
    counts = {"same": 0, "added": 0, "deleted": 0, "modified": 0,
              "binary": 0}
    truncated = False
    rels = list(A.keys()) + [r for r in B.keys() if r not in A]
    for rel in rels:
        if len(entries) >= ENTRY_CAP:
            truncated = True
            break
        in_a, in_b = rel in A, rel in B
        sa, da = A.get(rel, (0, False))
        sb, db = B.get(rel, (0, False))
        pa = os.path.join(dir_a, rel.replace("/", os.sep))
        pb = os.path.join(dir_b, rel.replace("/", os.sep))
        note = ""
        if in_a and not in_b:
            st = "deleted"
        elif in_b and not in_a:
            st = "added"
        elif da != db:
            st = "modified"
        elif da:
            st = "same"
        else:
            note = ""
            ba = is_binary_read(pa, sa)
            bb = is_binary_read(pb, sb)
            if ba or bb:
                st = "binary"
            elif sa > CONTENT_CAP or sb > CONTENT_CAP:
                if sa == sb:
                    st = "same"
                    note = "uncompared"
                else:
                    st = "modified"
            elif sa != sb:
                st = "modified"
            else:
                st = "same" if read_text_lossy(pa) == read_text_lossy(pb) \
                    else "modified"
        counts[st] += 1
        entries.append({"rel": rel, "status": st, "note": note,
                        "is_dir": da if in_a else db,
                        "size_a": sa if in_a else 0,
                        "size_b": sb if in_b else 0})
    return {"entries": entries, "counts": counts, "truncated": truncated,
            "err": ""}


# ─────────────────────────────────────────────────────────────────────
# fixtures（fixtures/dirdiff/：五形态+嵌套+空文件+dir 条目——提交件）
# ─────────────────────────────────────────────────────────────────────

INVALID_BYTES = b"\xff\xfe\xff\xfd\xbf\x80bin" * 4


def write_file(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    mode = "wb" if isinstance(data, bytes) else "w"
    with open(path, mode, **({} if mode == "wb" else
                             {"encoding": "utf-8", "newline": ""})) as f:
        f.write(data)


def build_fixtures():
    """fixtures/dirdiff/{base,rev}——五形态齐备：
    same（同文）/modified（尺寸差）/deleted·added（单侧）/binary（双二进制
    同字节）/nested（dir 条目+嵌套单侧）/empty（0B 双侧=same）。"""
    base = os.path.join(FIXDIR, "base")
    rev = os.path.join(FIXDIR, "rev")
    write_file(os.path.join(base, "same.txt"), "same content line\n")
    write_file(os.path.join(rev, "same.txt"), "same content line\n")
    write_file(os.path.join(base, "modified.txt"), "v1-short\n")
    write_file(os.path.join(rev, "modified.txt"),
               "v2-longer content\nsecond line\n")
    write_file(os.path.join(base, "deleted.txt"), "only in base\n")
    write_file(os.path.join(rev, "added.txt"), "only in rev\n")
    write_file(os.path.join(base, "binary.bin"), INVALID_BYTES)
    write_file(os.path.join(rev, "binary.bin"), INVALID_BYTES)
    write_file(os.path.join(base, "nested", "inner.txt"), "inner-v1\n")
    write_file(os.path.join(rev, "nested", "inner.txt"), "inner-v1\n")
    write_file(os.path.join(base, "nested", "old.txt"), "old only\n")
    write_file(os.path.join(rev, "nested", "new.txt"), "new only\n")
    write_file(os.path.join(base, "empty.txt"), "")
    write_file(os.path.join(rev, "empty.txt"), "")
    return base, rev


def golden_path():
    return os.path.join(FIXDIR, "dirdiff.golden.json")


# ─────────────────────────────────────────────────────────────────────
# RSS 观察（best-effort，注记口径非门）
# ─────────────────────────────────────────────────────────────────────

def proc_rss_kb(pid):
    try:
        import ctypes.wintypes as wt

        class PMC(ctypes.Structure):
            _fields_ = [("cb", wt.DWORD), ("PageFaultCount", wt.DWORD),
                        ("PeakWorkingSetSize", ctypes.c_size_t),
                        ("WorkingSetSize", ctypes.c_size_t),
                        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                        ("PagefileUsage", ctypes.c_size_t),
                        ("PeakPagefileUsage", ctypes.c_size_t)]

        pmc = PMC()
        pmc.cb = ctypes.sizeof(PMC)
        h = ctypes.windll.kernel32.OpenProcess(0x0400, False, pid)
        ok = ctypes.windll.psapi.GetProcessMemoryInfo(h, ctypes.byref(pmc),
                                                      pmc.cb)
        ctypes.windll.kernel32.CloseHandle(h)
        return pmc.WorkingSetSize // 1024 if ok else None
    except Exception:  # noqa: BLE001
        return None


# ─────────────────────────────────────────────────────────────────────
# 主流程
# ─────────────────────────────────────────────────────────────────────

def main():
    if not AUTO_BIN or not os.path.exists(AUTO_BIN):
        print(f"ERROR: auto binary not found (AUTO_BIN={AUTO_BIN or 'unset'})")
        sys.exit(2)

    report_lines = []
    checks = []
    decisions = {}

    def emit(line=""):
        print(line)
        report_lines.append(line)

    def check(item, name, ok, detail=""):
        checks.append({"item": item, "name": name, "ok": bool(ok),
                       "detail": str(detail)[:400]})
        emit(f"  {'PASS' if ok else 'FAIL'}  [{item}] {name}"
             + ("" if ok else f"  [{detail}]"))

    toolchain = subprocess.run([AUTO_BIN, "--version"], capture_output=True,
                               text=True).stdout.strip()
    emit(f"toolchain: {toolchain}")
    decisions["toolchain"] = toolchain

    # ============ fixtures + golden（python 参考实现） ============
    emit("\n" + "=" * 60)
    emit("golden：fixtures/dirdiff 五形态（python 参考实现=规范语义）")
    emit("=" * 60)
    base_dir, rev_dir = build_fixtures()
    ref = classify_tree(base_dir, rev_dir)
    gp = golden_path()
    if os.path.exists(gp):
        with open(gp, encoding="utf-8") as f:
            stored = json.load(f)
        golden_match = (stored["counts"] == ref["counts"] and
                        {e["rel"]: e["status"] for e in stored["entries"]}
                        == {e["rel"]: e["status"] for e in ref["entries"]} and
                        stored["truncated"] == ref["truncated"])
    else:
        with open(gp, "w", encoding="utf-8") as f:
            json.dump(ref, f, ensure_ascii=False, indent=2)
        golden_match = True
    check("golden", "dirdiff golden 自洽（五形态+嵌套+空文件）",
          golden_match and ref["err"] == "",
          f"counts={ref['counts']} n={len(ref['entries'])}")
    emit(f"       counts={ref['counts']} entries={len(ref['entries'])}")
    emit("       " + ", ".join(f"{e['rel']}:{e['status']}"
                               for e in ref["entries"]))

    # ============ ①a fs.copy 保留字阻断复现（迷你 app，可复现证据） ============
    emit("\n" + "=" * 60)
    emit("①a fs.copy 表面可达性：copy=保留字 token（Plan 122 废弃 ParamMode）")
    emit("=" * 60)
    mini = tempfile.mkdtemp(prefix="p012_kwprobe_")
    write_file(os.path.join(mini, "pac.at"),
               'name: "p012-kwprobe"\nversion: "0.1.0"\n'
               'scene: "ui"\nrender: "vm"\n')
    write_file(os.path.join(mini, "src", "back", "kw.at"),
               'pub fn kw_copy() str {\n'
               '    fs.copy("a", "b")\n'
               '    return "x"\n'
               '}\n')
    write_file(os.path.join(mini, "src", "front", "app.at"),
               'use back.kw: kw_copy\n\n'
               'store KwStore {\n'
               '    model { var out str = "" }\n'
               '    msg { PK }\n'
               '    on { .PK -> { .out = kw_copy() } }\n'
               '}\n\n'
               'widget App {\n'
               '    msg { PK }\n'
               '    view {\n'
               '        col (style: "h-full w-full p-2") {\n'
               '            button (text: "k", variant: "outline") '
               '{ onclick: .PK }\n'
               '            text .store.out { style: "text-xs font-mono" }\n'
               '        }\n'
               '    }\n'
               '    on { .PK -> { store.PK() } }\n'
               '}\n')
    kw = subprocess.run([AUTO_BIN, "run", "-r", "vm"], cwd=mini,
                        capture_output=True, text=True, timeout=120,
                        env={**os.environ})
    kw_out = (kw.stdout or "") + (kw.stderr or "")
    kw_blocked = kw.returncode != 0 and "got Copy" in kw_out
    check("①a", "fs.copy 词法阻断复现（非零退出+parser got Copy）",
          kw_blocked, f"rc={kw.returncode} "
          f"out={kw_out[-200:]!r}")
    if kw_blocked:
        emit("       证据：parser 'Expected identifier, @, *, number, or "
             "boolean after dot, got Copy'——fs.copy/File.copy 表面不可写")
    shutil.rmtree(mini, ignore_errors=True)
    decisions["fs_copy_keyword_block"] = {
        "verdict": "unwritable" if kw_blocked else "parse-accepted?",
        "token": "copy=TokenKind::Copy（token.rs:397，Plan 122 deprecated）",
        "evidence": "迷你 app 复现 rc!=0 + 'got Copy'" if kw_blocked
        else "复现未中——需人工复核"}

    # ============ ①②③ 载具会话（merged vm，MCP 驱动） ============
    emit("\n" + "=" * 60)
    emit("①②③ 载具会话：fs 五内建映射 + 二进制启发式 + 2MB 比对")
    emit("=" * 60)
    root = tempfile.mkdtemp(prefix="p012_probe_")
    # fixture 布局（探针专用 tmp——每项判定磁盘 E2E）
    write_file(os.path.join(root, "a", "f.txt"), "alpha-content-v1")
    write_file(os.path.join(root, "b", "f_exists.txt"), "OLD-CONTENT")
    write_file(os.path.join(root, "b", "f_del.txt"), "delete-me")
    os.makedirs(os.path.join(root, "b", "empty_dir"), exist_ok=True)
    write_file(os.path.join(root, "b_nonempty", "keep.txt"), "x")
    write_file(os.path.join(root, "a_tree", "top.txt"), "top-v1")
    write_file(os.path.join(root, "a_tree", "inner", "nested.txt"),
               "nested-v1")
    write_file(os.path.join(root, "b_tree_exists", "top.txt"), "OLD-TOP")
    write_file(os.path.join(root, "b_tree_del", "x.txt"), "1")
    write_file(os.path.join(root, "b_tree_del", "sub", "y.txt"), "2")
    write_file(os.path.join(root, "bin", "invalid.bin"), INVALID_BYTES)
    write_file(os.path.join(root, "bin", "empty.txt"), "")
    write_file(os.path.join(root, "bin", "valid.txt"), "just text")
    big_line = "0123456789abcdef" * 64  # 1KB/行
    big_same = "\n".join(big_line for _ in range(2048)) + "\n"  # ≈2MB
    big_a = "\n".join(
        (big_line if i != 1024 else "X" * 1024) for i in range(2048)) + "\n"
    write_file(os.path.join(root, "big", "same_a.txt"), big_same)
    write_file(os.path.join(root, "big", "same_b.txt"), big_same)
    write_file(os.path.join(root, "big", "diff_a.txt"), big_a)
    write_file(os.path.join(root, "big", "diff_b.txt"),
               big_same.replace("0123456789abcdef" * 64,
                                "0123456789abcdeF" * 64, 1))

    port = pick_free_port(9390)
    proc = subprocess.Popen(
        [AUTO_BIN, "run", "-r", "vm"],
        cwd=PROBE_APP, env={**os.environ, "AUTOUI_MCP_PORT": str(port),
                            "AUTO_DIRDIFF_PROBE": root},
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    url = f"http://127.0.0.1:{port}/mcp"
    toks = {}
    try:
        if not wait_for_server(url, 30):
            raise RuntimeError("MCP server did not start")
        mcp = McpClient(url)
        for _ in range(20):
            snap = mcp.snapshot()
            if "(rendered)" in snap and snap.count("onclick") > 0:
                break
            time.sleep(1)
        time.sleep(1.5)

        def click_and_read(label, key, timeout=90):
            """点按钮→轮询 state 全量→presence 解析 key{...}（每键唯一
            单击一次；state 读出带类型尾注——r1 教训：delta 切片错位）。"""
            el = find_button_by_text(mcp.snapshot(), label)
            if not el:
                return None, "button missing"
            mcp.click(el)
            t0 = time.time()
            pat = re.compile(r"(?:^|[^a-zA-Z0-9_])" + re.escape(key)
                             + r"\{([^}]*)\}")
            while time.time() - t0 < timeout:
                time.sleep(0.1)
                try:
                    now = mcp.state("out") or ""
                except Exception:  # noqa: BLE001
                    return None, "state error"
                mmatch = pat.search(now)
                if mmatch:
                    return mmatch.group(1), ""
            return None, "no-result"

        # root 注入复核（state 读出反斜杠转义形——双形归一比对）
        v, why = click_and_read("root", "root")

        def norm_path(s):
            if s is None:
                return None
            while "\\\\" in s:
                s = s.replace("\\\\", "\\")
            return s.replace("\\", "/")

        check("①", "env 注入→probe_root 读回",
              norm_path(v) == norm_path(root), f"{v!r} {why}")

        # ① 内建逐个（fs.copy 保留字阻断另证——见 ①a 迷你 app 复现）
        verdicts = {}
        for label, key in (("cp_bytes_small", "cp_bytes_small"),
                           ("cp_bytes_over", "cp_bytes_over"),
                           ("cp_bytes_big", "cp_bytes_big"),
                           ("cp_bytes_bin", "cp_bytes_bin"),
                           ("del_file", "del_file"),
                           ("rmdir_empty", "rmdir_empty"),
                           ("rmdir_nonempty", "rmdir_nonempty"),
                           ("cp_rec", "cp_rec"),
                           ("cp_rec_over", "cp_rec_over"),
                           ("rmdir_all", "rmdir_all")):
            v, why = click_and_read(label, key)
            verdicts[key] = v
            emit(f"       {key} = {v!r}" + (f" [{why}]" if why else ""))

        def _bytes_of(p):
            with open(p, "rb") as f:
                return f.read()

        # 磁盘 E2E 复核（verdict 串之外的第二证）
        e2e = {
            "cp_bytes_small": os.path.isfile(
                os.path.join(root, "b", "f_copy.txt"))
            and open(os.path.join(root, "b", "f_copy.txt"),
                     encoding="utf-8").read() == "alpha-content-v1",
            "cp_bytes_big": os.path.isfile(
                os.path.join(root, "b", "f_bytes_big.txt"))
            and os.path.getsize(os.path.join(root, "b", "f_bytes_big.txt"))
            == os.path.getsize(os.path.join(root, "big", "same_a.txt")),
            "cp_bytes_bin": os.path.isfile(
                os.path.join(root, "b", "f_bytes_bin.txt"))
            and _bytes_of(os.path.join(root, "b", "f_bytes_bin.txt"))
            == _bytes_of(os.path.join(root, "bin", "invalid.bin")),
            "del_file": not os.path.exists(
                os.path.join(root, "b", "f_del.txt")),
            "rmdir_empty": not os.path.exists(
                os.path.join(root, "b", "empty_dir")),
            "cp_rec": os.path.isfile(
                os.path.join(root, "b_tree_new", "inner", "nested.txt")),
            "rmdir_all": not os.path.exists(
                os.path.join(root, "b_tree_del")),
        }
        ok_map = {
            "cp_bytes_small": verdicts["cp_bytes_small"] == "ok"
            and e2e["cp_bytes_small"],
            "cp_bytes_over": verdicts["cp_bytes_over"] in
            ("overwritten", "target-kept", "no-effect", "throw") and
            (verdicts["cp_bytes_over"] != "overwritten" or
             open(os.path.join(root, "b", "f_exists.txt"),
                  encoding="utf-8").read() == "alpha-content-v1"),
            "cp_bytes_big": verdicts["cp_bytes_big"] == "ok-eq"
            and e2e["cp_bytes_big"],
            "cp_bytes_bin": verdicts["cp_bytes_bin"] == "ok"
            and e2e["cp_bytes_bin"],
            "del_file": verdicts["del_file"] == "ok" and e2e["del_file"],
            "rmdir_empty": verdicts["rmdir_empty"] == "ok"
            and e2e["rmdir_empty"],
            "rmdir_nonempty": os.path.exists(
                os.path.join(root, "b_nonempty")) and
            verdicts["rmdir_nonempty"] in ("kept", "throw", "no-effect"),
            "cp_rec": verdicts["cp_rec"] == "ok" and e2e["cp_rec"],
            "cp_rec_over": verdicts["cp_rec_over"] in
            ("overwritten", "target-kept", "no-effect", "throw"),
            "rmdir_all": verdicts["rmdir_all"] == "ok" and e2e["rmdir_all"],
        }
        for key, okk in ok_map.items():
            check("①", f"{key}: verdict+磁盘 E2E", okk,
                  f"verdict={verdicts[key]!r}")
        decisions["fs_builtins"] = {
            "file_copy_1007": "keyword-blocked（①a 迷你 app 复现——copy=保留字）",
            "file_copy_bytes_roundtrip": {
                "small": verdicts["cp_bytes_small"],
                "overwrite_2mb": verdicts["cp_bytes_over"],
                "big_2mb": verdicts["cp_bytes_big"],
                "binary": verdicts["cp_bytes_bin"]},
            "delete_1003": verdicts["del_file"],
            "remove_dir_empty_1014": verdicts["rmdir_empty"],
            "remove_dir_nonempty_guard": verdicts["rmdir_nonempty"],
            "copy_recursive_2862": verdicts["cp_rec"],
            "copy_recursive_overwrite": verdicts["cp_rec_over"],
            "remove_dir_all_1015": verdicts["rmdir_all"],
        }

        # ② 二进制启发式
        v, why = click_and_read("bin", "bin")
        okbin = False
        parsed = {}
        if v:
            for kv in v.split(","):
                if "=" in kv:
                    k2, _, v2 = kv.partition("=")
                    parsed[k2] = v2
            okbin = (parsed.get("inv") == "binary"
                     and int(parsed.get("meta", "0")) > 0
                     and parsed.get("empty0B") == "not-binary"
                     and int(parsed.get("txt_len", "0")) > 0)
        check("②", "二进制启发式（invalid→binary/0B 不误判/text 读出非空）",
              okbin, f"{v!r} {why}")
        emit(f"       bin 勘定: {v}")
        decisions["binary_heuristic"] = parsed
        decisions["read_range_prefix_form"] = {
            "total": parsed.get("rng_total"),
            "raw60": parsed.get("rng_raw")}

        # ③ 2MB 内容比对（墙钟+RSS 观察）
        rss0 = proc_rss_kb(proc.pid)
        t0 = time.time()
        v1, why1 = click_and_read("big_same", "big_same", timeout=120)
        t_same = time.time() - t0
        ok_same = v1 is not None and "verdict=eq" in v1
        check("③", "2MB 同内容 Str == → eq", ok_same, f"{v1!r} {why1}")
        t0 = time.time()
        v2, why2 = click_and_read("big_diff", "big_diff", timeout=120)
        t_diff = time.time() - t0
        ok_diff = v2 is not None and "verdict=uneq" in v2
        check("③", "2MB 同尺寸异内容 Str == → uneq", ok_diff,
              f"{v2!r} {why2}")
        rss1 = proc_rss_kb(proc.pid)
        emit(f"       墙钟: same={t_same:.2f}s diff={t_diff:.2f}s "
             f"RSS={rss0}KB→{rss1}KB（Δ{None if rss1 is None or rss0 is None else rss1 - rss0}KB）")
        decisions["bigcmp"] = {"same": v1, "diff": v2,
                               "wall_same_s": round(t_same, 3),
                               "wall_diff_s": round(t_diff, 3),
                               "rss_kb": [rss0, rss1]}
    except Exception as e:  # noqa: BLE001
        check("载具", "probe app 会话", False, repr(e)[:300])
    finally:
        _kill_proc_tree(proc)

    # ④ dialog_open 目录能力（静态勘定——人工步骤注记）
    emit("\n④ dialog_open 目录能力（静态勘定——rfd 阻塞式矩阵不可驱动）")
    emit("    人工步骤：菜单「工具 → 比较目录…」→ 双路径输入框手输目录路径")
    emit("    （v1 方案冻结：路径输入框+env 旁路；folder picker=upstream want）")
    decisions["dialog_open_dir"] = {
        "verdict": "file-only（rfd FileDialog 语义+catalog filter 形参数——"
                   "live 面不可驱动，静态勘定）",
        "v1_plan": "双路径输入框+env AUTO_DIRDIFF_A/B 旁路",
        "upstream_want": "dialog_pick_folder（目录选择对话框）→ §15 登记"}

    # ============ Phase A：⑤′/⑥′（端点在档时激活） ============
    emit("\n" + "=" * 60)
    emit("Phase A：diff_dirs/sync 端点（split back HTTP）")
    emit("=" * 60)
    port_a = pick_free_port(9395)
    srv_log = tempfile.NamedTemporaryFile(prefix="p012_srv_", suffix=".log",
                                          delete=False, mode="w",
                                          encoding="utf-8",
                                          errors="replace")
    proc_a = subprocess.Popen(
        [AUTO_BIN, "run", "--server", "vm", "-B", str(port_a)],
        cwd=PROJECT, env={**os.environ},
        stdout=srv_log, stderr=subprocess.STDOUT)
    srv_log.close()
    base_url = f"http://127.0.0.1:{port_a}"
    try:
        up = False
        for _ in range(40):
            try:
                requests.get(base_url + "/api/ws_root", timeout=2)
                up = True
                break
            except requests.ConnectionError:
                time.sleep(1)

        def deep_json(r):
            v = json.loads(r.text)
            if isinstance(v, str):
                v = json.loads(v)
            return v

        r = requests.get(base_url + "/api/diff_dirs",
                         params={"path_a": base_dir, "path_b": rev_dir},
                         timeout=30) if up else None
        if r is None or r.status_code == 404:
            emit("  SKIP  diff_dirs/sync 端点未在档——T-01/T-02 落地后重跑"
                 "本探针全绿（本节不计入 T-00 门）")
        else:
            # ⑤′ golden 逐字段
            try:
                env = deep_json(r)
                gold = json.load(open(gp, encoding="utf-8")) \
                    if os.path.exists(gp) else ref
                got_map = {e["rel"]: e for e in env.get("entries", [])}
                want_map = {e["rel"]: e for e in gold["entries"]}
                ok_env = (env.get("counts") == gold["counts"] and
                          got_map == want_map and
                          env.get("truncated") == gold["truncated"] and
                          env.get("err", "") == "")
                hint = ""
                if not ok_env:
                    hint = (f"counts {env.get('counts')} vs "
                            f"{gold['counts']} / n={len(got_map)} vs "
                            f"{len(want_map)} / err={env.get('err', '')[:40]!r}")
                    for k in want_map:
                        if got_map.get(k) != want_map[k]:
                            hint += f" first-diff@{k}: " \
                                f"{got_map.get(k)} vs {want_map[k]}"
                            break
                check("⑤′", "diff_dirs×dirdiff golden 逐字段", ok_env, hint)
            except Exception as e:  # noqa: BLE001
                check("⑤′", "diff_dirs golden", False, repr(e)[:200])

            # 错误形：根缺失不静默
            r2 = requests.get(base_url + "/api/diff_dirs",
                              params={"path_a": "Z:/nonexistent_p012",
                                      "path_b": rev_dir}, timeout=30)
            env2 = deep_json(r2)
            check("⑤′", "根缺失 err 形（不静默）",
                  env2.get("err", "") != "", repr(env2.get("err"))[:100])

            # 对齐算力定标（同长名树=长度桶最坏形态）：600/800=预算内
            # 全改对；1000/1500=桶积护栏优雅超限（err 形架构注记——T-01
            # 定标 N=800 过 0.65s/N=1000 WARN[budget] 死→700k 护栏）
            for n_files in (600, 800, 1000, 1500):
                tgen = tempfile.mkdtemp(prefix="p012_align_")
                ta = os.path.join(tgen, "a")
                tb = os.path.join(tgen, "b")
                for i in range(n_files):
                    write_file(os.path.join(ta, f"f{i:06d}.txt"), f"a{i}\n")
                    write_file(os.path.join(tb, f"f{i:06d}.txt"), f"b{i}\n")
                t0 = time.time()
                r3 = requests.get(base_url + "/api/diff_dirs",
                                  params={"path_a": ta, "path_b": tb},
                                  timeout=120)
                dt = time.time() - t0
                env3 = None
                try:
                    env3 = deep_json(r3)
                except Exception:  # noqa: BLE001
                    env3 = None
                if n_files <= 800:
                    if not isinstance(env3, dict):
                        check("⑤′",
                              f"对齐定标 N={n_files} 同长名（全改对）",
                              False,
                              f"非 dict envelope code={r3.status_code} "
                              f"body={r3.text[:120]!r} t={dt:.2f}s")
                    else:
                        c3 = env3.get("counts")
                        n_mod = c3.get("modified", -1) \
                            if isinstance(c3, dict) else -1
                        check("⑤′",
                              f"对齐定标 N={n_files} 同长名（全改对）",
                              n_mod == n_files and dt < 20.0,
                              f"counts={c3} t={dt:.2f}s")
                        emit(f"       N={n_files}: {dt:.2f}s counts={c3}")
                else:
                    ok_guard = isinstance(env3, dict) and \
                        "对齐超限" in (env3.get("err") or "")
                    check("⑤′",
                          f"对齐定标 N={n_files} 优雅超限（护栏 err 形）",
                          ok_guard,
                          f"code={r3.status_code} "
                          f"err={(env3 or {}).get('err', '')[:80]!r} "
                          f"t={dt:.2f}s")
                shutil.rmtree(tgen, ignore_errors=True)
            try:
                with open(srv_log.name, encoding="utf-8",
                          errors="replace") as f:
                    srv_txt = f.read()
                budget_hits = re.findall(r"WARN\[budget\] fn='([^']*)'",
                                         srv_txt)
                if budget_hits:
                    emit(f"       服务端预算墙证据: WARN[budget] × "
                         f"{len(budget_hits)} fn={sorted(set(budget_hits))}")
                decisions["align_budget_wall"] = {
                    "warn_budget_hits": sorted(set(budget_hits)),
                    "n_hits": len(budget_hits)}
            except OSError:
                pass

            # ⑥′ sync E2E（tmp 拷贝保 pristine）
            tsync = tempfile.mkdtemp(prefix="p012_sync_")
            sa = os.path.join(tsync, "a")
            sb = os.path.join(tsync, "b")
            shutil.copytree(base_dir, sa)
            shutil.copytree(rev_dir, sb)
            f_src = os.path.join(sa, "same.txt")
            f_dst = os.path.join(sb, "copied.txt")
            r4 = requests.post(base_url + "/api/sync_copy",
                               json={"src": f_src, "dst": f_dst,
                                     "is_dir": False}, timeout=30)
            ok4 = r4.status_code == 200 and deep_json(r4) in (True, 1, "true")
            check("⑥′", "sync_copy 文件（+磁盘 E2E）",
                  ok4 and os.path.isfile(f_dst), f"code={r4.status_code} "
                  f"body={r4.text[:60]!r}")
            r5 = requests.post(base_url + "/api/sync_delete",
                               json={"path": f_dst, "is_dir": False},
                               timeout=30)
            check("⑥′", "sync_delete 文件（+磁盘 E2E）",
                  r5.status_code == 200 and
                  deep_json(r5) in (True, 1, "true") and
                  not os.path.exists(f_dst), r5.text[:60])
            os.makedirs(os.path.join(sb, "empty_dir_p012"), exist_ok=True)
            r6 = requests.post(base_url + "/api/sync_delete",
                               json={"path": os.path.join(sb, "empty_dir_p012"),
                                     "is_dir": True}, timeout=30)
            check("⑥′", "sync_delete 空目录（+磁盘 E2E）",
                  r6.status_code == 200 and
                  deep_json(r6) in (True, 1, "true") and
                  not os.path.exists(os.path.join(sb, "empty_dir_p012")),
                  r6.text[:60])
            r7 = requests.post(base_url + "/api/sync_delete",
                               json={"path": os.path.join(sb, "nested"),
                                     "is_dir": True}, timeout=30)
            check("⑥′", "sync_delete 非空目录拒绝（护栏）",
                  deep_json(r7) in (False, 0, "false") and
                  os.path.exists(os.path.join(sb, "nested")),
                  r7.text[:60])
            def _rejected(rq):
                try:
                    v = deep_json(rq)
                except Exception:  # noqa: BLE001
                    return False
                if isinstance(v, dict):
                    return "error" in v
                return v in (False, 0, "false")

            r8 = requests.post(base_url + "/api/sync_delete",
                               json={"path": "", "is_dir": False},
                               timeout=30)
            r9 = requests.post(base_url + "/api/sync_delete",
                               json={"path": "Z:/nonexistent_p012",
                                     "is_dir": False}, timeout=30)
            check("⑥′", "sync_delete 空路径/缺失拒绝",
                  _rejected(r8) and _rejected(r9),
                  f"{r8.text[:40]!r} {r9.text[:40]!r}")
            shutil.rmtree(tsync, ignore_errors=True)
    finally:
        _kill_proc_tree(proc_a)

    # ============ 汇总 ============
    report = {"toolchain": toolchain, "decisions": decisions,
              "checks": checks,
              "pass": all(c["ok"] for c in checks)}
    emit("\n" + "=" * 60)
    emit("T-00 决策记录（decisions）")
    emit("=" * 60)
    emit(json.dumps(decisions, ensure_ascii=False, indent=2))
    failed = [c for c in checks if not c["ok"]]
    emit(f"\nRESULT: {len(checks) - len(failed)} passed, "
         f"{len(failed)} failed")
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines) + "\n")
    with open(REPORT_PATH.replace(".txt", ".json"), "w",
              encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\nreport: {REPORT_PATH}")
    sys.exit(0 if report["pass"] else 1)


if __name__ == "__main__":
    main()
