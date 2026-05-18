# PyRIT Docker Setup & Configuration

Run PyRIT in Docker containers while keeping Ollama on your host machine.

## Architecture

```
+-------------------------------------+
¦  Host Machine                       ¦
¦  +-----------------------------+    ¦
¦  ¦ Ollama (localhost:11434)    ¦    ¦
¦  ¦ Running models              ¦    ¦
¦  +-----------------------------+    ¦
¦            ?                        ¦
¦            ¦ (bridge/host network)  ¦
¦            ¦                        ¦
¦  +-----------------------------+    ¦
¦  ¦ Docker Container            ¦    ¦
¦  ¦  PyRIT + SQLite             ¦    ¦
¦  ¦  Scripts                    ¦    ¦
¦  +-----------------------------+    ¦
+-------------------------------------+
```

## Prerequisites

- Docker and Docker Compose installed
- Ollama running on host (`http://localhost:11434`)
- Target PyRIT repository cloned locally

## Quick start

From the repository root:

```bash
cd docker/
docker-compose up -d
```

Verify the container is running:

```bash
docker ps
```

Access shell inside container:

```bash
docker-compose exec pyrit bash
```

## Running the sample script in Docker

Once inside the container:

```bash
cd samples/security-evaluator/scripts/
python app/main.py
```

To do a quick validation run first:

```bash
python app/main.py --dry-run
```

## Mounting and persisting artifacts

Edit `docker/docker-compose.yaml` to mount local paths:

```yaml
volumes:
  - ./reports:/app/reports           # Persist artifacts  
  - ./logs:/app/logs                 # Persist logs
  - ./samples:/app/samples           # Mount samples
```

After running a red-team scenario, outputs appear on your host:

```
./reports/scorer_comparison.csv
./reports/run_report.json
./reports/cases/...
./logs/pyrit_owasp_redteam_production.log
```

## Environment configuration

Create or edit a `.env` file in the Docker directory:

```env
OLLAMA_ENDPOINT=http://host.docker.internal:11434/v1
OLLAMA_TARGET_MODEL=llama3.2
OLLAMA_ATTACKER_MODEL=mistral
PYLANCE_PYTHON_ENV=.venv
```

On Linux, use the host IP instead of `host.docker.internal`:

```env
OLLAMA_ENDPOINT=http://172.17.0.1:11434/v1
```

Pass to docker-compose:

```bash
docker-compose --env-file .env up
```

## Stopping and cleanup

```bash
# Stop containers  
docker-compose down

# Remove volumes (delete persisted data)
docker-compose down -v

# Rebuild image
docker-compose build --no-cache
```

## Troubleshooting

**"Cannot reach Ollama from container"**

- Verify Ollama is running on host: `curl http://localhost:11434/api/tags`
- Check Docker network: `docker network inspect bridge`
- On Linux, use host gateway IP instead of `host.docker.internal`

**"Port 8501 already in use"**

- Change GUI port in `docker-compose.yaml`
- Or check existing processes: `lsof -i :8501`

## Next steps

- Run the red-team sample: see [Quickstart](../../docs/script/quickstart.md)
- Set up GUI analysis: see [GUI Tutorial](gui_setup.md)
- Review configuration options: see [Usage Guide](../../docs/script/usage_guide.md)
