#Requires -Version 5.1
$ErrorActionPreference = 'Stop'

<#
=============================================================================
setup_sqlite_windows.ps1 -- SQLite + PyRIT installer for Windows
=============================================================================
Can be run directly OR dot-sourced by the main installer.

Usage:
    powershell -ExecutionPolicy Bypass -File .\samples\security-evaluator\scripts\installers\setup_sqlite_windows.ps1

Optional environment variables:
  PYRIT_DB_PATH    (default: .\pyrit_windows_demo.db)
  USE_VENV         (default: true)
  VENV_DIR         (default: .venv)
=============================================================================
#>

$LibDir = Join-Path $PSScriptRoot "common"
. (Join-Path $LibDir "lib_common.ps1")

$PyritDbPath = if ($env:PYRIT_DB_PATH) { $env:PYRIT_DB_PATH } else { ".\pyrit_windows_demo.db" }
$UseVenv     = if ($env:USE_VENV)     { $env:USE_VENV }     else { "true" }
$VenvDir     = if ($env:VENV_DIR)     { $env:VENV_DIR }     else { ".venv" }

function Install-SqliteWindows {
    if (Test-CommandExists "sqlite3") {
        $ver = (& sqlite3 --version) 2>$null
        Write-Ok "sqlite3 already installed: $ver"
        return
    }

    Write-Header "Installing sqlite3"
    $mgr = Get-WindowsPackageManager

    switch ($mgr) {
        "winget" {
            Write-Info "Using winget"
            winget install --id SQLite.SQLite --exact --silent --accept-source-agreements --accept-package-agreements
        }
        "choco" {
            Write-Info "Using Chocolatey"
            choco install sqlite -y
        }
        "scoop" {
            Write-Info "Using Scoop"
            scoop install sqlite
        }
        default { throw "No supported package manager found (winget/choco/scoop). Install sqlite manually." }
    }

    if (-not (Test-CommandExists "sqlite3")) {
        Write-Warn "sqlite3 is not yet on PATH. You may need to open a new terminal."
    } else {
        $ver = (& sqlite3 --version) 2>$null
        Write-Ok "sqlite3 installed: $ver"
    }
}

Write-Header "Windows SQLite + PyRIT setup"
Install-SqliteWindows
Invoke-SetupPythonEnv -UseVenv $UseVenv -VenvDir $VenvDir
Invoke-PyritSqliteSmokeTest -DbPath $PyritDbPath

Write-Header "Done"
Write-Ok "SQLite installation complete and PyRIT SQLite integration tested."
Write-Info "DB file path: $PyritDbPath"

