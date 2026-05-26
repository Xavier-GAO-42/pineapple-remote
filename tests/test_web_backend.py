"""Official webpage DOM-adapter checks for Pineapple."""

# Planted by GALAXY x Codex on 2026-05-25.

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from wechat_agent.bridge import WechatBridge
from wechat_agent.backends import WebFileHelperBackend
from wechat_agent.config import BridgeConfig

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None


SANITIZED_LOGGED_IN_HTML = """<!doctype html>
<html lang="zh-CN">
<body>
  <div class="page-logined">
    <div id="chatBody">
      <div class="msg-text">🍍?</div>
      <div class="msg-text">🍍：本地 DOM 测试</div>
      <div class="msg-text">普通消息</div>
    </div>
    <textarea class="chat-panel__input-container"></textarea>
    <a class="chat-send__button chat-send__button__disabled">发送</a>
  </div>
  <script>
    const input = document.querySelector('.chat-panel__input-container');
    const button = document.querySelector('.chat-send__button');
    input.addEventListener('input', () => {
      button.classList.toggle('chat-send__button__disabled', !input.value);
    });
    button.addEventListener('click', () => {
      if (!input.value) return;
      const message = document.createElement('div');
      message.className = 'msg-text';
      message.innerText = input.value;
      document.querySelector('#chatBody').appendChild(message);
      input.value = '';
      button.classList.add('chat-send__button__disabled');
    });
  </script>
</body>
</html>"""


class PageBoundWebBackend(WebFileHelperBackend):
    always_poll = True

    def __init__(self, directory: Path, page: object) -> None:
        super().__init__(directory, headed=False)
        self.page = page

    def _run_with_page(self, action: object) -> object:
        return action(self.page)


@unittest.skipUnless(sync_playwright, "Playwright web dependency is not installed")
class WebDomSelectorTests(unittest.TestCase):
    def test_web_backend_profile_is_task_local_and_cleaned_on_close(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            first = WebFileHelperBackend(Path(temporary), headed=False)
            second = WebFileHelperBackend(Path(temporary), headed=False)
            first_profile = first.profile_dir
            second_profile = second.profile_dir
            self.assertNotEqual(first_profile, second_profile)
            self.assertTrue(first_profile.exists())
            self.assertTrue(second_profile.exists())
            prior_session_id = first.transport_session_id
            first.close()
            second.close()
            self.assertFalse(first_profile.exists())
            self.assertFalse(second_profile.exists())
            self.assertNotEqual(first.transport_session_id, prior_session_id)
            first._new_session_profile()
            self.assertNotEqual(first.profile_dir, first_profile)
            first.close()

    def test_logged_in_dom_protocol_read_and_send(self) -> None:
        with tempfile.TemporaryDirectory() as temporary, sync_playwright() as playwright:
            try:
                browser = playwright.chromium.launch(channel="msedge", headless=True)
            except Exception as exc:
                self.skipTest(f"Microsoft Edge is unavailable for DOM test: {exc}")
            try:
                page = browser.new_page()
                page.set_content(SANITIZED_LOGGED_IN_HTML)
                backend = PageBoundWebBackend(Path(temporary), page)
                messages = backend.poll_messages(BridgeConfig())
                self.assertEqual([message.text for message in messages], ["🍍?", "🍍：本地 DOM 测试"])
                self.assertTrue(backend.send_message("🍍收到：本地发送验证。"))
                self.assertEqual(
                    page.locator("#chatBody .msg-text").last.inner_text(),
                    "🍍收到：本地发送验证。",
                )
            finally:
                browser.close()

    def test_first_web_poll_baselines_historical_protocol_messages(self) -> None:
        with tempfile.TemporaryDirectory() as temporary, sync_playwright() as playwright:
            try:
                browser = playwright.chromium.launch(channel="msedge", headless=True)
            except Exception as exc:
                self.skipTest(f"Microsoft Edge is unavailable for DOM test: {exc}")
            try:
                page = browser.new_page()
                page.set_content(SANITIZED_LOGGED_IN_HTML)
                backend = PageBoundWebBackend(Path(temporary), page)
                bridge = WechatBridge(backend, temporary)
                self.assertEqual(bridge.tick({"state": "idle"}), [])
                self.assertEqual(page.locator("#chatBody .msg-text").count(), 3)
                page.evaluate(
                    """() => {
                        const item = document.createElement('div');
                        item.className = 'msg-text';
                        item.innerText = '🍍？';
                        document.querySelector('#chatBody').appendChild(item);
                    }"""
                )
                self.assertEqual(bridge.tick({"state": "idle"}), [])
                self.assertEqual(
                    page.locator("#chatBody .msg-text").last.inner_text(),
                    "🍍收到：我现在空闲，正在等待任务。",
                )
                page.evaluate(
                    """() => {
                        const item = document.createElement('div');
                        item.className = 'msg-text';
                        item.innerText = '🍍？';
                        document.querySelector('#chatBody').appendChild(item);
                    }"""
                )
                self.assertEqual(bridge.tick({"state": "idle"}), [])
                self.assertEqual(
                    page.locator("#chatBody .msg-text").last.inner_text(),
                    "🍍收到：我现在空闲，正在等待任务。",
                )
                replies = page.locator("#chatBody .msg-text").evaluate_all(
                    "elements => elements.map(element => element.innerText).filter(text => text.startsWith('🍍收到'))"
                )
                self.assertEqual(len(replies), 2)
            finally:
                browser.close()


if __name__ == "__main__":
    unittest.main()
