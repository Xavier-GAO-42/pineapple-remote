"""Public single-tick API and protocol processing."""

# Planted by GALAXY x Codex on 2026-05-25.

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Mapping

from .backends import (
    Backend,
    BackendUnavailable,
    FileMockBackend,
    NullBackend,
    WebFileHelperBackend,
)
from .config import BridgeConfig
from .storage import JsonStore


MAX_DEDUP_KEYS = 500
_DEFAULT_WEB_BACKENDS: dict[str, WebFileHelperBackend] = {}


def _fingerprint(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _remember(items: list[str], value: str) -> None:
    if value not in items:
        items.append(value)
    if len(items) > MAX_DEDUP_KEYS:
        del items[:-MAX_DEDUP_KEYS]


def _sentence(text: str) -> str:
    text = text.strip()
    return text if text.endswith(("。", "！", "？", ".", "!", "?")) else text + "。"


class WechatBridge:
    """Run one bridge iteration against one selected transport backend."""

    def __init__(
        self,
        backend: Backend | None = None,
        storage_dir: str | Path | None = None,
        clock: Any = time.time,
    ) -> None:
        self.store = JsonStore(storage_dir)
        self.backend = backend or WebFileHelperBackend(self.store.directory)
        self.clock = clock

    def tick(
        self, status: Mapping[str, Any] | None, check_interval: int | None = None
    ) -> list[dict[str, str]]:
        status_dict = dict(status or {})
        config = BridgeConfig.from_mapping(
            self.store.load_json(self.store.config_path, {})
        )
        changed = config.update(status_dict.get("config"))
        if check_interval is not None:
            changed = config.update({"check_interval": check_interval}) or changed
        if changed or not self.store.config_path.exists():
            self.store.save_json(self.store.config_path, config.to_dict())

        runtime = self.store.load_json(
            self.store.runtime_path,
            {
                "handled_messages": [],
                "sent_completions": [],
                "sent_outbox": [],
                "last_check_at": 0.0,
                "transport_initialized": False,
                "transport_session_id": None,
                "last_backend_error": None,
            },
        )
        runtime.setdefault("handled_messages", [])
        runtime.setdefault("sent_completions", [])
        runtime.setdefault("sent_outbox", [])
        runtime.setdefault("last_check_at", 0.0)
        runtime.setdefault("transport_initialized", False)
        runtime.setdefault("transport_session_id", None)
        runtime.setdefault("last_backend_error", None)
        transport_session_id = getattr(self.backend, "transport_session_id", None)
        if (
            getattr(self.backend, "discard_existing_on_first_poll", False)
            and transport_session_id
            and runtime["transport_session_id"] != transport_session_id
        ):
            runtime["transport_initialized"] = False
            runtime["transport_session_id"] = transport_session_id
        runtime["current_status"] = status_dict
        runtime["updated_at"] = self.clock()
        self.store.save_json(self.store.runtime_path, runtime)

        events: list[dict[str, str]] = []
        self._send_lifecycle_notification(status_dict, config, runtime)
        self._send_outbox(status_dict, config, runtime)

        due = (
            getattr(self.backend, "always_poll", False)
            or self.clock() - float(runtime["last_check_at"]) >= config.check_interval
        )
        if due:
            try:
                messages = self.backend.poll_messages(config)
                runtime["last_backend_error"] = None
                runtime["last_check_at"] = self.clock()
                if (
                    getattr(self.backend, "discard_existing_on_first_poll", False)
                    and not runtime["transport_initialized"]
                ):
                    for message in messages:
                        _remember(runtime["handled_messages"], message.id)
                    runtime["transport_initialized"] = True
                    messages = []
                else:
                    runtime["transport_initialized"] = True
                for message in messages:
                    if message.id in runtime["handled_messages"]:
                        continue
                    _remember(runtime["handled_messages"], message.id)
                    event = self._handle_incoming(message.text.strip(), config, status_dict)
                    if event:
                        events.append(event)
            except BackendUnavailable as exc:
                error = str(exc)
                if runtime["last_backend_error"] != error:
                    self.store.log("backend_unavailable", error=error)
                    runtime["last_backend_error"] = error
            except Exception as exc:
                self.store.log("backend_error", error=str(exc))

        self.store.save_json(self.store.runtime_path, runtime)
        if self.terminal_notification_sent(status_dict):
            close = getattr(self.backend, "close", None)
            if callable(close):
                close()
        return events

    def _safe_send(self, text: str, action: str) -> bool:
        try:
            sent = self.backend.send_message(text)
        except BackendUnavailable as exc:
            self.store.log("send_unavailable", message_type=action, error=str(exc))
            return False
        except Exception as exc:
            self.store.log("send_error", message_type=action, error=str(exc))
            return False
        if sent:
            self.store.log("sent", message_type=action, text=text)
            return True
        return False

    def _handle_incoming(
        self, text: str, config: BridgeConfig, status: Mapping[str, Any]
    ) -> dict[str, str] | None:
        if text in config.query_commands():
            reply = f"{config.emoji}{config.received_prefix}{format_status(status)}"
            self._safe_send(reply, "status_reply")
            return None
        for prefix in config.request_prefixes():
            if text.startswith(prefix) and text[len(prefix) :].strip():
                ack = f"{config.emoji}{config.received_prefix}{config.auto_ack_text}"
                self._safe_send(ack, "auto_ack")
                try:
                    self.store.interrupt_flag_path.write_text("", encoding="utf-8")
                except OSError:
                    pass
                return {
                    "type": "request",
                    "content": text[len(prefix) :].strip(),
                    "source": "wechat",
                }
        return None

    def _send_lifecycle_notification(
        self,
        status: Mapping[str, Any],
        config: BridgeConfig,
        runtime: dict[str, Any],
    ) -> None:
        completion = self._completion(status)
        if completion is None:
            return
        key, result = completion
        if key in runtime["sent_completions"]:
            return
        if self._safe_send(f"{config.emoji}{config.done_prefix}{result}", "completion"):
            _remember(runtime["sent_completions"], key)

    def terminal_notification_sent(self, status: Mapping[str, Any] | None) -> bool:
        """Return true once a terminal status has had its completion notification sent."""
        completion = self._completion(dict(status or {}))
        if completion is None:
            return False
        runtime = self.store.load_json(self.store.runtime_path, {})
        return completion[0] in runtime.get("sent_completions", [])

    @staticmethod
    def _completion(status: Mapping[str, Any]) -> tuple[str, str] | None:
        state = status.get("state")
        if state not in ("done", "error"):
            return None
        result = str(status.get("result") or status.get("progress") or "").strip()
        if state == "error":
            result = f"任务未完成，原因：{result or '未知错误'}"
        else:
            result = result or "任务已完成"
        key = str(
            status.get("notification_id")
            or _fingerprint([state, status.get("task", ""), result])
        )
        return key, result

    def _send_outbox(
        self,
        status: Mapping[str, Any],
        config: BridgeConfig,
        runtime: dict[str, Any],
    ) -> None:
        outbox = status.get("outbox", [])
        if not isinstance(outbox, list):
            return
        for message in outbox:
            if not isinstance(message, Mapping) or not str(message.get("text", "")).strip():
                continue
            kind = str(message.get("type", "received"))
            text = str(message["text"]).strip()
            key = str(
                message.get("id")
                or _fingerprint([status.get("task", ""), kind, text])
            )
            if key in runtime["sent_outbox"]:
                continue
            prefix = config.done_prefix if kind == "done" else config.received_prefix
            if self._safe_send(f"{config.emoji}{prefix}{text}", "outbox"):
                _remember(runtime["sent_outbox"], key)


def format_status(status: Mapping[str, Any]) -> str:
    state = str(status.get("state", "idle"))
    task = str(status.get("task", "")).strip()
    progress = str(status.get("progress") or status.get("result") or "").strip()
    if state == "idle":
        return "我现在空闲，正在等待任务。"
    if state == "done":
        return "上一个任务已完成，目前等待新任务。"
    if state == "error":
        return f"上一个任务遇到错误，目前{_sentence(progress or '任务失败')}"
    if state == "waiting_user":
        return f"我正在等待用户补充信息，目前{_sentence(progress or '需要用户确认下一步')}"
    task_text = task or "处理任务"
    progress_text = progress or "任务正在进行中"
    return f"我正在{task_text}，目前{_sentence(progress_text)}"


def _backend_from_name(name: str | None, storage_dir: str | Path | None) -> Backend:
    if name == "file-mock":
        return FileMockBackend(storage_dir or JsonStore().directory)
    if name == "null":
        return NullBackend()
    directory = str(Path(storage_dir or JsonStore().directory).resolve())
    if directory not in _DEFAULT_WEB_BACKENDS:
        _DEFAULT_WEB_BACKENDS[directory] = WebFileHelperBackend(directory)
    return _DEFAULT_WEB_BACKENDS[directory]


def wechat_tick(
    status: Mapping[str, Any] | None,
    check_interval: int | None = None,
    *,
    backend: Backend | None = None,
    storage_dir: str | Path | None = None,
) -> list[dict[str, str]]:
    """Public API: persist state, exchange protocol messages, and return requests."""
    selected = backend or _backend_from_name(None, storage_dir)
    return WechatBridge(selected, storage_dir=storage_dir).tick(status, check_interval)
