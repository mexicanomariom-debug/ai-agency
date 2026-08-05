from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.inline import language_keyboard, level_keyboard
from bot.states.onboarding import OnboardingStates
from services.user_service import user_service

router = Router()

LANGUAGE_LABELS = {
    "english": "🇬🇧 English",
    "spanish": "🇪🇸 Español",
    "german": "🇩🇪 Deutsch",
}

LEVEL_LABELS = {
    "beginner": "A1",
    "elementary": "A2",
    "intermediate": "B1",
    "upper_intermediate": "B2",
    "advanced": "C1",
    "native": "C2",
}


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, session: AsyncSession) -> None:
    user = await user_service.get_or_create(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
    )

    name = message.from_user.first_name or "друг"

    if user.is_onboarded and user.language and user.level:
        await state.set_state(OnboardingStates.chatting)
        await message.answer(
            f"С возвращением, {name}! 👋\n\n"
            f"🗣 Язык: {LANGUAGE_LABELS.get(user.language.value, user.language.value)}\n"
            f"📊 Уровень: {LEVEL_LABELS.get(user.level.value, user.level.value)}\n\n"
            "Пиши сообщение или отправь голосовое — начнём практику!",
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    await state.set_state(OnboardingStates.choosing_language)
    await message.answer(
        f"Привет, {name}! 👋\n\n"
        "Я — AI-репетитор по школьной программе ФГОС.\n"
        "Помогу практиковать <b>английский</b>, <b>испанский</b> или <b>немецкий</b>.\n\n"
        "Выбери язык:",
        reply_markup=language_keyboard(),
    )


@router.callback_query(F.data.startswith("lang:"))
async def choose_language(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    lang_value = callback.data.split(":", 1)[1]

    user = await user_service.get_or_create(session, telegram_id=callback.from_user.id)
    from database.enums import Language

    language = Language(lang_value)
    await user_service.set_language(session, user, language)

    await state.set_state(OnboardingStates.choosing_level)
    await callback.message.edit_text(
        f"Отлично! Язык: {LANGUAGE_LABELS.get(lang_value, lang_value)}\n\n"
        "Выбери свой уровень:",
        reply_markup=level_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("level:"))
async def choose_level(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    level_value = callback.data.split(":", 1)[1]

    user = await user_service.get_or_create(session, telegram_id=callback.from_user.id)
    from database.enums import ProficiencyLevel

    level = ProficiencyLevel(level_value)
    await user_service.set_level(session, user, level)
    await user_service.complete_onboarding(session, user)

    await state.set_state(OnboardingStates.chatting)
    await callback.message.edit_text(
        f"Уровень: {LEVEL_LABELS.get(level_value, level_value)} ✅\n\n"
        "Всё готово! Напиши первое сообщение на выбранном языке\n"
        "или отправь голосовое сообщение."
    )
    await callback.answer()


@router.message(Command("settings"))
async def cmd_reset(message: Message, state: FSMContext, session: AsyncSession) -> None:
    user = await user_service.get_by_telegram_id(session, message.from_user.id)
    if user:
        user.is_onboarded = False
        user.language = None
        user.level = None
        await session.commit()

    await state.set_state(OnboardingStates.choosing_language)
    await message.answer(
        "⚙️ Настройки сброшены. Выбери язык:",
        reply_markup=language_keyboard(),
    )
