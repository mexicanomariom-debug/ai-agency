import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.enums import MessageRole, ProficiencyLevel
from database.models import ChatMessage, Persona, SessionAssessment, User
from services.cognitive_profiler import cognitive_profiler
from services.llm_service import llm_service

CEFR_TO_LEVEL: dict[str, ProficiencyLevel] = {
    "A1": ProficiencyLevel.BEGINNER,
    "A2": ProficiencyLevel.ELEMENTARY,
    "B1": ProficiencyLevel.INTERMEDIATE,
    "B2": ProficiencyLevel.UPPER_INTERMEDIATE,
    "C1": ProficiencyLevel.ADVANCED,
    "C2": ProficiencyLevel.ADVANCED,
}

LEVEL_LABELS: dict[ProficiencyLevel, str] = {
    ProficiencyLevel.BEGINNER: "A1",
    ProficiencyLevel.ELEMENTARY: "A2",
    ProficiencyLevel.INTERMEDIATE: "B1",
    ProficiencyLevel.UPPER_INTERMEDIATE: "B2",
    ProficiencyLevel.ADVANCED: "C1",
    ProficiencyLevel.NATIVE: "C2",
}

MIN_USER_MESSAGES = 2
SESSION_LOOKBACK_HOURS = 3
MAX_TRANSCRIPT_MESSAGES = 24


@dataclass
class SessionAssessmentResult:
    assessed: bool
    skipped_reason: str | None = None
    speaking_cefr: str | None = None
    mapped_level: str | None = None
    confidence: str | None = None
    strengths: list[str] = []
    weaknesses: list[str] = []
    grammar_focus: list[str] = []
    recommendation: str | None = None
    summary: str | None = None
    level_updated: bool = False


def _parse_json_object(text: str) -> dict:
    cleaned = text.strip()
    fence = re.search(r"```(?:json)?\s*([\{].*?[\}])\s*```", cleaned, re.DOTALL)
    if fence:
        cleaned = fence.group(1)
    else:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start >= 0 and end > start:
            cleaned = cleaned[start : end + 1]
    return json.loads(cleaned)


def _format_transcript(messages: list[ChatMessage]) -> str:
    lines: list[str] = []
    for msg in messages:
        label = "Student" if msg.role == MessageRole.USER else "Teacher"
        lines.append(f"{label}: {msg.content}")
    return "\n".join(lines)


def _normalize_cefr(value: str | None) -> str | None:
    if not value:
        return None
    match = re.search(r"(A1|A2|B1|B2|C1|C2)", value.upper())
    return match.group(1) if match else None


class SessionAssessmentService:
    async def _messages_for_session(
        self,
        session: AsyncSession,
        user: User,
        persona: Persona,
    ) -> list[ChatMessage]:
        profile = user.cognitive_profile
        since: datetime | None = None
        if profile and profile.last_assessed_at:
            since = profile.last_assessed_at
        else:
            since = datetime.now(timezone.utc) - timedelta(hours=SESSION_LOOKBACK_HOURS)

        stmt = (
            select(ChatMessage)
            .where(
                ChatMessage.user_id == user.id,
                ChatMessage.persona_id == persona.id,
                ChatMessage.created_at >= since,
            )
            .order_by(ChatMessage.created_at.asc())
            .limit(MAX_TRANSCRIPT_MESSAGES)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def assess_voice_session(
        self,
        session: AsyncSession,
        user: User,
        persona: Persona,
    ) -> SessionAssessmentResult:
        messages = await self._messages_for_session(session, user, persona)
        user_turns = [m for m in messages if m.role == MessageRole.USER]

        if len(user_turns) < MIN_USER_MESSAGES:
            return SessionAssessmentResult(
                assessed=False,
                skipped_reason="need_more_practice",
            )

        if not llm_service.has_provider():
            return SessionAssessmentResult(
                assessed=False,
                skipped_reason="no_llm",
            )

        transcript = _format_transcript(messages)
        lang = user.language.value if user.language else "unknown"
        current_level = user.level.value.replace("_", " ") if user.level else "unknown"
        audience = user.audience.value if user.audience else "adult"
        cefr_hint = LEVEL_LABELS.get(user.level, "unknown") if user.level else "unknown"

        system = (
            "You are an expert CEFR speaking assessor for language tutoring sessions. "
            "Return ONLY valid JSON, no markdown, no commentary."
        )
        user_prompt = f"""
Analyze this voice/chat tutoring session transcript.

Target language: {lang}
Student declared level: {current_level} (approx CEFR {cefr_hint})
Audience: {audience}

TRANSCRIPT:
{transcript}

Return JSON with exactly these keys:
{{
  "speaking_cefr": "A1|A2|B1|B2|C1|C2",
  "confidence": "low|medium|high",
  "strengths": ["2-4 short bullets in Russian"],
  "weaknesses": ["2-4 short bullets in Russian"],
  "grammar_focus": ["1-3 grammar points to practice next, Russian"],
  "recommendation_next": "one sentence in Russian — what to study next session",
  "session_summary": "2-3 sentences in Russian — what happened and progress"
}}

Rules:
- Base speaking_cefr on STUDENT utterances only (vocabulary range, grammar, fluency).
- Be conservative: short sessions need lower confidence.
- If student mostly spoke Russian, note that in weaknesses.
"""

        try:
            raw = await llm_service.chat_completion(
                [{"role": "user", "content": user_prompt}],
                system,
            )
            data = _parse_json_object(raw)
        except Exception:
            return SessionAssessmentResult(assessed=False, skipped_reason="assessment_failed")

        speaking_cefr = _normalize_cefr(str(data.get("speaking_cefr", "")))
        confidence = str(data.get("confidence", "low")).lower()
        if confidence not in {"low", "medium", "high"}:
            confidence = "low"

        strengths = [str(s).strip() for s in data.get("strengths", []) if str(s).strip()][:4]
        weaknesses = [str(s).strip() for s in data.get("weaknesses", []) if str(s).strip()][:4]
        grammar_focus = [str(s).strip() for s in data.get("grammar_focus", []) if str(s).strip()][:3]
        recommendation = str(data.get("recommendation_next", "")).strip() or None
        summary = str(data.get("session_summary", "")).strip() or None

        mapped = CEFR_TO_LEVEL.get(speaking_cefr) if speaking_cefr else None

        record = SessionAssessment(
            user_id=user.id,
            persona_id=persona.id,
            language=user.language.value if user.language else None,
            user_message_count=len(user_turns),
            speaking_cefr=speaking_cefr,
            mapped_level=mapped.value if mapped else None,
            confidence=confidence,
            strengths="\n".join(strengths) if strengths else None,
            weaknesses="\n".join(weaknesses) if weaknesses else None,
            grammar_focus="\n".join(grammar_focus) if grammar_focus else None,
            recommendation=recommendation,
            summary=summary,
        )
        session.add(record)

        level_updated = await cognitive_profiler.apply_session_assessment(
            session,
            user,
            speaking_cefr=speaking_cefr,
            mapped_level=mapped,
            confidence=confidence,
            strengths=strengths,
            weaknesses=weaknesses,
            grammar_focus=grammar_focus,
            recommendation=recommendation,
            summary=summary,
        )

        await session.flush()

        return SessionAssessmentResult(
            assessed=True,
            speaking_cefr=speaking_cefr,
            mapped_level=mapped.value if mapped else None,
            confidence=confidence,
            strengths=strengths,
            weaknesses=weaknesses,
            grammar_focus=grammar_focus,
            recommendation=recommendation,
            summary=summary,
            level_updated=level_updated,
        )


session_assessment_service = SessionAssessmentService()
