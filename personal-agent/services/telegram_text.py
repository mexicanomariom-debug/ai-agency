"""Safe delivery of text to Telegram (split long replies, HTML fallback)."""

from __future__ import annotations

import logging

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import InlineKeyboardMarkup, Message, ReplyKeyboardMarkup

logger = logging.getLogger(__name__)

TELEGRAM_TEXT_LIMIT = 4096
TELEGRAM_CAPTION_LIMIT = 1024

ReplyMarkup = InlineKeyboardMarkup | ReplyKeyboardMarkup | None


def split_for_telegram(text: str, limit: int = TELEGRAM_TEXT_LIMIT) -> list[str]:
    """Split on paragraph, then line, then word boundaries."""
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


async def answer_long_text(
    message: Message,
    text: str,
    *,
    reply_markup: ReplyMarkup = None,
    parse_mode: str | None = "HTML",
    prefix: str = "",
) -> Message | None:
    """Send text in chunks; retry without HTML when entities are invalid."""
    parts = split_for_telegram(text)
    if not parts:
        return None

    last: Message | None = None
    for index, part in enumerate(parts):
        body = f"{prefix}{part}" if index == 0 and prefix else part
        keyboard = reply_markup if index == len(parts) - 1 else None
        try:
            last = await message.answer(body, reply_markup=keyboard, parse_mode=parse_mode)
        except TelegramBadRequest as exc:
            if parse_mode and "can't parse entities" in str(exc).lower():
                logger.warning("HTML parse failed, resending chunk as plain text")
                last = await message.answer(body, reply_markup=keyboard, parse_mode=None)
            else:
                raise
    return last


async def answer_model_text(
    message: Message,
    text: str,
    *,
    reply_markup: ReplyMarkup = None,
    prefix: str = "",
) -> Message | None:
    """LLM output is not trusted HTML — always send as plain text."""
    return await answer_long_text(
        message,
        text,
        reply_markup=reply_markup,
        parse_mode=None,
        prefix=prefix,
    )
