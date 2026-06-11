param(
    [string]$ServiceName = "PyRITRedTeamAPI",
    [string]$NssmPath = "nssm"
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command $NssmPath -ErrorAction SilentlyContinue)) {
    throw "nssm executable not found. Install NSSM and pass -NssmPath if needed."
}

try {
    & $NssmPath stop $ServiceName
} catch {
    Write-Host "Service may already be stopped: $ServiceName"
}

& $NssmPath remove $ServiceName confirm
Write-Host "Service removed: $ServiceName"
