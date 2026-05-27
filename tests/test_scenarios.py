"""Required MVP scenarios for the WeChat File Transfer Assistant bridge."""

# Planted by GALAXY x Codex on 2026-05-25.

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from wechat_agent.bridge import WechatBridge
from wechat_agent.backends import MockBackend, NullBackend


class ClosingMockBackend(MockBackend):
    def __init__(self, terminal_settle_seconds: float = 0.0) -> None:
        super().__init__()
        self.closed = False
        self.terminal_settle_seconds = terminal_settle_seconds

    def close(self) -> None:
        self.closed = True


class ManualClock:
    def __init__(self) -> None:
        self.now = 100.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class RejectingClosingBackend(ClosingMockBackend):
    def send_message(self, text: str) -> bool:
        return False


class InitiallyRejectingBackend(MockBackend):
    def __init__(self) -> None:
        super().__init__()
        self.reject = True

    def send_message(self, text: str) -> bool:
        if self.reject:
            return False
        return super().send_message(text)


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
        self.assertEqual(
            self.backend.sent, ["🍍[自动回复]💻👌状态：我现在空闲，正在等待任务。"]
        )

    def test_02_running_status_query(self) -> None:
        self.backend.receive("🍍？")
        events = self.bridge.tick(
            {"state": "running", "task": "检查作业", "progress": "正在看 main.c"}
        )
        self.assertEqual(events, [])
        self.assertEqual(
            self.backend.sent,
            ["🍍[自动回复]💻👌状态：我正在检查作业，目前正在看 main.c。"],
        )

    def test_03_user_request_is_acked_and_returned(self) -> None:
        self.backend.receive("🍍：帮我检查文件")
        events = self.bridge.tick({"state": "idle"})
        self.assertEqual(
            events,
            [{"id": "mock-1", "type": "request", "content": "帮我检查文件", "source": "wechat"}],
        )
        self.assertEqual(
            self.backend.sent, ["🍍[自动回复]💻👌已接收请求，AI正在处理中。"]
        )

    def test_04_running_intervention_has_no_bridge_semantics(self) -> None:
        self.backend.receive("🍍：不要修改源码")
        events = self.bridge.tick({"state": "running", "task": "编辑代码"})
        self.assertEqual(events[0]["content"], "不要修改源码")
        self.assertEqual(events[0]["type"], "request")
        self.assertEqual(
            self.backend.sent, ["🍍[自动回复]💻👌已接收请求，AI正在处理中。"]
        )

    def test_05_custom_second_reply_is_deduplicated(self) -> None:
        status = {
            "state": "running",
            "task": "检查作业",
            "outbox": [{"type": "received", "text": "我会只给最小修改方案。"}],
        }
        self.bridge.tick(status)
        self.bridge.tick(status)
        self.assertEqual(self.backend.sent, ["🍍[AI回复]🤖👌我会只给最小修改方案。"])

    def test_connected_notice_is_an_outbox_message_sent_once(self) -> None:
        status = {
            "run_id": "run-001",
            "state": "running",
            "task": "当前主任务",
            "progress": "菠萝控制已连接，正在开始执行任务",
            "outbox": [
                {
                    "id": "run-001-connected",
                    "type": "received",
                    "text": "菠萝控制已连接。",
                }
            ],
        }
        self.bridge.tick(status)
        self.bridge.tick(status)
        self.assertEqual(self.backend.sent, ["🍍[AI回复]🤖👌菠萝控制已连接。"])

    def test_unsent_outbox_survives_status_overwrite_until_transport_is_ready(self) -> None:
        backend = InitiallyRejectingBackend()
        bridge = WechatBridge(backend, self.home)
        bridge.tick(
            {
                "run_id": "run-pending",
                "state": "running",
                "task": "启动任务",
                "outbox": [
                    {"id": "run-pending-connected", "type": "received", "text": "菠萝控制已连接。"}
                ],
            }
        )
        backend.reject = False
        bridge.tick(
            {
                "run_id": "run-pending",
                "state": "running",
                "task": "启动任务",
                "progress": "已经进入工作阶段",
            }
        )
        self.assertEqual(backend.sent, ["🍍[AI回复]🤖👌菠萝控制已连接。"])

    def test_new_run_id_resets_outbox_dedup_for_reused_status_path(self) -> None:
        for run_id in ("first-run", "second-run"):
            self.bridge.tick(
                {
                    "run_id": run_id,
                    "state": "running",
                    "task": "重用路径测试",
                    "outbox": [
                        {"id": "connected", "type": "received", "text": "菠萝控制已连接。"}
                    ],
                }
            )
        self.assertEqual(
            self.backend.sent,
            ["🍍[AI回复]🤖👌菠萝控制已连接。", "🍍[AI回复]🤖👌菠萝控制已连接。"],
        )

    def test_06_done_sends_completion(self) -> None:
        self.bridge.tick({"state": "done", "task": "测试", "result": "测试完成"})
        self.assertEqual(self.backend.sent, ["🍍[自动回复]💻👌完成：测试完成"])

    def test_terminal_status_closes_task_transport_after_sending(self) -> None:
        backend = ClosingMockBackend()
        bridge = WechatBridge(backend, self.home)
        bridge.tick({"state": "running", "task": "测试", "progress": "进行中"})
        self.assertFalse(backend.closed)
        bridge.tick({"state": "done", "task": "测试", "result": "测试完成"})
        self.assertTrue(backend.closed)
        self.assertEqual(backend.sent, ["🍍[自动回复]💻👌完成：测试完成"])

    def test_terminal_web_settle_window_closes_only_after_delay(self) -> None:
        clock = ManualClock()
        backend = ClosingMockBackend(terminal_settle_seconds=3.0)
        bridge = WechatBridge(backend, self.home, clock=clock)
        status = {
            "state": "done",
            "task": "测试",
            "result": "测试完成",
            "notification_id": "delayed-terminal",
        }
        bridge.tick(status)
        self.assertFalse(backend.closed)
        self.assertTrue(bridge.terminal_notification_sent(status))
        self.assertFalse(bridge.terminal_notification_settled(status))
        self.assertEqual(bridge.terminal_settle_remaining(status), 3.0)
        clock.advance(2.9)
        bridge.tick(status)
        self.assertFalse(backend.closed)
        clock.advance(0.1)
        bridge.tick(status)
        self.assertTrue(backend.closed)
        self.assertEqual(backend.sent, ["🍍[自动回复]💻👌完成：测试完成"])
        logs = (self.home / "bridge.jsonl").read_text(encoding="utf-8")
        self.assertIn('"action": "completion_submitted"', logs)
        self.assertIn('"action": "session_closed_after_settle"', logs)

    def test_terminal_settle_window_does_not_accept_new_requests(self) -> None:
        clock = ManualClock()
        backend = ClosingMockBackend(terminal_settle_seconds=3.0)
        bridge = WechatBridge(backend, self.home, clock=clock)
        status = {"state": "done", "task": "测试", "result": "测试完成"}
        bridge.tick(status)
        backend.receive("🍍：完成后不应接收", "late-steering")
        clock.advance(1.0)
        events = bridge.tick(status)
        self.assertEqual(events, [])
        self.assertEqual(backend.sent, ["🍍[自动回复]💻👌完成：测试完成"])

    def test_terminal_submission_does_not_send_late_outbox_items(self) -> None:
        backend = ClosingMockBackend(terminal_settle_seconds=3.0)
        bridge = WechatBridge(backend, self.home, clock=ManualClock())
        bridge.tick(
            {
                "state": "done",
                "task": "测试",
                "result": "测试完成",
                "outbox": [
                    {"id": "too-late", "type": "received", "text": "不应在结束后补发"}
                ],
            }
        )
        self.assertEqual(backend.sent, ["🍍[自动回复]💻👌完成：测试完成"])

    def test_terminal_send_failure_does_not_close_and_can_retry(self) -> None:
        backend = RejectingClosingBackend(terminal_settle_seconds=3.0)
        bridge = WechatBridge(backend, self.home)
        status = {"state": "done", "task": "测试", "result": "测试完成"}
        bridge.tick(status)
        bridge.tick(status)
        self.assertFalse(backend.closed)
        self.assertFalse(bridge.terminal_notification_sent(status))

    def test_terminal_waits_until_received_request_has_ai_ack(self) -> None:
        self.backend.receive("🍍：请先确认", "pending-terminal")
        self.bridge.tick({"run_id": "pending-terminal-run", "state": "running"})
        terminal = {
            "run_id": "pending-terminal-run",
            "state": "done",
            "task": "测试",
            "result": "测试完成",
            "notification_id": "pending-terminal-done",
            "outbox": [
                {
                    "id": "ack-pending-terminal",
                    "type": "received",
                    "text": "已记入，我会按你的要求继续处理。",
                }
            ],
        }
        self.bridge.tick(terminal)
        self.assertNotIn("🍍[自动回复]💻👌完成：测试完成", self.backend.sent)
        self.bridge.tick(terminal)
        self.assertEqual(
            self.backend.sent,
            [
                "🍍[自动回复]💻👌已接收请求，AI正在处理中。",
                "🍍[AI回复]🤖👌已记入，我会按你的要求继续处理。",
                "🍍[自动回复]💻👌完成：测试完成",
            ],
        )

    def test_07_done_notification_is_deduplicated(self) -> None:
        status = {"state": "done", "task": "测试", "result": "测试完成"}
        self.bridge.tick(status)
        self.bridge.tick(status)
        self.assertEqual(self.backend.sent, ["🍍[自动回复]💻👌完成：测试完成"])
        self.assertTrue(self.bridge.terminal_notification_sent(status))

    def test_08_error_sends_deduplicated_completion(self) -> None:
        status = {
            "state": "error",
            "task": "检查文件",
            "result": "没有找到目标文件",
        }
        self.bridge.tick(status)
        self.bridge.tick(status)
        self.assertEqual(
            self.backend.sent,
            ["🍍[自动回复]💻👌完成：任务未完成，原因：没有找到目标文件"],
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
        self.assertEqual(
            self.backend.sent, ["🛰️[自动回复]💻👌状态：我现在空闲，正在等待任务。"]
        )
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
        self.assertEqual(
            self.backend.sent, ["🍍[自动回复]💻👌已接收请求，AI正在处理中。"]
        )

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
            [{"id": "ascii-request", "type": "request", "content": "半角也可以", "source": "wechat"}],
        )
        self.assertEqual(
            self.backend.sent,
            [
                "🍍[自动回复]💻👌状态：我现在空闲，正在等待任务。",
                "🍍[自动回复]💻👌已接收请求，AI正在处理中。",
            ],
        )

    def test_package_exports_only_the_agent_tick_operation(self) -> None:
        import wechat_agent

        self.assertEqual(wechat_agent.__all__, ["wechat_tick"])
        self.assertTrue(callable(wechat_agent.wechat_tick))
        self.assertFalse(hasattr(wechat_agent, "WechatBridge"))


if __name__ == "__main__":
    unittest.main()
