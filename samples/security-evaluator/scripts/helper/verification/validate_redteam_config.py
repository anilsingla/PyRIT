#!/usr/bin/env python3
"""Validate the security-evaluator config files before running the suite."""

from __future__ import annotations

import argparse
import json
import shutil
import shlex
import sys
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[3]
DEFAULT_ENV_FILE = ROOT_DIR / ".env.local"
DEFAULT_PYRIT_CONFIG_FILE = ROOT_DIR / ".pyrit_config"
EXAMPLE_ENV_FILE = ROOT_DIR / "config" / ".env.local.example"
EXAMPLE_PYRIT_CONFIG_FILE = ROOT_DIR / "config" / ".pyrit_config.example"

REQUIRED_ENV_VARS = (
    "OLLAMA_ENDPOINT",
    "OLLAMA_TARGET_MODEL",
    "OLLAMA_ATTACKER_MODEL",
    "OLLAMA_CONVERTER_MODEL",
    "OLLAMA_TF_SCORER_MODEL",
    "OLLAMA_SCALE_SCORER_MODEL",
    "OLLAMA_REFUSAL_SCORER_MODEL",
    "PYRIT_SQLITE_DB_PATH",
)

RECOMMENDED_PYRIT_MODELS = {
    "DEFAULT_OPENAI_FRONTEND_MODEL": "gpt-4o",
    "OPENAI_CHAT_MODEL": "gpt-4o",
    "OPENAI_EMBEDDING_MODEL": "text-embedding-3-small",
    "OLLAMA_MODEL": "llama2",
}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate security-evaluator config files and show the active model catalog.",
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        default=DEFAULT_ENV_FILE,
        help="Path to the active .env.local file.",
    )
    parser.add_argument(
        "--pyrit-config",
        type=Path,
        default=DEFAULT_PYRIT_CONFIG_FILE,
        help="Path to the active .pyrit_config file.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print a machine-readable JSON report.",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Create missing root config files from the example templates.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing root config files when used with --fix.",
    )
    return parser


def _load_env_values(*, env_file: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        if line.startswith("export "):
            line = line[len("export ") :].strip()

        if "=" not in line:
            continue

        key, raw_value = line.split("=", 1)
        key = key.strip()
        value = raw_value.strip()
        if not key:
            continue

        if value and value[0] in {'"', "'"}:
            try:
                value = shlex.split(value, posix=True)[0]
            except Exception:
                value = value.strip('"\'')

        values[key] = value

    return values


def _load_pyrit_config(*, config_file: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore[import-not-found]
    except Exception as exc:
        raise RuntimeError(
            "PyYAML is required to parse .pyrit_config. Install with: pip install pyyaml"
        ) from exc

    with config_file.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    if not isinstance(payload, dict):
        raise ValueError(".pyrit_config must contain a YAML mapping at the top level.")
    return payload


def _validate_env(*, env_file: Path) -> list[str]:
    errors: list[str] = []
    if not env_file.exists():
        return [f"Missing env file: {env_file}"]

    values = _load_env_values(env_file=env_file)
    for key in REQUIRED_ENV_VARS:
        if not values.get(key):
            errors.append(f"Missing required variable in {env_file.name}: {key}")

    if values.get("OLLAMA_ENDPOINT", "").strip() and not values["OLLAMA_ENDPOINT"].endswith("/v1"):
        errors.append("OLLAMA_ENDPOINT should end with /v1 for the OpenAI-compatible Ollama API.")

    return errors


def _validate_pyrit_config(*, config_file: Path) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    if not config_file.exists():
        return [f"Missing PyRIT config file: {config_file}"], {}

    payload = _load_pyrit_config(config_file=config_file)

    if payload.get("memory_db_type") != "sqlite":
        errors.append("memory_db_type should be set to 'sqlite' for the local security-evaluator workflow.")

    env_files = payload.get("env_files")
    if not isinstance(env_files, list) or not env_files:
        errors.append("env_files should list the env file path(s) used by PyRIT.")
    else:
        env_paths = {str(item).strip() for item in env_files}
        if "./.env.local" not in env_paths and "./config/.env.local" not in env_paths:
            errors.append("env_files should include ./.env.local or ./config/.env.local.")

    return errors, payload


def _build_report(*, env_file: Path, pyrit_config_file: Path) -> dict[str, Any]:
    env_errors = _validate_env(env_file=env_file)
    pyrit_errors, pyrit_payload = _validate_pyrit_config(config_file=pyrit_config_file)

    env_values = _load_env_values(env_file=env_file) if env_file.exists() else {}
    model_catalog = {
        "runner": {
            "OLLAMA_TARGET_MODEL": env_values.get("OLLAMA_TARGET_MODEL", "llama3.2"),
            "OLLAMA_ATTACKER_MODEL": env_values.get("OLLAMA_ATTACKER_MODEL", "mistral"),
            "OLLAMA_CONVERTER_MODEL": env_values.get("OLLAMA_CONVERTER_MODEL", "phi3"),
            "OLLAMA_TF_SCORER_MODEL": env_values.get("OLLAMA_TF_SCORER_MODEL", "phi3"),
            "OLLAMA_SCALE_SCORER_MODEL": env_values.get("OLLAMA_SCALE_SCORER_MODEL", "phi3"),
            "OLLAMA_REFUSAL_SCORER_MODEL": env_values.get("OLLAMA_REFUSAL_SCORER_MODEL", "phi3"),
        },
        "pyrit_defaults": {
            key: env_values.get(key, default) for key, default in RECOMMENDED_PYRIT_MODELS.items()
        },
    }

    return {
        "valid": not env_errors and not pyrit_errors,
        "env_file": str(env_file.resolve()),
        "pyrit_config_file": str(pyrit_config_file.resolve()),
        "errors": env_errors + pyrit_errors,
        "warnings": [
            "PyRIT config is optional for the runner itself, but useful for GUI and scan workflows.",
        ],
        "model_catalog": model_catalog,
        "pyrit_config": pyrit_payload,
    }


def _copy_if_needed(*, source: Path, destination: Path, overwrite: bool) -> bool:
    if not source.exists():
        raise FileNotFoundError(f"Missing example template: {source}")
    if destination.exists() and not overwrite:
        return False
    shutil.copyfile(source, destination)
    return True


def _print_report(*, report: dict[str, Any]) -> None:
    print("=== security-evaluator config validation ===")
    print(f"Env file       : {report['env_file']}")
    print(f"PyRIT config   : {report['pyrit_config_file']}")

    print("\nRunner models:")
    for key, value in report["model_catalog"]["runner"].items():
        print(f"  - {key}: {value}")

    print("\nPyRIT defaults:")
    for key, value in report["model_catalog"]["pyrit_defaults"].items():
        print(f"  - {key}: {value}")

    if report["warnings"]:
        print("\nWarnings:")
        for warning in report["warnings"]:
            print(f"  - {warning}")

    if report["errors"]:
        print("\nErrors:")
        for error in report["errors"]:
            print(f"  - {error}")


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    if bool(args.fix):
        copied_env = _copy_if_needed(
            source=EXAMPLE_ENV_FILE,
            destination=DEFAULT_ENV_FILE,
            overwrite=bool(args.overwrite),
        )
        copied_pyrit = _copy_if_needed(
            source=EXAMPLE_PYRIT_CONFIG_FILE,
            destination=DEFAULT_PYRIT_CONFIG_FILE,
            overwrite=bool(args.overwrite),
        )
        print(
            "Created config files from templates: "
            f".env.local={'yes' if copied_env else 'already existed'}, "
            f".pyrit_config={'yes' if copied_pyrit else 'already existed'}"
        )
        if not bool(args.json):
            print("Run again without --fix to validate the resulting config files.")
        if not copied_env and not copied_pyrit and not bool(args.overwrite):
            return 0

    report = _build_report(env_file=args.env_file, pyrit_config_file=args.pyrit_config)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        _print_report(report=report)

    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
