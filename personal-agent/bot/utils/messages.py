from aiogram.types import InlineKeyboardMarkup, Message, ReplyKeyboardMarkup

from bot.keyboards.reply import main_menu_keyboard


async def answer_menu(
    message: Message,
    text: str,
    reply_markup: InlineKeyboardMarkup | ReplyKeyboardMarkup | None = None,
    **kwargs,
) -> Message:
    """Ответ с постоянным меню внизу (если не передана inline-клавиатура)."""
    if reply_markup is None:
        reply_markup = main_menu_keyboard()
    return await message.answer(text, reply_markup=reply_markup, **kwargs)
