"""One-shot live demo agent for the official File Helper web bridge.

Run this file directly from UTF-8 source. It waits for one WeChat request,
keeps a running-state query window open, sends completion, and exits.
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
    parser.add_argument("--wait-request", type=int, default=300)
    parser.add_argument("--running-seconds", type=int, default=15)
    args = parser.parse_args()

    storage_dir = Path(default_storage_dir())
    backend = WebFileHelperBackend(storage_dir, headed=True)
    run_id = uuid.uuid4().hex[:12]
    interval = 3

    idle_status = {
        "state": "idle",
        "task": "",
        "progress": "等待任务",
        "config": {"check_interval": interval},
    }
    print("官方文件传输助手页面已打开。若需要请扫码，然后发送：🍍：完整测试", flush=True)

    try:
        request_deadline = time.monotonic() + args.wait_request
        request_content = ""
        while time.monotonic() < request_deadline:
            events = wechat_tick(
                idle_status, check_interval=interval, backend=backend, storage_dir=storage_dir
            )
            request = next((event for event in events if event["type"] == "request"), None)
            if request:
                request_content = request["content"]
                break
            time.sleep(interval)
        else:
            print("等待测试请求超时，演示结束。", flush=True)
            return 2

        running_status = {
            "state": "running",
            "task": "运行微信 bridge 完整测试",
            "progress": "已收到请求，正在验证处理中状态",
            "outbox": [
                {
                    "id": f"{run_id}-running-instruction",
                    "type": "received",
                    "text": "完整测试已开始，请现在发送 🍍？ 查询处理中状态。",
                }
            ],
        }
        print(f"收到 request event：{request_content}", flush=True)
        running_deadline = time.monotonic() + args.running_seconds
        while time.monotonic() < running_deadline:
            wechat_tick(
                running_status, check_interval=interval, backend=backend, storage_dir=storage_dir
            )
            time.sleep(interval)

        done_status = {
            "state": "done",
            "task": "运行微信 bridge 完整测试",
            "progress": "已完成",
            "result": "完整测试完成：请求、状态查询和完成通知链路已运行。",
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
