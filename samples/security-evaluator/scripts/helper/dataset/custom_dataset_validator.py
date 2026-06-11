# pyright: reportMissingImports=false
#!/usr/bin/env python3
"""Validate custom PyRIT datasets and classify groups as single-turn or multi-turn."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

HELPER_DIR = Path(__file__).resolve().parent
if str(HELPER_DIR) not in sys.path:
    sys.path.insert(0, str(HELPER_DIR))

from dataset_format_utils import (
    convert_starter_json_to_pyrit_dict,
    is_starter_dataset_payload,
    load_json_payload,
)
from pyrit.models import SeedDataset
from pyrit.models.seeds.seed_group import SeedGroup
from pyrit.models.seeds.seed_attack_group import SeedAttackGroup
from pyrit.models.seeds.seed_objective import SeedObjective
from pyrit.models.seeds.seed_prompt import SeedPrompt
from pyrit.models.seeds.seed_simulated_conversation import SeedSimulatedConversation


def _build_parser() -> argparse.ArgumentParser:
    """Build command-line parser."""
    parser = argparse.ArgumentParser(
        description="Validate a custom PyRIT dataset file and summarize seed groups.",
    )
    parser.add_argument(
        "input",
        type=Path,
        help="Path to dataset file (.yaml/.yml/.json).",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=None,
        help="Optional path to write validation report JSON.",
    )
    return parser


def _load_dataset(*, input_path: Path) -> SeedDataset:
    """Load dataset from YAML or JSON file."""
    suffix = input_path.suffix.lower()
    if suffix in {".yaml", ".yml", ".prompt"}:
        return SeedDataset.from_yaml_file(str(input_path))

    if suffix == ".json":
        payload = load_json_payload(input_path=input_path)
        if is_starter_dataset_payload(payload=payload):
            payload = convert_starter_json_to_pyrit_dict(payload=payload)
        return SeedDataset.from_dict(payload)

    raise ValueError("Unsupported file extension. Use .yaml, .yml, .prompt, or .json.")


def _classify_turn_type(*, prompts: list[SeedPrompt], has_simulated_conversation: bool) -> str:
    """Classify a seed group as single-turn or multi-turn."""
    if has_simulated_conversation or len(prompts) > 1:
        return "multi_turn"
    if len(prompts) == 1:
        return "single_turn"
    return "no_prompt"


def _analyze_group(*, group_index: int, group: SeedGroup) -> dict[str, Any]:
    """Analyze one seed group and return validation details."""
    prompts = [seed for seed in group.seeds if isinstance(seed, SeedPrompt)]
    objectives = [seed for seed in group.seeds if isinstance(seed, SeedObjective)]
    simulated = [seed for seed in group.seeds if isinstance(seed, SeedSimulatedConversation)]

    group_errors: list[str] = []
    try:
        group.validate()
    except Exception as exc:
        group_errors.append(str(exc))

    sequences = sorted({prompt.sequence for prompt in prompts})
    expected = list(range(min(sequences), max(sequences) + 1)) if sequences else []
    has_sequence_gaps = bool(sequences and sequences != expected)

    if has_sequence_gaps:
        group_errors.append(f"Prompt sequences are not contiguous: found {sequences}.")

    objective_count = len(objectives)
    attack_group_eligible = isinstance(group, SeedAttackGroup)

    if objective_count == 1 and not attack_group_eligible:
        group_errors.append(
            "Group has one objective but failed SeedAttackGroup checks (likely role/sequence consistency issues)."
        )

    if objective_count != 1:
        attack_group_note = "Requires exactly one objective to be attack-ready."
    else:
        attack_group_note = "Eligible for attack workflows."

    return {
        "group_index": group_index,
        "prompt_group_id": str(group.seeds[0].prompt_group_id) if group.seeds and group.seeds[0].prompt_group_id else None,
        "seed_count": len(group.seeds),
        "prompt_count": len(prompts),
        "objective_count": objective_count,
        "simulated_conversation_count": len(simulated),
        "turn_type": _classify_turn_type(prompts=prompts, has_simulated_conversation=bool(simulated)),
        "prompt_sequences": sequences,
        "attack_group_eligible": attack_group_eligible,
        "attack_group_note": attack_group_note,
        "errors": group_errors,
    }


def _build_report(*, dataset: SeedDataset, source_path: Path) -> dict[str, Any]:
    """Build a full dataset validation report."""
    groups = list(dataset.seed_groups)
    group_reports = [_analyze_group(group_index=index + 1, group=group) for index, group in enumerate(groups)]

    errors = [
        f"Group {group_report['group_index']}: {err}"
        for group_report in group_reports
        for err in group_report["errors"]
    ]

    summary = {
        "dataset_name": dataset.dataset_name or dataset.name,
        "source_path": str(source_path.resolve()),
        "total_seeds": len(dataset.seeds),
        "total_groups": len(groups),
        "single_turn_groups": sum(1 for group_report in group_reports if group_report["turn_type"] == "single_turn"),
        "multi_turn_groups": sum(1 for group_report in group_reports if group_report["turn_type"] == "multi_turn"),
        "attack_group_eligible": sum(1 for group_report in group_reports if group_report["attack_group_eligible"]),
        "error_count": len(errors),
    }

    return {
        "valid": len(errors) == 0,
        "summary": summary,
        "errors": errors,
        "groups": group_reports,
    }


def _print_report(*, report: dict[str, Any]) -> None:
    """Print a concise human-readable report."""
    summary = report["summary"]

    print("=== PyRIT Custom Dataset Validation ===")
    print(f"Dataset           : {summary['dataset_name']}")
    print(f"Total seeds       : {summary['total_seeds']}")
    print(f"Total groups      : {summary['total_groups']}")
    print(f"Single-turn groups: {summary['single_turn_groups']}")
    print(f"Multi-turn groups : {summary['multi_turn_groups']}")
    print(f"Attack-ready groups: {summary['attack_group_eligible']}")
    print(f"Errors            : {summary['error_count']}")

    for group_report in report["groups"]:
        print(
            f"\n[Group {group_report['group_index']}] "
            f"type={group_report['turn_type']} "
            f"prompts={group_report['prompt_count']} "
            f"objectives={group_report['objective_count']} "
            f"attack_ready={group_report['attack_group_eligible']}"
        )
        if group_report["prompt_sequences"]:
            print(f"  sequences: {group_report['prompt_sequences']}")
        print(f"  note: {group_report['attack_group_note']}")
        if group_report["errors"]:
            for error in group_report["errors"]:
                print(f"  ERROR: {error}")


def _write_report_json(*, report: dict[str, Any], output_path: Path) -> None:
    """Write report as JSON file."""
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")


def main() -> int:
    """Run validator CLI."""
    parser = _build_parser()
    args = parser.parse_args()

    input_path: Path = args.input
    output_json: Path | None = args.output_json

    if not input_path.exists():
        print(f"Input file not found: {input_path}", file=sys.stderr)
        return 2

    try:
        dataset = _load_dataset(input_path=input_path)
        report = _build_report(dataset=dataset, source_path=input_path)
        _print_report(report=report)

        if output_json is not None:
            _write_report_json(report=report, output_path=output_json)
            print(f"\nJSON report written to: {output_json.resolve()}")

        if report["valid"]:
            print("\nValidation passed.")
            return 0

        print("\nValidation failed.")
        return 1
    except Exception as exc:
        print(f"Validation error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
