from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database.enums import SubscriptionTier
from services.payment_service import payment_service
from services.user_service import user_service

router = Router()


@router.message(Command("subscribe"))
async def cmd_subscribe(message: Message, session: AsyncSession) -> None:
    user = await user_service.get_by_telegram_id(session, message.from_user.id)
    if not user:
        await message.answer("Please /start first.")
        return

    tier = user.subscription_tier.value.title()
    limit = payment_service.get_daily_limit(user)
    limit_text = "unlimited" if limit < 0 else str(limit)

    await message.answer(
        f"Your plan: <b>{tier}</b>\n"
        f"Daily messages: <b>{limit_text}</b>\n\n"
        f"Upgrade at {settings.twa_url}/pricing"
    )


@router.message(Command("status"))
async def cmd_status(message: Message, session: AsyncSession) -> None:
    user = await user_service.get_by_telegram_id(session, message.from_user.id)
    if not user:
        await message.answer("Please /start first.")
        return

    lang = user.language.value.title() if user.language else "Not set"
    level = user.level.value.replace("_", " ").title() if user.level else "Not set"
    onboarded = "Yes" if user.is_onboarded else "No"

    await message.answer(
        f"<b>Your Profile</b>\n"
        f"Language: {lang}\n"
        f"Level: {level}\n"
        f"Onboarded: {onboarded}\n"
        f"Plan: {user.subscription_tier.value.title()}"
    )
