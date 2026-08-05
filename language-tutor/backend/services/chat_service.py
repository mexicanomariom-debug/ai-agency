from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from database.enums import MessageRole
from database.rag import rag_service
from services.chat_history import chat_history_service
from services.cognitive_profiler import cognitive_profiler
from services.openai_service import openai_service
from services.personas import persona_service
from services.user_service import user_service


def _build_system_prompt(user, persona, rag_context: str, cognitive_context: str) -> str:
    parts = [persona.system_prompt]

    if user.language:
        parts.append(f"The student is learning {user.language.value.title()}.")
    if user.level:
        parts.append(f"Their level is {user.level.value.replace('_', ' ').title()}.")
    if cognitive_context:
        parts.append(f"Student profile:\n{cognitive_context}")
    if rag_context:
        parts.append(f"Relevant learning material (FGOS school program):\n{rag_context}")

    parts.append("Respond in the target language when appropriate for practice.")
    return "\n\n".join(parts)


async def process_user_text(
    message: Message,
    session: AsyncSession,
    user_text: str,
    *,
    from_voice: bool = False,
) -> str | None:
    user = await user_service.get_by_telegram_id(session, message.from_user.id)
    if not user or not user.is_onboarded:
        await message.answer("Сначала пройди онбординг: /start")
        return None

    persona = await persona_service.get_default(session)
    history = await chat_history_service.get_recent(session, user, limit=10)

    rag_context = ""
    if user.language and user.level:
        chunks = await rag_service.search(session, user_text, user.language, user.level)
        rag_context = await rag_service.format_context(chunks)

    cognitive_context = cognitive_profiler.build_context(user.cognitive_profile)
    system_prompt = _build_system_prompt(user, persona, rag_context, cognitive_context)

    openai_messages = chat_history_service.to_openai_messages(history)
    openai_messages.append({"role": "user", "content": user_text})

    await message.bot.send_chat_action(message.chat.id, "typing")

    try:
        response = await openai_service.chat_completion(openai_messages, system_prompt)
    except Exception:
        await message.answer("Не удалось обработать сообщение. Попробуй ещё раз.")
        return None

    await chat_history_service.add_message(session, user, MessageRole.USER, user_text, persona)
    await chat_history_service.add_message(session, user, MessageRole.ASSISTANT, response, persona)
    await cognitive_profiler.update_from_conversation(session, user, user_text, response)

    prefix = "🎙 " if from_voice else ""
    await message.answer(f"{prefix}{response}")
    return response
