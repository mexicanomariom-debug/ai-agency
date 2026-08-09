from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.copy import (
    TRANSLATE_EXIT,
    TRANSLATE_NEED_OPENAI,
    TRANSLATE_PROMPT,
    TRANSLATE_RESULT,
)
from bot.keyboards.inline import translator_languages_keyboard
from bot.states.translator import TranslatorStates
from services.translator import translator_service
from services.user_service import user_service

router = Router()


async def _enter_translator(message: Message, session: AsyncSession, state: FSMContext) -> None:
    user = await user_service.get_or_create(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )
    if not translator_service.available:
        await message.answer(TRANSLATE_NEED_OPENAI)
        return

    target = user.translate_target_lang or "en"
    await state.set_state(TranslatorStates.waiting_text)
    await message.answer(
        TRANSLATE_PROMPT.format(lang=translator_service.language_label(target)),
        reply_markup=translator_languages_keyboard(target),
    )


async def _translate_and_reply(
    message: Message,
    session: AsyncSession,
    text: str,
    target_lang: str,
) -> bool:
    result = await translator_service.translate(text, target_lang)
    if not result:
        await message.answer("Не удалось перевести. Попробуйте ещё раз.")
        return False

    await message.answer(
        TRANSLATE_RESULT.format(
            source_lang=result.source_lang,
            target_lang=result.target_lang,
            source=result.source_text,
            translation=result.translated_text,
        )
    )
    return True


@router.message(Command("translate"))
@router.message(lambda m: m.text == "🌐 Переводчик")
async def cmd_translator(message: Message, session: AsyncSession, state: FSMContext) -> None:
    await _enter_translator(message, session, state)


@router.callback_query(F.data.startswith("tr:lang:"))
async def cb_set_language(callback: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    lang = callback.data.split(":")[-1]
    user = await user_service.get_or_create(
        session,
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name,
    )
    await user_service.set_translate_lang(session, user, lang)
    await state.set_state(TranslatorStates.waiting_text)
    await callback.answer(f"Язык: {translator_service.language_label(lang)}")
    await callback.message.edit_text(
        TRANSLATE_PROMPT.format(lang=translator_service.language_label(lang)),
        reply_markup=translator_languages_keyboard(lang),
    )


@router.callback_query(F.data == "tr:exit")
async def cb_exit_translator(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.answer("Переводчик закрыт")
    await callback.message.edit_text(TRANSLATE_EXIT)


@router.message(Command("translate_off"))
async def cmd_translate_off(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(TRANSLATE_EXIT)


@router.message(TranslatorStates.waiting_text, F.text)
async def handle_translate_text(message: Message, session: AsyncSession, state: FSMContext) -> None:
    if message.text in ("❌ Выйти", "/translate_off"):
        await state.clear()
        await message.answer(TRANSLATE_EXIT)
        return

    user = await user_service.get_or_create(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )
    target = user.translate_target_lang or "en"
    text = message.text

    await message.bot.send_chat_action(message.chat.id, "typing")
    await _translate_and_reply(message, session, text, target)
