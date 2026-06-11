"""Shared scorer formatting and validation helpers."""

from __future__ import annotations

from collections.abc import Callable

from app.utils.output_tools import Colors
from scorer.selector import validate_scorer_keys
from scorer.types import (
    format_float_scale_verdict,
    format_generic_verdict,
    format_true_false_verdict,
)

SCORER_DISPLAY_NAMES = {
    "substring": "SubStringScorer",
    "self_ask_true_false": "SelfAskTrueFalseScorer",
    "self_ask_scale": "SelfAskScaleScorer",
    "scale_threshold_0_7": "FloatScaleThresholdScorer",
    "refusal": "SelfAskRefusalScorer",
    "compliance_inverted_refusal": "TrueFalseInverterScorer",
}

SCORER_PRINT_ORDER = [
    "self_ask_true_false",
    "self_ask_scale",
    "scale_threshold_0_7",
    "refusal",
    "compliance_inverted_refusal",
    "substring",
]


def build_default_scorer_payload(
    *,
    score_to_json_dict: Callable[..., dict[str, object]],
) -> dict[str, dict[str, object]]:
    """Return an empty payload scaffold for all standard scorers."""
    return {
        "substring": score_to_json_dict(scorer_name="SubStringScorer", score=None),
        "self_ask_true_false": score_to_json_dict(scorer_name="SelfAskTrueFalseScorer", score=None),
        "self_ask_scale": score_to_json_dict(scorer_name="SelfAskScaleScorer", score=None),
        "scale_threshold_0_7": score_to_json_dict(scorer_name="FloatScaleThresholdScorer", score=None),
        "refusal": score_to_json_dict(scorer_name="SelfAskRefusalScorer", score=None),
        "compliance_inverted_refusal": score_to_json_dict(scorer_name="TrueFalseInverterScorer", score=None),
    }


def _format_verdict_for_score(*, score_type: object, score_value: object) -> tuple[str, str]:
    score_type_text = str(score_type or "").strip().lower()

    if score_type_text == "true_false":
        return format_true_false_verdict(score_value=score_value)

    if score_type_text == "float_scale":
        return format_float_scale_verdict(score_value=score_value)

    return format_generic_verdict(score_value=score_value)


def print_detailed_scorer_outputs(
    *,
    scorer_json: dict[str, dict[str, object]],
    weighted_metrics: dict[str, str],
    response_text: str,
) -> None:
    """Print a consistent, colorized scorer breakdown across attack runners."""
    print(f"{Colors.CYAN}    ┌─ SCORER OUTPUTS {Colors.DIM}{'─' * 43}{Colors.RESET}")

    printed_any = False
    for scorer_key in SCORER_PRINT_ORDER:
        payload = scorer_json.get(scorer_key)
        if payload is None:
            continue
        printed_any = True

        score_value = payload.get("score_value")
        score_type = payload.get("score_type")
        rationale = payload.get("score_rationale") or "n/a"
        verdict, verdict_extra = _format_verdict_for_score(score_type=score_type, score_value=score_value)

        print(f"{Colors.CYAN}    │{Colors.RESET}")
        print(
            f"{Colors.CYAN}    ├─ {SCORER_DISPLAY_NAMES.get(scorer_key, scorer_key)}{Colors.RESET} "
            f"{Colors.DIM}[{scorer_key}]{Colors.RESET}"
        )
        print(f"{Colors.CYAN}    │  ├─ Verdict:{Colors.RESET} {verdict} {verdict_extra}")
        print(f"{Colors.CYAN}    │  ├─ Raw Value:{Colors.RESET} {Colors.WHITE}{score_value}{Colors.RESET}")
        print(f"{Colors.CYAN}    │  ├─ Score Type:{Colors.RESET} {Colors.WHITE}{score_type}{Colors.RESET}")
        print(f"{Colors.CYAN}    │  └─ Rationale:{Colors.RESET} {Colors.WHITE}{rationale}{Colors.RESET}")

    if not printed_any:
        print(f"{Colors.CYAN}    │{Colors.RESET}")
        print(f"{Colors.CYAN}    ├─ No scorer outputs returned for this scenario.{Colors.RESET}")

    print(f"{Colors.CYAN}    │{Colors.RESET}")
    print(f"{Colors.CYAN}    ├─ WEIGHTED AGREEMENT{Colors.RESET}")
    print(
        f"{Colors.CYAN}    │  ├─ Majority:{Colors.RESET} "
        f"{Colors.WHITE}{weighted_metrics.get('weighted_majority', 'n/a')}{Colors.RESET}"
    )
    print(
        f"{Colors.CYAN}    │  ├─ Confidence:{Colors.RESET} "
        f"{Colors.WHITE}{weighted_metrics.get('weighted_confidence', 'n/a')}{Colors.RESET}"
    )
    print(
        f"{Colors.CYAN}    │  ├─ Disagreement:{Colors.RESET} "
        f"{Colors.WHITE}{weighted_metrics.get('weighted_disagreement', 'n/a')}{Colors.RESET}"
    )
    print(
        f"{Colors.CYAN}    │  └─ Scale Vote:{Colors.RESET} "
        f"{Colors.WHITE}{weighted_metrics.get('scale_vote', 'n/a')}"
        f" (raw={weighted_metrics.get('scale_raw', 'n/a')}){Colors.RESET}"
    )

    response_preview = response_text.strip().replace("\n", " ")
    if len(response_preview) > 220:
        response_preview = f"{response_preview[:220]}..."

    print(f"{Colors.CYAN}    │{Colors.RESET}")
    print(f"{Colors.CYAN}    ├─ TARGET RESPONSE PREVIEW{Colors.RESET}")
    print(f"{Colors.CYAN}    │  └─ {Colors.WHITE}{response_preview or 'n/a'}{Colors.RESET}")
    print(f"{Colors.CYAN}    └{'─' * 63}{Colors.RESET}")
