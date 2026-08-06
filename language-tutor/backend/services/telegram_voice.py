"""Send OpenAI TTS replies as Telegram voice messages."""

from aiogram.types import BufferedInputFile, Message

from services.openai_service import openai_service


async def send_voice_reply(message: Message, text: str) -> bool:
    """Synthesize speech and send as Telegram voice. Returns False if TTS unavailable."""
    if not openai_service.has_api_key() or not text.strip():
        return False

    await message.bot.send_chat_action(message.chat.id, "record_voice")
    try:
        audio = await openai_service.synthesize_speech(text.strip())
    except Exception:
        return False

    if not audio:
        return False

    caption = text.strip()
    if len(caption) > 1024:
        caption = caption[:1021] + "…"

    await message.answer_voice(
        BufferedInputFile(audio, filename="opus.mp3"),
        caption=caption,
    )
    return True
