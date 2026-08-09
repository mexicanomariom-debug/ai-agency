@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Personal Agent Bot

echo ================================
echo   Personal Agent - Telegram Bot
echo ================================
echo.

if not exist ".env" (
    echo [ОШИБКА] Файл .env не найден!
    echo.
    echo Сделайте так:
    echo   1. copy env.example .env
    echo   2. Откройте .env и вставьте BOT_TOKEN=ваш_токен
    echo.
    pause
    exit /b 1
)

findstr /B "BOT_TOKEN=$" .env >nul 2>&1
if %errorlevel%==0 (
    echo [ОШИБКА] BOT_TOKEN пустой в .env
    echo Откройте .env и вставьте токен от @BotFather
    pause
    exit /b 1
)

where py >nul 2>&1
if %errorlevel%==0 (
    set PYTHON=py
    set PIP=py -m pip
    goto :run
)

where python >nul 2>&1
if %errorlevel%==0 (
    set PYTHON=python
    set PIP=python -m pip
    goto :run
)

echo [ОШИБКА] Python не найден!
echo.
echo Установите Python: https://www.python.org/downloads/
echo При установке поставьте галочку "Add python.exe to PATH"
echo.
start https://www.python.org/downloads/
pause
exit /b 1

:run
echo Python найден. Устанавливаю зависимости...
%PIP% install -r requirements.txt -q
if %errorlevel% neq 0 (
    echo [ОШИБКА] Не удалось установить зависимости
    pause
    exit /b 1
)

echo.
echo Запускаю бота... Не закрывайте это окно!
echo Остановить: Ctrl+C
echo.
%PYTHON% -m bot.main
pause
