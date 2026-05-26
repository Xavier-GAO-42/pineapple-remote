# Command: Start Pineapple Control (Watch Mode)

**Result**: Bridge process is running; events stream from stdout; agent reads and writes `status.json`.

## Write Initial Status

Create `status.json` (any writable path):

```json
{"state": "running", "task": "task name", "progress": "starting"}
```

See [rules/status-format.md](../rules/status-format.md) for full structure.

## Start Watch Process

```powershell
<bridge-python> -m wechat_agent.wechat_tick --backend web --watch --status-json <path-to-status.json>
```

First run opens a browser window — scan the QR code once. The session persists.

## Read Events

The process emits newline-delimited JSON on stdout:

```json
{"type": "request", "content": "xxx", "source": "wechat"}
```

Read stdout line-by-line. Process `type: "request"` events as user instructions.

## Update Status During Task

Overwrite `status.json` from the agent at any time. The bridge picks up changes on the next tick.

## End a Task

```json
{"state": "done", "task": "task name", "result": "concise summary", "notification_id": "task-id"}
```

The bridge sends `🍍完成：<result>` automatically. No separate outbox entry needed.
