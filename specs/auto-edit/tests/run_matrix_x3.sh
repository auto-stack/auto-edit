#!/usr/bin/env bash
# PLAN-022 T-06: 供③ P716-D1 销账多跑——L0 全矩阵 ×3（021 谱 131/0 基线
# 复现）。P716-D1 销账处方落实：主实例 AUTOUI_MCP_PORT 钉位绕开 924x
# TOCTOU 竞态带（desktop_mcp.py 主实例钉位臂承接——本脚本逐跑拣 93xx
# 带空位钉入）。
# 用法：bash tests/run_matrix_x3.sh   （AUTO_BIN 指 ≥716 工具链）
set -u
cd "$(dirname "$0")"
for i in 1 2 3; do
  PORT=$((9320 + RANDOM % 60))
  echo "=== matrix run $i/3 port=$PORT $(date +%H:%M:%S) ==="
  AUTOUI_MCP_PORT="$PORT" AUTO_BIN="${AUTO_BIN:-auto}" python desktop_mcp.py \
    > "matrix-p022-run${i}.txt" 2>&1
  echo "run $i exit=$?"
  tail -3 "matrix-p022-run${i}.txt"
done
echo "=== x3 done $(date +%H:%M:%S) ==="
