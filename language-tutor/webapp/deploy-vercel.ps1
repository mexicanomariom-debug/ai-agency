# Deploy language-tutor webapp to Vercel (run as Vercel project owner)
# Usage: .\deploy-vercel.ps1

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "=== Deploy webapp to Vercel (production) ===" -ForegroundColor Cyan
Write-Host "Project: webapp  ->  https://webapp-bay-three-75.vercel.app"
Write-Host ""

if (-not (Get-Command npx -ErrorAction SilentlyContinue)) {
  Write-Host "ERROR: Node.js/npx not found. Install from https://nodejs.org" -ForegroundColor Red
  exit 1
}

Write-Host "1. Login - browser will open. Use the Vercel account that owns project webapp..."
npx vercel login

Write-Host ""
Write-Host "2. Link to existing project webapp..."
npx vercel link --yes --project webapp

Write-Host ""
Write-Host "3. Production deploy..."
npx vercel --prod --yes

Write-Host ""
Write-Host "=== Done ===" -ForegroundColor Green
Write-Host "Check: https://webapp-bay-three-75.vercel.app/voice"
Write-Host "Expected: HTTP 200 voice teacher page, not 404"
