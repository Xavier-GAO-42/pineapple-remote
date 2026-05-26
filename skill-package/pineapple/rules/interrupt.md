# Rule: Interrupt Detection

**Authority**: This file. No other source overrides interrupt handling.

## Mechanism

When a user sends `🍍：xxx`, the bridge:
1. Sends `🍍收到：AI正在处理中。` to WeChat automatically
2. Writes `interrupt.flag` in the storage directory
3. Emits `{"type":"request","content":"xxx"}` on stdout (watch mode)

## Agent Obligation

Check the flag before beginning the next tool operation while control is active:

```python
from wechat_agent.storage import JsonStore

flag = JsonStore().interrupt_flag_path
if flag.exists():
    # Finish the current atomic operation, then apply this steering to the main task.
    flag.unlink(missing_ok=True)
```

Treat a request event as steering for the active original task, not automatically as
a new standalone task. Preserve the original task summary unless the user explicitly
replaces it, and update `progress` to say that the WeChat instruction is being applied.
Unsafe or disallowed instructions must still be declined under the host agent's usual
approval and safety rules; a brief outbox reply can explain that result.

## Fallback (Evidence Rule)

If the flag does not exist: no interrupt is pending. Do not poll stdout on every call.

If storage is inaccessible: treat as no interrupt; continue the main task.
