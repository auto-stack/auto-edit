# -*- coding: utf-8 -*-
"""Disambiguate where 新建 appears in the snapshot: toolbar button vs menubar-content."""
import os
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
        prefix="probe_ctx_", suffix=".log", delete=False, mode="w",
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
        # print every line mentioning 新建 or menubar, with a 1-line lookbehind
        lines = snap.splitlines()
        for i, ln in enumerate(lines):
            if "新建" in ln or "menubar" in ln or "toolbar" in ln:
                print(f"--- ctx line {i} ---")
                for j in range(max(0, i - 1), min(len(lines), i + 2)):
                    print(f"  {j}: {lines[j]}")
        return 0
    finally:
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)],
                       capture_output=True)


if __name__ == "__main__":
    sys.exit(main())
