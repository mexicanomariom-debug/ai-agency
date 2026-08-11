# Copy secrets from neighboring project folders into language-tutor/.env
# Usage: .\scripts\sync-secrets.ps1

$ErrorActionPreference = "Stop"
$Target = Join-Path $PSScriptRoot "..\.env"
$Target = (Resolve-Path (Split-Path $Target -Parent)).Path + "\.env"

# Local secrets — primary: ai-ege-tutor-bot (@repetitors_ai_bot). See PROJECTS.md
$candidates = @(
    "$env:USERPROFILE\Projects\ai-ege-tutor-bot 2\ai-ege-tutor-bot\.env",
    "$env:USERPROFILE\Projects\ai-ege-tutor-bot\ai-ege-tutor-bot\.env",
    "$env:USERPROFILE\Projects\ai-ege-tutor-bot\.env",
    (Join-Path $PSScriptRoot "..\.env"),
    "$env:USERPROFILE\Projects\opus5\.env",
    "$env:USERPROFILE\Projects\language-tutor\.env",
    "$env:USERPROFILE\Projects\ai-agency\language-tutor\.env",
    (Join-Path $PSScriptRoot "..\..\opus5\.env"),
    (Join-Path $PSScriptRoot "..\..\language-tutor-secrets\.env"),
    (Join-Path $PSScriptRoot "..\..\ai-agency-secrets\.env")
)

$source = $null
foreach ($path in $candidates) {
    try {
        $resolved = Resolve-Path $path -ErrorAction Stop
        if (Test-Path $resolved) {
            $source = $resolved.Path
            break
        }
    } catch {}
}

if (-not $source) {
    Write-Host "No secrets .env found in neighboring folders." -ForegroundColor Yellow
    Write-Host "Searched:"
    $candidates | ForEach-Object { Write-Host "  $_" }
    Write-Host ""
    Write-Host "Create language-tutor\.env manually from .env.example"
    exit 1
}

Copy-Item $source $Target -Force
Write-Host "Copied secrets from:" -ForegroundColor Green
Write-Host "  $source"
Write-Host "  -> $Target"
