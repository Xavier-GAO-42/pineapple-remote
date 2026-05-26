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
- Every controlled task must send exactly one connected item after the page is usable:
  `{"id":"<run-id>-connected","type":"received","text":"菠萝控制已连接。"}`
- Completion is normally sent by terminal `state: "done"` or `state: "error"`;
  do not duplicate it as an outbox item.
- Additional outbox messages are optional and reserved for meaningful acknowledgements
  or blockers, not routine progress. Progress remains available through `🍍?`.
