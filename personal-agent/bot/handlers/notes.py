from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.copy import (
    NOTE_CREATED,
    NOTE_DELETE_CONFIRM,
    NOTE_DELETED,
    NOTE_LIST_EMPTY,
    NOTE_LIST_HEADER,
    NOTE_NOT_FOUND,
    NOTE_VIEW,
)
from bot.keyboards.inline import note_list_keyboard
from bot.utils.html import h
from bot.utils.messages import answer_menu
from services.note_service import note_service
from services.user_service import user_service

router = Router()


@router.message(Command("notes"))
@router.message(lambda m: m.text in ("📝 Заметки", "заметки", "мои заметки"))
async def cmd_notes(message: Message, session: AsyncSession) -> None:
    user = await user_service.get_or_create(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )
    notes = await note_service.list_recent(session, user)
    if not notes:
        await answer_menu(message, NOTE_LIST_EMPTY)
        return

    lines = [NOTE_LIST_HEADER.format(count=len(notes))]
    for note in notes:
        preview = h(note.content[:80] + ("…" if len(note.content) > 80 else ""))
        lines.append(f"#{note.id} — {preview}")
    await answer_menu(
        message,
        "\n\n".join(lines),
        reply_markup=note_list_keyboard(notes),
    )


@router.message(Command("note"))
async def cmd_note(message: Message, session: AsyncSession) -> None:
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await answer_menu(message, "Использование: /note текст заметки")
        return

    user = await user_service.get_or_create(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )
    note = await note_service.create(session, user, content=parts[1].strip())
    await answer_menu(message, NOTE_CREATED.format(note_id=note.id))


@router.message(Command("note_delete"))
async def cmd_note_delete(message: Message, session: AsyncSession) -> None:
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2 or not parts[1].isdigit():
        await answer_menu(message, "Использование: /note_delete <id>")
        return

    user = await user_service.get_or_create(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )
    note = await note_service.get(session, user, int(parts[1]))
    if not note:
        await answer_menu(message, NOTE_NOT_FOUND)
        return
    note_id = note.id
    await note_service.delete(session, note)
    await answer_menu(message, NOTE_DELETED.format(note_id=note_id))


@router.callback_query(lambda c: c.data and c.data.startswith("note:view:"))
async def cb_note_view(callback: CallbackQuery, session: AsyncSession) -> None:
    note_id = int(callback.data.split(":")[-1])
    user = await user_service.get_or_create(
        session,
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name,
    )
    note = await note_service.get(session, user, note_id)
    if not note:
        await callback.answer(NOTE_NOT_FOUND, show_alert=True)
        return
    await callback.answer()
    if callback.message:
        await callback.message.answer(
            NOTE_VIEW.format(note_id=note.id, content=h(note.content))
        )


@router.callback_query(lambda c: c.data and c.data.startswith("note:delete:"))
async def cb_note_delete(callback: CallbackQuery, session: AsyncSession) -> None:
    note_id = int(callback.data.split(":")[-1])
    user = await user_service.get_or_create(
        session,
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name,
    )
    note = await note_service.get(session, user, note_id)
    if not note:
        await callback.answer(NOTE_NOT_FOUND, show_alert=True)
        return
    await note_service.delete(session, note)
    await callback.answer("Удалено")
    if callback.message:
        await callback.message.answer(NOTE_DELETE_CONFIRM.format(note_id=note_id))
