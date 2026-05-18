# PyRIT Docker Setup & Configuration

Run PyRIT in Docker while keeping Ollama on your host machine.
This guide includes Docker installation, a unified container setup for PyRIT + evaluator commands + JupyterLab, and a beginner-friendly end-to-end flow.

## Architecture

```
+-----------------------------------------------------+
| Host Machine                                        |
| +-----------------------------+                     |
| | Ollama (localhost:11434)    |                     |
| +-----------------------------+                     |
|                 |                                   |
|                 | bridge/host-gateway networking    |
|                 v                                   |
| +-----------------------------------------------+   |
| | Unified Security Evaluator Container          |   |
| | PyRIT CLI + evaluator commands                |   |
| | JupyterLab on 8888                            |   |
| | Shared repo mount + SQLite database           |   |
| +-----------------------------------------------+   |
+-----------------------------------------------------+
```

## 1) Install Docker first (Windows, Linux, macOS)

### Windows

1. Install Docker Desktop from https://www.docker.com/products/docker-desktop/
2. Enable WSL2 backend when prompted.
3. Open Docker Desktop and confirm engine is running.
4. Verify installation:

```powershell
docker --version
docker compose version
```

### macOS

1. Install Docker Desktop from https://www.docker.com/products/docker-desktop/
2. Launch Docker Desktop and wait for "Engine running".
3. Verify installation:

```bash
docker --version
docker compose version
```

### Linux

Ubuntu/Debian example:

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo $VERSION_CODENAME) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker $USER
```

Then log out and back in (or run `newgrp docker`) and verify:

```bash
docker --version
docker compose version
```

## 2) Prerequisites for PyRIT in Docker

- Ollama running on the host (`http://localhost:11434`)
- One or more pulled models (for example `llama3.2`, `mistral`, `phi3`)
- PyRIT repository cloned locally

Quick host checks:

```bash
ollama list
curl http://localhost:11434/api/tags
```

## 3) Use the provided Docker setup for the unified runtime

This repository now includes a ready-to-use compose file at `samples/security-evaluator/docker-compose.yaml`.

Default service in that file:

- `copyrit`: unified runtime container for evaluator commands and JupyterLab

If you want to customize it, start from this baseline:

```yaml
services:
  copyrit:
    build:
      context: .
      dockerfile: Dockerfile.pyrit-copyrit-quick
    container_name: security-evaluator-copyrit
    working_dir: /workspace
    command: bash -lc "jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root & tail -f /dev/null"
    ports:
      - "8888:8888"
    volumes:
      - ../../:/workspace
    environment:
      OLLAMA_ENDPOINT: http://host.docker.internal:11434/v1
      OLLAMA_TARGET_MODEL: llama3.2
      OLLAMA_ATTACKER_MODEL: mistral
      OLLAMA_TF_SCORER_MODEL: phi3
      OLLAMA_SCALE_SCORER_MODEL: llama2
      OLLAMA_REFUSAL_SCORER_MODEL: mistral
      PYRIT_SQLITE_DB_PATH: /workspace/samples/security-evaluator/reports/pyrit_ollama_demo.db
      ARTIFACTS_ROOT_PATH: /workspace/samples/security-evaluator/reports
      LOGS_ROOT_PATH: /workspace/samples/security-evaluator/logs
    extra_hosts:
      - "host.docker.internal:host-gateway"
```

Linux note: if `host.docker.internal` is not available, use host gateway IP in environment values.

## 4) Start containers

From repository root:

```bash
docker compose -f samples/security-evaluator/docker-compose.yaml up -d
docker compose -f samples/security-evaluator/docker-compose.yaml ps
```

Expected: the single `copyrit` service is `Up` and JupyterLab is reachable on port `8888`.

## 5) Configure and run security-evaluator in the unified container

Enter the unified runtime container:

```bash
docker compose -f samples/security-evaluator/docker-compose.yaml exec copyrit bash
```

Inside container:

```bash
cd samples/security-evaluator
cp config/.env.local.example .env.local
cp config/.pyrit_config.example .pyrit_config
python scripts/app/main.py --dry-run
python scripts/app/main.py --attack-mode baseline
```

Artifacts are written under `samples/security-evaluator/reports/` on your host because the repository is volume-mounted.

## 6) Use JupyterLab in the unified container

Open Jupyter in browser:

```text
http://localhost:8888
```

Open notebooks under `doc/` or `samples/security-evaluator/` and run with the same mounted workspace.

Use JupyterLab for interactive analysis of run artifacts, scoring results, and case reports.

## 7) Optional GUI workflow for analysis

> Optional
>
> Use this only if you want a separate graphical analysis interface. The unified container quick start does not require it.

The PyRIT GUI reads the same SQLite database file that the evaluator run writes to on the host. That means the GUI can show your results as long as it points to the same `.db` file.

### How the SQLite database is accessible to the GUI

1. The evaluator writes to `samples/security-evaluator/reports/pyrit_ollama_demo.db` on the host.
2. The GUI must either run on the same machine and mount the same repository folder, or receive a copy of that `.db` file.
3. The GUI should use the same `PYRIT_SQLITE_DB_PATH` value, or point to the copied database file on the GUI host.
4. Because SQLite is a single file, the GUI can open the database directly without a separate database server.

### Option A: GUI on the same machine

If you want the GUI on the same host, keep the repository mounted and use the same database path:

```yaml
services:
  gui:
    image: python:3.11-slim
    working_dir: /workspace/doc/code
    volumes:
      - ../../:/workspace
    environment:
      PYRIT_SQLITE_DB_PATH: /workspace/samples/security-evaluator/reports/pyrit_ollama_demo.db
      OLLAMA_ENDPOINT: http://host.docker.internal:11434/v1
```

### Option B: GUI on a different host

If the GUI runs somewhere else, copy the database file first and then point the GUI to that copied file:

```bash
scp samples/security-evaluator/reports/pyrit_ollama_demo.db user@gui-host:/tmp/pyrit_ollama_demo.db
```

Then set the GUI database path on the analysis host:

```bash
export PYRIT_SQLITE_DB_PATH=/tmp/pyrit_ollama_demo.db
python pyrit_gui.py
```

### When to use the GUI

- Use the unified container for the normal evaluator workflow and JupyterLab analysis.
- Use the GUI only when you want a visual browser-based review of the same SQLite-backed reports.

## 7) Step-by-step install for a new Docker user

Follow this exact order:

1. Install Docker Desktop (Windows/macOS) or Docker Engine + Compose plugin (Linux).
2. Confirm `docker --version` and `docker compose version` both work.
3. Install and start Ollama on host.
4. Pull at least one model (`ollama pull llama3.2`).
5. Clone PyRIT repository.
6. Use the provided `samples/security-evaluator/docker-compose.yaml` file.
7. Run `docker compose -f samples/security-evaluator/docker-compose.yaml up -d`.
8. Enter the unified container and run `--dry-run` first.
9. Run first real attack (`baseline`).
10. Open Jupyter at `http://localhost:8888` for notebook-based analysis.

## 8) Stopping and cleanup

```bash
# Stop containers
docker compose -f samples/security-evaluator/docker-compose.yaml down

# Stop and remove anonymous volumes
docker compose -f samples/security-evaluator/docker-compose.yaml down -v

# Remove containers/images created by this compose
docker compose -f samples/security-evaluator/docker-compose.yaml rm -f
```

## 9) Troubleshooting

### Cannot reach Ollama from container

- Verify host endpoint: `curl http://localhost:11434/api/tags`
- Verify compose has `extra_hosts: host.docker.internal:host-gateway`
- Linux fallback: set `OLLAMA_ENDPOINT=http://172.17.0.1:11434/v1`

### Jupyter port already in use

- Change mapping from `8888:8888` to `8890:8888`
- Restart: `docker compose -f samples/security-evaluator/docker-compose.yaml up -d`

### Permission denied on mounted files (Linux)

- Ensure your user owns repository directory
- Run container with matching UID/GID if needed

## Next steps

- Run the red-team sample: see [Quickstart](../script/quickstart.md)
- Review configuration options: see [Usage Guide](../script/usage_guide.md)
