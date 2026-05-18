#!/usr/bin/env python3
"""Thin entrypoint for the modular security-evaluator installer."""

from __future__ import annotations

import sys
from pathlib import Path

SAMPLE_DIR = Path(__file__).resolve().parents[2]
if str(SAMPLE_DIR) not in sys.path:
    sys.path.insert(0, str(SAMPLE_DIR))

from scripts.installers.setup_wizard import run_wizard


def main() -> int:
    """Run the modular installer workflow."""
    return run_wizard(python_exe=sys.executable)


if __name__ == "__main__":
    raise SystemExit(main())

