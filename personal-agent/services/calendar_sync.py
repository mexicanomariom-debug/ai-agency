from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from database.session import async_session_factory
from services.google_calendar import google_calendar_service
from services.user_service import task_service

logger = logging.getLogger(__name__)


async def sync_pending_tasks_to_calendar(session: AsyncSession, user: User) -> tuple[int, int]:
    """Sync pending tasks without google_event_id. Returns (synced, failed)."""
    if not user.google_calendar_enabled or not user.google_refresh_token:
        return 0, 0

    tasks = await task_service.list_pending(session, user)
    synced = 0
    failed = 0
    for task in tasks:
        if task.google_event_id:
            continue
        event_id = await google_calendar_service.create_event(user, task)
        if event_id:
            task.google_event_id = event_id
            synced += 1
        else:
            failed += 1
            logger.warning("Calendar sync failed for task %s user %s", task.id, user.telegram_id)
    return synced, failed


async def sync_user_calendar_by_telegram_id(telegram_id: int) -> tuple[int, int]:
    async with async_session_factory() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if not user:
            return 0, 0
        synced, failed = await sync_pending_tasks_to_calendar(session, user)
        await session.commit()
        return synced, failed
