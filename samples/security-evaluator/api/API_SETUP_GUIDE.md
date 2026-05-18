# RedTeam Ollama API - Setup Guide

This guide explains dependencies, installation, requirements, and step-by-step setup for running the API in `samples/security-evaluator/api`.

## Quick Start (5 minutes)

If you just want it running now:

1. Open a terminal at repository root (`PyRIT/`).
2. Create and activate a virtual environment.
3. Install API dependencies.
4. Start the API from `samples/security-evaluator/`.
5. Test health endpoint.

Windows PowerShell:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r samples/security-evaluator/api/requirements.txt
Set-Location samples/security-evaluator
python -m api.run_api
```

Linux/macOS:
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r samples/security-evaluator/api/requirements.txt
cd samples/security-evaluator
python -m api.run_api
```

In another terminal:
```bash
curl http://localhost:8088/health
```

## 1) What this API does

The API exposes the red-team CLI utility (`scripts/app/main.py`) over HTTP/HTTPS.

Core features:
- Start attacks in background jobs
- Poll job status and read output logs
- Cancel running jobs
- Query available attack/scorer/converter options

Main entrypoint:
- `python -m api.run_api`

## 2) Requirements

- OS: Windows, Linux, or macOS
- Python: 3.11 or 3.12 recommended for the smoothest dependency install path; 3.10+ may work depending on package availability
- Network: Localhost access to chosen API port (default `8088`)
- For full attack execution: a working PyRIT + model setup (for example Ollama endpoint + models)

## 3) Dependencies

### API package dependencies
Declared in `api/requirements.txt`:
- `fastapi>=0.115.0`
- `uvicorn[standard]>=0.32.0`
- `pydantic>=2.11.0`

### Runtime dependencies used by attack jobs
The API launches `scripts/app/main.py`, so the environment must also have the redteam runner dependencies available (PyRIT and configured model backends).

## 4) Installation (step by step)

Run these from repository root (`PyRIT/`) unless noted.

### Step 1: Create virtual environment

Windows PowerShell:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Linux/macOS:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 2: Install API dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r samples/security-evaluator/api/requirements.txt
```

### Step 3: Ensure redteam runner dependencies are installed

If you are using this repo locally, install project/runtime dependencies in the same environment used by the API.

### Step 4: Configure redteam sample (recommended)

From `samples/security-evaluator/`:

Windows PowerShell:
```powershell
Copy-Item config/.env.local.example .env.local
Copy-Item config/.pyrit_config.example .pyrit_config
```

Linux/macOS:
```bash
cp config/.env.local.example .env.local
cp config/.pyrit_config.example .pyrit_config
```

Optional validation:
```bash
python scripts/helper/verification/validate_redteam_config.py
```

## 5) Start the API

From `samples/security-evaluator/`:

```bash
python -m api.run_api
```

Default bind:
- Host: `0.0.0.0`
- Port: `8088`

Swagger/OpenAPI docs:
- `http://localhost:8088/docs`
- `http://localhost:8088/redoc`

## 6) API environment variables

Runtime vars read by `api/run_api.py`:
- `API_HOST` (default: `0.0.0.0`)
- `API_PORT` (default: `8088`)
- `API_RELOAD` (default: `false`)
- `API_SSL_CERTFILE` (optional; enables HTTPS when set)
- `API_SSL_KEYFILE` (optional; enables HTTPS when set)

Example (PowerShell):
```powershell
$env:API_HOST = "127.0.0.1"
$env:API_PORT = "8088"
$env:API_RELOAD = "true"
python -m api.run_api
```

Example (bash/zsh):
```bash
export API_HOST=127.0.0.1
export API_PORT=8088
export API_RELOAD=true
python -m api.run_api
```

## 7) Enable HTTPS

Set certificate and key file paths before starting:

```bash
export API_SSL_CERTFILE=/path/to/cert.pem
export API_SSL_KEYFILE=/path/to/key.pem
python -m api.run_api
```

Then use `https://<host>:<port>`.

## 8) Quick smoke test

### Health endpoint
```bash
curl http://localhost:8088/health
```

### Start dry-run job
```bash
curl -X POST http://localhost:8088/api/v1/runs/dry-run \
  -H "Content-Type: application/json" \
  -d @api/examples/dry_run_payload.json
```

### Poll status + output
```bash
curl http://localhost:8088/api/v1/runs/<job_id>
curl "http://localhost:8088/api/v1/runs/<job_id>/output?tail_lines=200"
```

## 9) Endpoints summary

- `GET /health`
- `GET /api/v1/options`
- `POST /api/v1/runs`
- `POST /api/v1/runs/dry-run`
- `GET /api/v1/runs`
- `GET /api/v1/runs/{job_id}`
- `GET /api/v1/runs/{job_id}/output?tail_lines=200`
- `POST /api/v1/runs/{job_id}/cancel`

## 10) Troubleshooting

- `ModuleNotFoundError: fastapi|uvicorn|pydantic`
  - Reinstall: `python -m pip install -r samples/security-evaluator/api/requirements.txt`

- API starts but runs fail
  - Validate runner setup and models: `python scripts/helper/verification/validate_redteam_config.py`
  - Verify model endpoint and required local services are running.

- HTTPS certificate errors
  - Confirm cert/key paths and key-certificate match.
  - Trust your CA/self-signed cert in local environment if needed.

- Jobs disappear after API restart
  - Expected behavior. Job metadata is in-memory; log output files remain in `reports/api_runs/`.

## 11) Related docs

- API quick reference: `api/README.md`
- Example clients: `api/examples/README.md`
- Service hosting: `scripts/installers/app_service/SERVICES_GUIDE.md`
