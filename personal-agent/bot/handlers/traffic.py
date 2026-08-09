"""Traffic monitoring: menu button, setup wizard, multi-provider routing."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.inline import traffic_menu_keyboard, traffic_provider_keyboard
from bot.states.traffic import TrafficSetupStates
from bot.utils.messages import answer_menu
from database.models import User
from services.traffic import (
    fetch_traffic,
    format_traffic_message,
    is_check_window,
    provider_label,
)
from services.traffic_providers import is_russia_context, resolve_provider
from services.user_service import user_service

router = Router(name="traffic")

TRAFFIC_BUTTON = "🚗 Пробки"


def _traffic_status(user: User) -> str:
    enabled = "✅ включён" if getattr(user, "traffic_enabled", False) else "❌ выключен"
    origin = getattr(user, "traffic_origin", None) or "—"
    dest = getattr(user, "traffic_destination", None) or "—"
    threshold = getattr(user, "traffic_threshold_min", 15) or 15
    start = getattr(user, "traffic_check_start", None) or "07:00"
    end = getattr(user, "traffic_check_end", None) or "10:00"
    window = "сейчас в окне" if is_check_window(user) else "вне окна проверки"
    provider = provider_label(getattr(user, "traffic_provider", None) or "auto")
    if getattr(user, "traffic_provider", None) in (None, "auto"):
        if origin != "—" and dest != "—":
            provider = provider_label(resolve_provider(user, origin, dest)) + " (авто)"

    region = "🇷🇺 Россия → Яндекс/2ГИС" if is_russia_context(user) else "🌍 Мир → Google"

    return (
        f"🚗 <b>Мониторинг пробок</b>\n\n"
        f"Статус: {enabled}\n"
        f"Регион: {region}\n"
        f"Карты: {provider}\n"
        f"📍 Откуда: {origin}\n"
        f"🏁 Куда: {dest}\n"
        f"⏰ Окно: {start}–{end} ({window})\n"
        f"⚠️ Уведомлять при: +{threshold} мин\n\n"
        f"Нажмите <b>📍 Настроить маршрут</b> или напишите адреса по шагам.\n"
        f"Команды: /traffic check · /traffic hours 7:00 10:00"
    )


async def show_traffic_panel(message: Message, session: AsyncSession) -> None:
    user = await user_service.get_or_create(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )
    await answer_menu(
        message,
        _traffic_status(user),
        reply_markup=traffic_menu_keyboard(enabled=bool(user.traffic_enabled)),
    )


async def _save_route(
    message: Message,
    session: AsyncSession,
    state: FSMContext,
    user: User,
    origin: str,
    destination: str,
    provider: str | None = None,
) -> None:
    user.traffic_origin = origin
    user.traffic_destination = destination
    if provider:
        user.traffic_provider = provider
    elif is_russia_context(user, origin, destination):
        user.traffic_provider = "auto"
    else:
        user.traffic_provider = "google"
    user.traffic_enabled = True
    await state.clear()

    chosen = provider_label(resolve_provider(user, origin, destination))
    await answer_menu(
        message,
        f"✅ Маршрут сохранён ({chosen}):\n"
        f"📍 {origin}\n"
        f"🏁 {destination}\n\n"
        "Мониторинг включён. Проверка: кнопка 🔄 или /traffic check",
        reply_markup=traffic_menu_keyboard(enabled=True),
    )


@router.message(Command("traffic"))
@router.message(lambda m: m.text == TRAFFIC_BUTTON)
async def cmd_traffic(message: Message, session: AsyncSession, state: FSMContext) -> None:
    if not message.text or not message.from_user:
        return

    user = await user_service.get_or_create(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )

    parts = message.text.split(maxsplit=2)
    sub = parts[1].lower() if len(parts) > 1 and message.text.startswith("/") else ""

    if sub == "on":
        user.traffic_enabled = True
        await answer_menu(message, "🚗 Мониторинг пробок включён.", reply_markup=traffic_menu_keyboard(enabled=True))
        return

    if sub == "off":
        user.traffic_enabled = False
        await answer_menu(message, "Мониторинг пробок выключен.", reply_markup=traffic_menu_keyboard(enabled=False))
        return

    if sub == "setup":
        await state.set_state(TrafficSetupStates.waiting_origin)
        await answer_menu(
            message,
            "📍 <b>Откуда едете?</b>\n\n"
            "Напишите адрес или место:\n"
            "• Москва, Тверская 1\n"
            "• Playa del Carmen, Calle 10",
        )
        return

    if sub == "set" and len(parts) > 2:
        route = parts[2]
        if "|" in route:
            origin, dest = [s.strip() for s in route.split("|", 1)]
        elif "->" in route:
            origin, dest = [s.strip() for s in route.split("->", 1)]
        else:
            await answer_menu(message, "Формат: /traffic set Москва, дом | Офис, ул. Ленина 5")
            return
        if not origin or not dest:
            await answer_menu(message, "Укажите оба адреса через | или ->")
            return
        await _save_route(message, session, state, user, origin, dest)
        return

    if sub == "check":
        origin = getattr(user, "traffic_origin", None)
        dest = getattr(user, "traffic_destination", None)
        if not origin or not dest:
            await answer_menu(message, "Сначала настройте маршрут: кнопка 📍 Настроить маршрут")
            return
        await answer_menu(message, "⏳ Проверяю пробки…")
        result = await fetch_traffic(user, origin, dest)
        if not result:
            await answer_menu(
                message,
                "Не удалось получить данные. Для России нужен YANDEX_MAPS_API_KEY или DGIS_API_KEY, "
                "для остальных — GOOGLE_MAPS_API_KEY.",
            )
            return
        await answer_menu(message, format_traffic_message(result), reply_markup=traffic_menu_keyboard(enabled=True))
        return

    if sub == "threshold" and len(parts) > 2:
        try:
            minutes = int(parts[2])
            if minutes < 1 or minutes > 120:
                raise ValueError()
            user.traffic_threshold_min = minutes
            await answer_menu(message, f"Порог уведомлений: +{minutes} мин задержки")
        except ValueError:
            await answer_menu(message, "Укажите число от 1 до 120, например: /traffic threshold 15")
        return

    if sub == "hours" and len(parts) > 2:
        times = parts[2].split()
        if len(times) != 2:
            await answer_menu(message, "Формат: /traffic hours 7:00 10:00")
            return
        user.traffic_check_start = times[0]
        user.traffic_check_end = times[1]
        await answer_menu(message, f"Окно проверки: {times[0]}–{times[1]} (ваш часовой пояс)")
        return

    if sub in ("yandex", "dgis", "google", "auto"):
        user.traffic_provider = sub
        await answer_menu(message, f"Карты: {provider_label(sub)}")
        return

    await show_traffic_panel(message, session)


@router.message(TrafficSetupStates.waiting_origin, F.text)
async def msg_traffic_origin(message: Message, state: FSMContext) -> None:
    if not message.text or message.text.startswith("/"):
        return
    if message.text == TRAFFIC_BUTTON:
        return
    await state.update_data(traffic_origin=message.text.strip())
    await state.set_state(TrafficSetupStates.waiting_destination)
    await answer_menu(
        message,
        f"📍 Откуда: <b>{message.text.strip()}</b>\n\n"
        "🏁 <b>Куда едете?</b>\n"
        "Напишите адрес назначения.",
    )


@router.message(TrafficSetupStates.waiting_destination, F.text)
async def msg_traffic_destination(message: Message, session: AsyncSession, state: FSMContext) -> None:
    if not message.text or message.text.startswith("/"):
        return
    if message.text == TRAFFIC_BUTTON:
        return

    data = await state.get_data()
    origin = data.get("traffic_origin")
    if not origin:
        await state.clear()
        await answer_menu(message, "Начните заново: 🚗 Пробки → 📍 Настроить маршрут")
        return

    destination = message.text.strip()
    user = await user_service.get_or_create(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )

    if is_russia_context(user, origin, destination):
        await state.update_data(traffic_destination=destination)
        await state.set_state(TrafficSetupStates.waiting_provider)
        await answer_menu(
            message,
            "🇷🇺 <b>Маршрут в России</b>\n\n"
            f"📍 {origin}\n"
            f"🏁 {destination}\n\n"
            "Выберите карты для мониторинга:",
            reply_markup=traffic_provider_keyboard(),
        )
        return

    await _save_route(message, session, state, user, origin, destination, provider="google")


@router.callback_query(F.data == "traffic:setup")
async def cb_traffic_setup(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(TrafficSetupStates.waiting_origin)
    if callback.message:
        await callback.message.answer(
            "📍 <b>Откуда едете?</b>\n\n"
            "Напишите адрес или место.\n"
            "Для России — Яндекс или 2ГИС, для остальных — Google."
        )


@router.callback_query(F.data == "traffic:check")
async def cb_traffic_check(callback: CallbackQuery, session: AsyncSession) -> None:
    if not callback.from_user or not callback.message:
        await callback.answer()
        return
    user = await user_service.get_or_create(
        session,
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name,
    )
    origin = getattr(user, "traffic_origin", None)
    dest = getattr(user, "traffic_destination", None)
    if not origin or not dest:
        await callback.answer("Сначала настройте маршрут", show_alert=True)
        return
    await callback.answer("Проверяю…")
    result = await fetch_traffic(user, origin, dest)
    if not result:
        await callback.message.answer("Не удалось получить данные о пробках.")
        return
    await callback.message.answer(
        format_traffic_message(result),
        reply_markup=traffic_menu_keyboard(enabled=bool(user.traffic_enabled)),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "traffic:toggle")
async def cb_traffic_toggle(callback: CallbackQuery, session: AsyncSession) -> None:
    if not callback.from_user or not callback.message:
        await callback.answer()
        return
    user = await user_service.get_or_create(
        session,
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name,
    )
    user.traffic_enabled = not user.traffic_enabled
    status = "включён" if user.traffic_enabled else "выключен"
    await callback.answer(f"Мониторинг {status}")
    try:
        await callback.message.edit_text(
            _traffic_status(user),
            reply_markup=traffic_menu_keyboard(enabled=user.traffic_enabled),
            parse_mode="HTML",
        )
    except TelegramBadRequest:
        await callback.message.answer(
            _traffic_status(user),
            reply_markup=traffic_menu_keyboard(enabled=user.traffic_enabled),
            parse_mode="HTML",
        )


@router.callback_query(F.data.startswith("traffic:provider:"))
async def cb_traffic_provider_quick(callback: CallbackQuery, session: AsyncSession) -> None:
    if not callback.data or not callback.from_user:
        await callback.answer()
        return
    provider = callback.data.split(":")[-1]
    user = await user_service.get_or_create(
        session,
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name,
    )
    user.traffic_provider = provider
    await callback.answer(f"Карты: {provider_label(provider)}")
    if callback.message:
        try:
            await callback.message.edit_text(
                _traffic_status(user),
                reply_markup=traffic_menu_keyboard(enabled=bool(user.traffic_enabled)),
                parse_mode="HTML",
            )
        except TelegramBadRequest:
            pass


@router.callback_query(F.data.startswith("traffic:pick:"))
async def cb_traffic_pick_provider(callback: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    if not callback.data or not callback.from_user or not callback.message:
        await callback.answer()
        return
    provider = callback.data.split(":")[-1]
    data = await state.get_data()
    origin = data.get("traffic_origin")
    destination = data.get("traffic_destination")
    if not origin or not destination:
        await callback.answer("Сессия истекла", show_alert=True)
        await state.clear()
        return

    user = await user_service.get_or_create(
        session,
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name,
    )
    await callback.answer()
    await _save_route(callback.message, session, state, user, origin, destination, provider=provider)


@router.callback_query(F.data == "traffic:cancel")
async def cb_traffic_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.answer("Отменено")
    if callback.message:
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except TelegramBadRequest:
            pass
