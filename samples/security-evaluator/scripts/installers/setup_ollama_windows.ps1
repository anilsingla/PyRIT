#Requires -Version 5.1
$ErrorActionPreference = 'Stop'

<#
=============================================================================
setup_ollama_windows.ps1 -- Ollama install + setup helper for Windows
=============================================================================
Usage:
  powershell -ExecutionPolicy Bypass -File .\samples\security-evaluator\scripts\installers\setup_ollama_windows.ps1

Optional environment variables:
  OLLAMA_MODELS         comma/space-separated models (default: llama3.2 mistral phi3)
  SKIP_PULL             set to "true" to skip model pull (default: false)
  START_OLLAMA          set to "false" to skip process start check (default: true)
  TEST_MODEL            model for non-interactive test prompt (default: first from OLLAMA_MODELS)
  OLLAMA_ENDPOINT       endpoint to verify (default: http://localhost:11434)
  ENABLE_STARTUP_TASK   set to "true" to create startup scheduled task for ollama serve (default: false)
=============================================================================
#>

$LibDir = Join-Path $PSScriptRoot "common"
. (Join-Path $LibDir "lib_common.ps1")

$OllamaModels = if ($env:OLLAMA_MODELS) { $env:OLLAMA_MODELS } else { "llama3.2 mistral phi3" }
$SkipPull = if ($env:SKIP_PULL) { $env:SKIP_PULL } else { "false" }
$StartOllama = if ($env:START_OLLAMA) { $env:START_OLLAMA } else { "true" }
$TestModel = if ($env:TEST_MODEL) { $env:TEST_MODEL } else { "" }
$OllamaEndpoint = if ($env:OLLAMA_ENDPOINT) { $env:OLLAMA_ENDPOINT } else { "http://localhost:11434" }
$EnableStartupTask = if ($env:ENABLE_STARTUP_TASK) { $env:ENABLE_STARTUP_TASK } else { "false" }

function Install-OllamaWindows {
    if (Test-CommandExists "ollama") {
        $ver = (& ollama --version 2>$null) | Select-Object -First 1
        Write-Ok "Ollama already installed: $ver"
        return
    }

    Write-Header "Installing Ollama"
    $mgr = Get-WindowsPackageManager

    switch ($mgr) {
        "winget" {
            Write-Info "Using winget"
            winget install --id Ollama.Ollama --exact --silent --accept-source-agreements --accept-package-agreements
        }
        "choco" {
            Write-Info "Using Chocolatey"
            choco install ollama -y
        }
        "scoop" {
            Write-Info "Using Scoop"
            scoop install ollama
        }
        default { throw "No supported package manager found (winget/choco/scoop). Install manually: https://ollama.com/download" }
    }

    if (Test-CommandExists "ollama") {
        $ver = (& ollama --version 2>$null) | Select-Object -First 1
        Write-Ok "Ollama installed: $ver"
    } else {
        Write-Warn "Ollama may not be on PATH yet. Open a new terminal and rerun this script."
    }
}

function Test-OllamaEndpoint {
    try {
        $resp = Invoke-WebRequest -Uri "$OllamaEndpoint/api/tags" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
        return ($resp.StatusCode -eq 200)
    } catch {
        return $false
    }
}

function Start-OllamaIfNeeded {
    if ($StartOllama.ToLower() -ne "true") {
        Write-Info "Skipping start check (START_OLLAMA=false)."
        return
    }

    if (Test-OllamaEndpoint) {
        Write-Ok "Ollama endpoint already reachable at $OllamaEndpoint"
        return
    }

    Write-Header "Starting Ollama"
    Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden

    for ($i = 0; $i -lt 20; $i++) {
        Start-Sleep -Seconds 1
        if (Test-OllamaEndpoint) {
            Write-Ok "Ollama endpoint reachable at $OllamaEndpoint"
            return
        }
    }

    Write-Warn "Ollama endpoint is still not reachable at $OllamaEndpoint"
    Write-Info "Try launching Ollama desktop app or running 'ollama serve' in a dedicated terminal."
}

function Invoke-PullOllamaModels {
    if ($SkipPull.ToLower() -eq "true") {
        Write-Info "Skipping model pull (SKIP_PULL=true)."
        return
    }

    Write-Header "Pulling models"
    $models = $OllamaModels -split '[\s,]+' | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
    foreach ($model in $models) {
        Write-Info "Pulling: $model"
        & ollama pull $model
        Write-Ok "Pulled: $model"
    }

    Write-Info "Installed models:"
    & ollama list
}

function Invoke-TestModelRun {
    $model = $TestModel
    if ([string]::IsNullOrWhiteSpace($model)) {
        $model = (($OllamaModels -split '[\s,]+') | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -First 1)
    }

    if ([string]::IsNullOrWhiteSpace($model)) {
        Write-Info "No test model configured; skipping model run check."
        return
    }

    Write-Header "Running non-interactive model check"
    Write-Info "Testing model: $model"
    & ollama run $model "Reply with: OLLAMA_OK" | Select-Object -First 5 | ForEach-Object { Write-Host $_ }
}

function Register-OllamaStartupTask {
    if ($EnableStartupTask.ToLower() -ne "true") {
        return
    }

    Write-Header "Configuring startup task for Ollama"

    $taskName = "OllamaServeOnLogon"
    $action = New-ScheduledTaskAction -Execute "ollama" -Argument "serve"
    $trigger = New-ScheduledTaskTrigger -AtLogOn

    try {
        Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Description "Starts ollama serve at user logon" -Force | Out-Null
        Write-Ok "Scheduled task created: $taskName"
    } catch {
        Write-Warn "Could not create scheduled task. Run PowerShell as Administrator and try again."
    }
}

Write-Header "Ollama local setup (Windows)"
Install-OllamaWindows
Start-OllamaIfNeeded
Invoke-PullOllamaModels
Invoke-TestModelRun
Register-OllamaStartupTask

Write-Header "Done"
Write-Ok "Ollama install/setup flow completed."
Write-Info "Endpoint: $OllamaEndpoint"
Write-Info "Set in .env.local: OLLAMA_ENDPOINT=http://localhost:11434/v1"
Write-Info "Optional: set ENABLE_STARTUP_TASK=true to start ollama serve automatically on sign-in."
