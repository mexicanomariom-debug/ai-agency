"""Send OpenAI TTS replies as Telegram voice messages."""

import logging

from aiogram.types import BufferedInputFile, Message

from services.openai_service import openai_service
from services.telegram_text import (
    TELEGRAM_CAPTION_LIMIT,
    split_for_telegram,
    truncate_caption,
)

logger = logging.getLogger(__name__)

# OpenAI TTS hard limit; keep spoken audio and caption consistent.
TTS_INPUT_LIMIT = 4096


async def send_voice_reply(message: Message, text: str) -> bool:
    """Synthesize speech and send as Telegram voice. Returns False if unavailable."""
    spoken = text.strip()[:TTS_INPUT_LIMIT]
    if not openai_service.has_api_key() or not spoken:
        return False

    await message.bot.send_chat_action(message.chat.id, "record_voice")
    try:
        # Telegram voice notes expect OGG/Opus, not MP3.
        audio = await openai_service.synthesize_speech(spoken, response_format="opus")
    except Exception:
        logger.exception("TTS synthesis failed")
        return False

    if not audio:
        return False

    try:
        await message.answer_voice(
            BufferedInputFile(audio, filename="reply.ogg"),
            caption=truncate_caption(spoken),
        )
    except Exception:
        logger.exception("Sending voice message failed")
        return False

    # A caption holds only 1024 chars; send the rest so the student can read
    # the full explanation instead of losing it.
    if len(spoken) > TELEGRAM_CAPTION_LIMIT:
        for chunk in split_for_telegram(spoken[TELEGRAM_CAPTION_LIMIT:]):
            try:
                await message.answer(chunk)
            except Exception:
                logger.exception("Sending caption remainder failed")
                break
    return True
