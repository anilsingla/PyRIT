"""Generic verdict formatting fallback."""

from __future__ import annotations

from app.utils.output_tools import Colors
from scorer.types.true_false import to_bool_or_none


def format_generic_verdict(*, score_value: object) -> tuple[str, str]:
    """Return a generic verdict for untyped or unknown scorer outputs."""
    generic_bool = to_bool_or_none(value=score_value)
    if generic_bool is True:
        return (f"{Colors.RED}TRUE{Colors.RESET}", f"{Colors.RED}(triggered){Colors.RESET}")
    if generic_bool is False:
        return (f"{Colors.GREEN}FALSE{Colors.RESET}", f"{Colors.GREEN}(not triggered){Colors.RESET}")
    return (f"{Colors.WHITE}VALUE RECORDED{Colors.RESET}", "")
