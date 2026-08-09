"""Standalone OAuth API for Google Calendar (separate from Telegram polling)."""
from __future__ import annotations

import asyncio
import logging

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from api.oauth_server import start_oauth_server
from config import settings
from database.session import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main() -> None:
    await init_db()
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    runner = await start_oauth_server(bot)
    if not runner:
        raise RuntimeError("Failed to start OAuth server")
    logger.info("OAuth API ready on port %s", settings.oauth_server_port)
    try:
        await asyncio.Event().wait()
    finally:
        await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
