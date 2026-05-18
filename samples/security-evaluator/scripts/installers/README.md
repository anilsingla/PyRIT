# Installers

This folder contains setup and installation tooling for `samples/security-evaluator`.

Use this folder if you want either:
- one guided, end-to-end setup flow, or
- individual install scripts that can be run independently.

## Full Setup (Everything)

Run the interactive installer from `samples/security-evaluator/`:

```bash
python scripts/installers/install_security-evaluator.py
```

What it can do in one flow:
- install Python dependencies
- install SQLite
- install Ollama and pull default models (local mode)
- install Docker and optionally start compose stack (docker mode)
- create/update `.env.local` and `.pyrit_config`
- run config validation and optional smoke checks
- generate/install API service wrappers (Windows/Linux/macOS)

## Individual Install Scripts

All scripts below can be run on their own.

### SQLite + PyRIT bootstrap

Linux/macOS:

```bash
bash scripts/installers/setup_sqlite_linux.sh
```

Windows PowerShell:

```powershell
.\scripts\installers\setup_sqlite_windows.ps1
```

### Docker install

Linux/macOS:

```bash
bash scripts/installers/install_docker_linux.sh
```

Windows PowerShell:

```powershell
.\scripts\installers\install_docker_windows.ps1
```

### Ollama install

Linux/macOS:

```bash
bash scripts/installers/install_ollama_linux.sh
```

Windows PowerShell:

```powershell
.\scripts\installers\install_ollama_windows.ps1
```

### Component install actions via Python CLI

You can also run specific installer actions with:

```bash
python scripts/installers/platform_installers.py --install <component> --platform <windows|linux|macos>
```

Supported `<component>` values:
- `sqlite`
- `ollama`
- `docker`
- `jupyter`
- `python-packages`
- `pull-models`

Example:

```bash
python scripts/installers/platform_installers.py --install sqlite --platform linux
```

## Internal Orchestration Modules

- `setup_wizard.py`: main orchestration logic used by `install_security-evaluator.py`
- `menu.py`: interactive prompt collection
- `configuration.py`: `.env.local` and `.pyrit_config` file writing/validation
- `services.py`: API service wrapper generation/install logic
- `commands.py`, `constants.py`, `prompts.py`, `models.py`: shared helpers

## Notes

- Run commands from `samples/security-evaluator/` unless noted otherwise.
- Some operations require admin/sudo privileges (package installs, service install/start).
- If you only want to validate config without installing packages, run:

```bash
python scripts/helper/verification/validate_redteam_config.py
```

## Common Issues and Solutions

### All Platforms

**Python version mismatch**
- Issue: `python: command not found` or `Python 3.9+ required`
- Solution: Use `python3 --version` to verify. Add alias if needed: `alias python=python3`
- Windows: Check Environment Variables → PATH includes Python installation directory

**Port conflicts**
- Issue: `Address already in use` when starting API or Ollama
- Solution: Change port in `.env.local` (e.g., `OLLAMA_PORT=11435`) or stop conflicting service
- Linux: `sudo lsof -i :11434` to find process using port

**Permission denied errors**
- Issue: Scripts fail with permission/access errors
- Solution: Run installer with appropriate privileges; don't use `sudo` for Python venv commands (only for system package installs)

**Proxy/network issues**
- Issue: Download failures, timeouts, or `Connection refused`
- Solution: Configure proxy in `.env.local` if behind corporate firewall; check internet connectivity

### Windows

**PowerShell execution policy**
- Issue: `Cannot be loaded because running scripts is disabled on this system`
- Solution: Run PowerShell as Administrator and execute:
  ```powershell
  Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
  ```

**Administrator privileges required**
- Issue: `Access Denied` when installing or creating services
- Solution: Run PowerShell or Command Prompt as Administrator (right-click → Run as administrator)

**Paths with spaces or special characters**
- Issue: Script fails when PyRIT installed in `Program Files` or paths with spaces
- Solution: Use quotes around paths in commands, or install in a path without spaces (e.g., `C:\dev\PyRIT`)

**NSSM service installation fails**
- Issue: Service doesn't appear in Windows Services or fails to start
- Solution: Ensure running as Administrator; verify working directory path exists and is accessible; check Python path in service config matches your venv

**Python virtual environment issues on Windows**
- Issue: `activate.ps1` not found or activation fails
- Solution: Recreate venv: `python -m venv .venv` then `. .\.venv\Scripts\Activate.ps1`

### Linux

**sudo password prompt hangs**
- Issue: Installer waits for sudo password indefinitely
- Solution: Provide password when prompted or run without `sudo` for non-privileged tasks

**Missing build tools**
- Issue: `gcc: command not found` or similar during package compilation
- Solution: Install build essentials:
  ```bash
  sudo apt update
  sudo apt install build-essential python3-dev  # Debian/Ubuntu
  sudo yum groupinstall "Development Tools"     # RHEL/CentOS
  ```

**Permission denied on scripts**
- Issue: `Permission denied` when running `.sh` scripts
- Solution: Make executable: `chmod +x scripts/installers/*.sh`

**Systemd service installation issues**
- Issue: Service doesn't start or `Failed to restart`: `sudo systemctl status pyrit-redteam-api`
- Solution: Check service file in `/etc/systemd/system/`, verify WorkingDirectory and Python path exist, reload daemon: `sudo systemctl daemon-reload`

**SQLite permission errors**
- Issue: Database locked or read-only errors
- Solution: Ensure write permissions in `.pyrit_data/` directory: `chmod 755 .pyrit_data/`

**Docker daemon permission errors**
- Issue: `permission denied while trying to connect to Docker daemon`
- Solution: Add user to docker group: `sudo usermod -aG docker $USER` then logout/login or `newgrp docker`

### macOS

**Xcode command line tools missing**
- Issue: `xcrun: error: unable to find utility` or `clang: error: no such file or directory`
- Solution: Install Xcode tools: `xcode-select --install`

**Homebrew conflicts or slow installation**
- Issue: `homebrew-core is a shallow clone` warnings or very slow `brew install` commands
- Solution: Run `brew update` and consider switching Homebrew mirror if behind slow network

**Launchd plist permission issues**
- Issue: Service fails to load or `Permission denied` when copying plist
- Solution: Ensure target directory exists: `mkdir -p ~/Library/LaunchAgents` and file permissions are correct:
  ```bash
  chmod 644 ~/Library/LaunchAgents/com.pyrit.redteam.api.plist
  launchctl unload ~/Library/LaunchAgents/com.pyrit.redteam.api.plist  # if already loaded
  launchctl load ~/Library/LaunchAgents/com.pyrit.redteam.api.plist
  ```

**M1/M2 (Apple Silicon) compatibility**
- Issue: `arch mismatch` errors or services won't start with native Python
- Solution: Ensure Python and dependencies are compiled for ARM64 (native). Check architecture: `python -c "import platform; print(platform.machine())"`
- If using x86 Python under Rosetta, Docker/Ollama may have compatibility issues

**Directory not writable**
- Issue: `Error writing file: Permission denied` for `.env.local` or database
- Solution: Check ownership and permissions: `ls -la .env.local` and adjust if needed: `chmod u+w .env.local`

**Python virtual environment on macOS**
- Issue: Activation script not found after `python -m venv .venv`
- Solution: Use: `source .venv/bin/activate` (note `source` prefix and `bin/` not `Scripts/`)
