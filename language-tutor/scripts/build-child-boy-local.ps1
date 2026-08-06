# Сборка child-boy.glb с файлов в pack/
# Запуск из PowerShell:
#   cd C:\Users\DavidPC\Projects\ai-agency\language-tutor
#   .\scripts\build-child-boy-local.ps1

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$pack = Join-Path $root "assets\child-boy\pack"

Write-Host "Папка pack: $pack"
if (-not (Test-Path $pack)) {
    Write-Host "Создаю pack..."
    New-Item -ItemType Directory -Path $pack -Force | Out-Null
}

$gltf = Get-ChildItem -Path $pack -Filter *.gltf -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $gltf) {
    Write-Host "ERROR: Нет .gltf в pack. Положите файлы и запустите снова." -ForegroundColor Red
    exit 1
}

Write-Host "Найден: $($gltf.Name)"
Set-Location $root
node scripts/prepare-child-boy-model.mjs
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ""
Write-Host "OK: webapp\public\models\child-boy.glb" -ForegroundColor Green
Write-Host "Запуск сайта: cd webapp; npm run dev" -ForegroundColor Cyan
