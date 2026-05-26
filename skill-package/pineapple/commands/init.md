# Command: Start Pineapple Control

**Result**: for an active controlled task, a live Pineapple watch process accompanies that one task; on first use, install the reusable user-level tool before starting it.

This is the single initialization/startup flow for both first use and later sessions.

## Mode Decision

- `安装菠萝` or `初始化菠萝` without a main task: ensure the reusable tool is ready, then stop. Do not open WeChat.
- A current main task explicitly enables Pineapple: ensure the tool is ready, start one watch helper for that task, and immediately continue the original task.
- A bare request to start control with no task: ask whether to run a short connection test or to attach control to a stated task. Do not create an idle long-running listener.

Pineapple is not the task itself. It is a temporary control channel accompanying the user's original task.

## Ownership Invariant

For each controlled task, use exactly:

- one run id;
- one UTF-8 `status.json` file;
- one `--watch` helper launched with that same status file.

After the helper starts, update only that same file. Do not invoke another standalone
`wechat_tick()` process for progress or completion, and do not switch to a different
status file. The watch helper owns all WeChat reads and writes for this task.

## 1. Explain Permissions

Before first-time writes, tell the user exactly what may happen after approval:

- Write `~/.pineapple/bridge-tool` and a per-session status JSON.
- Create a local virtual environment and install the Python `playwright` dependency.
- Open a visible official File Transfer Assistant webpage only after starting control.
- Keep one helper process and its temporary webpage session alive only while the current task uses WeChat control.

If an auto-mode agent is blocked by repeated command approvals, suggest restarting this trusted session with bypass only after the user accepts the wider command-execution risk:

```powershell
# Codex CLI
codex --dangerously-bypass-approvals-and-sandbox

# Claude Code CLI, retaining the plugin
claude --plugin-dir "<pineapple-plugin-dir-or-zip>" --permission-mode bypassPermissions
```

Do not claim bypass is required. Do not use it silently. Because login needs network access, advise using it only for this explicitly trusted setup/task workspace.

## 2. Ensure The Tool Is Ready

Set `<skill-root>` to the directory containing this skill's `SKILL.md`.

On Windows:

```powershell
powershell -ExecutionPolicy Bypass -File "<skill-root>\scripts\bootstrap.ps1" discover --json
```

On macOS/Linux:

```bash
python3 -B "<skill-root>/scripts/bootstrap.py" discover --json
```

Handle the JSON result:

- `ready` with a non-empty reported `python`: keep it; continue directly to Start Watch.
- `ready` without a usable `python`: run `plan --source "<preferred.source>" --json`; after approval run `adopt --source "<preferred.source>" --json` to repair its local environment.
- `upgrade_needed`: explain that an older reusable bridge was found; run `plan --source bundled --json` and, only after approval, run `install --source bundled --json` to upgrade it before starting control.
- `source_found`: run `plan --source "<preferred.source>" --json`; present the plan and, only after explicit approval, run `adopt --source "<preferred.source>" --json`.
- `missing`: run `plan --source bundled --json`; present the plan and, only after explicit approval, run `install --source bundled --json`.

Use the same wrapper syntax as `discover`; only replace the command and parameters. `adopt`/`install` automatically create the local virtual environment and install the web dependency. Do not ask the user to run `pip` or `playwright install`.

If Python 3.10+ cannot be found, report that one prerequisite and stop initialization safely.

## 3. Start Watch For An Active Task

Only when there is an active controlled task, after receiving `{"status":"ready","python":"<bridge-python>"}`, create one UTF-8 status file in a writable per-task location. Use a stable unique run id:

```json
{
  "state": "running",
  "task": "<用户刚刚提交的主任务摘要>",
  "progress": "菠萝控制已连接，正在开始执行任务",
  "outbox": [
    {
      "id": "<run-id>-connected",
      "type": "received",
      "text": "菠萝控制已连接。"
    }
  ]
}
```

Start the following as an agent-owned active helper process and keep it running while control is enabled:

```powershell
<bridge-python> -m wechat_agent.wechat_tick --backend web --watch --status-json "<status-json>"
```

The command opens a fresh visible official File Transfer Assistant webpage. Ask the user to scan its QR code for this task. Once usable, the stable connected outbox sends exactly one `[AI回复]🤖👌🍍:菠萝控制已连接。`. Do not wait for a query or a new WeChat task before executing the original request. Do not close this helper before the task finishes.
Use Chinese for connected/progress/completion/outbox text by default unless the user explicitly asks for English.

## 4. Use During The Task

- Update the same status JSON immediately after startup, before substantial work phases, after meaningful milestones, when applying a WeChat intervention, and before the final response; follow [../rules/status-format.md](../rules/status-format.md).
- Before tool calls while control is active, follow [../rules/interrupt.md](../rules/interrupt.md).
- For proactive replies, follow [../rules/outbox.md](../rules/outbox.md).
- For every request event from `🍍：...`, update progress, apply it to the original task, and post one concise AI outbox acknowledgment. This is required, including for a language request such as “换成中文”.
- At task end, before giving the final host response, write a `done` or `error` status to the same file with a concise `result` and stable `notification_id`.
- Wait for the watch helper to exit. It submits `[自动回复]🤖👌🍍:完成：...`, holds the webpage for an approximately 3-second delivery-settle window, then closes this task's session and exits.
- If final submission is unavailable, the helper stays alive to retry. Do not report that WeChat was notified until the helper exits normally.
- A later controlled task starts fresh and asks for a new QR login.

## Before Final Response

- Confirm that only the original task status file was updated.
- Confirm that each received request event has an AI outbox acknowledgment.
- Confirm that terminal state and stable `notification_id` were written.
- Confirm that the watch helper exited normally after the terminal message settled.
