param(
    [string]$BaseUrl = "http://localhost:8088",
    [string]$PayloadPath = ".\api\examples\dry_run_payload.json",
    [int]$TailLines = 200,
    [int]$PollSeconds = 2,
    [int]$MaxPolls = 90
)

$ErrorActionPreference = "Stop"

Write-Host "== Health check =="
$health = Invoke-RestMethod -Method Get -Uri "$BaseUrl/health"
$health | ConvertTo-Json -Depth 5

Write-Host "`n== Supported options =="
$options = Invoke-RestMethod -Method Get -Uri "$BaseUrl/api/v1/options"
$options | ConvertTo-Json -Depth 5

if (-not (Test-Path $PayloadPath)) {
    throw "Payload file not found: $PayloadPath"
}

Write-Host "`n== Start dry run =="
$payload = Get-Content $PayloadPath -Raw
$start = Invoke-RestMethod -Method Post -Uri "$BaseUrl/api/v1/runs/dry-run" -ContentType "application/json" -Body $payload
$start | ConvertTo-Json -Depth 5

$jobId = $start.job_id
if (-not $jobId) {
    throw "API did not return job_id"
}

Write-Host "`n== Poll status ($jobId) =="
$status = $null
for ($i = 1; $i -le $MaxPolls; $i++) {
    $status = Invoke-RestMethod -Method Get -Uri "$BaseUrl/api/v1/runs/$jobId"
    Write-Host "Poll #$i status=$($status.status)"

    if ($status.status -in @("completed", "failed", "cancelled")) {
        break
    }
    Start-Sleep -Seconds $PollSeconds
}

if ($null -eq $status) {
    throw "Unable to fetch job status"
}

Write-Host "`n== Final status =="
$status | ConvertTo-Json -Depth 6

Write-Host "`n== Output tail =="
$output = Invoke-RestMethod -Method Get -Uri "$BaseUrl/api/v1/runs/$jobId/output?tail_lines=$TailLines"
$output.output
