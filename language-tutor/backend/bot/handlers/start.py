from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.inline import (
    audience_keyboard,
    language_keyboard,
    level_keyboard,
    premium_menu_keyboard,
)
from bot.states.onboarding import OnboardingStates
from services.placement_service import PLACEMENT_INTRO
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


def _welcome_copy(name: str) -> str:
    return (
        f"✦ <b>Opus 5 Concierge</b>\n"
        f"Добро пожаловать, {name}.\n\n"
        "Премиальный AI-репетитор с живым 3D-учителем Еленой — "
        "для детей с игровой атмосферой и для взрослых с деловой точностью.\n\n"
        "<b>Для кого занятия?</b>"
    )


def _ready_copy(audience: str, lang: str, level: str) -> str:
    if audience == "child":
        return (
            f"🎉 Профиль готов!\n"
            f"{AUDIENCE_LABELS.get(audience, audience)} · "
            f"{LANGUAGE_LABELS.get(lang, lang)} · {LEVEL_LABELS.get(level, level)}\n\n"
            "Елена уже ждёт тебя — можно писать в чат или нажать синюю кнопку "
            "«Учитель — общение» и поговорить вслух. Давай играть словами!"
        )
    if audience == "teen":
        return (
            f"✅ Профиль собран\n"
            f"{AUDIENCE_LABELS.get(audience, audience)} · "
            f"{LANGUAGE_LABELS.get(lang, lang)} · {LEVEL_LABELS.get(level, level)}\n\n"
            "Пиши в чат или открой синюю кнопку «Учитель — общение» — "
            "живой 3D-учитель поможет с школой, экзаменами и живым общением."
        )
    return (
        f"✦ Профиль активирован\n"
        f"{AUDIENCE_LABELS.get(audience, audience)} · "
        f"{LANGUAGE_LABELS.get(lang, lang)} · {LEVEL_LABELS.get(level, level)}\n\n"
        "Пишите в чат или откройте синюю кнопку «Учитель — общение» — "
        "голосовой 3D-репетитор Елена для переговоров, путешествий и точности речи."
    )


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
            f"С возвращением, {name}.\n\n"
            f"✦ <b>Ваш concierge-профиль</b>\n"
            f"Аудитория: {AUDIENCE_LABELS.get(audience, audience)}\n"
            f"Язык: {LANGUAGE_LABELS.get(user.language.value, user.language.value)}\n"
            f"Уровень: {LEVEL_LABELS.get(user.level.value, user.level.value)}\n\n"
            "• Чат — текст и голосовые\n"
            "• Синяя кнопка «Учитель — общение» — 3D-учитель Елена\n"
            "• /review — слова на сегодня (FSRS)\n"
            "• /test — мини-тест уровня на русском + программа (/program)\n"
            "• /progress — ваш прогресс и CEFR",
            reply_markup=premium_menu_keyboard(),
        )
        return

    await state.set_state(OnboardingStates.choosing_audience)
    await message.answer(
        _welcome_copy(name),
        reply_markup=audience_keyboard(),
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        "✦ <b>Opus 5 · как заниматься</b>\n\n"
        "1. <b>Чат</b> — пишите или отправляйте голосовые\n"
        "2. <b>Учитель — общение</b> — синяя кнопка: 3D-учитель говорит губами в реальном времени\n"
        "3. <b>/review</b> — повторить слова (FSRS)\n"
        "4. <b>/test</b> — мини-тест уровня на русском, затем <b>/program</b>\n"
        "5. <b>/progress</b> — прогресс и CEFR\n"
        "6. <b>/settings</b> — сменить профиль\n\n"
        "Ребёнку — игры и сказки. Взрослому — точность и деловой тон."
    )


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
        "🤔 Не знаете уровень? Отлично — сначала короткий тест на русском.\n\n"
        + PLACEMENT_INTRO.replace("<b>", "").replace("</b>", ""),
    )
    await callback.answer()
    await callback.message.answer(
        "Напишите в чат, например: «Не знаю уровень, хочу учить язык» — "
        "и я задам первый вопрос."
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
        reply_markup=premium_menu_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "menu:voice_hint")
async def menu_voice_hint(callback: CallbackQuery) -> None:
    await callback.message.answer(
        "🎙 Нажмите синюю кнопку «Учитель — общение» слева от поля ввода — "
        "откроется 3D-учитель Елена. Удерживайте микрофон и говорите."
    )
    await callback.answer()


@router.callback_query(F.data == "menu:chat_hint")
async def menu_chat_hint(callback: CallbackQuery) -> None:
    await callback.message.answer(
        "✍️ Просто напишите сообщение в этот чат — или пришлите голосовое. "
        "Репетитор ответит с учётом вашего профиля."
    )
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
