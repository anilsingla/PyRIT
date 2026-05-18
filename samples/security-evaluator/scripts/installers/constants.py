"""Constants and paths used by the security-evaluator installer."""

from __future__ import annotations

from pathlib import Path
from typing import Any


SAMPLE_DIR = Path(__file__).resolve().parents[2]
REPO_ROOT = SAMPLE_DIR.parents[1]
DEFAULT_ENV_FILE = SAMPLE_DIR / ".env.local"
DEFAULT_PYRIT_CONFIG_FILE = SAMPLE_DIR / ".pyrit_config"
API_REQUIREMENTS_FILE = SAMPLE_DIR / "api" / "requirements.txt"
WINDOWS_SERVICE_INSTALL_SCRIPT = SAMPLE_DIR / "scripts" / "installers" / "app_service" / "windows" / "install_service.ps1"
LINUX_SERVICE_TEMPLATE = SAMPLE_DIR / "scripts" / "installers" / "app_service" / "linux" / "pyrit-redteam-api.service"
MAC_SERVICE_TEMPLATE = SAMPLE_DIR / "scripts" / "installers" / "app_service" / "macos" / "com.pyrit.redteam.api.plist"
DOCKER_COMPOSE_FILE = REPO_ROOT / "docker" / "docker-compose.yaml"

COMMON_PYTHON_PACKAGES = ["pyrit", "sqlalchemy", "pyyaml"]

REQUIRED_ENV_DEFAULTS: dict[str, str] = {
    "DEBUG": "false",
    "ALLOW_RUNTIME_PIP_INSTALL": "false",
    "OLLAMA_ENDPOINT": "http://localhost:11434/v1",
    "ALLOW_REMOTE_OLLAMA_ENDPOINT": "false",
    "OLLAMA_TARGET_MODEL": "llama3.2",
    "OLLAMA_ATTACKER_MODEL": "mistral",
    "OLLAMA_SCORER_MODEL": "phi3",
    "OLLAMA_CONVERTER_MODEL": "phi3",
    "OLLAMA_TF_SCORER_MODEL": "phi3",
    "OLLAMA_SCALE_SCORER_MODEL": "phi3",
    "OLLAMA_REFUSAL_SCORER_MODEL": "phi3",
    "OLLAMA_MODEL": "llama2",
    "ARTIFACTS_ROOT_PATH": "reports",
    "LOGS_ROOT_PATH": "logs",
    "PYRIT_SQLITE_DB_PATH": "reports/pyrit_ollama_demo.db",
    "SCORER_COMPARISON_CSV_PATH": "reports/scorer_comparison.csv",
    "SCORER_OUTPUTS_JSON_PATH": "reports/scorer_outputs.json",
    "BATCH_SCORER_CHECK_JSON_PATH": "reports/batch_scorer_check.json",
    "RUN_REPORT_JSON_PATH": "reports/run_report.json",
    "REPORTS_ROOT_PATH": "reports/cases",
    "PYRIT_MAX_TURNS": "4",
    "PRINT_DATASET_SEEDS": "false",
    "DATASET_PREVIEW_ROWS": "3",
    "EXPORT_DETAILED_SCORES_JSON": "true",
    "RUN_ALL_AVAILABLE_DATASETS": "false",
    "MAX_DATASETS_PER_SCENARIO": "0",
    "OLLAMA_MAX_RETRIES_PER_SCENARIO": "3",
    "OLLAMA_RETRY_WAIT_SECONDS": "5",
    "RESUME_INCOMPLETE_RUN": "true",
}

REQUIRED_PYRIT_DEFAULTS: dict[str, Any] = {
    "memory_db_type": "sqlite",
    "operator": "local_redteam",
    "operation": "owasp_ollama_example",
    "initializers": [],
    "env_files": ["./.env.local"],
    "silent": False,
}
