from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

VOICE_TEACHER_LABEL = "🎙 Учитель — общение голосом"
TEXT_CHAT_LABEL = "💬 Текстовый чат"


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=VOICE_TEACHER_LABEL)],
            [KeyboardButton(text=TEXT_CHAT_LABEL)],
        ],
        resize_keyboard=True,
        input_field_placeholder="Напиши сообщение или отправь голосовое…",
    )
