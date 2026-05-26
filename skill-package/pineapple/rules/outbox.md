# Rule: Proactive Outbox

Outbox is the **only** mechanism for agent-initiated messages. `progress` and `task` are
only visible when the user sends `🍍?`. Use outbox whenever you want to push a message
without waiting for a query.

## Format

Add an `outbox` array to `status.json` before the next tick:

```json
{
  "state": "running",
  "task": "current task",
  "outbox": [
    {"id": "unique-stable-id", "type": "received", "text": "Message"}
  ]
}
```

## Rules

- `id` is **stable and unique** across ticks — same id = already sent, skip
- `type: "received"` → prefix `🍍收到：`
- `type: "done"` → prefix `🍍完成：`
- Keep text brief; this is a control channel, not a chat
