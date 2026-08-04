# Deploy Opus 5 to Oracle from Windows PowerShell 5.1+
# Usage:
#   .\deploy-to-oracle.ps1
#   .\deploy-to-oracle.ps1 -KeyPath "C:\Users\DavidPC\Downloads\ssh-key-2024-01-01.key"
#   .\deploy-to-oracle.ps1 -Server "opc@140.84.183.154" -KeyPath "C:\path\to\key.pem"

param(
    [string]$Host = "140.84.183.154",
    [string]$User = "ubuntu",
    [string]$RemoteDir = "/opt/opus5",
    [string]$KeyPath = ""
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

function Find-OracleKey {
    $candidates = @(
        $KeyPath,
        "$env:USERPROFILE\.ssh\oracle_key",
        "$env:USERPROFILE\.ssh\oracle_key.pem",
        "$env:USERPROFILE\.ssh\id_rsa",
        "$env:USERPROFILE\.ssh\id_ed25519"
    )
    $downloads = Get-ChildItem "$env:USERPROFILE\Downloads\*.pem" -ErrorAction SilentlyContinue
    foreach ($f in $downloads) { $candidates += $f.FullName }
    $sshDir = Get-ChildItem "$env:USERPROFILE\.ssh\*.pem" -ErrorAction SilentlyContinue
    foreach ($f in $sshDir) { $candidates += $f.FullName }

    foreach ($path in $candidates) {
        if ($path -and (Test-Path $path)) { return $path }
    }
    return $null
}

function Invoke-RemoteDeploy {
    param(
        [string]$Server,
        [string[]]$SshArgs,
        [string[]]$ScpArgs
    )

    Write-Host "-> Deploying to ${Server}:${RemoteDir}" -ForegroundColor Cyan

    $mkdirCmd = "sudo mkdir -p $RemoteDir; sudo chown -R `$(whoami):`$(whoami) $RemoteDir"
    & ssh @SshArgs $Server $mkdirCmd
    if ($LASTEXITCODE -ne 0) { return $false }

    $exclude = @("node_modules", ".next", "__pycache__", ".venv", ".git")
    $items = Get-ChildItem -Path $ScriptDir -Force | Where-Object { $_.Name -notin $exclude }

    foreach ($item in $items) {
        Write-Host "   copying $($item.Name)..." -ForegroundColor DarkGray
        & scp @ScpArgs -r $item.FullName "${Server}:${RemoteDir}/"
        if ($LASTEXITCODE -ne 0) { return $false }
    }

    $envFile = Join-Path $ScriptDir ".env.production"
    if (-not (Test-Path $envFile)) { $envFile = Join-Path $ScriptDir ".env" }
    if (Test-Path $envFile) {
        & scp @ScpArgs $envFile "${Server}:${RemoteDir}/.env"
        if ($LASTEXITCODE -ne 0) { return $false }
        Write-Host "   .env copied" -ForegroundColor DarkGray
    } else {
        Write-Warning "No .env or .env.production found - create on server manually"
    }

    Write-Host "-> Running setup on server..." -ForegroundColor Cyan
    $setupCmd = "chmod +x $RemoteDir/oracle-setup.sh; cd $RemoteDir; ./oracle-setup.sh"
    & ssh @SshArgs $Server $setupCmd
    return ($LASTEXITCODE -eq 0)
}

# Resolve SSH key
$key = Find-OracleKey
if (-not $key) {
    Write-Host ""
    Write-Host "SSH key not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Oracle Cloud gives you a .pem file when you create the VM."
    Write-Host "Find it (usually in Downloads) and run:"
    Write-Host ""
    Write-Host '  .\deploy-to-oracle.ps1 -KeyPath "C:\Users\DavidPC\Downloads\YOUR-KEY.pem"' -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Or test SSH manually:"
    Write-Host '  ssh -i "C:\path\to\key.pem" ubuntu@140.84.183.154' -ForegroundColor Yellow
    Write-Host '  ssh -i "C:\path\to\key.pem" opc@140.84.183.154' -ForegroundColor Yellow
    exit 1
}

Write-Host "Using SSH key: $key" -ForegroundColor DarkGray
$sshArgs = @("-i", $key, "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes")
$scpArgs = @("-i", $key, "-o", "StrictHostKeyChecking=no")

$users = @($User)
if ($User -eq "ubuntu") { $users += "opc" }

foreach ($u in $users) {
    $server = "${u}@${Host}"
    Write-Host ""
    Write-Host "Trying $server ..." -ForegroundColor Cyan
    if (Invoke-RemoteDeploy -Server $server -SshArgs $sshArgs -ScpArgs $scpArgs) {
        Write-Host ""
        Write-Host "Deploy complete!" -ForegroundColor Green
        Write-Host "   Web App: https://webapp-bay-three-75.vercel.app/app"
        Write-Host "   Bot:     https://t.me/All_languages_bot"
        exit 0
    }
    Write-Host "Failed for $server" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "SSH failed for all users. Permission denied (publickey)." -ForegroundColor Red
Write-Host ""
Write-Host "1. Find your Oracle .pem key (Downloads folder or Oracle Cloud console)"
Write-Host "2. Run with explicit path:"
Write-Host '   .\deploy-to-oracle.ps1 -KeyPath "C:\Users\DavidPC\Downloads\YOUR-KEY.pem"' -ForegroundColor Yellow
Write-Host "3. If key is correct but user is opc:"
Write-Host '   .\deploy-to-oracle.ps1 -User opc -KeyPath "C:\path\to\key.pem"' -ForegroundColor Yellow
exit 1
