# Deploy Opus 5 to Oracle from Windows PowerShell 5.1+
# Usage:
#   cd C:\Users\DavidPC\Projects\ai-agency\language-tutor
#   .\deploy-to-oracle.ps1
#   .\deploy-to-oracle.ps1 -Server "ubuntu@140.84.183.154" -KeyPath "C:\Users\DavidPC\.ssh\oracle_key"

param(
    [string]$Server = "ubuntu@140.84.183.154",
    [string]$RemoteDir = "/opt/opus5",
    [string]$KeyPath = ""
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "-> Deploying to ${Server}:${RemoteDir}" -ForegroundColor Cyan

$sshArgs = @()
$scpArgs = @()
if ($KeyPath -ne "") {
    if (-not (Test-Path $KeyPath)) {
        throw "SSH key not found: $KeyPath"
    }
    $sshArgs = @("-i", $KeyPath)
    $scpArgs = @("-i", $KeyPath)
}

# Create remote directory (use ';' not '&&' - bash on remote server)
$mkdirCmd = "sudo mkdir -p $RemoteDir; sudo chown -R `$(whoami):`$(whoami) $RemoteDir"
& ssh @sshArgs $Server $mkdirCmd
if ($LASTEXITCODE -ne 0) { throw "SSH mkdir failed with exit code $LASTEXITCODE" }

# Copy project files (exclude heavy folders)
$exclude = @("node_modules", ".next", "__pycache__", ".venv", ".git")
$items = Get-ChildItem -Path $ScriptDir -Force | Where-Object {
    $_.Name -notin $exclude
}

foreach ($item in $items) {
    Write-Host "   copying $($item.Name)..." -ForegroundColor DarkGray
    & scp @scpArgs -r $item.FullName "${Server}:${RemoteDir}/"
    if ($LASTEXITCODE -ne 0) { throw "SCP failed for $($item.Name)" }
}

# Copy .env
$envFile = Join-Path $ScriptDir ".env.production"
if (-not (Test-Path $envFile)) {
    $envFile = Join-Path $ScriptDir ".env"
}
if (Test-Path $envFile) {
    & scp @scpArgs $envFile "${Server}:${RemoteDir}/.env"
    if ($LASTEXITCODE -ne 0) { throw "SCP failed for .env" }
    Write-Host "   .env copied" -ForegroundColor DarkGray
} else {
    Write-Warning "No .env or .env.production found - create on server manually"
}

Write-Host "-> Running setup on server..." -ForegroundColor Cyan
$setupCmd = "chmod +x $RemoteDir/oracle-setup.sh; cd $RemoteDir; ./oracle-setup.sh"
& ssh @sshArgs $Server $setupCmd
if ($LASTEXITCODE -ne 0) { throw "Remote setup failed with exit code $LASTEXITCODE" }

Write-Host ""
Write-Host "Deploy complete!" -ForegroundColor Green
Write-Host "   Web App: https://webapp-bay-three-75.vercel.app/app"
Write-Host "   Bot:     https://t.me/All_languages_bot"
