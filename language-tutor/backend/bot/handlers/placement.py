import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.states.onboarding import OnboardingStates
from bot.utils.callbacks import usable_message
from database.enums import ProficiencyLevel
from services.chat_service import process_user_text
from services.placement_service import PLACEMENT_INTRO, placement_service
from services.user_service import user_service

logger = logging.getLogger(__name__)

router = Router()


async def _start_placement_test(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    user = await user_service.get_by_telegram_id(session, message.from_user.id)
    if not user or not user.is_onboarded:
        await message.answer("Сначала пройди онбординг: /start")
        return

    await state.set_state(OnboardingStates.placement_test)
    await message.answer(PLACEMENT_INTRO)
    await process_user_text(
        message,
        session,
        "Начни мини-тест уровня. Я не знаю свой уровень — задай первый вопрос.",
        placement_mode=True,
    )


@router.message(Command("test"))
async def cmd_test(message: Message, state: FSMContext, session: AsyncSession) -> None:
    await _start_placement_test(message, state, session)


@router.callback_query(F.data == "menu:test")
async def menu_test(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    target = usable_message(callback)
    await callback.answer()
    if target is not None:
        await _start_placement_test(target, state, session)


@router.message(OnboardingStates.placement_test, Command("program"))
async def cmd_program_in_test(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    await _finish_placement(message, state, session)


@router.message(Command("program"))
async def cmd_program(message: Message, state: FSMContext, session: AsyncSession) -> None:
    user = await user_service.get_by_telegram_id(session, message.from_user.id)
    if not user or not user.is_onboarded:
        await message.answer("Сначала пройди онбординг: /start")
        return
    await _finish_placement(message, state, session)


async def _finish_placement(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    user = await user_service.get_by_telegram_id(session, message.from_user.id)
    if not user:
        await message.answer("Нужен /start")
        return

    await message.bot.send_chat_action(message.chat.id, "typing")
    try:
        result = await placement_service.finalize(session, user)
    except Exception:
        # LLM timeouts and malformed JSON must not strand the user in test mode.
        logger.exception("Placement finalize failed")
        await state.set_state(OnboardingStates.chatting)
        await message.answer(
            "Не получилось собрать программу. Попробуйте /program ещё раз через минуту."
        )
        return

    await session.commit()
    await state.set_state(OnboardingStates.chatting)

    if not result.success:
        await message.answer(
            "Нужно больше ответов в тесте. Напишите /test и ответьте на 3–5 вопросов, "
            "затем снова /program."
        )
        return

    lines = ["📚 <b>Ваша программа</b>"]
    if result.speaking_cefr:
        lines.append(f"Уровень: <b>CEFR {result.speaking_cefr}</b>")
        if result.level_updated:
            lines.append("Профиль обновлён ✓")
    if result.summary:
        lines.append(f"\n{result.summary}")
    if result.program:
        lines.append(f"\n{result.program}")
    await message.answer("\n".join(lines))


@router.message(OnboardingStates.placement_test, Command("cancel"))
async def cmd_cancel_test(message: Message, state: FSMContext) -> None:
    await state.set_state(OnboardingStates.chatting)
    await message.answer("Тест отменён. Продолжаем обычный чат или /test снова.")


@router.message(OnboardingStates.placement_test, F.text, ~F.text.startswith("/"))
async def placement_chat(message: Message, session: AsyncSession) -> None:
    await process_user_text(message, session, message.text, placement_mode=True)


@router.message(OnboardingStates.placement_test)
async def placement_unsupported(message: Message) -> None:
    await message.answer(
        "В тесте отправьте текст или голосовое сообщение, либо /program для итогов."
    )
