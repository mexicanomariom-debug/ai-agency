from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.reply import TEXT_CHAT_LABEL, VOICE_TEACHER_LABEL, main_menu_keyboard
from bot.states.onboarding import OnboardingStates
from services.chat_service import process_user_text
from services.openai_service import openai_service

router = Router()


@router.message(F.text == VOICE_TEACHER_LABEL)
async def enable_voice_mode(message: Message, state: FSMContext) -> None:
    await state.set_state(OnboardingStates.voice_chatting)
    await message.answer(
        "🎙 Режим «Учитель — общение голосом» включён.\n\n"
        "Отправь голосовое сообщение — я отвечу текстом.\n"
        "Чтобы вернуться к обычному чату, нажми «Текстовый чат».",
        reply_markup=main_menu_keyboard(),
    )


@router.message(F.text == TEXT_CHAT_LABEL)
async def enable_text_mode(message: Message, state: FSMContext) -> None:
    await state.set_state(OnboardingStates.chatting)
    await message.answer(
        "💬 Текстовый режим. Пиши сообщения как обычно.",
        reply_markup=main_menu_keyboard(),
    )


@router.message(OnboardingStates.voice_chatting, F.voice)
async def handle_voice_message(message: Message, session: AsyncSession) -> None:
    if not openai_service.has_api_key():
        await message.answer(
            "🎙 Голосовой режим требует OPENAI_API_KEY на сервере.\n"
            "Пока можешь писать текстом."
        )
        return

    await message.bot.send_chat_action(message.chat.id, "typing")
    file = await message.bot.get_file(message.voice.file_id)
    audio_bytes = await message.bot.download_file(file.file_path)

    try:
        transcript = await openai_service.transcribe_voice(audio_bytes.read(), message.voice.mime_type or "audio/ogg")
    except Exception:
        await message.answer("Не удалось распознать голосовое. Попробуй записать ещё раз.")
        return

    if not transcript.strip():
        await message.answer("Не расслышал текст. Попробуй говорить чуть громче.")
        return

    await message.answer(f"📝 Ты сказал: <i>{transcript}</i>")
    await process_user_text(message, session, transcript, from_voice=True)
