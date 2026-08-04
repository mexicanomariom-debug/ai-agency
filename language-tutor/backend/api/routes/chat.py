import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user, get_db
from api.schemas import ChatStreamRequest
from database.enums import MessageRole
from database.models import User
from database.rag import rag_service
from services.chat_history import chat_history_service
from services.cognitive_profiler import cognitive_profiler
from services.openai_service import openai_service
from services.personas import persona_service

router = APIRouter(prefix="/chat", tags=["chat"])


def _build_system_prompt(user: User, persona, rag_context: str, cognitive_context: str) -> str:
    parts = [persona.system_prompt]
    if user.language:
        parts.append(f"The student is learning {user.language.value.title()}.")
    if user.level:
        parts.append(f"Their level is {user.level.value.replace('_', ' ').title()}.")
    if cognitive_context:
        parts.append(f"Student profile:\n{cognitive_context}")
    if rag_context:
        parts.append(f"Relevant learning material:\n{rag_context}")
    parts.append("Respond in the target language when appropriate for practice.")
    return "\n\n".join(parts)


async def _stream_response(
    session: AsyncSession,
    user: User,
    message: str,
    persona_slug: str | None,
) -> AsyncIterator[str]:
    if persona_slug:
        persona = await persona_service.get_by_slug(session, persona_slug)
        if not persona:
            yield f"data: {json.dumps({'error': 'Persona not found'})}\n\n"
            return
    else:
        persona = await persona_service.get_default(session)

    history = await chat_history_service.get_recent(session, user, limit=20, persona=persona)

    rag_context = ""
    if user.language and user.level:
        chunks = await rag_service.search(session, message, user.language, user.level)
        rag_context = await rag_service.format_context(chunks)

    cognitive_context = cognitive_profiler.build_context(user.cognitive_profile)
    system_prompt = _build_system_prompt(user, persona, rag_context, cognitive_context)

    openai_messages = chat_history_service.to_openai_messages(history)
    openai_messages.append({"role": "user", "content": message})

    full_response = ""
    try:
        async for chunk in openai_service.stream_chat_completion(openai_messages, system_prompt):
            full_response += chunk
            yield f"data: {json.dumps({'content': chunk, 'done': False})}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)})}\n\n"
        return

    await chat_history_service.add_message(session, user, MessageRole.USER, message, persona)
    await chat_history_service.add_message(session, user, MessageRole.ASSISTANT, full_response, persona)
    await cognitive_profiler.update_from_conversation(session, user, message, full_response)
    await session.commit()

    yield f"data: {json.dumps({'content': '', 'done': True})}\n\n"


@router.post("/stream")
async def chat_stream(
    body: ChatStreamRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    return StreamingResponse(
        _stream_response(session, user, body.message, body.persona_slug),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
