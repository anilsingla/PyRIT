#!/usr/bin/env python3
"""Standalone consolidated test runner with unified professional reporting."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


from pyrit.memory import CentralMemory
from pyrit.setup import initialize_pyrit_async
from pyrit.orchestrator import BaselineAttack
from pyrit.score import get_all_scorers

def run_test_attack(memory, args):
    attack_runner = BaselineAttack(memory=memory)
    results = asyncio.run(attack_runner.run())
    # Show all scorer results
    for result in results:
        for scorer in get_all_scorers():
            score = scorer.score(result)
            print(f"Scorer {scorer.__class__.__name__}: {score}")
    return 0 if results else 1


def main() -> int:

    db_path = "pyrit_test.db"
    asyncio.run(initialize_pyrit_async(memory_db_type="sqlite", db_path=db_path))
    memory = CentralMemory.get_memory_instance()
    return run_test_attack(memory, None)


if __name__ == "__main__":
    raise SystemExit(main())
