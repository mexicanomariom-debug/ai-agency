from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.copy import PRODUCT_SUITE

router = Router()


@router.message(Command("product"))
async def cmd_product(message: Message) -> None:
    await message.answer(PRODUCT_SUITE)


@router.callback_query(F.data == "menu:product")
async def menu_product(callback: CallbackQuery) -> None:
    await callback.message.answer(PRODUCT_SUITE)
    await callback.answer()
