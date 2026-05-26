# 菠萝 Pineapple

> 把微信文件传输助手变成本地 AI agent 的随身遥控器。

电脑上 agent 在跑任务，你可以直接用手机微信发消息：

| 发什么 | 效果 |
|--------|------|
| 🍍? | 查询当前进度 |
| 🍍：xxx | 给 agent 追加要求或干预 |

任务完成后，结果自动推送到文件传输助手：

`
🍍完成：检查完毕，修改位置与结果摘要已整理完成。
`

不需要守在电脑前，不需要服务端，不读取你的其他聊天。

---

## 快速安装（0基础）

**前提**：电脑已有 Python 3.10+（能运行 py -V 或 python -V 即可）。

### 第一步：下载安装包

| 你用的 CLI | 下载文件 |
|-----------|---------|
| Codex CLI | [pineapple-codex-skill-0.2.0.zip](dist/pineapple-codex-skill-0.2.0.zip) |
| Claude Code CLI | [pineapple-claude-plugin-0.2.0.zip](dist/pineapple-claude-plugin-0.2.0.zip) |

### 第二步：让 agent 安装它

**Codex CLI** — 打开 Codex，复制下面这句（替换实际路径）：

`
请把 D:\Downloads\pineapple-codex-skill-0.2.0.zip 安装为我的 pineapple skill。
安装完成后告诉我如何启用，不要启动微信页面。
`

**Claude Code CLI** — 打开 Claude Code，粘贴：

`
请把 D:\Downloads\pineapple-claude-plugin-0.2.0.zip 解压到 D:\Tools\pineapple-claude-plugin，
告诉我启动这个本地 plugin 的命令。不要启动微信页面。
`

然后按 Claude 给出的路径重新启动 Claude Code：

`powershell
claude --plugin-dir D:\Tools\pineapple-claude-plugin
`

### 第三步：初始化（仅首次）

在新 session 中输入：

`
启用菠萝。请先初始化；需要写入本地工具或安装依赖时，先把计划告诉我，等我确认。
`

Agent 会展示将要写入的内容，**你确认后**才会安装依赖和创建本地工具。不需要管理员权限。

### 第四步：开始使用

`
本次任务启用菠萝控制，打开文件传输助手网页让我登录。
`

扫码登录后，手机微信文件传输助手发 🍍? 即可查询进度。

> 菠萝只在 agent 任务运行期间工作，不会后台常驻。

---

## 日常用法

`
本次任务启用菠萝控制。
进入菠萝设置页。
把菠萝 emoji 改为 🛰️，刷新时间改为 3 秒。
菠萝简介。
`

---

## 技术实现

agent 周期性调用唯一公开主操作 `wechat_tick(status)`，即可查询协议消息、更新状态并发送任务通知。项目采用 MIT License，可审阅、修改和开源分发。

## 边界

这是什么：

- 本地 agent 的极简微信控制面板。
- 仅操作浏览器中登录的官方微信文件传输助手网页界面
  [filehelper.weixin.qq.com](https://filehelper.weixin.qq.com/)。
- agent-active mode：agent 正在运行并调用 tick 时才响应。

这不是什么：

- 不是微信机器人、群聊机器人或多联系人系统。
- 不使用微信协议逆向，不 hook、不注入、不启动 server 或 daemon。
- agent 没运行时，不能从微信启动 agent；未来可单独设计可选 launcher mode。

## 用户指令

默认控制符号为 `🍍`：

```text
🍍？
🍍：不要修改源码，只告诉我粘贴位置
```

输入标点同时接受半角形式 `🍍?` 和 `🍍:内容`；bridge 输出统一使用中文格式。

查询会收到简短状态回复，不产生任务 event。请求/干预会立刻收到：

```text
🍍收到：AI正在处理中。
```

完成或失败会收到：

```text
🍍完成：检查完毕，代码应粘贴到 main.c 第 35 行附近。
🍍完成：任务未完成，原因：没有找到目标文件
```

## 源码安装

下面是开发者或从源码运行的方式。使用上面的 skill/plugin 安装流程时，不需要手动执行这一节的安装命令。

核心协议和 mock 模式没有第三方依赖。官方网页自动化需要 Python Playwright：

```powershell
py -m pip install -e ".[web]"
```

通常不需要管理员权限。网页版登录会话可能在关闭页面时失效，因此推荐让实际
运行中的 agent 首次调用 `wechat_tick()` 打开官方页面，再在该保持打开的页面
中扫码；同一 agent 进程随后的 tick 会复用该页面。

## Python API

agent 只需周期性调用一个公开主函数：

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

状态示例：

```python
wechat_tick({"state": "idle", "progress": "等待任务"})

wechat_tick({
    "state": "done",
    "task": "检查 demo7 作业",
    "result": "检查完毕，代码应粘贴到 main.c 第 35 行附近。",
})

wechat_tick({
    "state": "error",
    "task": "检查 demo7 作业",
    "result": "没有找到目标文件",
})
```

自定义二次回复通过 `outbox` 发送；重复 tick 不会重复发送。需要在不同任务中
重复发送完全相同文本时，请给消息指定唯一 `id`。

```python
wechat_tick({
    "state": "running",
    "task": "检查 demo7 作业",
    "outbox": [
        {"id": "ack-intervention-1", "type": "received",
         "text": "我会只给最小修改方案，不改架构。"}
    ],
})
```

相同完成结果会自动去重；如果两个独立任务可能拥有完全一致的任务名和结果，
在完成状态加入不同的 `notification_id`。

## 配置

配置通过同一次 tick 的 `config` 字段修改并立即持久化：

```python
wechat_tick({
    "state": "running",
    "task": "配置 bridge",
    "config": {"emoji": "🛰️", "check_interval": 3},
})
```

修改后指令和输出立即变为 `🛰️？`、`🛰️：...`、`🛰️收到：...`、`🛰️完成：...`。
`emoji` 接受任意非空字符串。

`check_interval` 仅允许 `3`、`5`、`10` 秒，默认为 `5` 秒。非法值会归一化：

| 输入 | 实际间隔 |
| --- | --- |
| `<= 3` | `3` 秒 |
| `4` 至 `7` | `5` 秒 |
| `>= 8` | `10` 秒 |

默认约 5 秒看到用户请求；3 至 5 秒体验最佳，10 秒为更轻量模式。即使 agent
更频繁调用 tick，真实微信 UI 检查也按该间隔限流。

默认数据目录为 `%LOCALAPPDATA%\wechat-agent-bridge`，也可通过
`WECHAT_AGENT_HOME` 修改。目录中只有轻量本地文件：

- `config.json`：emoji 和检查间隔。
- `runtime.json`：当前状态和去重键。
- `bridge.jsonl`：发送与安全失败日志。
- `browser-profile\`：官方网页运行所使用的专用浏览器 profile。

## CLI API

```powershell
wechat-tick --backend file-mock --status-json status.json
py -m wechat_agent.wechat_tick --backend file-mock --status-json status.json
```

CLI 输出 JSON events，例如：

```json
[{"type": "request", "content": "帮我检查文件", "source": "wechat"}]
```

不用真实微信测试 CLI：

```powershell
New-Item -ItemType Directory -Force .bridge-test | Out-Null
'{"id":"q1","text":"🍍？"}' | Set-Content -Encoding utf8 .bridge-test\mock_inbox.jsonl
py -m wechat_agent.wechat_tick --backend file-mock --storage-dir .bridge-test --status-json status.json
Get-Content .bridge-test\mock_outbox.jsonl
```

真实官方网页必须让页面在前台 agent 进程存活期间保持打开，因此 CLI 使用持续模式：

```powershell
py -m wechat_agent.wechat_tick --backend web --watch --status-json status.json
```

该命令不是后台进程或 server：它是由 agent 持有的前台 bridge 进程。首次出现
官方网页时扫码登录；agent 后续更新 `status.json` 并从标准输出逐行读取 JSON
events。一次启动即退出的 `--backend web` 会被拒绝，因为关闭授权页面后不能
可靠保留网页版会话。

仓库提供可用于人工冒烟验证的 UTF-8 空闲状态文件：

```powershell
py -m wechat_agent.wechat_tick --backend web --watch --status-json examples\status-idle.json
```

## 官方网页后端

默认后端使用 Python Playwright 打开腾讯官方页面
[filehelper.weixin.qq.com](https://filehelper.weixin.qq.com/)，并在专用浏览器
profile 中运行一个可见页面。同一 agent 进程内会复用用户扫码建立的页面会话。
它只从 `#chatBody .msg-text` 读取可见文本，只处理当前 emoji 对应的协议消息
（查询和请求标点兼容全角/半角），并通过
`textarea.chat-panel__input-container` 回复。

如果尚未扫码登录、会话失效、网页结构调整或依赖缺失，bridge 会记录安全失败并
返回 `[]`，不影响 agent 主任务。首次成功读取网页时，bridge 只建立当前可见消息
基线，不回复历史协议文本；之后出现的新指令才会被处理。整个流程不增加 daemon、
server 或后台守护进程。

网页应用在加载和登录过程中会按腾讯官方页面自身行为请求腾讯的静态资源、登录
与文件助手服务域名；bridge 不自行调用微信协议接口，也不将消息发往第三方服务。

已在 Windows 官方网页版上人工验证：同一保持打开的 agent 会话中，连续两次发送
相同的状态查询均会在约 3 秒轮询模式下分别得到状态回复。

已在 Windows 官方网页版上完成一次真实 agent lifecycle 联调：微信侧发布请求后
收到固定确认与自定义确认，运行期间查询得到状态回复，任务结束后收到完成通知。

真实微信联调时，应从保存为 UTF-8 的 Python 模块调用 bridge；不要通过可能使用
本地代码页重编码的 shell 管道内联传递中文或 emoji 测试消息。

跑一次完整的真实生命周期演示：

```powershell
py -B examples\live_demo_agent.py
```

网页登录后发送 `🍍：完整测试`；收到脚本的提示时再发送一次 `🍍？`。演示会验证
固定确认、自定义确认、运行中状态查询和完成通知，并在一次任务完成后自动退出。

## 安全与隐私

- 运行时不截图、不截屏、不使用 OCR，也不读取剪贴板。
- 仅用 Python、Playwright、浏览器 DOM 与本地 JSON/浏览器 profile 实现。
- bridge 仅驱动官方文件传输助手网页界面，不访问微信协议层，不 hook 或 inject
  微信进程，不连接自建服务。
- 网页后端天生只呈现文件传输助手内容，并只接收当前 emoji 对应的协议文本。
- `bridge.jsonl` 仅用于本地 debug，会包含 bridge 发出的协议回复文本；不需要日志时
  可定期清理本地数据目录。

需要明确了解的风险：

- `browser-profile\` 会保存该官方网页的登录会话数据，应按敏感本地数据保护；结束使用后可以退出网页登录并删除该目录。
- 能使用你的微信账户或已登录网页会话的人，也能发送菠萝指令；本 MVP 不额外提供口令或多因素鉴权。
- 微信收到的请求会交给正在运行的 agent 处理。agent 必须继续遵守宿主原有的文件、命令与审批边界，不能因为消息来自菠萝而绕过确认。
- `runtime.json` 和发送日志会保存 agent 主动提供的状态/回复摘要；不要将口令、token 或不需要出现在微信里的敏感正文放入 `status` 或 `outbox`。
- 采用自带脚本时，确认后该源码会在启用 bridge 时运行。bootstrap 固定使用 skill 随附的打包配置，不执行被采用目录中的第三方构建配置。
- 微信网页版结构、登录政策或腾讯服务行为变化时，自动化可能失效；失败时 bridge 返回空事件并保留主任务运行。

## Mock 与测试

内存 `MockBackend` 供 Python 测试使用，文件型 `FileMockBackend` 供 CLI 使用。
二者都会记录 bridge 本应发送的内容，不依赖微信窗口。

运行必测场景：

```powershell
py -m unittest discover -s tests -v
```

覆盖空闲/运行查询、请求和干预、自定义回复、完成与错误通知去重、普通消息忽略、
emoji/间隔修改以及安全失败。

## License

[MIT License](LICENSE)

## Credits

Planted by **GALAXY x Codex** on `2026-05-25`.

## 二阶段 Skill 分发

二阶段遵循“只安装一个 skill，首次启用时创建或复用用户级工具”的原则：

- Codex 安装内容：`skill-package\pineapple\`。
- Claude Code 加载内容：`skill-package\claude-pineapple\` plugin 包装，其中仅包含同一个 `pineapple` skill。
- 共用工具默认位置：`%USERPROFILE%\.pineapple\bridge-tool`。
- skill 首次运行先只读搜索已有兼容工具；找到后报告来源，找不到则询问用户是否有脚本。
- 采用或安装前会先展示写入目录、创建 venv 和依赖安装计划，得到确认后才写入共用目录；最终回退才是安装 skill 内嵌模板。
- 后续 session 只需重新启用 skill，即可发现并复用共用工具。

skill 提供的对话能力：

- `菠萝简介`：返回产品简介、副标题和 slogan，不启动网页。
- `进入菠萝设置页`：显示当前 emoji 与刷新时间，并询问修改哪一项。
- 修改 emoji 或刷新时间：持久保存；刷新时间只允许 `3`、`5`、`10` 秒。
- 工作中启用：由当前 agent 保持官方网页开启，通过 `wechat_tick(status)` 或其 CLI 等价循环收发控制消息。

Codex 本地安装示例：

```powershell
Copy-Item -Recurse -Force skill-package\pineapple "$env:USERPROFILE\.codex\skills\pineapple"
```

Claude Code 本地测试示例：

```powershell
claude --plugin-dir skill-package\claude-pineapple
```

Claude Code 的 plugin 只是其加载 skill 的包装格式，并未增加后台服务或额外产品能力。
