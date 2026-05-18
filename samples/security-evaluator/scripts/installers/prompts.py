"""Prompt helper functions for interactive installer flows."""

from __future__ import annotations

from .constants import SAMPLE_DIR


def prompt(*, message: str, default: str | None = None) -> str:
    """Prompt the user and return entered text or default."""
    suffix = f" [{default}]" if default is not None else ""
    value = input(f"{message}{suffix}: ").strip()
    if value:
        return value
    return default or ""


def prompt_bool(*, message: str, default: bool) -> bool:
    """Prompt for yes/no value."""
    default_label = "Y/n" if default else "y/N"
    value = input(f"{message} ({default_label}): ").strip().lower()
    if not value:
        return default
    return value in {"y", "yes", "true", "1"}


def prompt_choice(*, message: str, choices: list[str], default: str) -> str:
    """Prompt for one value from fixed choices."""
    labels = "/".join(choices)
    while True:
        value = input(f"{message} ({labels}) [{default}]: ").strip().lower()
        if not value:
            return default
        if value in choices:
            return value
        print(f"Please choose one of: {', '.join(choices)}")


def prompt_int(*, message: str, default: int, min_value: int, max_value: int) -> int:
    """Prompt for an integer constrained by min and max."""
    while True:
        value = prompt(message=message, default=str(default))
        try:
            parsed = int(value)
        except ValueError:
            print("Please enter a valid integer.")
            continue
        if min_value <= parsed <= max_value:
            return parsed
        print(f"Please enter a value between {min_value} and {max_value}.")


def prompt_service_paths(*, platform_name: str, local_python_exe: str) -> tuple[str, str]:
    """Prompt for target-service working dir and Python executable path."""
    default_paths: dict[str, tuple[str, str]] = {
        "windows": (str(SAMPLE_DIR), local_python_exe),
        "linux": ("/opt/PyRIT/samples/security-evaluator", "/usr/bin/python3"),
        "macos": ("/opt/PyRIT/samples/security-evaluator", "/usr/bin/python3"),
    }
    default_working_dir, default_python_exe = default_paths.get(
        platform_name,
        (str(SAMPLE_DIR), local_python_exe),
    )
    working_dir = prompt(message="API service working directory", default=default_working_dir)
    python_exe = prompt(message="API service python executable", default=default_python_exe)
    return working_dir, python_exe


def prompt_multiline_defaults(*, defaults: dict[str, str]) -> dict[str, str]:
    """Prompt for key-value config values with defaults."""
    values: dict[str, str] = {}
    print("\nEnter configuration values. Press Enter to accept the default shown in brackets.")
    print("Type 'skip' for any optional value you do not want to set.")
    for key, default in defaults.items():
        value = prompt(message=key, default=default)
        if value.lower() == "skip":
            continue
        values[key] = value
    return values
