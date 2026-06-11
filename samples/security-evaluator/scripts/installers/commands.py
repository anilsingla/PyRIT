"""Command execution and environment detection helpers."""

from __future__ import annotations

import platform
import shutil
import subprocess
from pathlib import Path


def run_command(command: list[str], *, cwd: Path | None = None, check: bool = False) -> int:
    """Run command and optionally fail when exit code is non-zero."""
    result = subprocess.run(command, cwd=str(cwd) if cwd else None)
    if check and result.returncode != 0:
        raise RuntimeError(f"Command failed with exit code {result.returncode}: {' '.join(command)}")
    return result.returncode


def detect_package_manager() -> str | None:
    """Detect available package manager command name."""
    candidates = ["winget", "choco", "scoop", "brew", "apt-get", "dnf", "yum", "pacman", "zypper"]
    for candidate in candidates:
        if shutil.which(candidate):
            return candidate
    return None


def local_platform_name() -> str:
    """Return normalized local platform label."""
    system_name = platform.system().lower()
    if system_name.startswith("win"):
        return "windows"
    if system_name == "darwin":
        return "macos"
    return "linux"
