---
name: wechat-agent-bridge
description: Use the local WeChat File Transfer Assistant bridge as a lightweight control channel while an agent is actively working.
---

# WeChat Agent Bridge Skill

## When To Use

Use this bridge only when the user wants status checks, small interventions, or
completion notifications through the authorized official File Transfer Assistant web
page. Do not use it for group chats, arbitrary contacts, or unattended bot work.

The official page should stay open in the running agent process: on the first tick,
let the user scan the visible QR page, then keep calling `wechat_tick()` in that same
process so the Playwright page session remains available.

## Agent Loop

Import and periodically call the one public operation:

```python
from wechat_agent import wechat_tick

events = wechat_tick({
    "state": "running",
    "task": "short current task description",
    "progress": "short current activity",
})
```

Process returned `request` events as new instructions or interventions according to
the current task context. The bridge deliberately does not classify their meaning.

## State Values

- `idle`: waiting for work.
- `running`: performing work.
- `waiting_user`: blocked pending user information.
- `done`: task lifecycle ended successfully; include concise `result`.
- `error`: task lifecycle ended unsuccessfully; include concise `result`.

Use `notification_id` for independent completed tasks that may have identical text.

## Optional Output

After receiving a request, the bridge has already sent its fixed acknowledgment.
Send a second acknowledgment only when it is helpful:

```python
wechat_tick({
    "state": "running",
    "task": "update plan",
    "outbox": [{
        "id": "confirm-minimal-edit-1",
        "type": "received",
        "text": "我会只给最小修改方案。"
    }],
})
```

Supply stable unique `id` values so repeated ticks do not resend messages.

## Configuration

Change the active symbol or permitted polling mode inside the normal tick call:

```python
wechat_tick({
    "state": "running",
    "task": "configure bridge",
    "config": {"emoji": "🛰️", "check_interval": 3},
})
```

Polling modes are only `3`, `5`, and `10` seconds; other numeric inputs normalize
to those buckets. Configuration persists locally and applies immediately.

## Guardrails

- Address only File Transfer Assistant.
- Ignore non-protocol messages.
- Treat bridge failures as non-fatal to the main task.
- Keep result and progress messages brief because this is a control panel, not a full chat.
- Do not take screenshots, use OCR, or read clipboard contents; the bridge is Python
  Playwright DOM automation with local JSON state and a local browser profile only.
- Drive only the official File Helper web interface; its page may load Tencent-owned
  login and static-resource domains. Do not hook, inject, or reverse-engineer protocols.
- Treat the local browser profile as sensitive login-session data, and keep the host
  agent's normal approval boundaries for instructions received through the bridge.
- For live message validation, run UTF-8 Python module code and never pipe Chinese
  or emoji message literals through a shell whose encoding may alter them.
