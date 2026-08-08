from aiogram import Dispatcher

from bot.handlers import chat, payments, placement, product, progress, start, voice, vocab
from bot.middlewares.db import DbSessionMiddleware
from bot.middlewares.errors import ErrorNotifyMiddleware


def setup_dispatcher(dp: Dispatcher) -> None:
    dp.update.middleware(ErrorNotifyMiddleware())
    dp.update.middleware(DbSessionMiddleware())
    # Command and media routers must precede the catch-all text handlers in
    # placement.py (state catch-all) and chat.py, otherwise commands and voice
    # messages are swallowed and forwarded to the LLM as plain text.
    dp.include_router(start.router)
    dp.include_router(product.router)
    dp.include_router(progress.router)
    dp.include_router(vocab.router)
    dp.include_router(payments.router)
    dp.include_router(voice.router)
    dp.include_router(placement.router)
    dp.include_router(chat.router)
