"""Transport backends: deterministic mocks and official File Helper web UI."""

# Planted by GALAXY x Codex on 2026-05-25.

from __future__ import annotations

import json
import os
import secrets
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol
from urllib.parse import urlparse

from .config import BridgeConfig


class BackendUnavailable(RuntimeError):
    """The selected transport cannot access File Transfer Assistant right now."""


@dataclass(frozen=True)
class IncomingMessage:
    id: str
    text: str


class Backend(Protocol):
    always_poll: bool

    def poll_messages(self, config: BridgeConfig) -> list[IncomingMessage]: ...

    def send_message(self, text: str) -> bool: ...


class NullBackend:
    always_poll = False
    discard_existing_on_first_poll = False

    def poll_messages(self, config: BridgeConfig) -> list[IncomingMessage]:
        raise BackendUnavailable("No WeChat backend is configured.")

    def send_message(self, text: str) -> bool:
        raise BackendUnavailable("No WeChat backend is configured.")


class MockBackend:
    """In-memory backend for tests and embedding experiments."""

    always_poll = True
    discard_existing_on_first_poll = False

    def __init__(self) -> None:
        self._incoming: list[IncomingMessage] = []
        self.sent: list[str] = []
        self._next_id = 1

    def receive(self, text: str, message_id: str | None = None) -> str:
        message_id = message_id or f"mock-{self._next_id}"
        self._next_id += 1
        self._incoming.append(IncomingMessage(message_id, text))
        return message_id

    def poll_messages(self, config: BridgeConfig) -> list[IncomingMessage]:
        return list(self._incoming)

    def send_message(self, text: str) -> bool:
        self.sent.append(text)
        return True


class FileMockBackend:
    """JSONL-backed mock transport, useful with the CLI and without WeChat."""

    always_poll = True
    discard_existing_on_first_poll = False

    def __init__(self, directory: str | Path) -> None:
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.inbox_path = self.directory / "mock_inbox.jsonl"
        self.outbox_path = self.directory / "mock_outbox.jsonl"

    def poll_messages(self, config: BridgeConfig) -> list[IncomingMessage]:
        try:
            lines = self.inbox_path.read_text(encoding="utf-8").splitlines()
        except FileNotFoundError:
            return []
        messages: list[IncomingMessage] = []
        for line_number, line in enumerate(lines, start=1):
            try:
                item = json.loads(line)
                text = str(item["text"])
                message_id = str(item.get("id") or f"file-{line_number}")
            except (json.JSONDecodeError, KeyError, TypeError):
                continue
            messages.append(IncomingMessage(message_id, text))
        return messages

    def send_message(self, text: str) -> bool:
        with self.outbox_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps({"text": text}, ensure_ascii=False) + "\n")
        return True


class WebFileHelperBackend:
    """Python browser automation for the official WeChat File Helper web app.

    It opens only filehelper.weixin.qq.com in a dedicated persistent browser
    profile and reads DOM text. It does not inspect desktop WeChat, take images,
    use OCR, or speak an unofficial WeChat protocol.
    """

    always_poll = False
    discard_existing_on_first_poll = True
    url = "https://filehelper.weixin.qq.com/"
    input_selectors = (
        "textarea.chat-panel__input-container",
        "textarea",
        "[contenteditable='true']",
        "[role='textbox']",
    )
    message_selector = "#chatBody .msg-text"
    ready_selector = ".page-logined textarea.chat-panel__input-container"
    send_button_selector = ".chat-send__button:not(.chat-send__button__disabled)"

    def __init__(
        self,
        storage_dir: str | Path,
        *,
        headed: bool = True,
        browser_channel: str | None = None,
    ) -> None:
        self.profile_dir = Path(storage_dir) / "browser-profile"
        self.profile_dir.mkdir(parents=True, exist_ok=True)
        self.headed = headed
        self.browser_channel = browser_channel or os.environ.get(
            "WECHAT_AGENT_BROWSER_CHANNEL", "msedge"
        )
        self.transport_session_id = secrets.token_hex(8)
        self._playwright_manager: Any | None = None
        self._playwright: Any | None = None
        self._context: Any | None = None
        self._page: Any | None = None

    def _libraries(self) -> Any:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise BackendUnavailable(
                "Install web dependencies with: py -m pip install -e \".[web]\""
            ) from exc
        return sync_playwright

    def _ensure_page(self) -> Any:
        if self._page is not None and not self._page.is_closed():
            return self._page
        sync_playwright = self._libraries()
        try:
            self._playwright_manager = sync_playwright()
            self._playwright = self._playwright_manager.start()
            launch_args: dict[str, Any] = {"headless": not self.headed}
            if self.browser_channel:
                launch_args["channel"] = self.browser_channel
            try:
                self._context = self._playwright.chromium.launch_persistent_context(
                    str(self.profile_dir), **launch_args
                )
            except Exception:
                launch_args.pop("channel", None)
                self._context = self._playwright.chromium.launch_persistent_context(
                    str(self.profile_dir), **launch_args
                )
            self._page = (
                self._context.pages[0] if self._context.pages else self._context.new_page()
            )
            if "filehelper.weixin.qq.com" not in self._page.url:
                self._page.goto(self.url, wait_until="domcontentloaded", timeout=15000)
            self._page.wait_for_timeout(250)
            if urlparse(self._page.url).hostname != "filehelper.weixin.qq.com":
                raise BackendUnavailable(
                    "Official File Helper page redirected outside its expected host."
                )
            return self._page
        except BackendUnavailable:
            raise
        except Exception as exc:
            raise BackendUnavailable(f"Cannot operate official File Helper web UI: {exc}") from exc

    def _run_with_page(self, action: Any) -> Any:
        return action(self._ensure_page())

    def close(self) -> None:
        if self._context is not None:
            self._context.close()
        if self._playwright is not None:
            self._playwright.stop()
        self._page = None
        self._context = None
        self._playwright = None
        self._playwright_manager = None

    def _visible_input(self, page: Any) -> Any | None:
        for selector in self.input_selectors:
            locator = page.locator(selector)
            for index in range(locator.count() - 1, -1, -1):
                candidate = locator.nth(index)
                if candidate.is_visible():
                    return candidate
        return None

    def _require_logged_in(self, page: Any) -> None:
        if page.locator(self.ready_selector).count() == 0 or self._visible_input(page) is None:
            raise BackendUnavailable(
                "File Helper web session is not ready; keep the agent session open and scan the QR code."
            )

    def poll_messages(self, config: BridgeConfig) -> list[IncomingMessage]:
        def read(page: Any) -> list[IncomingMessage]:
            self._require_logged_in(page)
            queries = set(config.query_commands())
            request_prefixes = config.request_prefixes()
            items = page.locator(self.message_selector).evaluate_all(
                """elements => {
                    window.__wechatAgentMessageSeq = window.__wechatAgentMessageSeq || 0;
                    return elements.map(element => {
                        if (!element.dataset.wechatAgentMessageId) {
                            window.__wechatAgentMessageSeq += 1;
                            element.dataset.wechatAgentMessageId =
                                String(window.__wechatAgentMessageSeq);
                        }
                        return {
                            id: element.dataset.wechatAgentMessageId,
                            text: (element.innerText || '').trim()
                        };
                    });
                }"""
            )
            messages: list[IncomingMessage] = []
            for item in items:
                text = item["text"]
                if text not in queries and not any(
                    text.startswith(prefix) for prefix in request_prefixes
                ):
                    continue
                messages.append(
                    IncomingMessage(
                        f"web-{self.transport_session_id}-dom-{item['id']}", text
                    )
                )
            return messages

        return self._run_with_page(read)

    def send_message(self, text: str) -> bool:
        def send(page: Any) -> bool:
            self._require_logged_in(page)
            editor = self._visible_input(page)
            if editor is None:
                raise BackendUnavailable("File Helper message input was not found.")
            before = page.locator(self.message_selector).count()
            editor.click()
            editor.fill(text)
            button = page.locator(self.send_button_selector).last
            if button.count() and button.is_visible():
                button.click()
            else:
                editor.press("Enter")
            try:
                page.wait_for_function(
                    """({selector, before}) =>
                        document.querySelectorAll(selector).length > before""",
                    arg={"selector": self.message_selector, "before": before},
                    timeout=3000,
                )
            except Exception as exc:
                raise BackendUnavailable(
                    "File Helper did not show the sent message in its message list."
                ) from exc
            return True

        return bool(self._run_with_page(send))
