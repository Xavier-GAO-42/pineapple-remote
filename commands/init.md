# Command: Start Pineapple Control

Use this only when a current user task explicitly enables Pineapple control. Pineapple
accompanies that original task; it is never an idle listener waiting for a new task.

## Start

1. Load [../references/runtime.md](../references/runtime.md).
2. Ensure the reusable bridge is ready. If not, load [install.md](./install.md) and complete setup first.
3. Create a new unique run id and a fresh `<run-id>/status.json` for this task. Do not reuse a status path from an earlier task.
4. Start one `--watch` helper with that status path and keep its page open only for this task.
5. Run startup health check: within 5 seconds, confirm `.<status-stem>.pineapple-runtime/watch.lock` exists beside the status file.
6. When the page is usable, send the single connection outbox and immediately resume the original task.

Do not launch a second `wechat_tick()` process, create another status file, or stop
at "waiting for WeChat instructions."

## While Active

- Update the same `status.json` at meaningful milestones.
- At each checkpoint defined in runtime, read `requests.jsonl`; every unread request requires one useful AI answer, applied-change summary, or refusal before affected work continues.
- For loops or long waits, run one operation per agent checkpoint. Never create a shell `for` loop that performs multiple waits or status rewrites before the agent can read and answer WeChat requests.
- After a long tool result returns, confirm this run's helper is still alive. If it is gone while the task remains active, stop claiming Pineapple control is connected and re-establish the channel before continuing a control-required task.
- Keep messages Chinese by default unless the user explicitly requests English.

## Before Final Response

- [ ] Every request in `requests.jsonl` has exactly one useful `ack-<request-id>` AI reply; none merely says it was recorded.
- [ ] The same `status.json` now contains `done` or `error`, `result`, and a stable `notification_id`.
- [ ] The watch helper submitted `🍍[自动回复]💻👌完成：...`, completed its delivery settle, and exited.
