# Command: Install Or Upgrade Pineapple

Load this file only for first setup, explicit installation, or a tool upgrade.

## Permission Footprint

Before writes, tell the user that installation may write `~/.pineapple/bridge-tool`,
create its local virtual environment, and install the Python web dependency. Starting
control later opens one visible official File Transfer Assistant webpage for that task.

If repeated command approvals block a trusted setup, you may suggest bypass mode only
after disclosing its broader execution risk:

```powershell
# Codex CLI
codex --dangerously-bypass-approvals-and-sandbox

# Claude Code CLI, retaining the plugin
claude --plugin-dir "<pineapple-plugin-dir-or-zip>" --permission-mode bypassPermissions
```

Do not claim bypass is required or enable it silently.

## Bootstrap

Set `<skill-root>` to the directory containing this skill's `SKILL.md`.

```powershell
powershell -ExecutionPolicy Bypass -File "<skill-root>\scripts\bootstrap.ps1" discover --json
```

On macOS/Linux use:

```bash
python3 -B "<skill-root>/scripts/bootstrap.py" discover --json
```

Handle the result:

- `ready` with a usable `python`: installation is complete.
- `upgrade_needed` or `missing`: present `plan --source bundled --json`; after approval, run `install --source bundled --json`.
- `source_found`: present `plan --source "<preferred.source>" --json`; after approval, run `adopt --source "<preferred.source>" --json`.
- `ready` without a usable `python`: present and run `adopt` for the reported source after approval.

Use the same wrapper command style as `discover`. Do not ask the user to manually run
`pip` or `playwright install`. If Python 3.10+ cannot be found, report that prerequisite
and stop safely.
