from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📋 Мои задачи"),
                KeyboardButton(text="📆 Сегодня"),
            ],
            [
                KeyboardButton(text="📝 Заметки"),
                KeyboardButton(text="🌐 Переводчик"),
            ],
            [
                KeyboardButton(text="📅 Календарь"),
                KeyboardButton(text="📞 Телефон"),
            ],
            [
                KeyboardButton(text="❓ Помощь"),
            ],
        ],
        resize_keyboard=True,
    )
