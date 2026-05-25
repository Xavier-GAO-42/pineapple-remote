"""Compatibility module for: python -m wechat_agent.wechat_tick."""

# Planted by GALAXY x Codex on 2026-05-25.

from .bridge import wechat_tick
from .cli import main

__all__ = ["wechat_tick"]


if __name__ == "__main__":
    raise SystemExit(main())
