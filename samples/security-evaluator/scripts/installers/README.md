# Installers

This folder contains setup and installation tooling for `samples/security-evaluator`.

Use this folder if you want either:
- one guided, end-to-end setup flow, or
- individual install scripts that can be run independently.

## Full Setup (Everything)

Run the interactive installer from `samples/security-evaluator/`:

```bash
python scripts/installers/install_security_evaluator.py
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

### Ollama install + setup (install, start, pull, test)

Linux/macOS:

```bash
bash scripts/installers/setup_ollama_linux.sh
```

Windows PowerShell:

```powershell
.\scripts\installers\setup_ollama_windows.ps1
```

Useful environment variables for setup scripts:
- `OLLAMA_MODELS` (default: `llama3.2 mistral phi3`)
- `SKIP_PULL` (`true`/`false`)
- `START_OLLAMA` (`true`/`false`)
- `TEST_MODEL` (model for non-interactive test)
- `OLLAMA_ENDPOINT` (default: `http://localhost:11434`)

Windows-only:
- `ENABLE_STARTUP_TASK=true` creates a startup task for `ollama serve`

Linux-only:
- `ENABLE_SYSTEMD_SERVICE=true` attempts `systemctl enable --now ollama`

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

- `setup_wizard.py`: main orchestration logic used by `install_security_evaluator.py`
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

---

## SQLite Database: Architecture & Volume Mounting

This section explains where SQLite is physically stored and how Docker containers access the shared database file.

### WHERE SQLITE IS INSTALLED AND STORED

#### SQLite Binary (executable)

The SQLite command-line tool is installed on your **host machine** operating system:

**Linux/Ubuntu:**
- Installation command: `apt-get install sqlite3`
- Location: `/usr/bin/sqlite3`

**macOS:**
- Built-in: `/usr/bin/sqlite3` (system version)
- Or Homebrew: `brew install sqlite3` → `/usr/local/bin/sqlite3`

**Windows:**
- Installation command: `winget install SQLite.SQLite` or `choco install sqlite`
- Typical location: `C:\Program Files\sqlite\sqlite3.exe` or `C:\ProgramData\chocolatey\lib\sqlite\`

#### SQLite Database File (data)

The **database file** (`.db`) is stored on the **host machine** filesystem:

```
HOST MACHINE DISK
└── <YOUR_REPO_ROOT>/
    └── samples/security-evaluator/
        └── reports/
            └── pyrit_ollama_demo.db  ← PHYSICAL DATABASE FILE (HOST STORAGE)
```

**Example paths:**

Linux/macOS:
```
/home/user/PyRIT/samples/security-evaluator/reports/pyrit_ollama_demo.db
/Users/user/PyRIT/samples/security-evaluator/reports/pyrit_ollama_demo.db
```

Windows:
```
C:\Users\user\Documents\PyRIT\samples\security-evaluator\reports\pyrit_ollama_demo.db
```

### HOW CONTAINERS ACCESS THE DATABASE

When you run Docker containers with `docker-compose.yaml`, they do **not** have their own copies of the database. Instead, they access the **same host file** through **volume mounting**:

```
docker-compose.yaml:
┌─────────────────────────────────────────────────────────────────┐
│ services:                                                       │
│   copyrit:                                                      │
│     volumes:                                                    │
│       - ../../:/workspace  ← VOLUME MOUNT                       │
│     environment:                                                │
│       PYRIT_SQLITE_DB_PATH: /workspace/samples/.../pyrit...db   │
│                                                                 │
│   unified runtime:                                              │
│     volumes:                                                    │
│       - ../../:/workspace  ← SAME VOLUME MOUNT                  │
│     environment:                                                │
│       PYRIT_SQLITE_DB_PATH: /workspace/samples/.../pyrit...db   │
└─────────────────────────────────────────────────────────────────┘
```

**Volume Mount Mechanism:**

```
HOST FILESYSTEM                      CONTAINER FILESYSTEM
────────────────────────────────────────────────────────────────
/repo_root/  ←─────── volume bind ─────→ /workspace/
  ├─ samples/                             ├─ samples/
  │ └─ security-evaluator/                │ └─ security-evaluator/
  │   └─ reports/                         │   └─ reports/
  │     └─ pyrit_ollama_demo.db           │     └─ pyrit_ollama_demo.db
  │        ↑                              │        ↑
  │        └──────── SAME FILE ───────────┘
```

**Key Points:**

- **Volume mount** `../../:/workspace` binds the host repo root to `/workspace` inside the container
- The host and the unified container access the **same database file** on the host disk
- **No copying**, **no synchronization** - direct access to host filesystem
- SQLite file locking keeps access safe if you also open the same file from host-side tools

### HOW THE UNIFIED CONTAINER USES ONE DATABASE

The unified security-evaluator container in `docker-compose.yaml`:

1. Shares the **same volume mount** → `/workspace`
2. Uses the **same environment variable** → `PYRIT_SQLITE_DB_PATH=/workspace/.../pyrit_ollama_demo.db`
3. Accesses the **same host file** → no duplication
4. Uses **SQLite's file locking** → safe access if you open the database from multiple host-side tools

```
┌──────────────────────────────────────────────────────┐
│ docker-compose up -d                                 │
├──────────────────────────────────────────────────────┤
│                                                      │
│  unified container                                   │
│  ├─ mounts ../../                                    │
│  ├─ sets DB_PATH to /workspace/.../pyrit...db        │
│  └─→ FILE A (on host)                                │
│                                                      │
│  JupyterLab + evaluator commands use the same file   │
│  SQLite prevents conflicts via file locking          │
│                                                      │
└──────────────────────────────────────────────────────┘
```

### VERIFYING SETUP

**1. Check database file on host:**

```bash
ls -la samples/security-evaluator/reports/pyrit_ollama_demo.db
sqlite3 samples/security-evaluator/reports/pyrit_ollama_demo.db '.tables'
```

**2. Start containers and verify access from inside:**

```bash
docker-compose -f samples/security-evaluator/docker-compose.yaml up -d
docker-compose -f samples/security-evaluator/docker-compose.yaml exec copyrit bash
```

**Inside container:**

```bash
# Verify the file exists via volume mount
ls -la /workspace/samples/security-evaluator/reports/pyrit_ollama_demo.db

# Access from Python
python3 << 'EOF'
import sqlite3
db = sqlite3.connect('/workspace/samples/security-evaluator/reports/pyrit_ollama_demo.db')
cursor = db.cursor()
cursor.execute("SELECT sqlite_version()")
print(f"SQLite version: {cursor.fetchone()[0]}")
db.close()
EOF
```

**3. Run verification script:**

```bash
bash samples/security-evaluator/scripts/installers/verify_sqlite_volume_mount.sh
```

This script verifies:
- Database file exists on host
- The unified container can access the same file
- File checksums match (same file, not copied)
- Host and container are reading the same database

### TROUBLESHOOTING

**Database file not found in container:**
- **Cause:** Volume mount misconfigured
- **Solution:** Check `docker-compose.yaml` has `volumes: ../../:/workspace`
- **Verify:** `docker-compose exec copyrit ls -la /workspace`

**"Database is locked" errors:**
- **Cause:** Usually normal SQLite journaling behavior with concurrent access
- **Solution:** This is expected with high concurrency. Reduce parallel writes or increase SQLite timeout
- **Check:** SQLite uses OS-level file locking; conflicts should be rare

**Different database content in container vs host:**
- **Cause:** Likely running different database files or an outdated container image
- **Solution:**
  - Verify `PYRIT_SQLITE_DB_PATH` environment variable in compose file
  - Ensure containers are stopped/rebuilt: `docker-compose down && docker-compose build`
  - Confirm volume path: `docker-compose exec copyrit echo $PYRIT_SQLITE_DB_PATH`

**Can't write to database from container:**
- **Cause:** Permission issues on host filesystem
- **Solution:** 
  - On Linux: Check file permissions: `ls -la samples/security-evaluator/reports/`
  - Fix if needed: `chmod 666 samples/security-evaluator/reports/pyrit_ollama_demo.db`
  - Or use: `docker-compose exec -u root copyrit`
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
