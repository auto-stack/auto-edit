#!/usr/bin/env python3
"""regen_vue.py — vue 轨一键再生成（裸生成 wrapper）。

七类补件链已退役（2026-09-21，上游 auto-lang PLAN-671 r1+Phase 2 全周期
delivered——merge 后工具链 v0.4.2-1652+）：natives 声明（含对象形态
Env/Process 索引签名 + __vmOnly 抛错桩）/store 自调别名/toggle_id 内联/
int 负初值/EditorCtx 双参签名/button text variant/auto-sources+env.d.ts
均由生成器自备，strict（无 --lenient）裸产出即可构建。

补件链历史形态（PLAN-003 T-04 起，PLAN-004 F-1 增 1b 与⑥在场守卫）见
git 历史（fdc92aa 及此前）；旧工具链（<671 merge）不再支持。

vue 轨运行期内建缺口维持 README 登记限制（natives 层为抛错桩非实现：
dialog_open/Env.get/Process.exit 等——构建绿 ≠ 运行期可用）。

用法（cwd = specs/auto-edit）：
  python scripts/regen_vue.py            # 生成（strict）
  python scripts/regen_vue.py --install  # + pnpm install
  python scripts/regen_vue.py --build    # + pnpm build（含 install 检查）
"""
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # specs/auto-edit
VUE = os.path.join(ROOT, "gen", "front", "vue")


def which(name):
    # Windows：pnpm 是 .cmd 垫片，CreateProcess 的 PATH 搜索不解析——
    # shutil.which 取全路径。
    p = shutil.which(name)
    if p is None:
        sys.exit(f"[regen-vue] ERROR: {name} not found on PATH")
    return p


def run(cmd, **kw):
    print(f"[regen-vue] $ {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=ROOT if kw.pop("cwd_root", True) else VUE, **kw).returncode


def main():
    rc = run([which("auto"), "build", "--gen-only", "-r", "vue"])
    if rc != 0:
        sys.exit(rc)

    # PLAN-005 唯一保留件（非退役补件复活）：生成器硬编码 print→console.log
    # （ts_adapter.rs），与本 app store 名为 console 的 state 字段（Ref）遮蔽
    # 成 TS2339——上游未吸收（供料包 §9 登记），单行外科缓解：store 生成物
    # 内改写为 globalThis.console.log。幂等（改写后锚点不再命中）。
    store = os.path.join(VUE, "src", "stores", "useEditorStore.ts")
    if os.path.exists(store):
        with open(store, encoding="utf-8") as f:
            s = f.read()
        if "console.log(" in s and "globalThis.console.log(" not in s:
            with open(store, "w", encoding="utf-8", newline="\n") as f:
                f.write(s.replace("console.log(", "globalThis.console.log("))
            print("[regen-vue] print 遮蔽缓解：console.log → globalThis.console.log（store）")

    if "--install" in sys.argv or "--build" in sys.argv:
        rc = run([which("pnpm"), "install"], cwd_root=False)
        if rc != 0:
            sys.exit(rc)
    if "--build" in sys.argv:
        rc = run([which("pnpm"), "build"], cwd_root=False)
        if rc != 0:
            sys.exit(rc)
    print("[regen-vue] done")


if __name__ == "__main__":
    main()
