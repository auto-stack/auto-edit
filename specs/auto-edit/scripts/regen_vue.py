#!/usr/bin/env python3
"""regen_vue.py — PLAN-003 T-04 vue 轨一键再生成 + 补件链（jade-edit
scripts/regen-vue.mjs 同型先例）。

vue 轨生成命令固定 `--lenient`（T-00 P-1/P-2：S001 schema 漂移 = 上游
aura schema 未吸收 PLAN-630 menubar 族 props 的债，非本仓可修）。
生成器已知缺口（本脚本逐项补，补件全部幂等）：

  1. vm 宿主内建裸标识符（dialog/console/code_editor_*/Env/Process/
     file_basename）无类型声明 → src/lib/natives.d.ts（TS2304 面；
     运行期无实现 = vue 首版登记限制，见 README vue 节）。
  2. composable 文件内 store.X() 自调无别名 → 文件尾追加 store 别名
     （绑定模块内 handler const；App.vue 侧自带 reactive(useEditorStore())）。
  3. tree_util.toggle_id bp 函数在组件文件被内联、store 文件残留裸调
     → store 文件尾追加同体内联。
  4. int -1 模型初值被发射为 ref<number>(null) → 改回 -1。
  5. EditorCtx(x,y) 双参 handler 签名误发 (i) → 签名对齐（App.vue）。
  6. button variant "text"（vm 专属扁平样式）不在 shadcn cva 联合 →
     ui/button 补 text variant。
  7. Select Anything overlay 引 ../auto-sources 与 import.meta.env →
     stub + env.d.ts（PLAN-646 jade 同款补件）。

用法（cwd = specs/auto-edit）：
  python scripts/regen_vue.py            # 生成 + 补件
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

NATIVES_DTS = """\
// natives.d.ts — PLAN-003 T-04 补件（vue 轨类型声明层；由 scripts/regen_vue.py 重放）。
// vm 轨宿主内建在 vue 生成面为裸标识符发射（无声明 → vue-tsc TS2304，
// T-00 P-6 勘定）；本文件补类型声明使构建绿。运行期无实现——vue 首版 =
// 构建绿 + 生成即展示，功能环缺口登记 README vue 限制节。
declare function dialog_open(filter: string): string
declare function dialog_save(default_name: string): string
declare function console_log(msg: string): void
declare function console_lines(): string
declare function console_clear(): void
declare function file_basename(p: string): string
declare function code_editor_text(key: string): string
declare function code_editor_set_text(key: string, text: string): void
declare function code_editor_cursor_line(key: string): number
declare function code_editor_cursor_col(key: string): number
declare function code_editor_selection_len(key: string): number
declare function code_editor_select_all(key: string): void
declare function code_editor_cut(key: string): void
declare function code_editor_copy(key: string): void
declare function code_editor_paste(key: string): void
declare function code_editor_undo(key: string): void
declare function code_editor_redo(key: string): void
declare function code_editor_fold_toggle(key: string, line: number): void
declare function code_editor_fold_hidden_count(key: string): number
declare const Env: { get(name: string): string }
declare const Process: { exit(code: number): void }
"""

STORE_ALIAS = """\
    // PLAN-003 T-04 补件：store 自调别名（生成器在 composable 内发射
    // store.X() 自调——vm 轨 store 语义；别名绑定函数内 handler const，
    // vue 轨运行期同语义。App.vue 侧自带 reactive(useEditorStore())）。
    const store = { SyncCursor, RemoveAt, TabActivate, CloseRequest }
    return {
"""

TOGGLE_ID = """
// PLAN-003 T-04 补件：tree_util.toggle_id 内联（bp 函数生成器只在组件
// 文件内联，store 文件残留裸调；与 FileTree.vue 内联体一致）。
function toggle_id(list: any, id: any): any {
  let out: any[] = [];
  let found: boolean = false;
  let i: number = 0;
  while (i < list.length) {
    if (list[i] == id) { found = true } else { out.push(list[i]) }
    i = i + 1;
  }
  if (!found) { out.push(id) }
  return out;
}
"""

AUTO_SOURCES = ("// auto-sources.ts — stub（gen-only 构建流；`auto run` vue 流会重写真值）\n"
                "export const AUTO_SOURCES: Record<string, string> = {}\n")
ENV_DTS = "/// <reference types=\"vite/client\" />\n"

BUTTON_TEXT_VARIANT = ('        text: "hover:bg-accent/50 hover:text-accent-foreground",\n')


def run(cmd, **kw):
    print(f"[regen-vue] $ {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=ROOT if kw.pop("cwd_root", True) else VUE, **kw).returncode


def patch_file(path, repls, append=None, write=None):
    full = os.path.join(VUE, path)
    if write is not None:
        with open(full, "w", encoding="utf-8", newline="\n") as f:
            f.write(write)
        print(f"[regen-vue] 补件：{path}（重写）")
        return
    with open(full, encoding="utf-8") as f:
        s = f.read()
    for old, new in repls:
        if new in s:  # 幂等
            continue
        if old not in s:
            print(f"[regen-vue] ⚠ 锚点缺失 {path}: {old[:60]!r}")
            continue
        s = s.replace(old, new)
    if append and append not in s:
        s += append
    with open(full, "w", encoding="utf-8", newline="\n") as f:
        f.write(s)
    print(f"[regen-vue] 补件：{path}")


def main():
    rc = run([which("auto"), "build", "--gen-only", "--lenient", "-r", "vue"])
    if rc != 0:
        sys.exit(rc)

    # 1. natives 声明层（重写式，幂等）
    patch_file(os.path.join("src", "lib", "natives.d.ts"), [], write=NATIVES_DTS)
    # 2. store 自调别名（composable 函数体内、return 前）+ 3. toggle_id
    #    内联 + 4. null→-1
    patch_file(os.path.join("src", "stores", "useEditorStore.ts"),
               [("ref<number>(null)", "ref<number>(-1)"),
                ("    return {\n", STORE_ALIAS)],
               append=TOGGLE_ID)
    # 5. EditorCtx 双参签名对齐（App.vue）+ contextmenu 事件坐标实参
    patch_file(os.path.join("src", "App.vue"),
               [("function EditorCtx(i: any): void {", "function EditorCtx(x: any, y: any): void {"),
                ('@contextmenu="EditorCtx(i)"', '@contextmenu="EditorCtx($event.clientX, $event.clientY)"')])
    # 5b. 多段插值「行:列」vue 发射残缺（缺首 {{ 尾 }}——vm 侧 Plan 626
    #     已修扁平化，vue 侧仍破；两段各补界符）
    patch_file(os.path.join("src", "components", "StatusBar.vue"),
               [("store.line }}:{{ store.col", "{{ store.line }}:{{ store.col }}")])
    # 6. button text variant
    patch_file(os.path.join("src", "components", "ui", "button", "index.ts"),
               [("        default:", BUTTON_TEXT_VARIANT + "        default:")])
    # 7. auto-sources stub + env.d.ts（jade 同款）
    patch_file(os.path.join("src", "auto-sources.ts"), [], write=AUTO_SOURCES)
    patch_file(os.path.join("src", "env.d.ts"), [], write=ENV_DTS)

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
