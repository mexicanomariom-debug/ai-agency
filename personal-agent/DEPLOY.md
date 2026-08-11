# Personal Agent — Oracle Deploy

Рядом с репетитором (`/opt/opus5`, @repetitors_ai_bot) на том же сервере **140.84.183.154**.

Локально: `C:\Users\DavidPC\Projects\ai-agency\personal-agent` — см. `language-tutor/PROJECTS.md`.

| Проект | Путь на сервере | Порт |
|--------|-----------------|------|
| Language Tutor | `/opt/opus5` | 8000 (API) |
| **Personal Agent** | `/opt/personal-agent` | 8081 (OAuth Calendar) |

| Проект | Бот в Telegram | Secret в GitHub |
|--------|--------------|-----------------|
| Language Tutor | @repetitors_ai_bot | `BOT_TOKEN` |
| Personal Agent | @mychatbot7_bot | `PERSONAL_AGENT_BOT_TOKEN` |

## Два бота на одном сервере — это нормально

| Бот | Secret |
|-----|--------|
| @repetitors_ai_bot | `BOT_TOKEN` |
| @mychatbot7_bot | `PERSONAL_AGENT_BOT_TOKEN` |

**Не запускайте `bot.main` в двух местах с одним токеном** — Telegram пришлёт два ответа на каждое сообщение (разные базы задач).

Запрещено автозапускать бота в `.cursor/environment.json` и на ПК без `ALLOW_LOCAL_BOT=true`.

## Автодеплой (GitHub Actions)

1. GitHub → repo **Settings → Secrets → Actions**, добавьте:

| Secret | Значение |
|--------|----------|
| `PERSONAL_AGENT_BOT_TOKEN` | токен **@mychatbot7_bot** (не путать с `BOT_TOKEN` для language-tutor) |
| `OPENAI_API_KEY` | ключ OpenAI (уже может быть) |
| `ORACLE_SSH_KEY` | SSH ключ (уже есть для language-tutor) |

2. Push в ветку `cursor/personal-agent-task-scheduler-64cf` или вручную:
   **Actions → Deploy Personal Agent to Oracle → Run workflow**

## Ручной деплой с Windows

```powershell
cd C:\Users\DavidPC\ai-agency\personal-agent
# .env с BOT_TOKEN и OPENAI_API_KEY
.\deploy-to-oracle.ps1
```

## Ручной деплой с Linux

```bash
cd personal-agent
chmod +x deploy-to-oracle.sh oracle-setup.sh oracle-redeploy.sh
./deploy-to-oracle.sh ubuntu@140.84.183.154
```

## Проверка на сервере

```bash
ssh ubuntu@140.84.183.154
cd /opt/personal-agent
sudo docker compose -f docker-compose.prod.yml ps
sudo docker compose -f docker-compose.prod.yml logs bot --tail 50
```

## Google Calendar на Oracle

В Google Cloud Console добавьте redirect URI:

```
http://140.84.183.154:8081/oauth/google/callback
```

И в Oracle Security List откройте TCP **8081** (как для 8000 у language-tutor).

<!-- deploy trigger 2026-08-09 -->
