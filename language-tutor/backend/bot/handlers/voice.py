from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.states.onboarding import OnboardingStates
from services.chat_service import process_user_text
from services.openai_service import openai_service

router = Router()


@router.message(
    StateFilter(OnboardingStates.chatting, OnboardingStates.placement_test),
    F.voice,
)
async def handle_voice_message(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    if not openai_service.has_api_key():
        await message.answer(
            "🎙 Для голосовых сообщений нужен OPENAI_API_KEY на сервере.\n"
            "Пока можешь писать текстом."
        )
        return

    await message.bot.send_chat_action(message.chat.id, "typing")
    file = await message.bot.get_file(message.voice.file_id)
    audio_bytes = await message.bot.download_file(file.file_path)

    try:
        transcript = await openai_service.transcribe_voice(
            audio_bytes.read(), message.voice.mime_type or "audio/ogg"
        )
    except Exception:
        await message.answer("Не удалось распознать голосовое. Попробуй записать ещё раз.")
        return

    if not transcript.strip():
        await message.answer("Не расслышал текст. Попробуй говорить чуть громче.")
        return

    current = await state.get_state()
    placement_mode = current == OnboardingStates.placement_test.state
    await process_user_text(
        message,
        session,
        transcript,
        from_voice=True,
        placement_mode=placement_mode,
    )
