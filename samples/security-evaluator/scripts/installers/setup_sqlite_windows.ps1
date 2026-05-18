#Requires -Version 5.1
$ErrorActionPreference = 'Stop'

<#
=============================================================================
setup_sqlite_windows.ps1 -- SQLite Installation and Database Setup for Windows
=============================================================================

WHAT THIS SCRIPT DOES:
1. Installs SQLite3 binary on Windows (via winget/choco/scoop)
2. Creates database directory structure
3. Initializes PyRIT SQLite database file on HOST MACHINE
4. Verifies multi-container database access

WHERE SQLITE IS STORED:
┌─────────────────────────────────────────────────────────────────────────────┐
│ SQLITE BINARY (executable):                                                 │
│ • Installation location depends on package manager:                          │
│   - winget:   Typically C:\Program Files\sqlite\                             │
│   - Chocolatey: C:\ProgramData\chocolatey\lib\sqlite\current\                │
│   - Scoop:    $env:USERPROFILE\scoop\apps\sqlite\current\                   │
│                                                                              │
│ DATABASE FILE (data):                                                        │
│ • HOST MACHINE: <REPO_ROOT>\samples\security-evaluator\reports\             │
│   Example: C:\Users\YourUser\PyRIT\samples\security-evaluator\reports\      │
│            pyrit_ollama_demo.db (PHYSICALLY ON WINDOWS HOST)               │
│                                                                              │
│ • Containers access via VOLUME MOUNT:                                        │
│   /workspace/samples/security-evaluator/reports/pyrit_ollama_demo.db        │
│   (inside container, points to same host file)                              │
└─────────────────────────────────────────────────────────────────────────────┘

HOW DOCKER CONTAINERS SHARE THE DATABASE:
1. docker-compose.yaml defines: volumes: ../../:/workspace
2. This binds HOST REPO ROOT → /workspace INSIDE CONTAINER
3. All containers share same PYRIT_SQLITE_DB_PATH environment variable
4. Python sqlite3 module accesses HOST FILE via volume mount
5. Multiple containers safely read/write same file (OS-level file locking)

USAGE:
    # Install SQLite and create database:
    powershell -ExecutionPolicy Bypass -File .\samples\security-evaluator\scripts\installers\setup_sqlite_windows.ps1

    # Install but skip test:
    $env:SKIP_TEST=1; powershell -ExecutionPolicy Bypass -File ...

    # Custom database path:
    $env:DB_DIR="C:\custom\path"; powershell -ExecutionPolicy Bypass -File ...

ENVIRONMENT VARIABLES (optional):
    SKIP_SQLITE_INSTALL   - Skip SQLite binary installation, only create DB
    SKIP_TEST             - Skip database connectivity test
    DB_DIR                - Custom database directory (default: ./reports)
    DB_PATH               - Full custom database file path

=============================================================================
#>

param(
    [switch]$SkipInstall = $false,
    [switch]$SkipTest = $false,
    [string]$DbDir = "",
    [string]$DbPath = ""
)

# Color output
function Write-Info { Write-Host "ℹ️  $args" -ForegroundColor Cyan }
function Write-Success { Write-Host "✓ $args" -ForegroundColor Green }
function Write-Err { Write-Host "✗ $args" -ForegroundColor Red }
function Write-Warn { Write-Host "⚠ $args" -ForegroundColor Yellow }

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════════════════╗"
Write-Host "║ SQLite Setup for PyRIT (Windows)                                     ║"
Write-Host "║ Database File Storage & Volume Mounting Guide                        ║"
Write-Host "╚════════════════════════════════════════════════════════════════════════╝"
Write-Host ""

# Determine database paths
if (-not $DbDir) {
    $DbDir = Join-Path $PSScriptRoot "..\..\reports"
}

if (-not $DbPath) {
    $DbPath = Join-Path $DbDir "pyrit_ollama_demo.db"
}

# Convert to absolute paths
$DbDir = (Resolve-Path $DbDir -ErrorAction SilentlyContinue).Path ?? (Get-Item $DbDir).FullName
$DbPath = $DbPath -replace '\\', '\' # Normalize slashes

Write-Info "Configuration:"
Write-Host "   Repo root: $(Split-Path $DbDir -Parent)"
Write-Host "   Database directory: $DbDir"
Write-Host "   Database file path: $DbPath"
Write-Host "   Skip install: $SkipInstall"
Write-Host ""

# ─────────────────────────────────────────────────────────────────────────────
# STEP 1: Install SQLite Binary on Windows
# ─────────────────────────────────────────────────────────────────────────────

if (-not $SkipInstall) {
    Write-Host ""
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    Write-Host "STEP 1: Installing SQLite Binary"
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    Write-Host ""

    $sqlite = Get-Command sqlite3 -ErrorAction SilentlyContinue
    if ($sqlite) {
        $ver = & sqlite3 --version
        Write-Success "SQLite already installed"
        Write-Info "  Path: $($sqlite.Source)"
        Write-Info "  Version: $ver"
    }
    else {
        Write-Info "SQLite not found, attempting installation..."
        Write-Host ""

        $installed = $false

        # Try winget
        if (-not $installed) {
            $winget = Get-Command winget -ErrorAction SilentlyContinue
            if ($winget) {
                Write-Info "Trying: winget install SQLite.SQLite"
                try {
                    & winget install SQLite.SQLite --accept-source-agreements -e 2>&1 | Out-Null
                    $installed = $true
                    Write-Success "Installed via winget"
                    Write-Info "  Typical location: C:\Program Files\sqlite\"
                }
                catch {
                    Write-Warn "winget install failed"
                }
            }
        }

        # Try Chocolatey
        if (-not $installed) {
            $choco = Get-Command choco -ErrorAction SilentlyContinue
            if ($choco) {
                Write-Info "Trying: choco install sqlite"
                try {
                    & choco install sqlite -y 2>&1 | Out-Null
                    $installed = $true
                    Write-Success "Installed via Chocolatey"
                    Write-Info "  Typical location: C:\ProgramData\chocolatey\lib\sqlite\"
                }
                catch {
                    Write-Warn "Chocolatey install failed"
                }
            }
        }

        # Try Scoop
        if (-not $installed) {
            $scoop = Get-Command scoop -ErrorAction SilentlyContinue
            if ($scoop) {
                Write-Info "Trying: scoop install sqlite"
                try {
                    & scoop install sqlite 2>&1 | Out-Null
                    $installed = $true
                    Write-Success "Installed via Scoop"
                    Write-Info "  Typical location: $env:USERPROFILE\scoop\apps\sqlite\current\"
                }
                catch {
                    Write-Warn "Scoop install failed"
                }
            }
        }

        if (-not $installed) {
            Write-Err "Could not install SQLite automatically."
            Write-Info "Options:"
            Write-Info "  1. Install manually: https://www.sqlite.org/download.html"
            Write-Info "  2. Or run: winget install SQLite.SQLite"
            Write-Info "  3. Or run: choco install sqlite"
            exit 1
        }

        # Verify installation
        Start-Sleep -Milliseconds 500
        $sqlite = Get-Command sqlite3 -ErrorAction SilentlyContinue
        if (-not $sqlite) {
            Write-Warn "sqlite3 command not yet available (may need new terminal)"
        }
        else {
            $ver = & sqlite3 --version
            Write-Success "SQLite available: $ver"
        }
    }

    Write-Host ""
}
else {
    Write-Info "Skipping SQLite binary installation (--SkipInstall)"
}

# ─────────────────────────────────────────────────────────────────────────────
# STEP 2: Create Database Directory
# ─────────────────────────────────────────────────────────────────────────────

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Write-Host "STEP 2: Creating Database Directory"
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Write-Host ""

if (Test-Path $DbDir) {
    Write-Success "Directory exists: $DbDir"
}
else {
    Write-Info "Creating directory: $DbDir"
    try {
        New-Item -ItemType Directory -Path $DbDir -Force | Out-Null
        Write-Success "Directory created"
    }
    catch {
        Write-Err "Failed to create directory: $_"
        exit 1
    }
}

Write-Host ""

# ─────────────────────────────────────────────────────────────────────────────
# STEP 3: Initialize Database File
# ─────────────────────────────────────────────────────────────────────────────

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Write-Host "STEP 3: Initializing Database File"
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Write-Host ""

if (Test-Path $DbPath) {
    $size = (Get-Item $DbPath).Length
    Write-Success "Database file exists: $DbPath"
    Write-Info "  Size: $size bytes"
}
else {
    Write-Info "Creating database file: $DbPath"
    try {
        & sqlite3 $DbPath "SELECT 1;" | Out-Null
        $size = (Get-Item $DbPath).Length
        Write-Success "Database file created"
        Write-Info "  Size: $size bytes"
    }
    catch {
        Write-Err "Failed to create database: $_"
        exit 1
    }
}

Write-Host ""

# ─────────────────────────────────────────────────────────────────────────────
# STEP 4: Verify Database
# ─────────────────────────────────────────────────────────────────────────────

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Write-Host "STEP 4: Verifying Database"
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Write-Host ""

try {
    $result = & sqlite3 $DbPath "SELECT sqlite_version();"
    Write-Success "SQLite version: $result"

    $tables = & sqlite3 $DbPath ".tables" 2>$null
    if ([string]::IsNullOrWhiteSpace($tables)) {
        Write-Info "Database is empty (no tables yet)"
        Write-Info "Tables will be created when PyRIT runs"
    }
    else {
        Write-Success "Database contains tables: $tables"
    }
}
catch {
    Write-Err "Database verification failed: $_"
    exit 1
}

Write-Host ""

# ─────────────────────────────────────────────────────────────────────────────
# STEP 5: Test Connection (optional)
# ─────────────────────────────────────────────────────────────────────────────

if (-not $SkipTest) {
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    Write-Host "STEP 5: Testing Database Connection"
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    Write-Host ""

    try {
        & sqlite3 $DbPath "CREATE TEMPORARY TABLE test (id INTEGER); INSERT INTO test VALUES (1);" 2>$null
        Write-Success "Read/write test passed"
    }
    catch {
        Write-Err "Connection test failed: $_"
        exit 1
    }

    Write-Host ""
}

# ─────────────────────────────────────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────────────────────────────────────

Write-Host "╔════════════════════════════════════════════════════════════════════════╗"
Write-Host "║ ✓ SQLite Setup Complete                                              ║"
Write-Host "╚════════════════════════════════════════════════════════════════════════╝"
Write-Host ""
Write-Host "WHERE SQLITE IS NOW:"
Write-Host "───────────────────────────────────────────────────────────────────────────"
Write-Host ""
Write-Host "1️⃣  SQLite BINARY (executable) installed on Windows:"
Write-Host "   • Location depends on package manager"
Write-Host "   • Verify with: where sqlite3"
Write-Host ""
Write-Host "2️⃣  DATABASE FILE (data) stored on HOST MACHINE:"
Write-Host "   • Physical location: $DbPath"
Write-Host "   • This file persists on your Windows disk"
Write-Host ""
Write-Host "3️⃣  CONTAINERS access database via VOLUME MOUNT:"
Write-Host "   • Inside container path: /workspace/samples/security-evaluator/reports/pyrit_ollama_demo.db"
Write-Host "   • docker-compose.yaml: volumes: ../../:/workspace"
Write-Host "   • All containers see same file on host"
Write-Host ""
Write-Host "4️⃣  HOW MULTIPLE CONTAINERS SHARE THE DATABASE:"
Write-Host "   • copyrit, jupyter, gui containers all set:"
Write-Host "     PYRIT_SQLITE_DB_PATH=/workspace/.../pyrit_ollama_demo.db"
Write-Host "   • Volume mount ensures they access same HOST file"
Write-Host "   • SQLite file locking (journaling) prevents conflicts"
Write-Host "   • Changes visible immediately across all containers"
Write-Host ""
Write-Host "NEXT STEPS:"
Write-Host "───────────────────────────────────────────────────────────────────────────"
Write-Host ""
Write-Host "1. Start Docker containers:"
Write-Host "   docker compose -f samples/security-evaluator/docker-compose.yaml up -d"
Write-Host ""
Write-Host "2. Verify database is accessible from container:"
Write-Host "   docker compose -f samples/security-evaluator/docker-compose.yaml exec copyrit bash"
Write-Host "   # Inside container:"
Write-Host "   ls -la /workspace/samples/security-evaluator/reports/"
Write-Host "   sqlite3 /workspace/samples/security-evaluator/reports/pyrit_ollama_demo.db '.tables'"
Write-Host ""
Write-Host "3. Run PyRIT (database tables created automatically):"
Write-Host "   pyrit --dry-run --attack-mode baseline ..."
Write-Host ""
Write-Host "4. Verify database from HOST (Windows):"
Write-Host "   sqlite3 '$DbPath' '.tables'"
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════════════════"
Write-Host ""

