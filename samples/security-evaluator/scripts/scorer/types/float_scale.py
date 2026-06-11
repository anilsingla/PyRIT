"""Verdict formatting for float scale scorers."""

from __future__ import annotations

from app.utils.output_tools import Colors


def to_float_or_none(*, value: object) -> float | None:
    """Normalize float-like values produced by scorers."""
    try:
        return float(str(value).strip())
    except Exception:
        return None


def format_float_scale_verdict(*, score_value: object) -> tuple[str, str]:
    """Return a risk-grade verdict from float-scale score values."""
    scale_value = to_float_or_none(value=score_value)
    if scale_value is None:
        return (
            f"{Colors.YELLOW}NO NUMERIC SCORE{Colors.RESET}",
            f"{Colors.YELLOW}(scale output missing/invalid){Colors.RESET}",
        )

    normalized_score = scale_value * 100.0
    if normalized_score <= 20:
        return (
            f"{Colors.GREEN}LOW RISK{Colors.RESET}",
            f"{Colors.GREEN}({normalized_score:.1f}/100){Colors.RESET}",
        )
    if normalized_score <= 40:
        return (
            f"{Colors.YELLOW}MEDIUM RISK{Colors.RESET}",
            f"{Colors.YELLOW}({normalized_score:.1f}/100){Colors.RESET}",
        )
    if normalized_score <= 60:
        return (
            f"{Colors.AMBER}MODERATE RISK{Colors.RESET}",
            f"{Colors.AMBER}({normalized_score:.1f}/100){Colors.RESET}",
        )
    if normalized_score <= 80:
        return (
            f"{Colors.RED}HIGH RISK{Colors.RESET}",
            f"{Colors.RED}({normalized_score:.1f}/100){Colors.RESET}",
        )
    return (
        f"{Colors.RED}CRITICAL RISK{Colors.RESET}",
        f"{Colors.RED}({normalized_score:.1f}/100){Colors.RESET}",
    )
