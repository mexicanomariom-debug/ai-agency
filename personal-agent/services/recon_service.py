"""CRUD and helpers for recon sources."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models import ReconEvent, ReconSource, User

SOURCE_TYPE_LABELS = {
    "website": "🌐 Сайт / RSS",
    "telegram": "📢 Telegram",
    "instagram": "📸 Instagram",
    "tiktok": "🎵 TikTok",
    "econ_calendar": "📊 Эко-календарь",
}

VERDICT_LABELS = {
    "confirmed": "✅ Подтверждено",
    "unconfirmed": "⚠️ Не подтверждено",
    "contradicted": "❌ Противоречит фактам",
    "unknown": "❓ Неизвестно",
    "info": "ℹ️ Информация",
}


class ReconService:
    async def list_sources(self, session: AsyncSession, user: User) -> list[ReconSource]:
        result = await session.execute(
            select(ReconSource)
            .where(ReconSource.user_id == user.id)
            .order_by(ReconSource.id.desc())
        )
        return list(result.scalars().all())

    async def get_source(self, session: AsyncSession, user: User, source_id: int) -> ReconSource | None:
        result = await session.execute(
            select(ReconSource).where(ReconSource.id == source_id, ReconSource.user_id == user.id)
        )
        return result.scalar_one_or_none()

    async def add_source(
        self,
        session: AsyncSession,
        user: User,
        *,
        source_type: str,
        url_or_handle: str,
        label: str | None = None,
        check_interval_min: int = 60,
    ) -> ReconSource:
        source = ReconSource(
            user_id=user.id,
            source_type=source_type,
            url_or_handle=url_or_handle.strip(),
            label=label.strip() if label else None,
            check_interval_min=check_interval_min,
            enabled=True,
            verify_enabled=True,
        )
        session.add(source)
        await session.flush()
        return source

    async def delete_source(self, session: AsyncSession, user: User, source_id: int) -> bool:
        source = await self.get_source(session, user, source_id)
        if not source:
            return False
        await session.delete(source)
        return True

    async def recent_events(self, session: AsyncSession, user: User, *, limit: int = 5) -> list[ReconEvent]:
        result = await session.execute(
            select(ReconEvent)
            .join(ReconSource)
            .where(ReconSource.user_id == user.id)
            .options(selectinload(ReconEvent.source))
            .order_by(ReconEvent.detected_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


recon_service = ReconService()
