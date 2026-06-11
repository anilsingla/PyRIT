"""Verdict formatting for true/false scorers."""

from __future__ import annotations

from app.utils.output_tools import Colors


def to_bool_or_none(*, value: object) -> bool | None:
    """Normalize bool-like values produced by scorers."""
    normalized = str(value).strip().lower()
    if normalized in {"true", "1", "yes", "y"}:
        return True
    if normalized in {"false", "0", "no", "n"}:
        return False
    return None


def format_true_false_verdict(*, score_value: object) -> tuple[str, str]:
    """Return a professional colorized verdict for true/false score values."""
    verdict_bool = to_bool_or_none(value=score_value)
    if verdict_bool is True:
        return (
            f"{Colors.RED}ATTACK SUCCEEDED{Colors.RESET}",
            f"{Colors.RED}(vulnerability confirmed){Colors.RESET}",
        )
    if verdict_bool is False:
        return (
            f"{Colors.GREEN}ATTACK BLOCKED{Colors.RESET}",
            f"{Colors.GREEN}(system refused objective){Colors.RESET}",
        )
    return (
        f"{Colors.YELLOW}INCONCLUSIVE{Colors.RESET}",
        f"{Colors.YELLOW}(unrecognized true/false value){Colors.RESET}",
    )
