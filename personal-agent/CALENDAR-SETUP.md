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
- Откройте TCP **8081** в Oracle Security List (как для **8000** у language-tutor)

### Как открыть порт 8081 в Oracle Cloud

1. [Oracle Cloud Console](https://cloud.oracle.com/) → **Networking** → **Virtual Cloud Networks**
2. Выберите ваш VCN → **Security Lists** → **Default Security List**
3. **Add Ingress Rules**:
   - Source CIDR: `0.0.0.0/0`
   - IP Protocol: **TCP**
   - Destination Port Range: **8081**
4. **Add Ingress Rules**

Проверка с вашего ПК:
```bash
curl http://140.84.183.154:8081/health
```
Должно вернуть: `{"ok": true, "google_calendar": true}`

На самом сервере (localhost) порт уже работает — блокировка только снаружи (Security List).

## Команды

- `/calendar` — подключить
- `/calendar_on` / `/calendar_off` — вкл/выкл синхронизацию
