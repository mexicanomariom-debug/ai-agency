"""Log every incoming message/callback for debugging."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

logger = logging.getLogger(__name__)


class LogUpdatesMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict], Awaitable],
        event: TelegramObject,
        data: dict,
    ):
        if isinstance(event, Message):
            user = event.from_user.id if event.from_user else "?"
            preview = (event.text or event.caption or f"[{event.content_type}]")[:80]
            logger.info("MSG from=%s text=%r", user, preview)
        elif isinstance(event, CallbackQuery):
            user = event.from_user.id if event.from_user else "?"
            logger.info("CB from=%s data=%r", user, event.data)
        return await handler(event, data)
