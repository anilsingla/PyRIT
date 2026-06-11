#Requires -Version 5.1
# =============================================================================
# lib_common.ps1 — Shared utilities for security-evaluator installation scripts
# =============================================================================
# Dot-source this file from any installer script:
#   $LibDir = Join-Path $PSScriptRoot "common"
#   . (Join-Path $LibDir "lib_common.ps1")
# =============================================================================

# ---- Output helpers ---------------------------------------------------------

function Write-Header {
    param([string]$Text)
    Write-Host ""
    Write-Host "================================================================"
    Write-Host $Text
    Write-Host "================================================================"
}

function Write-Ok   { param([string]$Msg); Write-Host "[OK]   $Msg" }
function Write-Info { param([string]$Msg); Write-Host "[INFO] $Msg" }
function Write-Warn { param([string]$Msg); Write-Host "[WARN] $Msg" }
function Write-Err  { param([string]$Msg); Write-Error "[ERROR] $Msg" }

# ---- Command presence -------------------------------------------------------

function Test-CommandExists {
    param([string]$Name)
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

# ---- Package manager detection ---------------------------------------------

function Get-WindowsPackageManager {
    # Returns the first available Windows package manager, or $null.
    foreach ($mgr in @("winget", "choco", "scoop")) {
        if (Test-CommandExists $mgr) { return $mgr }
    }
    return $null
}

# ---- Python helpers ---------------------------------------------------------

function Get-PythonCommand {
    # Returns the first python executable found, or throws.
    foreach ($cmd in @("python", "py", "python3")) {
        if (Test-CommandExists $cmd) { return $cmd }
    }
    throw "Python not found. Install Python 3.10+ and add it to PATH."
}

function Invoke-SetupPythonEnv {
    # Env vars respected (set before dot-sourcing or as $env: vars):
    #   USE_VENV  (default: "true")
    #   VENV_DIR  (default: ".venv")
    param(
        [string]$UseVenv = $(if ($env:USE_VENV) { $env:USE_VENV } else { "true" }),
        [string]$VenvDir = $(if ($env:VENV_DIR) { $env:VENV_DIR } else { ".venv" })
    )

    Write-Header "Preparing Python environment"
    $pyCmd = Get-PythonCommand

    if ($UseVenv.ToLower() -eq "true") {
        if (-not (Test-Path $VenvDir)) {
            & $pyCmd -m venv $VenvDir
        }
        $activatePath = Join-Path $VenvDir "Scripts\Activate.ps1"
        . $activatePath
        Write-Ok "Virtual environment active: $VenvDir"
    } else {
        Write-Info "Skipping virtual environment (USE_VENV=false)."
    }

    & $pyCmd -m pip install --upgrade pip
    & $pyCmd -m pip install --upgrade pyrit
}

# ---- PyRIT SQLite smoke test -----------------------------------------------

function Invoke-PyritSqliteSmokeTest {
    param([string]$DbPath = $(if ($env:PYRIT_DB_PATH) { $env:PYRIT_DB_PATH } else { ".\pyrit_demo.db" }))

    Write-Header "PyRIT SQLite smoke test"
    $pyCmd = Get-PythonCommand

    $smokeScript = @"
import asyncio
from pathlib import Path

from pyrit.setup import SQLITE, initialize_pyrit_async
from pyrit.memory import CentralMemory

DB_PATH = Path(r"$DbPath").resolve()

async def main() -> None:
    await initialize_pyrit_async(memory_db_type=SQLITE, db_path=str(DB_PATH))
    memory = CentralMemory.get_memory_instance()
    dataset_names = memory.get_seed_dataset_names()
    print(f"[OK] PyRIT initialized with SQLITE at: {DB_PATH}")
    print(f"[INFO] Dataset names: {dataset_names}")

asyncio.run(main())
"@

    $tmpFile = Join-Path $env:TEMP "pyrit_smoke_$(Get-Random).py"
    Set-Content -Path $tmpFile -Value $smokeScript -Encoding UTF8
    try {
        & $pyCmd $tmpFile
    } finally {
        Remove-Item $tmpFile -ErrorAction SilentlyContinue
    }
}
