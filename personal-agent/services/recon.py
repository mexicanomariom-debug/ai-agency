"""Recon monitor: scheduled checks and notifications."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from database.models import ReconEvent, ReconSource
from services.recon_providers import ContentItem, FetchResult, fetch_source_content
from services.recon_service import (
    ITEM_BASED_SOURCE_TYPES,
    MEDIA_SOURCE_TYPES,
    SOURCE_TYPE_LABELS,
    VERDICT_LABELS,
    dump_seen_item_ids,
    keyword_prefilter,
    parse_seen_item_ids,
    recon_service,
)
from services.recon_verifier import recon_verifier

if TYPE_CHECKING:
    from aiogram import Bot
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

logger = logging.getLogger(__name__)

_MAX_NEW_ITEMS_PER_CHECK = 3


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
    if source.filter_query:
        lines.append(f"🎯 {source.filter_query[:120]}")
    if event.title:
        lines.append(f"📌 {event.title}")
    if event.summary:
        lines.append(event.summary)
    if event.excerpt:
        excerpt = event.excerpt[:400] + ("…" if len(event.excerpt) > 400 else "")
        lines.append(f"\n<i>{excerpt}</i>")
    if getattr(event, "translated_excerpt", None):
        lines.append(f"\n🌐 {event.translated_excerpt[:400]}")
    if getattr(event, "media_url", None):
        lines.append(f"\n🔗 {event.media_url[:200]}")
    return "\n".join(lines)


class ReconMonitor:
    def __init__(self, bot: "Bot", session_factory: "async_sessionmaker[AsyncSession]"):
        self.bot = bot
        self.session_factory = session_factory

    async def check_source(
        self, source: ReconSource, *, force: bool = False
    ) -> ReconEvent | list[ReconEvent] | None:
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
            if source.user:
                db_source.user = source.user
            db_source.last_checked_at = now

            if not fetched:
                await session.commit()
                return None

            db_source.last_preview = fetched.content[:500]

            use_items = bool(db_source.filter_query) or db_source.source_type in ITEM_BASED_SOURCE_TYPES
            if use_items:
                events = await self._check_filtered_items(session, db_source, fetched)
                await session.commit()
                if not events:
                    return None
                return events[0] if len(events) == 1 else events

            event = await self._check_aggregate_change(session, db_source, fetched, force=force)
            await session.commit()
            return event

    async def _check_aggregate_change(
        self,
        session: "AsyncSession",
        db_source: ReconSource,
        fetched: FetchResult,
        *,
        force: bool,
    ) -> ReconEvent | None:
        if not db_source.last_content_hash:
            db_source.last_content_hash = fetched.content_hash
            return None

        changed = db_source.last_content_hash != fetched.content_hash
        db_source.last_content_hash = fetched.content_hash

        if not changed and not force:
            return None

        old_preview = db_source.last_preview
        verification = None
        if db_source.verify_enabled:
            verification = await recon_verifier.verify_change(
                source_label=_source_label(db_source),
                old_preview=old_preview,
                new_content=fetched.content,
                source_type=db_source.source_type,
            )
            if verification and not verification.notify:
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
        await session.flush()
        return event

    async def _check_filtered_items(
        self,
        session: "AsyncSession",
        db_source: ReconSource,
        fetched: FetchResult,
    ) -> list[ReconEvent]:
        from services.recon_media import enrich_content_item

        seen = parse_seen_item_ids(db_source.last_seen_item_ids)
        items = fetched.items or []
        new_items = [item for item in items if item.item_id not in seen]

        if not seen and items:
            for item in items:
                seen.add(item.item_id)
            db_source.last_seen_item_ids = dump_seen_item_ids(seen)
            return []

        if not new_items:
            return []

        user = db_source.user
        translate_lang = getattr(user, "translate_target_lang", "en") if user else "en"
        if not user and db_source.user_id:
            from database.models import User

            user = await session.get(User, db_source.user_id)
            if user:
                translate_lang = user.translate_target_lang or "en"
        download_media = db_source.source_type in MEDIA_SOURCE_TYPES

        events: list[ReconEvent] = []
        ai_calls = 0
        for item in new_items:
            seen.add(item.item_id)
            if not keyword_prefilter(item.text, db_source.keywords):
                continue

            if db_source.filter_query:
                if ai_calls >= _MAX_NEW_ITEMS_PER_CHECK:
                    break
                interest = await recon_verifier.matches_interest(
                    filter_query=db_source.filter_query or "",
                    text=item.text,
                    source_label=_source_label(db_source),
                )
                ai_calls += 1
                if not interest.relevant:
                    continue

            working_item = item
            if download_media or item.media_type in ("video", "photo"):
                try:
                    working_item = await enrich_content_item(
                        item,
                        user_translate_lang=translate_lang,
                        download_media=download_media,
                    )
                except Exception:
                    logger.exception("Media enrich failed for item %s", item.item_id)

            verification = None
            if db_source.verify_enabled:
                if ai_calls >= _MAX_NEW_ITEMS_PER_CHECK:
                    break
                verification = await recon_verifier.verify_change(
                    source_label=_source_label(db_source),
                    old_preview=None,
                    new_content=working_item.text,
                    source_type=db_source.source_type,
                )
                ai_calls += 1
                if verification and not verification.notify:
                    continue

            event = ReconEvent(
                source_id=db_source.id,
                title=working_item.title or fetched.title,
                excerpt=working_item.text[:1000],
                verdict=verification.verdict if verification else "info",
                confidence=verification.confidence if verification else None,
                summary=verification.summary if verification else "Новый пост в источнике.",
                notified=False,
                media_url=working_item.page_url,
                media_type=working_item.media_type,
                translated_excerpt=working_item.translated_text,
            )
            session.add(event)
            await session.flush()
            if working_item.media_path:
                event._media_path = working_item.media_path  # type: ignore[attr-defined]
            events.append(event)

        db_source.last_seen_item_ids = dump_seen_item_ids(seen)
        return events

    async def run_checks(self) -> None:
        logger.info("Recon monitor: starting scheduled checks")
        async with self.session_factory() as session:
            result = await session.execute(
                select(ReconSource)
                .where(ReconSource.enabled == True)  # noqa: E712
                .options(selectinload(ReconSource.user))
            )
            sources = result.scalars().all()

        for source in sources:
            try:
                result = await self.check_source(source)
                if not result or not source.user:
                    continue
                events = result if isinstance(result, list) else [result]
                for event in events:
                    media_path = getattr(event, "_media_path", None)
                    await self._notify_user(
                        source.user.telegram_id,
                        source,
                        event,
                        media_path=media_path,
                    )
            except Exception:
                logger.exception("Recon check failed for source %s", source.id)
        logger.info("Recon monitor: scheduled checks finished (%s sources)", len(sources))

    async def _notify_user(
        self,
        telegram_id: int,
        source: ReconSource,
        event: ReconEvent,
        *,
        media_path: str | None = None,
    ) -> None:
        from aiogram.types import FSInputFile
        from services.recon_media import cleanup_media_item
        from services.recon_providers import ContentItem

        try:
            text = format_event_message(source, event)
            sent = False
            if media_path:
                path = media_path
                if event.media_type == "video":
                    await self.bot.send_video(
                        telegram_id,
                        FSInputFile(path),
                        caption=text[:1024],
                        parse_mode="HTML",
                    )
                    sent = True
                elif event.media_type == "photo":
                    await self.bot.send_photo(
                        telegram_id,
                        FSInputFile(path),
                        caption=text[:1024],
                        parse_mode="HTML",
                    )
                    sent = True
            if not sent:
                await self.bot.send_message(telegram_id, text, parse_mode="HTML")
            async with self.session_factory() as session:
                db_event = await session.get(ReconEvent, event.id)
                if db_event:
                    db_event.notified = True
                    await session.commit()
        except Exception:
            logger.exception("Failed to notify user %s about recon event", telegram_id)
        finally:
            if media_path:
                cleanup_media_item(ContentItem(item_id="x", text="", media_path=media_path))


_recon_monitor: ReconMonitor | None = None


def init_recon_monitor(bot: "Bot", session_factory: "async_sessionmaker[AsyncSession]") -> ReconMonitor:
    global _recon_monitor
    _recon_monitor = ReconMonitor(bot, session_factory)
    return _recon_monitor


def get_recon_monitor() -> ReconMonitor | None:
    return _recon_monitor
