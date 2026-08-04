from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

from config import settings
from database.enums import Language, ProficiencyLevel


def language_keyboard() -> InlineKeyboardMarkup:
    labels = {
        Language.ENGLISH: "🇬🇧 English",
        Language.SPANISH: "🇪🇸 Español",
        Language.GERMAN: "🇩🇪 Deutsch",
    }
    buttons = [
        [InlineKeyboardButton(text=label, callback_data=f"lang:{lang.value}")]
        for lang, label in labels.items()
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def level_keyboard() -> InlineKeyboardMarkup:
    labels = {
        ProficiencyLevel.BEGINNER: "A1 — Начальный",
        ProficiencyLevel.ELEMENTARY: "A2 — Элементарный",
        ProficiencyLevel.INTERMEDIATE: "B1 — Средний",
        ProficiencyLevel.UPPER_INTERMEDIATE: "B2 — Выше среднего",
        ProficiencyLevel.ADVANCED: "C1 — Продвинутый",
        ProficiencyLevel.NATIVE: "C2 — Профи",
    }
    buttons = [
        [InlineKeyboardButton(text=labels[level], callback_data=f"level:{level.value}")]
        for level in ProficiencyLevel
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def webapp_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🌐 Открыть Web App",
                    web_app=WebAppInfo(url=f"{settings.twa_url}/app"),
                )
            ]
        ]
    )
