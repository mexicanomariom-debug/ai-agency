from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from services.time_utils import format_user_datetime

from bot.copy import (
    CALENDAR_NOT_SYNCED_LINE,
    CALENDAR_SYNCED_LINE,
    NOTIFY_BOTH,
    NOTIFY_CALL,
    NOTIFY_MESSAGE,
    NOTIFY_PHONE,
    NOTIFY_PHONE_CALL,
    TASK_CREATED,
)
from bot.utils.messages import answer_menu
from database.models import Task, User
from services.calendar_sync import update_task_in_calendar
from services.google_calendar import google_calendar_service
from services.scheduler import reminder_scheduler
from services.task_editor import TaskEditChanges
from services.recurrence import recurrence_label
from services.user_service import task_service


def format_notify_types(notify_message: bool, notify_call: bool, notify_phone: bool) -> str:
    parts: list[str] = []
    if notify_message:
        parts.append(NOTIFY_MESSAGE)
    if notify_call:
        parts.append(NOTIFY_CALL)
    if notify_phone:
        parts.append(NOTIFY_PHONE)
    if not parts:
        return NOTIFY_MESSAGE
    if len(parts) == 3:
        return NOTIFY_BOTH + " + " + NOTIFY_PHONE
    if notify_phone and notify_call and not notify_message:
        return NOTIFY_PHONE_CALL
    return " + ".join(parts)


def format_due_at(due_at: datetime, timezone: str) -> str:
    return format_user_datetime(due_at, timezone)


def _recurrence_line(rule: str | None) -> str:
    if not rule:
        return ""
    return f"\n🔁 {recurrence_label(rule)}"


async def complete_task(
    session: AsyncSession,
    user: User,
    task: Task,
) -> tuple[bool, str]:
    """Mark task done or reschedule if recurring. Returns (removed_from_calendar, suffix)."""
    from services.calendar_sync import remove_task_from_calendar, update_task_in_calendar
    from services.recurrence import next_occurrence

    if task.recurrence_rule:
        task.due_at = next_occurrence(task.due_at, task.recurrence_rule, user.timezone)
        task.reminded_at = None
        calendar_updated = await update_task_in_calendar(user, task)
        if reminder_scheduler:
            reminder_scheduler.schedule_task(task.id, task.due_at)
        calendar_line = "\n📅 Время в Google Calendar обновлено." if calendar_updated else ""
        suffix = (
            f"\n🔁 Следующее напоминание: {format_due_at(task.due_at, user.timezone)}"
            + calendar_line
        )
        return False, suffix

    had_event = bool(task.google_event_id)
    removed = await remove_task_from_calendar(user, task)
    await task_service.mark_done(session, task)
    if reminder_scheduler:
        reminder_scheduler.cancel_task(task.id)
    suffix = ""
    if removed:
        suffix = "\n📅 Удалено из Google Calendar"
    elif had_event:
        suffix = "\n⚠️ Не удалось удалить из Google Calendar"
    return removed, suffix


async def create_tasks_from_parsed(
    session: AsyncSession,
    user: User,
    parsed: ParseResult,
) -> list[Task]:
    created: list[Task] = []
    for item in parsed.tasks:
        task = await task_service.create(
            session,
            user=user,
            title=item.title,
            description=item.description,
            due_at=item.due_at,
            notify_message=item.notify_message,
            notify_call=item.notify_call,
            notify_phone=item.notify_phone,
            recurrence_rule=item.recurrence_rule,
        )
        if user.google_calendar_enabled and user.google_refresh_token:
            event_id = await google_calendar_service.create_event(user, task)
            if event_id:
                task.google_event_id = event_id
                task._calendar_synced = True  # type: ignore[attr-defined]
            else:
                task._calendar_synced = False  # type: ignore[attr-defined]
        else:
            task._calendar_synced = None  # type: ignore[attr-defined]

        if reminder_scheduler:
            reminder_scheduler.schedule_task(task.id, task.due_at)
        created.append(task)
    await session.flush()
    return created


def build_task_reply(user: User, tasks: list[Task], parsed: ParseResult) -> str:
    if parsed.reply:
        return parsed.reply
    lines = []
    for task in tasks:
        calendar_line = ""
        synced = getattr(task, "_calendar_synced", None)
        if synced is True:
            calendar_line = CALENDAR_SYNCED_LINE
        elif synced is False:
            calendar_line = CALENDAR_NOT_SYNCED_LINE
        lines.append(
            TASK_CREATED.format(
                task_id=task.id,
                title=task.title,
                due_at=format_due_at(task.due_at, user.timezone),
                notify_types=format_notify_types(
                    task.notify_message, task.notify_call, task.notify_phone
                ),
                recurrence_line=_recurrence_line(task.recurrence_rule),
                calendar_line=calendar_line,
            )
        )
    return "\n\n".join(lines)


async def reply_with_created_tasks(
    message: Message,
    session: AsyncSession,
    user: User,
    parsed: ParseResult,
) -> None:
    tasks = await create_tasks_from_parsed(session, user, parsed)
    reply = build_task_reply(user, tasks, parsed)
    await answer_menu(message, reply)


async def apply_task_edit(
    session: AsyncSession,
    user: User,
    task: Task,
    changes: TaskEditChanges,
) -> Task:
    if changes.title:
        task.title = changes.title
    if changes.due_at:
        task.due_at = changes.due_at
        task.reminded_at = None
    if changes.notify_message is not None:
        task.notify_message = changes.notify_message
    if changes.notify_call is not None:
        task.notify_call = changes.notify_call
    if changes.notify_phone is not None:
        task.notify_phone = changes.notify_phone

    calendar_updated = await update_task_in_calendar(user, task)
    task._calendar_updated = calendar_updated  # type: ignore[attr-defined]

    if reminder_scheduler:
        if task.due_at > datetime.now(ZoneInfo("UTC")):
            reminder_scheduler.schedule_task(task.id, task.due_at)
        else:
            reminder_scheduler.cancel_task(task.id)

    await session.flush()
    return task
