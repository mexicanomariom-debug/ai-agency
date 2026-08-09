import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.dispatcher import setup_dispatcher
from config import settings
from database.session import async_session_factory, init_db
from services.notifier import init_notifier
from services.scheduler import init_scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main() -> None:
    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN is required. Copy env.example to .env and set your token.")

    await init_db()

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())
    setup_dispatcher(dp)

    notifier = init_notifier(bot, async_session_factory)
    scheduler = init_scheduler(async_session_factory, notifier)
    scheduler.start()
    try:
        await scheduler.bootstrap()
    except Exception:
        logger.exception("Scheduler bootstrap failed — bot will still run")

    logger.info("Personal agent bot started")
    try:
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
