import base64

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user, get_db
from api.schemas import (
    VoiceCapabilitiesResponse,
    VoiceChatRequest,
    VoiceSessionAssessmentResponse,
    VoiceSessionCloseRequest,
    VoiceTalkResponse,
    VoiceTutorResponse,
)
from config import settings
from database.enums import MessageRole
from database.models import User
from database.rag import rag_service
from services.chat_history import chat_history_service
from services.cognitive_profiler import cognitive_profiler
from services.llm_service import llm_service
from services.openai_service import openai_service
from services.personas import persona_service
from services.session_assessment import session_assessment_service
from services.tutor_context import build_tutor_system_prompt

router = APIRouter(prefix="/voice", tags=["voice"])

VOICE_TUTOR_SLUG = "voice-teacher"


@router.get("/tutor", response_model=VoiceTutorResponse)
async def get_voice_tutor(
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> VoiceTutorResponse:
    persona = await persona_service.get_by_slug(session, VOICE_TUTOR_SLUG)
    if not persona:
        persona = await persona_service.get_default(session)

    lang = user.language.value if user.language else None
    level = user.level.value if user.level else None
    audience = user.audience.value if user.audience else None
    first = user.first_name or "друг"

    if audience == "child":
        greeting = (
            f"Привет, {first}! Я Илья — твой учитель. "
            "Жми микрофон и говори — я отвечу голосом, как настоящий человек!"
        )
    elif audience == "teen":
        greeting = (
            f"Привет, {first}! Я Илья. Держи микрофон и говори — "
            "разберём язык по-взрослому, без скуки."
        )
    else:
        greeting = (
            f"Добро пожаловать, {first}. Я Илья, ваш премиальный репетитор. "
            "Удерживайте микрофон — отвечу голосом с живой мимикой."
        )

    return VoiceTutorResponse(
        name=persona.name,
        slug=persona.slug,
        description=persona.description,
        language=lang,
        level=level,
        audience=audience,
        greeting=greeting,
    )


@router.get("/capabilities", response_model=VoiceCapabilitiesResponse)
async def voice_capabilities() -> VoiceCapabilitiesResponse:
    has_openai = bool(settings.openai_api_key)
    has_llm = bool(settings.anthropic_api_key or settings.openai_api_key)
    provider = "anthropic" if settings.anthropic_api_key else ("openai" if has_openai else None)
    return VoiceCapabilitiesResponse(
        llm=has_llm,
        stt=has_openai,
        tts=has_openai,
        provider=provider,
    )


async def _generate_voice_reply(
    session: AsyncSession,
    user: User,
    transcript: str,
    persona_slug: str | None,
) -> VoiceTalkResponse:
    slug = persona_slug or VOICE_TUTOR_SLUG
    persona = await persona_service.get_by_slug(session, slug) or await persona_service.get_default(session)

    history = await chat_history_service.get_recent(session, user, limit=10, persona=persona)

    rag_context = ""
    if user.language and user.level:
        chunks = await rag_service.search(session, transcript, user.language, user.level)
        rag_context = await rag_service.format_context(chunks)

    cognitive_context = cognitive_profiler.build_context(user.cognitive_profile)
    system_prompt = build_tutor_system_prompt(
        persona,
        user=user,
        rag_context=rag_context,
        cognitive_context=cognitive_context,
        voice_mode=True,
    )

    messages = chat_history_service.to_openai_messages(history)
    messages.append({"role": "user", "content": transcript})

    try:
        reply = await llm_service.chat_completion(messages, system_prompt)
        if not (reply or "").strip():
            raise RuntimeError("Empty LLM reply")
    except Exception as exc:
        return VoiceTalkResponse(
            transcript=transcript,
            reply="Произошла ошибка при генерации ответа.",
            audio_base64=None,
            error=str(exc),
        )

    reply = reply.strip()
    await chat_history_service.add_message(session, user, MessageRole.USER, transcript, persona)
    await chat_history_service.add_message(session, user, MessageRole.ASSISTANT, reply, persona)
    await cognitive_profiler.update_from_conversation(session, user, transcript, reply)
    await session.commit()

    audio_mp3 = await openai_service.synthesize_speech(reply)
    audio_b64 = base64.b64encode(audio_mp3).decode("ascii") if audio_mp3 else None

    return VoiceTalkResponse(
        transcript=transcript,
        reply=reply,
        audio_base64=audio_b64,
        audio_mime="audio/mpeg" if audio_b64 else None,
    )


@router.post("/chat", response_model=VoiceTalkResponse)
async def voice_chat(
    body: VoiceChatRequest,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> VoiceTalkResponse:
    """Text in → teacher reply (works with Anthropic only; TTS optional via OpenAI)."""
    text = body.message.strip()
    if not text:
        return VoiceTalkResponse(
            transcript="",
            reply="Я вас не расслышал. Попробуйте ещё раз.",
            audio_base64=None,
        )
    return await _generate_voice_reply(session, user, text, body.persona_slug)


@router.post("/talk", response_model=VoiceTalkResponse)
async def voice_talk(
    audio: UploadFile = File(...),
    persona_slug: str | None = Form(None),
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> VoiceTalkResponse:
    audio_bytes = await audio.read()
    mime = audio.content_type or "audio/webm"

    try:
        transcript = await openai_service.transcribe_voice(audio_bytes, mime)
    except Exception as exc:
        return VoiceTalkResponse(
            transcript="",
            reply="",
            audio_base64=None,
            error=str(exc),
        )

    if not transcript.strip():
        return VoiceTalkResponse(
            transcript="",
            reply="Я вас не расслышал. Попробуйте говорить чуть громче.",
            audio_base64=None,
        )

    return await _generate_voice_reply(session, user, transcript, persona_slug)


@router.post("/session/close", response_model=VoiceSessionAssessmentResponse)
async def close_voice_session(
    body: VoiceSessionCloseRequest,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> VoiceSessionAssessmentResponse:
    """Run CEFR-style assessment on recent voice session messages and update profile."""
    slug = body.persona_slug or VOICE_TUTOR_SLUG
    persona = await persona_service.get_by_slug(session, slug) or await persona_service.get_default(session)

    result = await session_assessment_service.assess_voice_session(session, user, persona)
    await session.commit()

    return VoiceSessionAssessmentResponse(
        assessed=result.assessed,
        skipped_reason=result.skipped_reason,
        speaking_cefr=result.speaking_cefr,
        mapped_level=result.mapped_level,
        confidence=result.confidence,
        strengths=result.strengths,
        weaknesses=result.weaknesses,
        grammar_focus=result.grammar_focus,
        recommendation=result.recommendation,
        summary=result.summary,
        level_updated=result.level_updated,
        words_added=result.words_added,
    )
