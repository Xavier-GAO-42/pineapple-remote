# Command: Initialize Pineapple

**Result**: Bridge is installed and WeChat session is authenticated; `wechat_tick()` is ready to call.

## Install

```bash
pip install "wechat-agent-bridge[web]"
```

Requires Python 3.10+. Playwright is included with the `[web]` extra.

## First Login

```python
from wechat_agent import wechat_tick

# First call opens a browser window — scan the QR code once with WeChat mobile
events = wechat_tick({"state": "idle"})
```

The browser profile persists the session. Subsequent calls skip the login step.

## Verify

After login, send `🍍?` from WeChat. A status reply confirms the bridge is running.
