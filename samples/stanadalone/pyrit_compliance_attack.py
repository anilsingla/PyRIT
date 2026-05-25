#!/usr/bin/env python3
"""Standalone Compliance attack runner with unified professional reporting."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

script_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(script_dir))

from standalone_banking_attack_common import DualLogger, Colors, initialize_banking_attack_environment, get_centralized_scorers
from pyrit.prompt_target import OpenAIChatTarget
from pyrit.executor.attack import PromptSendingAttack
from pyrit.score import Score

async def run_compliance_attack():
    logger, tests, dataset_path, memory = await initialize_banking_attack_environment(
        script_name="pyrit_compliance_attack", script_dir=script_dir, db_name="pyrit_compliance.db"
    )

    chat_target = OpenAIChatTarget(
        endpoint="https://ollama.o31e.com/v1",
        api_key="dummy",
        model="llama3.2:1b",
        verify_ssl=False,
    )

    scorers = get_centralized_scorers()
    attack = PromptSendingAttack(objective_target=chat_target)

    for test in tests:
        logger.section(f"Test {test.test_number}: {test.objective}")
        result = await attack.execute_async(objective=test.objective)
        logger.info(f"LLM Response: {result.response}")
        for scorer in scorers:
            score = scorer.score(result)
            logger.info(f"Scorer {scorer.__class__.__name__}: {score}")

    logger.ok("All tests complete.")
    logger.close()
    return 0

def main() -> int:
    try:
        return asyncio.run(run_compliance_attack())
    except KeyboardInterrupt:
        return 130

if __name__ == "__main__":
    raise SystemExit(main())
