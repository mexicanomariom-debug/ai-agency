"""Notes merged into Блокнот-Идеи — /notes and /note kept as aliases."""

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.journal import NOTEBOOK_BUTTON, capture_notebook_message, cmd_journal
from services.user_service import user_service

router = Router()


@router.message(Command("notes"))
@router.message(lambda m: m.text in ("📝 Заметки", "заметки", "мои заметки"))
async def cmd_notes(message: Message, session: AsyncSession, state: FSMContext) -> None:
    await cmd_journal(message, session, state)


@router.message(Command("note"))
async def cmd_note(message: Message, session: AsyncSession, state: FSMContext) -> None:
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        await cmd_journal(message, session, state)
        return

    user = await user_service.get_or_create(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )
    await capture_notebook_message(message, session, user, parts[1].strip())


@router.callback_query(lambda c: c.data and c.data.startswith("note:"))
async def cb_note_legacy(callback: CallbackQuery) -> None:
    await callback.answer("Заметки теперь в 💡 Блокнот-Идеи")
    if callback.message:
        await callback.message.answer(
            f"Заметки объединены с блокнотом. Нажмите «{NOTEBOOK_BUTTON}»."
        )
