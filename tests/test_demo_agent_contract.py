"""Live demo source-contract checks for Pineapple."""

# Planted by GALAXY x Codex on 2026-05-25.

from __future__ import annotations

import unittest
from pathlib import Path


class DemoAgentContractTests(unittest.TestCase):
    def test_demo_is_utf8_source_and_contains_protocol_lifecycle(self) -> None:
        source = (
            Path(__file__).parents[1] / "examples" / "live_demo_agent.py"
        ).read_text(encoding="utf-8")
        self.assertIn("wechat_tick", source)
        self.assertIn('"state": "running"', source)
        self.assertIn('"state": "done"', source)
        self.assertIn('"run_id": run_id', source)
        self.assertIn("菠萝控制已连接。", source)
        self.assertIn('f"ack-{event[\'id\']}"', source)
        self.assertIn("🍍？", source)
        self.assertNotIn("等待测试请求", source)


if __name__ == "__main__":
    unittest.main()
