$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "================================" -ForegroundColor Cyan
Write-Host "  Personal Agent - Telegram Bot" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path ".env")) {
    Write-Host "[ОШИБКА] Файл .env не найден!" -ForegroundColor Red
    Write-Host "Выполните: Copy-Item env.example .env" -ForegroundColor Yellow
    Read-Host "Нажмите Enter"
    exit 1
}

$allowLocal = Select-String -Path ".env" -Pattern "^ALLOW_LOCAL_BOT=true" -CaseSensitive:$false
if (-not $allowLocal) {
    Write-Host "[СТОП] Локальный запуск отключён." -ForegroundColor Red
    Write-Host ""
    Write-Host "Бот @mychatbot7_bot работает на сервере Oracle 24/7." -ForegroundColor Yellow
    Write-Host "Локальный запуск с тем же токеном ломает бота для всех." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Для разработки добавьте в .env: ALLOW_LOCAL_BOT=true" -ForegroundColor Yellow
    Read-Host "Нажмите Enter"
    exit 1
}

$tokenLine = Select-String -Path ".env" -Pattern "^BOT_TOKEN=(.+)$" | Select-Object -First 1
if (-not $tokenLine -or $tokenLine.Matches.Groups[1].Value.Trim() -eq "") {
    Write-Host "[ОШИБКА] BOT_TOKEN пустой в .env" -ForegroundColor Red
    Read-Host "Нажмите Enter"
    exit 1
}

$python = $null
if (Get-Command py -ErrorAction SilentlyContinue) { $python = "py" }
elseif (Get-Command python -ErrorAction SilentlyContinue) { $python = "python" }
else {
    Write-Host "[ОШИБКА] Python не найден. Установите с python.org" -ForegroundColor Red
    Read-Host "Нажмите Enter"
    exit 1
}

Write-Host "Устанавливаю зависимости..." -ForegroundColor Green
& $python -m pip install -r requirements.txt -q

Write-Host ""
Write-Host "ЛОКАЛЬНЫЙ режим. Остановите Ctrl+C после теста!" -ForegroundColor Yellow
Write-Host ""

& $python -m bot.main

Read-Host "Нажмите Enter для выхода"
