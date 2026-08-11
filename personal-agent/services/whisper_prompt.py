"""Spelling hints for OpenAI Whisper (mixed Russian + foreign words)."""

from __future__ import annotations

_LANG_PROMPTS: dict[str, str] = {
    "en": (
        "Hello. How are you? Mixed Russian and English. "
        "Tasks, reminders, notes. Accurate English spelling."
    ),
    "es": (
        "Me llamo. Hola. Gracias. Mixed Russian and Spanish. "
        "Prefer correct Spanish spelling: llamo, llegar, ella, pollo, calle."
    ),
    "de": "Guten Tag. Ich heiße. Mixed Russian and German speech.",
    "fr": "Bonjour. Je m'appelle. Mixed Russian and French speech.",
    "it": "Ciao. Mi chiamo. Mixed Russian and Italian speech.",
    "pt": "Olá. Meu nome é. Mixed Russian and Portuguese speech.",
    "uk": "Привіт. Змішана українська та російська мова.",
    "zh": "你好. Mixed Russian and Chinese speech.",
    "ja": "こんにちは. Mixed Russian and Japanese speech.",
    "ko": "안녕하세요. Mixed Russian and Korean speech.",
}

_DEFAULT_ASSISTANT = (
    "Russian speech for a personal assistant. Tasks, reminders, notes, calendar. "
    "Accurate Russian spelling and punctuation."
)

_DEFAULT_TRANSLATOR = (
    "Mixed Russian and foreign-language speech. Translation mode. "
    "Keep target-language spelling accurate."
)


def whisper_prompt_for(
    *,
    target_lang: str | None = None,
    in_translator: bool = False,
) -> str:
    if in_translator:
        if target_lang and target_lang != "auto":
            return _LANG_PROMPTS.get(target_lang, _DEFAULT_TRANSLATOR)
        return _DEFAULT_TRANSLATOR
    return _DEFAULT_ASSISTANT
