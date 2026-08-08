"""Spelling / bilingual hints for OpenAI Whisper transcription."""

from database.enums import Language

_WHISPER_PROMPTS: dict[Language, str] = {
    Language.SPANISH: (
        "Me llamo. Hola. Gracias. Buenos días. ¿Cómo estás? "
        "Mixed Russian and Spanish. Prefer correct Spanish spelling: "
        "llamo, llegar, ella, pollo, calle."
    ),
    Language.ENGLISH: (
        "Hello. How are you? Mixed Russian and English speech for language learning."
    ),
    Language.GERMAN: (
        "Guten Tag. Ich heiße. Mixed Russian and German speech for language learning."
    ),
    Language.FRENCH: (
        "Bonjour. Je m'appelle. Mixed Russian and French speech for language learning."
    ),
    Language.ITALIAN: (
        "Ciao. Mi chiamo. Mixed Russian and Italian speech for language learning."
    ),
    Language.PORTUGUESE: (
        "Olá. Meu nome é. Mixed Russian and Portuguese speech for language learning."
    ),
    Language.CHINESE: (
        "你好. Mixed Russian and Chinese speech for language learning."
    ),
}

_DEFAULT_PROMPT = (
    "Mixed Russian and foreign-language speech for a language lesson. "
    "Keep target-language spelling accurate."
)


def whisper_prompt_for(language: Language | None) -> str:
    if language is None:
        return _DEFAULT_PROMPT
    return _WHISPER_PROMPTS.get(language, _DEFAULT_PROMPT)
