"""Required MVP scenarios for the WeChat File Transfer Assistant bridge."""

# Planted by GALAXY x Codex on 2026-05-25.

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from wechat_agent.bridge import WechatBridge
from wechat_agent.backends import MockBackend, NullBackend


class BridgeScenarioTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.home = Path(self.temp.name)
        self.backend = MockBackend()
        self.bridge = WechatBridge(self.backend, self.home)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_01_idle_status_query(self) -> None:
        self.backend.receive("🍍？")
        events = self.bridge.tick({"state": "idle", "task": "", "progress": "等待任务"})
        self.assertEqual(events, [])
        self.assertEqual(self.backend.sent, ["🍍收到：我现在空闲，正在等待任务。"])

    def test_02_running_status_query(self) -> None:
        self.backend.receive("🍍？")
        events = self.bridge.tick(
            {"state": "running", "task": "检查作业", "progress": "正在看 main.c"}
        )
        self.assertEqual(events, [])
        self.assertEqual(
            self.backend.sent, ["🍍收到：我正在检查作业，目前正在看 main.c。"]
        )

    def test_03_user_request_is_acked_and_returned(self) -> None:
        self.backend.receive("🍍：帮我检查文件")
        events = self.bridge.tick({"state": "idle"})
        self.assertEqual(
            events,
            [{"type": "request", "content": "帮我检查文件", "source": "wechat"}],
        )
        self.assertEqual(self.backend.sent, ["🍍收到：AI正在处理中。"])

    def test_04_running_intervention_has_no_bridge_semantics(self) -> None:
        self.backend.receive("🍍：不要修改源码")
        events = self.bridge.tick({"state": "running", "task": "编辑代码"})
        self.assertEqual(events[0]["content"], "不要修改源码")
        self.assertEqual(events[0]["type"], "request")
        self.assertEqual(self.backend.sent, ["🍍收到：AI正在处理中。"])

    def test_05_custom_second_reply_is_deduplicated(self) -> None:
        status = {
            "state": "running",
            "task": "检查作业",
            "outbox": [{"type": "received", "text": "我会只给最小修改方案。"}],
        }
        self.bridge.tick(status)
        self.bridge.tick(status)
        self.assertEqual(self.backend.sent, ["🍍收到：我会只给最小修改方案。"])

    def test_06_done_sends_completion(self) -> None:
        self.bridge.tick({"state": "done", "task": "测试", "result": "测试完成"})
        self.assertEqual(self.backend.sent, ["🍍完成：测试完成"])

    def test_07_done_notification_is_deduplicated(self) -> None:
        status = {"state": "done", "task": "测试", "result": "测试完成"}
        self.bridge.tick(status)
        self.bridge.tick(status)
        self.assertEqual(self.backend.sent, ["🍍完成：测试完成"])

    def test_08_error_sends_deduplicated_completion(self) -> None:
        status = {
            "state": "error",
            "task": "检查文件",
            "result": "没有找到目标文件",
        }
        self.bridge.tick(status)
        self.bridge.tick(status)
        self.assertEqual(
            self.backend.sent, ["🍍完成：任务未完成，原因：没有找到目标文件"]
        )

    def test_09_plain_message_is_ignored(self) -> None:
        self.backend.receive("下午把文档发给我")
        events = self.bridge.tick({"state": "idle"})
        self.assertEqual(events, [])
        self.assertEqual(self.backend.sent, [])

    def test_10_configuration_changes_apply_immediately_and_persist(self) -> None:
        self.backend.receive("🍍？", "old-command")
        self.backend.receive("🛰️？", "new-command")
        events = self.bridge.tick(
            {"state": "idle", "config": {"emoji": "🛰️", "check_interval": 3}}
        )
        self.assertEqual(events, [])
        self.assertEqual(self.backend.sent, ["🛰️收到：我现在空闲，正在等待任务。"])
        config = json.loads((self.home / "config.json").read_text(encoding="utf-8"))
        self.assertEqual(config["emoji"], "🛰️")
        self.assertEqual(config["check_interval"], 3)

        self.bridge.tick({"state": "idle", "config": {"check_interval": 2}})
        config = json.loads((self.home / "config.json").read_text(encoding="utf-8"))
        self.assertEqual(config["check_interval"], 3)
        self.bridge.tick({"state": "idle", "config": {"check_interval": 8}})
        config = json.loads((self.home / "config.json").read_text(encoding="utf-8"))
        self.assertEqual(config["check_interval"], 10)

    def test_request_message_id_is_not_processed_twice(self) -> None:
        self.backend.receive("🍍：重复检查", "same-message")
        first = self.bridge.tick({"state": "running"})
        second = self.bridge.tick({"state": "running"})
        self.assertEqual(len(first), 1)
        self.assertEqual(second, [])
        self.assertEqual(self.backend.sent, ["🍍收到：AI正在处理中。"])

    def test_unavailable_backend_keeps_state_and_returns_empty(self) -> None:
        bridge = WechatBridge(NullBackend(), self.home)
        events = bridge.tick({"state": "running", "task": "继续主任务"})
        bridge.tick({"state": "running", "task": "继续主任务"})
        self.assertEqual(events, [])
        runtime = json.loads((self.home / "runtime.json").read_text(encoding="utf-8"))
        self.assertEqual(runtime["current_status"]["task"], "继续主任务")
        logs = (self.home / "bridge.jsonl").read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(logs), 1)

    def test_ascii_query_and_request_punctuation_are_accepted(self) -> None:
        self.backend.receive("🍍?", "ascii-query")
        self.backend.receive("🍍:半角也可以", "ascii-request")
        events = self.bridge.tick({"state": "idle"})
        self.assertEqual(
            events,
            [{"type": "request", "content": "半角也可以", "source": "wechat"}],
        )
        self.assertEqual(
            self.backend.sent,
            ["🍍收到：我现在空闲，正在等待任务。", "🍍收到：AI正在处理中。"],
        )

    def test_package_exports_only_the_agent_tick_operation(self) -> None:
        import wechat_agent

        self.assertEqual(wechat_agent.__all__, ["wechat_tick"])
        self.assertTrue(callable(wechat_agent.wechat_tick))
        self.assertFalse(hasattr(wechat_agent, "WechatBridge"))


if __name__ == "__main__":
    unittest.main()
