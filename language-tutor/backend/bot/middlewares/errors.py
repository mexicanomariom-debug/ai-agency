import logging
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

logger = logging.getLogger(__name__)


class ErrorNotifyMiddleware(BaseMiddleware):
    """Reply to the user when a handler crashes instead of failing silently."""

    async def __call__(self, handler, event: TelegramObject, data: dict[str, Any]):
        try:
            return await handler(event, data)
        except Exception:
            logger.exception("Handler error for update %s", getattr(event, "update_id", event))
            if isinstance(event, Message):
                await event.answer(
                    "⚠️ Произошла ошибка. Попробуй ещё раз или напиши /start.\n"
                    "Если не помогает — подожди минуту и повтори."
                )
            raise
