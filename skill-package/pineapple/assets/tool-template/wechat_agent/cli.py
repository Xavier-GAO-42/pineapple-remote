"""Command line entry point for agents unable to import Python modules."""

# Planted by GALAXY x Codex on 2026-05-25.

from __future__ import annotations

import argparse
import ctypes
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

from .backends import FileMockBackend, NullBackend, WebFileHelperBackend
from .bridge import WechatBridge
from .config import BridgeConfig
from .storage import default_storage_dir


def _read_status(path: str) -> dict[str, Any]:
    if path == "-":
        data = json.load(sys.stdin)
    else:
        with Path(path).open("r", encoding="utf-8-sig") as stream:
            data = json.load(stream)
    if not isinstance(data, dict):
        raise ValueError("status JSON must contain an object")
    return data


def _append_requests(path: str, events: list[dict[str, str]]) -> None:
    """Persist watch-mode request events next to the task status file."""
    if path == "-":
        return
    request_events = [event for event in events if event.get("type") == "request"]
    if not request_events:
        return
    mailbox_path = Path(path).resolve().parent / "requests.jsonl"
    known_ids: set[str] = set()
    try:
        lines = mailbox_path.read_text(encoding="utf-8").splitlines()
    except (FileNotFoundError, OSError):
        lines = []
    for line in lines:
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict) and isinstance(item.get("id"), str):
            known_ids.add(item["id"])
    with mailbox_path.open("a", encoding="utf-8") as stream:
        for event in request_events:
            if event.get("id") in known_ids:
                continue
            stream.write(json.dumps(event, ensure_ascii=False) + "\n")
            known_ids.add(event["id"])


def _runtime_dir_for_status(path: str) -> Path | None:
    if path == "-":
        return None
    status_path = Path(path).resolve()
    return status_path.parent / f".{status_path.stem}.pineapple-runtime"


def _process_is_running(pid: int) -> bool:
    if os.name == "nt":
        query_limited_information = 0x1000
        still_active = 259
        handle = ctypes.windll.kernel32.OpenProcess(query_limited_information, False, pid)
        if not handle:
            return False
        try:
            exit_code = ctypes.c_ulong()
            if not ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
                return False
            return exit_code.value == still_active
        finally:
            ctypes.windll.kernel32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _acquire_watch_lock(runtime_dir: Path | None) -> Path | None:
    if runtime_dir is None:
        return None
    runtime_dir.mkdir(parents=True, exist_ok=True)
    lock_path = runtime_dir / "watch.lock"
    for _ in range(2):
        try:
            with lock_path.open("x", encoding="ascii") as stream:
                stream.write(str(os.getpid()))
            return lock_path
        except FileExistsError:
            try:
                owner = int(lock_path.read_text(encoding="ascii").strip())
            except (OSError, ValueError):
                owner = 0
            if not owner or not _process_is_running(owner):
                try:
                    lock_path.unlink()
                except OSError:
                    pass
                continue
            raise ValueError(
                f"a Pineapple watch helper is already active for this status file (pid {owner})"
            )
    raise ValueError("could not acquire Pineapple watch helper lock")


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Run one WeChat agent bridge tick.")
    parser.add_argument("--status-json", required=True, help="Status JSON path, or - for stdin.")
    parser.add_argument("--storage-dir", help="Override local JSON state directory.")
    parser.add_argument("--check-interval", type=int, help="Requested 3/5/10 second mode.")
    parser.add_argument(
        "--backend",
        choices=("web", "file-mock", "null"),
        default="web",
        help="Transport backend; file-mock is intended for local testing.",
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Keep one foreground web session open and emit one JSON events line per tick.",
    )
    args = parser.parse_args(argv)
    lock_path: Path | None = None
    if args.backend == "web" and not args.watch:
        parser.error(
            "the web backend requires --watch so the authorized official page remains open; "
            "use the Python API for in-process ticks"
        )
    try:
        storage_dir = args.storage_dir or str(default_storage_dir())
        task_runtime_dir = _runtime_dir_for_status(args.status_json) if args.watch else None
        runtime_dir = task_runtime_dir if args.watch and not args.storage_dir else None
        if args.watch:
            lock_path = _acquire_watch_lock(task_runtime_dir)
        if args.backend == "file-mock":
            backend = FileMockBackend(runtime_dir or storage_dir)
        elif args.backend == "null":
            backend = NullBackend()
        else:
            backend = WebFileHelperBackend(runtime_dir or storage_dir)
        bridge = WechatBridge(backend, storage_dir, runtime_dir=runtime_dir)
        try:
            if args.watch:
                while True:
                    status = _read_status(args.status_json)
                    events = bridge.tick(status, args.check_interval)
                    _append_requests(args.status_json, events)
                    print(json.dumps(events, ensure_ascii=False), flush=True)
                    if bridge.terminal_notification_settled(status):
                        return 0
                    terminal_remaining = bridge.terminal_settle_remaining(status)
                    if terminal_remaining is not None:
                        time.sleep(terminal_remaining)
                        continue
                    config = BridgeConfig.from_mapping(
                        bridge.store.load_json(bridge.store.config_path, {})
                    )
                    time.sleep(config.check_interval)
            status = _read_status(args.status_json)
            events = bridge.tick(status, args.check_interval)
            print(json.dumps(events, ensure_ascii=False), flush=True)
            return 0
        finally:
            close = getattr(backend, "close", None)
            if callable(close):
                close()
            if lock_path is not None:
                try:
                    lock_path.unlink()
                except OSError:
                    pass
    except KeyboardInterrupt:
        return 130
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
