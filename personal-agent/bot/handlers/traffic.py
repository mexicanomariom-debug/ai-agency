"""Traffic monitoring commands."""

from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from services.traffic import (
    fetch_traffic,
    format_traffic_message,
    is_check_window,
)
from services.user_service import user_service

router = Router(name="traffic")


def _traffic_status(user: User) -> str:
    enabled = "✅ включён" if getattr(user, "traffic_enabled", False) else "❌ выключен"
    origin = getattr(user, "traffic_origin", None) or "—"
    dest = getattr(user, "traffic_destination", None) or "—"
    threshold = getattr(user, "traffic_threshold_min", 15) or 15
    start = getattr(user, "traffic_check_start", None) or "07:00"
    end = getattr(user, "traffic_check_end", None) or "10:00"
    window = "сейчас в окне" if is_check_window(user) else "вне окна проверки"

    return (
        f"🚗 <b>Мониторинг пробок</b>\n\n"
        f"Статус: {enabled}\n"
        f"📍 Откуда: {origin}\n"
        f"🏁 Куда: {dest}\n"
        f"⏰ Окно проверки: {start}–{end} ({window})\n"
        f"⚠️ Уведомлять при задержке: +{threshold} мин\n\n"
        f"<b>Команды:</b>\n"
        f"/traffic on — включить\n"
        f"/traffic off — выключить\n"
        f"/traffic set <откуда> | <куда>\n"
        f"/traffic check — проверить сейчас\n"
        f"/traffic threshold 15 — порог в минутах\n"
        f"/traffic hours 7:00 10:00 — окно проверки"
    )


@router.message(Command("traffic"))
async def cmd_traffic(message: Message, session: AsyncSession) -> None:
    if not message.text or not message.from_user:
        return

    user = await user_service.get_or_create(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )

    parts = message.text.split(maxsplit=2)
    sub = parts[1].lower() if len(parts) > 1 else ""

    if sub == "on":
        user.traffic_enabled = True
        await message.answer("🚗 Мониторинг пробок включён. Используйте /traffic set для маршрута.")
        return

    if sub == "off":
        user.traffic_enabled = False
        await message.answer("Мониторинг пробок выключен.")
        return

    if sub == "set" and len(parts) > 2:
        route = parts[2]
        if "|" in route:
            origin, dest = [s.strip() for s in route.split("|", 1)]
        elif "->" in route:
            origin, dest = [s.strip() for s in route.split("->", 1)]
        else:
            await message.answer("Формат: /traffic set Calle 10, Playa del Carmen | Cancún Airport")
            return
        if not origin or not dest:
            await message.answer("Укажите оба адреса через | или ->")
            return
        user.traffic_origin = origin
        user.traffic_destination = dest
        user.traffic_enabled = True
        await message.answer(f"✅ Маршрут сохранён:\n📍 {origin}\n🏁 {dest}\n\nПроверка: /traffic check")
        return

    if sub == "check":
        origin = getattr(user, "traffic_origin", None)
        dest = getattr(user, "traffic_destination", None)
        if not origin or not dest:
            await message.answer("Сначала задайте маршрут: /traffic set откуда | куда")
            return
        await message.answer("⏳ Проверяю пробки...")
        result = await fetch_traffic(origin, dest)
        if not result:
            await message.answer("Не удалось получить данные. Проверьте GOOGLE_MAPS_API_KEY и адреса.")
            return
        await message.answer(format_traffic_message(result), parse_mode="HTML")
        return

    if sub == "threshold" and len(parts) > 2:
        try:
            minutes = int(parts[2])
            if minutes < 1 or minutes > 120:
                raise ValueError()
            user.traffic_threshold_min = minutes
            await message.answer(f"Порог уведомлений: +{minutes} мин задержки")
        except ValueError:
            await message.answer("Укажите число от 1 до 120, например: /traffic threshold 15")
        return

    if sub == "hours" and len(parts) > 2:
        times = parts[2].split()
        if len(times) != 2:
            await message.answer("Формат: /traffic hours 7:00 10:00")
            return
        user.traffic_check_start = times[0]
        user.traffic_check_end = times[1]
        await message.answer(f"Окно проверки: {times[0]}–{times[1]} (ваш часовой пояс)")
        return

    await message.answer(_traffic_status(user), parse_mode="HTML")
