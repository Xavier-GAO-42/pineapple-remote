# Command: Pineapple Settings

**Result**: Current settings displayed, or configuration updated.

## Read Settings

```python
from wechat_agent import wechat_tick
from wechat_agent.storage import JsonStore
from wechat_agent.config import BridgeConfig

store = JsonStore()
config = BridgeConfig.from_mapping(store.load_json(store.config_path, {}))
```

Reply in this **fixed format**:

```
菠萝设置
当前 emoji：<emoji>
刷新时间：<seconds> 秒
要修改 emoji 还是刷新时间？
```

## Change Settings

Pass `config` inside a tick call:

```python
wechat_tick({
    "state": "idle",
    "task": "configure",
    "config": {"emoji": "🛰️", "check_interval": 3},
})
```

Allowed intervals: `3`, `5`, `10` seconds. Other values normalize to the nearest bucket.
Changes persist to disk and apply to the next active loop.
