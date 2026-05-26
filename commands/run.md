# Command: Run Pineapple Control

**Result**: `wechat_tick()` is being called in-process with structured status; WeChat page is open.

## Agent Loop

```python
from wechat_agent import wechat_tick

events = wechat_tick({
    "state": "running",
    "task": "task name",
    "progress": "current activity",
})
for event in events:
    if event.get("type") == "request":
        pass  # process event["content"] as user instruction
```

Call at natural task boundaries. The bridge enforces its own polling interval internally.

Keep `wechat_tick()` in the **same process** so the Playwright page session stays open after QR login.

## Status Updates

Update the status dict as work proceeds. See [rules/status-format.md](../rules/status-format.md) for structure.

## Ending a Task

Set `state` to `done` or `error` and include a `result` field. The bridge sends the completion
notification automatically; no separate outbox entry needed.

```python
wechat_tick({
    "state": "done",
    "task": "task name",
    "result": "concise summary",
    "notification_id": "unique-task-id",
})
```
