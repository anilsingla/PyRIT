#!/usr/bin/env python3
"""Standalone Baseline attack runner with unified professional reporting."""

from __future__ import annotations



# --- Ensure latest PyRIT repo is importable ---
import sys
from pathlib import Path
script_dir = Path(__file__).resolve().parent
# Set this to your local clone of the latest PyRIT repo
pyrit_repo = Path("c:/githubrepos/Anil_github_repos/PyRIT/pyrit")
if str(pyrit_repo.parent) not in sys.path:
    sys.path.insert(0, str(pyrit_repo.parent))
sys.path.insert(0, str(script_dir))

import asyncio


# Only import what is used
from standalone_banking_attack_common import initialize_banking_attack_environment, get_centralized_scorers
from pyrit.prompt_target import OpenAIChatTarget
from pyrit.executor.attack import PromptSendingAttack

DEFAULT_OLLAMA_ENDPOINT = "https://ollama.o31e.com/v1"
DEFAULT_OLLAMA_MODEL = "llama3.2:1b"


from standalone_banking_attack_common import CentralizedScorerRunner

async def run_baseline_attack():
    logger, tests, dataset_path, memory = await initialize_banking_attack_environment(
        script_name="pyrit_baseline_attack", script_dir=script_dir, db_name="pyrit_baseline.db"
    )

    chat_target = OpenAIChatTarget(
        endpoint=DEFAULT_OLLAMA_ENDPOINT,
        api_key="dummy",
        model=DEFAULT_OLLAMA_MODEL,
        verify_ssl=False,
    )

    scorers = get_centralized_scorers()
    attack = PromptSendingAttack(objective_target=chat_target)
    runner = CentralizedScorerRunner(logger, scorers)
    await runner.run(tests, attack)
    return 0

def main() -> int:
    try:
        return asyncio.run(run_baseline_attack())
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())


