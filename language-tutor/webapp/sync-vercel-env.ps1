# Sync API keys from language-tutor/.env into Vercel project "webapp", then redeploy.
# Run from anywhere:  .\sync-vercel-env.ps1
# Must be logged in as Vercel project owner (npx vercel login).

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$envFile = Join-Path (Resolve-Path ..).Path ".env"
if (-not (Test-Path $envFile)) {
  $envFile = Join-Path (Resolve-Path ..\..).Path "language-tutor\.env"
}
if (-not (Test-Path $envFile)) {
  Write-Host "ERROR: language-tutor/.env not found. Create it with OPENAI_API_KEY=..." -ForegroundColor Red
  exit 1
}

function Get-DotEnvValue([string]$path, [string]$key) {
  $line = Get-Content $path | Where-Object { $_ -match "^\s*$key\s*=" } | Select-Object -First 1
  if (-not $line) { return $null }
  return ($line -replace "^\s*$key\s*=\s*", "").Trim().Trim('"').Trim("'")
}

$openai = Get-DotEnvValue $envFile "OPENAI_API_KEY"
$anthropic = Get-DotEnvValue $envFile "ANTHROPIC_API_KEY"

if (-not $openai) {
  Write-Host "ERROR: OPENAI_API_KEY missing in $envFile" -ForegroundColor Red
  exit 1
}

Write-Host "Linking project webapp..."
npx vercel link --yes --project webapp | Out-Null

Write-Host "Setting OPENAI_API_KEY on Vercel (production)..."
$openai | npx vercel env add OPENAI_API_KEY production --force

if ($anthropic) {
  Write-Host "Setting ANTHROPIC_API_KEY on Vercel (production)..."
  $anthropic | npx vercel env add ANTHROPIC_API_KEY production --force
}

Write-Host "Setting BACKEND_URL..."
"http://140.84.183.154:8000" | npx vercel env add BACKEND_URL production --force

Write-Host "Deploying production..."
# Deploy from repo root so Root Directory language-tutor/webapp is respected
Set-Location (Resolve-Path ..\..).Path
npx vercel deploy --prod --yes

Write-Host ""
Write-Host "Done. Open Telegram button again." -ForegroundColor Green
Write-Host "https://webapp-bay-three-75.vercel.app/voice"
