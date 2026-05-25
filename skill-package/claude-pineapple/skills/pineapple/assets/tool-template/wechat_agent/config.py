"""Bridge configuration and interval normalization."""

# Planted by GALAXY x Codex on 2026-05-25.

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping


ALLOWED_CHECK_INTERVALS = (3, 5, 10)


def normalize_check_interval(value: Any) -> int:
    """Return the nearest supported interval using the documented buckets."""
    try:
        seconds = float(value)
    except (TypeError, ValueError):
        return 5
    if seconds <= 3:
        return 3
    if seconds <= 7:
        return 5
    return 10


@dataclass
class BridgeConfig:
    emoji: str = "🍍"
    query_suffix: str = "？"
    request_suffix: str = "："
    received_prefix: str = "收到："
    done_prefix: str = "完成："
    auto_ack_text: str = "AI正在处理中。"
    check_interval: int = 5
    allowed_check_intervals: tuple[int, ...] = ALLOWED_CHECK_INTERVALS

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any] | None) -> "BridgeConfig":
        config = cls()
        if not raw:
            return config
        emoji = raw.get("emoji")
        if isinstance(emoji, str) and emoji.strip():
            config.emoji = emoji
        config.check_interval = normalize_check_interval(
            raw.get("check_interval", config.check_interval)
        )
        return config

    def update(self, changes: Mapping[str, Any] | None) -> bool:
        if not changes:
            return False
        before = self.to_dict()
        emoji = changes.get("emoji")
        if isinstance(emoji, str) and emoji.strip():
            self.emoji = emoji
        if "check_interval" in changes:
            self.check_interval = normalize_check_interval(changes["check_interval"])
        return before != self.to_dict()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["allowed_check_intervals"] = list(self.allowed_check_intervals)
        return data

    def query_commands(self) -> tuple[str, ...]:
        suffixes = dict.fromkeys((self.query_suffix, "？", "?"))
        return tuple(f"{self.emoji}{suffix}" for suffix in suffixes)

    def request_prefixes(self) -> tuple[str, ...]:
        suffixes = dict.fromkeys((self.request_suffix, "：", ":"))
        return tuple(f"{self.emoji}{suffix}" for suffix in suffixes)
