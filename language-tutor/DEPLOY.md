# Language Tutor — Deployment Guide

Auto-deploy: push to `cursor/language-tutor-recreate-a360` triggers GitHub Actions (Oracle + Vercel).

## Architecture

- **Telegram Bot** — onboarding (language → level → chat), no persona selection
- **FastAPI API** — SSE chat streaming, persona management, Telegram auth
- **Next.js Web App** — landing, pricing, Telegram Web App (TWA) with personas
- **PostgreSQL + pgvector** — user data and RAG embeddings

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
