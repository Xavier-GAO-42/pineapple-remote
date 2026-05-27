# Pineapple Active Runtime

Load this only while a current user task has Pineapple control enabled.

## One Task, One Helper

Allocate:

```text
~/.pineapple/sessions/<run-id>/status.json
~/.pineapple/sessions/<run-id>/requests.jsonl
```

The CLI automatically keeps transport runtime/profile files in a private sidecar
directory for this status file. It also rejects a second `--watch` helper for the
same `status.json`; do not retry by launching another helper.

Start exactly one helper using the Python path returned by bootstrap:

```powershell
<tool-python> -m wechat_agent.wechat_tick --backend web --watch --status-json "<status-json>"
```

If the tool is missing or reports an upgrade, read [../commands/install.md](../commands/install.md)
first. The helper opens one visible official page; ask the user to scan its QR code.

## Start Status

```json
{
  "state": "running",
  "task": "<当前主任务摘要>",
  "progress": "菠萝控制已连接，正在开始执行任务",
  "outbox": [
    {"id": "<run-id>-connected", "type": "received", "text": "菠萝控制已连接。"}
  ]
}
```

After connection, continue the original task immediately. Pineapple is its control
channel, not a service waiting for a separate WeChat task.

## Checkpoints

At connection start, before a substantial tool operation, after a long operation, and
before terminal status:

1. Read `requests.jsonl` if it exists.
2. Ask: “Which request ids do not yet have an `ack-<request-id>` outbox item?”
3. For every unread request, apply or decline it within the original task, update
   progress, and append one stable acknowledgment:

```json
{"id":"ack-<request-id>","type":"received","text":"已记入，我会按你的要求继续处理。"}
```

The mailbox is append-only during this task. Do not delete it or rely on helper stdout
as the durable source of instructions.

## End Gate

Before giving the final host-chat response:

- Confirm every recorded request id has an AI acknowledgment.
- Write `done` or `error` to the same `status.json` with concise `result` and stable `notification_id`.
- Wait for the helper to submit `🍍[自动回复]💻👌完成：...`, settle delivery for about 3 seconds, and exit.

For long-running repeated work, remain `running` and update `progress` at meaningful
checkpoints. Enter terminal state only when the full user task completes, fails, or
the user explicitly stops it.
