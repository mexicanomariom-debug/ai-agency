from aiogram import Dispatcher

from bot.handlers import start, tasks
from bot.middlewares.db import DbSessionMiddleware


def setup_dispatcher(dp: Dispatcher) -> None:
    dp.update.middleware(DbSessionMiddleware())
    dp.include_router(start.router)
    dp.include_router(tasks.router)
