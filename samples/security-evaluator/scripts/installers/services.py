"""Service wrapper generation and install helpers."""

from __future__ import annotations

import re
from pathlib import Path

from .commands import local_platform_name, run_command
from .constants import (
    LINUX_SERVICE_TEMPLATE,
    MAC_SERVICE_TEMPLATE,
    SAMPLE_DIR,
    WINDOWS_SERVICE_INSTALL_SCRIPT,
)
from .configuration import write_text_file
from .prompts import prompt, prompt_int, prompt_service_paths


def generate_linux_service_file(
    *,
    service_python_exe: str,
    service_working_dir: str,
    host: str,
    port: int,
) -> Path:
    """Generate Linux systemd service file using selected values."""
    content = LINUX_SERVICE_TEMPLATE.read_text(encoding="utf-8")
    content = re.sub(r"^WorkingDirectory=.*$", f"WorkingDirectory={service_working_dir}", content, flags=re.MULTILINE)
    content = re.sub(r"^ExecStart=.*$", f"ExecStart={service_python_exe} -m api.run_api", content, flags=re.MULTILINE)
    content = re.sub(r"^Environment=API_HOST=.*$", f"Environment=API_HOST={host}", content, flags=re.MULTILINE)
    content = re.sub(r"^Environment=API_PORT=.*$", f"Environment=API_PORT={port}", content, flags=re.MULTILINE)

    output_path = SAMPLE_DIR / "scripts" / "installers" / "app_service" / "linux" / "pyrit-redteam-api.generated.service"
    write_text_file(path=output_path, content=content)
    return output_path


def generate_macos_plist(
    *,
    service_python_exe: str,
    service_working_dir: str,
    host: str,
    port: int,
) -> Path:
    """Generate macOS launchd plist using selected values."""
    content = MAC_SERVICE_TEMPLATE.read_text(encoding="utf-8")
    content = content.replace("<string>/usr/bin/python3</string>", f"<string>{service_python_exe}</string>")
    content = content.replace("<string>/opt/PyRIT/samples/security-evaluator</string>", f"<string>{service_working_dir}</string>")
    content = re.sub(
        r"<key>API_HOST</key>\s*<string>.*?</string>",
        f"<key>API_HOST</key>\n      <string>{host}</string>",
        content,
        flags=re.DOTALL,
    )
    content = re.sub(
        r"<key>API_PORT</key>\s*<string>.*?</string>",
        f"<key>API_PORT</key>\n      <string>{port}</string>",
        content,
        flags=re.DOTALL,
    )

    output_path = SAMPLE_DIR / "scripts" / "installers" / "app_service" / "macos" / "com.pyrit.redteam.api.generated.plist"
    write_text_file(path=output_path, content=content)
    return output_path


def setup_api_service(*, platform_name: str, install_service: bool, python_exe: str) -> None:
    """Generate service wrappers and optionally install/start service."""
    host = prompt(message="API service host", default="0.0.0.0")
    port = prompt_int(message="API service port", default=8088, min_value=1, max_value=65535)
    service_working_dir, service_python_exe = prompt_service_paths(
        platform_name=platform_name,
        local_python_exe=python_exe,
    )

    if platform_name == "windows":
        print(f"Service install script: {WINDOWS_SERVICE_INSTALL_SCRIPT}")
        print(
            "Install command preview: "
            f"powershell -ExecutionPolicy Bypass -File {WINDOWS_SERVICE_INSTALL_SCRIPT} "
            f"-WorkingDirectory {service_working_dir} -PythonExe {service_python_exe} "
            f"-Host {host} -Port {port}"
        )
        if install_service:
            if local_platform_name() != "windows":
                raise RuntimeError("Windows service installation can only run on a Windows host.")
            run_command(
                [
                    "powershell",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(WINDOWS_SERVICE_INSTALL_SCRIPT),
                    "-WorkingDirectory",
                    service_working_dir,
                    "-PythonExe",
                    service_python_exe,
                    "-Host",
                    host,
                    "-Port",
                    str(port),
                ],
                cwd=SAMPLE_DIR,
                check=True,
            )
        else:
            print("Skip selected: service wrapper script was left unchanged.")
        return

    if platform_name == "linux":
        generated_path = generate_linux_service_file(
            service_python_exe=service_python_exe,
            service_working_dir=service_working_dir,
            host=host,
            port=port,
        )
        print(f"Generated Linux service file: {generated_path}")
        if install_service:
            if local_platform_name() != "linux":
                raise RuntimeError("Linux service installation can only run on a Linux host.")
            run_command(["sudo", "cp", str(generated_path), "/etc/systemd/system/pyrit-redteam-api.service"], check=True)
            run_command(["sudo", "systemctl", "daemon-reload"], check=True)
            run_command(["sudo", "systemctl", "enable", "pyrit-redteam-api"], check=True)
            run_command(["sudo", "systemctl", "start", "pyrit-redteam-api"], check=True)
            run_command(["sudo", "systemctl", "status", "pyrit-redteam-api"], check=True)
        return

    if platform_name == "macos":
        generated_path = generate_macos_plist(
            service_python_exe=service_python_exe,
            service_working_dir=service_working_dir,
            host=host,
            port=port,
        )
        print(f"Generated macOS launchd file: {generated_path}")
        if install_service:
            if local_platform_name() != "macos":
                raise RuntimeError("macOS service installation can only run on a macOS host.")
            launch_agents_dir = Path.home() / "Library" / "LaunchAgents"
            launch_agents_dir.mkdir(parents=True, exist_ok=True)
            target_path = launch_agents_dir / "com.pyrit.redteam.api.plist"
            run_command(["cp", str(generated_path), str(target_path)], check=True)
            run_command(["launchctl", "load", str(target_path)], check=True)
            run_command(["launchctl", "start", "com.pyrit.redteam.api"], check=True)
        return

    raise RuntimeError(f"Unsupported platform choice: {platform_name}")
