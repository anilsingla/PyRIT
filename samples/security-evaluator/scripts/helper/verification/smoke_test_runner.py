#!/usr/bin/env python3
"""Run a lightweight dry-run smoke check for the security-evaluator runner CLI."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path


SAMPLE_DIR = Path(__file__).resolve().parents[3]
PYTHON_EXE = sys.executable
RUNNER = SAMPLE_DIR / "scripts" / "app" / "main.py"

MODES = [
    ["--dry-run"],
    ["--attack-mode", "baseline", "--dry-run", "--max-seeds", "1"],
    ["--attack-mode", "redteam", "--dry-run", "--scenarios", "LLM01"],
    ["--attack-mode", "tap", "--dry-run", "--scenarios", "LLM01"],
    ["--attack-mode", "crescendo", "--dry-run", "--scenarios", "LLM01"],
    ["--attack-mode", "xpia", "--dry-run", "--scenarios", "LLM02"],
]


def _missing_dependencies() -> list[str]:
    """Return runner dependencies that are not importable in this environment."""
    missing = []
    for module_name in ("pyrit", "sqlalchemy"):
        if importlib.util.find_spec(module_name) is None:
            missing.append(module_name)
    return missing


def main() -> int:
    """Run a small set of CLI parse checks."""
    missing = _missing_dependencies()
    if missing:
        print("RUNNER_SMOKE_SKIPPED")
        print(f"Missing dependencies: {', '.join(missing)}")
        print("Install the sample dependencies, then rerun this check for a full dry-run smoke test.")
        return 2

    failures: list[str] = []

    for args in MODES:
        command = [PYTHON_EXE, str(RUNNER), *args]
        result = subprocess.run(command, cwd=str(SAMPLE_DIR), capture_output=True, text=True)
        if result.returncode != 0:
            failures.append(f"{' '.join(args)} -> exit {result.returncode}\n{result.stderr.strip() or result.stdout.strip()}")

    if failures:
        print("RUNNER_SMOKE_FAIL")
        for failure in failures:
            print(failure)
        return 1

    print("RUNNER_SMOKE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
