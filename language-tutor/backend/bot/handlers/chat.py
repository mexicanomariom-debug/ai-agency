from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.reply import MENU_BUTTON_TEXTS
from bot.states.onboarding import OnboardingStates
from services.chat_service import process_user_text

router = Router()


@router.message(
    OnboardingStates.chatting,
    F.text,
    ~F.text.startswith("/"),
    ~F.text.in_(MENU_BUTTON_TEXTS),
)
async def handle_chat(message: Message, session: AsyncSession) -> None:
    await process_user_text(message, session, message.text)


@router.message(OnboardingStates.chatting, F.text)
async def handle_unknown_command(message: Message) -> None:
    await message.answer(
        "Не знаю такую команду. Используйте кнопки внизу или "
        "/help · /review · /progress · /test · /product"
    )


@router.message(
    StateFilter(
        OnboardingStates.choosing_audience,
        OnboardingStates.choosing_language,
        OnboardingStates.choosing_level,
    ),
    F.text,
)
async def handle_during_onboarding(message: Message) -> None:
    await message.answer("Выберите вариант кнопкой выше или начните заново: /start")


@router.message(F.text)
async def handle_unboarded(message: Message) -> None:
    await message.answer("Начни с /start, чтобы выбрать язык и уровень.")
