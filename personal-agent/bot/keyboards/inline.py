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


def journal_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="💡 Идеи", callback_data="journal:filter:idea"),
                InlineKeyboardButton(text="💭 Мысли", callback_data="journal:filter:thought"),
            ],
            [
                InlineKeyboardButton(text="💸 Траты", callback_data="journal:filter:expense"),
                InlineKeyboardButton(text="📊 Сводка", callback_data="journal:summary"),
            ],
            [
                InlineKeyboardButton(text="📅 Вчера", callback_data="journal:yesterday"),
                InlineKeyboardButton(text="🔄 Сегодня", callback_data="journal:today"),
            ],
            [
                InlineKeyboardButton(text="❌ Выйти", callback_data="journal:exit"),
            ],
        ]
    )


def traffic_menu_keyboard(*, enabled: bool) -> InlineKeyboardMarkup:
    toggle = "❌ Выключить" if enabled else "✅ Включить"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🛣 Маршрут", callback_data="traffic:setup:route"),
                InlineKeyboardButton(text="🏙 Район/улица", callback_data="traffic:setup:area"),
            ],
            [
                InlineKeyboardButton(text="🔄 Проверить", callback_data="traffic:check"),
            ],
            [
                InlineKeyboardButton(text="🗺 Яндекс", callback_data="traffic:provider:yandex"),
                InlineKeyboardButton(text="🗺 2ГИС", callback_data="traffic:provider:dgis"),
                InlineKeyboardButton(text="🗺 Google", callback_data="traffic:provider:google"),
            ],
            [
                InlineKeyboardButton(text=toggle, callback_data="traffic:toggle"),
                InlineKeyboardButton(text="❌ Отмена", callback_data="traffic:cancel"),
            ],
        ]
    )


def traffic_provider_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🗺 Яндекс Карты", callback_data="traffic:pick:yandex"),
                InlineKeyboardButton(text="🗺 2ГИС", callback_data="traffic:pick:dgis"),
            ],
            [
                InlineKeyboardButton(text="🗺 Google Maps", callback_data="traffic:pick:google"),
                InlineKeyboardButton(text="🤖 Авто", callback_data="traffic:pick:auto"),
            ],
        ]
    )


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
