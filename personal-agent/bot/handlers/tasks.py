from __future__ import annotations

from datetime import datetime, timedelta

from services.time_utils import (
    TIMEZONE_TEXT,
    extract_timezone_argument,
    is_standalone_timezone_alias,
    normalize_timezone_text,
)
from zoneinfo import ZoneInfo

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.copy import (
    CALENDAR_REMOVED_LINE,
    CALENDAR_REMOVE_FAILED_LINE,
    INVALID_TIMEZONE,
    TASK_ARCHIVED_EMPTY,
    TASK_ARCHIVED_HEADER,
    TASK_ARCHIVED_ITEM,
    TASK_CANCELLED,
    TASK_DONE,
    TASK_ITEM,
    TASK_LIST_EMPTY,
    TASK_LIST_HEADER,
    TASK_NOT_FOUND,
    TASK_RESTORED,
    TASK_TODAY_HEADER,
    TIMEZONE_HELP_EXAMPLES,
    TIMEZONE_UPDATED,
)
from bot.utils.messages import answer_menu
from config import settings
from database.models import TaskStatus
from services.calendar_sync import remove_task_from_calendar, update_task_in_calendar
from services.google_calendar import google_calendar_service
from services.scheduler import reminder_scheduler
from services.task_flow import format_due_at, format_notify_types
from services.user_service import task_service, user_service

router = Router()


def _calendar_removal_suffix(removed: bool, had_event: bool) -> str:
    if removed:
        return CALENDAR_REMOVED_LINE
    if had_event:
        return CALENDAR_REMOVE_FAILED_LINE
    return ""


async def _apply_timezone_change(
    message: Message,
    session: AsyncSession,
    timezone_input: str,
) -> None:
    user = await user_service.get_or_create(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )
    ok = await user_service.set_timezone(session, user, timezone_input)
    if not ok:
        await answer_menu(message, INVALID_TIMEZONE.format(input=timezone_input))
        return
    await answer_menu(
        message,
        TIMEZONE_UPDATED.format(timezone=user.timezone)
        + "\n\nЕсли подключён Google Calendar — выполните /calendar_resync",
    )


@router.message(Command("timezone"))
async def cmd_timezone(message: Message, session: AsyncSession) -> None:
    timezone_input = extract_timezone_argument(message.text or "")
    if not timezone_input:
        user = await user_service.get_or_create(
            session,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
        )
        now = format_due_at(datetime.now(ZoneInfo("UTC")), user.timezone)
        await answer_menu(
            message,
            f"Сейчас у вас: <b>{user.timezone}</b>\n"
            f"Локальное время: {now}\n"
            f"Сборка бота: <code>{settings.bot_build_id}</code>\n\n"
            "Сменить (у каждого пользователя свой пояс):\n"
            + TIMEZONE_HELP_EXAMPLES,
        )
        return
    await _apply_timezone_change(message, session, timezone_input)


@router.message(F.text.func(lambda text: is_standalone_timezone_alias(text or "")))
async def msg_timezone_alias(message: Message, session: AsyncSession) -> None:
    await _apply_timezone_change(message, session, normalize_timezone_text(message.text or ""))


@router.message(F.text.regexp(TIMEZONE_TEXT))
async def msg_timezone_natural(message: Message, session: AsyncSession) -> None:
    timezone_input = extract_timezone_argument(message.text or "")
    if not timezone_input:
        return
    await _apply_timezone_change(message, session, timezone_input)


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
        await answer_menu(message, TASK_LIST_EMPTY)
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
    await answer_menu(message, "\n\n".join(lines))


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
        await answer_menu(message, "На сегодня задач нет.")
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
    await answer_menu(message, "\n\n".join(lines))


@router.message(Command("done"))
async def cmd_done(message: Message, session: AsyncSession) -> None:
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2 or not parts[1].isdigit():
        await answer_menu(message, "Использование: /done <id>")
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
        await answer_menu(message, TASK_NOT_FOUND)
        return

    had_event = bool(task.google_event_id)
    removed = await remove_task_from_calendar(user, task)
    await task_service.mark_done(session, task)
    if reminder_scheduler:
        reminder_scheduler.cancel_task(task.id)
    await answer_menu(
        message,
        TASK_DONE.format(task_id=task_id) + _calendar_removal_suffix(removed, had_event),
    )


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, session: AsyncSession) -> None:
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2 or not parts[1].isdigit():
        await answer_menu(message, "Использование: /cancel <id>")
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
        await answer_menu(message, TASK_NOT_FOUND)
        return

    had_event = bool(task.google_event_id)
    removed = await remove_task_from_calendar(user, task)
    await task_service.cancel(session, task)
    if reminder_scheduler:
        reminder_scheduler.cancel_task(task.id)
    await answer_menu(
        message,
        TASK_CANCELLED.format(task_id=task_id) + _calendar_removal_suffix(removed, had_event),
    )


@router.message(Command("tasks_done"))
async def cmd_tasks_done(message: Message, session: AsyncSession) -> None:
    user = await user_service.get_or_create(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )
    tasks = await task_service.list_finished(session, user)
    if not tasks:
        await answer_menu(message, TASK_ARCHIVED_EMPTY)
        return

    status_labels = {
        "done": "выполнена",
        "cancelled": "отменена",
    }
    lines = [TASK_ARCHIVED_HEADER]
    for task in tasks:
        lines.append(
            TASK_ARCHIVED_ITEM.format(
                id=task.id,
                title=task.title,
                status=status_labels.get(task.status.value, task.status.value),
                due_at=format_due_at(task.due_at, user.timezone),
            )
        )
    lines.append("\nВернуть в активные: <code>/restore ID</code>")
    await answer_menu(message, "\n\n".join(lines))


@router.message(Command("restore"))
async def cmd_restore(message: Message, session: AsyncSession) -> None:
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2 or not parts[1].isdigit():
        await answer_menu(message, "Использование: /restore <id>")
        return

    task_id = int(parts[1])
    user = await user_service.get_or_create(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )
    task = await task_service.get(session, user, task_id)
    if not task:
        await answer_menu(message, TASK_NOT_FOUND)
        return
    if task.status == TaskStatus.PENDING:
        await answer_menu(message, f"Задача #{task_id} уже активна.")
        return

    await task_service.restore(session, task)
    if user.google_calendar_enabled and user.google_refresh_token and not task.google_event_id:
        event_id = await google_calendar_service.create_event(user, task)
        if event_id:
            task.google_event_id = event_id
    if reminder_scheduler and task.due_at > datetime.now(ZoneInfo("UTC")):
        reminder_scheduler.schedule_task(task.id, task.due_at)
    await answer_menu(
        message,
        TASK_RESTORED.format(task_id=task.id, title=task.title),
    )


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

    had_event = bool(task.google_event_id)
    removed = await remove_task_from_calendar(user, task)
    await task_service.mark_done(session, task)
    if reminder_scheduler:
        reminder_scheduler.cancel_task(task.id)
    await callback.answer("Задача выполнена")
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        f"✅ Задача #{task.id} «{task.title}» отмечена <b>выполненной</b>.\n"
        "Она убрана из активных, но не удалена навсегда."
        + _calendar_removal_suffix(removed, had_event)
    )


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

    had_event = bool(task.google_event_id)
    removed = await remove_task_from_calendar(user, task)
    await task_service.cancel(session, task)
    if reminder_scheduler:
        reminder_scheduler.cancel_task(task.id)
    await callback.answer("Задача отменена")
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        f"🗑 Задача #{task.id} «{task.title}» <b>отменена</b> и убрана из активных."
        + _calendar_removal_suffix(removed, had_event)
    )


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
    calendar_updated = await update_task_in_calendar(user, task)
    if reminder_scheduler:
        reminder_scheduler.schedule_task(task.id, task.due_at)
    new_time = format_due_at(task.due_at, user.timezone)
    calendar_line = "\n📅 Время в Google Calendar обновлено." if calendar_updated else ""
    await callback.answer(f"Напоминание через {minutes} мин")
    await callback.message.answer(
        f"⏰ Задача #{task.id} «{task.title}» <b>отложена</b>.\n"
        f"Новое время: {new_time}\n"
        "Задача остаётся в списке <b>📋 Мои задачи</b>."
        + calendar_line
    )
