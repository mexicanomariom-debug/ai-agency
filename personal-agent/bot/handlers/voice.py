from aiogram import F, Router
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.copy import VOICE_FAILED, VOICE_HINT, VOICE_TRANSCRIBED
from services.assistant import Intent, assistant_service
from services.stt import stt_service
from services.task_parser import task_parser
from services.task_flow import reply_with_created_tasks
from services.user_service import user_service

router = Router()


@router.message(F.voice)
async def handle_voice(message: Message, session: AsyncSession) -> None:
    if not stt_service.available:
        await message.answer(VOICE_HINT)
        return

    await message.bot.send_chat_action(message.chat.id, "typing")
    text = await stt_service.transcribe_telegram_voice(message.bot, message.voice.file_id)
    if not text:
        await message.answer(VOICE_FAILED)
        return

    await message.answer(VOICE_TRANSCRIBED.format(text=text))

    user = await user_service.get_or_create(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )

    intent = await assistant_service.classify_intent(text, user.timezone)
    if intent == Intent.CREATE_TASK:
        parsed = await task_parser.parse(text, user.timezone)
        if parsed.tasks:
            await reply_with_created_tasks(message, session, user, parsed)
            return

    from bot.handlers.assistant import process_user_message

    await process_user_message(message, session, user, text)
