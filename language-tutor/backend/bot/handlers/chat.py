from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.reply import TEXT_CHAT_LABEL, VOICE_TEACHER_LABEL
from bot.states.onboarding import OnboardingStates
from services.chat_service import process_user_text

router = Router()


@router.message(OnboardingStates.chatting, F.text)
async def handle_chat(message: Message, session: AsyncSession) -> None:
    if message.text in {VOICE_TEACHER_LABEL, TEXT_CHAT_LABEL}:
        return
    await process_user_text(message, session, message.text)


@router.message(F.text)
async def handle_unboarded(message: Message) -> None:
    if message.text in {VOICE_TEACHER_LABEL, TEXT_CHAT_LABEL}:
        return
    await message.answer("Начни с /start, чтобы выбрать язык и уровень.")
