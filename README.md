# 🍍 菠萝 Pineapple

**把微信文件传输助手变成本地 AI agent 的随身遥控器。**

电脑上 agent 在跑任务？拿起手机，打开微信文件传输助手——

| 你发 | 效果 |
|------|------|
| 🍍? | 查询当前进度 |
| 🍍：改一下方案 | 给 agent 追加要求 |

任务完成，结果自动推送到手机。

> ✅ 无后台常驻 · 每次扫码 · 只读文件传输助手 · agent 完成即退出
> ✅ 已通过 DeepSeek V4 Flash / GPT 5.2 / Haiku 4.5 弱模型长线测试
> ✅ 推荐 Sonnet · Opus · DeepSeek V4 Pro · GPT 5.3+ 获得上佳体验
> ✅ Token 开销极低：每次任务仅增加约 500–2000 tokens（详见下方分析）

---

## Token 消耗

菠萝的设计目标是对 AI 会话的 token 开销几乎无感。

| 环节 | 增加的 tokens | 频率 |
|------|-------------|------|
| Skill 文档加载 | ~300–450 | 每次任务启动，一次性 |
| 状态更新（status.json） | ~100–300 | 每个检查点（约 1–5 次/分钟） |
| 用户干预回复 | ~50–120 | 每次发送 🍍：指令 |
| 微信轮询（后端） | 0 | 每 3–10 秒（不消耗 AI token） |
| 完成通知 | ~5–20 | 任务结束，一次性 |

**典型任务总开销：+500–2000 tokens**，取决于干预次数和状态更新频率。
对于一个消耗 10,000–50,000 tokens 的常规编程任务，菠萝的额外开销约 1–4%。
微信页面轮询完全在本地 Python 进程完成，不占用 AI token。

---

## 安装（5 分钟）

**前提**：电脑有 Python 3.10+，在用 Codex CLI 或 Claude Code CLI。

### 1 · 下载

| CLI | 安装包 |
|-----|--------|
| Codex CLI | [pineapple-codex-skill-0.3.4.zip](dist/pineapple-codex-skill-0.3.4.zip) |
| Claude Code CLI | [pineapple-claude-plugin-0.3.4.zip](dist/pineapple-claude-plugin-0.3.4.zip) |

### 2 · 交给 agent

**Codex** — 在 Codex 里说（替换路径）：

```
请把 D:\Downloads\pineapple-codex-skill-0.3.4.zip 安装为我的 pineapple skill。
安装完成后告诉我如何启用，不要启动微信页面。
```

**Claude Code** — 在 Claude Code 里说（替换路径）：

```
请把 D:\Downloads\pineapple-claude-plugin-0.3.4.zip 解压到 D:\Tools\pineapple-claude-plugin，
告诉我启动这个本地 plugin 的命令。不要启动微信页面。
```

然后按给出的路径重启 Claude Code：

```powershell
claude --plugin-dir D:\Tools\pineapple-claude-plugin
```

### 3 · 首次启用

在新 session 中，把控制要求和实际任务一起说：

```
本次任务启用菠萝控制。请检查 D:\demo7 作业，只告诉我应修改的位置。
首次请先展示初始化计划，确认后安装依赖并打开文件传输助手网页让我登录。
```

Agent 展示计划 → 你确认 → 安装依赖 → 打开网页 → 扫码 → 收到 `🍍[AI回复]🤖👌菠萝控制已连接。` → agent 开始执行任务。全程无需管理员权限。

### 4 · 任务运行中

- `🍍?` — 查进度
- `🍍：修改要求` — 发指令；bridge 立即自动确认，agent 随后必须回复如何执行
- 任务完成后自动收到结果摘要；bridge 会短暂等待最终消息同步后关闭本次网页会话

消息来源一眼可见：

```text
🍍[自动回复]💻👌状态：我正在检查项目，目前正在运行测试。
🍍[自动回复]💻👌已接收请求，AI正在处理中。
🍍[AI回复]🤖👌已记入，我会只给最小修改方案。
🍍[自动回复]💻👌完成：修改完成，测试通过。
```

> **注意**：每次任务都需要扫码一次。菠萝不后台常驻，不保留登录状态跨任务复用。

> **权限提示**：如果首次安装被命令授权拦截，agent 会说明写入范围并建议临时放宽权限：Codex 可用 `--dangerously-bypass-approvals-and-sandbox`，Claude Code 可用 `--permission-mode bypassPermissions`。这是高风险选项，仅在可信目录下使用。

---

## 日常用法

```
本次任务启用菠萝控制。
进入菠萝设置页。
把菠萝 emoji 改为 🛰️，刷新时间改为 3 秒。
菠萝简介。
```

---

## 架构简述

菠萝由单包 `wechat-agent-bridge` 驱动。Agent 在任务循环中周期性调用 `wechat_tick(status)`，该函数负责轮询微信页面、回复查询、发送主动消息和任务通知。

Codex / Claude Code 宿主通过 CLI watch 模式运行同一逻辑：一个任务生成一个新的 `run_id`、独立目录与一份 `status.json`，只启动一个 bridge helper。bridge 把干预请求追加到本轮 `requests.jsonl`，agent 在每个长操作结束后的 checkpoint 读取并用 AI 消息确认；收到但尚未确认的请求会阻止终态通知和退出。若 agent 错把命名状态文件放入共享目录，CLI 也会自动使用同名隔离 mailbox。尚未因扫码完成而送达的连接消息由 bridge 持久重试，不会因下一次状态更新丢失。若误启第二个 helper，CLI 会直接拒绝。长任务由 agent 逐步推进，不应交给一次多轮阻塞脚本。任务完成时，agent 将 `done/error` 写入状态文件并等待 helper 退出；bridge 提交最终通知，留出短暂同步时间后再关闭网页会话。

项目采用 **MIT License**，可审阅、修改和开源分发。

---

## 边界

**是什么**

- 仅操作腾讯官方页面 [filehelper.weixin.qq.com](https://filehelper.weixin.qq.com/)
- Agent 运行期间响应；不常驻，不跨任务保留会话
- 本地文件只有 bridge 状态/日志、任务级 `status.json` / `requests.jsonl` 和临时浏览器 profile

**不是什么**

- 不是微信机器人、群聊机器人或多联系人系统
- 不逆向微信协议，不 hook、不注入，不启动 server 或 daemon
- Agent 未运行时，不能从微信启动新任务

---

## Python API

```python
from wechat_agent import wechat_tick

events = wechat_tick({
    "state": "running",
    "task": "检查 demo7 作业",
    "progress": "正在看 main.c",
})
for event in events:
    if event["type"] == "request":
        # Apply the request, then include outbox id=f"ack-{event['id']}" on the next tick.
        handle_user_instruction(event["content"])
```

**状态字段**

| `state` | 含义 | 必须额外字段 |
|---------|------|------------|
| `idle` | 无活跃任务 | — |
| `running` | 进行中 | `task`, `progress` |
| `waiting_user` | 等待用户输入 | `task`, `progress` |
| `done` | 成功完成 | `result` |
| `error` | 失败 | `result` |

**主动推送（outbox）**

```python
wechat_tick({
    "state": "running",
    "task": "检查 demo7 作业",
    "outbox": [
        {"id": "demo7-connected", "type": "received", "text": "菠萝控制已连接。"}
    ],
})
```

`id` 用于去重，同一 id 只发一次。agent 的 `outbox` 消息使用 `<emoji>[AI回复]🤖👌`；查询、请求的立即确认和终态通知使用 `<emoji>[自动回复]💻👌`。request event 含稳定 `id`，agent 用 `ack-<request-id>` 回复一次。若两个独立任务可能产生相同完成文本，在 `done` 状态加 `notification_id` 字段区分。

---

## 配置

通过 `config` 字段实时修改，立即持久化：

```python
wechat_tick({
    "state": "running",
    "task": "配置",
    "config": {"emoji": "🛰️", "check_interval": 3},
})
```

`emoji` 接受任意非空字符串。`check_interval` 仅允许 `3`、`5`、`10` 秒（非法值就近归一化）。

| 输入 | 实际间隔 |
|------|---------|
| `<= 3` | 3 秒 |
| `4`–`7` | 5 秒 |
| `>= 8` | 10 秒 |

默认数据目录：`%LOCALAPPDATA%\wechat-agent-bridge`（可通过环境变量 `WECHAT_AGENT_HOME` 覆盖）。

---

## CLI API

```powershell
# Watch 模式：agent 写 status.json，从同目录 requests.jsonl 可靠读取干预
py -m wechat_agent.wechat_tick --backend web --watch --status-json status.json

# 冒烟测试（无需真实微信）
New-Item -ItemType Directory -Force .bridge-test | Out-Null
echo '{"id":"q1","text":"🍍？"}' | Set-Content -Encoding utf8 .bridge-test\mock_inbox.jsonl
py -m wechat_agent.wechat_tick --backend file-mock --storage-dir .bridge-test --status-json status.json
Get-Content .bridge-test\mock_outbox.jsonl
```

Bridge 在 `state` 变为 `done` 或 `error` 后提交通知；网页后端继续保持页面约 3 秒以完成最终同步，再自动退出。若发送失败则继续重试。`--backend web` 一次性退出模式会被拒绝。

人工冒烟验证：

```powershell
py -m wechat_agent.wechat_tick --backend web --watch --status-json examples\status-idle.json
```

---

## 官方网页后端

使用 Python Playwright 打开 [filehelper.weixin.qq.com](https://filehelper.weixin.qq.com/)，在任务专属临时浏览器 profile 中运行一个可见页面。

- **读取**：`#chatBody .msg-text` 可见文本；只处理当前 emoji 对应的协议消息，兼容全/半角标点
- **写入**：`textarea.chat-panel__input-container`
- **基线**：首次成功读取后建立当前消息基线，不回复历史文本
- **失败处理**：登录失效、网页结构变更或依赖缺失时记录安全失败，返回 `[]`，不中断主任务
- **网络范围**：仅访问腾讯官方域名；不调用微信协议接口，不发往第三方
- **源码安装**：`py -m pip install -e ".[web]"`
