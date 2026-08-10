"""CRUD and helpers for recon sources."""

from __future__ import annotations

import json

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

_MAX_SEEN_IDS = 120


def parse_seen_item_ids(raw: str | None) -> set[str]:
    if not raw:
        return set()
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return {str(x) for x in data if x}
    except json.JSONDecodeError:
        pass
    return set()


def dump_seen_item_ids(ids: set[str]) -> str:
    ordered = list(ids)
    if len(ordered) > _MAX_SEEN_IDS:
        ordered = ordered[-_MAX_SEEN_IDS:]
    return json.dumps(ordered, ensure_ascii=False)


def keyword_prefilter(text: str, keywords: str | None) -> bool:
    if not keywords or not keywords.strip():
        return True
    lowered = text.lower()
    for kw in keywords.split(","):
        kw = kw.strip().lower()
        if kw and kw in lowered:
            return True
    return False


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
        filter_query: str | None = None,
        keywords: str | None = None,
        check_interval_min: int = 60,
    ) -> ReconSource:
        source = ReconSource(
            user_id=user.id,
            source_type=source_type,
            url_or_handle=url_or_handle.strip(),
            label=label.strip() if label else None,
            filter_query=filter_query.strip() if filter_query else None,
            keywords=keywords.strip() if keywords else None,
            check_interval_min=check_interval_min,
            enabled=True,
            verify_enabled=True,
        )
        session.add(source)
        await session.flush()
        return source

    async def update_filter(
        self,
        session: AsyncSession,
        user: User,
        source_id: int,
        *,
        filter_query: str | None,
        keywords: str | None = None,
    ) -> ReconSource | None:
        source = await self.get_source(session, user, source_id)
        if not source:
            return None
        source.filter_query = filter_query.strip() if filter_query else None
        if keywords is not None:
            source.keywords = keywords.strip() if keywords.strip() else None
        return source

    async def update_settings(
        self,
        session: AsyncSession,
        user: User,
        source_id: int,
        *,
        verify_enabled: bool | None = None,
        check_interval_min: int | None = None,
        keywords: str | None = None,
    ) -> ReconSource | None:
        source = await self.get_source(session, user, source_id)
        if not source:
            return None
        if verify_enabled is not None:
            source.verify_enabled = verify_enabled
        if check_interval_min is not None:
            source.check_interval_min = max(15, min(360, check_interval_min))
        if keywords is not None:
            source.keywords = keywords.strip() if keywords.strip() else None
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

    async def recent_events_for_source(
        self,
        session: AsyncSession,
        user: User,
        source_id: int,
        *,
        limit: int = 10,
    ) -> list[ReconEvent]:
        result = await session.execute(
            select(ReconEvent)
            .join(ReconSource)
            .where(ReconSource.user_id == user.id, ReconSource.id == source_id)
            .options(selectinload(ReconEvent.source))
            .order_by(ReconEvent.detected_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_event(self, session: AsyncSession, user: User, event_id: int) -> ReconEvent | None:
        result = await session.execute(
            select(ReconEvent)
            .join(ReconSource)
            .where(ReconSource.user_id == user.id, ReconEvent.id == event_id)
            .options(selectinload(ReconEvent.source))
        )
        return result.scalar_one_or_none()


recon_service = ReconService()
