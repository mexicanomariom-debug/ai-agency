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


def journal_entries_keyboard(entries, *, back_callback: str = "journal:today") -> InlineKeyboardMarkup:
    from services.smart_journal import smart_journal_service

    rows: list[list[InlineKeyboardButton]] = [
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
    ]
    for entry in entries[:8]:
        icon = {"idea": "💡", "thought": "💭", "expense": "💸"}.get(entry.kind, "📔")
        preview = smart_journal_service.button_preview(entry.content)
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"{icon} #{entry.id} {preview}",
                    callback_data=f"journal:view:{entry.id}",
                ),
            ]
        )
    rows.append([InlineKeyboardButton(text="◀️ К списку", callback_data=back_callback)])
    rows.append([InlineKeyboardButton(text="❌ Выйти", callback_data="journal:exit")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def journal_entry_view_keyboard(entry_id: int, *, back_callback: str = "journal:filter:idea") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🗑 Удалить", callback_data=f"journal:delete:{entry_id}"),
                InlineKeyboardButton(text="◀️ Назад", callback_data=back_callback),
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
                InlineKeyboardButton(text="🔄 Авто", callback_data="traffic:check"),
            ],
            [
                InlineKeyboardButton(text="🗺 Яндекс", callback_data="traffic:check:yandex"),
                InlineKeyboardButton(text="🗺 2ГИС", callback_data="traffic:check:dgis"),
                InlineKeyboardButton(text="🗺 Google", callback_data="traffic:check:google"),
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


def recon_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ Источник", callback_data="recon:add"),
                InlineKeyboardButton(text="📋 Список", callback_data="recon:list"),
            ],
            [
                InlineKeyboardButton(text="🔄 Проверить всё", callback_data="recon:check_all"),
            ],
        ]
    )


def recon_type_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🌐 Сайт/RSS", callback_data="recon:type:website"),
                InlineKeyboardButton(text="📢 Telegram", callback_data="recon:type:telegram"),
            ],
            [
                InlineKeyboardButton(text="📊 Эко-календарь", callback_data="recon:type:econ_calendar"),
            ],
            [
                InlineKeyboardButton(text="📸 Instagram", callback_data="recon:type:instagram"),
                InlineKeyboardButton(text="🎵 TikTok", callback_data="recon:type:tiktok"),
            ],
            [
                InlineKeyboardButton(text="❌ Отмена", callback_data="recon:cancel"),
            ],
        ]
    )


def recon_sources_keyboard(sources) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for src in sources[:10]:
        label = (src.label or src.url_or_handle)[:28]
        status = "✅" if src.enabled else "⏸"
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"{status} #{src.id} {label}",
                    callback_data=f"recon:src:{src.id}",
                ),
            ]
        )
    rows.append([InlineKeyboardButton(text="❌ Закрыть", callback_data="recon:cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def recon_interest_prompt_keyboard(source_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⏭ Без фильтра",
                    callback_data=f"recon:interest_skip:{source_id}",
                ),
            ],
            [
                InlineKeyboardButton(text="❌ Отмена", callback_data="recon:cancel"),
            ],
        ]
    )


def recon_source_actions_keyboard(source_id: int, *, enabled: bool) -> InlineKeyboardMarkup:
    toggle = "⏸ Выкл" if enabled else "✅ Вкл"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Проверить", callback_data=f"recon:check:{source_id}"),
                InlineKeyboardButton(text="🎯 Фильтр", callback_data=f"recon:filter:{source_id}"),
            ],
            [
                InlineKeyboardButton(text=toggle, callback_data=f"recon:toggle:{source_id}"),
                InlineKeyboardButton(text="🗑 Удалить", callback_data=f"recon:delete:{source_id}"),
            ],
            [
                InlineKeyboardButton(text="◀️ Назад", callback_data="recon:list"),
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
