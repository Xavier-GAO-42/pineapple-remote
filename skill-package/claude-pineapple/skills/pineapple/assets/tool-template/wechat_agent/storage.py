"""Small local JSON persistence for Pineapple status and deduplication."""

# Planted by GALAXY x Codex on 2026-05-25.

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def default_storage_dir() -> Path:
    override = os.environ.get("WECHAT_AGENT_HOME")
    if override:
        return Path(override).expanduser()
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / "wechat-agent-bridge"
    return Path.home() / ".wechat-agent-bridge"


class JsonStore:
    def __init__(self, directory: str | Path | None = None) -> None:
        self.directory = Path(directory) if directory else default_storage_dir()
        self.directory.mkdir(parents=True, exist_ok=True)
        self.config_path = self.directory / "config.json"
        self.runtime_path = self.directory / "runtime.json"
        self.log_path = self.directory / "bridge.jsonl"
        self.interrupt_flag_path = self.directory / "interrupt.flag"

    def load_json(self, path: Path, default: dict[str, Any]) -> dict[str, Any]:
        try:
            with path.open("r", encoding="utf-8") as stream:
                data = json.load(stream)
            return data if isinstance(data, dict) else dict(default)
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return dict(default)

    def save_json(self, path: Path, data: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(
            dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump(data, stream, ensure_ascii=False, indent=2)
                stream.write("\n")
            os.replace(temp_name, path)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)

    def log(self, action: str, **fields: Any) -> None:
        record = {
            "time": datetime.now(timezone.utc).isoformat(),
            "action": action,
            **fields,
        }
        try:
            with self.log_path.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(record, ensure_ascii=False) + "\n")
        except OSError:
            pass
