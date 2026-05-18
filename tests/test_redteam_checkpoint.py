import importlib.util
import os
import sys
import types
from pathlib import Path

import pytest


def _load_reporting_ops_with_stub(tmp_path: Path):
    app_root = Path(__file__).resolve().parents[1] / "samples" / "security-evaluator" / "scripts" / "app"
    logs_root = tmp_path / "logs"
    reports_root = tmp_path / "reports"
    checkpoint_path = logs_root / "pyrit_owasp_redteam_production_checkpoint.json"
    log_path = logs_root / "pyrit_owasp_redteam_production.log"

    logs_root.mkdir(parents=True, exist_ok=True)
    reports_root.mkdir(parents=True, exist_ok=True)

    env_mod = types.ModuleType("redteam_runner.env_config")
    env_mod.ARTIFACTS_ROOT_PATH = reports_root
    env_mod.BATCH_SCORER_CHECK_JSON_PATH = reports_root / "batch_scorer_check.json"
    env_mod.PRODUCTION_RUN_CHECKPOINT_PATH = checkpoint_path
    env_mod.PRODUCTION_RUN_LOG_PATH = log_path
    env_mod.REPORTS_ROOT_PATH = reports_root / "cases"
    env_mod.RESUME_INCOMPLETE_RUN = True
    env_mod.SCORER_COMPARISON_CSV_PATH = reports_root / "scorer_comparison.csv"
    env_mod.SCORER_OUTPUTS_JSON_PATH = reports_root / "scorer_outputs.json"
    env_mod.RUN_REPORT_JSON_PATH = reports_root / "run_report.json"

    def debug_log(*, message: str) -> None:
        return None

    env_mod.debug_log = debug_log

    package_mod = types.ModuleType("redteam_runner")
    sys.modules["redteam_runner"] = package_mod
    sys.modules["redteam_runner.env_config"] = env_mod

    reporting_ops_path = app_root / "redteam_runner" / "reporting_ops.py"
    spec = importlib.util.spec_from_file_location("redteam_runner.reporting_ops", reporting_ops_path)
    reporting_ops = importlib.util.module_from_spec(spec)
    reporting_ops.__package__ = "redteam_runner"
    sys.modules["redteam_runner.reporting_ops"] = reporting_ops
    spec.loader.exec_module(reporting_ops)
    return reporting_ops


def test_initial_resume_state_defaults(tmp_path: Path):
    reporting_ops = _load_reporting_ops_with_stub(tmp_path)

    state = reporting_ops.initial_resume_state()

    assert state["next_scenario_index"] == 0
    assert state["completed"] is False
    assert state["totals"] == {"executed": 0, "passed": 0, "failed": 0}
    assert state["results_summary"] == []
    assert state["scorer_comparisons"] == []
    assert state["scorer_outputs_json_rows"] == []


def test_save_and_load_resume_state(tmp_path: Path):
    reporting_ops = _load_reporting_ops_with_stub(tmp_path)

    checkpoint_path = reporting_ops.PRODUCTION_RUN_CHECKPOINT_PATH
    state = {
        "next_scenario_index": 2,
        "completed": False,
        "totals": {"executed": 2, "passed": 1, "failed": 1},
        "results_summary": [{"owasp_id": "LLM01"}],
        "scorer_comparisons": [{"owasp_id": "LLM01", "weighted_confidence": 0.9}],
        "scorer_outputs_json_rows": [{"owasp_id": "LLM01", "scores": {}}],
    }

    reporting_ops.save_resume_state(state=state)
    assert checkpoint_path.exists()

    loaded = reporting_ops.load_resume_state()
    assert loaded["next_scenario_index"] == 2
    assert loaded["completed"] is False
    assert loaded["totals"] == {"executed": 2, "passed": 1, "failed": 1}
    assert loaded["results_summary"] == state["results_summary"]
    assert loaded["scorer_comparisons"] == state["scorer_comparisons"]
    assert loaded["scorer_outputs_json_rows"] == state["scorer_outputs_json_rows"]


def test_load_resume_state_preserves_run_config(tmp_path: Path):
    reporting_ops = _load_reporting_ops_with_stub(tmp_path)

    state = reporting_ops.initial_resume_state()
    state["next_scenario_index"] = 1
    state["run_config"] = {
        "selected_converters": ["base64", "leetspeak"],
        "selected_datasets": ["harmbench"],
        "selected_scorers": ["self_ask_true_false"],
        "run_all_available_datasets": False,
        "max_datasets_per_scenario": 2,
    }

    reporting_ops.save_resume_state(state=state)
    loaded = reporting_ops.load_resume_state()

    assert loaded["run_config"] == state["run_config"]


def test_load_resume_state_invalid_json_returns_initial_state(tmp_path: Path):
    reporting_ops = _load_reporting_ops_with_stub(tmp_path)

    checkpoint_path = reporting_ops.PRODUCTION_RUN_CHECKPOINT_PATH
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    checkpoint_path.write_text("not valid json", encoding="utf-8")

    loaded = reporting_ops.load_resume_state()
    assert loaded["next_scenario_index"] == 0
    assert loaded["completed"] is False
    assert loaded["totals"] == {"executed": 0, "passed": 0, "failed": 0}
    assert loaded["results_summary"] == []
    assert loaded["scorer_comparisons"] == []
    assert loaded["scorer_outputs_json_rows"] == []
