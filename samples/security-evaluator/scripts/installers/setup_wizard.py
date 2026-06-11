"""Main installation workflow orchestration."""

from __future__ import annotations

from .commands import run_command
from .configuration import (
    upsert_env_values,
    validate_configuration,
    write_configs_interactively,
)
from .constants import DEFAULT_ENV_FILE, SAMPLE_DIR
from .menu import collect_selection
from .platform_installers import (
    install_docker_stack,
    install_jupyter_and_gui,
    install_ollama,
    install_python_packages,
    install_sqlite,
    print_local_integration_steps,
    pull_default_ollama_models,
    start_docker_compose_stack,
)
from .services import setup_api_service


def run_wizard(*, python_exe: str) -> int:
    """Run interactive setup and return process exit code."""
    selection = collect_selection()

    if selection.install_python_packages:
        install_python_packages(python_exe=python_exe)

    if selection.install_sqlite:
        install_sqlite(platform_name=selection.platform_name)

    local_integration_requested = False
    if selection.installation_type == "docker":
        if selection.install_docker_stack:
            install_docker_stack(platform_name=selection.platform_name)
        if selection.start_docker_compose:
            start_docker_compose_stack()
    else:
        local_integration_requested = any(
            [
                selection.install_ollama_local,
                selection.pull_ollama_models,
                selection.install_jupyter_local,
                selection.setup_pyrit_gui_local,
            ]
        )
        if selection.install_ollama_local:
            install_ollama(platform_name=selection.platform_name)
        if selection.install_jupyter_local or selection.setup_pyrit_gui_local:
            install_jupyter_and_gui(python_exe=python_exe)
        if selection.pull_ollama_models:
            pull_default_ollama_models()

        if local_integration_requested:
            upsert_env_values(
                path=DEFAULT_ENV_FILE,
                updates={
                    "OLLAMA_ENDPOINT": "http://localhost:11434/v1",
                    "ALLOW_REMOTE_OLLAMA_ENDPOINT": "false",
                    "PYRIT_SQLITE_DB_PATH": "reports/pyrit_ollama_demo.db",
                },
            )

    wrote_configs = False
    if selection.create_env_file or selection.create_pyrit_config_file:
        write_configs_interactively()
        wrote_configs = True

    if selection.configure_api_service:
        setup_api_service(
            platform_name=selection.platform_name,
            install_service=selection.install_api_service,
            python_exe=python_exe,
        )

    if selection.validate_configuration:
        status = validate_configuration(python_exe=python_exe)
        if status != 0:
            print("Configuration validation failed.")
            return status
        print("Configuration validation passed.")

    if selection.run_sanity_checks:
        sanity_script = SAMPLE_DIR / "scripts" / "helper" / "verification" / "smoke_test_runner.py"
        sanity_exit = run_command([python_exe, str(sanity_script)], cwd=SAMPLE_DIR)
        if sanity_exit != 0:
            print("Sanity checks failed.")
            return sanity_exit

    print("\nSetup complete.")
    if wrote_configs:
        print("Config files were written/updated in samples/security-evaluator.")
    if selection.installation_type == "local" and local_integration_requested:
        print_local_integration_steps(python_exe=python_exe)
    if selection.installation_type == "docker":
        print("Docker mode selected. Use docker compose logs/services to verify runtime health.")

    return 0
