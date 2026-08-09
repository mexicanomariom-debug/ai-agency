from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram.types import InlineKeyboardMarkup, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.copy import (
    NOTIFY_BOTH,
    NOTIFY_CALL,
    NOTIFY_MESSAGE,
    NOTIFY_PHONE,
    NOTIFY_PHONE_CALL,
    TASK_CREATED,
)
from bot.keyboards.inline import task_actions_keyboard
from database.models import Task, User
from services.google_calendar import google_calendar_service
from services.scheduler import reminder_scheduler
from services.task_parser import ParseResult
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
    local = due_at.astimezone(ZoneInfo(timezone))
    return local.strftime("%d.%m.%Y %H:%M")


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
        )
        if user.google_calendar_enabled and user.google_refresh_token:
            event_id = await google_calendar_service.create_event(user, task)
            if event_id:
                task.google_event_id = event_id

        if reminder_scheduler:
            reminder_scheduler.schedule_task(task.id, task.due_at)
        created.append(task)
    return created


def build_task_reply(user: User, tasks: list[Task], parsed: ParseResult) -> str:
    if parsed.reply:
        return parsed.reply
    lines = []
    for task in tasks:
        lines.append(
            TASK_CREATED.format(
                task_id=task.id,
                title=task.title,
                due_at=format_due_at(task.due_at, user.timezone),
                notify_types=format_notify_types(
                    task.notify_message, task.notify_call, task.notify_phone
                ),
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
    keyboard: InlineKeyboardMarkup | None = None
    if tasks:
        keyboard = task_actions_keyboard(tasks[-1].id)
    await message.answer(reply, reply_markup=keyboard)
