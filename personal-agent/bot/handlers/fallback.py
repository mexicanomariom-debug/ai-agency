"""Catch-all handlers for updates that no router matched."""

import logging

from aiogram import Router
from aiogram.types import CallbackQuery

logger = logging.getLogger(__name__)

router = Router(name="fallback")


@router.callback_query()
async def unhandled_callback(callback: CallbackQuery) -> None:
    logger.info("Unhandled callback: %s", callback.data)
    await callback.answer(
        "Кнопка устарела — откройте раздел заново из меню",
        show_alert=True,
    )
