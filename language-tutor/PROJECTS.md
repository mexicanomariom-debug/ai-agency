# Локальные проекты (Windows) → Oracle

Токены и `.env` — в `C:\Users\DavidPC\Projects`. Сервер только **140.84.183.154**.

## Репетитор @repetitors_ai_bot — основной проект

| Локально | Бот | Oracle |
|----------|-----|--------|
| **`ai-ege-tutor-bot 2\ai-ege-tutor-bot`** | @repetitors_ai_bot | `/opt/opus5` |
| `ai-ege-tutor-bot` | @repetitors_ai_bot | `/opt/opus5` |
| `ai-agency\personal-agent` | @mychatbot7_bot | `/opt/personal-agent` |

`language-tutor` и `opus5` в ai-agency — **старый** language-tutor, не ваш EGE-репетитор.

## Деплой репетитора (одна команда)

```powershell
cd C:\Users\DavidPC\Projects\ai-agency
git pull origin cursor/personal-agent-task-scheduler-64cf
.\scripts\deploy-ai-ege-tutor-oracle.ps1
```

Проект: `C:\Users\DavidPC\Projects\ai-ege-tutor-bot 2\ai-ege-tutor-bot`  
Токен: `.env` в этой папке (`BOT_TOKEN` для @repetitors_ai_bot).

## `.env` репетитора

```env
BOT_TOKEN=...
BOT_USERNAME=repetitors_ai_bot
OPENAI_API_KEY=...
```

## Personal agent

```powershell
cd C:\Users\DavidPC\Projects\ai-agency\personal-agent
.\deploy-to-oracle.ps1
```

Отдельный токен `@mychatbot7_bot`.

## GitHub Actions

Секрет `REPETITORS_BOT_TOKEN` или `BOT_TOKEN` = токен @repetitors_ai_bot (не @All_languages_bot).
