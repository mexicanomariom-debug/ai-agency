# Deploy ai-ege-tutor-bot (@repetitors_ai_bot) -> Oracle 140.84.183.154
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

function Say([string]$Msg, [string]$Color = "Cyan") {
    Write-Host $Msg -ForegroundColor $Color
}

function Find-ProjectRoot {
    param([string]$Hint)
    if ($Hint -and (Test-Path $Hint)) {
        return (Resolve-Path $Hint).Path
    }
    foreach ($path in @(
        "$env:USERPROFILE\Projects\ai-ege-tutor-bot 2\ai-ege-tutor-bot",
        "$env:USERPROFILE\Projects\ai-ege-tutor-bot\ai-ege-tutor-bot",
        "$env:USERPROFILE\Projects\ai-ege-tutor-bot",
        "$env:USERPROFILE\Projects\ai-ege-tutor-bot 2"
    )) {
        if (Test-Path $path) { return (Resolve-Path $path).Path }
    }
    return $null
}

function Find-OracleKey {
    param([string]$KeyHint)
    foreach ($path in @(
        $KeyHint,
        "$env:USERPROFILE\.ssh\oracle_key",
        "$env:USERPROFILE\.ssh\oracle_key.pem",
        "$env:USERPROFILE\.ssh\id_rsa"
    )) {
        if ($path -and (Test-Path $path)) { return $path }
    }
    Get-ChildItem "$env:USERPROFILE\Downloads\*.pem" -ErrorAction SilentlyContinue | ForEach-Object {
        if (Test-Path $_.FullName) { return $_.FullName }
    }
    return $null
}

function Require-Command([string]$Name) {
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        Say "ERROR: command not found: $Name (install OpenSSH Client in Windows)" "Red"
        exit 1
    }
}

Require-Command "ssh"
Require-Command "scp"
Require-Command "tar"

$root = Find-ProjectRoot -Hint $ProjectPath
if (-not $root) {
    Say "ERROR: ai-ege-tutor-bot not found" "Red"
    Say "  C:\Users\DavidPC\Projects\ai-ege-tutor-bot 2\ai-ege-tutor-bot" "Yellow"
    exit 1
}

$key = Find-OracleKey -KeyHint $KeyPath
if (-not $key) {
    Say "ERROR: SSH key not found. Use -KeyPath" "Red"
    exit 1
}

$envFile = Join-Path $root ".env.production"
if (-not (Test-Path $envFile)) { $envFile = Join-Path $root ".env" }
if (-not (Test-Path $envFile)) {
    Say "ERROR: no .env in project — create .env with BOT_TOKEN for @repetitors_ai_bot" "Red"
    exit 1
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$remoteHelper = Join-Path $scriptDir "oracle-redeploy-remote.sh"
if (-not (Test-Path $remoteHelper)) {
    Say "ERROR: missing oracle-redeploy-remote.sh next to this script" "Red"
    exit 1
}

Say "Project:  $root"
Say "Server:   ${User}@${TargetHost}:$RemoteDir"
Say "Bot:      @repetitors_ai_bot"
Say "SSH key:  $key" "DarkGray"

$server = "${User}@${TargetHost}"
$sshArgs = @("-i", $key, "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes")
$scpArgs = @("-i", $key, "-o", "StrictHostKeyChecking=no")

Say "[1/6] SSH test..."
& ssh @sshArgs $server "echo SSH_OK"
if ($LASTEXITCODE -ne 0) {
    Say "ERROR: SSH failed — check key and Oracle IP" "Red"
    exit 1
}

Say "[2/6] Building archive..."
$Archive = Join-Path $env:TEMP "ai-ege-tutor-deploy.tar.gz"
if (Test-Path $Archive) { Remove-Item $Archive -Force }
Push-Location $root
& tar -czf $Archive --exclude=node_modules --exclude=.next --exclude=__pycache__ --exclude=.venv --exclude=.git .
Pop-Location
$sizeMb = [math]::Round((Get-Item $Archive).Length / 1MB, 1)
Say "Archive: $sizeMb MB"

Say "[3/6] Upload archive..."
& scp @scpArgs $Archive "${server}:/tmp/ai-ege-tutor-deploy.tar.gz"
if ($LASTEXITCODE -ne 0) { Say "ERROR: scp archive failed" "Red"; exit 1 }

Say "[4/6] Upload .env..."
& scp @scpArgs $envFile "${server}:${RemoteDir}/.env"
if ($LASTEXITCODE -ne 0) {
    Say "Upload .env to $RemoteDir failed — creating dir..." "Yellow"
    & ssh @sshArgs $server "sudo mkdir -p $RemoteDir && sudo chown -R `$(whoami):`$(whoami) $RemoteDir"
    & scp @scpArgs $envFile "${server}:${RemoteDir}/.env"
    if ($LASTEXITCODE -ne 0) { Say "ERROR: scp .env failed" "Red"; exit 1 }
}

Say "[5/6] Upload redeploy helper..."
& scp @scpArgs $remoteHelper "${server}:/tmp/oracle-redeploy-remote.sh"
if ($LASTEXITCODE -ne 0) { Say "ERROR: scp helper failed" "Red"; exit 1 }

Say "[6/6] Redeploy on server..."
& ssh @sshArgs $server "chmod +x /tmp/oracle-redeploy-remote.sh && bash /tmp/oracle-redeploy-remote.sh $RemoteDir"
if ($LASTEXITCODE -ne 0) {
    Say "ERROR: remote redeploy failed — see output above" "Red"
    exit 1
}

Say ""
Say "Deploy complete!" "Green"
Say "  API:  http://${TargetHost}:8000/health"
Say "  Bot:  https://t.me/repetitors_ai_bot" "Green"
