"""Разведка и Вериф — мониторинг источников и верификация."""

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.inline import (
    recon_menu_keyboard,
    recon_source_actions_keyboard,
    recon_sources_keyboard,
    recon_type_keyboard,
)
from bot.middlewares.translator import MENU_BUTTONS
from bot.states.recon import ReconSetupStates
from bot.utils.messages import answer_menu
from database.models import ReconSourceType
from services.recon import format_event_message, get_recon_monitor
from services.recon_providers import fetch_source_content
from services.recon_service import SOURCE_TYPE_LABELS, VERDICT_LABELS, recon_service
from services.recon_verifier import recon_verifier
from services.user_service import user_service

logger = logging.getLogger(__name__)

router = Router(name="recon")

RECON_BUTTON = "🔍 Разведка и Вериф"


def _panel_text(sources_count: int, enabled_count: int) -> str:
    return (
        "🔍 <b>Разведка и Вериф</b>\n\n"
        "Мониторинг сайтов, Telegram, эко-календаря и соцсетей.\n"
        "При изменениях — AI-верификация достоверности.\n\n"
        f"Источников: {sources_count} (активных: {enabled_count})\n\n"
        "<b>Добавить:</b> ➕ Источник\n"
        "<b>Верифицировать текст:</b> /recon verify ваш текст\n"
        "или перешлите сообщение с подписью <code>вериф:</code>"
    )


async def show_recon_panel(message: Message, session: AsyncSession) -> None:
    user = await user_service.get_or_create(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )
    sources = await recon_service.list_sources(session, user)
    enabled = sum(1 for s in sources if s.enabled)
    await answer_menu(
        message,
        _panel_text(len(sources), enabled),
        reply_markup=recon_menu_keyboard(),
    )


@router.message(Command("recon"))
@router.message(lambda m: m.text == RECON_BUTTON)
async def cmd_recon(message: Message, session: AsyncSession, state: FSMContext) -> None:
    if not message.text or not message.from_user:
        return

    parts = message.text.split(maxsplit=2)
    sub = parts[1].lower() if len(parts) > 1 and message.text.startswith("/") else ""

    if sub == "verify" and len(parts) > 2:
        claim = parts[2].strip()
        await _verify_claim(message, claim)
        return

    if sub == "list":
        await _show_sources(message, session)
        return

    await show_recon_panel(message, session)


@router.message(F.text.startswith("вериф:"))
async def msg_verify_prefix(message: Message) -> None:
    if not message.text:
        return
    claim = message.text.split(":", 1)[-1].strip()
    if claim:
        await _verify_claim(message, claim)


async def _verify_claim(message: Message, claim: str) -> None:
    await answer_menu(message, "⏳ Верифицирую…")
    result = await recon_verifier.verify_claim(claim)
    verdict = VERDICT_LABELS.get(result.verdict, result.verdict)
    conf = f"{int(result.confidence * 100)}%"
    await answer_menu(
        message,
        f"🔍 <b>Верификация</b>\n\n{verdict} ({conf})\n\n{result.summary}",
        parse_mode="HTML",
    )


async def _show_sources(message: Message, session: AsyncSession) -> None:
    user = await user_service.get_or_create(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )
    sources = await recon_service.list_sources(session, user)
    if not sources:
        await answer_menu(message, "Список пуст. Нажмите ➕ Источник.", reply_markup=recon_menu_keyboard())
        return
    lines = ["📋 <b>Источники</b>\n"]
    for src in sources[:15]:
        type_label = SOURCE_TYPE_LABELS.get(src.source_type, src.source_type)
        name = src.label or src.url_or_handle
        status = "✅" if src.enabled else "⏸"
        lines.append(f"{status} #{src.id} {type_label}: {name[:50]}")
    await answer_menu(
        message,
        "\n".join(lines),
        reply_markup=recon_sources_keyboard(sources),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "recon:add")
async def cb_recon_add(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(ReconSetupStates.waiting_type)
    if callback.message:
        await callback.message.answer(
            "➕ <b>Новый источник</b>\n\nВыберите тип:",
            reply_markup=recon_type_keyboard(),
            parse_mode="HTML",
        )


@router.callback_query(F.data.startswith("recon:type:"))
async def cb_recon_type(callback: CallbackQuery, state: FSMContext) -> None:
    if not callback.data:
        await callback.answer()
        return
    source_type = callback.data.split(":")[-1]
    await state.update_data(recon_source_type=source_type)
    await state.set_state(ReconSetupStates.waiting_url)
    await callback.answer()

    hints = {
        "website": "URL сайта или RSS:\n• https://example.com/news\n• https://site.com/feed.xml",
        "telegram": "Публичный канал:\n• @channelname\n• https://t.me/channelname",
        "instagram": "Ссылка на профиль Instagram:\n• https://instagram.com/username",
        "tiktok": "Ссылка на профиль TikTok:\n• https://tiktok.com/@username",
        "econ_calendar": "Экономический календарь — введите <code>auto</code> или любой текст",
    }
    label = SOURCE_TYPE_LABELS.get(source_type, source_type)
    if callback.message:
        await callback.message.answer(
            f"{label}\n\n{hints.get(source_type, 'Укажите адрес:')}",
            parse_mode="HTML",
        )


@router.message(ReconSetupStates.waiting_url, F.text)
async def msg_recon_url(message: Message, state: FSMContext) -> None:
    if not message.text or message.text.startswith("/") or message.text in MENU_BUTTONS:
        return
    data = await state.get_data()
    source_type = data.get("recon_source_type")
    url = message.text.strip()
    if source_type == ReconSourceType.ECON_CALENDAR.value:
        url = "ff_calendar_thisweek"
    await state.update_data(recon_url=url)
    await state.set_state(ReconSetupStates.waiting_label)
    await answer_menu(
        message,
        f"📍 <b>{url[:80]}</b>\n\n"
        "Название для списка (или «-» чтобы пропустить):",
    )


@router.message(ReconSetupStates.waiting_label, F.text)
async def msg_recon_label(message: Message, session: AsyncSession, state: FSMContext) -> None:
    if not message.text or message.text.startswith("/") or message.text in MENU_BUTTONS:
        return

    data = await state.get_data()
    source_type = data.get("recon_source_type")
    url = data.get("recon_url")
    if not source_type or not url:
        await state.clear()
        await answer_menu(message, "Сессия истекла. Начните снова: 🔍 Разведка и Вериф")
        return

    label = None if message.text.strip() == "-" else message.text.strip()
    user = await user_service.get_or_create(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )
    source = await recon_service.add_source(
        session,
        user,
        source_type=source_type,
        url_or_handle=url,
        label=label,
    )
    await state.clear()

    monitor = get_recon_monitor()
    if monitor:
        await monitor.check_source(source)

    type_label = SOURCE_TYPE_LABELS.get(source_type, source_type)
    await answer_menu(
        message,
        f"✅ Источник добавлен (#{source.id})\n"
        f"{type_label}: {label or url}\n\n"
        "Первый опрос выполнен. Дальше — автоматически каждый час.",
        reply_markup=recon_menu_keyboard(),
    )


@router.callback_query(F.data == "recon:list")
async def cb_recon_list(callback: CallbackQuery, session: AsyncSession) -> None:
    if not callback.from_user or not callback.message:
        await callback.answer()
        return
    await callback.answer()
    await _show_sources(callback.message, session)


@router.callback_query(F.data.startswith("recon:src:"))
async def cb_recon_src(callback: CallbackQuery, session: AsyncSession) -> None:
    if not callback.data or not callback.from_user or not callback.message:
        await callback.answer()
        return
    source_id = int(callback.data.split(":")[-1])
    user = await user_service.get_or_create(
        session,
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name,
    )
    source = await recon_service.get_source(session, user, source_id)
    if not source:
        await callback.answer("Не найден", show_alert=True)
        return
    await callback.answer()
    type_label = SOURCE_TYPE_LABELS.get(source.source_type, source.source_type)
    preview = (source.last_preview or "ещё не проверялся")[:300]
    text = (
        f"#{source.id} <b>{source.label or source.url_or_handle}</b>\n"
        f"{type_label}\n"
        f"Интервал: {source.check_interval_min} мин\n"
        f"Верификация: {'вкл' if source.verify_enabled else 'выкл'}\n\n"
        f"<i>{preview}</i>"
    )
    try:
        await callback.message.edit_text(
            text,
            reply_markup=recon_source_actions_keyboard(source.id, enabled=source.enabled),
            parse_mode="HTML",
        )
    except TelegramBadRequest:
        await callback.message.answer(
            text,
            reply_markup=recon_source_actions_keyboard(source.id, enabled=source.enabled),
            parse_mode="HTML",
        )


@router.callback_query(F.data.startswith("recon:check:"))
async def cb_recon_check_one(callback: CallbackQuery, session: AsyncSession) -> None:
    if not callback.data or not callback.from_user or not callback.message:
        await callback.answer()
        return
    source_id = int(callback.data.split(":")[-1])
    user = await user_service.get_or_create(
        session,
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name,
    )
    source = await recon_service.get_source(session, user, source_id)
    if not source:
        await callback.answer("Не найден", show_alert=True)
        return
    await callback.answer("Проверяю…")
    fetched = await fetch_source_content(source.source_type, source.url_or_handle)
    if not fetched:
        await callback.message.answer("Не удалось получить данные из источника.")
        return

    if source.verify_enabled:
        verification = await recon_verifier.verify_change(
            source_label=source.label or source.url_or_handle,
            old_preview=source.last_preview,
            new_content=fetched.content,
            source_type=source.source_type,
        )
        verdict = VERDICT_LABELS.get(verification.verdict, verification.verdict)
        text = (
            f"🔍 <b>{fetched.title}</b>\n\n"
            f"{verdict} ({int(verification.confidence * 100)}%)\n"
            f"{verification.summary}\n\n"
            f"<i>{fetched.content[:500]}…</i>"
        )
    else:
        text = f"🔍 <b>{fetched.title}</b>\n\n<i>{fetched.content[:600]}…</i>"

    source.last_preview = fetched.content[:500]
    source.last_content_hash = fetched.content_hash
    await callback.message.answer(text, parse_mode="HTML")


@router.callback_query(F.data == "recon:check_all")
async def cb_recon_check_all(callback: CallbackQuery, session: AsyncSession) -> None:
    if not callback.from_user or not callback.message:
        await callback.answer()
        return
    user = await user_service.get_or_create(
        session,
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name,
    )
    sources = [s for s in await recon_service.list_sources(session, user) if s.enabled]
    if not sources:
        await callback.answer("Нет активных источников", show_alert=True)
        return
    await callback.answer("Проверяю…")
    monitor = get_recon_monitor()
    if not monitor:
        await callback.message.answer("Монитор не инициализирован.")
        return
    checked = 0
    for source in sources:
        event = await monitor.check_source(source, force=True)
        if event:
            checked += 1
            await callback.message.answer(
                format_event_message(source, event),
                parse_mode="HTML",
            )
    if not checked:
        await callback.message.answer("Изменений не обнаружено.")


@router.callback_query(F.data.startswith("recon:toggle:"))
async def cb_recon_toggle(callback: CallbackQuery, session: AsyncSession) -> None:
    if not callback.data or not callback.from_user:
        await callback.answer()
        return
    source_id = int(callback.data.split(":")[-1])
    user = await user_service.get_or_create(
        session,
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name,
    )
    source = await recon_service.get_source(session, user, source_id)
    if not source:
        await callback.answer("Не найден", show_alert=True)
        return
    source.enabled = not source.enabled
    status = "Включён" if source.enabled else "Выключен"
    await callback.answer(status)
    if callback.message:
        type_label = SOURCE_TYPE_LABELS.get(source.source_type, source.source_type)
        preview = (source.last_preview or "ещё не проверялся")[:300]
        text = (
            f"#{source.id} <b>{source.label or source.url_or_handle}</b>\n"
            f"{type_label}\n"
            f"Интервал: {source.check_interval_min} мин\n"
            f"Верификация: {'вкл' if source.verify_enabled else 'выкл'}\n\n"
            f"<i>{preview}</i>"
        )
        try:
            await callback.message.edit_text(
                text,
                reply_markup=recon_source_actions_keyboard(source.id, enabled=source.enabled),
                parse_mode="HTML",
            )
        except TelegramBadRequest:
            pass


@router.callback_query(F.data.startswith("recon:delete:"))
async def cb_recon_delete(callback: CallbackQuery, session: AsyncSession) -> None:
    if not callback.data or not callback.from_user:
        await callback.answer()
        return
    source_id = int(callback.data.split(":")[-1])
    user = await user_service.get_or_create(
        session,
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name,
    )
    ok = await recon_service.delete_source(session, user, source_id)
    await callback.answer("Удалён" if ok else "Не найден")
    if callback.message and ok:
        await _show_sources(callback.message, session)


@router.callback_query(F.data == "recon:cancel")
async def cb_recon_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.answer("Отменено")
    if callback.message:
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except TelegramBadRequest:
            pass
