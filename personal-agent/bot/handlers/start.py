from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.copy import HELP_TEXT, TIMEZONE_SETUP_PROMPT, WELCOME
from bot.keyboards.reply import main_menu_keyboard
from config import settings
from bot.utils.messages import answer_menu
from database.models import User
from services.user_service import user_service

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession, state: FSMContext) -> None:
    await state.clear()
    result = await session.execute(
        select(User).where(User.telegram_id == message.from_user.id)
    )
    is_new = result.scalar_one_or_none() is None

    await user_service.get_or_create(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )
    name = message.from_user.first_name or "друг"
    await message.answer(WELCOME.format(name=name), reply_markup=main_menu_keyboard())
    if is_new:
        await message.answer(TIMEZONE_SETUP_PROMPT)


@router.message(Command("version"))
async def cmd_version(message: Message) -> None:
    await answer_menu(
        message,
        f"🤖 Личный агент\n"
        f"Сборка: <code>{settings.bot_build_id}</code>\n"
        f"Сервер: <code>{settings.environment}</code>\n\n"
        "Если сборка <code>dev</code> или старая — вы общаетесь не с Oracle-ботом.\n"
        "Остановите локальный <code>start-bot</code> на ПК.",
    )


@router.message(Command("help"))
@router.message(lambda m: m.text == "❓ Помощь")
async def cmd_help(message: Message) -> None:
    await answer_menu(message, HELP_TEXT)
