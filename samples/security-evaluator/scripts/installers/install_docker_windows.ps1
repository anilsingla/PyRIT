#Requires -Version 5.1
$ErrorActionPreference = 'Stop'

<#
=============================================================================
install_docker_windows.ps1 -- Standalone Docker Desktop installer for Windows
=============================================================================
Can be run directly OR dot-sourced by the main installer.

Usage:
    powershell -ExecutionPolicy Bypass -File .\samples\security-evaluator\scripts\installers\install_docker_windows.ps1

Optional environment variables:
  START_COMPOSE   -- "true" to run docker compose up -d after install (default: false)
  COMPOSE_FILE    -- path to docker-compose.yaml (default: auto-detected)
=============================================================================
#>

$LibDir = Join-Path $PSScriptRoot "common"
. (Join-Path $LibDir "lib_common.ps1")

$StartCompose = if ($env:START_COMPOSE) { $env:START_COMPOSE } else { "false" }
$ComposeFile  = if ($env:COMPOSE_FILE)  { $env:COMPOSE_FILE }  else { "" }

function Install-DockerWindows {
    if (Test-CommandExists "docker") {
        $ver = (& docker --version) 2>$null
        Write-Ok "Docker already installed: $ver"
        return
    }

    Write-Header "Installing Docker Desktop"
    $mgr = Get-WindowsPackageManager

    switch ($mgr) {
        "winget" {
            Write-Info "Using winget"
            winget install --id Docker.DockerDesktop --exact --silent --accept-source-agreements --accept-package-agreements
        }
        "choco" {
            Write-Info "Using Chocolatey"
            choco install docker-desktop -y
        }
        "scoop" {
            Write-Info "Using Scoop"
            scoop install docker
        }
        default { throw "No supported package manager found. Install Docker Desktop manually: https://www.docker.com/products/docker-desktop/" }
    }

    if (Test-CommandExists "docker") {
        $ver = (& docker --version) 2>$null
        Write-Ok "Docker installed: $ver"
    } else {
        Write-Warn "Docker may not be on PATH yet. Launch Docker Desktop and open a new terminal."
    }
}

function Test-DockerDaemon {
    Write-Header "Verifying Docker daemon"
    if (-not (Test-CommandExists "docker")) {
        Write-Warn "docker command not found after install."
        return
    }

    try {
        $null = & docker info 2>$null
        Write-Ok "Docker daemon is running."
    } catch {
        Write-Warn "Docker installed but daemon is not running."
        Write-Info "Launch Docker Desktop to start the daemon."
    }
}

function Start-ComposeStack {
    if ($StartCompose.ToLower() -ne "true") { return }

    if ([string]::IsNullOrWhiteSpace($ComposeFile)) {
        # Auto-locate: climb up 4 levels from this script to repo root, then docker/
        $repoRoot = (Get-Item $PSScriptRoot).Parent.Parent.Parent.Parent.FullName
        $ComposeFile = Join-Path $repoRoot "docker\docker-compose.yaml"
    }

    if (-not (Test-Path $ComposeFile)) {
        Write-Warn "docker-compose file not found: $ComposeFile"
        Write-Info "Set `$env:COMPOSE_FILE and re-run."
        return
    }

    Write-Header "Starting Docker Compose stack"
    $composeDir = Split-Path $ComposeFile -Parent
    Push-Location $composeDir
    try {
        docker compose up -d
        Write-Ok "Docker Compose stack started."
    } finally {
        Pop-Location
    }
}

Write-Header "Docker installer (Windows)"
Install-DockerWindows
Test-DockerDaemon
Start-ComposeStack

Write-Header "Done"
Write-Ok "Docker installation complete."
Write-Info "Launch Docker Desktop to start the daemon if not already running."
Write-Info "Run 'docker compose up -d' from the docker/ directory to start services."

