# -*- coding: utf-8 -*-
"""Dump every button label in the initial snapshot (closed-menu inventory)."""
import os
import re
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from desktop_mcp import (  # noqa: E402
    AUTO_BIN, PROJECT, McpClient, pick_free_port, wait_for_server,
)


def main():
    mcp_port = pick_free_port()
    mcp_url = f"http://localhost:{mcp_port}/mcp"
    app_log = tempfile.NamedTemporaryFile(
        prefix="probe_btns_", suffix=".log", delete=False, mode="w",
        encoding="utf-8", errors="replace")
    env = {**os.environ, "AUTOUI_MCP_PORT": str(mcp_port)}
    proc = subprocess.Popen(
        [AUTO_BIN, "run", "-r", "vm"],
        cwd=PROJECT, env=env,
        stdout=app_log, stderr=subprocess.STDOUT)
    try:
        if not wait_for_server(mcp_url):
            print("server not up")
            return 1
        mcp = McpClient(mcp_url)
        snap = ""
        for _ in range(15):
            snap = mcp.snapshot()
            if "(rendered)" in snap:
                break
            time.sleep(1)
        pat = re.compile(r'button #(\w+) "([^"]*)"')
        print("== all buttons ==")
        for m in pat.finditer(snap):
            print(f'  {m.group(2)!r}')
        print("== 全选 occurrences ==")
        for i, ln in enumerate(snap.splitlines()):
            if "全选" in ln or "SelectAll" in ln or "CtxMenu" in ln:
                print(f"  {i}: {ln.strip()}")
        return 0
    finally:
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)],
                       capture_output=True)


if __name__ == "__main__":
    sys.exit(main())
