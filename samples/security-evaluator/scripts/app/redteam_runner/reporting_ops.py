"""Reporting, checkpoint, and production log helpers."""

from __future__ import annotations

import csv
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ARTIFACTS_ROOT_PATH = Path(os.getenv("ARTIFACTS_ROOT_PATH", "reports")).resolve()
REPORTS_ROOT_PATH = Path(os.getenv("REPORTS_ROOT_PATH", str((ARTIFACTS_ROOT_PATH / "cases").resolve()))).resolve()
LOGS_ROOT_PATH = Path(os.getenv("LOGS_ROOT_PATH", "logs")).resolve()

BATCH_SCORER_CHECK_JSON_PATH = Path(
    os.getenv("BATCH_SCORER_CHECK_JSON_PATH", str((ARTIFACTS_ROOT_PATH / "batch_scorer_check.json").resolve()))
).resolve()
RUN_REPORT_JSON_PATH = Path(
    os.getenv("RUN_REPORT_JSON_PATH", str((ARTIFACTS_ROOT_PATH / "run_report.json").resolve()))
).resolve()
SCORER_COMPARISON_CSV_PATH = Path(
    os.getenv("SCORER_COMPARISON_CSV_PATH", str((ARTIFACTS_ROOT_PATH / "scorer_comparison.csv").resolve()))
).resolve()
SCORER_OUTPUTS_JSON_PATH = Path(
    os.getenv("SCORER_OUTPUTS_JSON_PATH", str((ARTIFACTS_ROOT_PATH / "scorer_outputs.json").resolve()))
).resolve()
PRODUCTION_RUN_LOG_PATH = Path(
    os.getenv("PRODUCTION_RUN_LOG_PATH", str((LOGS_ROOT_PATH / "pyrit_owasp_redteam_production.log").resolve()))
).resolve()
PRODUCTION_RUN_CHECKPOINT_PATH = Path(
    os.getenv(
        "PRODUCTION_RUN_CHECKPOINT_PATH",
        str((LOGS_ROOT_PATH / "pyrit_owasp_redteam_production_checkpoint.json").resolve()),
    )
).resolve()
RESUME_INCOMPLETE_RUN = os.getenv("RESUME_INCOMPLETE_RUN", "true").strip().lower() in {
    "1",
    "true",
    "yes",
    "y",
    "on",
}


def debug_log(*, message: str) -> None:
    del message


def _join_slug_parts(*, values: list[str], empty_label: str) -> str:
    parts: list[str] = []
    for value in values:
        slug = slugify_for_path(value=value)
        if slug:
            parts.append(slug)
    if not parts:
        return empty_label
    return "__".join(parts)


def build_run_artifacts_root(
    *,
    attack_mode: str,
    dataset_names: list[str],
    scorer_names: list[str],
    run_id: str | None = None,
) -> Path:
    """Build a run-specific report root keyed by attack mode, datasets, and scorers."""
    dataset_slug = f"datasets__{_join_slug_parts(values=sorted(set(dataset_names)), empty_label='all')}"
    scorer_slug = f"scorers__{_join_slug_parts(values=sorted(set(scorer_names)), empty_label='all')}"
    timestamp_slug = run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return ARTIFACTS_ROOT_PATH / slugify_for_path(value=attack_mode) / dataset_slug / scorer_slug / timestamp_slug


def build_run_report_paths(*, run_root: Path) -> dict[str, Path]:
    """Return the standard artifact paths for a single run."""
    return {
        "run_root": run_root,
        "cases_root": run_root / "cases",
        "scorer_comparison_csv": run_root / "scorer_comparison.csv",
        "scorer_outputs_json": run_root / "scorer_outputs.json",
        "batch_scorer_check_json": run_root / "batch_scorer_check.json",
        "run_report_json": run_root / "run_report.json",
        "run_report_html": run_root / "run_report.html",
        "run_report_md": run_root / "run_report.md",
        "report_summary_json": run_root / "report_summary.json",
        "all_selection_comparison_json": run_root / "all_selection_comparison_report.json",
    }


def export_scorer_comparison_csv(*, rows: list[dict[str, str]], output_path: Path | None = None) -> None:
    """Export flattened scorer comparison rows to CSV."""
    if not rows:
        return

    target_path = output_path or SCORER_COMPARISON_CSV_PATH
    target_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "owasp_id",
        "owasp_name",
        "self_ask_true_false",
        "self_ask_scale",
        "scale_threshold_0_7",
        "refusal",
        "compliance_inverted_refusal",
        "substring",
        "weighted_majority",
        "weighted_confidence",
        "weighted_disagreement",
        "scale_raw",
        "scale_vote",
    ]

    with target_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def export_scorer_outputs_json(*, rows: list[dict[str, object]], output_path: Path | None = None) -> None:
    """Export detailed scorer JSON records."""
    payload = {
        "description": "Per-scenario scorer outputs and score metadata",
        "rows": rows,
    }
    target_path = output_path or SCORER_OUTPUTS_JSON_PATH
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def export_batch_scorer_check_json(*, payload: dict[str, object], output_path: Path | None = None) -> None:
    """Export BatchScorer applicability check details as JSON."""
    target_path = output_path or BATCH_SCORER_CHECK_JSON_PATH
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def export_run_report_json(*, payload: dict[str, object], output_path: Path | None = None) -> None:
    """Export a consolidated run report JSON with links to all outputs."""
    target_path = output_path or RUN_REPORT_JSON_PATH
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def slugify_for_path(*, value: str) -> str:
    """Convert text to a path-safe lowercase slug."""
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "_", value.strip().lower())
    return slug.strip("_") or "unknown"


def export_per_scorer_case_reports(
    *,
    owasp_id: str,
    owasp_name: str,
    dataset_name: str,
    seed_group_name: str,
    objective: str,
    scorer_payloads: dict[str, dict[str, object]],
    scenario_index: int,
    case_index: int,
    error: str | None = None,
    cases_root: Path | None = None,
) -> list[str]:
    """Export per-case scorer JSON reports in hierarchy: scenario/dataset/seed_group/scorer."""
    scenario_slug = slugify_for_path(value=f"{owasp_id}_{owasp_name}")
    dataset_slug = slugify_for_path(value=dataset_name)
    seed_group_slug = slugify_for_path(value=seed_group_name)
    target_root = cases_root or REPORTS_ROOT_PATH
    written_files: list[str] = []

    for scorer_name, scorer_payload in scorer_payloads.items():
        scorer_slug = slugify_for_path(value=scorer_name)
        out_dir = target_root / scenario_slug / dataset_slug / seed_group_slug / scorer_slug
        out_dir.mkdir(parents=True, exist_ok=True)

        out_path = out_dir / f"case_{case_index:05d}_scenario_{scenario_index:05d}.json"
        report_payload = {
            "owasp_id": owasp_id,
            "owasp_name": owasp_name,
            "dataset": dataset_name,
            "seed_group": seed_group_name,
            "objective": objective,
            "scenario_index": scenario_index,
            "case_index": case_index,
            "scorer_name": scorer_name,
            "scorer_payload": scorer_payload,
            "error": error,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        }
        out_path.write_text(json.dumps(report_payload, indent=2), encoding="utf-8")
        written_files.append(str(out_path))

    return written_files


def append_production_log(*, event: str, data: dict[str, object]) -> None:
    """Append one structured JSON log line to the production log file."""
    payload = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "event": event,
        **data,
    }
    PRODUCTION_RUN_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with PRODUCTION_RUN_LOG_PATH.open("a", encoding="utf-8") as file:
        file.write(json.dumps(payload, ensure_ascii=False) + "\n")
    debug_log(message=f"Appended production log event='{event}'")


def initial_resume_state() -> dict[str, Any]:
    """Create default checkpoint state for resumable execution."""
    return {
        "next_scenario_index": 0,
        "completed": False,
        "totals": {"executed": 0, "passed": 0, "failed": 0},
        "results_summary": [],
        "scorer_comparisons": [],
        "scorer_outputs_json_rows": [],
        "run_config": {
            "selected_converters": [],
            "selected_datasets": [],
            "selected_scorers": [],
            "run_all_available_datasets": False,
            "max_datasets_per_scenario": 0,
        },
    }


def load_resume_state() -> dict[str, Any]:
    """Load checkpoint state from disk, or return initial defaults."""
    state: dict[str, Any] = initial_resume_state()
    if not RESUME_INCOMPLETE_RUN or not PRODUCTION_RUN_CHECKPOINT_PATH.exists():
        debug_log(message="Resume disabled or checkpoint missing; starting fresh state")
        return state

    try:
        loaded = json.loads(PRODUCTION_RUN_CHECKPOINT_PATH.read_text(encoding="utf-8"))
    except Exception:
        debug_log(message="Failed to parse checkpoint; starting with initial state")
        return state

    if not isinstance(loaded, dict):
        debug_log(message="Checkpoint format invalid; starting with initial state")
        return state

    next_index = loaded.get("next_scenario_index", 0)
    if isinstance(next_index, int):
        state["next_scenario_index"] = next_index
    elif isinstance(next_index, str) and next_index.isdigit():
        state["next_scenario_index"] = int(next_index)

    state["completed"] = bool(loaded.get("completed", False))

    loaded_totals = loaded.get("totals")
    if isinstance(loaded_totals, dict):
        state["totals"] = {
            "executed": int(loaded_totals.get("executed", 0)) if str(loaded_totals.get("executed", 0)).isdigit() else 0,
            "passed": int(loaded_totals.get("passed", 0)) if str(loaded_totals.get("passed", 0)).isdigit() else 0,
            "failed": int(loaded_totals.get("failed", 0)) if str(loaded_totals.get("failed", 0)).isdigit() else 0,
        }

    for key in ["results_summary", "scorer_comparisons", "scorer_outputs_json_rows"]:
        value = loaded.get(key)
        if isinstance(value, list):
            state[key] = value

    loaded_run_config = loaded.get("run_config")
    if isinstance(loaded_run_config, dict):
        state["run_config"] = {
            "selected_converters": list(loaded_run_config.get("selected_converters", [])),
            "selected_datasets": list(loaded_run_config.get("selected_datasets", [])),
            "selected_scorers": list(loaded_run_config.get("selected_scorers", [])),
            "run_all_available_datasets": bool(loaded_run_config.get("run_all_available_datasets", False)),
            "max_datasets_per_scenario": int(loaded_run_config.get("max_datasets_per_scenario", 0)),
        }

    debug_log(message=f"Loaded resume state at next_scenario_index={state['next_scenario_index']}")
    return state


def save_resume_state(*, state: dict[str, Any]) -> None:
    """Persist checkpoint state to disk for resume support."""
    PRODUCTION_RUN_CHECKPOINT_PATH.parent.mkdir(parents=True, exist_ok=True)
    PRODUCTION_RUN_CHECKPOINT_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")
    debug_log(message=f"Saved resume state at next_scenario_index={state.get('next_scenario_index')}")


def get_seed_tracking_info(*, memory: Any, dataset_name: str | None) -> dict[str, object]:
    """Extract seed metadata for production logging."""
    if not dataset_name:
        return {
            "dataset": "none",
            "seed_group_id": None,
            "seed_index": None,
            "seed_preview": None,
            "seed_group_size": 0,
        }

    try:
        seeds = list(memory.get_seeds(dataset_name=dataset_name))
    except Exception:
        seeds = []

    if not seeds:
        return {
            "dataset": dataset_name,
            "seed_group_id": None,
            "seed_index": None,
            "seed_preview": None,
            "seed_group_size": 0,
        }

    first_seed = seeds[0]
    group_id = getattr(first_seed, "prompt_group_id", None)
    seed_value = re.sub(r"\s+", " ", str(first_seed.value))[:180]
    return {
        "dataset": dataset_name,
        "seed_group_id": str(group_id) if group_id else None,
        "seed_index": 0,
        "seed_preview": seed_value,
        "seed_group_size": len(seeds),
    }
