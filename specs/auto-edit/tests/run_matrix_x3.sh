#!/usr/bin/env bash
# PLAN-022 T-06: 供③ P716-D1 销账多跑——L0 全矩阵 ×3（021 谱 131/0 基线
# 复现；AUTOUI_MCP_PORT 动态避让 924x 带为脚本内建 pick_free_port 语义）。
# 用法：bash tests/run_matrix_x3.sh   （AUTO_BIN 指 ≥716 工具链）
set -u
cd "$(dirname "$0")"
for i in 1 2 3; do
  echo "=== matrix run $i/3 $(date +%H:%M:%S) ==="
  AUTO_BIN="${AUTO_BIN:-auto}" python desktop_mcp.py \
    > "matrix-p022-run${i}.txt" 2>&1
  echo "run $i exit=$?"
  tail -3 "matrix-p022-run${i}.txt"
done
echo "=== x3 done $(date +%H:%M:%S) ==="
