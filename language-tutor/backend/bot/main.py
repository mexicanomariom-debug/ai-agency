import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.dispatcher import setup_dispatcher
from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main() -> None:
    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN is required")

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())
    setup_dispatcher(dp)

    logger.info("Starting bot @%s", settings.bot_username)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
