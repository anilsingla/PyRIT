param(
    [string]$ServiceName = "PyRITRedTeamAPI",
    [string]$DisplayName = "PyRIT Security Evaluator API",
    [string]$Description = "Runs the security-evaluator API service",
    [string]$PythonExe = "python",
    [string]$WorkingDirectory = "C:\githubrepos\PyRIT\samples\security-evaluator",
    [string]$Host = "127.0.0.1",
    [int]$Port = 8088,
    [string]$NssmPath = "nssm"
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command $NssmPath -ErrorAction SilentlyContinue)) {
    throw "nssm executable not found. Install NSSM and pass -NssmPath if needed."
}

$arguments = "-m api.run_api"

& $NssmPath install $ServiceName $PythonExe $arguments
& $NssmPath set $ServiceName AppDirectory $WorkingDirectory
& $NssmPath set $ServiceName AppEnvironmentExtra "API_HOST=$Host`nAPI_PORT=$Port`nAPI_RELOAD=false"
& $NssmPath set $ServiceName DisplayName $DisplayName
& $NssmPath set $ServiceName Description $Description
& $NssmPath set $ServiceName Start SERVICE_AUTO_START
& $NssmPath start $ServiceName

Write-Host "Service installed and started: $ServiceName"
