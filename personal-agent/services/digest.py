from __future__ import annotations

import logging
from datetime import datetime

from aiogram import Bot
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from zoneinfo import ZoneInfo

from bot.copy import DIGEST_EMPTY, DIGEST_HEADER, DIGEST_ITEM
from database.models import User
from services.task_flow import format_due_at, format_notify_types
from services.user_service import task_service

logger = logging.getLogger(__name__)


class DigestService:
    def __init__(self, bot: Bot, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._bot = bot
        self._session_factory = session_factory

    async def send_due_digests(self) -> None:
        async with self._session_factory() as session:
            result = await session.execute(select(User).where(User.digest_enabled.is_(True)))
            users = result.scalars().all()
            for user in users:
                try:
                    await self._maybe_send_digest(session, user)
                except Exception:
                    logger.exception("Digest failed for user %s", user.telegram_id)

    async def _maybe_send_digest(self, session: AsyncSession, user: User) -> None:
        tz = ZoneInfo(user.timezone)
        now_local = datetime.now(tz)
        if now_local.hour != user.digest_hour or now_local.minute >= 10:
            return

        today = now_local.date().isoformat()
        if user.digest_last_sent == today:
            return

        tasks = await task_service.list_today(session, user)
        if not tasks:
            text = DIGEST_EMPTY
        else:
            lines = [DIGEST_HEADER.format(count=len(tasks))]
            for task in tasks:
                recurrence = ""
                if task.recurrence_rule:
                    from services.recurrence import recurrence_label

                    recurrence = f" · 🔁 {recurrence_label(task.recurrence_rule)}"
                lines.append(
                    DIGEST_ITEM.format(
                        id=task.id,
                        title=task.title,
                        due_at=format_due_at(task.due_at, user.timezone),
                        notify_types=format_notify_types(
                            task.notify_message, task.notify_call, task.notify_phone
                        ),
                        recurrence=recurrence,
                    )
                )
            text = "\n\n".join(lines)

        await self._bot.send_message(chat_id=user.telegram_id, text=text)
        user.digest_last_sent = today
        await session.commit()


digest_service: DigestService | None = None


def init_digest_service(bot: Bot, session_factory: async_sessionmaker[AsyncSession]) -> DigestService:
    global digest_service
    digest_service = DigestService(bot, session_factory)
    return digest_service
