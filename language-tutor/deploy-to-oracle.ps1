# Fast deploy to Oracle via tar archive (PowerShell 5.1+)
# Usage:
#   .\deploy-to-oracle.ps1 -KeyPath "C:\Users\DavidPC\.ssh\oracle_key"

param(
    [string]$TargetHost = "140.84.183.154",
    [string]$User = "ubuntu",
    [string]$RemoteDir = "/opt/opus5",
    [string]$KeyPath = ""
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Archive = Join-Path $env:TEMP "opus5-deploy.tar.gz"

function Find-OracleKey {
    $candidates = @(
        $KeyPath,
        "$env:USERPROFILE\.ssh\oracle_key",
        "$env:USERPROFILE\.ssh\oracle_key.pem",
        "$env:USERPROFILE\.ssh\id_rsa"
    )
    Get-ChildItem "$env:USERPROFILE\Downloads\*.pem" -ErrorAction SilentlyContinue | ForEach-Object { $candidates += $_.FullName }
    Get-ChildItem "$env:USERPROFILE\.ssh\*.pem" -ErrorAction SilentlyContinue | ForEach-Object { $candidates += $_.FullName }
    foreach ($path in $candidates) {
        if ($path -and (Test-Path $path)) { return $path }
    }
    return $null
}

function Invoke-Deploy {
    param([string]$Server, [string[]]$SshArgs, [string[]]$ScpArgs)

    Write-Host "-> Building archive..." -ForegroundColor Cyan
    if (Test-Path $Archive) { Remove-Item $Archive -Force }

    Push-Location $ScriptDir
    & tar -czf $Archive `
        --exclude=node_modules `
        --exclude=.next `
        --exclude=__pycache__ `
        --exclude=.venv `
        --exclude=.git `
        .
    Pop-Location

    $sizeMb = [math]::Round((Get-Item $Archive).Length / 1MB, 1)
    Write-Host "   Archive: $sizeMb MB" -ForegroundColor DarkGray

    $mkdirCmd = "sudo mkdir -p $RemoteDir; sudo chown -R `$(whoami):`$(whoami) $RemoteDir"
    & ssh @SshArgs $Server $mkdirCmd
    if ($LASTEXITCODE -ne 0) { return $false }

    Write-Host "-> Uploading..." -ForegroundColor Cyan
    & scp @ScpArgs $Archive "${Server}:/tmp/opus5-deploy.tar.gz"
    if ($LASTEXITCODE -ne 0) { return $false }

    $envFile = Join-Path $ScriptDir ".env.production"
    if (-not (Test-Path $envFile)) { $envFile = Join-Path $ScriptDir ".env" }
    if (Test-Path $envFile) {
        & scp @ScpArgs $envFile "${Server}:${RemoteDir}/.env"
        if ($LASTEXITCODE -ne 0) { return $false }
    }

    Write-Host "-> Clean redeploy on server..." -ForegroundColor Cyan
    $remoteCmd = "cd $RemoteDir; tar -xzf /tmp/opus5-deploy.tar.gz; rm -f /tmp/opus5-deploy.tar.gz; chmod +x oracle-redeploy.sh oracle-setup.sh; ./oracle-redeploy.sh"
    & ssh @SshArgs $Server $remoteCmd
    return ($LASTEXITCODE -eq 0)
}

$key = Find-OracleKey
if (-not $key) {
    Write-Host "SSH key not found. Run:" -ForegroundColor Red
    Write-Host '  .\deploy-to-oracle.ps1 -KeyPath "C:\Users\DavidPC\.ssh\oracle_key"' -ForegroundColor Yellow
    exit 1
}

Write-Host "Using SSH key: $key" -ForegroundColor DarkGray
$sshArgs = @("-i", $key, "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes")
$scpArgs = @("-i", $key, "-o", "StrictHostKeyChecking=no")

$users = @($User)
if ($User -eq "ubuntu") { $users += "opc" }

foreach ($u in $users) {
    $server = "${u}@${TargetHost}"
    Write-Host ""
    Write-Host "Trying $server ..." -ForegroundColor Cyan
    if (Invoke-Deploy -Server $server -SshArgs $sshArgs -ScpArgs $scpArgs) {
        Write-Host ""
        Write-Host "Deploy complete!" -ForegroundColor Green
        Write-Host "   API:     http://140.84.183.154:8000/health"
        Write-Host "   Web App: https://webapp-bay-three-75.vercel.app/app"
        Write-Host "   Bot:     https://t.me/repetitors_ai_bot"
        exit 0
    }
}

Write-Host "Deploy failed. Check SSH key and server access." -ForegroundColor Red
exit 1
