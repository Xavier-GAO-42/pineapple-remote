"""Settings and product-copy checks for Pineapple."""

# Planted by GALAXY x Codex on 2026-05-25.

from __future__ import annotations

import tempfile
import unittest

from wechat_agent.control import product_info, load_config, update_config


class ControlTests(unittest.TestCase):
    def test_product_info_matches_pineapple_copy(self) -> None:
        info = product_info()
        self.assertEqual(info["name"], "菠萝 Pineapple")
        self.assertIn("微信文件传输助手", info["description"])
        self.assertIn("随身遥控器", info["slogan"])

    def test_settings_can_change_emoji_and_normalize_interval_without_page(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            changed = update_config({"emoji": "🛰️", "check_interval": 8}, temporary)
            self.assertEqual(changed.emoji, "🛰️")
            self.assertEqual(changed.check_interval, 10)
            loaded = load_config(temporary)
            self.assertEqual(loaded.emoji, "🛰️")
            self.assertEqual(loaded.check_interval, 10)


if __name__ == "__main__":
    unittest.main()
