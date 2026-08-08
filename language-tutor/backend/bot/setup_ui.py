import logging

from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeDefault, MenuButtonCommands

logger = logging.getLogger(__name__)


async def setup_bot_ui(bot: Bot) -> None:
    """Commands menu only — no WebApp / Mini App button."""
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="✦ Opus 5 · начать"),
            BotCommand(command="product", description="✦ О продукте"),
            BotCommand(command="help", description="📖 Навигатор"),
            BotCommand(command="test", description="📋 Мини-тест уровня"),
            BotCommand(command="review", description="📚 Слова на сегодня"),
            BotCommand(command="finish", description="✅ Итоги урока и CEFR"),
            BotCommand(command="progress", description="📊 Мой прогресс"),
            BotCommand(command="settings", description="⚙️ Профиль"),
        ],
        scope=BotCommandScopeDefault(),
    )

    await bot.set_chat_menu_button(menu_button=MenuButtonCommands())
    logger.info("Menu button → commands (no WebApp)")
