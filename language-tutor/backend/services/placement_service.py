import json
import re
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.enums import MessageRole, ProficiencyLevel
from database.models import ChatMessage, User
from services.cognitive_profiler import cognitive_profiler
from services.llm_service import llm_service
from services.session_assessment import CEFR_TO_LEVEL, LEVEL_LABELS
from services.user_service import user_service

PLACEMENT_INTRO = (
    "📋 <b>Мини-тест уровня</b> (5–7 вопросов, можно на русском).\n\n"
    "Так мы подберём программу, даже если вы не знаете свой CEFR.\n"
    "Отвечайте в чате — когда закончим, напишите <b>/program</b> для итогов и плана."
)

PLACEMENT_SYSTEM_BLOCK = """
PLACEMENT TEST MODE (active):
- Conduct a short level check mostly in RUSSIAN (student's native language).
- Ask 5–7 focused questions: prior study, self-assessment, sample translation/production,
  listening/reading comfort, goals (school, travel, work).
- Include 1–2 prompts in the TARGET LANGUAGE only if the student already studies it —
  scale difficulty up if they answer well; do not stay at baby level if they use B1+.
- Do NOT output the final level or full program yet — keep interviewing until the student
  sends /program or says they are done with the test.
- Be warm and clear; one question per message.
"""


def build_placement_program_block(user: User) -> str:
    lang = user.language.value if user.language else "english"
    return (
        f"{PLACEMENT_SYSTEM_BLOCK.strip()}\n"
        f"Target language to assess: {lang.title()}."
    )


@dataclass
class PlacementResult:
    success: bool
    skipped_reason: str | None = None
    speaking_cefr: str | None = None
    mapped_level: str | None = None
    confidence: str | None = None
    program: str | None = None
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
        label = "Student" if msg.role == MessageRole.USER else "Tutor"
        lines.append(f"{label}: {msg.content}")
    return "\n".join(lines)


def _normalize_cefr(value: str | None) -> str | None:
    if not value:
        return None
    match = re.search(r"(A1|A2|B1|B2|C1|C2)", value.upper())
    return match.group(1) if match else None


class PlacementService:
    async def finalize(
        self,
        session: AsyncSession,
        user: User,
        *,
        limit: int = 30,
    ) -> PlacementResult:
        stmt = (
            select(ChatMessage)
            .where(ChatMessage.user_id == user.id)
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
        )
        rows = list((await session.execute(stmt)).scalars().all())
        rows.reverse()

        user_msgs = [m for m in rows if m.role == MessageRole.USER]
        if len(user_msgs) < 2:
            return PlacementResult(
                success=False,
                skipped_reason="need_more_messages",
            )

        lang = user.language.value if user.language else "english"
        transcript = _format_transcript(rows)

        system = (
            "You are an expert language assessor and curriculum designer. "
            "Based on the placement dialogue, output ONLY valid JSON with keys:\n"
            "speaking_cefr (A1–C2), confidence (low|medium|high), summary (Russian, 2–3 sentences), "
            "program (Russian, structured 4-week plan with weekly themes and daily habits, "
            "bullet lines using •), recommendation (one next step).\n"
            f"Target language studied: {lang}."
        )

        prompt = (
            f"Student profile audience: {user.audience.value if user.audience else 'adult'}.\n"
            f"Current profile level label: {user.level.value if user.level else 'unknown'}.\n\n"
            f"Placement dialogue:\n{transcript}\n\n"
            "Infer the best CEFR level from demonstrated ability, not only self-report."
        )

        raw = await llm_service.chat_completion(
            [{"role": "user", "content": prompt}],
            system,
        )
        data = _parse_json_object(raw)

        speaking_cefr = _normalize_cefr(str(data.get("speaking_cefr", "")))
        confidence = str(data.get("confidence", "medium")).lower()
        summary = str(data.get("summary", "")).strip() or None
        program = str(data.get("program", "")).strip() or None
        recommendation = str(data.get("recommendation", "")).strip() or None

        mapped = CEFR_TO_LEVEL.get(speaking_cefr or "") if speaking_cefr else None
        level_updated = False

        if mapped and confidence in {"high", "medium"}:
            await user_service.set_level(session, user, mapped)
            level_updated = True

        if summary or recommendation:
            await cognitive_profiler.apply_session_assessment(
                session,
                user,
                speaking_cefr=speaking_cefr,
                mapped_level=mapped,
                confidence=confidence,
                strengths=[],
                weaknesses=[],
                grammar_focus=[],
                recommendation=recommendation,
                summary=summary or program,
            )

        await session.flush()

        return PlacementResult(
            success=True,
            speaking_cefr=speaking_cefr,
            mapped_level=LEVEL_LABELS.get(mapped) if mapped else None,
            confidence=confidence,
            program=program,
            summary=summary,
            level_updated=level_updated,
        )


placement_service = PlacementService()
