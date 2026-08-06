from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.copy import (
    CHAT_HINT,
    HELP_TEXT,
    READY_ADULT,
    READY_CHILD,
    READY_TEEN,
    VOICE_HINT,
    WELCOME_BACK,
    WELCOME_NEW,
)
from services.placement_service import PLACEMENT_INTRO
from bot.keyboards.inline import (
    audience_keyboard,
    language_keyboard,
    level_keyboard,
    hub_menu_keyboard,
)
from bot.states.onboarding import OnboardingStates
from services.user_service import user_service

router = Router()

LANGUAGE_LABELS = {
    "english": "🇬🇧 English",
    "spanish": "🇪🇸 Español",
    "german": "🇩🇪 Deutsch",
}

LEVEL_LABELS = {
    "beginner": "A1 — Начальный",
    "elementary": "A2 — Элементарный",
    "intermediate": "B1 — Средний",
    "upper_intermediate": "B2 — Выше среднего",
    "advanced": "C1 — Продвинутый",
    "native": "C2 — Профи",
}

AUDIENCE_LABELS = {
    "child": "🧒 Ребёнок",
    "teen": "🎒 Подросток",
    "adult": "👔 Взрослый",
}


def _profile_line(audience: str, lang: str, level: str) -> str:
    return (
        f"{AUDIENCE_LABELS.get(audience, audience)} · "
        f"{LANGUAGE_LABELS.get(lang, lang)} · {LEVEL_LABELS.get(level, level)}"
    )


def _ready_copy(audience: str, lang: str, level: str) -> str:
    line = _profile_line(audience, lang, level)
    if audience == "child":
        return READY_CHILD.format(profile_line=line)
    if audience == "teen":
        return READY_TEEN.format(profile_line=line)
    return READY_ADULT.format(profile_line=line)


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
        audience = user.audience.value if user.audience else "adult"
        await message.answer(
            WELCOME_BACK.format(
                name=name,
                audience=AUDIENCE_LABELS.get(audience, audience),
                language=LANGUAGE_LABELS.get(user.language.value, user.language.value),
                level=LEVEL_LABELS.get(user.level.value, user.level.value),
            ),
            reply_markup=hub_menu_keyboard(),
        )
        return

    await state.set_state(OnboardingStates.choosing_audience)
    await message.answer(
        WELCOME_NEW.format(name=name),
        reply_markup=audience_keyboard(),
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(HELP_TEXT)


@router.callback_query(F.data.startswith("audience:"))
async def choose_audience(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    audience_value = callback.data.split(":", 1)[1]
    user = await user_service.get_or_create(session, telegram_id=callback.from_user.id)
    from database.enums import Audience

    audience = Audience(audience_value)
    await user_service.set_audience(session, user, audience)
    await state.update_data(audience=audience_value)
    await state.set_state(OnboardingStates.choosing_language)

    if audience_value == "child":
        prompt = "Круто! Теперь выбери язык, который будем учить вместе:"
    elif audience_value == "teen":
        prompt = "Отлично. Какой язык качаем?"
    else:
        prompt = "Выберите язык обучения:"

    await callback.message.edit_text(
        f"{AUDIENCE_LABELS.get(audience_value, audience_value)} ✓\n\n{prompt}",
        reply_markup=language_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("lang:"))
async def choose_language(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    lang_value = callback.data.split(":", 1)[1]

    user = await user_service.get_or_create(session, telegram_id=callback.from_user.id)
    from database.enums import Language

    language = Language(lang_value)
    await user_service.set_language(session, user, language)

    data = await state.get_data()
    audience = data.get("audience") or (user.audience.value if user.audience else "adult")
    await state.update_data(audience=audience)
    await state.set_state(OnboardingStates.choosing_level)

    if audience == "child":
        level_prompt = "Как ты себя чувствуешь в этом языке?"
    else:
        level_prompt = "Выберите уровень владения:"

    await callback.message.edit_text(
        f"Язык: {LANGUAGE_LABELS.get(lang_value, lang_value)} ✓\n\n{level_prompt}",
        reply_markup=level_keyboard(audience),
    )
    await callback.answer()


@router.callback_query(F.data == "level:discover")
async def choose_level_discover(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    from database.enums import ProficiencyLevel

    user = await user_service.get_or_create(session, telegram_id=callback.from_user.id)
    await user_service.set_level(session, user, ProficiencyLevel.BEGINNER)
    await user_service.complete_onboarding(session, user)

    await state.set_state(OnboardingStates.placement_test)
    await callback.message.edit_text(
        "🤔 Не знаете уровень? Сначала короткий тест на русском.\n\n"
        + PLACEMENT_INTRO.replace("<b>", "").replace("</b>", ""),
    )
    await callback.answer()
    await callback.message.answer(
        "Напишите в чат, например: «Не знаю уровень» — и задам первый вопрос."
    )


@router.callback_query(F.data.startswith("level:"))
async def choose_level(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    level_value = callback.data.split(":", 1)[1]
    if level_value == "discover":
        await callback.answer()
        return

    user = await user_service.get_or_create(session, telegram_id=callback.from_user.id)
    from database.enums import ProficiencyLevel

    level = ProficiencyLevel(level_value)
    await user_service.set_level(session, user, level)
    await user_service.complete_onboarding(session, user)

    data = await state.get_data()
    audience = data.get("audience") or (user.audience.value if user.audience else "adult")
    lang = user.language.value if user.language else ""

    await state.set_state(OnboardingStates.chatting)
    await callback.message.edit_text(
        _ready_copy(audience, lang, level_value),
        reply_markup=hub_menu_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "menu:voice_hint")
async def menu_voice_hint(callback: CallbackQuery) -> None:
    await callback.message.answer(VOICE_HINT)
    await callback.answer()


@router.callback_query(F.data == "menu:chat_hint")
async def menu_chat_hint(callback: CallbackQuery) -> None:
    await callback.message.answer(CHAT_HINT)
    await callback.answer()


@router.callback_query(F.data == "menu:settings")
async def menu_settings(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    await _reset_settings(callback.from_user.id, state, session)
    await callback.message.answer(
        "⚙️ Профиль сброшен. Для кого занятия?",
        reply_markup=audience_keyboard(),
    )
    await callback.answer()


@router.message(Command("settings"))
async def cmd_reset(message: Message, state: FSMContext, session: AsyncSession) -> None:
    await _reset_settings(message.from_user.id, state, session)
    await message.answer(
        "⚙️ Настройки сброшены.\n\nДля кого занятия?",
        reply_markup=audience_keyboard(),
    )


async def _reset_settings(telegram_id: int, state: FSMContext, session: AsyncSession) -> None:
    user = await user_service.get_by_telegram_id(session, telegram_id)
    if user:
        user.is_onboarded = False
        user.language = None
        user.level = None
        user.audience = None
        await session.commit()
    await state.clear()
    await state.set_state(OnboardingStates.choosing_audience)
