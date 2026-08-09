from __future__ import annotations

import asyncio
import logging

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Task, TaskStatus, User
from database.session import async_session_factory
from services.google_calendar import google_calendar_service
from services.user_service import task_service

logger = logging.getLogger(__name__)

SYNC_OVERALL_TIMEOUT_SEC = 90


async def count_calendar_sync_state(session: AsyncSession, user: User) -> tuple[int, int, int]:
    """Return (pending_total, linked, unlinked)."""
    result = await session.execute(
        select(
            func.count(Task.id),
            func.count(Task.google_event_id),
        ).where(
            Task.user_id == user.id,
            Task.status == TaskStatus.PENDING,
        )
    )
    total, linked = result.one()
    return total, linked, total - linked


async def sync_pending_tasks_to_calendar(
    session: AsyncSession,
    user: User,
    *,
    resync: bool = False,
) -> tuple[int, int]:
    """Sync pending tasks to Google Calendar. Returns (synced, failed)."""
    if not user.google_refresh_token:
        return 0, 0

    creds = await google_calendar_service._credentials_async(user)
    if not creds:
        logger.warning("Calendar sync: no Google credentials for user %s", user.telegram_id)
        return 0, 0

    tasks = await task_service.list_pending(session, user)
    synced = 0
    failed = 0
    for task in tasks:
        if task.google_event_id:
            if not resync:
                continue
            await google_calendar_service.delete_event(user, task.google_event_id, creds=creds)
            task.google_event_id = None

        event_id = await google_calendar_service.create_event(user, task, creds=creds)
        if event_id:
            task.google_event_id = event_id
            synced += 1
        else:
            failed += 1
            logger.warning("Calendar sync failed for task %s user %s", task.id, user.telegram_id)
    return synced, failed


async def sync_user_calendar_by_telegram_id(
    telegram_id: int,
    *,
    resync: bool = False,
) -> tuple[int, int]:
    async def _run() -> tuple[int, int]:
        async with async_session_factory() as session:
            result = await session.execute(select(User).where(User.telegram_id == telegram_id))
            user = result.scalar_one_or_none()
            if not user:
                return 0, 0
            synced, failed = await sync_pending_tasks_to_calendar(session, user, resync=resync)
            await session.commit()
            return synced, failed

    try:
        return await asyncio.wait_for(_run(), timeout=SYNC_OVERALL_TIMEOUT_SEC)
    except TimeoutError:
        logger.error("Calendar sync timed out for telegram_id=%s", telegram_id)
        raise
