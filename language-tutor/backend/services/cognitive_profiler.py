from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from database.enums import Language, ProficiencyLevel
from database.models import CognitiveProfile, User


def _merge_bullets(existing: str | None, new_items: list[str], limit: int = 8) -> str:
    seen: list[str] = []
    for source in (existing or "").split("\n"):
        line = source.strip().lstrip("-• ").strip()
        if line and line not in seen:
            seen.append(line)
    for item in new_items:
        line = item.strip().lstrip("-• ").strip()
        if line and line not in seen:
            seen.append(line)
    return "\n".join(seen[:limit])


class CognitiveProfiler:
    async def get_or_create(self, session: AsyncSession, user: User) -> CognitiveProfile:
        if user.cognitive_profile:
            return user.cognitive_profile

        profile = CognitiveProfile(user_id=user.id)
        session.add(profile)
        await session.flush()
        return profile

    async def update_from_conversation(
        self,
        session: AsyncSession,
        user: User,
        user_message: str,
        assistant_response: str,
    ) -> CognitiveProfile:
        profile = await self.get_or_create(session, user)

        if user.language and user.level:
            profile.vocabulary_level = f"{user.language.value} — {user.level.value}"

        await session.flush()
        return profile

    async def apply_session_assessment(
        self,
        session: AsyncSession,
        user: User,
        *,
        speaking_cefr: str | None,
        mapped_level: ProficiencyLevel | None,
        confidence: str,
        strengths: list[str],
        weaknesses: list[str],
        grammar_focus: list[str],
        recommendation: str | None,
        summary: str | None,
    ) -> bool:
        profile = await self.get_or_create(session, user)

        if strengths:
            profile.strengths = _merge_bullets(profile.strengths, strengths)
        if weaknesses:
            profile.weaknesses = _merge_bullets(profile.weaknesses, weaknesses)

        if grammar_focus:
            notes = _merge_bullets(profile.grammar_notes, grammar_focus, limit=10)
            if recommendation:
                notes = _merge_bullets(notes, [f"Next: {recommendation}"], limit=10)
            profile.grammar_notes = notes

        if speaking_cefr:
            profile.last_speaking_cefr = speaking_cefr
        if summary:
            profile.last_session_summary = summary[:2000]
        profile.last_assessed_at = datetime.now(timezone.utc)

        if user.language and mapped_level:
            profile.vocabulary_level = f"{user.language.value} — {mapped_level.value} (CEFR {speaking_cefr or '?'})"

        level_updated = False
        if mapped_level and confidence == "high" and user.language:
            if user.level != mapped_level:
                user.level = mapped_level
                level_updated = True

        await session.flush()
        return level_updated

    def build_context(self, profile: CognitiveProfile | None) -> str:
        if not profile:
            return ""
        parts = []
        if profile.strengths:
            parts.append(f"Strengths: {profile.strengths}")
        if profile.weaknesses:
            parts.append(f"Weaknesses: {profile.weaknesses}")
        if profile.learning_style:
            parts.append(f"Learning style: {profile.learning_style}")
        if profile.vocabulary_level:
            parts.append(f"Vocabulary level: {profile.vocabulary_level}")
        if profile.last_speaking_cefr:
            parts.append(f"Last assessed speaking (CEFR): {profile.last_speaking_cefr}")
        if profile.last_session_summary:
            parts.append(f"Last session summary: {profile.last_session_summary}")
        if profile.grammar_notes:
            parts.append(f"Grammar notes: {profile.grammar_notes}")
        return "\n".join(parts)


cognitive_profiler = CognitiveProfiler()
