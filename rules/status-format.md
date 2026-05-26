# Rule: Status JSON Format

**Authority**: This file is the single source of truth for status structure.

## Template

```json
{
  "state": "running",
  "task": "<top-level task name>",
  "progress": "<active subtask or current activity>",
  "detail": {
    "done": ["step 1", "step 2"],
    "current": "<step N – specific action>",
    "remaining": 3
  }
}
```

The `progress` string is displayed in `[自动回复]🤖👌<emoji>:状态：...` replies after `🍍?`. Make it specific enough to
be useful: `"Task 4/10 完成，当前：Task 5"` rather than `"进行中"`.

The `detail` field is optional. Use it for multi-step tasks where subtask tracking is
meaningful; omit it for short or single-step work.

## State Values

| Value | Meaning | Required extra fields |
|-------|---------|----------------------|
| `idle` | No active task | — |
| `running` | Work in progress | `task`, `progress` |
| `waiting_user` | Blocked, needs input | `task`, `progress` |
| `done` | Completed successfully | `result`, `notification_id` |
| `error` | Failed | `result`, `notification_id` |

Use `waiting_user` only when execution of the original main task is blocked by a
concrete missing decision or information. Do not use it because the bridge is open,
because QR login is pending while other work can proceed, or because the user has
not sent an optional WeChat instruction.

Update status at user-visible milestones rather than every trivial read: connection
startup, a substantial phase beginning or ending, application of steering, and task end.
In CLI watch mode, every update for a task goes to the one status file passed to its
watch helper. Never publish terminal status through a second tick process.

## Completion Example

```json
{
  "state": "done",
  "task": "refactor login module",
  "result": "完成，3 个文件已修改，测试通过",
  "notification_id": "refactor-login-20260526"
}
```

Use `notification_id` when multiple tasks may produce identical completion text.
