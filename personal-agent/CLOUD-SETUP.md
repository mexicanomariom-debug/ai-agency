# Как дать Cloud Agent доступ к токенам (безопасно)

**Никогда не загружайте `.env` с токенами в GitHub.**  
Токены попадут в историю репозитория, и их смогут украсть.

---

## Правильный способ — секреты в Cursor

### Шаг 1. Залейте код на GitHub (без токенов)

Токены в git не нужны. Достаточно обычного push:

```powershell
cd C:\Users\DavidPC\ai-agency
git add .
git commit -m "my changes"
git push
```

Файл `.env` **не попадёт** в git — он в `.gitignore`.

---

### Шаг 2. Добавьте секреты в Cursor (не в git)

1. Откройте [cursor.com](https://cursor.com) → **Dashboard**
2. Перейдите в **Cloud Agents** → **Environments**
3. Выберите репозиторий `ai-agency` (или создайте Environment)
4. В разделе **Secrets / Environment Variables** добавьте:

| Имя переменной | Значение |
|----------------|----------|
| `BOT_TOKEN` | токен от @BotFather |
| `OPENAI_API_KEY` | ключ OpenAI (если есть) |
| `GOOGLE_CLIENT_ID` | для календаря (если есть) |
| `GOOGLE_CLIENT_SECRET` | для календаря (если есть) |
| `TWILIO_ACCOUNT_SID` | для звонков (если есть) |
| `TWILIO_AUTH_TOKEN` | для звонков (если есть) |
| `TWILIO_FROM_NUMBER` | для звонков (если есть) |

5. Сохраните Environment

---

### Шаг 3. Запустите Cloud Agent

1. В Cursor откройте чат с агентом
2. Выберите режим **Cloud Agent**
3. Укажите Environment с вашими секретами
4. Напишите: «Запусти personal-agent бота»

Агент получит токены из секретов Cursor и сможет запустить бота в облаке.

---

## Что уже настроено в репозитории

Файл `.cursor/environment.json` говорит Cloud Agent:
- установить зависимости (`pip install`)
- запустить бота (`python -m bot.main`)

Секреты подставляются из Cursor Environment, не из git.

---

## Альтернатива — написать токены прямо в чат

Можно отправить агенту:

```
BOT_TOKEN=7123...
OPENAI_API_KEY=sk-...
```

Но это **менее безопасно** — токены останутся в истории чата.  
Лучше использовать Secrets в Cursor Dashboard.

---

## Чеклист

- [ ] `.env` есть локально на ПК (для `start-bot.bat`)
- [ ] `.env` **не** закоммичен в git
- [ ] Секреты добавлены в Cursor → Environments
- [ ] Запущен Cloud Agent с этим Environment
