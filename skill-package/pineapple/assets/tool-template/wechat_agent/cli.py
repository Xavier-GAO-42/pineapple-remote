"""Command line entry point for agents unable to import Python modules."""

# Planted by GALAXY x Codex on 2026-05-25.

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

from .backends import FileMockBackend, NullBackend, WebFileHelperBackend
from .bridge import WechatBridge
from .config import BridgeConfig
from .storage import default_storage_dir


def _read_status(path: str) -> dict[str, Any]:
    if path == "-":
        data = json.load(sys.stdin)
    else:
        with Path(path).open("r", encoding="utf-8") as stream:
            data = json.load(stream)
    if not isinstance(data, dict):
        raise ValueError("status JSON must contain an object")
    return data


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Run one WeChat agent bridge tick.")
    parser.add_argument("--status-json", required=True, help="Status JSON path, or - for stdin.")
    parser.add_argument("--storage-dir", help="Override local JSON state directory.")
    parser.add_argument("--check-interval", type=int, help="Requested 3/5/10 second mode.")
    parser.add_argument(
        "--backend",
        choices=("web", "file-mock", "null"),
        default="web",
        help="Transport backend; file-mock is intended for local testing.",
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Keep one foreground web session open and emit one JSON events line per tick.",
    )
    args = parser.parse_args(argv)
    if args.backend == "web" and not args.watch:
        parser.error(
            "the web backend requires --watch so the authorized official page remains open; "
            "use the Python API for in-process ticks"
        )
    try:
        storage_dir = args.storage_dir or str(default_storage_dir())
        if args.backend == "file-mock":
            backend = FileMockBackend(storage_dir)
        elif args.backend == "null":
            backend = NullBackend()
        else:
            backend = WebFileHelperBackend(storage_dir)
        bridge = WechatBridge(backend, storage_dir)
        try:
            if args.watch:
                while True:
                    status = _read_status(args.status_json)
                    events = bridge.tick(status, args.check_interval)
                    print(json.dumps(events, ensure_ascii=False), flush=True)
                    if bridge.terminal_notification_sent(status):
                        return 0
                    config = BridgeConfig.from_mapping(
                        bridge.store.load_json(bridge.store.config_path, {})
                    )
                    time.sleep(config.check_interval)
            status = _read_status(args.status_json)
            events = bridge.tick(status, args.check_interval)
            print(json.dumps(events, ensure_ascii=False), flush=True)
            return 0
        finally:
            close = getattr(backend, "close", None)
            if callable(close):
                close()
    except KeyboardInterrupt:
        return 130
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
