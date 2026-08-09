from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


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
