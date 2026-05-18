# API Example Clients

This folder contains quick clients for calling the security-evaluator API.

## Files

- `dry_run_payload.json` - Sample request body for `POST /api/v1/runs/dry-run`
- `powershell_client.ps1` - End-to-end PowerShell client (health, options, run, poll, output)
- `curl_client.sh` - End-to-end curl client for Linux/macOS (health, options, run, poll, output)

## PowerShell usage (Windows)

From `samples/security-evaluator/`:

```powershell
.\api\examples\powershell_client.ps1 -BaseUrl "http://localhost:8088"
```

Optional arguments:

- `-PayloadPath .\api\examples\dry_run_payload.json`
- `-TailLines 300`
- `-PollSeconds 2`
- `-MaxPolls 90`

## curl usage (Linux/macOS)

From `samples/security-evaluator/`:

```bash
chmod +x api/examples/curl_client.sh
./api/examples/curl_client.sh http://localhost:8088 ./api/examples/dry_run_payload.json
```

Optional env vars:

- `TAIL_LINES=300`
- `POLL_SECONDS=2`
- `MAX_POLLS=90`

## HTTPS usage

If API runs with TLS, use `https://` base URL:

- PowerShell: `-BaseUrl "https://localhost:8088"`
- curl: `./api/examples/curl_client.sh https://localhost:8088 ./api/examples/dry_run_payload.json`

If using self-signed certs, add the appropriate trust configuration for your shell/environment.
