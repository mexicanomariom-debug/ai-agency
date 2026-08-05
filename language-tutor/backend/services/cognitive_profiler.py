from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.enums import Language, ProficiencyLevel
from database.models import CognitiveProfile, User


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

        notes = profile.grammar_notes or ""
        if len(user_message) > 20:
            snippet = user_message[:200]
            if snippet not in notes:
                profile.grammar_notes = (notes + f"\nObserved: {snippet}").strip()[:2000]

        await session.flush()
        return profile

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
        if profile.grammar_notes:
            parts.append(f"Grammar notes: {profile.grammar_notes}")
        return "\n".join(parts)


cognitive_profiler = CognitiveProfiler()
