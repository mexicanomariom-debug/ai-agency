from database.models import User

from services.pedagogy import build_pedagogy_block


def build_tutor_system_prompt(
    persona,
    *,
    user: User | None = None,
    rag_context: str = "",
    cognitive_context: str = "",
    voice_mode: bool = False,
) -> str:
    parts = [persona.system_prompt]

    if user:
        if user.language:
            parts.append(f"The student is learning {user.language.value.title()}.")
        if user.level:
            parts.append(
                f"Their CEFR-style level is {user.level.value.replace('_', ' ').title()}. "
                "Calibrate vocabulary, grammar complexity, and speaking pace to this level."
            )

    if cognitive_context:
        parts.append(f"Student profile (use for fading and targeting weak areas):\n{cognitive_context}")
    if rag_context:
        parts.append(f"Relevant learning material (prefer this over general knowledge):\n{rag_context}")

    parts.append(build_pedagogy_block(voice_mode=voice_mode))

    return "\n\n".join(parts)
