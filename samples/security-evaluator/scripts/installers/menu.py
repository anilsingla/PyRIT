"""Interactive menu and selection collection for installer."""

from __future__ import annotations

from .models import WizardSelection
from .prompts import prompt_bool, prompt_choice


def collect_selection() -> WizardSelection:
    """Collect user choices for installation workflow."""
    print("RedTeam Ollama setup wizard")
    print("1) Full setup (install packages, create configs, validate)")
    print("2) Install only")
    print("3) Create/update config files only")
    print("4) Validate existing config")
    print("5) Install packages + config, then validate")
    print("6) Configure/install API service wrappers")

    choice = prompt_choice(message="Choose an action", choices=["1", "2", "3", "4", "5", "6"], default="1")
    platform_choice = prompt_choice(message="Target platform", choices=["windows", "linux", "macos"], default="linux")
    installation_type = prompt_choice(message="Installation type", choices=["local", "docker"], default="local")

    install_docker_stack = False
    start_docker_compose = False
    install_ollama_local = False
    install_jupyter_local = False
    setup_pyrit_gui_local = False
    pull_ollama_models = False

    if installation_type == "docker":
        install_docker_stack = prompt_bool(
            message="Install Docker and Docker Compose for this platform",
            default=True,
        )
        start_docker_compose = prompt_bool(
            message="Start docker compose stack now (docker compose up -d)",
            default=False,
        )
    else:
        install_ollama_local = prompt_bool(message="Install Ollama locally", default=True)
        pull_ollama_models = prompt_bool(
            message="Pull default Ollama models (llama3.2, mistral, phi3)",
            default=False,
        )
        install_jupyter_local = prompt_bool(message="Install Jupyter (lab/notebook)", default=True)
        setup_pyrit_gui_local = prompt_bool(
            message="Install dependencies for PyRIT GUI integration",
            default=True,
        )

    configure_service = False
    if installation_type == "local":
        configure_service = choice == "6" or prompt_bool(
            message="Configure API service wrappers during setup",
            default=False,
        )

    install_service = False
    if configure_service:
        install_service = prompt_bool(
            message="Install/start the API service now (requires admin/sudo on matching host)",
            default=False,
        )

    return WizardSelection(
        install_python_packages=choice in {"1", "2", "5"},
        install_sqlite=choice in {"1", "2", "5"},
        create_env_file=choice in {"1", "3", "5"},
        create_pyrit_config_file=choice in {"1", "3", "5"},
        installation_type=installation_type,
        install_ollama_local=install_ollama_local,
        install_jupyter_local=install_jupyter_local,
        setup_pyrit_gui_local=setup_pyrit_gui_local,
        pull_ollama_models=pull_ollama_models,
        install_docker_stack=install_docker_stack,
        start_docker_compose=start_docker_compose,
        configure_api_service=configure_service,
        install_api_service=install_service,
        validate_configuration=choice in {"1", "4", "5"},
        run_sanity_checks=prompt_bool(message="Run quick sanity checks after setup", default=False),
        platform_name=platform_choice,
    )
