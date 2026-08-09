"""Recon monitor: scheduled checks and notifications."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from database.models import ReconEvent, ReconSource
from services.recon_providers import fetch_source_content
from services.recon_service import SOURCE_TYPE_LABELS, VERDICT_LABELS, recon_service
from services.recon_verifier import recon_verifier

if TYPE_CHECKING:
    from aiogram import Bot
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

logger = logging.getLogger(__name__)


def _source_label(source: ReconSource) -> str:
    if source.label:
        return source.label
    return source.url_or_handle[:80]


def format_event_message(source: ReconSource, event: ReconEvent) -> str:
    verdict = VERDICT_LABELS.get(event.verdict or "info", event.verdict or "ℹ️")
    conf = f"{int((event.confidence or 0) * 100)}%" if event.confidence is not None else "—"
    type_label = SOURCE_TYPE_LABELS.get(source.source_type, source.source_type)
    lines = [
        "🔍 <b>Разведка и Вериф</b>",
        f"{type_label}: <b>{_source_label(source)}</b>",
        f"{verdict} ({conf})",
    ]
    if event.title:
        lines.append(f"📌 {event.title}")
    if event.summary:
        lines.append(event.summary)
    if event.excerpt:
        excerpt = event.excerpt[:400] + ("…" if len(event.excerpt) > 400 else "")
        lines.append(f"\n<i>{excerpt}</i>")
    return "\n".join(lines)


class ReconMonitor:
    def __init__(self, bot: "Bot", session_factory: "async_sessionmaker[AsyncSession]"):
        self.bot = bot
        self.session_factory = session_factory

    async def check_source(self, source: ReconSource, *, force: bool = False) -> ReconEvent | None:
        now = datetime.now(ZoneInfo("UTC"))
        if not force and source.last_checked_at:
            delta = now - source.last_checked_at.replace(tzinfo=ZoneInfo("UTC"))
            if delta < timedelta(minutes=source.check_interval_min or 60):
                return None

        fetched = await fetch_source_content(source.source_type, source.url_or_handle)
        async with self.session_factory() as session:
            db_source = await session.get(ReconSource, source.id)
            if not db_source:
                return None
            db_source.last_checked_at = now

            if not fetched:
                await session.commit()
                return None

            if not db_source.last_content_hash:
                db_source.last_content_hash = fetched.content_hash
                db_source.last_preview = fetched.content[:500]
                await session.commit()
                return None

            changed = db_source.last_content_hash != fetched.content_hash
            db_source.last_content_hash = fetched.content_hash
            db_source.last_preview = fetched.content[:500]

            if not changed and not force:
                await session.commit()
                return None

            verification = None
            if db_source.verify_enabled:
                verification = await recon_verifier.verify_change(
                    source_label=_source_label(db_source),
                    old_preview=source.last_preview,
                    new_content=fetched.content,
                    source_type=db_source.source_type,
                )
                if verification and not verification.notify:
                    await session.commit()
                    return None

            event = ReconEvent(
                source_id=db_source.id,
                title=fetched.title,
                excerpt=fetched.content[:1000],
                verdict=verification.verdict if verification else "info",
                confidence=verification.confidence if verification else None,
                summary=verification.summary if verification else "Обновление в источнике.",
                notified=False,
            )
            session.add(event)
            await session.commit()
            await session.refresh(event)
            return event

    async def run_checks(self) -> None:
        async with self.session_factory() as session:
            result = await session.execute(
                select(ReconSource)
                .where(ReconSource.enabled == True)  # noqa: E712
                .options(selectinload(ReconSource.user))
            )
            sources = result.scalars().all()

        for source in sources:
            try:
                event = await self.check_source(source)
                if event and source.user:
                    await self._notify_user(source.user.telegram_id, source, event)
            except Exception:
                logger.exception("Recon check failed for source %s", source.id)

    async def _notify_user(self, telegram_id: int, source: ReconSource, event: ReconEvent) -> None:
        try:
            text = format_event_message(source, event)
            await self.bot.send_message(telegram_id, text, parse_mode="HTML")
            async with self.session_factory() as session:
                db_event = await session.get(ReconEvent, event.id)
                if db_event:
                    db_event.notified = True
                    await session.commit()
        except Exception:
            logger.exception("Failed to notify user %s about recon event", telegram_id)


_recon_monitor: ReconMonitor | None = None


def init_recon_monitor(bot: "Bot", session_factory: "async_sessionmaker[AsyncSession]") -> ReconMonitor:
    global _recon_monitor
    _recon_monitor = ReconMonitor(bot, session_factory)
    return _recon_monitor


def get_recon_monitor() -> ReconMonitor | None:
    return _recon_monitor
