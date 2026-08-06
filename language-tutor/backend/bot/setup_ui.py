import logging

from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeDefault, MenuButtonWebApp, WebAppInfo

from config import settings

logger = logging.getLogger(__name__)

MENU_BUTTON_TEXT = "⬡ Opus Neural"


async def setup_bot_ui(bot: Bot) -> None:
    """Opus Neural WebApp button + concierge commands."""
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="✦ Opus 5 · начать"),
            BotCommand(command="product", description="✦ О продукте"),
            BotCommand(command="help", description="📖 Навигатор"),
            BotCommand(command="test", description="📋 Мини-тест уровня"),
            BotCommand(command="review", description="📚 Слова на сегодня"),
            BotCommand(command="progress", description="📊 Мой прогресс"),
            BotCommand(command="settings", description="⚙️ Профиль"),
        ],
        scope=BotCommandScopeDefault(),
    )

    await bot.set_chat_menu_button(
        menu_button=MenuButtonWebApp(
            text=MENU_BUTTON_TEXT,
            web_app=WebAppInfo(url=f"{settings.twa_url}/voice"),
        )
    )
    logger.info("Opus Neural menu button → %s/voice", settings.twa_url)
