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
- Any agent outbox item → prefix `<emoji>[AI回复]🤖👌`
- `type: "done"` additionally prefixes its text with `完成：`; normal completion should use terminal state
- Keep text brief; this is a control channel, not a chat
- Default outbox text language is Chinese unless the user explicitly requests English.
- Every controlled task must send exactly one connected item after the page is usable:
  `{"id":"<run-id>-connected","type":"received","text":"菠萝控制已连接。"}`
- Put only the reply body in `text`; do not include the emoji or `[AI回复]` prefix.
- If login is not ready when an outbox item is first seen, the bridge keeps retrying it;
  the agent may continue status updates without removing delivery responsibility.
- Completion is normally sent by terminal `state: "done"` or `state: "error"`;
  do not duplicate it as an outbox item.
- For every request event from `🍍：内容`, one concise useful reply outbox item is mandatory: answer, applied change, stop result, or refusal; never a receipt-only "已记录".
- Other additional messages are optional and reserved for blockers or major decisions, not routine progress.

Before sending an outbox item, ask: “用户是否需要立即知道我已接纳、拒绝或受阻？”
If the answer is no and there was no request event, expose it through `🍍?` status instead.
