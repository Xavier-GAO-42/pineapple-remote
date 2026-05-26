---
name: pineapple
description: Use Pineapple/菠萝 as a lightweight local WeChat 文件传输助手 control channel for an active AI agent task. Trigger for 启用菠萝, 初始化菠萝, 菠萝控制, 微信远程控制 agent, 文件传输助手查进度/干预任务, 菠萝简介, 修改菠萝 emoji, or 修改刷新时间.
---

# 菠萝 Pineapple

把微信文件传输助手变成 AI agent 的随身遥控器。

## Triggers -> Commands

| User says | Load |
|-----------|------|
| 启用菠萝 / 初始化菠萝 / 首次使用 / 本次任务启用菠萝控制 / start control | [commands/init.md](./commands/init.md) |
| 进入菠萝设置页 / 改 emoji / 改刷新时间 | [commands/settings.md](./commands/settings.md) |
| 菠萝简介 | Print product copy below; do NOT open any page |

**Product copy:** 把微信文件传输助手变成 AI agent 的随身遥控器。电脑上 agent 在跑任务，你可以直接用手机微信发送 `🍍?` 查进度，用 `🍍：xxx` 追加要求。任务完成后，结果自动发回文件传输助手。

## Three Rules

- `省`: load only the command or rule needed at the current stage; do not load every detail up front.
- `准`: Pineapple accompanies the original task. A WeChat request is steering for that task, and must get an agent reply.
- `稳`: one controlled task owns exactly one status file and one watch helper, ending only after its terminal notification settles and the helper exits.

## Fixed Workflow

Use this checklist for every controlled task:

- [ ] Decide whether this is install-only or control for a current task; load [commands/init.md](./commands/init.md).
- [ ] Prepare exactly one run id, one UTF-8 `status.json`, and one `--watch` helper.
- [ ] After page login is usable, send exactly one AI connection message: `[AI回复]🤖👌🍍:菠萝控制已连接。`
- [ ] Immediately continue the original task; update status only at meaningful milestones.
- [ ] For each `🍍：内容` event, incorporate the steering and send one concise `[AI回复]` acknowledgment.
- [ ] At task end, write one `done` or `error` status with a stable `notification_id`.
- [ ] Before final host response, wait until the helper exits after its final delivery-settle window.

## Active Task Rules

Load these whenever control is active:

| Rule | Load when |
|------|-----------|
| [rules/status-format.md](./rules/status-format.md) | Updating status.json |
| [rules/interrupt.md](./rules/interrupt.md) | Handling `🍍：...` steering or checking interruption |
| [rules/outbox.md](./rules/outbox.md) | Sending proactive messages |

## Protocol

- `🍍?` / `🍍？` → status reply only; no request event
- `🍍:内容` / `🍍：内容` → automatic acknowledgment, then steering event; the agent must send one manual acknowledgment
- Status query → `[自动回复]🤖👌🍍:状态：<status>`
- Request receipt → `[自动回复]🤖👌🍍:已接收请求，AI正在处理中。`
- Agent acknowledgment/outbox → `[AI回复]🤖👌🍍:<text>`
- Task end → `[自动回复]🤖👌🍍:完成：<summary>`, then delivery settle and helper exit

## Language Policy

- Default language for all Pineapple channel messages is Chinese.
- Use English only when the user explicitly requests English output.
- If the user requests switching back to Chinese, that request follows the same mandatory agent acknowledgment rule.

## Safety

- Operate only the official File Transfer Assistant webpage.
- Bridge failures are non-fatal; keep the main task going.
- Live Chinese/emoji text must originate from UTF-8 Python source, not shell literals.
- The task-local webpage login exists only for the active helper and is closed at task end.
- WeChat instructions remain subject to the host agent's normal approval rules.
