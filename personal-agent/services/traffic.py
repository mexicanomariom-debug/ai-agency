"""Traffic / jam monitoring via Google Directions API."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, time
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

import httpx

from config import settings

if TYPE_CHECKING:
    from aiogram import Bot
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from database.models import User

logger = logging.getLogger(__name__)

DIRECTIONS_URL = "https://maps.googleapis.com/maps/api/directions/json"


@dataclass
class TrafficResult:
    origin: str
    destination: str
    duration_min: int
    duration_in_traffic_min: int
    delay_min: int
    distance_km: float
    summary: str

    @property
    def is_congested(self) -> bool:
        return self.delay_min > 0


def _parse_time(s: str | None, default: time) -> time:
    if not s:
        return default
    try:
        h, m = s.split(":")
        return time(int(h), int(m))
    except (ValueError, AttributeError):
        return default


def is_check_window(user: "User", now: datetime | None = None) -> bool:
    """True if current local time is within user's traffic check window."""
    tz = ZoneInfo(user.timezone or "UTC")
    now = now or datetime.now(tz)
    start = _parse_time(getattr(user, "traffic_check_start", None), time(7, 0))
    end = _parse_time(getattr(user, "traffic_check_end", None), time(10, 0))
    t = now.time()
    if start <= end:
        return start <= t <= end
    return t >= start or t <= end


async def fetch_traffic(origin: str, destination: str) -> TrafficResult | None:
    api_key = settings.google_maps_api_key
    if not api_key:
        logger.warning("GOOGLE_MAPS_API_KEY not set")
        return None

    params = {
        "origin": origin,
        "destination": destination,
        "departure_time": "now",
        "traffic_model": "best_guess",
        "language": "ru",
        "key": api_key,
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(DIRECTIONS_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        logger.exception("Directions API error: %s", e)
        return None

    if data.get("status") != "OK" or not data.get("routes"):
        logger.warning("Directions API status: %s", data.get("status"))
        return None

    leg = data["routes"][0]["legs"][0]
    duration_sec = leg["duration"]["value"]
    traffic_sec = leg.get("duration_in_traffic", leg["duration"])["value"]
    distance_m = leg.get("distance", {}).get("value", 0)

    duration_min = max(1, duration_sec // 60)
    traffic_min = max(1, traffic_sec // 60)
    delay_min = max(0, traffic_min - duration_min)

    return TrafficResult(
        origin=origin,
        destination=destination,
        duration_min=duration_min,
        duration_in_traffic_min=traffic_min,
        delay_min=delay_min,
        distance_km=round(distance_m / 1000, 1),
        summary=data["routes"][0].get("summary", ""),
    )


def format_traffic_message(result: TrafficResult, *, alert: bool = False) -> str:
    emoji = "🚗🔴" if alert else "🚗"
    lines = [
        f"{emoji} <b>Пробки на маршруте</b>",
        f"📍 {result.origin} → {result.destination}",
        f"⏱ Без пробок: ~{result.duration_min} мин",
        f"🚦 С пробками: ~{result.duration_in_traffic_min} мин",
    ]
    if result.delay_min > 0:
        lines.append(f"⚠️ Задержка: +{result.delay_min} мин")
    else:
        lines.append("✅ Дорога свободна")
    if result.summary:
        lines.append(f"🛣 {result.summary}")
    return "\n".join(lines)


async def check_user_traffic(user: "User") -> TrafficResult | None:
    origin = getattr(user, "traffic_origin", None)
    destination = getattr(user, "traffic_destination", None)
    if not origin or not destination:
        return None
    if not getattr(user, "traffic_enabled", False):
        return None
    return await fetch_traffic(origin, destination)


async def maybe_notify_traffic(
    bot: "Bot",
    session: "AsyncSession",
    user: "User",
    result: TrafficResult,
) -> bool:
    """Send alert if delay exceeds threshold. Returns True if notified."""
    threshold = getattr(user, "traffic_threshold_min", 15) or 15
    if result.delay_min < threshold:
        return False

    from datetime import datetime
    from zoneinfo import ZoneInfo

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
    """Periodic traffic checks for users with monitoring enabled."""

    def __init__(self, bot: "Bot", session_factory: "async_sessionmaker[AsyncSession]"):
        self.bot = bot
        self.session_factory = session_factory

    async def run_checks(self) -> None:
        from sqlalchemy import select

        from database.models import User

        async with self.session_factory() as session:
            result = await session.execute(
                select(User).where(
                    User.traffic_enabled == True,  # noqa: E712
                    User.traffic_origin.isnot(None),
                    User.traffic_destination.isnot(None),
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
