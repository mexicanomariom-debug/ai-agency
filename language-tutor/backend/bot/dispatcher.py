from aiogram import Dispatcher

from bot.handlers import chat, payments, start
from bot.middlewares.db import DbSessionMiddleware


def setup_dispatcher(dp: Dispatcher) -> None:
    dp.update.middleware(DbSessionMiddleware())
    dp.include_router(start.router)
    dp.include_router(chat.router)
    dp.include_router(payments.router)
