from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.utils.callbacks import usable_message
from services.progress_service import progress_service
from services.user_service import user_service

router = Router()


async def _send_progress(message: Message, session: AsyncSession, telegram_id: int) -> None:
    user = await user_service.get_by_telegram_id(session, telegram_id)
    if not user or not user.is_onboarded:
        await message.answer("Сначала пройди онбординг: /start")
        return

    snapshot = await progress_service.get_snapshot(session, user)
    await message.answer(progress_service.format_telegram(snapshot))


@router.message(Command("progress"))
async def cmd_progress(message: Message, session: AsyncSession) -> None:
    await _send_progress(message, session, message.from_user.id)


@router.callback_query(F.data == "menu:progress")
async def menu_progress(callback: CallbackQuery, session: AsyncSession) -> None:
    target = usable_message(callback)
    await callback.answer()
    if target is not None:
        await _send_progress(target, session, callback.from_user.id)
