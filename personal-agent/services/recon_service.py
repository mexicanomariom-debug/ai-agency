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
    "twitter": "🐦 Twitter/X",
    "facebook": "📘 Facebook",
    "whatsapp": "💬 WhatsApp",
    "econ_calendar": "📊 Эко-календарь",
}

ITEM_BASED_SOURCE_TYPES = frozenset(
    {"telegram", "tiktok", "instagram", "twitter", "facebook", "whatsapp"}
)

MEDIA_SOURCE_TYPES = frozenset({"tiktok", "instagram"})

RECON_TYPE_ALIASES = {
    "website": "website",
    "сайт": "website",
    "rss": "website",
    "telegram": "telegram",
    "телеграм": "telegram",
    "tg": "telegram",
    "tiktok": "tiktok",
    "тикток": "tiktok",
    "tt": "tiktok",
    "instagram": "instagram",
    "инстаграм": "instagram",
    "ig": "instagram",
    "twitter": "twitter",
    "твиттер": "twitter",
    "x": "twitter",
    "facebook": "facebook",
    "фейсбук": "facebook",
    "fb": "facebook",
    "whatsapp": "whatsapp",
    "wa": "whatsapp",
    "econ": "econ_calendar",
    "calendar": "econ_calendar",
    "календарь": "econ_calendar",
}


def resolve_recon_type_name(name: str) -> str | None:
    return RECON_TYPE_ALIASES.get(name.strip().lower())

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


def normalize_source_key(source_type: str, url_or_handle: str) -> str:
    value = (url_or_handle or "").strip().lower()
    if source_type == "telegram":
        from services.recon_providers import _normalize_telegram_handle

        return f"telegram:{_normalize_telegram_handle(value)}"
    if source_type == "tiktok":
        from services.recon_social import normalize_tiktok_handle

        return f"tiktok:{normalize_tiktok_handle(value)}"
    if source_type == "twitter":
        from services.recon_social import normalize_twitter_handle

        return f"twitter:{normalize_twitter_handle(value)}"
    if source_type == "instagram":
        from services.recon_social import normalize_instagram_handle

        return f"instagram:{normalize_instagram_handle(value)}"
    if source_type == "facebook":
        from services.recon_social import normalize_facebook_page

        return f"facebook:{normalize_facebook_page(value)}"
    if source_type == "whatsapp":
        from services.recon_social import normalize_whatsapp_channel

        return f"whatsapp:{normalize_whatsapp_channel(value)}"
    if source_type == "econ_calendar":
        return "econ_calendar:ff_calendar_thisweek"
    return f"{source_type}:{value.rstrip('/')}"


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

    async def find_duplicate(
        self,
        session: AsyncSession,
        user: User,
        *,
        source_type: str,
        url_or_handle: str,
    ) -> ReconSource | None:
        key = normalize_source_key(source_type, url_or_handle)
        for source in await self.list_sources(session, user):
            if normalize_source_key(source.source_type, source.url_or_handle) == key:
                return source
        return None

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

    async def update_source_type(
        self,
        session: AsyncSession,
        user: User,
        source_id: int,
        *,
        source_type: str,
        url_or_handle: str | None = None,
        label: str | None = None,
    ) -> ReconSource | None:
        source = await self.get_source(session, user, source_id)
        if not source:
            return None
        source.source_type = source_type
        if url_or_handle is not None:
            source.url_or_handle = url_or_handle.strip()
        if label is not None:
            source.label = label.strip() or None
        source.last_content_hash = None
        source.last_preview = None
        source.last_seen_item_ids = None
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
