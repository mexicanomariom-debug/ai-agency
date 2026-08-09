from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.copy import VOICE_FAILED, VOICE_HINT, VOICE_TRANSCRIBED
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
