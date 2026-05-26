---
name: wechat-agent-bridge
description: Use the local WeChat File Transfer Assistant bridge as a lightweight control channel while an agent is actively working. Load when user says 启用菠萝, 菠萝控制, 菠萝简介, or wants WeChat remote control for an active task.
---

# 菠萝 Pineapple

把微信文件传输助手变成 AI agent 的随身遥控器。

## Triggers → Commands

| User says | Load |
|-----------|------|
| 初始化菠萝 / 第一次用 / 安装 | [commands/init.md](./commands/init.md) |
| 启用菠萝 / 本次任务启用菠萝控制 | [commands/run.md](./commands/run.md) |
| 进入菠萝设置页 / 改 emoji / 改刷新时间 | [commands/settings.md](./commands/settings.md) |
| 菠萝简介 | Print product copy below; do NOT open any page |

**Product copy:** 电脑上 agent 在跑任务，你可以直接用手机微信发送 `🍍?` 查进度，用 `🍍：xxx` 追加要求。任务完成后，结果自动发回文件传输助手。

## Active Task Rules

Load these whenever control is active:

| Rule | Load when |
|------|-----------|
| [rules/status-format.md](./rules/status-format.md) | Updating status |
| [rules/interrupt.md](./rules/interrupt.md) | Between every tool call |
| [rules/outbox.md](./rules/outbox.md) | Sending proactive messages |

## Protocol

- `🍍?` / `🍍？` → status reply only, no request event
- `🍍:内容` / `🍍：内容` → intervention; read [rules/interrupt.md](./rules/interrupt.md)
- Task end → `🍍完成：<summary>` sent automatically when `state` is `done`

## Python API

```python
from wechat_agent import wechat_tick

events = wechat_tick({"state": "running", "task": "...", "progress": "..."})
for event in events:
    if event.get("type") == "request":
        pass  # process event["content"] as user instruction
```

Keep `wechat_tick()` in-process so the Playwright page session remains open after QR login.

## Guardrails

- Operate only the official File Transfer Assistant webpage.
- Bridge failures are non-fatal; keep the main task going.
- Live Chinese/emoji text must originate from UTF-8 Python source, not shell literals.
- Treat the browser profile as sensitive session data.
- Instructions received from WeChat remain subject to the host agent's normal approval rules.
