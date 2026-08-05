from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from database.enums import Audience, Language, ProficiencyLevel


def audience_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="🧒 Ребёнок · игра и сказки", callback_data="audience:child")],
        [InlineKeyboardButton(text="🎒 Подросток · школа и общение", callback_data="audience:teen")],
        [InlineKeyboardButton(text="👔 Взрослый · карьера и путешествия", callback_data="audience:adult")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def language_keyboard() -> InlineKeyboardMarkup:
    labels = {
        Language.ENGLISH: "🇬🇧 English · Английский",
        Language.SPANISH: "🇪🇸 Español · Испанский",
        Language.GERMAN: "🇩🇪 Deutsch · Немецкий",
    }
    buttons = [
        [InlineKeyboardButton(text=label, callback_data=f"lang:{lang.value}")]
        for lang, label in labels.items()
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def level_keyboard(audience: str | None = None) -> InlineKeyboardMarkup:
    if audience == Audience.CHILD.value:
        labels = {
            ProficiencyLevel.BEGINNER: "🌱 Только начинаю",
            ProficiencyLevel.ELEMENTARY: "📗 Знаю слова и фразы",
            ProficiencyLevel.INTERMEDIATE: "🚀 Уже болтаю!",
        }
        levels = [
            ProficiencyLevel.BEGINNER,
            ProficiencyLevel.ELEMENTARY,
            ProficiencyLevel.INTERMEDIATE,
        ]
    elif audience == Audience.TEEN.value:
        labels = {
            ProficiencyLevel.BEGINNER: "A1 — С нуля",
            ProficiencyLevel.ELEMENTARY: "A2 — Школьный старт",
            ProficiencyLevel.INTERMEDIATE: "B1 — Уверенно",
            ProficiencyLevel.UPPER_INTERMEDIATE: "B2 — Сильный",
            ProficiencyLevel.ADVANCED: "C1 — Продвинутый",
        }
        levels = [
            ProficiencyLevel.BEGINNER,
            ProficiencyLevel.ELEMENTARY,
            ProficiencyLevel.INTERMEDIATE,
            ProficiencyLevel.UPPER_INTERMEDIATE,
            ProficiencyLevel.ADVANCED,
        ]
    else:
        labels = {
            ProficiencyLevel.BEGINNER: "A1 — Начальный",
            ProficiencyLevel.ELEMENTARY: "A2 — Элементарный",
            ProficiencyLevel.INTERMEDIATE: "B1 — Средний",
            ProficiencyLevel.UPPER_INTERMEDIATE: "B2 — Выше среднего",
            ProficiencyLevel.ADVANCED: "C1 — Продвинутый",
            ProficiencyLevel.NATIVE: "C2 — Профи",
        }
        levels = list(ProficiencyLevel)

    buttons = [
        [InlineKeyboardButton(text=labels[level], callback_data=f"level:{level.value}")]
        for level in levels
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def premium_menu_keyboard() -> InlineKeyboardMarkup:
    """Quick actions after onboarding — premium feel for kids & adults."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎙 Голосовой учитель Илья", callback_data="menu:voice_hint")],
            [InlineKeyboardButton(text="📚 Слова на сегодня", callback_data="menu:review")],
            [InlineKeyboardButton(text="✍️ Написать в чат", callback_data="menu:chat_hint")],
            [InlineKeyboardButton(text="⚙️ Сменить профиль", callback_data="menu:settings")],
        ]
    )


def vocab_rating_keyboard(card_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="😕 Забыл", callback_data=f"vocab:rate:{card_id}:1"),
                InlineKeyboardButton(text="😬 Сложно", callback_data=f"vocab:rate:{card_id}:2"),
            ],
            [
                InlineKeyboardButton(text="👍 Норм", callback_data=f"vocab:rate:{card_id}:3"),
                InlineKeyboardButton(text="🌟 Легко", callback_data=f"vocab:rate:{card_id}:4"),
            ],
        ]
    )
