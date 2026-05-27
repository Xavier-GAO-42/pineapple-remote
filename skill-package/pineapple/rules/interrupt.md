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
2. “What exactly does each unread request's `content` say?”
3. “How does that content change the original task, or what answer does it require?”

The request text field is exactly `content`, not `text`, `message`, or the flag file.
Do not write a PowerShell/Python loop that invents AI reply bodies from placeholders
or phases. The agent must read `content`, decide the response, then write the outbox item.

For every unread request, interpret and handle it, update progress, and send exactly
one useful AI reply before continuing affected work. The `ack-<request-id>` id means
"handled once"; it does not mean "send a generic receipt."

```json
{"id":"ack-<request-id>","type":"received","text":"<answer, applied-change summary, or refusal>"}
```

Choose the reply from the request's intent:

- A question requires the answer in the AI reply.
- A steering instruction requires a concise statement of what will change.
- A stop/cancel instruction requires a reply and prompt terminal handling.
- A disallowed request requires a refusal with a brief reason.
- Use "已记录" only if the user explicitly asks to record something.

Ask before sending: "Does this reply satisfy the user's instruction, or only confirm
that I read it?" A receipt-only reply is not handled. Terminal delivery is held until
a reply with stable `ack-<request-id>` has been sent.

Treat a request event as steering for the active original task, not automatically as
a new standalone task. Preserve the original task summary unless the user explicitly
replaces it, and update `progress` to say that the WeChat instruction is being applied.
Unsafe or disallowed instructions must still be declined under the host agent's usual
approval and safety rules; the required outbox reply should explain that result.

## Fallback (Evidence Rule)

If `requests.jsonl` is absent, no persisted request is pending. If storage cannot be
read, record that control input is unavailable and continue the main task safely.

The normal layout is `<run-id>/status.json` beside `<run-id>/requests.jsonl`. If a
named status file was incorrectly created in a shared directory, read its isolated
`<status-stem>.requests.jsonl` mailbox instead.
