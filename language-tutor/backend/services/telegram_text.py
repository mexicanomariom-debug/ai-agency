"""Safe delivery of model-generated text to Telegram.

LLM output is not trusted HTML: a stray `<`, `>` or `&` makes Telegram reject
the message with "can't parse entities". Replies can also exceed the 4096-char
message limit. Both cases silently lose an answer the user already paid for.
"""

import logging

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message

logger = logging.getLogger(__name__)

TELEGRAM_TEXT_LIMIT = 4096
TELEGRAM_CAPTION_LIMIT = 1024


def split_for_telegram(text: str, limit: int = TELEGRAM_TEXT_LIMIT) -> list[str]:
    """Split on paragraph, then line, then hard boundaries."""
    text = text.strip()
    if not text:
        return []
    if len(text) <= limit:
        return [text]

    chunks: list[str] = []
    remaining = text
    while len(remaining) > limit:
        window = remaining[:limit]
        cut = window.rfind("\n\n")
        if cut < limit // 2:
            cut = window.rfind("\n")
        if cut < limit // 2:
            cut = window.rfind(" ")
        if cut <= 0:
            cut = limit
        chunks.append(remaining[:cut].strip())
        remaining = remaining[cut:].strip()
    if remaining:
        chunks.append(remaining)
    return chunks


def truncate_caption(text: str, limit: int = TELEGRAM_CAPTION_LIMIT) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


async def answer_model_text(message: Message, text: str, prefix: str = "") -> None:
    """Send model output, retrying without HTML parsing when entities are invalid."""
    parts = split_for_telegram(text)
    if not parts:
        return

    for index, part in enumerate(parts):
        body = f"{prefix}{part}" if index == 0 and prefix else part
        try:
            await message.answer(body)
        except TelegramBadRequest as exc:
            if "can't parse entities" not in str(exc).lower():
                raise
            logger.warning("HTML parse failed, resending as plain text")
            await message.answer(body, parse_mode=None)
