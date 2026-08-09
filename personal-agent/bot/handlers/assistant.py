from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.copy import NOTE_CREATED, PARSE_FAILED
from bot.handlers.tasks import cmd_tasks, cmd_today
from bot.handlers.task_edit import try_one_shot_edit
from bot.states.notebook import NotebookStates
from bot.states.task_edit import TaskEditStates
from bot.states.traffic import TrafficSetupStates
from bot.states.translator import TranslatorStates
from bot.utils.messages import answer_menu
from database.models import User
from services.assistant import Intent, assistant_service
from services.chat_history import chat_history_service
from services.note_service import note_service
from services.ambient import ambient_service
from services.task_flow import reply_with_created_tasks
from services.task_parser import task_parser
from services.user_service import user_service

router = Router()


async def process_user_message(
    message: Message,
    session: AsyncSession,
    user: User,
    text: str,
) -> None:
    if await try_one_shot_edit(message, session, user, text):
        return

    ambient_acks = await ambient_service.capture_from_text(session, user, text)

    parsed = await task_parser.parse(text, user.timezone)
    if parsed.tasks:
        await reply_with_created_tasks(message, session, user, parsed)
        if ambient_acks:
            await answer_menu(message, "🌊 " + "\n".join(ambient_acks))
        return

    intent = await assistant_service.classify_intent(text, user.timezone)

    if intent == Intent.CREATE_TASK:
        await answer_menu(message, PARSE_FAILED)
        return

    if intent == Intent.CREATE_NOTE:
        _, content = assistant_service.extract_note_content(text)
        if not content:
            await answer_menu(message, "Напишите текст заметки, например: Заметка: идея проекта")
            return
        note = await note_service.create(session, user, content=content)
        await answer_menu(message, NOTE_CREATED.format(note_id=note.id))
        return

    if intent == Intent.LIST_NOTES:
        from bot.handlers.notes import cmd_notes

        await cmd_notes(message, session)
        return

    if intent == Intent.LIST_TASKS_TODAY:
        await cmd_today(message, session)
        return

    if intent == Intent.LIST_TASKS:
        await cmd_tasks(message, session)
        return

    history = await chat_history_service.get_recent(session, user)
    reply = await assistant_service.chat(text, history)
    await chat_history_service.add(session, user, "user", text)
    await chat_history_service.add(session, user, "assistant", reply)
    if ambient_acks:
        reply = reply + "\n\n🌊 " + "\n".join(ambient_acks)
    await answer_menu(message, reply)


@router.message(F.text)
async def handle_text(message: Message, session: AsyncSession, state: FSMContext) -> None:
    if not message.text or message.text.startswith("/"):
        return

    if await state.get_state() == TranslatorStates.waiting_text.state:
        return

    if await state.get_state() == TaskEditStates.waiting_changes.state:
        return

    if await state.get_state() == NotebookStates.writing.state:
        return

    traffic_state = await state.get_state()
    if traffic_state and traffic_state.startswith(TrafficSetupStates.__name__):
        return

    quick_buttons = {
        "📋 Мои задачи",
        "❓ Помощь",
        "💡 Блокнот-Идеи",
        "🚗 Пробки",
        "📝 Заметки",
        "📅 Календарь",
        "📞 Телефон",
        "📆 Сегодня",
        "🌐 Переводчик",
    }
    if message.text in quick_buttons:
        return

    user = await user_service.get_or_create(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )
    await process_user_message(message, session, user, message.text)
