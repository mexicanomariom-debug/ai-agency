"""Persistent bottom menu — always visible after onboarding."""

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

BTN_START_LESSON = "🚀 Начать обучение"
BTN_TEST = "📋 Пройти тест"
BTN_REVIEW = "📚 Слова"
BTN_PROGRESS = "📊 Прогресс"
BTN_FINISH = "✅ Итоги урока"
BTN_SETTINGS = "⚙️ Профиль"
BTN_HELP = "📖 Помощь"

MENU_BUTTON_TEXTS = frozenset(
    {
        BTN_START_LESSON,
        BTN_TEST,
        BTN_REVIEW,
        BTN_PROGRESS,
        BTN_FINISH,
        BTN_SETTINGS,
        BTN_HELP,
    }
)


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_START_LESSON), KeyboardButton(text=BTN_TEST)],
            [KeyboardButton(text=BTN_REVIEW), KeyboardButton(text=BTN_PROGRESS)],
            [KeyboardButton(text=BTN_FINISH), KeyboardButton(text=BTN_SETTINGS)],
            [KeyboardButton(text=BTN_HELP)],
        ],
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder="Напишите или отправьте голосовое…",
    )
