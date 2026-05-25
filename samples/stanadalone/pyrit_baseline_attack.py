#!/usr/bin/env python3
"""Standalone Baseline attack runner with unified professional reporting."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


from pyrit.memory import CentralMemory
from pyrit.setup import initialize_pyrit_async
from pyrit.orchestrator import BaselineAttack

def run_baseline_attack(memory, args):
    # Example: You may need to adapt arguments to BaselineAttack as per your PyRIT version
    attack_runner = BaselineAttack(memory=memory)
    # You may want to pass dataset, model, or other config here
    results = asyncio.run(attack_runner.run())
    return 0 if results else 1


def main() -> int:
    # Initialize PyRIT database (adjust db_path as needed)
    db_path = "pyrit_baseline.db"
    asyncio.run(initialize_pyrit_async(memory_db_type="sqlite", db_path=db_path))
    memory = CentralMemory.get_memory_instance()

    # Parse arguments if needed (optional, or adapt to BaselineAttack requirements)
    # parser = build_common_parser("Standalone baseline attack runner.")
    # args = parser.parse_args()

    try:
        return run_baseline_attack(memory, None)
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())


