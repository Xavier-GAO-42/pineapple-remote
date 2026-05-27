---
name: pineapple
description: Use Pineapple/菠萝 as a lightweight local WeChat 文件传输助手 control channel for an active AI agent task. Trigger for 启用菠萝, 初始化菠萝, 菠萝控制, 微信远程控制 agent, 文件传输助手查进度/干预任务, 菠萝简介, 修改菠萝 emoji, or 修改刷新时间.
---

# 菠萝 Pineapple

## Active Control Card

When Pineapple controls an active task, these four obligations override convenience:

1. Check `requests.jsonl` at every checkpoint. Read each request's `content` field yourself and send one useful `🍍[AI回复]🤖👌...` answer, applied-change summary, or refusal; never let a shell template reply for you.
2. Start with a fresh `run_id` and its own `status.json`; keep updating that file only.
3. Before answering the host user at task end, write `done` or `error` with `result` and a stable `notification_id`.
4. Wait for the watch helper to send its terminal notification, settle delivery, and exit.

For long or repeated work, the agent owns the loop: perform one substantive operation,
return to a Pineapple checkpoint, then continue. Never delegate many iterations to one
blocking shell script, because it cannot apply WeChat steering or recover a lost helper.

把微信文件传输助手变成 AI agent 的随身遥控器。

## Triggers

| User intent | Read next |
|-------------|-----------|
| 安装菠萝 / 初始化菠萝，无主任务 | [commands/install.md](./commands/install.md) |
| 本次任务启用菠萝控制 / start control | [commands/init.md](./commands/init.md), then [references/runtime.md](./references/runtime.md) |
| 进入菠萝设置页 / 改 emoji / 改刷新时间 | [commands/settings.md](./commands/settings.md) |
| 菠萝简介 | Print the product copy below; do not open any page |

**Product copy:** 把微信文件传输助手变成 AI agent 的随身遥控器。电脑上 agent 在跑任务，你可以直接用手机微信发送 `🍍?` 查进度，用 `🍍：xxx` 追加要求。任务完成后，结果自动发回文件传输助手。

## Fixed Lifecycle

- [ ] Identify install-only versus active control; load only the listed document.
- [ ] For active control, create a fresh run id, its own run directory and UTF-8 `status.json`, and one `--watch` helper.
- [ ] If helper startup reports one is already active for that status file, reuse it; never start a replacement helper.
- [ ] Run startup health check: if `.<status-stem>.pineapple-runtime/watch.lock` is missing within 5 seconds, treat startup as failed.
- [ ] After login is usable, send once: `🍍[AI回复]🤖👌菠萝控制已连接。`
- [ ] Execute the original task; at each checkpoint check `requests.jsonl`, meaningfully answer or apply unread requests, then update status.
- [ ] After every long wait/tool operation: verify the helper is still active, read requests, send required AI replies, then start the next operation.
- [ ] At task end write `done` or `error`, then wait for the helper to exit before replying in the host chat.

## Protocol

- `🍍?` / `🍍？` -> `🍍[自动回复]💻👌状态：<status>`; no request event.
- `🍍:内容` / `🍍：内容` -> `🍍[自动回复]💻👌已接收请求，AI正在处理中。`, then a durable request event that requires one useful AI reply.
- Agent outbox -> `🍍[AI回复]🤖👌<text>`.
- Task end -> `🍍[自动回复]💻👌完成：<summary>`, then delivery settle and helper exit.
- The configurable `emoji` replaces `🍍`; default control-channel language is Chinese unless the user explicitly requests English.

## Read When Needed

| Document | Read when |
|----------|-----------|
| [references/runtime.md](./references/runtime.md) | Starting or operating an active helper |
| [rules/status-format.md](./rules/status-format.md) | Writing status |
| [rules/interrupt.md](./rules/interrupt.md) | Checking or applying WeChat steering |
| [rules/outbox.md](./rules/outbox.md) | Sending an AI message |

## Safety

- Operate only the official File Transfer Assistant webpage.
- Bridge failures are non-fatal; keep the main task going.
- Live Chinese/emoji text must originate from UTF-8 Python source, not shell literals.
- A controlled task owns one temporary webpage session, closed at task end.
- WeChat instructions remain subject to the host agent's normal permissions and safety rules.
