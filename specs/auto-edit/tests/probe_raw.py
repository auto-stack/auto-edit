# -*- coding: utf-8 -*-
"""Print the RAW autoui_action response for a menubar trigger press."""
import os
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from desktop_mcp import (  # noqa: E402
    AUTO_BIN, PROJECT, McpClient, find_button_by_text, pick_free_port,
    wait_for_server,
)


def main():
    mcp_port = pick_free_port()
    mcp_url = f"http://localhost:{mcp_port}/mcp"
    app_log = tempfile.NamedTemporaryFile(
        prefix="probe_raw_", suffix=".log", delete=False, mode="w",
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
        for label in ("视图", "编辑", "文件"):
            btn = find_button_by_text(snap, label)
            raw = mcp.call("autoui_action", element_id=btn, action="press")
            print(f"press {label} ({btn}) -> {raw!r}")
        # toolbar ActNew for contrast (known-good user handler)
        tb = find_button_by_text(snap, "file-plus新建")
        if tb:
            raw = mcp.call("autoui_action", element_id=tb, action="press")
            print(f"press toolbar 新建 ({tb}) -> {raw!r}")
        return 0
    finally:
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)],
                       capture_output=True)


if __name__ == "__main__":
    sys.exit(main())
