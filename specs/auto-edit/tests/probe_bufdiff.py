#!/usr/bin/env python3
"""PLAN-016 T-00 消费勘定探针（决策件）——diff natives 裸名解析+缓冲区消费形.
PLAN-017 T-00 扩段（③）——probe 装载轨形/live 驱动面四臂勘定.

载具 = tests/probe_bufdiff_app/（vm 轨最小 app：back fsys 形模块裸调
diff_files/diff_dirs/diff_snapshots[9915-9917] + front 双 code_editor
tab-N 键形快照正路径）。三项勘定：

  ① 裸名解析探针：fsys 形模块内裸调三 natives——split 臂 back HTTP
     （df/dd 正路径 envelope 字段族+ctx<=0 钳 3 同形+缺文件/缺目录
     err 形+ds 缺键 err 形[split back 无编辑器=天然缺键臂]）；merged
     臂 MCP（bufdiff 正路径净形 hunks/rows:[]/计数+bufmiss err 形）。
     绑定证明：app 链接运行成功（裸名未注册=Undefined symbol 运行期
     炸）+ 引擎 envelope 字段断言全中。
  ② 缓冲区消费形定案：merged 臂 tab.key 形键（「tab-N」逐字面=产品
     tabs[].key 形态）registry 直读成功 → 候选 (a) 双已开 tab 比较+
     面板序号输入定案（零装载面；v1 跳转=A 侧首位）。旁路形态
     （AUTO_DIFFBUF_A/B→OpenPath×2→跨 Tick 装载等待→compute）按
     011/012 Tick 消费先例设计，矩阵 15.16 承载。
  ③ PLAN-017 T-00 勘定臂（P1-P4）：probe 装载轨形（未实化键否定面/
     隐藏 widget 正面+重装载幂等）+registry 卸载存活（diff 视图开态
     语义前提）+set_text 内容驱动面（live 预览模拟驱动形）——badge
     随件落/降级 want 登记二选一裁定。

用法：cd specs/auto-edit/tests && python probe_bufdiff.py
前置同 desktop_mcp.py（requests、AUTO_BIN 或 PATH 的 auto）。
退出码 = 勘定门（0 = 全 PASS）。
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from desktop_mcp import (  # noqa: E402
    McpClient, wait_for_server, pick_free_port, _kill_proc_tree,
    find_button_by_text, state_str, state_int, state_bool,
)

AUTO_BIN = os.environ.get("AUTO_BIN") or shutil.which("auto") or ""
TESTS = os.path.dirname(os.path.abspath(__file__))
PROBE_APP = os.path.join(TESTS, "probe_bufdiff_app")

REPORT_PATH = os.path.join(TESTS, "probe_bufdiff_report.txt")


def http_env(r):
    """标量返回铁律：端点标量经 JSON 编码交付（可能双层）——解码到 dict。"""
    v = json.loads(r.text)
    if isinstance(v, str):
        v = json.loads(v)
    return v


def state_json(state_text, field):
    """state_str 捕获的是 state 文本原样转义形（\\\" 序列）——先直解，
    败则去 `\\\"` 转义再解（engine envelope 无裸反斜杠内容，安全）。"""
    raw = state_str(state_text, field) or ""
    try:
        return json.loads(raw)
    except Exception:  # noqa: BLE001
        try:
            return json.loads(raw.replace('\\"', '"'))
        except Exception:  # noqa: BLE001
            return {}


def spawn_split(port):
    env = {**os.environ, "AUTO_PROJECT_DIR": TESTS}
    proc = subprocess.Popen(
        [AUTO_BIN, "run", "--server", "vm", "-B", str(port)],
        cwd=PROBE_APP, env=env,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    base = f"http://127.0.0.1:{port}"
    up = False
    for _ in range(40):
        try:
            requests.get(base + "/api/ws_root", timeout=2)
            up = True
            break
        except requests.ConnectionError:
            time.sleep(1)
    if not up:
        _kill_proc_tree(proc)
        raise RuntimeError("split back server did not start")
    return proc, base


def spawn_merged(port):
    env = {**os.environ, "AUTOUI_MCP_PORT": str(port),
           "APPDATA": tempfile.mkdtemp(prefix="p016_probe_")}
    proc = subprocess.Popen(
        [AUTO_BIN, "run", "-r", "vm"],
        cwd=PROBE_APP, env=env,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    url = f"http://127.0.0.1:{port}/mcp"
    assert wait_for_server(url, 30), "merged MCP server never up"
    t = McpClient(url)
    for _ in range(15):
        s = t.snapshot()
        if "(rendered)" in s and s.count("onclick") > 0:
            break
        time.sleep(1)
    time.sleep(1.5)
    return proc, t


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

    # ============ ① split 臂：裸名 df/dd/ds HTTP 面 ============
    emit("\n" + "=" * 60)
    emit("① 裸名解析探针（split 臂 back HTTP：df/dd 正路径+err 形+ctx 钳）")
    emit("=" * 60)
    td = tempfile.mkdtemp(prefix="p016_probe_fx_")
    fa = os.path.join(td, "f.a.txt")
    fb = os.path.join(td, "f.b.txt")
    with open(fa, "w", encoding="utf-8", newline="") as f:
        f.write("alpha\nbeta\ngamma\n")
    with open(fb, "w", encoding="utf-8", newline="") as f:
        f.write("alpha\ndelta\ngamma\n")
    da = os.path.join(td, "dirA")
    db = os.path.join(td, "dirB")
    os.makedirs(os.path.join(da))
    os.makedirs(os.path.join(db))
    with open(os.path.join(da, "same.txt"), "w", encoding="utf-8") as f:
        f.write("s")
    with open(os.path.join(da, "mod.txt"), "w", encoding="utf-8") as f:
        f.write("aaa\n")
    with open(os.path.join(db, "same.txt"), "w", encoding="utf-8") as f:
        f.write("s")
    with open(os.path.join(db, "mod.txt"), "w", encoding="utf-8") as f:
        f.write("bbb\n")
    with open(os.path.join(db, "added.txt"), "w", encoding="utf-8") as f:
        f.write("x")

    port = pick_free_port(9470)
    try:
        proc, base = spawn_split(port)

        # df 正路径：envelope 字段族+已知内容坐标
        r = requests.get(base + "/api/df",
                         params={"path_a": fa, "path_b": fb, "ctx": 3},
                         timeout=30)
        try:
            env = http_env(r)
            # 文件面尾空吸收（契约「尾空元素吸收」）→ 3 行文件 hunk 钳 [0,3)；
            # 快照面（②）尾空行保留 → [0,4)——两面尾行语义差异=上游内部
            # 行为，各按实测真值断言。
            ok = (r.status_code == 200
                  and env.get("hunks") == [{"a1": 0, "a2": 3, "b1": 0, "b2": 3}]
                  and env.get("adds") == 1 and env.get("dels") == 1
                  and env.get("truncated") is False
                  and env.get("degraded") is False
                  and env.get("err") == ""
                  and isinstance(env.get("rows"), list)
                  and len(env["rows"]) == 3)
            check("①", "df 正路径（1 hunk/[0,3)×2/+1/-1/rows=3/零注记）", ok,
                  json.dumps(env, ensure_ascii=False)[:200])
        except Exception as e:  # noqa: BLE001
            check("①", "df 正路径", False, f"decode fail {e!r} {r.text[:120]!r}")

        # ctx<=0 钳 3：ctx=0 与 ctx=3 输出逐字节同形
        r0 = requests.get(base + "/api/df",
                          params={"path_a": fa, "path_b": fb, "ctx": 0},
                          timeout=30)
        r3 = requests.get(base + "/api/df",
                          params={"path_a": fa, "path_b": fb, "ctx": 3},
                          timeout=30)
        check("①", "ctx=0 钳 3（与 ctx=3 输出逐字节同形）",
              r0.text == r3.text, f"len {len(r0.text)} vs {len(r3.text)}")

        # df 缺文件 err 形
        r = requests.get(base + "/api/df",
                         params={"path_a": os.path.join(td, "nope.txt"),
                                 "path_b": fb, "ctx": 3}, timeout=30)
        try:
            env = http_env(r)
            check("①", "df 缺文件 err 形（文件不存在+空 hunks）",
                  "文件不存在" in env.get("err", "") and env.get("hunks") == [],
                  repr(env.get("err"))[:100])
        except Exception as e:  # noqa: BLE001
            check("①", "df 缺文件 err 形", False, repr(e))

        # dd 正路径：counts 五态
        r = requests.get(base + "/api/dd",
                         params={"path_a": da, "path_b": db}, timeout=30)
        try:
            env = http_env(r)
            c = env.get("counts", {})
            ok = (env.get("err") == "" and c.get("same") == 1
                  and c.get("added") == 1 and c.get("deleted") == 0
                  and c.get("modified") == 1 and c.get("binary") == 0
                  and isinstance(env.get("entries"), list)
                  and len(env["entries"]) == 3)
            check("①", "dd 正路径（counts 1/1/0/1/0+entries 3）", ok,
                  json.dumps(env, ensure_ascii=False)[:200])
        except Exception as e:  # noqa: BLE001
            check("①", "dd 正路径", False, f"decode fail {e!r} {r.text[:120]!r}")

        # dd 缺目录 err 形
        r = requests.get(base + "/api/dd",
                         params={"path_a": os.path.join(td, "nodir"),
                                 "path_b": db}, timeout=30)
        try:
            env = http_env(r)
            check("①", "dd 缺目录 err 形（目录不存在）",
                  "目录不存在" in env.get("err", ""),
                  repr(env.get("err"))[:100])
        except Exception as e:  # noqa: BLE001
            check("①", "dd 缺目录 err 形", False, repr(e))

        # ds split 臂：back 进程无编辑器注册=天然缺键（err 形=绑定证明面：
        # 未定义符号会在此时报 Undefined symbol 而非 err envelope）
        r = requests.get(base + "/api/ds",
                         params={"key_a": "tab-1", "key_b": "tab-2"},
                         timeout=30)
        try:
            env = http_env(r)
            check("①", "ds split 臂缺键 err 形（编辑器不存在，非 Undefined）",
                  "编辑器不存在" in env.get("err", "")
                  and env.get("hunks") == [] and env.get("rows") == [],
                  repr(env.get("err"))[:100])
        except Exception as e:  # noqa: BLE001
            check("①", "ds split 臂", False, f"decode fail {e!r} {r.text[:120]!r}")
    finally:
        try:
            _kill_proc_tree(proc)
        except Exception:  # noqa: BLE001
            pass

    # ============ ② merged 臂：缓冲区消费形（tab.key registry 直读） ============
    emit("\n" + "=" * 60)
    emit("② 缓冲区消费形勘定（merged 臂 MCP：tab-N 键 registry 直读正路径）")
    emit("=" * 60)
    port_m = pick_free_port()
    try:
        proc_m, t = spawn_merged(port_m)
        # 编辑器内容就绪竞态垫（首拍点击可能早于 code_editor 内容应用
        # ——双空快照=0 hunk 假阴性；重试至 hunks 非空或 err 非空）。
        env = {}
        ok_click = False
        for _ in range(12):
            btn = find_button_by_text(t.snapshot(), "bufdiff")
            if not btn:
                time.sleep(0.5)
                continue
            t.click(btn)
            ok_click = True
            time.sleep(1.0)
            st = t.state("snap_out", "runs", "ka", "kb")
            env = state_json(st, "snap_out")
            if env.get("hunks") or env.get("err"):
                break
            time.sleep(0.5)
        raw = json.dumps(env, ensure_ascii=False)
        ok = (ok_click
              and env.get("hunks") == [{"a1": 0, "a2": 4, "b1": 0, "b2": 4}]
              and env.get("rows") == []
              and env.get("adds") == 1 and env.get("dels") == 1
              and env.get("truncated") is False
              and env.get("degraded") is False
              and env.get("err") == "")
        check("②", "bufdiff 正路径（净形 rows:[]/1 hunk/+1/-1/tab-N 键直读）",
              ok, raw[:200])
        btn2 = find_button_by_text(t.snapshot(), "bufmiss")
        if btn2:
            t.click(btn2)
        time.sleep(1.5)
        st2 = t.state("snap_miss", "runs")
        env2 = state_json(st2, "snap_miss")
        raw2 = json.dumps(env2, ensure_ascii=False)
        check("②", "bufmiss 缺键 err 形（编辑器不存在: tab-nope）",
              "编辑器不存在" in env2.get("err", "")
              and "tab-nope" in env2.get("err", ""),
              raw2[:160])
        decisions["buf_consumption_form"] = {
            "form": "(a) 双已开 tab 比较+面板双 tab 序号输入",
            "evidence": "merged 臂 tab.key 形键（tab-1/tab-2 逐字面）registry "
                        "直读出净形 envelope——键语义=tab.key 直接可用（VM 轨 "
                        "normalize_payload_key 对齐）；零装载面（已开 tab 即"
                        "快照源）；v1 跳转=A 侧首位（set_cursor(key, a1, 0)"
                        "——014 先例 1 基→0 基换算）",
            "bypass": "AUTO_DIFFBUF_A/B→OpenPath×2→跨 Tick 装载等待"
                      "（tabs[].loaded 双真门）→DiffBufCompute（011/012 "
                      "Tick 消费先例——load_key 单槽协议：B 先装、A 经 "
                      "TabActivate 懒装载轮转）",
            "probe": "①② 双臂全绿=裸名绑定 native + 消费形成立",
        }
    finally:
        try:
            _kill_proc_tree(proc_m)
        except Exception:  # noqa: BLE001
            pass

    # ============ ③ PLAN-017 T-00 勘定臂：probe 装载轨形/live 驱动面 ============
    # 四臂（载具=probe_bufdiff_app PLAN-017 扩段，AUTO_PROBE_FILE 供料）：
    #   P1 probe-never —— 未实化键 load_file+快照（badge 轨形否定面）
    #   P2 unmount     —— widget 卸载后快照存活（diff 视图开态 registry 语义）
    #   P3 probe-a     —— 隐藏 widget（h-0）装载轨形+重装载幂等（badge 正面）
    #   P4 set_text    —— 内容驱动→计数变化（live 预览模拟驱动形）
    emit("\n" + "=" * 60)
    emit("③ PLAN-017 T-00 勘定（probe 装载轨形/卸载存活/隐藏 widget/live 驱动）")
    emit("=" * 60)
    port_p = pick_free_port()
    try:
        pfx = tempfile.mkdtemp(prefix="p017_probe_fx_")
        pfa = os.path.join(pfx, "probe.a.txt")
        with open(pfa, "w", encoding="utf-8", newline="") as f:
            f.write("alpha\nOMEGA\ngamma\n")
        env_p = {**os.environ, "AUTOUI_MCP_PORT": str(port_p),
                 "APPDATA": tempfile.mkdtemp(prefix="p017_probe_"),
                 "AUTO_PROBE_FILE": pfa}
        proc_p = subprocess.Popen(
            [AUTO_BIN, "run", "-r", "vm"],
            cwd=PROBE_APP, env=env_p,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        assert wait_for_server(f"http://127.0.0.1:{port_p}/mcp", 30), \
            "③ merged MCP server never up"
        tp = McpClient(f"http://127.0.0.1:{port_p}/mcp")
        for _ in range(15):
            s = tp.snapshot()
            if "(rendered)" in s and s.count("onclick") > 0:
                break
            time.sleep(1)
        time.sleep(1.5)

        def click_and_state(label, fields, tries=6):
            """按钮点击+state 轮询（内容应用竞态垫——② 同款卫生）。"""
            for _ in range(tries):
                btn = find_button_by_text(tp.snapshot(), label)
                if not btn:
                    time.sleep(0.5)
                    continue
                tp.click(btn)
                time.sleep(1.0)
                st = tp.state(*fields)
                if all((state_str(st, f) or "") != "" for f in fields):
                    return st
                time.sleep(0.5)
            return tp.state(*fields)

        # P1: 未实化键装载（否定面勘定：err 形/load -1=轨形不成立）
        st1 = click_and_state("probe-never", ["snap_never", "load_ret"])
        env1 = state_json(st1, "snap_never")
        ret1 = state_int(st1, "load_ret")
        ok1 = ("编辑器不存在" in env1.get("err", "")) or ret1 < 0
        check("③", "P1 未实化键装载=否定面（err 形或 load 负值）", ok1,
              f"ret={ret1} env={json.dumps(env1, ensure_ascii=False)[:120]}")

        # P2: 卸载存活勘定（先 hide1 卸载 tab-1，再快照）
        b_hide = find_button_by_text(tp.snapshot(), "hide1")
        if b_hide:
            tp.click(b_hide)
            time.sleep(1.0)
        st2 = click_and_state("probe-unmount", ["snap_unmount"])
        env2 = state_json(st2, "snap_unmount")
        alive = env2.get("err") == "" and env2.get("hunks") is not None
        check("③", "P2 卸载后快照存活（registry 卸载语义勘定）", alive,
              json.dumps(env2, ensure_ascii=False)[:160])

        # P3: 隐藏 widget 装载轨形（正面勘定）+P3b 重装载幂等
        #（期望形注：probe.a 文件 3 行装载进 buffer 后按快照面语义参与
        # 对打——①段实勘「快照面尾空行保留」→ 3 行内容=4 行域 [0,4)；
        # ret=全字节数 18=装载成功证明。）
        st3 = click_and_state("probe-hidden", ["snap_hidden", "load_ret"])
        env3 = state_json(st3, "snap_hidden")
        ret3 = state_int(st3, "load_ret")
        ok3 = (env3.get("err") == ""
               and env3.get("hunks") == [{"a1": 0, "a2": 4, "b1": 0, "b2": 4}]
               and env3.get("adds") == 1 and env3.get("dels") == 1
               and env3.get("rows") == [] and ret3 == 18)
        check("③", "P3 隐藏 widget 装载轨形（净形 1 hunk/+1/-1+ret 全字节）", ok3,
              f"ret={ret3} env={json.dumps(env3, ensure_ascii=False)[:160]}")
        st3b = click_and_state("probe-reload", ["snap_reload", "load_ret"])
        env3b = state_json(st3b, "snap_reload")
        ok3b = (env3b.get("err") == "" and env3b.get("adds") == 1
                and env3b.get("dels") == 1)
        check("③", "P3b 重装载幂等（probe 键生命周期可刷新）", ok3b,
              json.dumps(env3b, ensure_ascii=False)[:160])

        # P4: set_text 内容驱动（live 驱动面：tab-2 改内容→计数变化；
        # 期望形=实测真值：beta 行对齐后 gamma→OMEGA 改+尾行增=B 侧
        # [0,5) adds=1 dels=0——对 baseline（[0,4)×2 +1/-1）计数已变。）
        st4 = click_and_state("probe-live", ["snap_live"])
        env4 = state_json(st4, "snap_live")
        ok4 = (env4.get("err") == "" and env4.get("adds") == 1
               and env4.get("dels") == 0
               and env4.get("hunks") and env4["hunks"][0].get("b2") == 5)
        check("③", "P4 set_text 内容驱动（快照计数随内容变化）", ok4,
              json.dumps(env4, ensure_ascii=False)[:160])

        # 决策产物：badge 轨形二选一（T-00① 裁定）
        badge_form = ("probe-hidden-widget 轨形成立——badge 随件落"
                      if ok3 and ok3b
                      else "probe 轨形不成立——降级 dirty 提示+want 登记")
        decisions["probe_load_track"] = {
            "never_mounted_load": "fail(err/-1)" if ok1 else "unexpected-success",
            "unmount_survival": "alive" if alive else "registry-dropped",
            "hidden_widget_load": "ok" if ok3 else "fail",
            "reload_idempotent": "ok" if ok3b else "fail",
            "set_text_drive": "ok" if ok4 else "fail",
            "badge_form": badge_form,
        }
    finally:
        try:
            _kill_proc_tree(proc_p)
        except Exception:  # noqa: BLE001
            pass

    # ============ 汇总 ============
    decisions["toolchain"] = toolchain
    report = {"toolchain": toolchain, "decisions": decisions,
              "checks": checks,
              "pass": all(c["ok"] for c in checks)}
    emit("\n决策产物（T-00）")
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
