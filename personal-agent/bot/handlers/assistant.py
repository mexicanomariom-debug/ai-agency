from aiogram import F, Router
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.copy import NOTE_CREATED, PARSE_FAILED, TASK_LIST_EMPTY, TASK_TODAY_HEADER
from database.models import User
from services.assistant import Intent, assistant_service
from services.chat_history import chat_history_service
from services.note_service import note_service
from services.task_flow import format_due_at, format_notify_types, reply_with_created_tasks
from services.task_parser import task_parser
from services.user_service import task_service, user_service

router = Router()


async def process_user_message(
    message: Message,
    session: AsyncSession,
    user: User,
    text: str,
) -> None:
    intent = await assistant_service.classify_intent(text, user.timezone)

    if intent == Intent.CREATE_TASK:
        parsed = await task_parser.parse(text, user.timezone)
        if parsed.tasks:
            await reply_with_created_tasks(message, session, user, parsed)
            return
        await message.answer(PARSE_FAILED)
        return

    if intent == Intent.CREATE_NOTE:
        _, content = assistant_service.extract_note_content(text)
        if not content:
            await message.answer("Напишите текст заметки, например: Заметка: идея проекта")
            return
        note = await note_service.create(session, user, content=content)
        await message.answer(NOTE_CREATED.format(note_id=note.id))
        return

    if intent == Intent.LIST_NOTES:
        from bot.handlers.notes import cmd_notes

        await cmd_notes(message, session)
        return

    if intent == Intent.LIST_TASKS:
        tasks = await task_service.list_today(session, user)
        if not tasks:
            await message.answer(TASK_LIST_EMPTY)
            return
        lines = [TASK_TODAY_HEADER.format(count=len(tasks))]
        for task in tasks:
            lines.append(
                f"#{task.id} — <b>{task.title}</b>\n"
                f"⏰ {format_due_at(task.due_at, user.timezone)} · "
                f"{format_notify_types(task.notify_message, task.notify_call, task.notify_phone)}"
            )
        await message.answer("\n\n".join(lines))
        return

    history = await chat_history_service.get_recent(session, user)
    reply = await assistant_service.chat(text, history)
    await chat_history_service.add(session, user, "user", text)
    await chat_history_service.add(session, user, "assistant", reply)
    await message.answer(reply)


@router.message(F.text)
async def handle_text(message: Message, session: AsyncSession) -> None:
    if not message.text or message.text.startswith("/"):
        return

    quick_buttons = {
        "📋 Мои задачи",
        "❓ Помощь",
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
