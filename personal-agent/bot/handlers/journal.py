from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.inline import (
    journal_entries_keyboard,
    journal_entry_view_keyboard,
    journal_menu_keyboard,
)
from bot.states.notebook import NotebookStates
from bot.utils.menu_forward import try_forward_menu_button
from bot.utils.messages import answer_menu
from services.journal_service import journal_service
from services.smart_journal import smart_journal_service
from services.user_service import user_service

router = Router()
logger = logging.getLogger(__name__)

NOTEBOOK_BUTTON = "💡 Блокнот-Идеи"
NOTEBOOK_EMPTY_HINT = (
    "Пока пусто. Напишите идею, мысль или расход — я сам разложу по полочкам.\n"
    "Примеры:\n"
    "• «Идея: приложение для учёта трат»\n"
    "• «Решил не брать этот проект»\n"
    "• «Обед 350 песо»"
)
NOTEBOOK_MODE_ON = (
    "✍️ <b>Режим блокнота включён</b>\n"
    "Пишите или диктуйте — всё попадёт в дневник.\n"
    "Выйти: кнопка ❌ Выйти или любая кнопка меню."
)
TELEGRAM_TEXT_LIMIT = 4096


def _journal_back_callback(*, filter_kind: str | None, day_offset: int) -> str:
    if filter_kind == "idea":
        return "journal:filter:idea"
    if filter_kind == "thought":
        return "journal:filter:thought"
    if filter_kind == "expense":
        return "journal:filter:expense"
    if day_offset == -1:
        return "journal:yesterday"
    return "journal:today"


async def show_journal(
    message: Message,
    session: AsyncSession,
    *,
    day_offset: int = 0,
    filter_kind: str | None = None,
    enter_mode: bool = True,
    state: FSMContext | None = None,
    actor=None,
    edit: bool = False,
) -> None:
    tg_user = actor or message.from_user
    if not tg_user:
        return
    user = await user_service.get_or_create(
        session,
        telegram_id=tg_user.id,
        username=tg_user.username,
        first_name=tg_user.first_name,
    )
    day_key = smart_journal_service.day_key_for_user(user, offset_days=day_offset)
    ideas_feed = filter_kind == "idea" and day_offset == 0

    if ideas_feed:
        entries = await journal_service.list_ideas_recent(session, user, limit=12)
        title = "💡 Идеи — все недавние"
    else:
        entries = await journal_service.list_for_day(session, user, day_key, kind=filter_kind)
        if day_offset == -1:
            title = f"📔 Блокнот — вчера ({day_key})"
        elif filter_kind == "idea":
            title = f"💡 Идеи — {day_key}"
        elif filter_kind == "thought":
            title = f"💭 Мысли — {day_key}"
        elif filter_kind == "expense":
            title = f"💸 Траты — {day_key}"
        else:
            title = f"📔 Блокнот — сегодня ({day_key})"

    text = smart_journal_service.format_day_entries(
        entries,
        title=title,
        empty_hint=NOTEBOOK_EMPTY_HINT,
        filter_kind=filter_kind,
        timezone=user.timezone or "UTC",
        today_key=day_key,
        ideas_feed=ideas_feed,
    )

    if enter_mode and state is not None:
        await state.set_state(NotebookStates.writing)
        text = f"{text}\n\n{NOTEBOOK_MODE_ON}"

    if len(text) > TELEGRAM_TEXT_LIMIT:
        text = text[: TELEGRAM_TEXT_LIMIT - 20].rstrip() + "\n\n… (обрезано)"

    back_cb = _journal_back_callback(filter_kind=filter_kind, day_offset=day_offset)
    markup = (
        journal_entries_keyboard(entries, back_callback=back_cb)
        if entries
        else journal_menu_keyboard()
    )

    if edit:
        try:
            await message.edit_text(text, reply_markup=markup, parse_mode="HTML")
            return
        except TelegramBadRequest:
            logger.debug("Could not edit journal message")

    await answer_menu(message, text, reply_markup=markup, parse_mode="HTML")


async def capture_notebook_message(
    message: Message,
    session: AsyncSession,
    user,
    text: str,
) -> None:
    acks = await smart_journal_service.capture_text(session, user, text)
    if not acks:
        await answer_menu(message, "Не удалось сохранить. Попробуйте ещё раз.")
        return
    await answer_menu(
        message,
        "📔 <b>Записано:</b>\n" + "\n".join(f"• {line}" for line in acks),
        reply_markup=journal_menu_keyboard(),
        parse_mode="HTML",
    )


@router.message(Command("journal"))
@router.message(lambda m: m.text == NOTEBOOK_BUTTON)
async def cmd_journal(message: Message, session: AsyncSession, state: FSMContext) -> None:
    parts = (message.text or "").split(maxsplit=1)
    sub = parts[1].strip().lower() if len(parts) > 1 and message.text.startswith("/") else ""

    if sub in ("off", "выход", "exit"):
        await state.clear()
        await answer_menu(message, "Вышли из режима блокнота.")
        return

    if sub in ("summary", "сводка"):
        user = await user_service.get_or_create(
            session,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
        )
        await answer_menu(message, "⏳ Готовлю сводку…")
        summary = await smart_journal_service.summarize_day(session, user)
        await answer_menu(message, summary, reply_markup=journal_menu_keyboard(), parse_mode="HTML")
        return

    if sub in ("ideas", "идеи"):
        await show_journal(message, session, filter_kind="idea", state=state)
        return

    if sub in ("yesterday", "вчера"):
        await show_journal(message, session, day_offset=-1, enter_mode=False, state=state)
        return

    await show_journal(message, session, state=state)


@router.message(NotebookStates.writing, F.text)
async def msg_notebook_write(
    message: Message,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    if not message.text or message.text.startswith("/"):
        return
    if await try_forward_menu_button(message, session, state):
        return

    user = await user_service.get_or_create(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )
    await capture_notebook_message(message, session, user, message.text)


@router.callback_query(F.data == "journal:today")
async def cb_journal_today(callback: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    if not callback.message:
        await callback.answer()
        return
    await callback.answer()
    await show_journal(
        callback.message,
        session,
        state=state,
        actor=callback.from_user,
        edit=True,
    )


@router.callback_query(F.data == "journal:yesterday")
async def cb_journal_yesterday(callback: CallbackQuery, session: AsyncSession) -> None:
    if not callback.message:
        await callback.answer()
        return
    await callback.answer()
    await show_journal(
        callback.message,
        session,
        day_offset=-1,
        enter_mode=False,
        actor=callback.from_user,
        edit=True,
    )


@router.callback_query(F.data.startswith("journal:filter:"))
async def cb_journal_filter(callback: CallbackQuery, session: AsyncSession) -> None:
    if not callback.data or not callback.message:
        await callback.answer()
        return
    kind = callback.data.split(":")[-1]
    await callback.answer()
    await show_journal(
        callback.message,
        session,
        filter_kind=kind,
        enter_mode=False,
        actor=callback.from_user,
        edit=True,
    )


@router.callback_query(F.data.startswith("journal:view:"))
async def cb_journal_view(callback: CallbackQuery, session: AsyncSession) -> None:
    if not callback.data or not callback.from_user or not callback.message:
        await callback.answer()
        return
    entry_id = int(callback.data.split(":")[-1])
    user = await user_service.get_or_create(
        session,
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name,
    )
    entry = await journal_service.get_entry(session, user, entry_id)
    if not entry:
        await callback.answer("Запись не найдена", show_alert=True)
        return
    await callback.answer()
    back = "journal:filter:idea" if entry.kind == "idea" else "journal:today"
    text = smart_journal_service.format_entry_detail(entry, timezone=user.timezone or "UTC")
    try:
        await callback.message.edit_text(
            text,
            reply_markup=journal_entry_view_keyboard(entry.id, back_callback=back),
            parse_mode="HTML",
        )
    except TelegramBadRequest:
        await callback.message.answer(
            text,
            reply_markup=journal_entry_view_keyboard(entry.id, back_callback=back),
            parse_mode="HTML",
        )


@router.callback_query(F.data.startswith("journal:delete:"))
async def cb_journal_delete(callback: CallbackQuery, session: AsyncSession) -> None:
    if not callback.data or not callback.from_user or not callback.message:
        await callback.answer()
        return
    entry_id = int(callback.data.split(":")[-1])
    user = await user_service.get_or_create(
        session,
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name,
    )
    entry = await journal_service.get_entry(session, user, entry_id)
    ok = await journal_service.delete_entry(session, user, entry_id)
    await callback.answer("Удалено" if ok else "Не найдено")
    if not ok or not entry:
        return
    back_kind = entry.kind if entry.kind in ("idea", "thought", "expense") else None
    await show_journal(
        callback.message,
        session,
        filter_kind=back_kind,
        enter_mode=False,
        actor=callback.from_user,
        edit=True,
    )


@router.callback_query(F.data == "journal:summary")
async def cb_journal_summary(callback: CallbackQuery, session: AsyncSession) -> None:
    if not callback.from_user or not callback.message:
        await callback.answer()
        return
    user = await user_service.get_or_create(
        session,
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name,
    )
    await callback.answer("Готовлю сводку…")
    summary = await smart_journal_service.summarize_day(session, user)
    try:
        await callback.message.edit_text(summary, reply_markup=journal_menu_keyboard(), parse_mode="HTML")
    except TelegramBadRequest:
        await callback.message.answer(summary, reply_markup=journal_menu_keyboard(), parse_mode="HTML")


@router.callback_query(F.data == "journal:exit")
async def cb_journal_exit(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.answer("Вышли из блокнота")
    if callback.message:
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except TelegramBadRequest:
            pass
        await callback.message.answer("📔 Режим блокнота выключен. Открыть снова: кнопка «💡 Блокнот-Идеи».")


@router.message(Command("pulse"))
async def cmd_pulse(message: Message, session: AsyncSession) -> None:
    user = await user_service.get_or_create(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )
    parts = (message.text or "").split(maxsplit=1)
    arg = parts[1].strip().lower() if len(parts) > 1 else ""
    if arg in ("on", "вкл", "1"):
        user.pulse_enabled = True
        await answer_menu(
            message,
            f"💓 Пульс включён. Утро в {user.digest_hour}:00, днём — только если важно.",
        )
        return
    if arg in ("off", "выкл", "0"):
        user.pulse_enabled = False
        await answer_menu(message, "Пульс выключен.")
        return
    status = "включён" if user.pulse_enabled else "выключен"
    await answer_menu(
        message,
        f"💓 Пульс: <b>{status}</b>\n"
        f"Утро: {user.digest_hour}:00 · Ночь: {user.night_hour}:00\n"
        "/pulse on · /pulse off · /ambient · /night",
        parse_mode="HTML",
    )


@router.message(Command("ambient"))
async def cmd_ambient(message: Message, session: AsyncSession) -> None:
    user = await user_service.get_or_create(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )
    parts = (message.text or "").split(maxsplit=1)
    arg = parts[1].strip().lower() if len(parts) > 1 else ""
    if arg in ("on", "вкл"):
        user.ambient_enabled = True
        await answer_menu(message, "🌊 Ambient включён — ловлю траты, мысли и решения из обычного чата.")
        return
    if arg in ("off", "выкл"):
        user.ambient_enabled = False
        await answer_menu(message, "Ambient выключен.")
        return
    status = "включён" if user.ambient_enabled else "выключен"
    await answer_menu(
        message,
        f"🌊 Ambient: <b>{status}</b>\n"
        "Пиши как живому — «обед 500», «устал», «решил не брать проект».\n"
        "/ambient on · /ambient off",
        parse_mode="HTML",
    )


@router.message(Command("night"))
async def cmd_night(message: Message, session: AsyncSession) -> None:
    user = await user_service.get_or_create(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) > 1 and parts[1].strip().isdigit():
        hour = int(parts[1].strip())
        if 0 <= hour <= 23:
            user.night_hour = hour
            user.night_enabled = True
            await answer_menu(message, f"🌙 Ночной итог в <b>{hour}:00</b>.", parse_mode="HTML")
            return
    arg = parts[1].strip().lower() if len(parts) > 1 else ""
    if arg in ("on", "вкл"):
        user.night_enabled = True
        await answer_menu(message, f"🌙 Ночной итог включён ({user.night_hour}:00).")
        return
    if arg in ("off", "выкл"):
        user.night_enabled = False
        await answer_menu(message, "Ночной итог выключен.")
        return
    status = "включён" if user.night_enabled else "выключен"
    await answer_menu(
        message,
        f"🌙 Ночной итог: <b>{status}</b> ({user.night_hour}:00)\n"
        "/night on · /night off · /night 21",
        parse_mode="HTML",
    )
