# Personal Agent — Oracle Deploy

Рядом с language-tutor (`/opt/opus5`) на том же сервере **140.84.183.154**.

| Проект | Путь на сервере | Порт |
|--------|-----------------|------|
| Language Tutor | `/opt/opus5` | 8000 (API) |
| **Personal Agent** | `/opt/personal-agent` | 8081 (OAuth Calendar) |

| Проект | Бот в Telegram | Secret в GitHub |
|--------|--------------|-----------------|
| Language Tutor | @All_languages_bot | `BOT_TOKEN` |
| Personal Agent | @mychatbot7_bot | `PERSONAL_AGENT_BOT_TOKEN` |

**Важно:** у каждого бота свой токен от @BotFather. Если подставить один токен в оба проекта — Telegram будет конфликтовать (`409`), и боты перестанут отвечать. Деплой одного проекта **не должен** останавливать другой.

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
