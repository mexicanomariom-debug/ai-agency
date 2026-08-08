import logging

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.states.onboarding import OnboardingStates
from database.enums import Language
from services.chat_service import process_user_text
from services.openai_service import openai_service
from services.user_service import user_service

router = Router()
logger = logging.getLogger(__name__)

# Whisper rejects files above 25 MB; Telegram allows far larger uploads.
MAX_VOICE_BYTES = 24 * 1024 * 1024
MAX_VOICE_SECONDS = 300

# Spelling hints for Whisper when students practice the target language aloud.
_WHISPER_PROMPTS: dict[Language, str] = {
    Language.SPANISH: (
        "Me llamo. Hola. Gracias. Buenos días. ¿Cómo estás? "
        "Mixed Russian and Spanish. Prefer correct Spanish spelling: "
        "llamo, llegar, ella, pollo, calle."
    ),
    Language.ENGLISH: (
        "Hello. How are you? Mixed Russian and English speech for language learning."
    ),
    Language.GERMAN: (
        "Guten Tag. Ich heiße. Mixed Russian and German speech for language learning."
    ),
    Language.FRENCH: (
        "Bonjour. Je m'appelle. Mixed Russian and French speech for language learning."
    ),
    Language.ITALIAN: (
        "Ciao. Mi chiamo. Mixed Russian and Italian speech for language learning."
    ),
    Language.CHINESE: (
        "你好. Mixed Russian and Chinese speech for language learning."
    ),
}


def _whisper_prompt_for(language: Language | None) -> str | None:
    if language is None:
        return (
            "Mixed Russian and foreign-language speech for a language lesson. "
            "Keep target-language spelling accurate."
        )
    return _WHISPER_PROMPTS.get(language) or (
        "Mixed Russian and foreign-language speech for a language lesson. "
        "Keep target-language spelling accurate."
    )


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
    prompt = _whisper_prompt_for(user.language if user else None)

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
