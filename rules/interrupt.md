# Rule: Interrupt Detection

**Authority**: This file. No other source overrides interrupt handling.

## Mechanism

When a user sends `🍍：xxx`, the bridge:
1. Sends `🍍[自动回复]💻👌已接收请求，AI正在处理中。` automatically.
2. Appends `{"id":"...","type":"request","content":"xxx","source":"wechat"}` to the task's `requests.jsonl` in CLI watch mode.
3. Emits the same event on stdout for compatibility.
4. May write `interrupt.flag` as a legacy marker; do not use it as the content source.

## Agent Obligation

At each runtime checkpoint, read `requests.jsonl` and ask:

1. “Which request ids do not yet have an `ack-<request-id>` outbox item?”
2. “How does each unread request change the original task?”

For every unread request, apply or decline it, update progress, and send exactly one
acknowledgment before continuing affected work:

```json
{"id":"ack-<request-id>","type":"received","text":"已记入，我会按你的要求继续处理。"}
```

Treat a request event as steering for the active original task, not automatically as
a new standalone task. Preserve the original task summary unless the user explicitly
replaces it, and update `progress` to say that the WeChat instruction is being applied.
Unsafe or disallowed instructions must still be declined under the host agent's usual
approval and safety rules; the required outbox reply should explain that result.

## Fallback (Evidence Rule)

If `requests.jsonl` is absent, no persisted request is pending. If storage cannot be
read, record that control input is unavailable and continue the main task safely.
