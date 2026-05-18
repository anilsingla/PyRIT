# Service Files (Optional)

This folder contains optional service wrappers for hosting the security-evaluator API in the background.

New to this sample? Start with [START_HERE.md](../../../../START_HERE.md) for a simple step-by-step path from first run to advanced modes.

## Full services guide (single file for all environments)

- See [SERVICES_GUIDE.md](SERVICES_GUIDE.md) for Windows, Linux, and macOS step-by-step service setup and operations.
- For a guided dependency, config, and service-wrapper setup flow, use [../install_security-evaluator.py](../install_security-evaluator.py).

## Linux (systemd)

File: `scripts/installers/app_service/linux/pyrit-redteam-api.service`

### Install

```bash
sudo cp scripts/installers/app_service/linux/pyrit-redteam-api.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable pyrit-redteam-api
sudo systemctl start pyrit-redteam-api
sudo systemctl status pyrit-redteam-api
```

Update `WorkingDirectory` and Python path in the service file before enabling.

## macOS (launchd)

File: `scripts/installers/app_service/macos/com.pyrit.redteam.api.plist`

### Install

```bash
cp scripts/installers/app_service/macos/com.pyrit.redteam.api.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.pyrit.redteam.api.plist
launchctl start com.pyrit.redteam.api
launchctl list | grep com.pyrit.redteam.api
```

Update `WorkingDirectory` and Python path before loading.

## Windows (NSSM)

Files:
- `scripts/installers/app_service/windows/install_service.ps1`
- `scripts/installers/app_service/windows/uninstall_service.ps1`

### Install

```powershell
# Run PowerShell as Administrator
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\installers\app_service\windows\install_service.ps1 -WorkingDirectory "C:\githubrepos\PyRIT\samples\security-evaluator"
Get-Service PyRITRedTeamAPI
```

### Uninstall

```powershell
.\scripts\installers\app_service\windows\uninstall_service.ps1
```

NSSM is required for Windows service hosting of this Python app.

