from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.copy import (
    INVALID_PHONE,
    PHONE_CURRENT,
    PHONE_REMOVED,
    PHONE_SAVED,
    PHONE_TWILIO_NOT_CONFIGURED,
)
from config import settings
from bot.utils.messages import answer_menu
from services.user_service import user_service

router = Router()


@router.message(Command("phone"))
async def cmd_phone(message: Message, session: AsyncSession) -> None:
    parts = (message.text or "").split(maxsplit=1)
    user = await user_service.get_or_create(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )

    if len(parts) < 2:
        if user.phone_number:
            await answer_menu(message, PHONE_CURRENT.format(phone=user.phone_number))
        else:
            await answer_menu(message, "Использование: /phone +79991234567")
        return

    arg = parts[1].strip().lower()
    if arg in ("off", "remove", "удалить"):
        user.phone_number = None
        await answer_menu(message, PHONE_REMOVED)
        return

    if not settings.has_twilio:
        await answer_menu(message, PHONE_TWILIO_NOT_CONFIGURED)
        return

    ok = await user_service.set_phone(session, user, parts[1].strip())
    if not ok:
        await answer_menu(message, INVALID_PHONE)
        return
    await answer_menu(message, PHONE_SAVED.format(phone=user.phone_number))


@router.message(lambda m: m.text == "📞 Телефон")
async def btn_phone(message: Message, session: AsyncSession) -> None:
    user = await user_service.get_or_create(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )
    if user.phone_number:
        await answer_menu(message, PHONE_CURRENT.format(phone=user.phone_number))
    else:
        await answer_menu(message, "Укажите номер: /phone +79991234567")
