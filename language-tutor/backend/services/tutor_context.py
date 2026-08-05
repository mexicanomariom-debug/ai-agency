from database.models import User


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
            parts.append(f"Their level is {user.level.value.replace('_', ' ').title()}.")

    if cognitive_context:
        parts.append(f"Student profile:\n{cognitive_context}")
    if rag_context:
        parts.append(f"Relevant learning material:\n{rag_context}")

    parts.append(
        "You are a professional teacher and tutor. Be encouraging, correct mistakes gently, "
        "and adapt explanations to the student's level."
    )

    if voice_mode:
        parts.append(
            "VOICE MODE: Reply in 2-4 short spoken sentences. "
            "Use the target language for practice; brief Russian explanations only when needed. "
            "No markdown, lists, or emojis — plain speech."
        )
    else:
        parts.append("Respond in the target language when appropriate for practice.")

    return "\n\n".join(parts)
