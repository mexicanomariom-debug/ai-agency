from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Note, User


class NoteService:
    async def create(
        self,
        session: AsyncSession,
        user: User,
        content: str,
        title: str | None = None,
    ) -> Note:
        note = Note(user_id=user.id, title=title, content=content)
        session.add(note)
        await session.flush()
        return note

    async def list_recent(self, session: AsyncSession, user: User, limit: int = 20) -> list[Note]:
        result = await session.execute(
            select(Note).where(Note.user_id == user.id).order_by(Note.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())

    async def get(self, session: AsyncSession, user: User, note_id: int) -> Note | None:
        result = await session.execute(
            select(Note).where(Note.id == note_id, Note.user_id == user.id)
        )
        return result.scalar_one_or_none()

    async def delete(self, session: AsyncSession, note: Note) -> None:
        await session.delete(note)


note_service = NoteService()
