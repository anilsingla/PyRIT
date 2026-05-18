# RedTeam Ollama API

This folder exposes the sample utility in `scripts/app/main.py` over HTTP/HTTPS.

New to this sample? Start with [START_HERE.md](../START_HERE.md) for a simple step-by-step path from first run to advanced modes.

## Full setup guide

- See [API_SETUP_GUIDE.md](API_SETUP_GUIDE.md) for dependencies, installation, requirements, and step-by-step setup.
- For a guided install that also writes sample config files, use [../scripts/installers/install_security-evaluator.py](../scripts/installers/install_security-evaluator.py).

## Endpoints

- `GET /health` - Service health probe.
- `GET /api/v1/options` - Supported modes, converters, scorers.
- `POST /api/v1/runs` - Start a background run.
- `POST /api/v1/runs/dry-run` - Start run with `--dry-run` forced.
- `GET /api/v1/runs` - List jobs.
- `GET /api/v1/runs/{job_id}` - Get job status.
- `GET /api/v1/runs/{job_id}/output?tail_lines=200` - Tail log output.
- `POST /api/v1/runs/{job_id}/cancel` - Cancel running job.

## Start API (HTTP)

From `samples/security-evaluator/`:

```bash
python -m api.run_api
```

Default bind:
- Host: `0.0.0.0`
- Port: `8088`

## Start API (HTTPS)

Set env vars before running:

- `API_SSL_CERTFILE=/path/to/cert.pem`
- `API_SSL_KEYFILE=/path/to/key.pem`

Then run:

```bash
python -m api.run_api
```

## Example: start a dry run

```bash
curl -X POST http://localhost:8088/api/v1/runs/dry-run \
  -H "Content-Type: application/json" \
  -d '{
    "options": {
      "attack_mode": "redteam",
      "turn_mode": "single",
      "local_datasets_only": true,
      "converters": ["base64", "leetspeak"],
      "scenarios": ["LLM01", "LLM02"]
    }
  }'
```

## Notes

- Each run writes output to `reports/api_runs/<job_id>.log`.
- Jobs are in-memory; API restart clears active history, while output files remain.

## Example clients

- PowerShell and curl clients are available in `api/examples/`.
- Start with [examples/README.md](examples/README.md).

