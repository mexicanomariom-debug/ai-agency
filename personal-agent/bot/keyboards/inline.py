from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from database.models import Task


def task_actions_keyboard(task_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Выполнено",
                    callback_data=f"task:done:{task_id}",
                ),
                InlineKeyboardButton(
                    text="⏰ Через 15 мин",
                    callback_data=f"task:snooze:{task_id}:15",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🗑 Отменить задачу",
                    callback_data=f"task:cancel:{task_id}",
                ),
            ],
        ]
    )


def task_edit_keyboard(task_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ Выйти",
                    callback_data=f"task:edit_cancel:{task_id}",
                ),
            ],
        ]
    )


def task_list_edit_keyboard(tasks: list[Task], *, max_buttons: int = 12) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for task in tasks[:max_buttons]:
        row.append(
            InlineKeyboardButton(
                text=f"✏️ #{task.id}",
                callback_data=f"task:edit:{task.id}",
            )
        )
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=rows)
