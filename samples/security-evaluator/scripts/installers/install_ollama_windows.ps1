#Requires -Version 5.1
$ErrorActionPreference = 'Stop'

<#
=============================================================================
install_ollama_windows.ps1 -- Standalone Ollama installer for Windows
=============================================================================
Can be run directly OR dot-sourced by the main installer.

Usage:
    powershell -ExecutionPolicy Bypass -File .\samples\security-evaluator\scripts\installers\install_ollama_windows.ps1

Optional environment variables:
  OLLAMA_MODELS   -- comma- or space-separated models to pull (default: none)
  SKIP_PULL       -- set to "true" to skip model pull (default: false)
  OLLAMA_ENDPOINT -- endpoint to verify (default: http://localhost:11434)
=============================================================================
#>

$LibDir = Join-Path $PSScriptRoot "common"
. (Join-Path $LibDir "lib_common.ps1")

$OllamaModels    = if ($env:OLLAMA_MODELS)   { $env:OLLAMA_MODELS }   else { "" }
$SkipPull        = if ($env:SKIP_PULL)       { $env:SKIP_PULL }       else { "false" }
$OllamaEndpoint  = if ($env:OLLAMA_ENDPOINT) { $env:OLLAMA_ENDPOINT } else { "http://localhost:11434" }

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
        default { throw "No supported package manager found (winget/choco/scoop). Install Ollama manually from https://ollama.com/download" }
    }

    if (Test-CommandExists "ollama") {
        $ver = (& ollama --version 2>$null) | Select-Object -First 1
        Write-Ok "Ollama installed: $ver"
    } else {
        Write-Warn "Ollama may not be on PATH yet. Open a new terminal after install."
    }
}

function Invoke-PullOllamaModels {
    if ($SkipPull.ToLower() -eq "true") {
        Write-Info "Skipping model pull (SKIP_PULL=true)."
        return
    }

    if ([string]::IsNullOrWhiteSpace($OllamaModels)) {
        Write-Info "No OLLAMA_MODELS specified. Skipping model pull."
        Write-Info "Set `$env:OLLAMA_MODELS='llama3.2 mistral phi3' to pull automatically."
        return
    }

    Write-Header "Pulling Ollama models"
    $models = $OllamaModels -split '[\s,]+' | Where-Object { $_ -ne "" }
    foreach ($model in $models) {
        Write-Info "Pulling: $model"
        & ollama pull $model
        Write-Ok "Pulled: $model"
    }
}

function Test-OllamaEndpoint {
    Write-Header "Verifying Ollama endpoint"
    try {
        $resp = Invoke-WebRequest -Uri "$OllamaEndpoint/api/tags" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
        if ($resp.StatusCode -eq 200) {
            Write-Ok "Ollama is reachable at $OllamaEndpoint"
        }
    } catch {
        Write-Warn "Ollama endpoint not reachable at $OllamaEndpoint"
        Write-Info "Start Ollama: launch the Ollama app or run 'ollama serve' in a terminal."
    }
}

Write-Header "Ollama installer (Windows)"
Install-OllamaWindows
Invoke-PullOllamaModels
Test-OllamaEndpoint

Write-Header "Done"
Write-Ok "Ollama installation complete."
Write-Info "Start Ollama: launch the Ollama app or run 'ollama serve'."
Write-Info "Verify: Invoke-WebRequest http://localhost:11434/api/tags"

