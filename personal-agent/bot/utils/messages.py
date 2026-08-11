from aiogram.types import InlineKeyboardMarkup, Message, ReplyKeyboardMarkup

from bot.keyboards.reply import main_menu_keyboard
from services.telegram_text import answer_long_text


async def answer_menu(
    message: Message,
    text: str,
    reply_markup: InlineKeyboardMarkup | ReplyKeyboardMarkup | None = None,
    **kwargs,
) -> Message | None:
    """Ответ с постоянным меню внизу (если не передана inline-клавиатура)."""
    if reply_markup is None:
        reply_markup = main_menu_keyboard()
    return await answer_long_text(message, text, reply_markup=reply_markup, **kwargs)
