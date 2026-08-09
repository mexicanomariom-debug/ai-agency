from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.copy import (
    TRANSLATE_EXIT,
    TRANSLATE_LANG_SET,
    TRANSLATE_NEED_OPENAI,
    TRANSLATE_PROMPT,
    TRANSLATE_RESULT,
    TRANSLATE_SAME_LANG,
    TRANSLATE_UNKNOWN_LANG,
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


async def translate_user_text(
    message: Message,
    session: AsyncSession,
    text: str,
    *,
    explicit_target: str | None = None,
) -> bool:
    user = await user_service.get_or_create(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )
    return await _translate_and_reply(
        message,
        text,
        user_preferred_lang=user.translate_target_lang,
        explicit_target=explicit_target,
    )


async def _translate_and_reply(
    message: Message,
    text: str,
    *,
    user_preferred_lang: str = "en",
    explicit_target: str | None = None,
) -> bool:
    parsed = translator_service.parse_inline_request(text)
    if parsed:
        body = parsed.text
        target = parsed.target_lang or explicit_target or AUTO_LANG
    else:
        prefixed = translator_service.parse_target_prefix(text)
        if prefixed:
            body = prefixed.text
            target = prefixed.target_lang or AUTO_LANG
        else:
            body = text
            target = explicit_target or AUTO_LANG

    result = await translator_service.translate(
        body,
        target,
        user_preferred_lang=user_preferred_lang,
    )
    if not result:
        await answer_menu(message, TRANSLATE_SAME_LANG)
        return False

    await answer_menu(
        message,
        TRANSLATE_RESULT.format(
            source_lang=translator_service.language_label(result.source_lang),
            target_lang=translator_service.language_label(result.target_lang),
            source=result.source_text,
            translation=result.translated_text,
        ),
    )
    return True


def is_translate_request(text: str) -> bool:
    if translator_service.parse_inline_request(text):
        return True
    if translator_service.parse_target_prefix(text):
        return True
    lower = text.strip().lower()
    return lower.startswith(("переведи", "перевод", "translate"))


@router.message(Command("translate"))
@router.message(lambda m: m.text == "🌐 Переводчик")
async def cmd_translator(message: Message, state: FSMContext) -> None:
    await _enter_translator(message, state)


@router.message(Command("translate_off"))
async def cmd_translate_off(message: Message, state: FSMContext) -> None:
    await state.clear()
    await answer_menu(message, TRANSLATE_EXIT)


@router.message(Command("translate_lang"))
async def cmd_translate_lang(message: Message, session: AsyncSession) -> None:
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await answer_menu(
            message,
            "Язык для перевода с русского (когда текст уже на русском):\n"
            "/translate_lang en — English\n"
            "/translate_lang es — Español\n"
            "/translate_lang de — Deutsch\n"
            "/translate_lang fr — Français",
        )
        return

    user = await user_service.get_or_create(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )
    code = translator_service.resolve_alias(parts[1].strip()) or parts[1].strip().lower()
    if not await user_service.set_translate_lang(session, user, code):
        await answer_menu(message, TRANSLATE_UNKNOWN_LANG)
        return
    await answer_menu(
        message,
        TRANSLATE_LANG_SET.format(lang=translator_service.language_label(user.translate_target_lang)),
    )


@router.message(TranslatorStates.waiting_text, F.text)
async def handle_translate_text(message: Message, session: AsyncSession, state: FSMContext) -> None:
    if message.text in ("❌ Выйти", "/translate_off"):
        await state.clear()
        await answer_menu(message, TRANSLATE_EXIT)
        return

    await message.bot.send_chat_action(message.chat.id, "typing")
    await translate_user_text(message, session, message.text or "")


@router.message(TranslatorStates.waiting_text, F.voice)
async def handle_translate_voice(message: Message, session: AsyncSession, state: FSMContext) -> None:
    from bot.handlers.voice import transcribe_for_user

    await message.bot.send_chat_action(message.chat.id, "typing")
    text = await transcribe_for_user(message, in_translator=True)
    if not text:
        return
    await translate_user_text(message, session, text)
