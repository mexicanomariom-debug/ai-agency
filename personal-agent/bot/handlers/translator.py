from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.copy import (
    TRANSLATE_EXIT,
    TRANSLATE_NEED_OPENAI,
    TRANSLATE_PROMPT,
    TRANSLATE_RESULT,
)
from bot.states.translator import TranslatorStates
from bot.utils.messages import answer_menu
from services.translator import translator_service
from services.user_service import user_service

router = Router()

AUTO_LANG = "auto"


async def _enter_translator(message: Message, state: FSMContext) -> None:
    if not translator_service.available:
        await answer_menu(message, TRANSLATE_NEED_OPENAI)
        return

    await state.set_state(TranslatorStates.waiting_text)
    await answer_menu(message, TRANSLATE_PROMPT)


async def _translate_and_reply(message: Message, text: str) -> bool:
    result = await translator_service.translate(text, AUTO_LANG)
    if not result:
        await answer_menu(message, "Не удалось перевести. Попробуйте ещё раз.")
        return False

    await answer_menu(
        message,
        TRANSLATE_RESULT.format(
            source_lang=result.source_lang,
            target_lang=result.target_lang,
            source=result.source_text,
            translation=result.translated_text,
        ),
    )
    return True


@router.message(Command("translate"))
@router.message(lambda m: m.text == "🌐 Переводчик")
async def cmd_translator(message: Message, state: FSMContext) -> None:
    await _enter_translator(message, state)


@router.message(Command("translate_off"))
async def cmd_translate_off(message: Message, state: FSMContext) -> None:
    await state.clear()
    await answer_menu(message, TRANSLATE_EXIT)


@router.message(TranslatorStates.waiting_text, F.text)
async def handle_translate_text(message: Message, session: AsyncSession, state: FSMContext) -> None:
    if message.text in ("❌ Выйти", "/translate_off"):
        await state.clear()
        await answer_menu(message, TRANSLATE_EXIT)
        return

    await user_service.get_or_create(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )

    await message.bot.send_chat_action(message.chat.id, "typing")
    await _translate_and_reply(message, message.text)
