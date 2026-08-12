# ai-ege-tutor-bot (@repetitors_ai_bot)

Скопируйте сюда ваш проект с ПК, затем push — Cloud Agent задеплоит на Oracle.

## Скопировать с ПК (PowerShell)

```powershell
$src = "C:\Users\DavidPC\Projects\ai-ege-tutor-bot 2\ai-ege-tutor-bot"
$dst = "C:\Users\DavidPC\Projects\ai-agency\ai-ege-tutor-bot"
Remove-Item $dst -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $dst | Out-Null
Copy-Item -Path "$src\*" -Destination $dst -Recurse -Force
# .env не коммитить — токен только в GitHub Secrets
Remove-Item "$dst\.env" -Force -ErrorAction SilentlyContinue
```

```powershell
cd C:\Users\DavidPC\Projects\ai-agency
git add ai-ege-tutor-bot
git commit -m "add ai-ege-tutor-bot for Oracle deploy"
git push origin main
```

## Секреты GitHub (не в чат!)

Repo → Settings → Secrets and variables → Actions:

| Secret | Значение |
|--------|----------|
| `ORACLE_SSH_KEY` | приватный ключ Oracle (уже есть, если personal-agent деплоился) |
| `REPETITORS_BOT_TOKEN` | `BOT_TOKEN` из `.env` репетитора (@repetitors_ai_bot) |

Добавить секрет с ПК:

```powershell
cd C:\Users\DavidPC\Projects\ai-agency
gh auth login
gh secret set REPETITORS_BOT_TOKEN --body "ВСТАВЬТЕ_ТОКЕН_ИЗ_.env"
```

После push запустится workflow **Deploy ai-ege-tutor-bot to Oracle**.
