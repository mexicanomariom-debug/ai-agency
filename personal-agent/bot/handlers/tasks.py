from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.copy import (
    INVALID_TIMEZONE,
    TASK_CANCELLED,
    TASK_DONE,
    TASK_ITEM,
    TASK_LIST_EMPTY,
    TASK_LIST_HEADER,
    TASK_NOT_FOUND,
    TASK_TODAY_HEADER,
    TIMEZONE_UPDATED,
)
from services.google_calendar import google_calendar_service
from services.scheduler import reminder_scheduler
from services.task_flow import format_due_at, format_notify_types
from services.user_service import task_service, user_service

router = Router()


@router.message(Command("tasks"))
@router.message(lambda m: m.text == "📋 Мои задачи")
async def cmd_tasks(message: Message, session: AsyncSession) -> None:
    user = await user_service.get_or_create(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )
    tasks = await task_service.list_pending(session, user)
    if not tasks:
        await message.answer(TASK_LIST_EMPTY)
        return

    lines = [TASK_LIST_HEADER.format(count=len(tasks))]
    for task in tasks:
        lines.append(
            TASK_ITEM.format(
                id=task.id,
                title=task.title,
                due_at=format_due_at(task.due_at, user.timezone),
                notify_types=format_notify_types(
                    task.notify_message, task.notify_call, task.notify_phone
                ),
            )
        )
    await message.answer("\n\n".join(lines))


@router.message(lambda m: m.text == "📆 Сегодня")
async def cmd_today(message: Message, session: AsyncSession) -> None:
    user = await user_service.get_or_create(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )
    tasks = await task_service.list_today(session, user)
    if not tasks:
        await message.answer("На сегодня задач нет.")
        return
    lines = [TASK_TODAY_HEADER.format(count=len(tasks))]
    for task in tasks:
        lines.append(
            TASK_ITEM.format(
                id=task.id,
                title=task.title,
                due_at=format_due_at(task.due_at, user.timezone),
                notify_types=format_notify_types(
                    task.notify_message, task.notify_call, task.notify_phone
                ),
            )
        )
    await message.answer("\n\n".join(lines))


@router.message(Command("done"))
async def cmd_done(message: Message, session: AsyncSession) -> None:
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer("Использование: /done <id>")
        return

    task_id = int(parts[1])
    user = await user_service.get_or_create(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )
    task = await task_service.get_pending(session, user, task_id)
    if not task:
        await message.answer(TASK_NOT_FOUND)
        return

    if task.google_event_id and user.google_refresh_token:
        await google_calendar_service.delete_event(user, task.google_event_id)
    await task_service.mark_done(session, task)
    if reminder_scheduler:
        reminder_scheduler.cancel_task(task.id)
    await message.answer(TASK_DONE.format(task_id=task_id))


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, session: AsyncSession) -> None:
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer("Использование: /cancel <id>")
        return

    task_id = int(parts[1])
    user = await user_service.get_or_create(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )
    task = await task_service.get_pending(session, user, task_id)
    if not task:
        await message.answer(TASK_NOT_FOUND)
        return

    if task.google_event_id and user.google_refresh_token:
        await google_calendar_service.delete_event(user, task.google_event_id)
    await task_service.cancel(session, task)
    if reminder_scheduler:
        reminder_scheduler.cancel_task(task.id)
    await message.answer(TASK_CANCELLED.format(task_id=task_id))


@router.message(Command("timezone"))
async def cmd_timezone(message: Message, session: AsyncSession) -> None:
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Использование: /timezone Europe/Moscow")
        return

    user = await user_service.get_or_create(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )
    ok = await user_service.set_timezone(session, user, parts[1].strip())
    if not ok:
        await message.answer(INVALID_TIMEZONE)
        return
    await message.answer(TIMEZONE_UPDATED.format(timezone=user.timezone))


@router.callback_query(F.data.startswith("task:done:"))
async def cb_task_done(callback: CallbackQuery, session: AsyncSession) -> None:
    task_id = int(callback.data.split(":")[-1])
    user = await user_service.get_or_create(
        session,
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name,
    )
    task = await task_service.get_pending(session, user, task_id)
    if not task:
        await callback.answer(TASK_NOT_FOUND, show_alert=True)
        return

    if task.google_event_id and user.google_refresh_token:
        await google_calendar_service.delete_event(user, task.google_event_id)
    await task_service.mark_done(session, task)
    if reminder_scheduler:
        reminder_scheduler.cancel_task(task.id)
    await callback.answer("Готово!")
    await callback.message.edit_reply_markup(reply_markup=None)


@router.callback_query(F.data.startswith("task:cancel:"))
async def cb_task_cancel(callback: CallbackQuery, session: AsyncSession) -> None:
    task_id = int(callback.data.split(":")[-1])
    user = await user_service.get_or_create(
        session,
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name,
    )
    task = await task_service.get_pending(session, user, task_id)
    if not task:
        await callback.answer(TASK_NOT_FOUND, show_alert=True)
        return

    if task.google_event_id and user.google_refresh_token:
        await google_calendar_service.delete_event(user, task.google_event_id)
    await task_service.cancel(session, task)
    if reminder_scheduler:
        reminder_scheduler.cancel_task(task.id)
    await callback.answer("Отменено")
    await callback.message.edit_reply_markup(reply_markup=None)


@router.callback_query(F.data.startswith("task:snooze:"))
async def cb_task_snooze(callback: CallbackQuery, session: AsyncSession) -> None:
    _, _, task_id_str, minutes_str = callback.data.split(":")
    task_id = int(task_id_str)
    minutes = int(minutes_str)

    user = await user_service.get_or_create(
        session,
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name,
    )
    task = await task_service.get_pending(session, user, task_id)
    if not task:
        await callback.answer(TASK_NOT_FOUND, show_alert=True)
        return

    task.due_at = datetime.now(ZoneInfo("UTC")) + timedelta(minutes=minutes)
    if reminder_scheduler:
        reminder_scheduler.schedule_task(task.id, task.due_at)
    await callback.answer(f"Отложено на {minutes} мин")
