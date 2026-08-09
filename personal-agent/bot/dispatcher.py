from aiogram import Dispatcher

from bot.handlers import assistant, calendar, notes, phone, start, tasks, translator, voice
from bot.middlewares.db import DbSessionMiddleware


def setup_dispatcher(dp: Dispatcher) -> None:
    dp.update.middleware(DbSessionMiddleware())
    dp.include_router(start.router)
    dp.include_router(tasks.router)
    dp.include_router(calendar.router)
    dp.include_router(notes.router)
    dp.include_router(phone.router)
    dp.include_router(translator.router)
    dp.include_router(voice.router)
    dp.include_router(assistant.router)
