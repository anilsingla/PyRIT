"""Modular OWASP Ollama red-team runner package."""

from attacks.redteam_attack_runner import run_redteam_suite_async
from .workflow import run_attack_mode_async

__all__ = ["run_attack_mode_async", "run_redteam_suite_async"]
