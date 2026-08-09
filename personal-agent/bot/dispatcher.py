import logging

from aiogram import Dispatcher
from aiogram.types import ErrorEvent

from bot.handlers import assistant, calendar, notes, phone, start, tasks, translator, voice
from bot.middlewares.db import DbSessionMiddleware
from bot.middlewares.translator import ClearTranslatorOnMenuMiddleware
from bot.utils.messages import answer_menu

logger = logging.getLogger(__name__)


async def on_handler_error(event: ErrorEvent) -> bool:
    logger.exception("Handler error for update %s", event.update.update_id, exc_info=event.exception)
    if event.update.message:
        try:
            await answer_menu(
                event.update.message,
                "❌ Что-то пошло не так. Попробуйте ещё раз или напишите /help",
            )
        except Exception:
            logger.exception("Failed to send error reply")
    return True


def setup_dispatcher(dp: Dispatcher) -> None:
    dp.errors.register(on_handler_error)
    dp.update.middleware(DbSessionMiddleware())
    dp.update.middleware(ClearTranslatorOnMenuMiddleware())
    dp.include_router(start.router)
    dp.include_router(tasks.router)
    dp.include_router(calendar.router)
    dp.include_router(notes.router)
    dp.include_router(phone.router)
    dp.include_router(translator.router)
    dp.include_router(voice.router)
    dp.include_router(assistant.router)
