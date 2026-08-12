# ONE script: copy ai-ege-tutor-bot into ai-agency, set secret, push → GitHub deploys to Oracle
# Run in PowerShell:
#   cd C:\Users\DavidPC\Projects\ai-agency
#   irm https://raw.githubusercontent.com/mexicanomariom-debug/ai-agency/main/scripts/do-all-ai-ege-deploy.ps1 | iex
# Or:
#   .\scripts\do-all-ai-ege-deploy.ps1

$ErrorActionPreference = "Stop"

$Agency = "C:\Users\DavidPC\Projects\ai-agency"
$SrcCandidates = @(
    "C:\Users\DavidPC\Projects\ai-ege-tutor-bot 2\ai-ege-tutor-bot",
    "C:\Users\DavidPC\Projects\ai-ege-tutor-bot\ai-ege-tutor-bot",
    "C:\Users\DavidPC\Projects\ai-ege-tutor-bot"
)

$src = $null
foreach ($p in $SrcCandidates) {
    if (Test-Path $p) { $src = $p; break }
}
if (-not $src) {
    Write-Host "ERROR: ai-ege-tutor-bot folder not found under Projects" -ForegroundColor Red
    exit 1
}

$envPath = Join-Path $src ".env"
if (-not (Test-Path $envPath)) {
    Write-Host "ERROR: no .env in $src" -ForegroundColor Red
    exit 1
}
$tokenLine = Get-Content $envPath | Where-Object { $_ -match '^BOT_TOKEN=' } | Select-Object -First 1
if (-not $tokenLine) {
    Write-Host "ERROR: BOT_TOKEN missing in .env" -ForegroundColor Red
    exit 1
}
$token = $tokenLine -replace '^BOT_TOKEN=', ''

Write-Host "Source: $src" -ForegroundColor Cyan
Write-Host "Agency: $Agency" -ForegroundColor Cyan

if (-not (Test-Path $Agency)) {
    Write-Host "ERROR: ai-agency not found at $Agency" -ForegroundColor Red
    exit 1
}

Set-Location $Agency
git pull origin main

$dst = Join-Path $Agency "ai-ege-tutor-bot"
Write-Host "Copying project (without .env)..." -ForegroundColor Cyan
if (Test-Path $dst) {
    Get-ChildItem $dst -Force | Where-Object { $_.Name -notin @('.gitignore','README.md') } | Remove-Item -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $dst | Out-Null
Copy-Item -Path (Join-Path $src "*") -Destination $dst -Recurse -Force
Remove-Item (Join-Path $dst ".env") -Force -ErrorAction SilentlyContinue
Remove-Item (Join-Path $dst ".env.production") -Force -ErrorAction SilentlyContinue

if (Get-Command gh -ErrorAction SilentlyContinue) {
    Write-Host "Setting GitHub secret REPETITORS_BOT_TOKEN..." -ForegroundColor Cyan
    $token | gh secret set REPETITORS_BOT_TOKEN
} else {
    Write-Host "WARN: gh CLI not found — set REPETITORS_BOT_TOKEN manually in GitHub Secrets" -ForegroundColor Yellow
}

git add ai-ege-tutor-bot
git status
git commit -m "add ai-ege-tutor-bot source for Oracle deploy" --allow-empty
git push origin main

Write-Host ""
Write-Host "DONE. GitHub Actions will deploy to Oracle." -ForegroundColor Green
Write-Host "Check: https://github.com/mexicanomariom-debug/ai-agency/actions" -ForegroundColor Green
Write-Host "Bot:   https://t.me/repetitors_ai_bot" -ForegroundColor Green
