# Command: Start Pineapple Control

Use this only when a current user task explicitly enables Pineapple control. Pineapple
accompanies that original task; it is never an idle listener waiting for a new task.

## Start

1. Load [../references/runtime.md](../references/runtime.md).
2. Ensure the reusable bridge is ready. If not, load [install.md](./install.md) and complete setup first.
3. Create one run id and one UTF-8 `status.json` for this task.
4. Start one `--watch` helper with that status path and keep its page open only for this task.
5. When the page is usable, send the single connection outbox and immediately resume the original task.

Do not launch a second `wechat_tick()` process, create another status file, or stop
at “waiting for WeChat instructions.”

## While Active

- Update the same `status.json` at meaningful milestones.
- At each checkpoint defined in runtime, read `requests.jsonl`; every unread request requires an AI acknowledgment before affected work continues.
- Keep messages Chinese by default unless the user explicitly requests English.

## Before Final Response

- [ ] Every request in `requests.jsonl` has exactly one `ack-<request-id>` outbox item.
- [ ] The same `status.json` now contains `done` or `error`, `result`, and a stable `notification_id`.
- [ ] The watch helper submitted `🍍[自动回复]💻👌完成：...`, completed its delivery settle, and exited.
