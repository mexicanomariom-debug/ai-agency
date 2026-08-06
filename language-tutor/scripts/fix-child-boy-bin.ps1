# Диагностика pack/ + фиксация имени .bin под пробелы
# Запуск:  .\scripts\fix-child-boy-bin.ps1

$ErrorActionPreference = "Stop"
$pack = Join-Path (Split-Path $PSScriptRoot -Parent) "assets\child-boy\pack"

Write-Host "Папка: $pack" -ForegroundColor Cyan
if (-not (Test-Path $pack)) {
    Write-Host "Папки нет. Создайте и положите файлы." -ForegroundColor Red
    exit 1
}

Write-Host "`nСодержимое pack:" -ForegroundColor Yellow
Get-ChildItem $pack -File | ForEach-Object { "  $($_.Name)  ($([math]::Round($_.Length/1MB,1)) MB)" }

$bins = Get-ChildItem $pack -Recurse -Filter *.bin -File -ErrorAction SilentlyContinue
Write-Host "`nФайлы .bin:" -ForegroundColor Yellow
if (-not $bins) {
    Write-Host "  НЕТ .bin — это и есть ошибка." -ForegroundColor Red
    Write-Host @"

Что сделать:
1. На CGTrader снова скачайте .gltf (часто .bin идёт вместе с ним)
2. Или скачайте .fbx и в Blender: File → Export → glTF 2.0 (.glb)
3. Положите .bin / .glb в:
   $pack
"@
    exit 1
}

$bins | ForEach-Object { "  $($_.FullName)" }

$wanted = "young boy character riigged.bin"
$dest = Join-Path $pack $wanted
if (-not (Test-Path $dest)) {
    $src = $bins[0].FullName
    Copy-Item -LiteralPath $src -Destination $dest -Force
    Write-Host "`nСкопировал: $($bins[0].Name) → $wanted" -ForegroundColor Green
} else {
    Write-Host "`nУже есть: $wanted" -ForegroundColor Green
}

Write-Host "`nЗапуск сборки..." -ForegroundColor Cyan
Set-Location (Split-Path $PSScriptRoot -Parent)
node scripts\prepare-child-boy-model.mjs
