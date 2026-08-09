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
                    text="⏰ 15 мин",
                    callback_data=f"task:snooze:{task_id}:15",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="+1 час",
                    callback_data=f"task:reschedule:{task_id}:1h",
                ),
                InlineKeyboardButton(
                    text="Завтра 9:00",
                    callback_data=f"task:reschedule:{task_id}:t9",
                ),
                InlineKeyboardButton(
                    text="Вечером",
                    callback_data=f"task:reschedule:{task_id}:eve",
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


def task_list_edit_keyboard(tasks: list[Task], *, max_buttons: int = 10) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for task in tasks[:max_buttons]:
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"✏️ #{task.id}",
                    callback_data=f"task:edit:{task.id}",
                ),
                InlineKeyboardButton(
                    text=f"✅ #{task.id}",
                    callback_data=f"task:done:{task.id}",
                ),
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def note_list_keyboard(notes) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for note in notes[:12]:
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"📖 #{note.id}",
                    callback_data=f"note:view:{note.id}",
                ),
                InlineKeyboardButton(
                    text=f"🗑 #{note.id}",
                    callback_data=f"note:delete:{note.id}",
                ),
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)
