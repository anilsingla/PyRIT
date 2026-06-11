# RedTeam Ollama API Services Guide (All Environments)

This single guide explains how to run the API as a background service on:
- Windows (NSSM)
- Linux (systemd)
- macOS (launchd)

Service files live in:
- `scripts/installers/app_service/windows/`
- `scripts/installers/app_service/linux/`
- `scripts/installers/app_service/macos/`

## Quick Start (choose your OS)

Use this if you want a service quickly.

### Linux (systemd)
```bash
sudo cp scripts/installers/app_service/linux/pyrit-redteam-api.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable pyrit-redteam-api
sudo systemctl start pyrit-redteam-api
```

### macOS (launchd)
```bash
cp scripts/installers/app_service/macos/com.pyrit.redteam.api.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.pyrit.redteam.api.plist
launchctl start com.pyrit.redteam.api
```

### Windows (NSSM, Administrator PowerShell)
```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\installers\app_service\windows\install_service.ps1 -WorkingDirectory "C:\githubrepos\PyRIT\samples\security-evaluator"
```

Then verify:
```bash
curl http://localhost:8088/health
```

## 1) Common prerequisites

Before installing any service:

1. API runs manually from `samples/security-evaluator/`:
   ```bash
   python -m api.run_api
   ```
2. Python environment is prepared and has required packages.
3. Redteam utility dependencies/config are present in the same runtime environment.
4. Decide host/port and optional HTTPS cert paths.

Recommended quick verification:
```bash
curl http://localhost:8088/health
```

## 2) Common runtime environment variables

Service wrappers should pass these variables:
- `API_HOST` (default `127.0.0.1`)
- `API_PORT` (default `8088`)
- `API_ALLOW_REMOTE_HOST` (`false` by default; set `true` only when intentionally exposing API remotely)
- `API_AUTH_ENABLED` (`false` by default; set `true` to require bearer token auth for `/api/v1/*`)
- `API_BEARER_TOKEN` (required only when `API_AUTH_ENABLED=true`)
- `API_RELOAD` (`false` for services)
- `API_SSL_CERTFILE` (optional)
- `API_SSL_KEYFILE` (optional)

## 3) Linux service (systemd)

Service template:
- `scripts/installers/app_service/linux/pyrit-redteam-api.service`

### Install

```bash
sudo cp scripts/installers/app_service/linux/pyrit-redteam-api.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable pyrit-redteam-api
sudo systemctl start pyrit-redteam-api
sudo systemctl status pyrit-redteam-api
```

### Important edits before enable/start

Open `/etc/systemd/system/pyrit-redteam-api.service` and update:
- `WorkingDirectory` to your actual `samples/security-evaluator` path
- `ExecStart` to the exact Python executable you want
- Add TLS env vars if using HTTPS

Example additional env lines:
```ini
Environment=API_SSL_CERTFILE=/opt/certs/fullchain.pem
Environment=API_SSL_KEYFILE=/opt/certs/privkey.pem
```

### Operations

```bash
sudo systemctl restart pyrit-redteam-api
sudo systemctl stop pyrit-redteam-api
sudo systemctl disable pyrit-redteam-api
journalctl -u pyrit-redteam-api -f
```

### Uninstall

```bash
sudo systemctl stop pyrit-redteam-api
sudo systemctl disable pyrit-redteam-api
sudo rm /etc/systemd/system/pyrit-redteam-api.service
sudo systemctl daemon-reload
```

## 4) macOS service (launchd)

LaunchAgent template:
- `scripts/installers/app_service/macos/com.pyrit.redteam.api.plist`

### Install

```bash
cp scripts/installers/app_service/macos/com.pyrit.redteam.api.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.pyrit.redteam.api.plist
launchctl start com.pyrit.redteam.api
launchctl list | grep com.pyrit.redteam.api
```

### Important edits before load

Edit plist and update:
- `ProgramArguments[0]` Python executable path
- `WorkingDirectory`
- `EnvironmentVariables`
- Optional TLS variables (`API_SSL_CERTFILE`, `API_SSL_KEYFILE`)

### Operations

```bash
launchctl stop com.pyrit.redteam.api
launchctl start com.pyrit.redteam.api
launchctl unload ~/Library/LaunchAgents/com.pyrit.redteam.api.plist
```

Logs configured in template:
- `/tmp/pyrit-redteam-api.out.log`
- `/tmp/pyrit-redteam-api.err.log`

### Uninstall

```bash
launchctl unload ~/Library/LaunchAgents/com.pyrit.redteam.api.plist
rm ~/Library/LaunchAgents/com.pyrit.redteam.api.plist
```

## 5) Windows service (NSSM)

Scripts:
- `scripts/installers/app_service/windows/install_service.ps1`
- `scripts/installers/app_service/windows/uninstall_service.ps1`

### Prerequisite

Install NSSM and ensure `nssm.exe` is on PATH, or pass `-NssmPath`.

### Install (Run PowerShell as Administrator)

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\installers\app_service\windows\install_service.ps1 -WorkingDirectory "C:\githubrepos\PyRIT\samples\security-evaluator"
Get-Service PyRITRedTeamAPI
```

Optional parameters:
- `-ServiceName`
- `-DisplayName`
- `-Description`
- `-PythonExe`
- `-Host`
- `-Port`
- `-NssmPath`

### Add HTTPS vars on Windows service

After install, set environment via NSSM:

```powershell
nssm set PyRITRedTeamAPI AppEnvironmentExtra "API_HOST=127.0.0.1`nAPI_PORT=8088`nAPI_ALLOW_REMOTE_HOST=false`nAPI_AUTH_ENABLED=true`nAPI_BEARER_TOKEN=replace-with-strong-random-value`nAPI_RELOAD=false`nAPI_SSL_CERTFILE=C:\certs\cert.pem`nAPI_SSL_KEYFILE=C:\certs\key.pem"
Restart-Service PyRITRedTeamAPI
```

### Operations

```powershell
Get-Service PyRITRedTeamAPI
Restart-Service PyRITRedTeamAPI
Stop-Service PyRITRedTeamAPI
Start-Service PyRITRedTeamAPI
```

### Uninstall

```powershell
.\scripts\installers\app_service\windows\uninstall_service.ps1
```

## 6) Service verification checklist

After deployment on any OS:

1. Service reports running/healthy.
2. Health endpoint responds:
   - `http://<host>:<port>/health`
3. Option endpoint responds:
   - `http://<host>:<port>/api/v1/options`
4. Dry-run job starts and returns a `job_id`.

## 7) Troubleshooting

- Service starts then exits
  - Wrong `WorkingDirectory` or Python path.
  - Missing dependencies in that Python environment.

- Port already in use
  - Change `API_PORT` in service environment.

- HTTPS not working
  - Validate cert/key path permissions and file pair.

- Jobs fail while service is healthy
  - Validate redteam runtime configuration and model backend availability.

## 8) Related docs

- API setup: `api/API_SETUP_GUIDE.md`
- API quick reference: `api/README.md`
- API clients: `api/examples/README.md`
