# Command: Pineapple Settings (CLI)

**Result**: Current settings displayed, or configuration updated.

## Read Settings

```powershell
<bridge-python> -m wechat_agent.control settings
```

Reply in this **fixed format**:

```
菠萝设置
当前 emoji：<emoji>
刷新时间：<seconds> 秒
要修改 emoji 还是刷新时间？
```

## Change Settings

```powershell
<bridge-python> -m wechat_agent.control configure --emoji 🛰️ --check-interval 3
```

Allowed intervals: `3`, `5`, `10` seconds. Other values normalize to the nearest bucket.
Changes persist immediately to disk and apply on the next watch loop.
