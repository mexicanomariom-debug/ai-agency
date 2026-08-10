"""Forward main-menu button presses from FSM handlers to the right module."""

from __future__ import annotations

import logging

from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.middlewares.translator import MENU_BUTTONS

logger = logging.getLogger(__name__)


async def try_forward_menu_button(
    message: Message,
    session: AsyncSession,
    state: FSMContext,
) -> bool:
    """Clear FSM and route a menu button to its normal handler. Returns True if handled."""
    text = message.text
    if not text or text not in MENU_BUTTONS:
        return False

    await state.clear()

    try:
        if text == "📋 Мои задачи":
            from bot.handlers.tasks import cmd_tasks

            await cmd_tasks(message, session)
        elif text == "📆 Сегодня":
            from bot.handlers.tasks import cmd_today

            await cmd_today(message, session)
        elif text == "💡 Блокнот-Идеи":
            from bot.handlers.journal import cmd_journal

            await cmd_journal(message, session, state)
        elif text == "🔍 Разведка и Вериф":
            from bot.handlers.recon import cmd_recon

            await cmd_recon(message, session, state)
        elif text in ("🚗 Монитор траффика", "🚗 Пробки"):
            from bot.handlers.traffic import cmd_traffic

            await cmd_traffic(message, session, state)
        elif text == "📅 Календарь":
            from bot.handlers.calendar import btn_calendar

            await btn_calendar(message, session)
        elif text == "📞 Телефон":
            from bot.handlers.phone import btn_phone

            await btn_phone(message, session)
        elif text == "🌐 Переводчик":
            from bot.handlers.translator import cmd_translator

            await cmd_translator(message, state)
        elif text == "❓ Помощь":
            from bot.handlers.start import cmd_help

            await cmd_help(message)
        else:
            return False
    except Exception:
        logger.exception("Failed to forward menu button %r", text)
        raise

    return True
