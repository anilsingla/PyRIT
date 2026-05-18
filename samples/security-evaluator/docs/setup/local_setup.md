# PyRIT Local Installation & Configuration

Install and configure PyRIT directly on your machine for red-team testing.

## Prerequisites

- Python 3.11 or 3.12 recommended for the smoothest dependency install path
- SQLite 3.x
- Ollama installed locally
- Available Ollama models (e.g., `llama3.2`, `mistral`, `phi3`)

## Install and configure Ollama locally

PyRIT security-evaluator uses Ollama as the local model runtime. Complete this section before running attacks.

### 1) Install Ollama

Recommended one-command setup scripts (same location pattern as SQLite setup):

Windows (PowerShell):

```powershell
Set-Location samples/security-evaluator
.\scripts\installers\setup_ollama_windows.ps1
```

Linux/macOS (bash):

```bash
cd samples/security-evaluator
bash scripts/installers/setup_ollama_linux.sh
```

Manual install options:

Windows (PowerShell, winget):

```powershell
winget install Ollama.Ollama
```

macOS (Homebrew):

```bash
brew install ollama
```

Linux (official installer):

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Verify installation:

```bash
ollama --version
```

### 2) Start the Ollama service

On most systems, Ollama auto-starts after installation. If needed, start it manually:

```bash
ollama serve
```

Notes:
1. Keep this process running while using PyRIT.
2. Default local endpoint is `http://localhost:11434`.
3. PyRIT uses the OpenAI-compatible path `http://localhost:11434/v1` in `.env.local`.

### 2.1) Keep Ollama running after reboot (optional)

Linux (systemd):

```bash
sudo systemctl enable --now ollama
sudo systemctl status ollama
```

macOS (Homebrew service):

```bash
brew services start ollama
brew services list | grep ollama
```

Windows (startup task):

```powershell
$env:ENABLE_STARTUP_TASK = "true"
.\scripts\installers\setup_ollama_windows.ps1
```

This creates a logon task that starts `ollama serve` automatically.

### 3) Pull required models

Download one or more models before running tests:

```bash
ollama pull llama3.2
ollama pull mistral
ollama pull phi3
```

Check downloaded models:

```bash
ollama list
```

### 4) Run/test a model interactively

Use this to verify local inference is working:

```bash
ollama run llama3.2
```

Type a test prompt and confirm you receive a response, then exit with `Ctrl+C`.

Non-interactive quick check:

```bash
ollama run llama3.2 "Reply with OLLAMA_OK"
```

### 5) Verify the HTTP endpoint

If Ollama is running correctly, the tags endpoint should respond:

```bash
curl http://localhost:11434/api/tags
```

If this fails, restart the service with `ollama serve` and retry.

### 6) Configure PyRIT to use local Ollama

Set these values in `samples/security-evaluator/.env.local`:

```dotenv
OLLAMA_ENDPOINT=http://localhost:11434/v1
OLLAMA_TARGET_MODEL=llama3.2
OLLAMA_ATTACKER_MODEL=mistral
OLLAMA_TF_SCORER_MODEL=llama3.2
OLLAMA_SCALE_SCORER_MODEL=llama3.2
OLLAMA_REFUSAL_SCORER_MODEL=llama3.2
```

You can reuse one model for all roles, but using a smaller attacker model can reduce runtime and resource usage.

### 7) Minimal end-to-end sanity check

From `samples/security-evaluator`:

```bash
python scripts/app/main.py --dry-run
```

This validates config and connectivity before any real attack run.

## Platform-specific setup

### Windows

Use the PowerShell setup script:

```powershell
Set-Location samples/security-evaluator
.\scripts\installers\setup_sqlite_windows.ps1
```

This script:
1. Installs SQLite via winget/chocolatey/scoop
2. Creates Python virtual environment
3. Installs/updates PyRIT
4. Runs a smoke test

### Linux/macOS

Use the Bash setup script:

```bash
cd samples/security-evaluator
bash scripts/installers/setup_sqlite_linux.sh
```

This script:
1. Installs sqlite3 via your package manager
2. Creates Python virtual environment
3. Installs/updates PyRIT
4. Runs a smoke test

## Quick start (5 minutes)

### Windows (PowerShell)

```powershell
Set-Location samples/security-evaluator
.\scripts\installers\setup_sqlite_windows.ps1
python scripts/app/main.py --dry-run
```

### Linux/macOS (bash)

```bash
cd samples/security-evaluator
bash scripts/installers/setup_sqlite_linux.sh
python scripts/app/main.py --dry-run
```

## Manual setup (if not using scripts)

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\Activate on Windows

# Install PyRIT
pip install --upgrade pip
pip install pyrit

# Verify SQLite support
python -c "from pyrit.setup import SQLITE, initialize_pyrit_async; print('[OK] PyRIT SQLITE support available')"
```

## Post-installation verification

Confirm Ollama is reachable:

```bash
curl http://localhost:11434/api/tags
```

Or run the smoke test:

```bash
python -c "
import asyncio
from pyrit.setup import SQLITE, initialize_pyrit_async
from pyrit.memory import CentralMemory

async def test():
    await initialize_pyrit_async(memory_db_type=SQLITE, db_path='test.db')
    mem = CentralMemory.get_memory_instance()
    print('[OK] PyRIT initialized with SQLITE')

asyncio.run(test())
"
```

## Environment variables

Common configuration options:

```bash
export OLLAMA_ENDPOINT=http://localhost:11434/v1
export OLLAMA_TARGET_MODEL=llama3.2
export DEBUG=false
```

On Windows PowerShell, use:

```powershell
$env:OLLAMA_ENDPOINT = "http://localhost:11434/v1"
$env:OLLAMA_TARGET_MODEL = "llama3.2"
$env:DEBUG = "false"
```

See [Usage Guide](../../docs/script/usage_guide.md) for a complete list.

## Security baseline

- Keep `ALLOW_REMOTE_OLLAMA_ENDPOINT=false` unless you intentionally use a remote endpoint.
- Do not expose Ollama publicly without access controls.
- Treat `reports/` and `logs/` as sensitive and archive/rotate regularly.

## Next steps

- Run the sample red-team script: `python scripts/app/main.py`
- Read the [Quickstart](../../docs/script/quickstart.md)
- Explore [GUI setup](gui_setup.md) for visual analysis


