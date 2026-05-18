# PyRIT Docker Setup & Configuration

Run PyRIT in Docker while keeping Ollama on your host machine.
This guide includes Docker installation, container setup for CoPyRIT (core PyRIT runtime) and Jupyter, and a beginner-friendly end-to-end flow.

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
| +--------+ +--------+ +-------+ |
| | CoPyRIT| | Jupyter| | GUI   | |
| | shell  | | Lab    | | 8501  | |
| | runtime| | 8888   | |       | |
| +--------+ +--------+ +-------+ |
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

## 3) Use the provided Docker setup for CoPyRIT, Jupyter, and GUI

This repository now includes a ready-to-use compose file at `samples/security-evaluator/docker-compose.yaml`.

Default services in that file:

- `copyrit`: core runtime container for security-evaluator commands
- `jupyter`: notebook container for analysis at port `8888`
- `gui`: CoPyRIT GUI (PyRIT Streamlit app) for interactive analysis at port `8501`

If you want to customize it, start from this baseline:

```yaml
services:
  copyrit:
    image: python:3.11-slim
    container_name: security-evaluator-copyrit
    working_dir: /workspace
    command: bash -lc "pip install --upgrade pip pyrit jupyterlab && tail -f /dev/null"
    volumes:
      - ../../:/workspace
    environment:
      OLLAMA_ENDPOINT: http://host.docker.internal:11434/v1
      OLLAMA_TARGET_MODEL: llama3.2
      OLLAMA_ATTACKER_MODEL: mistral
      OLLAMA_TF_SCORER_MODEL: llama3.2
      OLLAMA_SCALE_SCORER_MODEL: llama3.2
      OLLAMA_REFUSAL_SCORER_MODEL: llama3.2
      PYRIT_SQLITE_DB_PATH: /workspace/samples/security-evaluator/reports/pyrit_ollama_demo.db
      ARTIFACTS_ROOT_PATH: /workspace/samples/security-evaluator/reports
      LOGS_ROOT_PATH: /workspace/samples/security-evaluator/logs
    extra_hosts:
      - "host.docker.internal:host-gateway"

  jupyter:
    image: python:3.11-slim
    container_name: security-evaluator-jupyter
    working_dir: /workspace
    command: bash -lc "pip install --upgrade pip pyrit jupyterlab && jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root"
    ports:
      - "8888:8888"
    volumes:
      - ../../:/workspace
    environment:
      OLLAMA_ENDPOINT: http://host.docker.internal:11434/v1
      PYRIT_SQLITE_DB_PATH: /workspace/samples/security-evaluator/reports/pyrit_ollama_demo.db
    extra_hosts:
      - "host.docker.internal:host-gateway"

  gui:
    image: python:3.11-slim
    container_name: security-evaluator-gui
    working_dir: /workspace/doc/code
    command: bash -lc "pip install --upgrade pip pyrit streamlit && streamlit run pyrit_gui.py --server.port=8501 --server.address=0.0.0.0"
    ports:
      - "8501:8501"
    volumes:
      - ../../:/workspace
    environment:
      OLLAMA_ENDPOINT: http://host.docker.internal:11434/v1
      PYRIT_SQLITE_DB_PATH: /workspace/samples/security-evaluator/reports/pyrit_ollama_demo.db
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

Expected: all three services (`copyrit`, `jupyter`, `gui`) are `Up`.

## 5) Configure and run security-evaluator in CoPyRIT container

Enter runtime container:

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

## 6) Use Jupyter container and CoPyRIT GUI

Open Jupyter in browser:

```text
http://localhost:8888
```

Open notebooks under `doc/` or `samples/security-evaluator/` and run with the same mounted workspace.

Open CoPyRIT GUI in browser:

```text
http://localhost:8501
```

Use the GUI for interactive analysis of run artifacts, scoring results, and case reports.

## 7) Step-by-step install for a new Docker user

Follow this exact order:

1. Install Docker Desktop (Windows/macOS) or Docker Engine + Compose plugin (Linux).
2. Confirm `docker --version` and `docker compose version` both work.
3. Install and start Ollama on host.
4. Pull at least one model (`ollama pull llama3.2`).
5. Clone PyRIT repository.
6. Use the provided `samples/security-evaluator/docker-compose.yaml` file.
7. Run `docker compose -f samples/security-evaluator/docker-compose.yaml up -d`.
8. Enter CoPyRIT container and run `--dry-run` first.
9. Run first real attack (`baseline`).
10. Open Jupyter at `http://localhost:8888` for notebook-based analysis.
11. Open CoPyRIT GUI at `http://localhost:8501` for interactive result review.

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

### GUI port (8501) already in use

- Change mapping from `8501:8501` to `8502:8501` in the compose file
- Restart: `docker compose -f samples/security-evaluator/docker-compose.yaml up -d`

### Permission denied on mounted files (Linux)

- Ensure your user owns repository directory
- Run container with matching UID/GID if needed

## Next steps

- Run the red-team sample: see [Quickstart](../script/quickstart.md)
- Set up GUI analysis: see [GUI Tutorial](gui_setup.md)
- Review configuration options: see [Usage Guide](../script/usage_guide.md)
