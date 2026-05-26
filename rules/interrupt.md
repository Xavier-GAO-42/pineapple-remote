# Rule: Interrupt Detection

**Authority**: This file. No other source overrides interrupt handling.

## Mechanism

When a user sends `🍍：xxx`, the bridge:
1. Sends `🍍收到：AI正在处理中。` to WeChat automatically
2. Writes `interrupt.flag` in the storage directory
3. Emits `{"type":"request","content":"xxx"}` from `wechat_tick()`

## Flag Path (Windows default)

```
%LOCALAPPDATA%\wechat-agent-bridge\interrupt.flag
```

## Agent Obligation

Check the flag **before every tool call**:

```python
from wechat_agent.storage import JsonStore

flag = JsonStore().interrupt_flag_path
if flag.exists():
    # 1. Finish current atomic operation (at most 1 more tool call)
    # 2. Read and process event["content"] from wechat_tick() return value
    # 3. Send an outbox acknowledgment — see rules/outbox.md
    flag.unlink(missing_ok=True)
```

## Fallback (Evidence Rule)

If the flag does not exist: no interrupt is pending. Do not poll terminal output or
check bridge logs on every call.

If the storage directory is inaccessible: treat as no interrupt; continue the main task.
