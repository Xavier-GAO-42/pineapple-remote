"""CLI behavior checks for Pineapple."""

# Planted by GALAXY x Codex on 2026-05-25.

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


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
                [{"type": "request", "content": "CLI 请求", "source": "wechat"}],
            )
            sent = [
                json.loads(line)["text"]
                for line in (directory / "mock_outbox.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
            ]
            self.assertEqual(sent, ["🍍收到：AI正在处理中。"])

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
            self.assertEqual(sent, ["🍍完成：任务已经完成"])


if __name__ == "__main__":
    unittest.main()
