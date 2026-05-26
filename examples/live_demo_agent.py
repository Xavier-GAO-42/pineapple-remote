"""One-shot active-task demo for the official File Helper web bridge.

Run this file directly from UTF-8 source. The main task starts immediately,
allows query or steering while active, sends completion, and exits.
"""

# Planted by GALAXY x Codex on 2026-05-25.

from __future__ import annotations

import argparse
import sys
import time
import uuid
from pathlib import Path

from wechat_agent import wechat_tick
from wechat_agent.backends import WebFileHelperBackend
from wechat_agent.storage import default_storage_dir


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Run one live WeChat bridge demo task.")
    parser.add_argument("--running-seconds", type=int, default=20)
    args = parser.parse_args()

    storage_dir = Path(default_storage_dir())
    backend = WebFileHelperBackend(storage_dir, headed=True)
    run_id = uuid.uuid4().hex[:12]
    interval = 3

    try:
        running_status = {
            "state": "running",
            "task": "运行菠萝伴随主任务演示",
            "progress": "菠萝控制已连接，正在验证运行中状态",
            "config": {"check_interval": interval},
            "outbox": [
                {
                    "id": f"{run_id}-connected",
                    "type": "received",
                    "text": "菠萝控制已连接。",
                }
            ],
        }
        print("官方文件传输助手页面已打开。请为本次任务扫码，并发送 🍍？ 查询进度。", flush=True)
        running_deadline = time.monotonic() + args.running_seconds
        while time.monotonic() < running_deadline:
            events = wechat_tick(
                running_status, check_interval=interval, backend=backend, storage_dir=storage_dir
            )
            for event in events:
                if event["type"] == "request":
                    print(f"收到 steering event：{event['content']}", flush=True)
            time.sleep(interval)

        done_status = {
            "state": "done",
            "task": "运行菠萝伴随主任务演示",
            "progress": "已完成",
            "result": "演示完成：连接通知、状态查询和完成通知链路已运行。",
            "notification_id": f"{run_id}-done",
        }
        wechat_tick(
            done_status, check_interval=interval, backend=backend, storage_dir=storage_dir
        )
        print("完成通知已发送，演示结束。", flush=True)
        return 0
    finally:
        backend.close()


if __name__ == "__main__":
    raise SystemExit(main())
