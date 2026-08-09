from __future__ import annotations

import re
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database.models import Task, TaskStatus, User
from services.time_utils import resolve_timezone
from services.translator import LANGUAGES, normalize_lang_code, translator_service

PHONE_RE = re.compile(r"^\+[1-9]\d{7,14}$")


class UserService:
    async def get_or_create(
        self,
        session: AsyncSession,
        *,
        telegram_id: int,
        username: str | None,
        first_name: str | None,
    ) -> User:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if user:
            user.username = username
            user.first_name = first_name
            return user

        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            timezone=settings.default_timezone,
        )
        session.add(user)
        await session.flush()
        return user

    async def set_timezone(self, session: AsyncSession, user: User, timezone: str) -> bool:
        resolved = resolve_timezone(timezone)
        if not resolved:
            return False
        user.timezone = resolved
        return True

    def normalize_phone(self, phone: str) -> str | None:
        cleaned = re.sub(r"[\s\-()]", "", phone.strip())
        if cleaned.startswith("8") and len(cleaned) == 11:
            cleaned = "+7" + cleaned[1:]
        if not cleaned.startswith("+"):
            cleaned = "+" + cleaned
        if PHONE_RE.match(cleaned):
            return cleaned
        return None

    async def set_phone(self, session: AsyncSession, user: User, phone: str) -> bool:
        normalized = self.normalize_phone(phone)
        if not normalized:
            return False
        user.phone_number = normalized
        return True

    async def set_translate_lang(self, session: AsyncSession, user: User, lang: str) -> bool:
        resolved = translator_service.resolve_alias(lang) or normalize_lang_code(lang)
        if resolved not in LANGUAGES:
            return False
        user.translate_target_lang = resolved
        return True


class TaskService:
    async def create(
        self,
        session: AsyncSession,
        *,
        user: User,
        title: str,
        due_at: datetime,
        description: str | None = None,
        notify_message: bool = True,
        notify_call: bool = False,
        notify_phone: bool = False,
    ) -> Task:
        task = Task(
            user_id=user.id,
            title=title,
            description=description,
            due_at=due_at,
            notify_message=notify_message,
            notify_call=notify_call,
            notify_phone=notify_phone,
            status=TaskStatus.PENDING,
        )
        session.add(task)
        await session.flush()
        return task

    async def list_pending(self, session: AsyncSession, user: User) -> list[Task]:
        result = await session.execute(
            select(Task)
            .where(Task.user_id == user.id, Task.status == TaskStatus.PENDING)
            .order_by(Task.due_at)
        )
        return list(result.scalars().all())

    async def list_today(self, session: AsyncSession, user: User) -> list[Task]:
        tz = ZoneInfo(user.timezone)
        now = datetime.now(tz)
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start.replace(hour=23, minute=59, second=59)
        start_utc = start.astimezone(ZoneInfo("UTC"))
        end_utc = end.astimezone(ZoneInfo("UTC"))
        result = await session.execute(
            select(Task)
            .where(
                Task.user_id == user.id,
                Task.status == TaskStatus.PENDING,
                Task.due_at >= start_utc,
                Task.due_at <= end_utc,
            )
            .order_by(Task.due_at)
        )
        return list(result.scalars().all())

    async def get_pending(self, session: AsyncSession, user: User, task_id: int) -> Task | None:
        result = await session.execute(
            select(Task).where(
                Task.id == task_id,
                Task.user_id == user.id,
                Task.status == TaskStatus.PENDING,
            )
        )
        return result.scalar_one_or_none()

    async def get(self, session: AsyncSession, user: User, task_id: int) -> Task | None:
        result = await session.execute(
            select(Task).where(Task.id == task_id, Task.user_id == user.id)
        )
        return result.scalar_one_or_none()

    async def list_finished(self, session: AsyncSession, user: User, *, limit: int = 20) -> list[Task]:
        result = await session.execute(
            select(Task)
            .where(
                Task.user_id == user.id,
                Task.status.in_((TaskStatus.DONE, TaskStatus.CANCELLED)),
            )
            .order_by(Task.id.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def mark_done(self, session: AsyncSession, task: Task) -> None:
        task.status = TaskStatus.DONE

    async def cancel(self, session: AsyncSession, task: Task) -> None:
        task.status = TaskStatus.CANCELLED

    async def restore(self, session: AsyncSession, task: Task) -> None:
        task.status = TaskStatus.PENDING
        task.reminded_at = None

    async def mark_reminded(self, session: AsyncSession, task: Task) -> None:
        task.reminded_at = datetime.now(ZoneInfo("UTC"))


user_service = UserService()
task_service = TaskService()
