"""Send OpenAI TTS as Telegram voice notes."""

from __future__ import annotations

import logging

from aiogram.types import BufferedInputFile, Message

from services.openai_speech import openai_speech_service
from services.telegram_text import TELEGRAM_CAPTION_LIMIT, split_for_telegram, truncate_caption

logger = logging.getLogger(__name__)

TTS_INPUT_LIMIT = 4096


async def send_voice_reply(message: Message, text: str) -> bool:
    """Synthesize speech and send as Telegram voice. Returns False if unavailable."""
    spoken = text.strip()[:TTS_INPUT_LIMIT]
    if not openai_speech_service.available or not spoken:
        return False

    await message.bot.send_chat_action(message.chat.id, "record_voice")
    audio = await openai_speech_service.synthesize_speech(spoken, response_format="opus")
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

    if len(spoken) > TELEGRAM_CAPTION_LIMIT:
        for chunk in split_for_telegram(spoken[TELEGRAM_CAPTION_LIMIT:]):
            try:
                await message.answer(chunk, parse_mode=None)
            except Exception:
                logger.exception("Sending caption remainder failed")
                break
    return True
