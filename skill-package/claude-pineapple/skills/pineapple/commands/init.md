# Command: Initialize Pineapple (First Time)

**Result**: Bridge tool is installed to `~/.pineapple/bridge-tool/`; ready to start watch mode.

## Bootstrap

Run the discover-and-plan step first (read-only, nothing is written):

```powershell
<tool-python> scripts/bootstrap.py --plan
```

Review the output, then confirm to install:

```powershell
<tool-python> scripts/bootstrap.py --adopt-or-install
```

`<tool-python>` is the Python 3.10+ executable (e.g., `py` on Windows). Bootstrap returns JSON:

```json
{"status": "ready", "tool_home": "~/.pineapple/bridge-tool", "python": "<bridge-python>"}
```

Save the `python` value — use it for all subsequent Pineapple commands.

## Install Web Driver

```powershell
<bridge-python> -m playwright install chromium
```

Only needed once. Skippable if browser is already present.

## Verify

Run the bridge once in idle mode:

```powershell
<bridge-python> -m wechat_agent.wechat_tick --backend web --watch --status-json status-idle.json
```

A browser window opens. Scan the QR code with WeChat mobile. Send `🍍?` — a status reply confirms the bridge is working. Press Ctrl+C to stop.
