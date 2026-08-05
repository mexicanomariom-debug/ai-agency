from aiogram import Dispatcher

from bot.handlers import chat, payments, start, voice
from bot.middlewares.db import DbSessionMiddleware
from bot.middlewares.errors import ErrorNotifyMiddleware


def setup_dispatcher(dp: Dispatcher) -> None:
    dp.update.middleware(ErrorNotifyMiddleware())
    dp.update.middleware(DbSessionMiddleware())
    dp.include_router(start.router)
    dp.include_router(voice.router)
    dp.include_router(chat.router)
    dp.include_router(payments.router)
