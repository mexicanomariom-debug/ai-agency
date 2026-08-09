from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from services.translator import LANGUAGES


def task_actions_keyboard(task_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Готово", callback_data=f"task:done:{task_id}"),
                InlineKeyboardButton(text="⏰ +15 мин", callback_data=f"task:snooze:{task_id}:15"),
            ],
            [
                InlineKeyboardButton(text="🗑 Отменить", callback_data=f"task:cancel:{task_id}"),
            ],
        ]
    )


def translator_languages_keyboard(selected: str) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    codes = list(LANGUAGES.keys())
    for i in range(0, len(codes), 2):
        row = []
        for code in codes[i : i + 2]:
            label = LANGUAGES[code]
            prefix = "✓ " if code == selected else ""
            row.append(InlineKeyboardButton(text=f"{prefix}{label}", callback_data=f"tr:lang:{code}"))
        rows.append(row)
    rows.append([InlineKeyboardButton(text="❌ Выйти из переводчика", callback_data="tr:exit")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
