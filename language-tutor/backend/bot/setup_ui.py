import logging

from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeDefault, MenuButtonWebApp, WebAppInfo

from config import settings

logger = logging.getLogger(__name__)

MENU_BUTTON_TEXT = "Учитель — общение"


async def setup_bot_ui(bot: Bot) -> None:
    """Premium teacher menu: blue voice button + concierge commands."""
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="✦ Concierge · начать"),
            BotCommand(command="help", description="📖 Как заниматься"),
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
    logger.info("Teacher menu: blue button → %s/voice", settings.twa_url)
