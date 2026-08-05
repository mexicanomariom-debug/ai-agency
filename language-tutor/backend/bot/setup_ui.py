import logging

from aiogram import Bot
from aiogram.types import BotCommand, MenuButtonWebApp, WebAppInfo

from config import settings

logger = logging.getLogger(__name__)

MENU_BUTTON_TEXT = "Учитель — общение голосом"


async def setup_bot_ui(bot: Bot) -> None:
    """Rename the blue menu button and register bot commands."""
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Начать / выбрать язык"),
            BotCommand(command="settings", description="Сбросить настройки"),
        ]
    )

    # Rename the blue Mini App button (was «Опус 5» in BotFather).
    await bot.set_chat_menu_button(
        menu_button=MenuButtonWebApp(
            text=MENU_BUTTON_TEXT,
            web_app=WebAppInfo(url=f"{settings.twa_url}/voice"),
        )
    )
    logger.info("Menu button set to: %s", MENU_BUTTON_TEXT)
