param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]] $BootstrapArgs
)

$ErrorActionPreference = "Stop"
$scriptPath = Join-Path $PSScriptRoot "bootstrap.py"
$templatePath = Join-Path (Split-Path $PSScriptRoot -Parent) "assets\tool-template"
$defaultToolHome = Join-Path $env:USERPROFILE ".pineapple\bridge-tool"
$toolHome = if ($env:PINEAPPLE_TOOL_HOME) { $env:PINEAPPLE_TOOL_HOME } else { $defaultToolHome }
$toolVersion = "0.3.4"
$command = if ($BootstrapArgs.Count -gt 0) { $BootstrapArgs[0] } else { "" }

function Test-PineappleToolSource([string] $Path) {
    return (
        (Test-Path -LiteralPath (Join-Path $Path "pyproject.toml")) -and
        (Test-Path -LiteralPath (Join-Path $Path "wechat_agent\bridge.py")) -and
        (Test-Path -LiteralPath (Join-Path $Path "wechat_agent\control.py"))
    )
}

if ($command -eq "discover") {
    $candidatePaths = [System.Collections.Generic.List[string]]::new()
    $candidatePaths.Add($toolHome)
    if ($env:PINEAPPLE_BRIDGE_SOURCE) { $candidatePaths.Add($env:PINEAPPLE_BRIDGE_SOURCE) }
    $candidatePaths.Add((Get-Location).Path)
    $candidatePaths.Add((Split-Path (Get-Location).Path -Parent))
    $candidatePaths.Add((Join-Path $env:USERPROFILE "projects\Pineapple"))
    $found = @()
    foreach ($candidate in ($candidatePaths | Select-Object -Unique)) {
        if (Test-PineappleToolSource $candidate) {
            $resolved = (Resolve-Path -LiteralPath $candidate).Path
            $venvPython = Join-Path $resolved ".venv\Scripts\python.exe"
            $manifestPath = Join-Path $resolved "pineapple-install.json"
            $installedVersion = $null
            if ($resolved -eq $toolHome -and (Test-Path -LiteralPath $manifestPath)) {
                try { $installedVersion = (Get-Content -Raw -Encoding UTF8 $manifestPath | ConvertFrom-Json).tool_version } catch {}
            }
            $found += [ordered]@{
                source = $resolved
                installed = ($resolved -eq $toolHome)
                python = $(if (Test-Path -LiteralPath $venvPython) { $venvPython } else { $null })
                tool_version = $installedVersion
            }
        }
    }
    if ($found.Count -eq 0) {
        [ordered]@{
            status = "missing"
            tool_home = $toolHome
            next_action = "ask_for_existing_source_or_install_bundled_template"
        } | ConvertTo-Json -Compress
    } else {
        $preferred = @($found | Where-Object { $_.installed })[0]
        if (-not $preferred) { $preferred = $found[0] }
        [ordered]@{
            status = $(if ($preferred.installed -and $preferred.tool_version -ne $toolVersion) { "upgrade_needed" } elseif ($preferred.installed) { "ready" } else { "source_found" })
            found = $found
            preferred = $preferred
            latest_tool_version = $toolVersion
        } | ConvertTo-Json -Depth 4 -Compress
    }
    exit 0
}

if ($command -eq "plan") {
    $source = "bundled_template"
    for ($index = 1; $index -lt $BootstrapArgs.Count - 1; $index++) {
        if ($BootstrapArgs[$index] -eq "--source" -and $BootstrapArgs[$index + 1] -ne "bundled") {
            $source = $BootstrapArgs[$index + 1]
        }
    }
    [ordered]@{
        status = "plan"
        source = $source
        tool_version = $toolVersion
        packaging_source = "bundled_template"
        tool_home = $toolHome
        writes = @(
            (Join-Path $toolHome "pyproject.toml"),
            (Join-Path $toolHome "LICENSE"),
            (Join-Path $toolHome "README.md"),
            (Join-Path $toolHome "wechat_agent"),
            (Join-Path $toolHome "wechat_agent_bridge.egg-info"),
            (Join-Path $toolHome ".venv"),
            (Join-Path $toolHome "pineapple-install.json")
        )
        creates_background_process = $false
        opens_browser = $false
        installs_dependencies = @("playwright>=1.49")
        adopted_source_code_runs_when_enabled = ($source -ne "bundled_template")
        requires_confirmation = $true
    } | ConvertTo-Json -Compress
    exit 0
}

$pythonCandidates = [System.Collections.Generic.List[string]]::new()
foreach ($name in @("py", "python", "python3")) {
    $pythonCommand = Get-Command $name -ErrorAction SilentlyContinue
    if ($pythonCommand) { $pythonCandidates.Add($pythonCommand.Source) }
}
foreach ($pattern in @(
    (Join-Path $env:LOCALAPPDATA "Python\pythoncore-*\python.exe"),
    (Join-Path $env:LOCALAPPDATA "Programs\Python\Python*\python.exe"),
    (Join-Path $env:USERPROFILE "AppData\Local\Programs\Python\Python*\python.exe"),
    (Join-Path $env:USERPROFILE "miniconda3\python.exe"),
    (Join-Path $env:USERPROFILE "anaconda3\python.exe")
)) {
    Get-Item -Path $pattern -ErrorAction SilentlyContinue |
        ForEach-Object { $pythonCandidates.Add($_.FullName) }
}
$python = $pythonCandidates | Select-Object -First 1
if (-not $python) {
    Write-Error "Pineapple installation requires Python 3.10+; no Python interpreter was found."
    exit 2
}
if ([System.IO.Path]::GetFileNameWithoutExtension($python) -eq "py") {
    & $python -3 -B $scriptPath @BootstrapArgs
} else {
    & $python -B $scriptPath @BootstrapArgs
}
exit $LASTEXITCODE
