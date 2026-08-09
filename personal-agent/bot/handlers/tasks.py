from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.copy import (
    INVALID_TIMEZONE,
    NOTIFY_BOTH,
    NOTIFY_CALL,
    NOTIFY_MESSAGE,
    PARSE_FAILED,
    TASK_CANCELLED,
    TASK_CREATED,
    TASK_DONE,
    TASK_ITEM,
    TASK_LIST_EMPTY,
    TASK_LIST_HEADER,
    TASK_NOT_FOUND,
    TIMEZONE_UPDATED,
)
from bot.keyboards.inline import task_actions_keyboard
from services.scheduler import reminder_scheduler
from services.task_parser import task_parser
from services.user_service import task_service, user_service

router = Router()


def _format_notify_types(notify_message: bool, notify_call: bool) -> str:
    if notify_message and notify_call:
        return NOTIFY_BOTH
    if notify_call:
        return NOTIFY_CALL
    return NOTIFY_MESSAGE


def _format_due_at(due_at: datetime, timezone: str) -> str:
    local = due_at.astimezone(ZoneInfo(timezone))
    return local.strftime("%d.%m.%Y %H:%M")


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
                due_at=_format_due_at(task.due_at, user.timezone),
                notify_types=_format_notify_types(task.notify_message, task.notify_call),
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


@router.message(F.text)
async def handle_natural_language(message: Message, session: AsyncSession) -> None:
    if message.text.startswith("/"):
        return

    user = await user_service.get_or_create(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )

    parsed = await task_parser.parse(message.text, user.timezone)
    if not parsed.tasks:
        await message.answer(PARSE_FAILED)
        return

    created_lines: list[str] = []
    for item in parsed.tasks:
        task = await task_service.create(
            session,
            user=user,
            title=item.title,
            description=item.description,
            due_at=item.due_at,
            notify_message=item.notify_message,
            notify_call=item.notify_call,
        )
        if reminder_scheduler:
            reminder_scheduler.schedule_task(task.id, task.due_at)

        created_lines.append(
            TASK_CREATED.format(
                task_id=task.id,
                title=task.title,
                due_at=_format_due_at(task.due_at, user.timezone),
                notify_types=_format_notify_types(task.notify_message, task.notify_call),
            )
        )

    reply = parsed.reply or "\n\n".join(created_lines)
    last_task_id = None
    if parsed.tasks:
        result_tasks = await task_service.list_pending(session, user)
        if result_tasks:
            last_task_id = result_tasks[-1].id

    keyboard = task_actions_keyboard(last_task_id) if last_task_id else None
    await message.answer(reply, reply_markup=keyboard)
