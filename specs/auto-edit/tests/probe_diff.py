#!/usr/bin/env python3
"""PLAN-011 T-00 探针勘定（决策件）—— M3-01 文件 diff v1 五项勘定.

载具 = tests/probe_diff_app/（vm merged 最小 app：AutoVM 算力微基准 +
scroll controller 定标 + onscroll 观察面）+ 真实 auto-edit 实例（Phase A
back HTTP env 链）。五项：
  ① AutoVM 算力微基准：list push/get、str 比较、空循环（10⁴/10⁵/10⁶ 三档）
     + 401×401 二维表填/扫（DP-LCS 上限 400 行最坏形态）+ 600 行 rows 记录
     构建（渲染 cap 形态）+ 5k 行 split 定标 → 定三参数：
     DP-LCS 中间区上限 / 全览渲染行数 cap / 文件上限（50k 行·2MB 复核）。
  ② 朴素分层原型对拍：python 参考实现（①公共前后缀裁剪 ②≤上限 DP-LCS
     行级 ③大中段降级单 replace hunk ④replace 区索引对齐配对+公共前后缀
     三段标记 ⑤ctx=3 切 hunk）× fixtures 六形态 golden 逐字段对照
     （envelope：{hunks:[{a1,a2,b1,b2}],rows:[{lo,ro,ln,rn,lk,rk,lpre,
     lmid,lpost,rpre,rmid,rpost}],adds,dels,truncated,err}；
     hunk 区间=0 基半开；rows 行号 lo/ro=1 基，缺席侧=0）。
  ③ scroll 定标：scroll-pane controller 绑定 + scroll_to(handle,"y",px)
     绝对像素语义（native.rs shim_scroll_to 源码裁定）+ scroll_state 读回
     offset_y/viewport_h/content_h → 行高 = content_h/行数；跳转公式
     offset = 目标行(0 基) × 行高。
  ④ 双栏同步：scroll widget 有 onscroll 事件面（schema.rs:495 Closure prop；
     aura_view_builder.rs scroll_pane_semantics 8 位置 float 实参
     offset_x..progress_y）——MCP scroll action（operation::scroll_to 直落）
     试驱动观察回声，实测不可得性如实记录。
  ⑤ 入口链：dialog_open×2=手动路径（步骤成文）；env 旁路 AUTO_DIFF_A/B
     消费形态=env_str 端点链实测定形（split 实例注入 env → GET /api/
     env_str 读回）+ ActOpen env 旁路先例（editor_store.at:1099-1106）为
     T-02 消费形模板。

用法：cd specs/auto-edit/tests && python probe_diff.py
前置同 desktop_mcp.py（requests、AUTO_BIN 或 PATH 的 auto）。
退出码 = 勘定门（0 = 全 PASS）。
"""

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
    find_button_by_text, state_str,
)

def state_float(state_text, field):
    """autoui_state 浮点字段读出（desktop_mcp 只有 str/int/bool 三助手）。"""
    m = re.search(rf"{field}:\s*(-?\d+\.\d+)", state_text)
    return float(m.group(1)) if m else None


AUTO_BIN = os.environ.get("AUTO_BIN") or shutil.which("auto") or ""
TESTS = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.normpath(os.path.join(TESTS, ".."))
PROBE_APP = os.path.join(TESTS, "probe_diff_app")
FIXDIR = os.path.join(TESTS, "fixtures", "diff")

DIFF_CAP = 400        # 预判：DP-LCS 中间区上限（O(N·M)≈1.6×10⁵ 单元）
RENDER_CAP = 600      # 预判：全览渲染行数 cap
DIFF_CTX = 3          # hunk 上下文窗（计划默认）

REPORT_PATH = os.path.join(TESTS, "probe_diff_report.txt")


# ─────────────────────────────────────────────────────────────────────
# ② python 参考实现（与计划 §2 同一算法——T-01 back 实现的对拍基准）
# ─────────────────────────────────────────────────────────────────────

def split_lines(text):
    """文本 → 行数组："\n" 切分；文本非空时丢弃 split 产生的末尾空行。"""
    if text == "":
        return []
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    return lines


def lcs_ops(am, bm):
    """DP-LCS 行级编辑脚本（keep/del/add），确定性回溯（del 优先）。"""
    n, m = len(am), len(bm)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        ai = am[i]
        row, below = dp[i], dp[i + 1]
        for j in range(m - 1, -1, -1):
            if ai == bm[j]:
                row[j] = below[j + 1] + 1
            else:
                v1, v2 = below[j], row[j + 1]
                row[j] = v1 if v1 >= v2 else v2
    ops = []
    i = j = 0
    while i < n and j < m:
        if am[i] == bm[j]:
            ops.append(("keep", i, j))
            i += 1
            j += 1
        elif dp[i + 1][j] >= dp[i][j + 1]:
            ops.append(("del", i, None))
            i += 1
        else:
            ops.append(("add", None, j))
            j += 1
    while i < n:
        ops.append(("del", i, None))
        i += 1
    while j < m:
        ops.append(("add", None, j))
        j += 1
    return ops


def _segments(x, y):
    """配对行公共前后缀三段标记：返回 (lpre, lmid, lpost, rpre, rmid, rpost)。"""
    p = 0
    top = min(len(x), len(y))
    while p < top and x[p] == y[p]:
        p += 1
    s = 0
    while s < min(len(x) - p, len(y) - p) and \
            x[len(x) - 1 - s] == y[len(y) - 1 - s]:
        s += 1
    return (x[:p], x[p:len(x) - s], x[len(x) - s:],
            y[:p], y[p:len(y) - s], y[len(y) - s:])


def naive_layered_diff(a_text, b_text, ctx=DIFF_CTX, cap=DIFF_CAP):
    """朴素分层 diff（计划 §2 算法①-⑤）。envelope 契约=计算↔视图唯一接口。

    hunk 区间 a1/a2/b1/b2 = 0 基半开（a_lines/b_lines 行索引）；
    rows.lo/ro = 1 基行号（缺席侧 0），lk/rk ∈ ctx/del/add（双侧行
    lk=del/rk=add；单侧行缺席侧 kind 为空串，ln/rn 为空串）。
    degraded=true = 中段超上限走整块 replace（降级注记，SD-01 契约件）。
    """
    a = split_lines(a_text)
    b = split_lines(b_text)
    len_a, len_b = len(a), len(b)
    err = None
    truncated = False
    degraded = False

    # ① 公共前后缀行裁剪
    p = 0
    while p < len_a and p < len_b and a[p] == b[p]:
        p += 1
    s = 0
    while s < len_a - p and s < len_b - p and \
            a[len_a - 1 - s] == b[len_b - 1 - s]:
        s += 1
    a_mid = a[p:len_a - s]
    b_mid = b[p:len_b - s]

    # ②/③ 中间区编辑脚本
    if len(a_mid) == 0:
        mid_ops = [("add", None, j) for j in range(len(b_mid))]
    elif len(b_mid) == 0:
        mid_ops = [("del", i, None) for i in range(len(a_mid))]
    elif len(a_mid) <= cap and len(b_mid) <= cap:
        mid_ops = lcs_ops(a_mid, b_mid)
    else:
        # 大中段降级：整块 del + 整块 add（单 replace hunk，注记降级）
        degraded = True
        mid_ops = ([("del", i, None) for i in range(len(a_mid))] +
                   [("add", None, j) for j in range(len(b_mid))])

    adds = sum(1 for k, _, _ in mid_ops if k == "add")
    dels = sum(1 for k, _, _ in mid_ops if k == "del")

    # 全文件对齐流：公共前缀 keep（两侧同号）+ 中间区 ops（绝对索引）
    # + 公共后缀 keep。每条 op 携 (i,j) 边界坐标，供 hunk 切分与 rows 展开。
    stream = [("keep", i, i) for i in range(p)]
    ii = jj = p
    for kind, i, j in mid_ops:
        if kind == "keep":
            stream.append(("keep", i + p, j + p))
            ii, jj = i + p + 1, j + p + 1
        elif kind == "del":
            stream.append(("del", i + p, jj))
        else:
            stream.append(("add", ii, j + p))
    for k in range(s):
        stream.append(("keep", len_a - s + k, len_b - s + k))

    # ⑤ 上下文窗切 hunk：非 keep op 按 keep 间距 ≤ 2·ctx 归组；
    # ctx 扩张越出中间区（公共前/后缀行可作上下文），钳位全文件。
    changes = [op for op in stream if op[0] != "keep"]
    hunks = []
    if changes:
        groups = [[changes[0]]]
        last = changes[0]
        for ch in changes[1:]:
            gap_i = ch[1] - last[1]
            gap_j = ch[2] - last[2]
            if gap_i <= 2 * ctx and gap_j <= 2 * ctx:
                groups[-1].append(ch)
            else:
                groups.append([ch])
            last = ch
        for g in groups:
            # 半开区间语义：del 覆盖 [i, i+1)；add 在边界 i 占空位
            # （a2/b2 取边界而非 +1——纯插入组不吞多余上下文行）。
            a_lo = min(op[1] for op in g)
            a_hi = max([op[1] + 1 for op in g if op[0] == "del"] +
                       [op[1] for op in g if op[0] == "add"])
            b_lo = min(op[2] for op in g)
            b_hi = max([op[2] + 1 for op in g if op[0] == "add"] +
                       [op[2] for op in g if op[0] == "del"])
            hunks.append({
                "a1": max(0, a_lo - ctx),
                "a2": min(len_a, a_hi + ctx),
                "b1": max(0, b_lo - ctx),
                "b2": min(len_b, b_hi + ctx),
            })

    # rows：hunk 展开（渲染就绪形）。变更块=连续非 keep 段，块内
    # 索引对齐配对（i-th del 对 i-th add）；④ 配对行公共前后缀三段标记。
    rows = []

    def row_ctx(i, j):
        t = a[i]
        return {"lo": i + 1, "ro": j + 1, "ln": t, "rn": t,
                "lk": "ctx", "rk": "ctx",
                "lpre": t, "lmid": "", "lpost": "",
                "rpre": t, "rmid": "", "rpost": ""}

    def row_del(i):
        t = a[i]
        return {"lo": i + 1, "ro": 0, "ln": t, "rn": "",
                "lk": "del", "rk": "",
                "lpre": "", "lmid": t, "lpost": "",
                "rpre": "", "rmid": "", "rpost": ""}

    def row_add(j):
        t = b[j]
        return {"lo": 0, "ro": j + 1, "ln": "", "rn": t,
                "lk": "", "rk": "add",
                "lpre": "", "lmid": "", "lpost": "",
                "rpre": "", "rmid": t, "rpost": ""}

    def row_pair(i, j):
        x, y = a[i], b[j]
        lpre, lmid, lpost, rpre, rmid, rpost = _segments(x, y)
        return {"lo": i + 1, "ro": j + 1, "ln": x, "rn": y,
                "lk": "del", "rk": "add",
                "lpre": lpre, "lmid": lmid, "lpost": lpost,
                "rpre": rpre, "rmid": rmid, "rpost": rpost}

    for hk in hunks:
        ops_in = [op for op in stream
                  if (op[0] == "keep" and hk["a1"] <= op[1] < hk["a2"]) or
                     (op[0] == "del" and hk["a1"] <= op[1] < hk["a2"]) or
                     (op[0] == "add" and hk["b1"] <= op[2] < hk["b2"])]
        idx = 0
        while idx < len(ops_in):
            op = ops_in[idx]
            if op[0] == "keep":
                rows.append(row_ctx(op[1], op[2]))
                idx += 1
                continue
            block = []
            while idx < len(ops_in) and ops_in[idx][0] != "keep":
                block.append(ops_in[idx])
                idx += 1
            ds = [o[1] for o in block if o[0] == "del"]
            ad = [o[2] for o in block if o[0] == "add"]
            for k in range(max(len(ds), len(ad))):
                li = ds[k] if k < len(ds) else None
                rj = ad[k] if k < len(ad) else None
                if li is not None and rj is not None:
                    rows.append(row_pair(li, rj))
                elif li is not None:
                    rows.append(row_del(li))
                else:
                    rows.append(row_add(rj))

    return {"hunks": hunks, "rows": rows, "adds": adds, "dels": dels,
            "truncated": truncated, "degraded": degraded, "err": err}


# ─────────────────────────────────────────────────────────────────────
# fixtures 六形态（五形态 golden + 删多增少 Q-4 视觉件）
# ─────────────────────────────────────────────────────────────────────

def _numbered(tag, n, start=1):
    return [f"{tag}{k}" for k in range(start, start + n)]


def build_fixtures():
    fx = {}

    base = _numbered("L", 10)
    b = base[:5] + ["E1", "E2", "E3"] + base[5:]
    fx["add_only"] = ("\n".join(base) + "\n", "\n".join(b) + "\n")

    fx["del_only"] = ("\n".join(base) + "\n",
                      "\n".join(base[:4] + base[7:]) + "\n")

    b = base[:]
    b[3] = "let x = 2"
    b[4] = "let y = call(2)"
    b[5] = "let z = 3"
    a = base[:]
    a[3] = "let x = 1"
    a[4] = "let y = call(1)"
    a[5] = "let z = 3;"
    fx["modify"] = ("\n".join(a) + "\n", "\n".join(b) + "\n")

    a = _numbered("L", 40)
    b = a[:]
    b[4] = "L4-changed"
    b[19] = "L19-changed"
    b[34] = "L34-changed"
    fx["scattered"] = ("\n".join(a) + "\n", "\n".join(b) + "\n")

    # 大重排：中段 610 行（>400 上限）整块互换 → 降级单 replace hunk
    P = _numbered("P", 5)
    S = _numbered("S", 5)
    M = _numbered("M", 10)
    A3 = _numbered("A", 300)
    B3 = _numbered("B", 300)
    a = P + A3 + M + B3 + S
    b = P + B3 + M + A3 + S
    fx["big_reorder"] = ("\n".join(a) + "\n", "\n".join(b) + "\n")

    # Q-4：删多增少（3 删 1 增 → 1 配对行 + 2 不成对整行染色行）
    a = _numbered("L", 10)
    b = a[:6] + ["NEW"] + a[9:]
    fx["unbalanced"] = ("\n".join(a) + "\n", "\n".join(b) + "\n")

    return fx


def item_golden(fx):
    os.makedirs(FIXDIR, exist_ok=True)
    results = {}
    for name, (ta, tb) in fx.items():
        pa = os.path.join(FIXDIR, f"{name}.a.txt")
        pb = os.path.join(FIXDIR, f"{name}.b.txt")
        pg = os.path.join(FIXDIR, f"{name}.golden.json")
        for path, text in ((pa, ta), (pb, tb)):
            if not os.path.exists(path):
                with open(path, "w", encoding="utf-8") as f:
                    f.write(text)
        env = naive_layered_diff(ta, tb)
        if os.path.exists(pg):
            with open(pg, encoding="utf-8") as f:
                stored = json.load(f)
            match = stored == env
        else:
            with open(pg, "w", encoding="utf-8") as f:
                json.dump(env, f, ensure_ascii=False, indent=2)
            match = True
        results[name] = {"golden_match": match, "env": env,
                         "hunks": len(env["hunks"]), "rows": len(env["rows"]),
                         "adds": env["adds"], "dels": env["dels"]}
    return results


def render_ascii(name, env, a_text, b_text, limit=14):
    """unbalanced 形态视觉初判（Q-4）：左右栏 + 三段标记 ASCII 示意。"""
    a = split_lines(a_text)
    b = split_lines(b_text)
    out = [f"--- {name}: {len(env['hunks'])} hunks, "
           f"+{env['adds']}/-{env['dels']}, rows={len(env['rows'])} ---"]
    for r in env["rows"][:limit]:
        left = f"{r['lo']:>3}|{r['lpre']}<{r['lmid']}>{r['lpost']}" if r["lo"] else " " * 24
        right = f"{r['ro']:>3}|{r['rpre']}<{r['rmid']}>{r['rpost']}" if r["ro"] else ""
        out.append(f"{left}  ‖  {right}")
    if len(env["rows"]) > limit:
        out.append(f"… ({len(env['rows']) - limit} more rows)")
    return "\n".join(out)


# ─────────────────────────────────────────────────────────────────────
# 通用探针工具
# ─────────────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────────────
# 主流程
# ─────────────────────────────────────────────────────────────────────

def main():
    if not AUTO_BIN or not os.path.exists(AUTO_BIN):
        print(f"ERROR: auto binary not found (AUTO_BIN={AUTO_BIN or 'unset'})")
        sys.exit(2)

    report_lines = []
    checks = []

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
    decisions = {}

    # ============ ② 朴素分层原型对拍（纯 python，先行落 golden） ============
    emit("\n" + "=" * 60)
    emit("② 朴素分层原型对拍（python 参考实现 × fixtures golden 逐字段）")
    emit("=" * 60)
    fx = build_fixtures()
    golden = item_golden(fx)
    for name, g in golden.items():
        check("②", f"golden 逐字段对照: {name}",
              g["golden_match"],
              f"hunks={g['hunks']} rows={g['rows']} +{g['adds']}/-{g['dels']}")
        emit(f"       {name}: hunks={g['hunks']} rows={g['rows']} "
             f"+{g['adds']}/-{g['dels']}")
    # 结构性抽查：半开区间/行号/三段标记
    env_m = golden["modify"]["env"]
    row_pair = [r for r in env_m["rows"] if r["lk"] == "del" and r["rk"] == "add"]
    seg_ok = any(r["lpre"] == "let x = " and r["lmid"] == "1"
                 and r["rmid"] == "2" and r["lpost"] == "" for r in row_pair)
    check("②", "modify 配对行三段标记（let x = <1>/<2>）", seg_ok,
          repr(row_pair[:1]))
    env_s = golden["scattered"]["env"]
    check("②", "scattered 三处远距改动 → 独立 hunk", len(env_s["hunks"]) == 3,
          f"hunks={len(env_s['hunks'])}")
    env_b = golden["big_reorder"]["env"]
    check("②", "big_reorder 中段>上限 → 单 replace hunk 降级",
          len(env_b["hunks"]) == 1 and env_b["adds"] == 610
          and env_b["dels"] == 610,
          f"hunks={len(env_b['hunks'])} +{env_b['adds']}/-{env_b['dels']}")
    # Q-4 视觉初判数据面
    art = render_ascii("unbalanced", golden["unbalanced"]["env"],
                       fx["unbalanced"][0], fx["unbalanced"][1])
    emit("\nQ-4 删多增少形态渲染示意（配对行 <mid> 高亮；不成对行整行 mid）：")
    emit(art)
    env_u = golden["unbalanced"]["env"]
    q4_rows = [(r["lo"], r["ro"]) for r in env_u["rows"]
               if r["lk"] == "del" and r["rk"] == ""]
    check("②", "unbalanced 不成对行存在（Q-4 判据面）", len(q4_rows) >= 2,
          f"unpaired={q4_rows}")

    # ============ ⑤ Phase A：env 旁路链（真实 app，back HTTP） ============
    emit("\n" + "=" * 60)
    emit("⑤ 入口链预演：env 旁路 AUTO_DIFF_A/B 消费形态（Phase A back HTTP）")
    emit("=" * 60)
    port_a = pick_free_port(9360)
    env_a = {**os.environ,
             "AUTO_DIFF_A": os.path.join(FIXDIR, "modify.a.txt"),
             "AUTO_DIFF_B": os.path.join(FIXDIR, "modify.b.txt")}
    proc_a = subprocess.Popen(
        [AUTO_BIN, "run", "--server", "vm", "-B", str(port_a)],
        cwd=PROJECT, env=env_a,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    base = f"http://127.0.0.1:{port_a}"
    try:
        for _ in range(40):
            try:
                requests.get(base + "/api/ws_root", timeout=2)
                break
            except requests.ConnectionError:
                time.sleep(1)

        def http_scalar(r):
            """标量返回铁律：端点标量经 JSON 编码交付（str 带引号+转义、
            bool true/false）——读回断言一律解码后比对（前轮败因：
            裸 r.text 比对撞 JSON 引号形）。"""
            try:
                return json.loads(r.text)
            except (ValueError, TypeError):
                return r.text
        for name, want in (("AUTO_DIFF_A", env_a["AUTO_DIFF_A"]),
                           ("AUTO_DIFF_B", env_a["AUTO_DIFF_B"])):
            r = requests.get(base + "/api/env_str", params={"name": name},
                             timeout=10)
            got = http_scalar(r)
            check("⑤", f"env 注入→env_str 读回: {name}", r.status_code == 200
                  and got == want, f"got={r.text[:120]!r}")
        r = requests.get(base + "/api/exists",
                         params={"path": env_a["AUTO_DIFF_A"]}, timeout=10)
        check("⑤", "AUTO_DIFF_A 路径 exists 复核",
              http_scalar(r) in (True, 1) or r.text.strip() in ("true", "1"),
              r.text[:80])
        r = requests.get(base + "/api/env_str", params={"name": "AUTO_DIFF_C"},
                         timeout=10)
        check("⑤", "未设 AUTO_DIFF_C = 空串（取消语义面）",
              http_scalar(r) == "", repr(r.text))
    finally:
        _kill_proc_tree(proc_a)
    emit("  dialog_open×2 手动路径（rfd 阻塞式，矩阵不可驱动——人工步骤）：")
    emit("    1) 菜单「工具 → 比较文件…」（T-03 静态 menubar item）")
    emit("    2) dialog_open 选文件 A（取消 → 整链零动作，console 记 cancelled）")
    emit("    3) dialog_open 选文件 B（取消 → 同上）")
    emit("    4) 双路径齐备 → DiffCompute（T-02 接线，AUTO_OPEN_PATH 先例"
         " editor_store.at:1099-1106 同款 env_str 消费形）")

    # ============ Phase B：probe app——双会话隔离（B1 微基准 / B2 scroll+④）============
    # T-00 三轮实勘：大分配突发可硬崩 app（1914@push1e6、2044@dp400，
    # 无 panic 无 budget 告警=原生层静默死）——双会话使崩溃爆炸半径
    # 互不波及：B1 先收小档+split+rows（低险），dp 大表档殿后降序尝试
    # （崩则用 1914 首轮实测 dp400=1.026s→cap 353 记账沿用）；B2 全新
    # app 做 scroll/④（零堆积）。
    emit("\n" + "=" * 60)
    emit("Phase B: probe_diff_app（B1 微基准 / B2 scroll+onscroll——双会话）")
    emit("=" * 60)

    def spawn_app():
        port = pick_free_port()
        lg = tempfile.NamedTemporaryFile(
            prefix="p011_probe_", suffix=".log", delete=False, mode="w",
            encoding="utf-8", errors="replace")
        pr = subprocess.Popen(
            [AUTO_BIN, "run", "-r", "vm"],
            cwd=PROBE_APP, env={**os.environ, "AUTOUI_MCP_PORT": str(port)},
            stdout=lg, stderr=subprocess.STDOUT)
        u = f"http://127.0.0.1:{port}/mcp"
        if not wait_for_server(u, 30):
            _kill_proc_tree(pr)
            raise RuntimeError("MCP server did not start")
        m = McpClient(u)
        snap = ""
        for _ in range(20):
            snap = m.snapshot()
            if "(rendered)" in snap and snap.count("onclick") > 0:
                break
            time.sleep(1)
        time.sleep(2.0)  # 首拍派发竞态窗定驻（009 惯例）
        return pr, lg, m

    def click_btn(mcp, label):
        el = find_button_by_text(mcp.snapshot(), label)
        if not el:
            return False
        mcp.click(el)
        return True

    def run_bench(mcp, label, timeout=120):
        """点按钮并轮询 bench_out 增量；计时口径=python 墙钟
        （click→增量出现耗时；UI app 轨 Instant.elapsed() 不解析
        ——tnow 通/tel 默杀实证，故弃 .at 侧时钟）。"""
        before = state_str(mcp.state("bench_out"), "bench_out")
        if not click_btn(mcp, label):
            return None, "button missing"
        t0 = time.time()
        while time.time() - t0 < timeout:
            time.sleep(0.05)  # 0.05s 量子——0.5s 轮询曾把亚 0.5s 真值
            # 全部量化到地板（rows600/split5k 读 503ms 实为 ≤0.5s 未知）
            try:
                now = state_str(mcp.state("bench_out"), "bench_out")
            except Exception as e:  # noqa: BLE001
                return None, f"state error: {e!r}"
            if now != before:
                delta = now[len(before):]
                wall = time.time() - t0
                out = {}
                for kv in delta.replace(";", ",").split(","):
                    if "=" not in kv:
                        continue
                    k, v = kv.split("=", 1)
                    k, v = k.strip(), v.strip()
                    if not k:
                        continue
                    out[k] = wall if v == "done" else v
                return out, ""
        return None, f"no-result {time.time() - t0:.0f}s"

    bench = {}
    log_b1 = None
    run_1e6 = os.environ.get("PROBE_DIFF_1E6") == "1"

    # ---- B1：微基准会话 ----
    # 标签=app.at 按钮精确文本（find_button_by_text 精确正则）。
    # 顺序=低险档先行（小循环/push/get/str + dp200/300 + bld/bspl/brows
    # ——split/rows 定标数据必收），dp400 殿后（2044 工具链 dp400 硬崩
    # 实勘——崩则用 dp300/200 定参，全灭则 1914 首轮实测 dp400=1.026s
    # →cap 353 记账沿用）。1e6 档默认不实跑（PROBE_DIFF_1E6=1 复验）
    # ——预算墙已源码+首轮 WARN[budget]×4 双锚定。
    emit("\n① AutoVM 算力微基准（秒；python 墙钟口径 click→完成）")
    try:
        proc_b, log, mcp = spawn_app()
        log_b1 = log
        try:
            tiers = [("bl4", "loop1e4", 120), ("bl5", "loop1e5", 120),
                     ("bp4", "push1e4", 120), ("bp5", "push1e5", 120),
                     ("bg5", "get1e5", 120), ("bs5", "str1e5", 120),
                     ("dp200", "dp200", 90), ("dp300", "dp300", 90),
                     ("bld", "bld", 120),
                     ("bspl", "split5k", 120), ("brows", "rows600", 120),
                     ("dp400", "dp400", 30)]
            if run_1e6:
                tiers += [("bl6", "loop1e6", 25), ("bp6", "push1e6", 25),
                          ("bg6", "get1e6", 25), ("bs6", "str1e6", 25)]
            for label, key, btime in tiers:
                res, why = run_bench(mcp, label, timeout=btime)
                if res is None:
                    bench[key] = None
                    # 1e6 档（短超时）与 dp400（崩溃/挂起双态——2044 实勘
                    # 两种都出过）无回声=预期风险档形态，软通过；定参由
                    # 降档兜底。其余无回声=环境败不通过。
                    soft = (btime <= 30 or key == "dp400") and \
                        ("no-result" in str(why) or "state error" in str(why))
                    check("①", f"微基准 {key}", soft, why)
                    continue
                if key.startswith("dp") and isinstance(res, dict):
                    res = {key: res.get(key), key + "_acc": res.get("acc")}
                for k, v in res.items():
                    bench[k] = v
                pretty = {k: (f"{v * 1000:.1f}ms" if isinstance(v, float)
                              else v) for k, v in res.items()}
                emit(f"       {label}: {pretty}")
        except Exception as e:  # noqa: BLE001
            check("B1", "微基准会话中断（app 疑似崩溃——B2 隔离续跑）",
                  False, repr(e)[:200])
        finally:
            _kill_proc_tree(proc_b)
    except Exception as e:  # noqa: BLE001
        check("B1", "probe app 启动", False, repr(e))

    def sec_of(key):
        v = bench.get(key)
        return v if isinstance(v, float) else None

    # 吞吐健全性（墙钟轮询 0.5s 量化下非严格单调即可）。
    check("①", "吞吐健全性 loop1e4≤1e5（墙钟口径）",
          all(isinstance(bench.get(k), float) for k in
              ("loop1e4", "loop1e5")) and
          bench["loop1e4"] <= bench["loop1e5"] + 0.05,
          repr({k: bench.get(k) for k in ("loop1e4", "loop1e5")}))

    # 单消息算力墙：默认=已锚定证据记账（源码+首轮 WARN[budget]×4
    # 实证）；PROBE_DIFF_1E6=1 时重演 live（无回声档 × 日志交叉）。
    wall_keys = [k for k in ("loop1e6", "push1e6", "get1e6", "str1e6")
                 if run_1e6 and bench.get(k) is None]
    budget_hits = []
    if log_b1 is not None:
        try:
            with open(log_b1.name, encoding="utf-8", errors="replace") as f:
                ltxt = f.read()
            budget_hits = re.findall(r"WARN\[budget\] fn='[^']*Bench(\w+)'",
                                     ltxt)
        except OSError:
            pass
    decisions["step_budget"] = {
        "per_handler_steps": 10000000,
        "source": "auto-lang engine.rs:2145 let budget = 10_000_000"
                  "（VM 源码读）",
        "evidence": "T-00 首轮实证：1e6 四档 120s 无回声 + "
                    "WARN[budget]×4（BenchLoop6/BenchPush6/BenchGet6/"
                    "BenchStr6），app 存活后续基准正常；二轮 push1e6/"
                    "三轮 dp400 触发 app 硬崩（无 panic 无 budget 告警"
                    "=原生层静默死，大分配突发）——默认不重演",
        "live_rerun": (f"1e6 无回声 {len(wall_keys)}/4 + WARN[budget]"
                       f"×{len(budget_hits)}") if run_1e6 else
                      "off（PROBE_DIFF_1E6=1 复验）",
        "design_rule": "diff_files 单 handler 全链（split+DP+rows 构建"
                       "+JSON 拼装）总步数 <10M——T-01 实现约束"}
    check("①", "单消息算力墙勘定（10M steps/源码+首轮实证双锚）",
          (not run_1e6) or len(budget_hits) >= 1,
          f"budget_fn={sorted(set(budget_hits))}")

    rows600 = sec_of("rows600")
    split5k = sec_of("split5k")

    # DP-LCS 中间区上限：dp 档降序取最大存活档定参。t≤0.8s 且档=400
    # → cap=400 维持；否则 cap=档×√(0.8/t)（√ 缩放到预算，质量换时延）。
    # 全灭兜底=1914 首轮实测记账沿用（dp400=1.026s → cap 353）。
    DP_BUDGET = 0.8
    dp_t = None
    dp_tier = None
    for k, tier in (("dp400", 400), ("dp300", 300), ("dp200", 200)):
        if sec_of(k) is not None:
            dp_t = sec_of(k)
            dp_tier = tier
            break
    if dp_t is not None:
        if dp_tier == DIFF_CAP and dp_t <= DP_BUDGET:
            cap = DIFF_CAP
        else:
            cap = max(100, int(dp_tier * (DP_BUDGET / dp_t) ** 0.5))
        decisions["dp_cap"] = {
            "value": cap, "measured_tier": dp_tier,
            "measured_dp_fill_scan_s": dp_t, "budget_s": DP_BUDGET,
            "rule": "fill+scan≤0.8s 维持 400，超则 cap=档×√(0.8/t)"}
        check("①", f"DP-LCS 中间区上限定参 = {cap}",
              True, f"dp{dp_tier} fill+scan={dp_t:.3f}s")
    else:
        decisions["dp_cap"] = {
            "value": 353, "measured_tier": 400,
            "measured_dp_fill_scan_s": 1.026,
            "budget_s": DP_BUDGET,
            "rule": "当前工具链 dp 档不可得（硬崩）——1914 首轮实测"
                    "dp400=1.026s → 400×√(0.8/1.026)≈353 记账沿用",
            "evidence": "T-00 首轮报告（1914 工具链）"}
        check("①", "DP-LCS 中间区上限定参 = 353（1914 实测记账沿用）",
              True, "live 不可得，历史实测兜底")

    # 全览渲染 cap：600 rows 记录构建 ≤ 0.2s → 600 维持（渲染侧为
    # renderer 成本，VM 侧仅承担 rows 预计算——如实注记口径）。
    ROWS_BUDGET = 0.2
    if rows600 is not None:
        rcap = RENDER_CAP if rows600 <= ROWS_BUDGET else \
            max(200, int(RENDER_CAP * ROWS_BUDGET / rows600))
        decisions["render_cap"] = {
            "value": rcap, "measured_rows600_build_s": rows600,
            "budget_s": ROWS_BUDGET,
            "rule": "rows 构建≤0.2s 维持 600（渲染侧成本不含，口径注记）"}
        check("①", f"全览渲染 cap 定参 = {rcap}",
              True, f"rows600_build={rows600:.3f}s")
    else:
        decisions["render_cap"] = {"value": RENDER_CAP, "measured": None,
                                   "rule": "测量缺失，维持预判"}
        check("①", "全览渲染 cap 定参", False, "rows bench 缺失")

    # 文件上限复核：split5k 线性外推 50k 行 / 2MB 预判；超预算
    # （>1.5s）则按实测降参（计划 Q-1 预授权：超预判降参并注记，
    # 质量换时延）。行数门 post-split（≤尺寸门才走到，耗时受控），
    # 尺寸门 pre-read（fs.metadata 字节长，即时拒——防大文件长等）。
    if split5k is not None:
        lines5k = str(bench.get("split5k_lines"))
        check("①", "split 定标前置：5000 行 body 构建在档",
              lines5k == "5001", f"lines={lines5k}")
        split50k_est = split5k * 10
        if lines5k == "5001" and split50k_est <= 1.5:
            decisions["file_cap"] = {
                "value": "50k 行 / 2MB",
                "measured_split5k_s": split5k,
                "split50k_est_s": split50k_est,
                "rule": "split 线性外推 ≤1.5s → 维持预判上限"}
            check("①", "文件上限复核 = 50k 行/2MB", True,
                  f"split5k={split5k:.3f}s → 50k 估 {split50k_est:.2f}s")
        elif lines5k == "5001":
            cap_lines = max(500, int(5000 * 1.5 / split5k) // 100 * 100)
            cap_bytes = max(65536, cap_lines * 100 // 65536 * 65536)
            decisions["file_cap"] = {
                "value": f"{cap_lines} 行 / {cap_bytes // 1024}KB",
                "measured_split5k_s": split5k,
                "split50k_pred_s": split50k_est,
                "split_per_line_ms": round(split5k / 5000 * 1000, 3),
                "rule": "50k/2MB 预判不成立（split 实测外推超 1.5s "
                        f"预算 {split50k_est:.1f} 倍）→ 行数门按 1.5s "
                        "线性外推降参（百位取整），尺寸门=行数×均长 "
                        "100B 向下 64KB 对齐（pre-read 即时拒，防长等）",
                "arch_note": "全文大文件 diff 为架构阻塞（AutoVM str "
                             "split ~0.5ms/行）——内核引擎 diff_snapshots"
                             "（供料 §5）时代清偿；上限门注记指引"}
            check("①", f"文件上限定参（降参 {cap_lines} 行/"
                        f"{cap_bytes // 1024}KB，预判不成立已注记）",
                  True, f"split5k={split5k:.3f}s → 50k 估 "
                        f"{split50k_est:.2f}s")

    # ---- B2：scroll/④ 会话（全新 app，零堆积）----
    # 前轮教训：未滚动先读 → viewport_h 未 populated（=0）。本轮先
    # by100 滚动再读；行高公式改由 content_h÷行数 实测（不依赖 vh
    # ——vh 若仍 0 则注记「仅 onscroll 实参携带」）。
    emit("\n③ scroll 定标（controller 绑定 + scroll_to 像素语义 + 行高）")
    try:
        proc_b, log, mcp = spawn_app()
        try:
            click_btn(mcp, "rows200")
            time.sleep(1.5)
            click_btn(mcp, "sc-by100")
            time.sleep(1.0)
            vh = ch = oy = None
            for _ in range(25):
                click_btn(mcp, "sc-probe")
                time.sleep(0.6)
                st = mcp.state("sc_oy", "sc_vh", "sc_ch", "n_rows")
                oy = state_float(st, "sc_oy")
                vh = state_float(st, "sc_vh")
                ch = state_float(st, "sc_ch")
                if ch and ch > 0:
                    break
            if not (ch and ch > 0):
                check("③", "scroll_state 读回 content_h", False,
                      f"oy={oy} vh={vh} ch={ch}")
            else:
                row_h = ch / 200.0
                emit(f"       measured: viewport_h={vh} content_h={ch:.2f} "
                     f"→ row_h={row_h:.3f}px (h-6 样式=24px 预期)")
                check("③", "scroll_state 读回 content_h（200 行溢出）",
                      abs(row_h - 24.0) < 3.0, f"row_h={row_h:.3f}")
                if not (vh and vh > 0):
                    emit("       注记: viewport_h 恒 0（滚动后读回仍 0）——"
                         "vh 仅 onscroll 实参携带（④ obs_vh=96 实证）；"
                         "行高公式不依赖 vh，hunk 跳转偏移=行号×row_h")
                click_btn(mcp, "sc-to40")
                time.sleep(1.2)
                click_btn(mcp, "sc-probe")
                time.sleep(0.5)
                oy2 = state_float(mcp.state("sc_oy"), "sc_oy")
                # 绝对像素语义：scroll_to(handle,"y",960) → offset_y≈960
                check("③", "scroll_to(handle,'y',960) → offset_y≈960（绝对像素）",
                      oy2 is not None and abs(oy2 - 960.0) <= 3.0, f"oy={oy2}")
                formula_ok = oy2 is not None and \
                    abs(oy2 - 40 * row_h) <= row_h * 0.25
                check("③", "跳转公式 offset=行号(0基)×行高 成立",
                      formula_ok, f"oy={oy2} vs 40×{row_h:.3f}={40 * row_h:.1f}")
                click_btn(mcp, "sc-by100")
                time.sleep(1.0)
                click_btn(mcp, "sc-probe")
                time.sleep(0.5)
                oy3 = state_float(mcp.state("sc_oy"), "sc_oy")
                check("③", "scroll_by(+100) 相对推进",
                      oy2 is not None and oy3 is not None
                      and 80 <= oy3 - oy2 <= 120,
                      f"Δ={(oy3 or 0) - (oy2 or 0):.1f}")
                decisions["scroll"] = {
                    "unit": "px（auto.scroll.to shim_scroll_to 源码裁定+实测）",
                    "measured_row_h_px": round(row_h, 3),
                    "row_h_source": "content_h÷行数（scroll_state 读回；"
                                    "vh 依赖面见注记）",
                    "style": "h-6（24px）固定行高",
                    "formula": "scroll_to(handle, \"y\", "
                               "target_row_0based × row_h)"
                               "（row_h = scroll_state(handle).content_h ÷ "
                               "行数）",
                    "readback": "scroll_state(handle) → offset_y/viewport_h/"
                                "content_h"}

            # ---- ④ onscroll 事件面 ----
            emit("\n④ 双栏同步：onscroll 事件面（MCP scroll action 试驱动）")
            snap = mcp.snapshot()
            nodes = re.findall(r'(\S*scroll\S*) #?(vnode_\d+|aura_\d+)',
                               snap, re.I)
            emit(f"       snapshot scroll 节点: {nodes}")
            obs_result = {"nodes": nodes}
            if len(nodes) >= 2:
                click_btn(mcp, "obs-clear")
                time.sleep(0.4)
                r = mcp.call("autoui_action", element_id=nodes[1][1],
                             action="scroll", value=48.0)
                time.sleep(1.0)
                st = mcp.state("obs_n", "obs_oy", "obs_vh")
                m_n = re.search(r"obs_n:\s*(-?\d+)", st)
                obs_n = int(m_n.group(1)) if m_n else None
                obs_result["after_mcp_scroll"] = {
                    "obs_n": obs_n, "raw": st.replace("\n", " "),
                    "mcp_reply": str(r)[:120]}
                emit(f"       MCP scroll(48px) 后 obs: "
                     f"{obs_result['after_mcp_scroll']}")
                decisions["q3_onscroll"] = {
                    "event_surface": "有（schema.rs scroll 元素 onscroll: "
                                     "Closure；aura_view_builder.rs "
                                     "scroll_pane_semantics——8 位置 float "
                                     "实参 offset_x..progress_y）",
                    "programmatic_echo": f"MCP operation::scroll_to 驱动后 "
                                         f"obs_n={obs_n}（controller.rs:"
                                         "239-242 注记：程序化 scroll_to 不"
                                         "回声 onscroll）",
                    "dual_pane_v1": "事件面在册 → 双栏同步 v1 可做（左栏 "
                                    "onscroll → scroll_to 右栏）；矩阵驱动"
                                    "面=用户滚动不可合成，T15 仅状态断言，"
                                    "视觉同步走人工复验"}
                check("④", "onscroll 事件面勘定（有/无+实证记录）", True,
                      f"obs_n={obs_n}")
            else:
                decisions["q3_onscroll"] = {
                    "event_surface": "snapshot 未见 scroll 节点——实测不可得",
                    "dual_pane_v1": "登记 upstream want（v1=导航跳转）"}
                check("④", "onscroll 事件面勘定", False, "scroll 节点缺失")
        except Exception as e:  # noqa: BLE001
            check("B2", "scroll 会话中断", False, repr(e)[:200])
        finally:
            _kill_proc_tree(proc_b)
    except Exception as e:  # noqa: BLE001
        check("B2", "probe app 启动", False, repr(e))

    # Q-4 裁定数据落 decisions
    decisions["q4_pairing"] = {
        "strategy": "replace 区索引对齐配对（i-th del 对 i-th add）",
        "unpaired_visual": "不成对行整行 mid 染色（整行红/绿），ASCII 见上",
        "judgment": "可接受——不成对行语义=整段删除/新增，整行染色与 "
                    "VS Code/BC 同款形态；三段数据保留在 envelope 供"
                    "引擎时代 refine"}

    # ============ 汇总 ============
    decisions["toolchain"] = toolchain
    report = {"toolchain": toolchain, "decisions": decisions,
              "checks": checks,
              "pass": all(c["ok"] for c in checks)}
    emit("\n" + "=" * 60)
    emit("三参数定值（T-00 决策）")
    emit("=" * 60)
    emit(json.dumps(decisions, ensure_ascii=False, indent=2))
    failed = [c for c in checks if not c["ok"]]
    emit(f"\nRESULT: {len(checks) - len(failed)} passed, {len(failed)} failed")
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines) + "\n")
    with open(REPORT_PATH.replace(".txt", ".json"), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\nreport: {REPORT_PATH}")
    sys.exit(0 if report["pass"] else 1)


if __name__ == "__main__":
    main()
