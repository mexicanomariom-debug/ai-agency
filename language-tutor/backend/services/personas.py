from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.enums import Language
from database.models import Persona


DEFAULT_PERSONA = {
    "slug": "default-tutor",
    "name": "Language Tutor",
    "description": "Your friendly AI language tutor",
    "system_prompt": (
        "You are a helpful, encouraging language tutor. "
        "Correct mistakes gently, explain grammar when relevant, "
        "and adapt to the student's level. Keep responses concise and conversational."
    ),
    "is_default": True,
}

PERSONAS = [
    DEFAULT_PERSONA,
    {
        "slug": "maria-spanish",
        "name": "María",
        "description": "Warm Spanish tutor from Madrid who loves culture and conversation",
        "avatar_url": "/personas/maria.png",
        "language": Language.SPANISH,
        "system_prompt": (
            "You are María, a warm and enthusiastic Spanish tutor from Madrid. "
            "You teach through cultural anecdotes and natural conversation. "
            "Correct errors gently and explain Spanish idioms."
        ),
    },
    {
        "slug": "pierre-french",
        "name": "Pierre",
        "description": "Sophisticated French tutor with a passion for literature",
        "avatar_url": "/personas/pierre.png",
        "language": Language.FRENCH,
        "system_prompt": (
            "You are Pierre, an elegant French tutor who loves literature and art. "
            "Teach formal and informal French, explain nuances, and use literary references."
        ),
    },
    {
        "slug": "yuki-japanese",
        "name": "Yuki",
        "description": "Patient Japanese tutor who makes kanji and grammar fun",
        "avatar_url": "/personas/yuki.png",
        "language": Language.JAPANESE,
        "system_prompt": (
            "You are Yuki, a patient Japanese tutor. "
            "Break down kanji, explain grammar patterns clearly, and include cultural context."
        ),
    },
    {
        "slug": "hans-german",
        "name": "Hans",
        "description": "Direct and efficient German tutor from Berlin",
        "avatar_url": "/personas/hans.png",
        "language": Language.GERMAN,
        "system_prompt": (
            "You are Hans, a direct German tutor from Berlin. "
            "Focus on precise grammar, compound words, and practical vocabulary."
        ),
    },
]


class PersonaService:
    async def seed_personas(self, session: AsyncSession) -> None:
        for data in PERSONAS:
            existing = await session.execute(select(Persona).where(Persona.slug == data["slug"]))
            if existing.scalar_one_or_none():
                continue
            session.add(Persona(**data))

    async def get_default(self, session: AsyncSession) -> Persona:
        result = await session.execute(select(Persona).where(Persona.is_default == True).limit(1))
        persona = result.scalar_one_or_none()
        if persona:
            return persona
        await self.seed_personas(session)
        await session.flush()
        result = await session.execute(select(Persona).where(Persona.is_default == True).limit(1))
        return result.scalar_one()

    async def get_by_slug(self, session: AsyncSession, slug: str) -> Persona | None:
        result = await session.execute(select(Persona).where(Persona.slug == slug, Persona.is_active == True))
        return result.scalar_one_or_none()

    async def list_active(self, session: AsyncSession, language: Language | None = None) -> list[Persona]:
        stmt = select(Persona).where(Persona.is_active == True, Persona.is_default == False)
        if language:
            stmt = stmt.where(Persona.language == language)
        stmt = stmt.order_by(Persona.name)
        result = await session.execute(stmt)
        return list(result.scalars().all())


persona_service = PersonaService()
