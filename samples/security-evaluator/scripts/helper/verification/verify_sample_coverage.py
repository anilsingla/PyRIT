#!/usr/bin/env python3
"""Verify samples/security-evaluator coverage requirements.

Checks:
1) Scorer coverage: all defined scorer keys are available through the runner.
2) Dataset coverage: all-datasets mode wiring exists and dataset provider is referenced.
3) Custom dataset: required banking dataset file exists and is valid starter JSON.
4) Artifact coverage: report and log output structure keys are present.
"""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
from typing import Any


SAMPLE_ROOT = Path(__file__).resolve().parents[3]
MAIN_PY = SAMPLE_ROOT / "scripts" / "app" / "main.py"
SCORING_OPS_PY = SAMPLE_ROOT / "scripts" / "app" / "redteam_runner" / "scoring_ops.py"
REPORTING_OPS_PY = SAMPLE_ROOT / "scripts" / "app" / "redteam_runner" / "reporting_ops.py"
ENV_CONFIG_PY = SAMPLE_ROOT / "scripts" / "app" / "redteam_runner" / "env_config.py"
BANKING_DATASET_JSON = SAMPLE_ROOT / "custom_datasets" / "banking_app_security_dataset.json"

REQUIRED_SCORER_KEYS = {
    "substring",
    "self_ask_true_false",
    "self_ask_scale",
    "scale_threshold_0_7",
    "refusal",
    "compliance_inverted_refusal",
}

REQUIRED_REPORT_PATH_KEYS = {
    "run_root",
    "cases_root",
    "scorer_comparison_csv",
    "scorer_outputs_json",
    "batch_scorer_check_json",
    "run_report_json",
    "run_report_html",
    "run_report_md",
    "report_summary_json",
    "all_selection_comparison_json",
}

REQUIRED_LOG_CONSTANTS = {
    "PRODUCTION_RUN_LOG_PATH",
    "PRODUCTION_RUN_CHECKPOINT_PATH",
    "LOGS_ROOT_PATH",
}


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _extract_tuple_constant_strings(path: Path, constant_name: str) -> set[str]:
    module = ast.parse(_read_text(path))
    for node in module.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == constant_name and isinstance(node.value, ast.Tuple):
                    values: set[str] = set()
                    for element in node.value.elts:
                        if isinstance(element, ast.Constant) and isinstance(element.value, str):
                            values.add(element.value)
                    return values
        if isinstance(node, ast.AnnAssign):
            target = node.target
            if isinstance(target, ast.Name) and target.id == constant_name and isinstance(node.value, ast.Tuple):
                values = set()
                for element in node.value.elts:
                    if isinstance(element, ast.Constant) and isinstance(element.value, str):
                        values.add(element.value)
                return values
    return set()


def _extract_return_dict_keys(path: Path, function_name: str) -> set[str]:
    module = ast.parse(_read_text(path))
    for node in module.body:
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            for statement in node.body:
                if isinstance(statement, ast.Return) and isinstance(statement.value, ast.Dict):
                    keys: set[str] = set()
                    for key in statement.value.keys:
                        if isinstance(key, ast.Constant) and isinstance(key.value, str):
                            keys.add(key.value)
                    return keys
    return set()


def _contains_tokens(path: Path, tokens: set[str]) -> bool:
    text = _read_text(path)
    return all(token in text for token in tokens)


def _validate_banking_dataset(path: Path) -> tuple[bool, str]:
    if not path.exists():
        return False, f"Missing required custom dataset: {path}"

    try:
        payload = json.loads(_read_text(path))
    except Exception as exc:
        return False, f"Invalid JSON in custom dataset: {exc}"

    if not isinstance(payload, dict):
        return False, "Custom dataset must be a JSON object"

    dataset_name = str(payload.get("dataset_name", "")).strip()
    dataset_type = str(payload.get("dataset_type", "")).strip()
    seeds = payload.get("seeds")

    if dataset_name != "banking_app_security_dataset":
        return False, "Custom dataset_name must be 'banking_app_security_dataset'"

    if dataset_type != "single-turn":
        return False, "Custom banking dataset must be single-turn for this sample"

    if not isinstance(seeds, list) or not seeds:
        return False, "Custom banking dataset must include at least one seed"

    return True, f"Custom banking dataset valid with {len(seeds)} seed(s)"


def run_verification() -> dict[str, Any]:
    scoring_keys = _extract_tuple_constant_strings(SCORING_OPS_PY, "AVAILABLE_SCORER_KEYS")
    report_keys = _extract_return_dict_keys(REPORTING_OPS_PY, "build_run_report_paths")

    scorer_ok = REQUIRED_SCORER_KEYS.issubset(scoring_keys)
    main_all_flags_ok = _contains_tokens(MAIN_PY, {"--all-scorers", "--all-datasets"})
    dataset_provider_ok = _contains_tokens(ENV_CONFIG_PY, {"get_all_dataset_names"})
    report_ok = REQUIRED_REPORT_PATH_KEYS.issubset(report_keys)
    logs_ok = _contains_tokens(REPORTING_OPS_PY, REQUIRED_LOG_CONSTANTS)
    banking_ok, banking_message = _validate_banking_dataset(BANKING_DATASET_JSON)

    overall_ok = all(
        [
            scorer_ok,
            main_all_flags_ok,
            dataset_provider_ok,
            report_ok,
            logs_ok,
            banking_ok,
        ]
    )

    return {
        "overall_ok": overall_ok,
        "checks": {
            "all_scorers_defined": {
                "ok": scorer_ok,
                "expected": sorted(REQUIRED_SCORER_KEYS),
                "found": sorted(scoring_keys),
            },
            "all_scorers_and_datasets_cli_flags": {
                "ok": main_all_flags_ok,
                "required_flags": ["--all-scorers", "--all-datasets"],
            },
            "all_datasets_provider_hook": {
                "ok": dataset_provider_ok,
                "required_symbol": "get_all_dataset_names",
            },
            "report_structure_coverage": {
                "ok": report_ok,
                "expected_keys": sorted(REQUIRED_REPORT_PATH_KEYS),
                "found_keys": sorted(report_keys),
            },
            "log_structure_coverage": {
                "ok": logs_ok,
                "required_constants": sorted(REQUIRED_LOG_CONSTANTS),
            },
            "banking_custom_dataset": {
                "ok": banking_ok,
                "message": banking_message,
                "path": str(BANKING_DATASET_JSON.relative_to(SAMPLE_ROOT)),
            },
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify sample coverage requirements for security-evaluator.")
    parser.add_argument(
        "--output-json",
        type=Path,
        default=None,
        help="Optional path to write machine-readable verification results.",
    )
    args = parser.parse_args()

    result = run_verification()

    print("=== security-evaluator coverage verification ===")
    print(f"overall_ok: {result['overall_ok']}")

    checks = result["checks"]
    for name, payload in checks.items():
        status = "PASS" if payload.get("ok") else "FAIL"
        print(f"- {name}: {status}")

    if args.output_json is not None:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"wrote: {args.output_json}")

    return 0 if result["overall_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
