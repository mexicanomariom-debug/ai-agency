"""Notes merged into Блокнот-Идеи — this module keeps /notes as an alias."""

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.journal import NOTEBOOK_BUTTON, capture_notebook_message, cmd_journal, show_journal
from bot.utils.messages import answer_menu
from services.note_service import note_service
from services.user_service import user_service

router = Router()


@router.message(Command("notes"))
@router.message(Command("note"))
@router.message(lambda m: m.text in ("📝 Заметки", "заметки", "мои заметки"))
async def cmd_notes(message: Message, session: AsyncSession, state: FSMContext) -> None:
    """Совместимость: заметки → блокнот."""
    if message.text and message.text.startswith("/note ") and message.text.count(" ") >= 1:
        user = await user_service.get_or_create(
            session,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
        )
        content = message.text.split(maxsplit=1)[1].strip()
        if content:
            await state.set_state(None)
            from bot.states.notebook import NotebookStates

            await state.set_state(NotebookStates.writing)
            await capture_notebook_message(message, session, user, content)
            return

    await cmd_journal(message, session, state)


@router.callback_query(lambda c: c.data and c.data.startswith("note:"))
async def cb_note_legacy(callback: CallbackQuery, session: AsyncSession) -> None:
    """Старые inline-кнопки заметок — перенаправляем в блокнот."""
    await callback.answer("Заметки теперь в 💡 Блокнот-Идеи")
    if callback.message:
        await callback.message.answer(
            f"Заметки объединены с блокнотом. Нажмите «{NOTEBOOK_BUTTON}»."
        )
