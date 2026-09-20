# -*- coding: utf-8 -*-
"""Find the enclosing fn/impl for a given 1-based line in renderer.rs."""
import io
import re
import sys

PATH = r"D:\autostack\auto-lang\crates\auto-lang\src\ui\iced\renderer.rs"
TARGET = 15797

lines = io.open(PATH, encoding="utf-8", errors="replace").read().splitlines()
for i in range(TARGET - 1, 13000, -1):
    line = lines[i]
    if re.match(r"\s*(pub(\(.*?\))? )?fn ", line):
        print(i + 1, line.strip()[:110])
        indent = len(line) - len(line.lstrip())
        if indent == 0:
            break
    if re.match(r"^impl ", line):
        print(i + 1, line.strip()[:110])
        break
