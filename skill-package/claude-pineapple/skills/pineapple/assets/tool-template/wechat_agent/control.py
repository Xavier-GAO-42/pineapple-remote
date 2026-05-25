"""Product information and local configuration management for Pineapple."""

# Planted by GALAXY x Codex on 2026-05-25.

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .config import BridgeConfig
from .storage import JsonStore


PRODUCT_NAME = "菠萝 Pineapple"
PRODUCT_DESCRIPTION = "用微信文件传输助手，远程监控和干预你的 AI agent。"
PRODUCT_SUBTITLE = (
    "电脑上 agent 在跑任务，你可以直接用手机微信发送 🍍? 查进度，"
    "用 🍍：xxx 追加要求。任务完成后，结果自动发回文件传输助手。"
)
PRODUCT_SLOGAN = "把微信文件传输助手变成 AI agent 的随身遥控器。"


def product_info() -> dict[str, str]:
    return {
        "name": PRODUCT_NAME,
        "description": PRODUCT_DESCRIPTION,
        "subtitle": PRODUCT_SUBTITLE,
        "slogan": PRODUCT_SLOGAN,
    }


def load_config(storage_dir: str | Path | None = None) -> BridgeConfig:
    store = JsonStore(storage_dir)
    return BridgeConfig.from_mapping(store.load_json(store.config_path, {}))


def update_config(
    changes: dict[str, Any], storage_dir: str | Path | None = None
) -> BridgeConfig:
    store = JsonStore(storage_dir)
    config = BridgeConfig.from_mapping(store.load_json(store.config_path, {}))
    config.update(changes)
    store.save_json(store.config_path, config.to_dict())
    return config


def _setting_payload(config: BridgeConfig) -> dict[str, Any]:
    return {
        "emoji": config.emoji,
        "check_interval": config.check_interval,
        "allowed_check_intervals": list(config.allowed_check_intervals),
    }


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="View or update Pineapple settings.")
    parser.add_argument("--storage-dir", help="Override Pineapple local state directory.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("info", help="Print Pineapple product information as JSON.")
    subparsers.add_parser("settings", help="Print current emoji and interval as JSON.")
    configure = subparsers.add_parser("configure", help="Update local settings.")
    configure.add_argument("--emoji")
    configure.add_argument("--check-interval", type=int)
    args = parser.parse_args(argv)

    if args.command == "info":
        print(json.dumps(product_info(), ensure_ascii=False))
        return 0
    if args.command == "settings":
        print(json.dumps(_setting_payload(load_config(args.storage_dir)), ensure_ascii=False))
        return 0
    changes: dict[str, Any] = {}
    if args.emoji is not None:
        changes["emoji"] = args.emoji
    if args.check_interval is not None:
        changes["check_interval"] = args.check_interval
    print(json.dumps(_setting_payload(update_config(changes, args.storage_dir)), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
