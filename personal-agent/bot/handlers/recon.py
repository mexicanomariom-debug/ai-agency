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
    recon_interest_prompt_keyboard,
    recon_menu_keyboard,
    recon_source_actions_keyboard,
    recon_sources_keyboard,
    recon_type_keyboard,
)
from bot.middlewares.translator import MENU_BUTTONS
from bot.states.recon import ReconSetupStates
from bot.utils.html import h as html_escape
from bot.utils.messages import answer_menu
from services.recon import format_event_message, get_recon_monitor
from services.recon_providers import _parse_source_input, fetch_source_content
from services.recon_service import (
    SOURCE_TYPE_LABELS,
    VERDICT_LABELS,
    dump_seen_item_ids,
    recon_service,
)
from services.recon_verifier import recon_verifier
from services.user_service import user_service

logger = logging.getLogger(__name__)

router = Router(name="recon")

RECON_BUTTON = "🔍 Разведка и Вериф"
_SKIP_INTEREST = {"-", "skip", "всё", "все", "всё подряд", "без фильтра", "нет"}


async def apply_recon_interest(
    message: Message,
    session: AsyncSession,
    state: FSMContext,
    text: str,
) -> bool:
    """Save interest filter for a recon source. Returns False if state is invalid."""
    if not message.from_user:
        return False

    data = await state.get_data()
    source_id = data.get("recon_source_id")
    if not source_id:
        await state.clear()
        return False

    user = await user_service.get_or_create(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )
    cleaned = text.strip()
    if cleaned.lower() in _SKIP_INTEREST:
        await recon_service.update_filter(session, user, int(source_id), filter_query=None)
        reply = "Без фильтра — буду присылать все изменения в источнике."
    else:
        await recon_service.update_filter(session, user, int(source_id), filter_query=cleaned)
        reply = (
            f"🎯 Сохранено: <b>{html_escape(cleaned)}</b>\n"
            "Буду присылать только подходящие сообщения."
        )

    await state.clear()
    await answer_menu(message, reply, reply_markup=recon_menu_keyboard(), parse_mode="HTML")
    return True


def _panel_text(sources_count: int, enabled_count: int) -> str:
    return (
        "🔍 <b>Разведка и Вериф</b>\n\n"
        "Мониторинг сайтов, Telegram, эко-календаря и соцсетей.\n"
        "Укажите <b>интерес</b> — бот пришлёт только подходящие сообщения, а не весь канал подряд.\n\n"
        f"Источников: {sources_count} (активных: {enabled_count})\n\n"
        "<b>Добавить:</b> ➕ Источник → <code>@канал</code>\n"
        "С интересом сразу: <code>/recon add @канал интерес: решения FOMC, CPI</code>\n"
        "<b>Фильтр:</b> <code>/recon filter 3 ваш интерес</code>\n"
        "<b>Верификация:</b> /recon verify ваш текст"
    )


def _source_detail_text(source) -> str:
    type_label = SOURCE_TYPE_LABELS.get(source.source_type, source.source_type)
    preview = html_escape((source.last_preview or "ещё не проверялся")[:300])
    name = html_escape(source.label or source.url_or_handle)
    if source.filter_query:
        filter_line = f"🎯 <b>Интерес:</b> {html_escape(source.filter_query)}"
    else:
        filter_line = "🎯 <b>Интерес:</b> не задан — приходят все изменения"
    if source.keywords:
        filter_line += f"\n🔑 Ключевые слова: {html_escape(source.keywords)}"
    return (
        f"#{source.id} <b>{name}</b>\n"
        f"{type_label}\n"
        f"Интервал: {source.check_interval_min} мин\n"
        f"Верификация: {'вкл' if source.verify_enabled else 'выкл'}\n"
        f"{filter_line}\n\n"
        f"<i>{preview}</i>"
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

    if sub == "add" and len(parts) > 2:
        await _add_source_from_text(message, session, state, " ".join(parts[2:]))
        return

    if sub == "filter" and len(parts) > 2:
        await _set_filter_from_command(message, session, parts[2])
        return

    if sub == "list":
        await _show_sources(
            message,
            session,
            actor_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
        )
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


async def _show_sources(
    message: Message,
    session: AsyncSession,
    *,
    actor_id: int,
    username: str | None = None,
    first_name: str | None = None,
    edit: bool = False,
) -> None:
    user = await user_service.get_or_create(
        session,
        telegram_id=actor_id,
        username=username,
        first_name=first_name,
    )
    sources = await recon_service.list_sources(session, user)
    if not sources:
        text = "Список пуст. Нажмите ➕ Источник."
        markup = recon_menu_keyboard()
    else:
        lines = ["📋 <b>Источники</b>\n"]
        for src in sources[:15]:
            type_label = SOURCE_TYPE_LABELS.get(src.source_type, src.source_type)
            name = html_escape(src.label or src.url_or_handle)[:50]
            status = "✅" if src.enabled else "⏸"
            interest = " 🎯" if src.filter_query else ""
            lines.append(f"{status} #{src.id} {type_label}: {name}{interest}")
        text = "\n".join(lines)
        markup = recon_sources_keyboard(sources)

    if edit:
        try:
            await message.edit_text(text, reply_markup=markup, parse_mode="HTML")
            return
        except TelegramBadRequest:
            logger.debug("Could not edit recon list message, sending new one")

    await answer_menu(message, text, reply_markup=markup, parse_mode="HTML")


async def _seed_source_baseline(source, fetched) -> None:
    source.last_preview = fetched.content[:500]
    source.last_content_hash = fetched.content_hash
    if fetched.items:
        ids = {item.item_id for item in fetched.items}
        source.last_seen_item_ids = dump_seen_item_ids(ids)


async def _add_source_from_text(
    message: Message,
    session: AsyncSession,
    state: FSMContext,
    text: str,
    *,
    source_type: str | None = None,
) -> None:
    parsed_type, url, label, filter_query = _parse_source_input(text, source_type)
    if not url:
        await answer_menu(message, "Укажите адрес, @канал или ссылку.")
        return

    user = await user_service.get_or_create(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )
    await answer_menu(message, "⏳ Добавляю источник и проверяю…")

    source = await recon_service.add_source(
        session,
        user,
        source_type=parsed_type,
        url_or_handle=url,
        label=label,
        filter_query=filter_query,
    )

    fetched = await fetch_source_content(parsed_type, url)
    probe = ""
    if fetched:
        await _seed_source_baseline(source, fetched)
        preview = fetched.content[:200].replace("<", "").replace(">", "")
        probe = f"\n\n✅ Пробное чтение OK ({len(fetched.items or [])} элементов):\n<i>{preview}…</i>"
    else:
        hints = {
            "telegram": (
                "\n\n⚠️ Канал пока не читается. Нужен <b>публичный</b> канал "
                "(t.me/s/имя). Приватные каналы пока не поддерживаются."
            ),
            "website": "\n\n⚠️ Сайт не ответил. Проверьте URL или RSS-ссылку.",
        }
        probe = hints.get(parsed_type, "\n\n⚠️ Источник добавлен, но данные пока не получены.")

    type_label = SOURCE_TYPE_LABELS.get(parsed_type, parsed_type)
    if filter_query:
        await state.clear()
        await answer_menu(
            message,
            f"✅ Источник #{source.id} добавлен\n"
            f"{type_label}: <b>{label or url}</b>\n"
            f"🎯 Интерес: <b>{filter_query}</b>{probe}",
            reply_markup=recon_menu_keyboard(),
            parse_mode="HTML",
        )
        return

    await state.set_state(ReconSetupStates.waiting_interest)
    await state.update_data(recon_source_id=source.id)
    await answer_menu(
        message,
        f"✅ Источник #{source.id} добавлен\n"
        f"{type_label}: <b>{label or url}</b>{probe}\n\n"
        "🎯 <b>Что вас интересует в этом источнике?</b>\n"
        "Напишите темы текстом или нажмите кнопку ниже.\n"
        "Например: <code>решения FOMC, инфляция CPI, ставка ЦБ</code>",
        reply_markup=recon_interest_prompt_keyboard(source.id),
        parse_mode="HTML",
    )


async def _set_filter_from_command(message: Message, session: AsyncSession, args: str) -> None:
    parts = args.strip().split(maxsplit=1)
    if len(parts) < 2:
        await answer_menu(message, "Формат: <code>/recon filter 3 ваш интерес</code>", parse_mode="HTML")
        return
    try:
        source_id = int(parts[0].lstrip("#"))
    except ValueError:
        await answer_menu(message, "Укажите номер источника: <code>/recon filter 3 …</code>", parse_mode="HTML")
        return

    user = await user_service.get_or_create(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )
    query = parts[1].strip()
    if query.lower() in _SKIP_INTEREST:
        source = await recon_service.update_filter(session, user, source_id, filter_query=None)
        text = "Фильтр снят — снова все изменения."
    else:
        source = await recon_service.update_filter(session, user, source_id, filter_query=query)
        text = f"🎯 Интерес сохранён: <b>{query}</b>"
    if not source:
        await answer_menu(message, "Источник не найден.")
        return
    await answer_menu(message, f"#{source_id}: {text}", parse_mode="HTML")


@router.callback_query(F.data == "recon:add")
async def cb_recon_add(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(ReconSetupStates.waiting_url)
    await state.update_data(recon_source_type=None)
    if callback.message:
        await callback.message.answer(
            "➕ <b>Новый источник</b>\n\n"
            "Выберите тип кнопкой ниже <b>или сразу напишите</b>:\n"
            "• <code>@канал</code>\n"
            "• <code>https://t.me/канал</code>\n"
            "• <code>https://site.com/feed.xml</code>\n\n"
            "С интересом: <code>@канал интерес: ваши темы</code>",
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
        "website": "Отправьте URL сайта или RSS:\n• https://example.com/feed.xml",
        "telegram": "Отправьте публичный канал:\n• @channelname\n• @channel интерес: ваши темы",
        "instagram": "Ссылка Instagram:\n• https://instagram.com/username",
        "tiktok": "Ссылка TikTok:\n• https://tiktok.com/@username",
        "econ_calendar": "Напишите <code>auto</code> или любой текст — подключу календарь на неделю",
    }
    label = SOURCE_TYPE_LABELS.get(source_type, source_type)
    if callback.message:
        await callback.message.answer(
            f"📢 <b>{label}</b>\n\n{hints.get(source_type, 'Укажите адрес:')}",
            parse_mode="HTML",
        )


@router.message(ReconSetupStates.waiting_url, F.text)
async def msg_recon_url(message: Message, session: AsyncSession, state: FSMContext) -> None:
    if not message.text or message.text.startswith("/") or message.text in MENU_BUTTONS:
        if message.text in MENU_BUTTONS and message.text != RECON_BUTTON:
            await state.clear()
        return
    data = await state.get_data()
    source_type = data.get("recon_source_type")
    await _add_source_from_text(message, session, state, message.text.strip(), source_type=source_type)


@router.message(ReconSetupStates.waiting_interest, F.text)
async def msg_recon_interest(message: Message, session: AsyncSession, state: FSMContext) -> None:
    if not message.text or not message.from_user:
        return
    if message.text in MENU_BUTTONS and message.text != RECON_BUTTON:
        await state.clear()
        return
    await apply_recon_interest(message, session, state, message.text)


@router.message(ReconSetupStates.waiting_interest, F.voice)
async def msg_recon_interest_voice(message: Message, session: AsyncSession, state: FSMContext) -> None:
    from bot.handlers.voice import transcribe_for_user

    await message.bot.send_chat_action(message.chat.id, "typing")
    text = await transcribe_for_user(message, in_translator=False)
    if text:
        await apply_recon_interest(message, session, state, text)


@router.message(ReconSetupStates.waiting_url, F.voice)
async def msg_recon_url_voice(message: Message, session: AsyncSession, state: FSMContext) -> None:
    from bot.handlers.voice import transcribe_for_user

    await message.bot.send_chat_action(message.chat.id, "typing")
    text = await transcribe_for_user(message, in_translator=False)
    if not text:
        return
    data = await state.get_data()
    source_type = data.get("recon_source_type")
    await _add_source_from_text(message, session, state, text.strip(), source_type=source_type)


@router.callback_query(F.data.startswith("recon:interest_skip:"))
async def cb_recon_interest_skip(callback: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
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
    source = await recon_service.update_filter(session, user, source_id, filter_query=None)
    await state.clear()
    await callback.answer("Без фильтра")
    if callback.message:
        name = source.label or source.url_or_handle if source else f"#{source_id}"
        await callback.message.answer(
            f"#{source_id} <b>{name}</b>\n"
            "Фильтр не задан — буду присылать все изменения.\n"
            "Позже можно задать интерес: кнопка 🎯 Фильтр в карточке источника.",
            reply_markup=recon_menu_keyboard(),
            parse_mode="HTML",
        )


@router.callback_query(F.data.startswith("recon:filter:"))
async def cb_recon_filter(callback: CallbackQuery, state: FSMContext) -> None:
    if not callback.data:
        await callback.answer()
        return
    source_id = int(callback.data.split(":")[-1])
    await state.set_state(ReconSetupStates.waiting_interest)
    await state.update_data(recon_source_id=source_id)
    await callback.answer()
    if callback.message:
        await callback.message.answer(
            f"🎯 <b>Интерес для #{source_id}</b>\n\n"
            "Опишите, что именно вас интересует в этом источнике.\n"
            "Например: <code>IPO, отчётность, сделки M&A</code>\n\n"
            "Или нажмите ⏭ Без фильтра, если нужны все изменения.",
            reply_markup=recon_interest_prompt_keyboard(source_id),
            parse_mode="HTML",
        )


@router.callback_query(F.data == "recon:list")
async def cb_recon_list(callback: CallbackQuery, session: AsyncSession) -> None:
    if not callback.from_user or not callback.message:
        await callback.answer()
        return
    await callback.answer()
    await _show_sources(
        callback.message,
        session,
        actor_id=callback.from_user.id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name,
        edit=True,
    )


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
    text = _source_detail_text(source)
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
    monitor = get_recon_monitor()
    if monitor:
        result = await monitor.check_source(source, force=True)
        if result:
            events = result if isinstance(result, list) else [result]
            for event in events:
                await callback.message.answer(
                    format_event_message(source, event),
                    parse_mode="HTML",
                )
            return

    fetched = await fetch_source_content(source.source_type, source.url_or_handle)
    if not fetched:
        await callback.message.answer("Не удалось получить данные из источника.")
        return
    await callback.message.answer(
        f"🔍 <b>{fetched.title}</b>\n\n<i>{fetched.content[:600]}…</i>",
        parse_mode="HTML",
    )


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
        result = await monitor.check_source(source, force=True)
        if not result:
            continue
        events = result if isinstance(result, list) else [result]
        for event in events:
            checked += 1
            await callback.message.answer(
                format_event_message(source, event),
                parse_mode="HTML",
            )
    if not checked:
        await callback.message.answer("Новых совпадений не найдено.")


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
        text = _source_detail_text(source)
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
    if callback.message and ok and callback.from_user:
        await _show_sources(
            callback.message,
            session,
            actor_id=callback.from_user.id,
            username=callback.from_user.username,
            first_name=callback.from_user.first_name,
            edit=True,
        )


@router.callback_query(F.data == "recon:cancel")
async def cb_recon_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.answer("Отменено")
    if callback.message:
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except TelegramBadRequest:
            pass
