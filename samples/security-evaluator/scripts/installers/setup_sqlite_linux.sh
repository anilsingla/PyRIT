#!/usr/bin/env bash
set -euo pipefail

################################################################################
# setup_sqlite_linux.sh - SQLite Installation and Database Setup for Linux/macOS
################################################################################
#
# WHAT THIS SCRIPT DOES:
# 1. Installs SQLite3 binary on Linux/macOS
# 2. Creates database directory structure
# 3. Initializes PyRIT SQLite database file on HOST MACHINE
# 4. Verifies multi-container database access
#
# WHERE SQLITE IS STORED:
# ┌─────────────────────────────────────────────────────────────────────────┐
# │ SQLITE BINARY (executable):                                             │
# │ • On Linux:                                                              │
# │   - Debian/Ubuntu: /usr/bin/sqlite3 (via apt)                           │
# │   - RHEL/Fedora:   /usr/bin/sqlite3 (via dnf/yum)                       │
# │   - Arch:          /usr/bin/sqlite3 (via pacman)                        │
# │                                                                         │
# │ • On macOS:                                                              │
# │   - System: /usr/bin/sqlite3 (built-in)                                 │
# │   - Homebrew: /usr/local/bin/sqlite3 (via brew)                         │
# │                                                                         │
# │ DATABASE FILE (data):                                                    │
# │ • HOST MACHINE: <REPO_ROOT>/samples/security-evaluator/reports/         │
# │   Example: /home/user/PyRIT/samples/security-evaluator/reports/         │
# │            pyrit_ollama_demo.db (PHYSICALLY ON LINUX/MAC HOST)         │
# │                                                                         │
# │ • Containers access via VOLUME MOUNT:                                    │
# │   /workspace/samples/security-evaluator/reports/pyrit_ollama_demo.db   │
# │   (inside container, points to same host file)                          │
# └─────────────────────────────────────────────────────────────────────────┘
#
# HOW DOCKER CONTAINERS SHARE THE DATABASE:
# 1. docker-compose.yaml defines: volumes: ../../:/workspace
# 2. This binds HOST REPO ROOT -> /workspace INSIDE CONTAINER
# 3. All containers share same PYRIT_SQLITE_DB_PATH environment variable
# 4. Python sqlite3 module accesses HOST FILE via volume mount
# 5. Multiple containers safely read/write same file (OS-level file locking)
#
# USAGE:
#   chmod +x ./samples/security-evaluator/scripts/installers/setup_sqlite_linux.sh
#   ./samples/security-evaluator/scripts/installers/setup_sqlite_linux.sh
#
#   # Custom database path:
#   DB_DIR=/custom/path ./samples/security-evaluator/scripts/installers/setup_sqlite_linux.sh
#
# ENVIRONMENT VARIABLES (optional):
#   SKIP_INSTALL     - Skip SQLite binary installation, only create DB
#   SKIP_TEST        - Skip database connectivity test
#   DB_DIR           - Custom database directory
#   DB_PATH          - Full custom database file path
#
################################################################################

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;36m'
NC='\033[0m' # No Color

# Helper functions
print_info() { echo -e "${BLUE}i  $*${NC}"; }
print_success() { echo -e "${GREEN}v $*${NC}"; }
print_error() { echo -e "${RED}x $*${NC}"; }
print_warn() { echo -e "${YELLOW}! $*${NC}"; }
print_header() { echo ""; echo "=============================================================================="; echo "$*"; echo "=============================================================================="; }
run_as_root() { if [[ $EUID -ne 0 ]]; then sudo "$@"; else "$@"; fi; }

# Detect package manager
detect_pkg_manager() {
  if command -v apt-get &> /dev/null; then echo "apt-get"
  elif command -v dnf &> /dev/null; then echo "dnf"
  elif command -v yum &> /dev/null; then echo "yum"
  elif command -v pacman &> /dev/null; then echo "pacman"
  elif command -v zypper &> /dev/null; then echo "zypper"
  elif command -v brew &> /dev/null; then echo "brew"
  else echo "unknown"; fi
}

# ─────────────────────────────────────────────────────────────────────────────
# MAIN SCRIPT
# ─────────────────────────────────────────────────────────────────────────────

echo ""
echo "SQLite Setup for PyRIT (Linux/macOS)"
echo "Database File Storage & Volume Mounting Guide"
echo ""

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DB_DIR="${DB_DIR:-$(dirname "$SCRIPT_DIR")/../../reports}"
DB_PATH="${DB_PATH:-$DB_DIR/pyrit_ollama_demo.db}"
SKIP_INSTALL="${SKIP_INSTALL:-0}"
SKIP_TEST="${SKIP_TEST:-0}"

# Normalize paths
DB_DIR="$(mkdir -p "$DB_DIR" && cd "$DB_DIR" && pwd)"
DB_PATH="$DB_DIR/pyrit_ollama_demo.db"

print_info "Configuration:"
echo "   Repo root: $(dirname "$DB_DIR")"
echo "   Database directory: $DB_DIR"
echo "   Database file path: $DB_PATH"
echo "   Skip install: $SKIP_INSTALL"
echo ""

# ─────────────────────────────────────────────────────────────────────────────
# STEP 1: Install SQLite Binary
# ─────────────────────────────────────────────────────────────────────────────

if [[ "$SKIP_INSTALL" != "1" ]]; then
    print_header "STEP 1: Installing SQLite Binary"

    if command -v sqlite3 &> /dev/null; then
        print_success "SQLite already installed"
        SQLITE_PATH=$(command -v sqlite3)
        SQLITE_VER=$(sqlite3 --version)
        print_info "  Path: $SQLITE_PATH"
        print_info "  Version: $SQLITE_VER"
    else
        print_info "SQLite not found, attempting installation..."
        echo ""

        PKG_MGR=$(detect_pkg_manager)
        print_info "Detected package manager: $PKG_MGR"
        echo ""

        case "$PKG_MGR" in
            apt-get)
                print_info "Running: apt-get update && apt-get install -y sqlite3"
                run_as_root apt-get update -qq
                run_as_root apt-get install -y -qq sqlite3 libsqlite3-dev
                print_success "Installed via apt"
                print_info "  Location: /usr/bin/sqlite3"
                ;;
            dnf)
                print_info "Running: dnf install -y sqlite"
                run_as_root dnf install -y -q sqlite sqlite-devel
                print_success "Installed via dnf"
                print_info "  Location: /usr/bin/sqlite3"
                ;;
            yum)
                print_info "Running: yum install -y sqlite"
                run_as_root yum install -y -q sqlite sqlite-devel
                print_success "Installed via yum"
                print_info "  Location: /usr/bin/sqlite3"
                ;;
            pacman)
                print_info "Running: pacman -Sy --noconfirm sqlite"
                run_as_root pacman -Sy --noconfirm -q sqlite
                print_success "Installed via pacman"
                print_info "  Location: /usr/bin/sqlite3"
                ;;
            zypper)
                print_info "Running: zypper install sqlite3"
                run_as_root zypper --non-interactive install -q sqlite3 sqlite3-devel
                print_success "Installed via zypper"
                print_info "  Location: /usr/bin/sqlite3"
                ;;
            brew)
                print_info "Running: brew install sqlite3"
                brew install sqlite3 2>&1 | grep -v "Warning" || true
                print_success "Installed via Homebrew"
                print_info "  Location: $(command -v sqlite3 || echo /usr/local/bin/sqlite3)"
                ;;
            *)
                print_error "Unknown package manager. Install sqlite3 manually."
                exit 1
                ;;
        esac

        # Verify
        if ! command -v sqlite3 &> /dev/null; then
            print_warn "sqlite3 command not found after installation (may need new shell)"
            print_warn "Try: exec bash"
            exit 1
        fi

        SQLITE_VER=$(sqlite3 --version)
        print_success "SQLite available: $SQLITE_VER"
    fi

    echo ""
else
    print_info "Skipping SQLite binary installation (SKIP_INSTALL=1)"
    echo ""
fi

# ─────────────────────────────────────────────────────────────────────────────
# STEP 2: Create Database Directory
# ─────────────────────────────────────────────────────────────────────────────

print_header "STEP 2: Creating Database Directory"

if [[ -d "$DB_DIR" ]]; then
    print_success "Directory exists: $DB_DIR"
else
    print_info "Creating directory: $DB_DIR"
    mkdir -p "$DB_DIR" || { print_error "Failed to create directory"; exit 1; }
    print_success "Directory created"
fi

# Check permissions
if [[ ! -w "$DB_DIR" ]]; then
    print_error "No write permission to $DB_DIR"
    exit 1
fi

print_success "Write permissions OK"
echo ""

# ─────────────────────────────────────────────────────────────────────────────
# STEP 3: Initialize Database File
# ─────────────────────────────────────────────────────────────────────────────

print_header "STEP 3: Initializing Database File"

if [[ -f "$DB_PATH" ]]; then
    SIZE=$(stat -c%s "$DB_PATH" 2>/dev/null || stat -f%z "$DB_PATH" 2>/dev/null || echo "unknown")
    print_success "Database file exists: $DB_PATH"
    print_info "  Size: $SIZE bytes"
else
    print_info "Creating database file: $DB_PATH"
    if sqlite3 "$DB_PATH" "SELECT 1;" &>/dev/null; then
        SIZE=$(stat -c%s "$DB_PATH" 2>/dev/null || stat -f%z "$DB_PATH" 2>/dev/null)
        print_success "Database file created"
        print_info "  Size: $SIZE bytes"
    else
        print_error "Failed to create database file"
        exit 1
    fi
fi

echo ""

# ─────────────────────────────────────────────────────────────────────────────
# STEP 4: Verify Database
# ─────────────────────────────────────────────────────────────────────────────

print_header "STEP 4: Verifying Database"

if VER=$(sqlite3 "$DB_PATH" "SELECT sqlite_version();" 2>&1); then
    print_success "SQLite version: $VER"
else
    print_error "Failed to verify database: $VER"
    exit 1
fi

TABLES=$(sqlite3 "$DB_PATH" ".tables" 2>/dev/null || echo "")
if [[ -z "$TABLES" ]]; then
    print_info "Database is empty (no tables yet)"
    print_info "Tables will be created when PyRIT runs"
else
    print_success "Database contains tables: $TABLES"
fi

echo ""

# ─────────────────────────────────────────────────────────────────────────────
# STEP 5: Test Connection (optional)
# ─────────────────────────────────────────────────────────────────────────────

if [[ "$SKIP_TEST" != "1" ]]; then
    print_header "STEP 5: Testing Database Connection"

    if sqlite3 "$DB_PATH" "CREATE TEMPORARY TABLE test (id INTEGER); INSERT INTO test VALUES (1);" 2>/dev/null; then
        print_success "Read/write test passed"
    else
        print_error "Connection test failed"
        exit 1
    fi

    echo ""
fi

# ─────────────────────────────────────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────────────────────────────────────

echo "SQLite Setup Complete"
echo ""
echo "WHERE SQLITE IS NOW:"
echo "─────────────────────────────────────────────────────────────────────────"
echo ""
echo "1. SQLite BINARY (executable) installed on $(uname -s):"
SQLITE_PATH=$(command -v sqlite3)
echo "   Location: $SQLITE_PATH"
echo "   Verify: sqlite3 --version"
echo ""
echo "2. DATABASE FILE (data) stored on HOST MACHINE:"
echo "   Physical location: $DB_PATH"
echo "   This file persists on your disk"
echo ""
echo "3. CONTAINERS access database via VOLUME MOUNT:"
echo "   Inside container path: /workspace/samples/security-evaluator/reports/pyrit_ollama_demo.db"
echo "   docker-compose.yaml: volumes: ../../:/workspace"
echo "   All containers see same file on host"
echo ""
echo "4. HOW MULTIPLE CONTAINERS SHARE THE DATABASE:"
echo "   copyrit, jupyter, gui containers all set:"
echo "   PYRIT_SQLITE_DB_PATH=/workspace/.../pyrit_ollama_demo.db"
echo "   Volume mount ensures they access same HOST file"
echo "   SQLite file locking (journaling) prevents conflicts"
echo "   Changes visible immediately across all containers"
echo ""
echo "NEXT STEPS:"
echo "─────────────────────────────────────────────────────────────────────────"
echo ""
echo "1. Start Docker containers:"
echo "   docker compose -f samples/security-evaluator/docker-compose.yaml up -d"
echo ""
echo "2. Verify database is accessible from container:"
echo "   docker compose -f samples/security-evaluator/docker-compose.yaml exec copyrit bash"
echo "   # Inside container:"
echo "   ls -la /workspace/samples/security-evaluator/reports/"
echo "   sqlite3 /workspace/samples/security-evaluator/reports/pyrit_ollama_demo.db '.tables'"
echo ""
echo "3. Run PyRIT (database tables created automatically):"
echo "   pyrit --dry-run --attack-mode baseline ..."
echo ""
echo "4. Verify database from HOST ($(uname -s)):"
echo "   sqlite3 '$DB_PATH' '.tables'"
echo ""
echo "=============================================================================="
echo ""
