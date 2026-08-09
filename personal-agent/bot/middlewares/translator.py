from collections.abc import Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, TelegramObject

MENU_BUTTONS = {
    "📋 Мои задачи",
    "📆 Сегодня",
    "📝 Заметки",
    "📅 Календарь",
    "📞 Телефон",
    "❓ Помощь",
}


class ClearTranslatorOnMenuMiddleware(BaseMiddleware):
    """Выйти из режима переводчика при нажатии любой другой кнопки меню."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict], Awaitable],
        event: TelegramObject,
        data: dict,
    ):
        state: FSMContext | None = data.get("state")
        if state and isinstance(event, Message) and event.text:
            if event.text in MENU_BUTTONS:
                await state.clear()
            elif event.text.startswith("/"):
                command = event.text.split(maxsplit=1)[0].lower()
                if command not in ("/translate",):
                    await state.clear()
        return await handler(event, data)
