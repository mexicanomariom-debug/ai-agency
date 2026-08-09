from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import JournalEntry, User


class JournalService:
    async def add(
        self,
        session: AsyncSession,
        user: User,
        *,
        kind: str,
        content: str,
        amount: float | None = None,
        currency: str | None = None,
        day_key: str | None = None,
    ) -> JournalEntry:
        if not day_key:
            day_key = datetime.now(ZoneInfo(user.timezone)).date().isoformat()
        entry = JournalEntry(
            user_id=user.id,
            kind=kind,
            content=content,
            amount=amount,
            currency=currency,
            day_key=day_key,
        )
        session.add(entry)
        await session.flush()
        return entry

    async def list_for_day(
        self,
        session: AsyncSession,
        user: User,
        day_key: str,
    ) -> list[JournalEntry]:
        result = await session.execute(
            select(JournalEntry)
            .where(JournalEntry.user_id == user.id, JournalEntry.day_key == day_key)
            .order_by(JournalEntry.created_at)
        )
        return list(result.scalars().all())

    async def list_recent(
        self,
        session: AsyncSession,
        user: User,
        *,
        limit: int = 15,
    ) -> list[JournalEntry]:
        result = await session.execute(
            select(JournalEntry)
            .where(JournalEntry.user_id == user.id)
            .order_by(JournalEntry.created_at.desc())
            .limit(limit)
        )
        return list(reversed(result.scalars().all()))


journal_service = JournalService()
