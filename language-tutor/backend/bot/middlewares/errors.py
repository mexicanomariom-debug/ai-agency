import logging
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject, Update

logger = logging.getLogger(__name__)

ERROR_TEXT = (
    "⚠️ Произошла ошибка. Попробуй ещё раз или напиши /start.\n"
    "Если не помогает — подожди минуту и повтори."
)


def _extract_target(event: TelegramObject) -> Message | CallbackQuery | None:
    """Update-level middleware receives Update, not Message/CallbackQuery."""
    if isinstance(event, Update):
        return event.message or event.callback_query
    if isinstance(event, (Message, CallbackQuery)):
        return event
    return None


class ErrorNotifyMiddleware(BaseMiddleware):
    """Reply to the user when a handler crashes instead of failing silently."""

    async def __call__(self, handler, event: TelegramObject, data: dict[str, Any]):
        try:
            return await handler(event, data)
        except Exception:
            logger.exception("Handler error for update %s", getattr(event, "update_id", event))
            target = _extract_target(event)
            try:
                if isinstance(target, Message):
                    await target.answer(ERROR_TEXT)
                elif isinstance(target, CallbackQuery):
                    await target.answer("⚠️ Ошибка, попробуйте ещё раз", show_alert=True)
                    if target.message:
                        await target.message.answer(ERROR_TEXT)
            except Exception:
                logger.exception("Failed to notify user about handler error")
            raise
