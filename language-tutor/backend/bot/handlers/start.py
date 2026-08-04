from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.inline import language_keyboard, level_keyboard, webapp_keyboard
from bot.states.onboarding import OnboardingStates
from config import settings
from database.enums import Language, ProficiencyLevel
from services.user_service import user_service

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, session: AsyncSession) -> None:
    user = await user_service.get_or_create(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
    )

    if user.is_onboarded and user.language and user.level:
        await state.set_state(OnboardingStates.chatting)
        await message.answer(
            f"Welcome back, {message.from_user.first_name or 'friend'}! "
            f"You're learning <b>{user.language.value.title()}</b> at "
            f"<b>{user.level.value.replace('_', ' ').title()}</b> level.\n\n"
            "Send me a message to practice, or open the Web App for persona tutors.",
            reply_markup=webapp_keyboard(),
        )
        return

    await state.set_state(OnboardingStates.choosing_language)
    await message.answer(
        "👋 Welcome to <b>Language Tutor</b>!\n\n"
        "I'll help you practice languages through conversation.\n\n"
        "First, which language would you like to learn?",
        reply_markup=language_keyboard(),
    )


@router.callback_query(F.data.startswith("lang:"))
async def choose_language(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    lang_value = callback.data.split(":", 1)[1]
    language = Language(lang_value)

    user = await user_service.get_or_create(session, telegram_id=callback.from_user.id)
    await user_service.set_language(session, user, language)

    await state.update_data(language=lang_value)
    await state.set_state(OnboardingStates.choosing_level)

    await callback.message.edit_text(
        f"Great choice! <b>{language.value.title()}</b> it is.\n\n"
        "What's your current level?",
        reply_markup=level_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("level:"))
async def choose_level(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    level_value = callback.data.split(":", 1)[1]
    level = ProficiencyLevel(level_value)

    user = await user_service.get_or_create(session, telegram_id=callback.from_user.id)
    await user_service.set_level(session, user, level)
    await user_service.complete_onboarding(session, user)

    await state.set_state(OnboardingStates.chatting)

    await callback.message.edit_text(
        f"Perfect! You're set up for <b>{user.language.value.title()}</b> "
        f"at <b>{level.value.replace('_', ' ').title()}</b> level.\n\n"
        "Start chatting with me now, or open the Web App to choose a persona tutor.",
        reply_markup=webapp_keyboard(),
    )
    await callback.answer()


@router.message(Command("webapp"))
async def cmd_webapp(message: Message) -> None:
    await message.answer(
        f"Open our Web App for persona tutors and more features:",
        reply_markup=webapp_keyboard(),
    )


@router.message(Command("reset"))
async def cmd_reset(message: Message, state: FSMContext, session: AsyncSession) -> None:
    user = await user_service.get_by_telegram_id(session, message.from_user.id)
    if user:
        user.is_onboarded = False
        user.language = None
        user.level = None

    await state.set_state(OnboardingStates.choosing_language)
    await message.answer(
        "Onboarding reset. Let's start over!\n\nWhich language would you like to learn?",
        reply_markup=language_keyboard(),
    )
