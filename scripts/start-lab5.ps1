$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
foreach ($labPort in @(5015,5195)) {
    if (Get-NetTCPConnection -LocalPort $labPort -State Listen -ErrorAction SilentlyContinue) {
        throw "Lab port $labPort is already occupied. Existing services were not stopped."
    }
}
$labOutput = Join-Path $projectRoot 'output/lab5'
New-Item -ItemType Directory -Path $labOutput -Force | Out-Null
$env:LINK_BACKEND_URL = 'http://127.0.0.1:5015'
$env:VITE_ADAPTIVE_ENABLED = 'true'
Start-Process -FilePath (Get-Command python).Source -ArgumentList @('scripts/lab5.py','serve') -WorkingDirectory $projectRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $labOutput 'backend.log') -RedirectStandardError (Join-Path $labOutput 'backend-error.log')
Start-Process -FilePath (Get-Command node).Source -ArgumentList @('node_modules/vite/bin/vite.js','--host','127.0.0.1','--port','5195','--strictPort') -WorkingDirectory (Join-Path $projectRoot 'frontend') -WindowStyle Hidden -RedirectStandardOutput (Join-Path $labOutput 'frontend.log') -RedirectStandardError (Join-Path $labOutput 'frontend-error.log')
Write-Output 'Lab UI: http://127.0.0.1:5195/adaptive ; account: lab5_student ; password: Lab5-demo-2026'
