#!/usr/bin/env bash
# =============================================================================
# lib_common.sh — Shared utilities for security-evaluator installation scripts
# =============================================================================
# Source this file from any installer script:
#   SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
#   source "$SCRIPT_DIR/common/lib_common.sh"
# =============================================================================

# ---- Output helpers ---------------------------------------------------------

print_header() {
  echo
  echo "================================================================"
  echo "$1"
  echo "================================================================"
}

print_ok()   { echo "[OK]   $*"; }
print_info() { echo "[INFO] $*"; }
print_warn() { echo "[WARN] $*"; }
print_err()  { echo "[ERROR] $*" >&2; }

# ---- Privilege helper -------------------------------------------------------

run_as_root() {
  # Runs a command via sudo when available, otherwise runs directly.
  if command -v sudo >/dev/null 2>&1; then
    sudo "$@"
  else
    "$@"
  fi
}

# ---- Package manager detection ----------------------------------------------

detect_pkg_manager() {
  # Echoes the name of the first package manager found on PATH.
  for mgr in apt-get dnf yum pacman zypper; do
    if command -v "$mgr" >/dev/null 2>&1; then
      echo "$mgr"
      return 0
    fi
  done
  echo ""
  return 1
}

# ---- Python environment helpers --------------------------------------------

# Env vars consulted (caller may export before sourcing):
#   USE_VENV   (default: true)   — create/activate .venv when "true"
#   VENV_DIR   (default: .venv)  — path to venv directory

USE_VENV="${USE_VENV:-true}"
VENV_DIR="${VENV_DIR:-.venv}"

require_python3() {
  if ! command -v python3 >/dev/null 2>&1; then
    print_err "python3 is not installed. Please install Python 3.10+ first."
    exit 1
  fi
}

setup_python_env() {
  print_header "Preparing Python environment"
  require_python3

  if [[ "${USE_VENV,,}" == "true" ]]; then
    if [[ ! -d "$VENV_DIR" ]]; then
      python3 -m venv "$VENV_DIR"
    fi
    # shellcheck disable=SC1090
    source "$VENV_DIR/bin/activate"
    print_ok "Virtual environment active: $VENV_DIR"
  else
    print_info "Skipping virtual environment (USE_VENV=false)."
  fi

  python3 -m pip install --upgrade pip
  python3 -m pip install --upgrade pyrit
}

# ---- PyRIT SQLite smoke test -----------------------------------------------

# Env vars:
#   PYRIT_DB_PATH  (default: ./pyrit_demo.db)

PYRIT_DB_PATH="${PYRIT_DB_PATH:-./pyrit_demo.db}"

run_pyrit_sqlite_smoke_test() {
  print_header "PyRIT SQLite smoke test"
  require_python3

  export PYRIT_DB_PATH
  python3 - <<'PY'
import asyncio
import os
from pathlib import Path

from pyrit.setup import SQLITE, initialize_pyrit_async
from pyrit.memory import CentralMemory

DB_PATH = Path(os.environ.get("PYRIT_DB_PATH", "./pyrit_demo.db")).resolve()

async def main() -> None:
    await initialize_pyrit_async(memory_db_type=SQLITE, db_path=str(DB_PATH))
    memory = CentralMemory.get_memory_instance()
    dataset_names = memory.get_seed_dataset_names()
    print(f"[OK] PyRIT initialized with SQLITE at: {DB_PATH}")
    print(f"[INFO] Dataset names: {dataset_names}")

asyncio.run(main())
PY
}
