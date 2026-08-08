import logging

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.states.onboarding import OnboardingStates
from services.chat_service import process_user_text
from services.openai_service import openai_service
from services.user_service import user_service
from services.whisper_prompt import whisper_prompt_for

router = Router()
logger = logging.getLogger(__name__)

# Whisper rejects files above 25 MB; Telegram allows far larger uploads.
MAX_VOICE_BYTES = 24 * 1024 * 1024
MAX_VOICE_SECONDS = 300


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

    voice = message.voice
    if voice.duration and voice.duration > MAX_VOICE_SECONDS:
        await message.answer("Голосовое слишком длинное. Запишите до 5 минут.")
        return
    if voice.file_size and voice.file_size > MAX_VOICE_BYTES:
        await message.answer("Файл слишком большой. Запишите сообщение покороче.")
        return

    await message.bot.send_chat_action(message.chat.id, "typing")

    user = await user_service.get_by_telegram_id(session, message.from_user.id)
    prompt = whisper_prompt_for(user.language if user else None)

    try:
        file = await message.bot.get_file(voice.file_id)
        if not file.file_path:
            await message.answer("Не удалось скачать голосовое. Запишите его ещё раз.")
            return
        audio_bytes = await message.bot.download_file(file.file_path)
        transcript = await openai_service.transcribe_voice(
            audio_bytes.read(),
            voice.mime_type or "audio/ogg",
            prompt=prompt,
        )
    except Exception:
        logger.exception("Voice transcription failed for chat=%s", message.chat.id)
        await message.answer("Не удалось распознать голосовое. Попробуй записать ещё раз.")
        return

    transcript = transcript.strip()
    if not transcript:
        await message.answer("Не расслышал текст. Попробуй говорить чуть громче.")
        return

    logger.info(
        "voice transcript chat=%s user=%s text=%r",
        message.chat.id,
        message.from_user.id if message.from_user else None,
        transcript[:200],
    )
    # Show what STT heard so the student can spot Whisper mistakes immediately.
    await message.answer(f"📝 {transcript}")

    current = await state.get_state()
    placement_mode = current == OnboardingStates.placement_test.state
    await process_user_text(
        message,
        session,
        transcript,
        from_voice=True,
        placement_mode=placement_mode,
    )


@router.message(F.voice)
async def handle_voice_before_onboarding(message: Message) -> None:
    await message.answer("Сначала настроим профиль — отправьте /start.")
