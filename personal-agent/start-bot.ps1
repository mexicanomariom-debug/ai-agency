$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "================================" -ForegroundColor Cyan
Write-Host "  Personal Agent - Telegram Bot" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path ".env")) {
    Write-Host "[ОШИБКА] Файл .env не найден!" -ForegroundColor Red
    Write-Host "Выполните: Copy-Item env.example .env" -ForegroundColor Yellow
    Write-Host "Затем вставьте BOT_TOKEN в .env" -ForegroundColor Yellow
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
    Start-Process "https://www.python.org/downloads/"
    Read-Host "Нажмите Enter"
    exit 1
}

Write-Host "Устанавливаю зависимости..." -ForegroundColor Green
& $python -m pip install -r requirements.txt -q

Write-Host ""
Write-Host "Запускаю бота... Не закрывайте окно!" -ForegroundColor Green
Write-Host "Остановить: Ctrl+C" -ForegroundColor Yellow
Write-Host ""

& $python -m bot.main

Read-Host "Нажмите Enter для выхода"
