# Google Calendar — подключение

## Redirect URI для Google Cloud

Используйте **домен Vercel** (Google не принимает IP-адрес):

```
https://ai-agency-drab.vercel.app/api/google/oauth/callback
```

Добавьте в Google Cloud → Credentials → OAuth client → Authorized redirect URIs.

## Секреты

### GitHub Actions (бот на Oracle)

| Secret | Описание |
|--------|----------|
| `GOOGLE_CLIENT_ID` | Client ID |
| `GOOGLE_CLIENT_SECRET` | Client Secret |
| `PERSONAL_AGENT_INTERNAL_SECRET` | Общий секрет с Vercel |
| `PERSONAL_AGENT_BOT_TOKEN` | Токен бота |

### Vercel (проект ai-agency)

Settings → Environment Variables:

| Variable | Value |
|----------|-------|
| `GOOGLE_CLIENT_ID` | тот же Client ID |
| `GOOGLE_CLIENT_SECRET` | тот же Client Secret |
| `GOOGLE_REDIRECT_URI` | `https://ai-agency-drab.vercel.app/api/google/oauth/callback` |
| `PERSONAL_AGENT_BOT_URL` | `http://140.84.183.154:8081` |
| `PERSONAL_AGENT_INTERNAL_SECRET` | тот же секрет, что в GitHub |

После добавления — **Redeploy** проект ai-agency на Vercel.

## Подключение в Telegram

1. Убедитесь, что секреты добавлены (GitHub + Vercel)
2. Дождитесь деплоя бота (push в ветку или Actions)
3. В боте: **📅 Календарь** → ссылка → войти в Google
4. Вернитесь в Telegram — придёт «Google Calendar подключён»

## Порты Oracle

- **8081** — внутренний API бота (Vercel → Oracle)
- Откройте TCP 8081 в Oracle Security List (как 8000)

## Команды

- `/calendar` — подключить
- `/calendar_on` / `/calendar_off` — вкл/выкл синхронизацию
