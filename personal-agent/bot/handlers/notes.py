from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.copy import NOTE_CREATED, NOTE_DELETED, NOTE_LIST_EMPTY, NOTE_LIST_HEADER, NOTE_NOT_FOUND
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
        await message.answer(NOTE_LIST_EMPTY)
        return

    lines = [NOTE_LIST_HEADER.format(count=len(notes))]
    for note in notes:
        preview = note.content[:120] + ("…" if len(note.content) > 120 else "")
        lines.append(f"#{note.id} — {preview}")
    await message.answer("\n\n".join(lines))


@router.message(Command("note"))
async def cmd_note(message: Message, session: AsyncSession) -> None:
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Использование: /note текст заметки")
        return

    user = await user_service.get_or_create(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )
    note = await note_service.create(session, user, content=parts[1].strip())
    await message.answer(NOTE_CREATED.format(note_id=note.id))


@router.message(Command("note_delete"))
async def cmd_note_delete(message: Message, session: AsyncSession) -> None:
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer("Использование: /note_delete <id>")
        return

    user = await user_service.get_or_create(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )
    note = await note_service.get(session, user, int(parts[1]))
    if not note:
        await message.answer(NOTE_NOT_FOUND)
        return
    note_id = note.id
    await note_service.delete(session, note)
    await message.answer(NOTE_DELETED.format(note_id=note_id))
