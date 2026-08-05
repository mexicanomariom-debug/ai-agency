import asyncio
import logging
import subprocess

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.dispatcher import setup_dispatcher
from bot.setup_ui import setup_bot_ui
from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_migrations() -> None:
    logger.info("Running database migrations...")
    subprocess.run(["alembic", "upgrade", "head"], check=True)


async def main() -> None:
    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN is required")

    run_migrations()

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())
    setup_dispatcher(dp)

    await setup_bot_ui(bot)

    logger.info("Starting bot @%s", settings.bot_username)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
