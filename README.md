# 菠萝 Pineapple
> 把微信文件传输助手变成本地 AI agent 的随身遥控器。

电脑上 agent 在跑任务，你可以直接用手机微信发消息：

| 发什么 | 效果 |
|--------|------|
| 🍍? | 查询当前进度 |
| 🍍：xxx | 给 agent 追加要求或干预 |

任务完成后，结果自动推送到文件传输助手：

```text
🍍完成：检查完毕，修改位置与结果摘要已整理完成。
```

不需要守在电脑前，不需要服务端，不读取你的其他聊天。

菠萝跟随的是你刚刚交给 agent 的那一次任务：连接建立后会先发出
`🍍收到：菠萝控制已连接。`，随后 agent 继续原任务；结果发出后，本次
Python helper 自动退出，不在电脑上留下等待新任务的常驻服务。每次启用
都会打开一个新的临时网页会话，由你为这一次任务扫码登录。

---

## 安装（5 分钟）

**前提**：电脑有 Python 3.10+，在用 Codex CLI 或 Claude Code CLI。

### 1 · 下载

| CLI | 安装包 |
|-----|--------|
| Codex CLI | [pineapple-codex-skill-0.2.2.zip](dist/pineapple-codex-skill-0.2.2.zip) |
| Claude Code CLI | [pineapple-claude-plugin-0.2.2.zip](dist/pineapple-claude-plugin-0.2.2.zip) |

### 2 · 交给 agent

**Codex** — 在 Codex 里说（替换路径）：

```
请把 D:\Downloads\pineapple-codex-skill-0.2.2.zip 安装为我的 pineapple skill。
安装完成后告诉我如何启用，不要启动微信页面。
```

**Claude Code** — 在 Claude Code 里说（替换路径）：

```
请把 D:\Downloads\pineapple-claude-plugin-0.2.2.zip 解压到 D:\Tools\pineapple-claude-plugin，
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

Agent 展示计划 → 你确认 → 安装依赖 → 打开网页 → 扫码 → 收到 `🍍收到：菠萝控制已连接。` → agent 开始执行任务。全程无需管理员权限。

### 4 · 任务运行中

- `🍍?` — 查进度
- `🍍：修改要求` — 发指令，agent 立即收到并确认
- 任务完成后自动收到结果摘要，本次网页会话随即关闭

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

Codex / Claude Code 宿主通过 CLI watch 模式运行同一逻辑：bridge 作为前台进程持有页面，从标准输出逐行输出 JSON 事件，agent 写入 `status.json` 更新状态。任务完成后，bridge 发送通知并退出，页面会话随之关闭。

项目采用 **MIT License**，可审阅、修改和开源分发。

---

## 边界

**是什么**

- 仅操作腾讯官方页面 [filehelper.weixin.qq.com](https://filehelper.weixin.qq.com/)
- Agent 运行期间响应；不常驻，不跨任务保留会话
- 本地文件只有 `config.json`、`runtime.json`、`bridge.jsonl` 和临时浏览器 profile

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

`id` 用于去重，同一 id 只发一次。`type: "received"` 前缀 `🍍收到：`，`type: "done"` 前缀 `🍍完成：`。若两个独立任务可能产生相同完成文本，在 `done` 状态加 `notification_id` 字段区分。

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
# Watch 模式：agent 写 status.json，从 stdout 读事件
py -m wechat_agent.wechat_tick --backend web --watch --status-json status.json

# 冒烟测试（无需真实微信）
New-Item -ItemType Directory -Force .bridge-test | Out-Null
echo '{"id":"q1","text":"🍍？"}' | Set-Content -Encoding utf8 .bridge-test\mock_inbox.jsonl
py -m wechat_agent.wechat_tick --backend file-mock --storage-dir .bridge-test --status-json status.json
Get-Content .bridge-test\mock_outbox.jsonl
```

Bridge 在 `state` 变为 `done` 或 `error` 且通知发送成功后自动退出。`--backend web` 一次性退出模式会被拒绝（关闭页面后无法可靠保留会话）。

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
