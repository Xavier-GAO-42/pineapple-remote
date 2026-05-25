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
- Runtime only while enabled: open the official File Transfer Assistant browser page and
  write local state/log files under the Pineapple data directory.
- Never: background daemon, server, screenshots, OCR, clipboard reads, desktop-WeChat
  inspection, or non-official WeChat protocol access.

The browser profile is local login-session material and should be treated as sensitive.
Anyone able to command the same WeChat File Transfer Assistant account can send bridge
instructions; the host agent must continue enforcing its normal approval rules.

## Codex And Claude Code Foreground Loop

These hosts cannot import a Python module into their own conversation loop. Maintain one
foreground helper owned by the active task:

1. Write UTF-8 status JSON in `~/.pineapple/sessions/<session-name>/status.json`.
2. Start:

```powershell
<tool-python> -m wechat_agent.wechat_tick --backend web --watch --status-json <status-json>
```

3. Keep the command running only while remote control is desired. The visible official
   webpage it opens must remain open after QR login.
4. Update the one status JSON object while work proceeds.
5. Consume JSON events printed by the helper; treat `{"type":"request"}` as a user
   instruction or intervention according to the current task.
6. Stop the helper when the controlled task or session ends.

This is the CLI adaptation of the single `wechat_tick(status)` contract; it is not a
daemon or server.

## Status Examples

```json
{"state":"running","task":"检查项目","progress":"正在运行测试"}
```

```json
{"state":"waiting_user","task":"检查项目","progress":"需要用户确认下一步"}
```

```json
{"state":"done","task":"检查项目","result":"测试通过","notification_id":"task-unique-id"}
```

## Settings

Use `python -m wechat_agent.control info` for product copy and `settings` or
`configure` for local configuration. These commands do not open WeChat or send messages.
