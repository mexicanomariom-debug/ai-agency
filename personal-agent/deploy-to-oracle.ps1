param(
    [string]$Server = "ubuntu@140.84.183.154",
    [string]$KeyPath = ""
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Archive = Join-Path $env:TEMP "personal-agent-deploy.tar.gz"
$RemoteDir = "/opt/personal-agent"

if ($KeyPath -and (Test-Path $KeyPath)) {
    $env:GIT_SSH_COMMAND = "ssh -i `"$KeyPath`" -o StrictHostKeyChecking=no"
    $sshOpts = @("-i", $KeyPath, "-o", "StrictHostKeyChecking=no")
} else {
    $sshOpts = @("-o", "StrictHostKeyChecking=no")
}

Write-Host "-> Building archive..." -ForegroundColor Cyan
Push-Location $ScriptDir
tar -czf $Archive --exclude=__pycache__ --exclude=.venv --exclude=.git --exclude=data --exclude=.env .
Pop-Location

Write-Host "-> Uploading to $Server ..." -ForegroundColor Cyan
ssh @sshOpts $Server "sudo mkdir -p $RemoteDir && sudo chown -R `$(whoami):`$(whoami) $RemoteDir"
scp @sshOpts $Archive "${Server}:/tmp/personal-agent-deploy.tar.gz"

$envFile = Join-Path $ScriptDir ".env"
$envProd = Join-Path $ScriptDir ".env.production"
if (Test-Path $envProd) {
    scp @sshOpts $envProd "${Server}:${RemoteDir}/.env"
} elseif (Test-Path $envFile) {
    scp @sshOpts $envFile "${Server}:${RemoteDir}/.env"
}

Write-Host "-> Redeploying..." -ForegroundColor Cyan
ssh @sshOpts $Server @"
set -e
cd $RemoteDir
tar -xzf /tmp/personal-agent-deploy.tar.gz
rm -f /tmp/personal-agent-deploy.tar.gz
chmod +x oracle-redeploy.sh oracle-setup.sh
./oracle-redeploy.sh
"@

Remove-Item $Archive -ErrorAction SilentlyContinue
Write-Host ""
Write-Host "Deploy complete! Bot at $RemoteDir" -ForegroundColor Green
