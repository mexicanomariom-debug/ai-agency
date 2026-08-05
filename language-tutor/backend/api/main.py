from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import chat, personas, users, voice
from config import settings
from database.session import async_session_factory
from services.personas import persona_service


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
