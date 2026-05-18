# RedTeam Ollama API

This folder exposes the sample utility in `scripts/app/main.py` over HTTP/HTTPS.

New to this sample? Start with [START_HERE.md](../START_HERE.md) for a simple step-by-step path from first run to advanced modes.

## Full setup guide

- See [API_SETUP_GUIDE.md](API_SETUP_GUIDE.md) for dependencies, installation, requirements, and step-by-step setup.
- For a guided install that also writes sample config files, use [../scripts/installers/install_security_evaluator.py](../scripts/installers/install_security_evaluator.py).

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
- Host: `127.0.0.1`
- Port: `8088`

To intentionally expose the API on a network interface, set:
- `API_HOST=0.0.0.0` (or another non-local host)
- `API_ALLOW_REMOTE_HOST=true`

Optional endpoint auth (disabled by default):
- `API_AUTH_ENABLED=false` (default)
- `API_BEARER_TOKEN=<token>` (required only when `API_AUTH_ENABLED=true`)

## Start API (HTTPS)

Set env vars before running:

- `API_SSL_CERTFILE=/path/to/cert.pem`
- `API_SSL_KEYFILE=/path/to/key.pem`

Then run:

```bash
python -m api.run_api
```

## Optional bearer auth (explicit enable)

The API auth control is optional and disabled by default.

When enabled, all `/api/v1/*` endpoints require `Authorization: Bearer <token>`.

Example:

- `API_AUTH_ENABLED=true`
- `API_BEARER_TOKEN=replace-with-strong-random-value`

Request example:

```bash
curl -H "Authorization: Bearer replace-with-strong-random-value" http://localhost:8088/api/v1/options
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
- The API does not include built-in authentication. Keep it bound to localhost, or place it behind an authenticated reverse proxy before remote exposure.

## Example clients

- PowerShell and curl clients are available in `api/examples/`.
- Start with [examples/README.md](examples/README.md).

