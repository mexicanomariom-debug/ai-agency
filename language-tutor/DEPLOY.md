# Language Tutor — Deployment Guide

Auto-deploy: push to `cursor/language-tutor-recreate-a360` triggers GitHub Actions (Oracle + Vercel).

## Architecture

- **Telegram Bot** — onboarding (language → level → chat), no persona selection
- **FastAPI API** — SSE chat streaming, persona management, Telegram auth
- **Next.js Web App** — landing, pricing, Telegram Web App (TWA) with personas
- **PostgreSQL + pgvector** — user data and RAG embeddings

## Oracle Server (140.84.183.154)

### Windows (PowerShell)

```powershell
# 1. Clone repo (if not yet)
cd C:\Users\DavidPC\Projects
git clone https://github.com/mexicanomariom-debug/ai-agency.git
cd ai-agency\language-tutor

# 2. Checkout branch with language-tutor
git checkout cursor/language-tutor-recreate-a360

# 3. Create .env with BOT_TOKEN and OPENAI_API_KEY (copy from .env.example)

# 4. Deploy (with SSH key if needed)
.\deploy-to-oracle.ps1
# or with explicit key:
.\deploy-to-oracle.ps1 -KeyPath "C:\Users\DavidPC\.ssh\oracle_key"
```

### Linux / macOS / Git Bash

```bash
cd language-tutor
chmod +x deploy-to-oracle.sh
./deploy-to-oracle.sh ubuntu@140.84.183.154
```

## Local Development

```bash
cp .env.example .env
# Edit .env with BOT_TOKEN and OPENAI_API_KEY

docker compose up -d --build
docker compose exec api alembic upgrade head
```

API: http://localhost:8000  
Webapp: `cd webapp && npm install && npm run dev`

## Production (Docker)

```bash
chmod +x deploy.sh
./deploy.sh
```

Set strong values for `POSTGRES_PASSWORD`, `API_SECRET_KEY`, and disable `DEMO_MODE`.

## Render

Push to GitHub and connect the repo in Render. Use `render.yaml` for blueprint deployment.

Required secrets in Render dashboard:
- `BOT_TOKEN`
- `OPENAI_API_KEY`
- `POSTGRES_PASSWORD` (if not using Render Postgres)

## Vercel (Web App)

```bash
cd webapp
vercel --prod
```

Set environment variables in Vercel:
- `NEXT_PUBLIC_API_URL` — your FastAPI URL
- `NEXT_PUBLIC_TWA_URL` — Vercel deployment URL
- `NEXT_PUBLIC_DEMO_MODE` — `false` in production

## Environment Variables

| Variable | Description |
|----------|-------------|
| `BOT_TOKEN` | Telegram bot token from @BotFather |
| `BOT_USERNAME` | Bot username (default: All_languages_bot) |
| `OPENAI_API_KEY` | OpenAI API key |
| `DATABASE_URL` | PostgreSQL connection string |
| `TWA_URL` | Telegram Web App URL |
| `API_SECRET_KEY` | JWT/session signing key |
| `DEMO_MODE` | Allow web demo without Telegram auth |

## Migrations

```bash
docker compose exec api alembic upgrade head
docker compose exec api alembic revision --autogenerate -m "description"
```
