"""CLI behavior checks for Pineapple."""

# Planted by GALAXY x Codex on 2026-05-25.

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from wechat_agent.cli import _acquire_watch_lock, _append_requests, _runtime_dir_for_status


class CliTests(unittest.TestCase):
    def test_file_mock_cli_returns_request_and_records_ack(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            status_path = directory / "status.json"
            status_path.write_text(
                json.dumps({"state": "running", "task": "CLI 测试"}, ensure_ascii=False),
                encoding="utf-8",
            )
            (directory / "mock_inbox.jsonl").write_text(
                json.dumps({"id": "request-1", "text": "🍍：CLI 请求"}, ensure_ascii=False)
                + "\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    "-m",
                    "wechat_agent.wechat_tick",
                    "--backend",
                    "file-mock",
                    "--storage-dir",
                    str(directory),
                    "--status-json",
                    str(status_path),
                ],
                cwd=Path(__file__).parents[1],
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=True,
            )
            self.assertEqual(
                json.loads(result.stdout),
                [{"id": "request-1", "type": "request", "content": "CLI 请求", "source": "wechat"}],
            )
            sent = [
                json.loads(line)["text"]
                for line in (directory / "mock_outbox.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
            ]
            self.assertEqual(sent, ["🍍[自动回复]💻👌已接收请求，AI正在处理中。"])

    def test_watch_mailbox_appends_request_events_in_order(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            status_path = Path(temporary) / "status.json"
            _append_requests(
                str(status_path),
                [
                    {"id": "r1", "type": "request", "content": "第一条", "source": "wechat"},
                    {"id": "r2", "type": "request", "content": "第二条", "source": "wechat"},
                ],
            )
            _append_requests(
                str(status_path),
                [{"id": "r1", "type": "request", "content": "第一条", "source": "wechat"}],
            )
            mailbox = [
                json.loads(line)
                for line in (Path(temporary) / "requests.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
            ]
            self.assertEqual([event["id"] for event in mailbox], ["r1", "r2"])

    def test_watch_mailbox_preserves_dedup_if_one_line_is_malformed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            status_path = Path(temporary) / "status.json"
            mailbox_path = Path(temporary) / "requests.jsonl"
            mailbox_path.write_text(
                '{"id":"r1","type":"request","content":"第一条","source":"wechat"}\n'
                "not-json\n",
                encoding="utf-8",
            )
            _append_requests(
                str(status_path),
                [
                    {"id": "r1", "type": "request", "content": "第一条", "source": "wechat"},
                    {"id": "r2", "type": "request", "content": "第二条", "source": "wechat"},
                ],
            )
            events = [
                json.loads(line)
                for line in mailbox_path.read_text(encoding="utf-8").splitlines()
                if line.startswith("{")
            ]
            self.assertEqual([event["id"] for event in events], ["r1", "r2"])

    def test_default_watch_runtime_is_scoped_to_status_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            first = _runtime_dir_for_status(str(Path(temporary) / "first.json"))
            second = _runtime_dir_for_status(str(Path(temporary) / "second.json"))
            self.assertEqual(first, Path(temporary) / ".first.pineapple-runtime")
            self.assertEqual(second, Path(temporary) / ".second.pineapple-runtime")
            self.assertNotEqual(first, second)

    def test_duplicate_watch_helper_is_rejected_for_same_status(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            runtime_dir = Path(temporary) / ".status.pineapple-runtime"
            lock_path = _acquire_watch_lock(runtime_dir)
            try:
                with self.assertRaisesRegex(ValueError, "already active"):
                    _acquire_watch_lock(runtime_dir)
            finally:
                if lock_path is not None:
                    lock_path.unlink()

    def test_web_cli_requires_foreground_watch_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            status_path = Path(temporary) / "status.json"
            status_path.write_text('{"state":"idle"}', encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    "-m",
                    "wechat_agent.wechat_tick",
                    "--backend",
                    "web",
                    "--status-json",
                    str(status_path),
                ],
                cwd=Path(__file__).parents[1],
                text=True,
                encoding="utf-8",
                capture_output=True,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("--watch", result.stderr)

    def test_watch_exits_after_terminal_notification_is_sent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            status_path = directory / "status.json"
            status_path.write_text(
                json.dumps(
                    {
                        "state": "done",
                        "task": "生命周期测试",
                        "result": "任务已经完成",
                        "notification_id": "lifecycle-done",
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8-sig",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    "-m",
                    "wechat_agent.wechat_tick",
                    "--backend",
                    "file-mock",
                    "--watch",
                    "--storage-dir",
                    str(directory),
                    "--status-json",
                    str(status_path),
                ],
                cwd=Path(__file__).parents[1],
                text=True,
                encoding="utf-8",
                capture_output=True,
                timeout=5,
                check=True,
            )
            self.assertEqual(json.loads(result.stdout), [])
            sent = [
                json.loads(line)["text"]
                for line in (directory / "mock_outbox.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
            ]
            self.assertEqual(sent, ["🍍[自动回复]💻👌完成：任务已经完成"])


if __name__ == "__main__":
    unittest.main()
