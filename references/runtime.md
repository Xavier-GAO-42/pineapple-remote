# Pineapple Active Runtime

Load this only while a current user task has Pineapple control enabled.

## One Task, One Helper

Allocate:

```text
~/.pineapple/sessions/<run-id>/status.json
~/.pineapple/sessions/<run-id>/requests.jsonl
```

`<run-id>` must be newly generated for this task and must also be stored as
`"run_id": "<run-id>"` in every status update. Never reuse an older run directory.
If an agent instead uses a named status file in a shared directory, the CLI isolates
its mailbox as `<status-stem>.requests.jsonl`.

The CLI automatically keeps transport runtime/profile files in a private sidecar
directory for this status file. It also rejects a second `--watch` helper for the
same `status.json`; do not retry by launching another helper.

Start exactly one helper using the Python path returned by bootstrap:

```powershell
<tool-python> -m wechat_agent.wechat_tick --backend web --watch --status-json "<status-json>"
```

If the tool is missing or reports an upgrade, read [../commands/install.md](../commands/install.md)
first. The helper opens one visible official page; ask the user to scan its QR code.

Startup health check is mandatory: within 5 seconds after launch, confirm
`.<status-stem>.pineapple-runtime/watch.lock` exists beside the status file.
If missing, treat startup as failed and do not continue claiming Pineapple is connected.

## Start Status

```json
{
  "run_id": "<run-id>",
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
The bridge persists an unsent connection outbox item until login is ready, even if a
later status update omits `outbox`.

## Checkpoints

At connection start, before a substantial tool operation, after a long operation, and
before terminal status:

1. Read `requests.jsonl` if it exists.
2. Ask: "Which request ids do not yet have an `ack-<request-id>` outbox item?"
3. Read the exact instruction from the request's `content` field. Do not use `text`.
4. For every unread request, answer, apply, stop, or decline it within the original
   task, update progress, and append one stable AI reply:

```json
{"id":"ack-<request-id>","type":"received","text":"<answer, applied-change summary, or refusal>"}
```

`ack-<request-id>` records that the instruction was handled exactly once. It must not
be a generic "已记录" receipt unless the user explicitly asked only for recording.
Questions must be answered in the AI reply; stop/cancel instructions must end the
remaining work at this checkpoint and proceed to the end gate.
Shell code may find unread ids and update status, but must not manufacture the semantic
AI reply without the agent reading and acting on `content`.

The mailbox is append-only during this task. Do not delete it or rely on helper stdout
as the durable source of instructions.
For repeated or slow work, execute one bounded segment at a time and return to these
checkpoints. One segment means one substantial tool action or one requested wait, not
five loop iterations inside a shell script. Do not wrap a multi-minute loop in one
blocking tool invocation.

At each checkpoint, also confirm this run's helper has not disappeared. The sidecar
`.<status-stem>.pineapple-runtime/watch.lock` exists while the helper owns the active
web session. If it vanishes before terminal completion, the control channel is no
longer active; re-establish it or notify the host user before continuing.

## End Gate

Before giving the final host-chat response:

- Confirm every recorded request id has one useful AI reply, not merely a receipt.
- Write `done` or `error` to the same `status.json` with concise `result` and stable `notification_id`.
- Wait for the helper to submit `🍍[自动回复]💻👌完成：...`, settle delivery for about 3 seconds, and exit.

The bridge will not submit terminal completion while a received request still lacks
its sent `ack-<request-id>` AI acknowledgment.

For long-running repeated work, remain `running` and update `progress` at meaningful
checkpoints. Enter terminal state only when the full user task completes, fails, or
the user explicitly stops it.
