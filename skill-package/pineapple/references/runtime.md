# Pineapple Runtime

## Installed Tool Location

Bootstrap returns JSON containing `tool_home` and `python`. The default installation is:

```text
~/.pineapple/bridge-tool
~/.pineapple/bridge-tool/.venv/Scripts/python.exe
```

Use the reported Python path, not an assumed global environment.

## Permission Footprint

Initialization is intentionally small and explicit:

- Read-only: search for a compatible local tool source and print an installation plan.
- After user approval only: write `~/.pineapple/bridge-tool`, standard local package
  metadata (`*.egg-info`), create its `.venv`, and install the tool plus the Playwright
  Python package into that venv.
- When adopting an existing tool, use the bundled packaging metadata; adopted Python
  source is still executable code when the user later enables the bridge.
- Runtime only while enabled: open a fresh official File Transfer Assistant browser page,
  keep its temporary browser session for this task, and write local state/log files.
- Never: background daemon, server, screenshots, OCR, clipboard reads, desktop-WeChat
  inspection, or non-official WeChat protocol access.

The temporary browser session is sensitive while the task is active and is closed when
the helper exits. Each new controlled task asks for a new QR login. Anyone able to
command the same WeChat File Transfer Assistant account during that active task can
send bridge instructions; the host agent must continue enforcing its normal approval rules.

## Codex And Claude Code Task Companion Loop

These hosts cannot import a Python module into their own conversation loop. Maintain one
foreground helper owned by the active task:

1. Preserve the user's original main task; Pineapple is only its control channel.
2. Write UTF-8 status JSON in `~/.pineapple/sessions/<session-name>/status.json`.
   The first running status includes one stable outbox item with text
   `菠萝控制已连接。`.
3. Start:

```powershell
<tool-python> -m wechat_agent.wechat_tick --backend web --watch --status-json <status-json>
```

4. Keep the command running only while this task is executing. Scan the new visible
   official webpage for this task and keep it open until completion.
5. Immediately resume the original task after starting control; never wait for an
   optional WeChat instruction.
6. Update the one status JSON object at meaningful milestones while work proceeds.
7. Consume JSON events printed by the helper; treat `{"type":"request"}` as steering
   for the active original task unless its content explicitly replaces that task.
8. Write terminal `done` or `error` status at task end. After the completion message
   is delivered, the helper closes this page session and exits automatically; an
   unavailable send is retried.

This is the CLI adaptation of the single `wechat_tick(status)` contract; it is not a
daemon or server.

## Status Examples

```json
{"state":"running","task":"检查项目","progress":"菠萝控制已连接，正在运行测试","outbox":[{"id":"check-project-connected","type":"received","text":"菠萝控制已连接。"}]}
```

```json
{"state":"waiting_user","task":"检查项目","progress":"需要用户确认下一步"}
```

```json
{"state":"done","task":"检查项目","result":"测试通过","notification_id":"task-unique-id"}
```

Use `waiting_user` only if the main task cannot proceed until a concrete user answer
arrives. It does not mean waiting for QR login or waiting for optional WeChat control.

## Settings

Use `python -m wechat_agent.control info` for product copy and `settings` or
`configure` for local configuration. These commands do not open WeChat or send messages.
