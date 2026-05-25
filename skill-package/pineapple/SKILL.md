---
name: pineapple
description: Initialize and use Pineapple, a local WeChat File Transfer Assistant control channel for monitoring or intervening in active AI agent tasks. Use when the user asks to enable 菠萝/Pineapple, connect WeChat file helper, remote-control an agent, view 菠萝简介, or change its emoji or refresh interval.
---

# 菠萝 Pineapple

用微信文件传输助手，远程监控和干预你的 AI agent。

## Product Copy

- 副标题：电脑上 agent 在跑任务，你可以直接用手机微信发送 `🍍?` 查进度，用 `🍍：xxx` 追加要求。任务完成后，结果自动发回文件传输助手。
- Slogan：把微信文件传输助手变成 AI agent 的随身遥控器。

When asked for `菠萝简介`, respond with the product copy above. Do not start a page unless the user also asks to connect or run it.

## First Use

The installed skill is the only manually installed product. Its first use may create a reusable local tool under `~/.pineapple/bridge-tool`.

Set `<skill-root>` to the directory containing this `SKILL.md`. In Claude plugin
loading it is `${CLAUDE_PLUGIN_ROOT}/skills/pineapple`; in Codex use the skill path
provided in the available-skills metadata.

1. On Windows, run `powershell -ExecutionPolicy Bypass -File "<skill-root>/scripts/bootstrap.ps1" discover --json`. On macOS/Linux, run `python3 -B "<skill-root>/scripts/bootstrap.py" discover --json`.
2. If it reports `ready`, reuse it. Do not reinstall it.
3. If it reports `source_found`, report that source to the user and ask permission before adopting it into the shared user directory.
4. If it reports `missing`, tell the user no compatible reusable tool was found and ask whether they already have a Pineapple/`wechat_tick` script directory to adopt.
5. Before any adoption or bundled installation, run the same wrapper with `plan --source <path-or-bundled>` and show its JSON summary: target directory, files copied, bundled packaging metadata, venv creation, optional dependency installation, and whether adopted source code will run when enabled. Proceed only after explicit user confirmation.
6. If the user provides and approves a compatible source, run the wrapper with `adopt --source <path> --json`.
7. If there is no compatible existing source and the user approves the displayed plan, run the wrapper with `install --json`.
8. Read `references/runtime.md` for actual loop commands after a tool is ready.

The tool is user-level and reusable by Codex, Claude Code, and other agent sessions. Do not create a server, database, launcher daemon, tray application, or background service.
Do not ask the user to install Python packages manually: after approval, `adopt` or `install`
creates the local virtual environment and installs its Playwright dependency. If Python
3.10+ itself cannot be found, explain that runtime prerequisite clearly.

Permission rule: `discover` and `plan` are read-only. `adopt` and `install` may write only
the displayed user-level tool directory and its local virtual environment. Never perform
these write operations silently. Adoption uses the bundled packaging metadata, rather than
executing build metadata from the discovered source directory.

## Start Control During Work

For a Python agent capable of holding imports, call the installed tool's single API:

```python
from wechat_agent import wechat_tick
events = wechat_tick({"state": "running", "task": "...", "progress": "..."})
```

For Codex or Claude Code, use the agent-owned foreground helper described in `references/runtime.md`; keep it alive only while the current task needs WeChat control. It preserves the official web page session and exposes the same status/event contract.

Tell the user to scan the official File Transfer Assistant web page when it appears. Operate only its visible chat interface; the official page may itself load Tencent-owned login and static-resource domains.

## Settings Conversation

When the user says `进入菠萝设置页`, do not build a UI. Read current settings, then respond:

```text
菠萝设置
当前 emoji：<emoji>
刷新时间：<seconds> 秒
要修改 emoji 还是刷新时间？
```

Use the installed tool:

```powershell
<tool-python> -m wechat_agent.control settings
<tool-python> -m wechat_agent.control configure --emoji "🛰️"
<tool-python> -m wechat_agent.control configure --check-interval 3
```

Allowed refresh intervals are `3`, `5`, and `10` seconds; other numeric requests normalize to those modes. Changes persist for later sessions and apply to the next active loop.

## Protocol

- Status query: `🍍?` or `🍍？`; reply only, never create a request event.
- Request/intervention: `🍍:内容` or `🍍：内容`; immediately acknowledge and return a request event.
- Completion: send `🍍完成：<摘要>` once.
- The configured emoji replaces `🍍` immediately after a configuration change.

## Safety

- Operate only the official File Transfer Assistant webpage.
- Do not read contacts, groups, or unrelated chats.
- Do not screenshot, OCR, inspect clipboard contents, reverse-engineer protocols, hook, or inject.
- Initial successful connection baselines existing visible messages; handle only messages appearing afterward.
- If the page is unavailable, keep the user's primary task going and report the bridge issue briefly.
- Live Chinese/emoji messages must originate in UTF-8 Python source or status JSON, not shell-piped inline literals.
- Treat the local browser profile as sensitive login-session data; a person who controls the logged-in WeChat account can issue bridge commands.
- Instructions received from WeChat remain subject to the host agent's usual approval and filesystem/command permissions.
