# Deploy repetitor (@repetitors_ai_bot) from C:\Users\DavidPC\Projects
# Usage:
#   cd C:\Users\DavidPC\Projects\ai-agency\language-tutor
#   .\scripts\deploy-from-projects.ps1
# Or from standalone opus5:
#   cd C:\Users\DavidPC\Projects\opus5
#   .\scripts\deploy-from-projects.ps1   # if script copied, or run deploy-to-oracle.ps1 directly

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$LtuDir = Split-Path -Parent $ScriptDir

Write-Host "Projects deploy -> Oracle 140.84.183.154 (/opt/opus5) @repetitors_ai_bot" -ForegroundColor Cyan

& (Join-Path $ScriptDir "sync-secrets.ps1")

$deployScript = Join-Path $LtuDir "deploy-to-oracle.ps1"
if (-not (Test-Path $deployScript)) {
    Write-Host "deploy-to-oracle.ps1 not found in $LtuDir" -ForegroundColor Red
    exit 1
}

& $deployScript -KeyPath "C:\Users\DavidPC\.ssh\oracle_key"
