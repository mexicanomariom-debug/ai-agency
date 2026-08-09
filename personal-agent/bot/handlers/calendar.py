from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.copy import (
    CALENDAR_DISABLED,
    CALENDAR_ENABLED,
    CALENDAR_NOT_CONFIGURED,
    CALENDAR_NOT_CONNECTED,
    CALENDAR_STATUS,
)
from config import settings
from bot.utils.messages import answer_menu
from services.google_calendar import google_calendar_service
from services.user_service import user_service

router = Router()


@router.message(Command("calendar"))
async def cmd_calendar(message: Message, session: AsyncSession) -> None:
    if not google_calendar_service.available:
        await answer_menu(message, CALENDAR_NOT_CONFIGURED)
        return

    user = await user_service.get_or_create(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )

    if user.google_refresh_token and user.google_calendar_enabled:
        await answer_menu(message, 
            CALENDAR_STATUS.format(
                status="подключён ✅",
                redirect=settings.google_redirect_uri,
            )
        )
        return

    auth_url = google_calendar_service.build_auth_url(message.from_user.id)
    await answer_menu(message, CALENDAR_NOT_CONNECTED.format(url=auth_url))


@router.message(Command("calendar_on"))
async def cmd_calendar_on(message: Message, session: AsyncSession) -> None:
    user = await user_service.get_or_create(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )
    if not user.google_refresh_token:
        await answer_menu(message, "Сначала подключите календарь: /calendar")
        return
    user.google_calendar_enabled = True
    await answer_menu(message, CALENDAR_ENABLED)


@router.message(Command("calendar_off"))
async def cmd_calendar_off(message: Message, session: AsyncSession) -> None:
    user = await user_service.get_or_create(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )
    user.google_calendar_enabled = False
    await answer_menu(message, CALENDAR_DISABLED)


@router.message(lambda m: m.text == "📅 Календарь")
async def btn_calendar(message: Message, session: AsyncSession) -> None:
    await cmd_calendar(message, session)
