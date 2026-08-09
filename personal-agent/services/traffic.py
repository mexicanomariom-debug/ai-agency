"""Traffic / jam monitoring with multi-provider support."""

from __future__ import annotations

import logging
from datetime import datetime, time
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

from config import settings
from services.traffic_providers import (
    PROVIDER_LABELS,
    TrafficResult,
    consume_google_last_error,
    consume_provider_last_error,
    diagnose_google_maps,
    fetch_area_traffic_for_user,
    fetch_traffic_for_user,
    is_russia_context,
    resolve_provider,
)

if TYPE_CHECKING:
    from aiogram import Bot
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from database.models import User

logger = logging.getLogger(__name__)


def _parse_time(s: str | None, default: time) -> time:
    if not s:
        return default
    try:
        h, m = s.split(":")
        return time(int(h), int(m))
    except (ValueError, AttributeError):
        return default


def is_check_window(user: "User", now: datetime | None = None) -> bool:
    tz = ZoneInfo(user.timezone or "UTC")
    now = now or datetime.now(tz)
    start = _parse_time(getattr(user, "traffic_check_start", None), time(7, 0))
    end = _parse_time(getattr(user, "traffic_check_end", None), time(10, 0))
    t = now.time()
    if start <= end:
        return start <= t <= end
    return t >= start or t <= end


def provider_label(provider: str | None) -> str:
    return PROVIDER_LABELS.get(provider or "google", provider or "Google Maps")


async def fetch_traffic(
    user: "User",
    origin: str,
    destination: str,
    *,
    provider_override: str | None = None,
) -> TrafficResult | None:
    return await fetch_traffic_for_user(user, origin, destination, provider_override=provider_override)


async def fetch_area_traffic(
    user: "User",
    location: str,
    *,
    provider_override: str | None = None,
) -> TrafficResult | None:
    return await fetch_area_traffic_for_user(user, location, provider_override=provider_override)


def format_traffic_message(result: TrafficResult, *, alert: bool = False) -> str:
    emoji = "🚗🔴" if alert else "🚗"
    provider = provider_label(result.provider)

    if result.monitor_mode == "area":
        lines = [
            f"{emoji} <b>Монитор траффика</b>",
            f"🏙 {result.origin}",
            f"🗺 {provider}",
        ]
        if result.area_detail:
            lines.append(f"📊 {result.area_detail}")
        lines.append(f"⏱ Без пробок: ~{result.duration_min} мин (среднее)")
        lines.append(f"🚦 С пробками: ~{result.duration_in_traffic_min} мин (среднее)")
        if result.delay_min > 0:
            lines.append(f"⚠️ Средняя задержка: +{result.delay_min} мин")
        else:
            lines.append("✅ В районе дороги свободны")
        return "\n".join(lines)

    lines = [
        f"{emoji} <b>Монитор траффика</b>",
        f"🛣 Маршрут",
        f"🗺 {provider}",
        f"📍 {result.origin} → {result.destination}",
        f"⏱ Без пробок: ~{result.duration_min} мин",
        f"🚦 С пробками: ~{result.duration_in_traffic_min} мин",
    ]
    if result.delay_min > 0:
        lines.append(f"⚠️ Задержка: +{result.delay_min} мин")
    else:
        lines.append("✅ Дорога свободна")
    if result.summary and result.summary not in PROVIDER_LABELS.values():
        lines.append(f"🛣 {result.summary}")
    return "\n".join(lines)


async def check_user_traffic(
    user: "User",
    *,
    manual: bool = False,
    provider_override: str | None = None,
) -> TrafficResult | None:
    if not manual and not getattr(user, "traffic_enabled", False):
        return None

    origin = getattr(user, "traffic_origin", None)
    if not origin:
        return None

    mode = getattr(user, "traffic_mode", None) or "route"
    if mode == "area":
        return await fetch_area_traffic(user, origin, provider_override=provider_override)

    destination = getattr(user, "traffic_destination", None)
    if not destination:
        return None
    return await fetch_traffic(user, origin, destination, provider_override=provider_override)


def traffic_check_error_hint(
    user: "User",
    *,
    google_detail: str | None = None,
    provider_override: str | None = None,
) -> str:
    origin = getattr(user, "traffic_origin", None)
    if not origin:
        return "Сначала настройте монитор: 🛣 Маршрут или 🏙 Район/улица."

    mode = getattr(user, "traffic_mode", None) or "route"
    dest = getattr(user, "traffic_destination", None) if mode == "route" else origin
    if mode == "route" and not dest:
        return "Сначала настройте маршрут: кнопка 🛣 Маршрут."

    russia = is_russia_context(user, origin, dest or origin)
    forced = provider_override or "auto"
    provider_err = consume_provider_last_error(forced if forced != "auto" else resolve_provider(user, origin, dest or origin))

    if forced in ("yandex", "dgis") and not russia:
        return (
            f"{provider_label(forced)} работает для России/СНГ.\n"
            f"Для «{origin}» используйте 🔄 Авто или 🗺 Google."
        )

    if russia:
        if not settings.yandex_maps_api_key and not settings.dgis_api_key and not settings.google_maps_api_key:
            return (
                "Нет ключей карт для России. Добавьте YANDEX_MAPS_API_KEY, DGIS_API_KEY "
                "или GOOGLE_MAPS_API_KEY в секреты деплоя."
            )
        lines = [f"Не удалось получить данные ({provider_label(forced)})."]
        if provider_err:
            lines.append(f"\n<b>Детали:</b> {provider_err}")
        lines.append(
            "\n\nПроверьте ключи: Яндекс — HTTP Геокодер + API Маршрутизации; "
            "2ГИС — Geocoder + Routing API."
        )
        return "".join(lines)

    if not settings.google_maps_api_key:
        return "Не настроен GOOGLE_MAPS_API_KEY. Создайте отдельный ключ для карт в Google Cloud."

    detail = google_detail or provider_err or consume_google_last_error()
    lines = ["Не удалось получить данные от Google Maps."]
    if detail:
        lines.append(f"\n<b>Детали:</b> {detail}")
    lines.append(
        "\n\n<b>Что проверить в Google Cloud Console:</b>\n"
        "1. APIs & Services → Library → включить <b>Geocoding API</b> и <b>Directions API</b>\n"
        "2. APIs & Services → Credentials → ключ GOOGLE_MAPS_API_KEY\n"
        "   • Application restrictions: <b>None</b> или IP сервера <code>140.84.183.154</code>\n"
        "   • API restrictions: только Geocoding + Directions\n"
        "3. Billing → привязана карта к проекту\n"
        "4. GitHub Secret <code>GOOGLE_MAPS_API_KEY</code> — именно ключ карт, не OAuth Client ID"
    )
    return "".join(lines)


async def traffic_check_error_hint_async(
    user: "User",
    *,
    provider_override: str | None = None,
) -> str:
    detail = consume_google_last_error()
    origin = getattr(user, "traffic_origin", None) or ""
    mode = getattr(user, "traffic_mode", None) or "route"
    dest = getattr(user, "traffic_destination", None) if mode == "route" else origin
    if (
        not detail
        and not is_russia_context(user, origin, dest or origin)
        and settings.google_maps_api_key
        and (provider_override in (None, "auto", "google"))
    ):
        detail = await diagnose_google_maps()
    return traffic_check_error_hint(user, google_detail=detail, provider_override=provider_override)


async def maybe_notify_traffic(
    bot: "Bot",
    session: "AsyncSession",
    user: "User",
    result: TrafficResult,
) -> bool:
    threshold = getattr(user, "traffic_threshold_min", 15) or 15
    if result.delay_min < threshold:
        return False

    tz = ZoneInfo(user.timezone or "UTC")
    now = datetime.now(tz)
    alert_key = f"{now.strftime('%Y-%m-%d-%H')}:{result.delay_min // 5}"
    last = getattr(user, "traffic_last_alert", None)
    if last == alert_key:
        return False

    text = format_traffic_message(result, alert=True)
    text += f"\n\n💡 Порог уведомлений: +{threshold} мин"
    try:
        await bot.send_message(user.telegram_id, text, parse_mode="HTML")
        user.traffic_last_alert = alert_key
        await session.flush()
        return True
    except Exception as e:
        logger.warning("Failed to send traffic alert to %s: %s", user.telegram_id, e)
        return False


class TrafficMonitor:
    def __init__(self, bot: "Bot", session_factory: "async_sessionmaker[AsyncSession]"):
        self.bot = bot
        self.session_factory = session_factory

    async def run_checks(self) -> None:
        from sqlalchemy import select

        from database.models import User

        async with self.session_factory() as session:
            from sqlalchemy import or_

            result = await session.execute(
                select(User).where(
                    User.traffic_enabled == True,  # noqa: E712
                    User.traffic_origin.isnot(None),
                    or_(
                        User.traffic_destination.isnot(None),
                        User.traffic_mode == "area",
                    ),
                )
            )
            users = result.scalars().all()

        for user in users:
            try:
                if not is_check_window(user):
                    continue
                traffic = await check_user_traffic(user)
                if traffic:
                    async with self.session_factory() as session:
                        db_user = await session.get(User, user.id)
                        if db_user:
                            await maybe_notify_traffic(self.bot, session, db_user, traffic)
                            await session.commit()
            except Exception as e:
                logger.exception("Traffic check failed for user %s: %s", user.id, e)


_traffic_monitor: TrafficMonitor | None = None


def init_traffic_monitor(bot: "Bot", session_factory: "async_sessionmaker[AsyncSession]") -> TrafficMonitor:
    global _traffic_monitor
    _traffic_monitor = TrafficMonitor(bot, session_factory)
    return _traffic_monitor


def get_traffic_monitor() -> TrafficMonitor | None:
    return _traffic_monitor
