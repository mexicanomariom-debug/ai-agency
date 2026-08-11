import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.dispatcher import setup_dispatcher
from config import settings
from database.session import async_session_factory, init_db
from services.notifier import init_notifier
from services.pulse import init_pulse_service
from services.recon import init_recon_monitor
from services.scheduler import init_scheduler
from services.traffic import init_traffic_monitor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main() -> None:
    logger.info("Personal agent booting (env=%s, build=%s)", settings.environment, settings.bot_build_id)

    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN is required. Copy env.example to .env and set your token.")

    if settings.environment != "production" and os.getenv("ALLOW_LOCAL_BOT", "").lower() != "true":
        raise RuntimeError(
            "Локальный polling отключён (на Oracle уже работает @mychatbot7_bot).\n"
            "Для разработки на ПК добавьте ALLOW_LOCAL_BOT=true в .env.\n"
            "Cloud Agent / Cursor VM не должен запускать bot.main — иначе два ответа в Telegram."
        )

    logger.info("Initializing database…")
    await init_db()
    logger.info("Database ready")

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())
    setup_dispatcher(dp)

    notifier = init_notifier(bot, async_session_factory)
    init_pulse_service(bot, async_session_factory)
    init_traffic_monitor(bot, async_session_factory)
    init_recon_monitor(bot, async_session_factory)
    scheduler = init_scheduler(async_session_factory, notifier)
    scheduler.start()
    try:
        await scheduler.bootstrap()
    except Exception:
        logger.exception("Scheduler bootstrap failed — bot will still run")

    logger.info(
        "Personal agent bot started (env=%s, build=%s)",
        settings.environment,
        settings.bot_build_id,
    )
    try:
        await dp.start_polling(bot, drop_pending_updates=True)
    finally:
        scheduler.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
