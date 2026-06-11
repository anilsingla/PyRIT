"""Platform installation actions for local and docker flows."""

from __future__ import annotations

# Bootstrap: allow running as a standalone script (python platform_installers.py --install ...)
# as well as being imported as part of the 'installers' package.
import sys as _sys
from pathlib import Path as _Path

if __name__ == "__main__" and not __package__:
    # Add scripts/ to sys.path so 'installers' is a resolvable package.
    _helper_dir = _Path(__file__).resolve().parent.parent
    _sys.path.insert(0, str(_helper_dir))
    import installers.platform_installers as _mod

    _sys.exit(_mod._cli_main())

import argparse
import platform as _platform
import shutil
import sys

from .commands import detect_package_manager, run_command
from .constants import API_REQUIREMENTS_FILE, COMMON_PYTHON_PACKAGES, DOCKER_COMPOSE_FILE, SAMPLE_DIR


def install_python_packages(*, python_exe: str) -> None:
    """Install Python dependencies for API and sample tooling."""
    print("\nInstalling Python packages...")
    run_command([python_exe, "-m", "pip", "install", "--upgrade", "pip"], check=True)
    if API_REQUIREMENTS_FILE.exists():
        run_command([python_exe, "-m", "pip", "install", "-r", str(API_REQUIREMENTS_FILE)], check=True)
    run_command([python_exe, "-m", "pip", "install", *COMMON_PYTHON_PACKAGES], check=True)


def install_sqlite(*, platform_name: str) -> None:
    """Install SQLite for selected platform."""
    manager = detect_package_manager()
    if platform_name == "windows":
        if manager == "winget":
            run_command(["winget", "install", "--id", "SQLite.SQLite", "--exact", "--silent", "--accept-source-agreements", "--accept-package-agreements"], check=True)
            return
        if manager == "choco":
            run_command(["choco", "install", "sqlite", "-y"], check=True)
            return
        if manager == "scoop":
            run_command(["scoop", "install", "sqlite"], check=True)
            return
        raise RuntimeError("Could not auto-install SQLite on Windows.")

    if platform_name == "macos":
        if shutil.which("brew"):
            run_command(["brew", "install", "sqlite"], check=True)
            return
        raise RuntimeError("Homebrew not found for SQLite install on macOS.")

    if manager == "apt-get":
        run_command(["sudo", "apt-get", "update"], check=True)
        run_command(["sudo", "apt-get", "install", "-y", "sqlite3", "libsqlite3-dev"], check=True)
    elif manager == "dnf":
        run_command(["sudo", "dnf", "install", "-y", "sqlite", "sqlite-devel"], check=True)
    elif manager == "yum":
        run_command(["sudo", "yum", "install", "-y", "sqlite", "sqlite-devel"], check=True)
    elif manager == "pacman":
        run_command(["sudo", "pacman", "-Sy", "--noconfirm", "sqlite"], check=True)
    elif manager == "zypper":
        run_command(["sudo", "zypper", "--non-interactive", "install", "sqlite3", "sqlite3-devel"], check=True)
    else:
        raise RuntimeError("Could not auto-install SQLite on Linux.")


def install_docker_stack(*, platform_name: str) -> None:
    """Install Docker and Docker Compose for selected platform."""
    manager = detect_package_manager()
    if platform_name == "windows":
        if manager == "winget":
            run_command(["winget", "install", "--id", "Docker.DockerDesktop", "--exact", "--silent", "--accept-source-agreements", "--accept-package-agreements"], check=True)
            return
        if manager == "choco":
            run_command(["choco", "install", "docker-desktop", "-y"], check=True)
            return
        if manager == "scoop":
            run_command(["scoop", "install", "docker"], check=True)
            return
        raise RuntimeError("No supported package manager for Docker Desktop on Windows.")

    if platform_name == "macos":
        if shutil.which("brew"):
            run_command(["brew", "install", "--cask", "docker"], check=True)
            return
        raise RuntimeError("Homebrew not found for Docker Desktop install on macOS.")

    if manager == "apt-get":
        run_command(["sudo", "apt-get", "update"], check=True)
        run_command(["sudo", "apt-get", "install", "-y", "docker.io", "docker-compose-plugin"], check=True)
    elif manager == "dnf":
        run_command(["sudo", "dnf", "install", "-y", "docker", "docker-compose-plugin"], check=True)
    elif manager == "yum":
        run_command(["sudo", "yum", "install", "-y", "docker", "docker-compose-plugin"], check=True)
    elif manager == "pacman":
        run_command(["sudo", "pacman", "-Sy", "--noconfirm", "docker", "docker-compose"], check=True)
    elif manager == "zypper":
        run_command(["sudo", "zypper", "--non-interactive", "install", "docker", "docker-compose"], check=True)
    else:
        raise RuntimeError("No supported package manager for Docker on Linux.")


def start_docker_compose_stack() -> None:
    """Run docker compose stack from repo docker directory."""
    if not DOCKER_COMPOSE_FILE.exists():
        raise RuntimeError(f"docker-compose file not found: {DOCKER_COMPOSE_FILE}")
    if shutil.which("docker") is None:
        raise RuntimeError("Docker command not found after installation.")

    run_command(["docker", "compose", "up", "-d"], cwd=DOCKER_COMPOSE_FILE.parent, check=True)


def install_ollama(*, platform_name: str) -> None:
    """Install Ollama based on selected platform."""
    manager = detect_package_manager()
    if platform_name == "windows":
        if manager == "winget":
            run_command(["winget", "install", "--id", "Ollama.Ollama", "--exact", "--silent", "--accept-source-agreements", "--accept-package-agreements"], check=True)
            return
        if manager == "choco":
            run_command(["choco", "install", "ollama", "-y"], check=True)
            return
        if manager == "scoop":
            run_command(["scoop", "install", "ollama"], check=True)
            return
        raise RuntimeError("No supported package manager for Ollama on Windows.")

    if platform_name == "macos":
        if shutil.which("brew"):
            run_command(["brew", "install", "ollama"], check=True)
            return
        raise RuntimeError("Homebrew not found for Ollama install on macOS.")

    run_command(["bash", "-lc", "curl -fsSL https://ollama.com/install.sh | sh"], check=True)


def install_jupyter_and_gui(*, python_exe: str) -> None:
    """Install Jupyter stack and Streamlit dependency used by GUI."""
    run_command([python_exe, "-m", "pip", "install", "jupyterlab", "notebook", "streamlit"], check=True)


def pull_default_ollama_models() -> None:
    """Pull default local models used by sample workflows."""
    for model_name in ["llama3.2", "mistral", "phi3"]:
        run_command(["ollama", "pull", model_name], check=True)


def print_local_integration_steps(*, python_exe: str) -> None:
    """Print next-step command hints for local integration."""
    print("\nLocal integration steps")
    print("1) Start Ollama service:")
    print("   - Windows/macOS: launch Ollama app")
    print("   - Linux: ollama serve")
    print("2) Verify Ollama endpoint: curl http://localhost:11434/api/tags")
    print("3) Launch Jupyter Lab:")
    print(f"   {python_exe} -m jupyter lab")
    print("4) Run the security-evaluator main workflow:")
    print(f"   cd {SAMPLE_DIR / 'scripts'}")
    print(f"   {python_exe} app/main.py --dry-run --local-datasets-only")
    print("5) Ensure scripts read SQLite path from .env.local (PYRIT_SQLITE_DB_PATH).")


def _build_cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run a single platform installer action directly.\n\n"
            "Examples:\n"
            "  python -m scripts.installers.platform_installers --install sqlite --platform linux\n"
            "  python platform_installers.py --install ollama --platform windows\n"
            "  python platform_installers.py --install docker --platform macos\n"
            "  python platform_installers.py --install python-packages"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--install",
        required=True,
        choices=["sqlite", "ollama", "docker", "jupyter", "python-packages", "pull-models"],
        help="Which component to install.",
    )
    parser.add_argument(
        "--platform",
        choices=["windows", "linux", "macos"],
        default=None,
        help="Target platform (default: auto-detect from current OS).",
    )
    parser.add_argument(
        "--start-compose",
        action="store_true",
        help="Start docker compose stack after Docker install.",
    )
    return parser


def _auto_platform() -> str:
    name = _platform.system().lower()
    if name.startswith("win"):
        return "windows"
    if name == "darwin":
        return "macos"
    return "linux"


def _cli_main() -> int:
    parser = _build_cli_parser()
    args = parser.parse_args()

    platform_name: str = args.platform or _auto_platform()
    python_exe = sys.executable
    action: str = args.install

    try:
        if action == "sqlite":
            install_sqlite(platform_name=platform_name)
        elif action == "ollama":
            install_ollama(platform_name=platform_name)
        elif action == "docker":
            install_docker_stack(platform_name=platform_name)
            if args.start_compose:
                start_docker_compose_stack()
        elif action == "jupyter":
            install_jupyter_and_gui(python_exe=python_exe)
        elif action == "python-packages":
            install_python_packages(python_exe=python_exe)
        elif action == "pull-models":
            pull_default_ollama_models()
    except RuntimeError as exc:
        print(f"[ERROR] {exc}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(_cli_main())

