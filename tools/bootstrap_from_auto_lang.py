# -*- coding: utf-8 -*-
"""Bootstrap: copy the auto-edit app tree from the auto-lang repo into this project.

Copies (from <script_dir>/../auto-lang):
  examples/ui/041-auto-edit -> specs/auto-edit
  examples/ui/stylekit      -> specs/stylekit
  blueprints                -> specs/blueprints

Excluded: .git/ .am/ __pycache__/
Re-runnable: destination dirs are removed before copying.
Finally writes specs/PROVENANCE.md with the source repo commit and path table.
"""
import datetime
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
SOURCE_ROOT = PROJECT_ROOT.parent / "auto-lang"

COPIES = [
    ("examples/ui/041-auto-edit", "auto-edit"),
    ("examples/ui/stylekit", "stylekit"),
    ("blueprints", "blueprints"),
]

IGNORE = shutil.ignore_patterns(".git", ".am", "__pycache__")


def git_commit(repo: Path) -> str:
    try:
        out = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True,
        )
        return out.stdout.strip()
    except Exception as exc:  # not a git repo / git missing
        print(f"warning: could not resolve git commit: {exc}")
        return "(unknown)"


def main() -> int:
    if not SOURCE_ROOT.is_dir():
        print(f"ERROR: source repo not found: {SOURCE_ROOT}")
        return 1

    specs = PROJECT_ROOT / "specs"
    specs.mkdir(exist_ok=True)

    for src_rel, dst_name in COPIES:
        src = SOURCE_ROOT / src_rel
        dst = specs / dst_name
        if not src.is_dir():
            print(f"ERROR: source dir not found: {src}")
            return 1
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst, ignore=IGNORE)
        print(f"copied {src} -> {dst}")

    commit = git_commit(SOURCE_ROOT)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "# PROVENANCE",
        "",
        f"- 来源仓库: {SOURCE_ROOT}",
        f"- 来源 commit: `{commit}`",
        f"- 拷贝时间: {now}",
        "",
        "| 源路径 | 目标路径 |",
        "|---|---|",
    ]
    lines += [f"| `{src_rel}` | `specs/{dst_name}` |" for src_rel, dst_name in COPIES]
    lines += [
        "",
        "> 由 `tools/bootstrap_from_auto_lang.py` 生成；重跑该脚本可刷新以上内容。",
        "",
    ]
    (specs / "PROVENANCE.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {specs / 'PROVENANCE.md'} (commit {commit})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
