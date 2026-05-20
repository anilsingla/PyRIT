"""Common scorer selection helpers used by runners."""

from __future__ import annotations


def validate_scorer_keys(*, selected_scorers: set[str] | None, available_scorer_keys: list[str]) -> None:
    """Validate optional scorer selection against known keys."""
    if not selected_scorers:
        return

    invalid = sorted(set(selected_scorers) - set(available_scorer_keys))
    if invalid:
        raise ValueError(
            f"Unsupported scorer key(s): {', '.join(invalid)}. "
            f"Supported keys: {', '.join(available_scorer_keys)}"
        )


def resolve_requested_scorers(
    *,
    selected_scorers: set[str] | None,
    available_scorer_keys: tuple[str, ...] | list[str],
    scorer_dependencies: dict[str, set[str]],
) -> set[str]:
    """Resolve explicit scorer selection including dependency scorers."""
    requested_scorers = set(available_scorer_keys) if not selected_scorers else set(selected_scorers)
    for scorer_key in list(requested_scorers):
        requested_scorers.update(scorer_dependencies.get(scorer_key, set()))
    return requested_scorers


def build_run_flags(*, requested_scorers: set[str]) -> dict[str, bool]:
    """Convert requested scorer keys to runner-friendly execution flags."""
    return {
        "run_substring": "substring" in requested_scorers,
        "run_tf": "self_ask_true_false" in requested_scorers,
        "run_scale": "self_ask_scale" in requested_scorers or "scale_threshold_0_7" in requested_scorers,
        "run_threshold": "scale_threshold_0_7" in requested_scorers,
        "run_refusal": "refusal" in requested_scorers or "compliance_inverted_refusal" in requested_scorers,
        "run_compliance": "compliance_inverted_refusal" in requested_scorers,
    }
