#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# setup_sqlite_linux.sh � SQLite + PyRIT installer for Linux
# ============================================================================
# Can be run directly OR sourced by the main installer.
#
# Usage:
#   chmod +x samples/security-evaluator/scripts/installers/setup_sqlite_linux.sh
#   ./samples/security-evaluator/scripts/installers/setup_sqlite_linux.sh
#
# Optional environment variables:
#   PYRIT_DB_PATH    (default: ./pyrit_linux_demo.db)
#   USE_VENV         (default: true)
#   VENV_DIR         (default: .venv)
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common/lib_common.sh"

PYRIT_DB_PATH="${PYRIT_DB_PATH:-./pyrit_linux_demo.db}"

install_sqlite_linux() {
  if command -v sqlite3 >/dev/null 2>&1; then
    print_ok "sqlite3 already installed: $(sqlite3 --version)"
    return
  fi

  print_header "Installing sqlite3"
  PKG_MGR="$(detect_pkg_manager)"

  case "$PKG_MGR" in
    apt-get)
      run_as_root apt-get update
      run_as_root apt-get install -y sqlite3 libsqlite3-dev
      ;;
    dnf)
      run_as_root dnf install -y sqlite sqlite-devel
      ;;
    yum)
      run_as_root yum install -y sqlite sqlite-devel
      ;;
    pacman)
      run_as_root pacman -Sy --noconfirm sqlite
      ;;
    zypper)
      run_as_root zypper --non-interactive install sqlite3 sqlite3-devel
      ;;
    *)
      print_err "No supported package manager found. Install sqlite3 manually."
      exit 1
      ;;
  esac

  print_ok "sqlite3 installed: $(sqlite3 --version)"
}

main() {
  print_header "Linux SQLite + PyRIT setup"
  install_sqlite_linux
  setup_python_env
  run_pyrit_sqlite_smoke_test

  print_header "Done"
  print_ok "SQLite is installed and PyRIT is integrated with SQLITE memory."
  print_info "DB file path: $PYRIT_DB_PATH"
}

# Run only when executed directly (not when sourced by another script).
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  main "$@"
fi
