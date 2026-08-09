from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from openai import AsyncOpenAI

from config import settings

logger = logging.getLogger(__name__)

LANGUAGES: dict[str, str] = {
    "ru": "🇷🇺 Русский",
    "en": "🇬🇧 English",
    "es": "🇪🇸 Español",
    "de": "🇩🇪 Deutsch",
    "fr": "🇫🇷 Français",
    "it": "🇮🇹 Italiano",
    "pt": "🇵🇹 Português",
    "uk": "🇺🇦 Українська",
    "pl": "🇵🇱 Polski",
    "tr": "🇹🇷 Türkçe",
    "zh": "🇨🇳 中文",
    "ja": "🇯🇵 日本語",
    "ko": "🇰🇷 한국어",
    "ar": "🇸🇦 العربية",
    "hi": "🇮🇳 हिन्दी",
    "th": "🇹🇭 ไทย",
    "vi": "🇻🇳 Tiếng Việt",
}

# ISO-ish aliases → code
LANG_ALIASES: dict[str, str] = {
    "русский": "ru",
    "russian": "ru",
    "ru": "ru",
    "английский": "en",
    "english": "en",
    "en": "en",
    "eng": "en",
    "испанский": "es",
    "spanish": "es",
    "español": "es",
    "es": "es",
    "немецкий": "de",
    "german": "de",
    "deutsch": "de",
    "de": "de",
    "французский": "fr",
    "french": "fr",
    "fr": "fr",
    "итальянский": "it",
    "italian": "it",
    "it": "it",
    "португальский": "pt",
    "portuguese": "pt",
    "pt": "pt",
    "украинский": "uk",
    "ukrainian": "uk",
    "uk": "uk",
    "польский": "pl",
    "polish": "pl",
    "pl": "pl",
    "турецкий": "tr",
    "turkish": "tr",
    "tr": "tr",
    "китайский": "zh",
    "chinese": "zh",
    "zh": "zh",
    "японский": "ja",
    "japanese": "ja",
    "ja": "ja",
    "корейский": "ko",
    "korean": "ko",
    "ko": "ko",
    "арабский": "ar",
    "arabic": "ar",
    "ar": "ar",
    "хинди": "hi",
    "hindi": "hi",
    "hi": "hi",
    "тайский": "th",
    "thai": "th",
    "th": "th",
    "вьетнамский": "vi",
    "vietnamese": "vi",
    "vi": "vi",
}

LANG_CODE_ALIASES: dict[str, str] = {
    "eng": "en",
    "rus": "ru",
    "esp": "es",
    "deu": "de",
    "fra": "fr",
    "ita": "it",
    "por": "pt",
    "ukr": "uk",
    "pol": "pl",
    "tur": "tr",
    "zho": "zh",
    "cmn": "zh",
    "jpn": "ja",
    "kor": "ko",
    "ara": "ar",
    "hin": "hi",
    "tha": "th",
    "vie": "vi",
}


@dataclass
class TranslationResult:
    source_text: str
    translated_text: str
    source_lang: str
    target_lang: str


@dataclass
class ParsedTranslateRequest:
    text: str
    target_lang: str | None = None


def normalize_lang_code(code: str | None) -> str:
    if not code:
        return "?"
    raw = code.strip().lower().replace("_", "-").split("-")[0]
    return LANG_CODE_ALIASES.get(raw, raw)


class TranslatorService:
    def __init__(self) -> None:
        self._openai = AsyncOpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

    @property
    def available(self) -> bool:
        return self._openai is not None

    def language_label(self, code: str) -> str:
        normalized = normalize_lang_code(code)
        return LANGUAGES.get(normalized, normalized.upper())

    def resolve_alias(self, name: str) -> str | None:
        key = name.strip().lower()
        if key in LANG_ALIASES:
            code = LANG_ALIASES[key]
            return code if code in LANGUAGES else None
        return None

    def parse_inline_request(self, text: str) -> ParsedTranslateRequest | None:
        stripped = text.strip()
        lower = stripped.lower()
        if not lower.startswith(("переведи", "перевод", "translate")):
            return None

        body = stripped
        for prefix in ("переведи", "перевод", "translate"):
            if lower.startswith(prefix):
                body = stripped[len(prefix) :].strip()
                break

        target_lang, body = self._extract_target_lang(body)
        if not body:
            return None
        return ParsedTranslateRequest(text=body, target_lang=target_lang)

    def parse_target_prefix(self, text: str) -> ParsedTranslateRequest | None:
        """In translator mode: «на испанский: текст» or «to english: text»."""
        stripped = text.strip()
        target_lang, body = self._extract_target_lang(stripped)
        if target_lang and body:
            return ParsedTranslateRequest(text=body, target_lang=target_lang)
        return None

    def _extract_target_lang(self, body: str) -> tuple[str | None, str]:
        body_stripped = body.strip()
        lower = body_stripped.lower()

        for alias, code in sorted(LANG_ALIASES.items(), key=lambda item: len(item[0]), reverse=True):
            patterns = (
                f"на {alias}:",
                f"на {alias} ",
                f"to {alias}:",
                f"to {alias} ",
                f"в {alias}:",
                f"в {alias} ",
            )
            for pattern in patterns:
                if lower.startswith(pattern):
                    rest = body_stripped[len(pattern) :].strip()
                    if code in LANGUAGES:
                        return code, rest

        return None, body_stripped

    def resolve_auto_target(self, source_lang: str, user_preferred: str = "en") -> str:
        """Default: foreign → Russian; Russian → user's preferred (usually English)."""
        source = normalize_lang_code(source_lang)
        if source == "ru":
            preferred = normalize_lang_code(user_preferred)
            return preferred if preferred in LANGUAGES and preferred != "ru" else "en"
        return "ru"

    async def translate(
        self,
        text: str,
        target_lang: str,
        *,
        user_preferred_lang: str = "en",
    ) -> TranslationResult | None:
        if not self._openai or not text.strip():
            return None

        explicit_target = None if target_lang == "auto" else normalize_lang_code(target_lang)
        if explicit_target and explicit_target not in LANGUAGES:
            explicit_target = self.resolve_alias(target_lang)

        if explicit_target:
            target_instruction = (
                f"Detect the source language. Translate into {self.language_label(explicit_target)} "
                f"(ISO code {explicit_target})."
            )
            resolved_target = explicit_target
        else:
            target_instruction = (
                "Detect the source language (ISO 639-1) accurately — Spanish is es, not ru. "
                "Translate into Russian (ru) unless the source is already Russian. "
                "If source is Russian (ru), translate into English (en). "
                "Never output the same language as both source and target unless impossible."
            )
            resolved_target = "auto"

        try:
            response = await self._openai.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a professional translator. "
                            f"{target_instruction} "
                            "Use natural, fluent wording. "
                            'Reply ONLY valid JSON: '
                            '{"source_lang":"iso","target_lang":"iso","translation":"text"}'
                        ),
                    },
                    {"role": "user", "content": text},
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
            )
            data = json.loads(response.choices[0].message.content or "{}")
            translation = (data.get("translation") or "").strip()
            if not translation:
                return None

            source_lang = normalize_lang_code(data.get("source_lang"))
            out_target = normalize_lang_code(data.get("target_lang"))

            if resolved_target == "auto":
                out_target = self.resolve_auto_target(source_lang, user_preferred_lang)
            else:
                out_target = resolved_target

            if source_lang == out_target:
                if source_lang == "ru":
                    out_target = self.resolve_auto_target("ru", user_preferred_lang)
                else:
                    out_target = "ru"

            if translation.lower().strip() == text.lower().strip() and source_lang == out_target:
                return None

            return TranslationResult(
                source_text=text,
                translated_text=translation,
                source_lang=source_lang,
                target_lang=out_target,
            )
        except Exception:
            logger.exception("Translation failed")
            return None

    def supported_languages_text(self) -> str:
        return ", ".join(f"{label}" for _, label in list(LANGUAGES.items())[:8]) + ", …"


translator_service = TranslatorService()
