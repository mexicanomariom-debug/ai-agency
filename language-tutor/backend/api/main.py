from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from api.routes import chat, personas, users, voice
from config import settings
from database.session import async_session_factory
from services.personas import persona_service

VOICE_TWA_HTML = Path(__file__).resolve().parent.parent / "static" / "voice_twa.html"
TG_FRAME_CSP = "frame-ancestors 'self' https://web.telegram.org https://telegram.org"


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with async_session_factory() as session:
        await persona_service.seed_personas(session)
        await session.commit()
    yield


app = FastAPI(
    title="Language Tutor API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api")
app.include_router(voice.router, prefix="/api")
app.include_router(personas.router, prefix="/api")
app.include_router(users.router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok", "environment": settings.environment}


@app.get("/twa/voice")
async def voice_twa():
    """Self-contained voice teacher mini-app (proxied by Vercel /voice rewrite)."""
    return FileResponse(
        VOICE_TWA_HTML,
        media_type="text/html",
        headers={"Content-Security-Policy": TG_FRAME_CSP},
    )
