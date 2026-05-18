# PyRIT Local Installation & Configuration

Install and configure PyRIT directly on your machine for red-team testing.

## Prerequisites

- Python 3.11 or 3.12 recommended for the smoothest dependency install path
- SQLite 3.x
- Ollama running locally (`http://localhost:11434`)
- Available Ollama models (e.g., `llama3.2`, `mistral`, `phi3`)

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


