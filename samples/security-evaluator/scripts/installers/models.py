"""Data models for installer choices."""

from __future__ import annotations

import platform
from dataclasses import dataclass


@dataclass
class WizardSelection:
    """User-selected setup options."""

    install_python_packages: bool = True
    install_sqlite: bool = True
    create_env_file: bool = True
    create_pyrit_config_file: bool = True
    installation_type: str = "local"
    install_ollama_local: bool = False
    install_jupyter_local: bool = False
    setup_pyrit_gui_local: bool = False
    pull_ollama_models: bool = False
    install_docker_stack: bool = False
    start_docker_compose: bool = False
    configure_api_service: bool = False
    install_api_service: bool = False
    validate_configuration: bool = True
    run_sanity_checks: bool = False
    platform_name: str = platform.system().lower()
