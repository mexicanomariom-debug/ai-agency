# Локальные проекты (Windows) → Oracle

Токены и `.env` меняете **локально** в `C:\Users\DavidPC\Projects`. Деплой только на **наш** сервер `140.84.183.154`.

## Карта папок

| Локально (`C:\Users\DavidPC\Projects\…`) | Бот Telegram | На сервере Oracle |
|------------------------------------------|--------------|-------------------|
| `opus5` | @repetitors_ai_bot | `/opt/opus5` |
| `language-tutor` | @repetitors_ai_bot | `/opt/opus5` (тот же деплой) |
| `ai-agency\language-tutor` | @repetitors_ai_bot | `/opt/opus5` |
| `ai-agency\personal-agent` | @mychatbot7_bot | `/opt/personal-agent` |

`opus5` на диске и `language-tutor` в монорепо — **один и тот же репетитор** (код language-tutor). Путь `/opt/opus5` на сервере — историческое имя, не старый `@All_languages_bot`.

## Токены в `.env`

В `.env` репетитора (любая из папок выше, кроме personal-agent):

```env
BOT_TOKEN=...          # токен @repetitors_ai_bot от BotFather
BOT_USERNAME=repetitors_ai_bot
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...  # опционально
```

Для personal-agent — отдельный токен `@mychatbot7_bot` (не `BOT_TOKEN` репетитора).

## Деплой репетитора с ПК

```powershell
cd C:\Users\DavidPC\Projects\ai-agency\language-tutor
.\scripts\sync-secrets.ps1
.\deploy-to-oracle.ps1 -KeyPath "C:\Users\DavidPC\.ssh\oracle_key"
```

Если работаете из standalone `opus5`:

```powershell
cd C:\Users\DavidPC\Projects\opus5
.\deploy-to-oracle.ps1 -KeyPath "C:\Users\DavidPC\.ssh\oracle_key"
```

Скрипт копирует **ваш локальный** `.env` на сервер — GitHub Secrets не нужны для ручного деплоя.

## GitHub Actions

Workflow **Restart Language Tutor on Oracle** берёт `BOT_TOKEN` из GitHub Secrets. Если секрет — токен старого `@All_languages_bot`, на сервере снова поднимется не тот бот. Обновите секрет `BOT_TOKEN` на токен `@repetitors_ai_bot` (тот же, что в локальном `.env`).

## Не запускать боты в двух местах

Один токен = один процесс polling. Остановите бот на старом сервере / втором ПК, если видите `TelegramConflictError`.
