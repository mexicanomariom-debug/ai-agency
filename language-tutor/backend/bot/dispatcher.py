from aiogram import Dispatcher

from bot.handlers import (
    chat,
    menu,
    payments,
    placement,
    product,
    progress,
    session,
    start,
    voice,
    vocab,
)
from bot.middlewares.db import DbSessionMiddleware
from bot.middlewares.errors import ErrorNotifyMiddleware


def setup_dispatcher(dp: Dispatcher) -> None:
    dp.update.middleware(ErrorNotifyMiddleware())
    dp.update.middleware(DbSessionMiddleware())
    # Command, reply-menu and media routers must precede catch-all text handlers
    # in placement.py / chat.py, otherwise buttons and voice are swallowed.
    dp.include_router(start.router)
    dp.include_router(menu.router)
    dp.include_router(product.router)
    dp.include_router(progress.router)
    dp.include_router(vocab.router)
    dp.include_router(session.router)
    dp.include_router(payments.router)
    dp.include_router(voice.router)
    dp.include_router(placement.router)
    dp.include_router(chat.router)
