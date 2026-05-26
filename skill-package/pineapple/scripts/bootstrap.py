"""Discover or install the reusable Pineapple tool from a single skill package."""

# Planted by GALAXY x Codex on 2026-05-25.

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time
import venv
from pathlib import Path
from typing import Any


SKILL_DIR = Path(__file__).resolve().parents[1]
TEMPLATE_DIR = SKILL_DIR / "assets" / "tool-template"
DEFAULT_TOOL_HOME = Path.home() / ".pineapple" / "bridge-tool"
PACKAGING_FILES = ("pyproject.toml", "LICENSE", "README.md")
TOOL_VERSION = "0.2.1"


def tool_home() -> Path:
    override = os.environ.get("PINEAPPLE_TOOL_HOME")
    return Path(override).expanduser() if override else DEFAULT_TOOL_HOME


def python_path(directory: Path) -> Path:
    if os.name == "nt":
        return directory / ".venv" / "Scripts" / "python.exe"
    return directory / ".venv" / "bin" / "python"


def is_tool_source(directory: Path) -> bool:
    return (
        (directory / "pyproject.toml").is_file()
        and (directory / "wechat_agent" / "bridge.py").is_file()
        and (directory / "wechat_agent" / "control.py").is_file()
    )


def installed_version(directory: Path) -> str | None:
    try:
        payload = json.loads((directory / "pineapple-install.json").read_text(encoding="utf-8"))
        return str(payload.get("tool_version") or "")
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return None


def candidates(extra: list[str]) -> list[Path]:
    values: list[Path] = [tool_home()]
    env_source = os.environ.get("PINEAPPLE_BRIDGE_SOURCE")
    if env_source:
        values.append(Path(env_source).expanduser())
    values.extend(Path(value).expanduser() for value in extra)
    cwd = Path.cwd()
    values.extend((cwd, cwd.parent, Path.home() / "projects" / "Pineapple"))
    if os.environ.get("PINEAPPLE_SKIP_IMPORT_DISCOVERY") != "1":
        try:
            spec = importlib.util.find_spec("wechat_agent")
            if spec and spec.origin:
                values.append(Path(spec.origin).resolve().parents[1])
        except (ImportError, ValueError):
            pass
    distinct: list[Path] = []
    seen: set[str] = set()
    for value in values:
        resolved = value.resolve()
        key = str(resolved).lower() if os.name == "nt" else str(resolved)
        if key not in seen:
            seen.add(key)
            distinct.append(resolved)
    return distinct


def result(status: str, **fields: Any) -> dict[str, Any]:
    return {"status": status, **fields}


def discover(extra: list[str]) -> dict[str, Any]:
    found = []
    for directory in candidates(extra):
        if is_tool_source(directory):
            found.append(
                {
                    "source": str(directory),
                    "installed": directory == tool_home().resolve(),
                    "python": str(python_path(directory))
                    if python_path(directory).exists()
                    else None,
                    "tool_version": installed_version(directory)
                    if directory == tool_home().resolve()
                    else None,
                }
            )
    if not found:
        return result(
            "missing",
            tool_home=str(tool_home()),
            next_action="ask_for_existing_source_or_install_bundled_template",
        )
    preferred = next((item for item in found if item["installed"]), found[0])
    if preferred["installed"] and preferred["tool_version"] != TOOL_VERSION:
        return result(
            "upgrade_needed",
            found=found,
            preferred=preferred,
            latest_tool_version=TOOL_VERSION,
        )
    return result("ready" if preferred["installed"] else "source_found", found=found, preferred=preferred)


def plan(source: Path, skip_dependencies: bool) -> dict[str, Any]:
    target = tool_home().resolve()
    label = "bundled_template" if source.resolve() == TEMPLATE_DIR.resolve() else str(source.resolve())
    return result(
        "plan",
        source=label,
        tool_version=TOOL_VERSION,
        packaging_source="bundled_template",
        tool_home=str(target),
        writes=[
            str(target / "pyproject.toml"),
            str(target / "LICENSE"),
            str(target / "README.md"),
            str(target / "wechat_agent"),
            str(target / "wechat_agent_bridge.egg-info"),
            str(target / ".venv"),
            str(target / "pineapple-install.json"),
        ],
        creates_background_process=False,
        opens_browser=False,
        installs_dependencies=[] if skip_dependencies else ["playwright>=1.49"],
        adopted_source_code_runs_when_enabled=source.resolve() != TEMPLATE_DIR.resolve(),
        requires_confirmation=True,
    )


def prepare_target(source: Path, target: Path) -> None:
    if target.exists() and any(target.iterdir()) and not is_tool_source(target):
        backup = target.with_name(f"{target.name}.backup-{int(time.time())}")
        target.rename(backup)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.mkdir(parents=True, exist_ok=True)
    for name in PACKAGING_FILES:
        shutil.copy2(TEMPLATE_DIR / name, target / name)
    shutil.copytree(
        source / "wechat_agent",
        target / "wechat_agent",
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.egg-info"),
    )


def create_environment(target: Path, skip_dependencies: bool) -> Path:
    environment_python = python_path(target)
    if not environment_python.exists():
        venv.EnvBuilder(with_pip=True).create(target / ".venv")
    command = [str(environment_python), "-m", "pip", "install", "-e", str(target)]
    if not skip_dependencies:
        command[-1] = f"{target}[web]"
    subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return environment_python


def install(source: Path, skip_dependencies: bool) -> dict[str, Any]:
    if not is_tool_source(source):
        return result("invalid_source", source=str(source), required="pyproject.toml and wechat_agent bridge/control modules")
    target = tool_home().resolve()
    prepare_target(source.resolve(), target)
    try:
        environment_python = create_environment(target, skip_dependencies)
    except subprocess.CalledProcessError as exc:
        return result("install_failed", tool_home=str(target), error=(exc.stderr or str(exc))[-500:])
    manifest = {
        "tool_home": str(target),
        "python": str(environment_python),
        "tool_version": TOOL_VERSION,
        "installed_from": str(source.resolve()),
        "installed_at": int(time.time()),
    }
    (target / "pineapple-install.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return result("ready", **manifest)


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Initialize the user-level Pineapple bridge tool.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    find = subparsers.add_parser("discover")
    find.add_argument("--candidate", action="append", default=[])
    find.add_argument("--json", action="store_true")
    for name in ("plan", "install", "adopt"):
        operation = subparsers.add_parser(name)
        operation.add_argument("--source")
        operation.add_argument("--skip-dependencies", action="store_true")
        operation.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if args.command == "discover":
        payload = discover(args.candidate)
    else:
        source = (
            TEMPLATE_DIR
            if not args.source or args.source == "bundled"
            else Path(args.source).expanduser()
        )
        payload = (
            plan(source, args.skip_dependencies)
            if args.command == "plan"
            else install(source, args.skip_dependencies)
        )
    print(json.dumps(payload, ensure_ascii=False))
    return 0 if payload["status"] in ("ready", "source_found", "missing", "upgrade_needed", "plan") else 2


if __name__ == "__main__":
    raise SystemExit(main())
