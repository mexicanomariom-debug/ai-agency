from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from zoneinfo import ZoneInfo
from datetime import datetime

from bot.utils.html import h
from bot.utils.messages import answer_menu
from services.journal_service import journal_service
from services.user_service import user_service

router = Router()

KIND_LABELS = {
    "expense": "💸",
    "thought": "💭",
    "decision": "⚖️",
    "mood": "🌡",
    "insight": "✨",
}


@router.message(Command("journal"))
async def cmd_journal(message: Message, session: AsyncSession) -> None:
    user = await user_service.get_or_create(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )
    day_key = datetime.now(ZoneInfo(user.timezone)).date().isoformat()
    entries = await journal_service.list_for_day(session, user, day_key)
    if not entries:
        await answer_menu(message, "📔 Сегодня записей нет. Просто пиши — я подхвачу мысли, траты и решения.")
        return

    lines = ["📔 <b>Дневник за сегодня</b>\n"]
    for entry in entries:
        icon = KIND_LABELS.get(entry.kind, "•")
        extra = ""
        if entry.amount is not None:
            extra = f" — {entry.amount:g} {entry.currency or ''}".rstrip()
        lines.append(f"{icon} {h(entry.content)}{extra}")
    await answer_menu(message, "\n".join(lines))


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
            await answer_menu(message, f"🌙 Ночной итог в <b>{hour}:00</b>.")
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
    )
