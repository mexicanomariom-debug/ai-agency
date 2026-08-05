# Language Tutor — Deployment Guide

Auto-deploy: push to `main` triggers GitHub Actions (Oracle + Vercel build check).

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

Production URL: `https://webapp-bay-three-75.vercel.app`

The blue Telegram button **«Учитель — общение»** opens `/voice`. If you see **404**, the Vercel project was not redeployed after adding the route.

### Option A — Deploy Hook (recommended, 2 minutes)

1. Vercel → project **webapp-bay-three-75** → **Settings → Git → Deploy Hooks**
2. Create hook for branch `main` (Root Directory must be `language-tutor/webapp`)
3. GitHub → repo **Secrets** → add `VERCEL_DEPLOY_HOOK` with the hook URL
4. Re-run workflow **Deploy Webapp to Vercel** or push any change to `language-tutor/webapp/`

### Option B — Vercel CLI token

```bash
cd language-tutor/webapp
vercel link   # select webapp-bay project
vercel --prod
```

Or add GitHub Secrets: `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID` (from `.vercel/project.json` after `vercel link`).

### Option C — Manual from CI

Push to `main` triggers build verification. Without secrets, only the `vercel-webapp` branch sync runs (webapp-only tree for separate Vercel project).

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
