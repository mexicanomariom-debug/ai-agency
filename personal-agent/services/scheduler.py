from __future__ import annotations

import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from config import settings
from database.models import Task, TaskStatus
from services.notifier import Notifier

logger = logging.getLogger(__name__)

JOB_PREFIX = "task_reminder_"


class ReminderScheduler:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession], notifier: Notifier) -> None:
        self._session_factory = session_factory
        self._notifier = notifier
        self._scheduler = AsyncIOScheduler(
            jobstores={"default": MemoryJobStore()},
            timezone="UTC",
        )

    def start(self) -> None:
        if not self._scheduler.running:
            self._scheduler.start()
            logger.info("Reminder scheduler started")

    def shutdown(self) -> None:
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)

    async def bootstrap(self) -> None:
        async with self._session_factory() as session:
            now = datetime.now(ZoneInfo("UTC"))
            result = await session.execute(
                select(Task)
                .options(selectinload(Task.user))
                .where(Task.status == TaskStatus.PENDING, Task.due_at > now)
            )
            tasks = result.scalars().all()
            for task in tasks:
                self.schedule_task(task.id, task.due_at)
            logger.info("Scheduled %s pending reminders", len(tasks))

    def schedule_task(self, task_id: int, due_at: datetime) -> None:
        job_id = f"{JOB_PREFIX}{task_id}"
        due_utc = due_at.astimezone(ZoneInfo("UTC")) if due_at.tzinfo else due_at.replace(tzinfo=ZoneInfo("UTC"))
        now = datetime.now(ZoneInfo("UTC"))

        # Не слать напоминание сразу после создания (кнопки «Готово» / «15 мин» только в срок)
        if due_utc <= now:
            logger.info("Task %s due in the past (%s), reminder not scheduled", task_id, due_utc)
            return

        self._scheduler.add_job(
            self._fire_reminder,
            trigger="date",
            run_date=due_utc,
            id=job_id,
            replace_existing=True,
            args=[task_id],
        )

    def cancel_task(self, task_id: int) -> None:
        job_id = f"{JOB_PREFIX}{task_id}"
        if self._scheduler.get_job(job_id):
            self._scheduler.remove_job(job_id)

    async def _fire_reminder(self, task_id: int) -> None:
        await self._notifier.send_reminder(task_id)


reminder_scheduler: ReminderScheduler | None = None


def init_scheduler(
    session_factory: async_sessionmaker[AsyncSession],
    notifier: Notifier,
) -> ReminderScheduler:
    global reminder_scheduler
    reminder_scheduler = ReminderScheduler(session_factory, notifier)
    return reminder_scheduler
