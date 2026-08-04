from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

from config import settings
from database.enums import Language, ProficiencyLevel


def language_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=lang.value.title(), callback_data=f"lang:{lang.value}")]
        for lang in Language
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def level_keyboard() -> InlineKeyboardMarkup:
    labels = {
        ProficiencyLevel.BEGINNER: "Beginner (A1)",
        ProficiencyLevel.ELEMENTARY: "Elementary (A2)",
        ProficiencyLevel.INTERMEDIATE: "Intermediate (B1)",
        ProficiencyLevel.UPPER_INTERMEDIATE: "Upper Intermediate (B2)",
        ProficiencyLevel.ADVANCED: "Advanced (C1)",
        ProficiencyLevel.NATIVE: "Native (C2)",
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
                    text="Open Web App",
                    web_app=WebAppInfo(url=f"{settings.twa_url}/app"),
                )
            ]
        ]
    )
