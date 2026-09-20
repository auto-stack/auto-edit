# -*- coding: utf-8 -*-
"""Probe: does the menubar popover open, and does it stay open?

Starts the app, clicks the 视图 menubar trigger, then snapshots at several
delays and reports whether menu items are visible in each snapshot.
"""
import os
import re
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from desktop_mcp import (  # noqa: E402
    AUTO_BIN, PROJECT, McpClient, find_button_by_text, pick_free_port,
    wait_for_server,
)

MCP_PORT_DEFAULT = 9247


def main():
    mcp_port = pick_free_port()
    mcp_url = f"http://localhost:{mcp_port}/mcp"
    print(f"probe port: {mcp_port}")

    app_log = tempfile.NamedTemporaryFile(
        prefix="probe_menu_", suffix=".log", delete=False, mode="w",
        encoding="utf-8", errors="replace")
    env = {**os.environ, "AUTOUI_MCP_PORT": str(mcp_port)}
    proc = subprocess.Popen(
        [AUTO_BIN, "run", "-r", "vm"],
        cwd=PROJECT, env=env,
        stdout=app_log, stderr=subprocess.STDOUT)
    print(f"app log: {app_log.name}")

    try:
        if not wait_for_server(mcp_url):
            print("ERROR: server not up in 30s")
            return 1
        mcp = McpClient(mcp_url)

        # wait for rendered snapshot
        for _ in range(15):
            snap = mcp.snapshot()
            if "(rendered)" in snap:
                break
            time.sleep(1)
        print("rendered:", "(rendered)" in snap)

        # find the 视图 trigger
        btn = find_button_by_text(snap, "视图")
        print("视图 trigger id:", btn)
        if btn is None:
            # dump all menubar-ish lines to see what triggers look like
            for line in snap.splitlines():
                if "menubar" in line or "文件" in line:
                    print("  |", line.strip())
            return 1

        mcp.click(btn)
        for delay in (0.0, 0.3, 1.0, 3.0):
            time.sleep(delay)
            s = mcp.snapshot()
            marks = {
                "切换 Console": "切换 Console" in s,
                "切换 Tab": "切换 Tab" in s,
                "折叠切换": "折叠切换" in s,
                "新建": "新建" in s,
            }
            print(f"t+{delay:.1f}s -> {marks}")
            if not any(marks.values()):
                # show the menubar area for diagnosis
                idx = s.find("menubar")
                print("  menubar region:", s[idx:idx + 600].replace("\n", " | ") if idx >= 0 else "(no menubar text)")
        return 0
    finally:
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)],
                       capture_output=True)


if __name__ == "__main__":
    sys.exit(main())
