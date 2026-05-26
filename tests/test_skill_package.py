"""Skill bootstrap and permission-contract checks for Pineapple."""

# Planted by GALAXY x Codex on 2026-05-25.

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
SKILL = ROOT / "skill-package" / "pineapple"
BOOTSTRAP = SKILL / "scripts" / "bootstrap.py"


class SkillPackageTests(unittest.TestCase):
    def test_skill_contains_bootstrap_and_template_contract(self) -> None:
        self.assertTrue((SKILL / "SKILL.md").is_file())
        self.assertTrue(BOOTSTRAP.is_file())
        self.assertTrue((SKILL / "scripts" / "bootstrap.ps1").is_file())
        template = SKILL / "assets" / "tool-template"
        self.assertTrue((template / "wechat_agent" / "bridge.py").is_file())
        self.assertTrue((template / "wechat_agent" / "control.py").is_file())
        self.assertTrue((template / "README.md").is_file())

    def test_startup_command_is_single_valid_live_control_flow(self) -> None:
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        startup = (SKILL / "commands" / "init.md").read_text(encoding="utf-8")
        interrupt = (SKILL / "rules" / "interrupt.md").read_text(encoding="utf-8")
        self.assertIn("本次任务启用菠萝控制", skill)
        self.assertIn("[commands/init.md]", skill)
        self.assertFalse((SKILL / "commands" / "run.md").exists())
        self.assertIn("discover --json", startup)
        self.assertIn("plan --source", startup)
        self.assertIn("install --source bundled --json", startup)
        self.assertNotIn("--plan", startup)
        self.assertNotIn("--adopt-or-install", startup)
        self.assertIn("--backend web --watch", startup)
        self.assertIn("Ask the user to scan its QR code for this task", startup)
        self.assertIn("菠萝控制已连接。", startup)
        self.assertIn("delivery-settle window", startup)
        self.assertIn("one UTF-8 `status.json` file", startup)
        self.assertIn("Do not invoke another standalone", startup)
        self.assertIn("new QR login", startup)
        self.assertNotIn("正在等待微信指令", startup)
        self.assertIn("--dangerously-bypass-approvals-and-sandbox", startup)
        self.assertIn("--permission-mode bypassPermissions", startup)
        self.assertIn("JsonStore().interrupt_flag_path", interrupt)
        status_rule = (SKILL / "rules" / "status-format.md").read_text(encoding="utf-8")
        self.assertIn("Do not use it because the bridge is open", status_rule)

    def test_discover_reports_missing_in_clean_user_home(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            tool_home = Path(temporary) / "shared-tool"
            env = dict(os.environ)
            env["PINEAPPLE_TOOL_HOME"] = str(tool_home)
            env["PINEAPPLE_SKIP_IMPORT_DISCOVERY"] = "1"
            result = subprocess.run(
                [sys.executable, "-B", str(BOOTSTRAP), "discover", "--json"],
                cwd=Path(temporary),
                env=env,
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=True,
            )
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "missing")
            self.assertEqual(Path(payload["tool_home"]), tool_home)

    def test_discover_finds_compatible_source_without_installing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            env = dict(os.environ)
            env["PINEAPPLE_TOOL_HOME"] = str(Path(temporary) / "shared-tool")
            result = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(BOOTSTRAP),
                    "discover",
                    "--candidate",
                    str(ROOT),
                    "--json",
                ],
                cwd=Path(temporary),
                env=env,
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=True,
            )
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "source_found")
            self.assertEqual(Path(payload["preferred"]["source"]), ROOT)

    def test_discover_reports_installed_older_tool_needs_upgrade(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "shared-tool"
            package = target / "wechat_agent"
            package.mkdir(parents=True)
            (target / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
            (package / "bridge.py").write_text("", encoding="utf-8")
            (package / "control.py").write_text("", encoding="utf-8")
            (target / "pineapple-install.json").write_text(
                '{"tool_version":"0.2.0"}', encoding="utf-8"
            )
            env = dict(os.environ)
            env["PINEAPPLE_TOOL_HOME"] = str(target)
            env["PINEAPPLE_SKIP_IMPORT_DISCOVERY"] = "1"
            result = subprocess.run(
                [sys.executable, "-B", str(BOOTSTRAP), "discover", "--json"],
                env=env,
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=True,
            )
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "upgrade_needed")
            self.assertEqual(payload["latest_tool_version"], "0.3.0")

    def test_plan_is_explicit_about_user_level_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "shared-tool"
            env = dict(os.environ)
            env["PINEAPPLE_TOOL_HOME"] = str(target)
            result = subprocess.run(
                [sys.executable, "-B", str(BOOTSTRAP), "plan", "--source", "bundled", "--json"],
                cwd=Path(temporary),
                env=env,
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=True,
            )
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "plan")
            self.assertTrue(payload["requires_confirmation"])
            self.assertFalse(payload["creates_background_process"])
            self.assertFalse(target.exists())

    @unittest.skipUnless(os.name == "nt", "PowerShell wrapper is Windows-only")
    def test_powershell_plan_matches_transparent_install_footprint(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "shared-tool"
            env = dict(os.environ)
            env["PINEAPPLE_TOOL_HOME"] = str(target)
            result = subprocess.run(
                [
                    "powershell",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(SKILL / "scripts" / "bootstrap.ps1"),
                    "plan",
                    "--source",
                    str(ROOT),
                    "--json",
                ],
                env=env,
                capture_output=True,
                text=True,
                encoding="utf-8-sig",
                check=True,
            )
            payload = json.loads(result.stdout)
            self.assertEqual(payload["packaging_source"], "bundled_template")
            self.assertTrue(payload["adopted_source_code_runs_when_enabled"])
            self.assertIn(str(target / "README.md"), payload["writes"])
            self.assertFalse(target.exists())

    @unittest.skipUnless(os.name == "nt", "PowerShell wrapper is Windows-only")
    def test_powershell_discover_returns_installed_python_for_reuse(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "shared-tool"
            (target / "wechat_agent").mkdir(parents=True)
            (target / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
            (target / "wechat_agent" / "bridge.py").write_text("", encoding="utf-8")
            (target / "wechat_agent" / "control.py").write_text("", encoding="utf-8")
            expected_python = target / ".venv" / "Scripts" / "python.exe"
            expected_python.parent.mkdir(parents=True)
            expected_python.write_text("", encoding="utf-8")
            (target / "pineapple-install.json").write_text(
                '{"tool_version":"0.3.0"}', encoding="utf-8"
            )
            env = dict(os.environ)
            env["PINEAPPLE_TOOL_HOME"] = str(target)
            result = subprocess.run(
                [
                    "powershell",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(SKILL / "scripts" / "bootstrap.ps1"),
                    "discover",
                    "--json",
                ],
                env=env,
                capture_output=True,
                text=True,
                encoding="utf-8-sig",
                check=True,
            )
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "ready")
            self.assertEqual(Path(payload["preferred"]["python"]), expected_python)

    def test_adoption_uses_bundled_packaging_instead_of_source_build_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "external-source"
            package = source / "wechat_agent"
            package.mkdir(parents=True)
            (source / "pyproject.toml").write_text(
                "[build-system]\nrequires = ['untrusted-build-hook']\n",
                encoding="utf-8",
            )
            (package / "bridge.py").write_text(
                "def wechat_tick(status): return []\n", encoding="utf-8"
            )
            (package / "control.py").write_text(
                "def settings(): return {}\n", encoding="utf-8"
            )
            target = Path(temporary) / "shared-tool"
            env = dict(os.environ)
            env["PINEAPPLE_TOOL_HOME"] = str(target)
            result = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(BOOTSTRAP),
                    "adopt",
                    "--source",
                    str(source),
                    "--skip-dependencies",
                    "--json",
                ],
                env=env,
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=True,
            )
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "ready")
            bundled_pyproject = (
                SKILL / "assets" / "tool-template" / "pyproject.toml"
            ).read_text(encoding="utf-8")
            self.assertEqual(
                (target / "pyproject.toml").read_text(encoding="utf-8"),
                bundled_pyproject,
            )


if __name__ == "__main__":
    unittest.main()
