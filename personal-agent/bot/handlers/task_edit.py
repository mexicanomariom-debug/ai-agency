from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.copy import (
    TASK_EDIT_EMPTY_CHANGES,
    TASK_EDIT_EXIT,
    TASK_EDIT_NEED_ID,
    TASK_EDIT_NOT_FOUND,
    TASK_EDIT_PROMPT,
    TASK_EDIT_SUCCESS,
    TASK_NOT_FOUND,
)
from bot.keyboards.inline import task_edit_keyboard, task_list_edit_keyboard
from bot.states.task_edit import TaskEditStates
from bot.utils.menu_forward import try_forward_menu_button
from bot.utils.html import h
from bot.utils.messages import answer_menu
from services.task_editor import TaskEditChanges, task_editor
from services.task_flow import apply_task_edit, format_due_at, format_notify_types
from services.user_service import task_service, user_service

router = Router()
logger = logging.getLogger(__name__)


def _edit_prompt(task, user) -> str:
    return TASK_EDIT_PROMPT.format(
        task_id=task.id,
        title=h(task.title),
        due_at=format_due_at(task.due_at, user.timezone),
        notify_types=format_notify_types(
            task.notify_message, task.notify_call, task.notify_phone
        ),
    )


async def _start_edit_session(
    message: Message,
    session: AsyncSession,
    state: FSMContext,
    task_id: int,
) -> None:
    user = await user_service.get_or_create(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )
    task = await task_service.get_pending(session, user, task_id)
    if not task:
        await answer_menu(message, TASK_EDIT_NOT_FOUND.format(task_id=task_id))
        return

    await state.set_state(TaskEditStates.waiting_changes)
    await state.update_data(task_id=task_id)
    await answer_menu(
        message,
        _edit_prompt(task, user),
        reply_markup=task_edit_keyboard(task_id),
    )


async def _start_edit_from_callback(
    callback: CallbackQuery,
    session: AsyncSession,
    state: FSMContext,
    task_id: int,
) -> None:
    if not callback.from_user:
        await callback.answer("Ошибка", show_alert=True)
        return

    user = await user_service.get_or_create(
        session,
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name,
    )
    task = await task_service.get_pending(session, user, task_id)
    if not task:
        await callback.answer(
            TASK_EDIT_NOT_FOUND.format(task_id=task_id),
            show_alert=True,
        )
        return

    await callback.answer()
    await state.set_state(TaskEditStates.waiting_changes)
    await state.update_data(task_id=task_id)

    prompt = _edit_prompt(task, user)
    markup = task_edit_keyboard(task_id)

    if callback.message:
        try:
            await callback.message.edit_text(
                prompt,
                reply_markup=markup,
                parse_mode="HTML",
            )
            return
        except TelegramBadRequest as e:
            logger.warning("edit_text failed for task %s: %s", task_id, e)

        await callback.message.answer(prompt, reply_markup=markup, parse_mode="HTML")
        return

    await callback.bot.send_message(
        user.telegram_id,
        prompt,
        reply_markup=markup,
        parse_mode="HTML",
    )


async def process_task_edit_message(
    message: Message,
    session: AsyncSession,
    user,
    text: str,
    *,
    task_id: int,
) -> bool:
    """Apply edit from text. Returns True if handled."""
    parsed = await task_editor.parse_edit_request(text, user.timezone, task_id=task_id)
    if not parsed:
        return False

    task = await task_service.get_pending(session, user, task_id)
    if not task:
        await answer_menu(message, TASK_NOT_FOUND)
        return True

    if not _has_changes(parsed.changes):
        await answer_menu(message, TASK_EDIT_EMPTY_CHANGES)
        return True

    updated = await apply_task_edit(session, user, task, parsed.changes)
    await answer_menu(
        message,
        TASK_EDIT_SUCCESS.format(
            task_id=updated.id,
            title=h(updated.title),
            due_at=format_due_at(updated.due_at, user.timezone),
            notify_types=format_notify_types(
                updated.notify_message, updated.notify_call, updated.notify_phone
            ),
        ),
    )
    return True


def _has_changes(changes: TaskEditChanges) -> bool:
    return bool(
        changes.title
        or changes.due_at
        or changes.notify_message is not None
        or changes.notify_call is not None
        or changes.notify_phone is not None
    )


@router.message(Command("edit"))
async def cmd_edit(message: Message, session: AsyncSession, state: FSMContext) -> None:
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip().isdigit():
        user = await user_service.get_or_create(
            session,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
        )
        tasks = await task_service.list_pending(session, user)
        if not tasks:
            await answer_menu(message, TASK_EDIT_NEED_ID)
            return
        await answer_menu(
            message,
            "Выберите задачу для редактирования или отправьте <code>/edit ID</code>:",
            reply_markup=task_list_edit_keyboard(tasks),
        )
        return

    await _start_edit_session(message, session, state, int(parts[1].strip()))


@router.message(Command("edit_off"))
async def cmd_edit_off(message: Message, state: FSMContext) -> None:
    await state.clear()
    await answer_menu(message, TASK_EDIT_EXIT)


@router.message(
    TaskEditStates.waiting_changes,
    F.text.in_({"❌ Выйти", "Выйти из редактирования"}),
)
async def msg_edit_exit(message: Message, state: FSMContext) -> None:
    await state.clear()
    await answer_menu(message, TASK_EDIT_EXIT)


@router.message(TaskEditStates.waiting_changes, F.text)
async def msg_edit_changes(message: Message, session: AsyncSession, state: FSMContext) -> None:
    if await try_forward_menu_button(message, session, state):
        return

    data = await state.get_data()
    task_id = data.get("task_id")
    if not task_id:
        await state.clear()
        return

    user = await user_service.get_or_create(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )
    handled = await process_task_edit_message(
        message, session, user, message.text or "", task_id=task_id
    )
    if handled:
        await state.clear()


@router.callback_query(F.data.startswith("task:edit_cancel:"))
async def cb_task_edit_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.answer("Редактирование отменено")
    if callback.message:
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except TelegramBadRequest:
            pass
        await callback.message.answer(TASK_EDIT_EXIT)


@router.callback_query(F.data.regexp(r"^task:edit:\d+$"))
async def cb_task_edit(callback: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    if not callback.data:
        await callback.answer("Нет данных", show_alert=True)
        return
    try:
        task_id = int(callback.data.rsplit(":", 1)[-1])
    except ValueError:
        await callback.answer("Неверный ID", show_alert=True)
        return

    try:
        await _start_edit_from_callback(callback, session, state, task_id)
    except Exception:
        logger.exception("task:edit callback failed for %s", callback.data)
        await callback.answer("Ошибка. Попробуйте /edit", show_alert=True)


async def try_one_shot_edit(
    message: Message,
    session: AsyncSession,
    user,
    text: str,
) -> bool:
    """Handle natural-language edit without FSM. Returns True if handled."""
    if not task_editor.is_edit_intent(text):
        return False

    parsed = await task_editor.parse_edit_request(text, user.timezone)
    if not parsed or not parsed.task_id:
        return False
    if not _has_changes(parsed.changes):
        return False

    return await process_task_edit_message(
        message, session, user, text, task_id=parsed.task_id
    )
