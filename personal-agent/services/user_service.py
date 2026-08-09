from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database.models import Task, TaskStatus, User


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
        try:
            ZoneInfo(timezone)
        except ZoneInfoNotFoundError:
            return False
        user.timezone = timezone
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
    ) -> Task:
        task = Task(
            user_id=user.id,
            title=title,
            description=description,
            due_at=due_at,
            notify_message=notify_message,
            notify_call=notify_call,
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

    async def get_pending(self, session: AsyncSession, user: User, task_id: int) -> Task | None:
        result = await session.execute(
            select(Task).where(
                Task.id == task_id,
                Task.user_id == user.id,
                Task.status == TaskStatus.PENDING,
            )
        )
        return result.scalar_one_or_none()

    async def mark_done(self, session: AsyncSession, task: Task) -> None:
        task.status = TaskStatus.DONE

    async def cancel(self, session: AsyncSession, task: Task) -> None:
        task.status = TaskStatus.CANCELLED

    async def mark_reminded(self, session: AsyncSession, task: Task) -> None:
        task.reminded_at = datetime.now(ZoneInfo("UTC"))


user_service = UserService()
task_service = TaskService()
