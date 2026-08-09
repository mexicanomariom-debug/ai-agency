from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.copy import VOICE_FAILED, VOICE_HINT, VOICE_TRANSCRIBED
from bot.states.notebook import NotebookStates
from bot.states.recon import ReconSetupStates
from bot.states.task_edit import TaskEditStates
from bot.states.translator import TranslatorStates
from bot.utils.messages import answer_menu
from services.stt import stt_service

router = Router()


async def transcribe_for_user(message: Message, *, in_translator: bool = False) -> str | None:
    if not stt_service.available:
        await answer_menu(message, VOICE_HINT)
        return None

    # В переводчике — автоопределение языка (es, en, ru…). Для задач — тоже auto.
    text = await stt_service.transcribe_telegram_voice(
        message.bot,
        message.voice.file_id,
        language=None,
    )
    if not text:
        await answer_menu(message, VOICE_FAILED)
        return None

    if not in_translator:
        await answer_menu(message, VOICE_TRANSCRIBED.format(text=text))
    return text


@router.message(F.voice)
async def handle_voice(message: Message, session: AsyncSession, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state == TranslatorStates.waiting_text.state:
        return
    if current_state == TaskEditStates.waiting_changes.state:
        from bot.handlers.task_edit import process_task_edit_message
        from services.user_service import user_service

        data = await state.get_data()
        task_id = data.get("task_id")
        if not task_id:
            return

        await message.bot.send_chat_action(message.chat.id, "typing")
        text = await transcribe_for_user(message, in_translator=False)
        if not text:
            return

        user = await user_service.get_or_create(
            session,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
        )
        if await process_task_edit_message(message, session, user, text, task_id=task_id):
            await state.clear()
        return

    if current_state == NotebookStates.writing.state:
        from bot.handlers.journal import capture_notebook_message
        from services.user_service import user_service

        await message.bot.send_chat_action(message.chat.id, "typing")
        text = await transcribe_for_user(message, in_translator=False)
        if not text:
            return

        user = await user_service.get_or_create(
            session,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
        )
        await capture_notebook_message(message, session, user, text)
        return

    if current_state == ReconSetupStates.waiting_interest.state:
        from bot.handlers.recon import apply_recon_interest

        await message.bot.send_chat_action(message.chat.id, "typing")
        text = await transcribe_for_user(message, in_translator=False)
        if text:
            await apply_recon_interest(message, session, state, text)
        return

    if current_state == ReconSetupStates.waiting_url.state:
        from bot.handlers.recon import _add_source_from_text

        await message.bot.send_chat_action(message.chat.id, "typing")
        text = await transcribe_for_user(message, in_translator=False)
        if not text:
            return
        data = await state.get_data()
        source_type = data.get("recon_source_type")
        await _add_source_from_text(message, session, state, text.strip(), source_type=source_type)
        return

    from bot.handlers.assistant import process_user_message
    from services.user_service import user_service

    await message.bot.send_chat_action(message.chat.id, "typing")
    text = await transcribe_for_user(message, in_translator=False)
    if not text:
        return

    user = await user_service.get_or_create(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )
    await process_user_message(message, session, user, text)
