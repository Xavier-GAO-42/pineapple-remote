# Rule: Interrupt Detection

**Authority**: This file. No other source overrides interrupt handling.

## Mechanism

When a user sends `🍍：xxx`, the bridge:
1. Sends `🍍收到：AI正在处理中。` to WeChat automatically
2. Writes `interrupt.flag` in the storage directory
3. Emits `{"type":"request","content":"xxx"}` on stdout (watch mode)

## Flag Path (Windows default)

```
%LOCALAPPDATA%\wechat-agent-bridge\interrupt.flag
```

## Agent Obligation

Check the flag **before every tool call**:

```powershell
if (Test-Path "$env:LOCALAPPDATA\wechat-agent-bridge\interrupt.flag") {
    # 1. Finish current atomic operation (at most 1 more tool call)
    # 2. Read the request from stdout (watch process output)
    # 3. Send an outbox acknowledgment — see rules/outbox.md
    Remove-Item "$env:LOCALAPPDATA\wechat-agent-bridge\interrupt.flag"
}
```

## Fallback (Evidence Rule)

If the flag does not exist: no interrupt is pending. Do not poll stdout on every call.

If storage is inaccessible: treat as no interrupt; continue the main task.
