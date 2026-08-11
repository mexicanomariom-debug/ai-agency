# Deploy ai-ege-tutor-bot (@repetitors_ai_bot) from C:\Users\DavidPC\Projects to Oracle
# Usage:
#   cd C:\Users\DavidPC\Projects\ai-agency
#   .\scripts\deploy-ai-ege-tutor-oracle.ps1

param(
    [string]$ProjectPath = "",
    [string]$TargetHost = "140.84.183.154",
    [string]$User = "ubuntu",
    [string]$RemoteDir = "/opt/opus5",
    [string]$KeyPath = "C:\Users\DavidPC\.ssh\oracle_key"
)

$ErrorActionPreference = "Stop"

function Find-ProjectRoot {
    param([string]$Hint)
    if ($Hint -and (Test-Path $Hint)) {
        return (Resolve-Path $Hint).Path
    }
    $candidates = @(
        "$env:USERPROFILE\Projects\ai-ege-tutor-bot 2\ai-ege-tutor-bot",
        "$env:USERPROFILE\Projects\ai-ege-tutor-bot\ai-ege-tutor-bot",
        "$env:USERPROFILE\Projects\ai-ege-tutor-bot",
        "$env:USERPROFILE\Projects\ai-ege-tutor-bot 2"
    )
    foreach ($path in $candidates) {
        if (Test-Path $path) {
            return (Resolve-Path $path).Path
        }
    }
    return $null
}

function Find-OracleKey {
    param([string]$KeyHint)
    $candidates = @(
        $KeyHint,
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

$root = Find-ProjectRoot -Hint $ProjectPath
if (-not $root) {
    Write-Host "ai-ege-tutor-bot not found. Expected:" -ForegroundColor Red
    Write-Host "  C:\Users\DavidPC\Projects\ai-ege-tutor-bot 2\ai-ege-tutor-bot" -ForegroundColor Yellow
    exit 1
}

$key = Find-OracleKey -KeyHint $KeyPath
if (-not $key) {
    Write-Host "SSH key not found. Use -KeyPath" -ForegroundColor Red
    exit 1
}

Write-Host "Project:  $root" -ForegroundColor Cyan
Write-Host "Server:   ${User}@${TargetHost}:$RemoteDir" -ForegroundColor Cyan
Write-Host "Bot:      @repetitors_ai_bot" -ForegroundColor Cyan
Write-Host "SSH key:  $key" -ForegroundColor DarkGray

$Archive = Join-Path $env:TEMP "ai-ege-tutor-deploy.tar.gz"
if (Test-Path $Archive) { Remove-Item $Archive -Force }

Push-Location $root
& tar -czf $Archive `
    --exclude=node_modules `
    --exclude=.next `
    --exclude=__pycache__ `
    --exclude=.venv `
    --exclude=.git `
    .
Pop-Location

$sizeMb = [math]::Round((Get-Item $Archive).Length / 1MB, 1)
Write-Host "Archive: $sizeMb MB" -ForegroundColor DarkGray

$sshArgs = @("-i", $key, "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes")
$scpArgs = @("-i", $key, "-o", "StrictHostKeyChecking=no")
$server = "${User}@${TargetHost}"

& ssh @sshArgs $server "sudo mkdir -p $RemoteDir && sudo chown -R `$(whoami):`$(whoami) $RemoteDir"
& scp @scpArgs $Archive "${server}:/tmp/ai-ege-tutor-deploy.tar.gz"

$envFile = Join-Path $root ".env.production"
if (-not (Test-Path $envFile)) { $envFile = Join-Path $root ".env" }
if (-not (Test-Path $envFile)) {
    Write-Host "WARN: no .env in project — create .env with BOT_TOKEN for @repetitors_ai_bot" -ForegroundColor Yellow
} else {
    & scp @scpArgs $envFile "${server}:${RemoteDir}/.env"
}

$remoteCmd = @"
cd $RemoteDir
tar -xzf /tmp/ai-ege-tutor-deploy.tar.gz
rm -f /tmp/ai-ege-tutor-deploy.tar.gz
if [ -f oracle-redeploy.sh ]; then
  chmod +x oracle-redeploy.sh oracle-setup.sh 2>/dev/null || true
  ./oracle-redeploy.sh
elif [ -f docker-compose.prod.yml ]; then
  sudo docker compose -f docker-compose.prod.yml up -d --build
elif [ -f docker-compose.yml ]; then
  sudo docker compose up -d --build
else
  echo 'No oracle-redeploy.sh or docker-compose — check project structure'
  exit 1
fi
"@

& ssh @sshArgs $server $remoteCmd
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host ""
Write-Host "Deploy complete!" -ForegroundColor Green
Write-Host "  API:  http://${TargetHost}:8000/health"
Write-Host "  Bot:  https://t.me/repetitors_ai_bot"
