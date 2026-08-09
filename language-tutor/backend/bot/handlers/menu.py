"""Reply-keyboard menu actions (bottom Telegram buttons)."""

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.copy import HELP_TEXT
from bot.keyboards.reply import (
    BTN_FINISH,
    BTN_HELP,
    BTN_PROGRESS,
    BTN_REVIEW,
    BTN_SETTINGS,
    BTN_START_LESSON,
    BTN_TEST,
    main_menu_keyboard,
)
from bot.states.onboarding import OnboardingStates
from services.chat_service import process_user_text
from services.user_service import user_service

router = Router()


@router.message(F.text == BTN_START_LESSON)
async def menu_start_lesson(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    user = await user_service.get_by_telegram_id(session, message.from_user.id)
    if not user or not user.is_onboarded:
        await message.answer("Сначала пройди онбординг: /start")
        return

    await state.set_state(OnboardingStates.chatting)
    await message.answer(
        "🚀 Начинаем обучение.\n"
        "Пишите текстом или отправьте голосовое — отвечу текстом.",
        reply_markup=main_menu_keyboard(),
    )
    await process_user_text(
        message,
        session,
        (
            "Давай начнём урок. Предложи одну тему под мой уровень и цель, "
            "задай первый короткий вопрос для практики."
        ),
    )


@router.message(F.text == BTN_TEST)
async def menu_btn_test(message: Message, state: FSMContext, session: AsyncSession) -> None:
    from bot.handlers.placement import _start_placement_test

    await _start_placement_test(message, state, session)


@router.message(F.text == BTN_REVIEW)
async def menu_btn_review(message: Message, session: AsyncSession) -> None:
    from bot.handlers.vocab import _send_review_session

    await _send_review_session(message, session, message.from_user.id)


@router.message(F.text == BTN_PROGRESS)
async def menu_btn_progress(message: Message, session: AsyncSession) -> None:
    from bot.handlers.progress import _send_progress

    await _send_progress(message, session, message.from_user.id)


@router.message(F.text == BTN_FINISH)
async def menu_btn_finish(message: Message, session: AsyncSession) -> None:
    from bot.handlers.session import _finish_lesson

    await _finish_lesson(message, session, message.from_user.id)


@router.message(F.text == BTN_SETTINGS)
async def menu_btn_settings(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    from bot.handlers.start import _reset_settings
    from bot.keyboards.inline import audience_keyboard

    await _reset_settings(message.from_user.id, state, session)
    await message.answer(
        "⚙️ Профиль сброшен. Для кого занятия?",
        reply_markup=audience_keyboard(),
    )


@router.message(F.text == BTN_HELP)
async def menu_btn_help(message: Message) -> None:
    await message.answer(HELP_TEXT, reply_markup=main_menu_keyboard())
