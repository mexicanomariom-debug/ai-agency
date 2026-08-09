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
    "zh": "🇨🇳 中文",
    "ar": "🇸🇦 العربية",
    "auto": "🔄 Умный (ru↔en)",
}

LANG_ALIASES: dict[str, str] = {
    "русский": "ru",
    "russian": "ru",
    "ru": "ru",
    "английский": "en",
    "english": "en",
    "en": "en",
    "испанский": "es",
    "spanish": "es",
    "es": "es",
    "немецкий": "de",
    "german": "de",
    "de": "de",
    "французский": "fr",
    "french": "fr",
    "fr": "fr",
    "китайский": "zh",
    "chinese": "zh",
    "zh": "zh",
    "арабский": "ar",
    "arabic": "ar",
    "ar": "ar",
    "auto": "auto",
    "умный": "auto",
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


class TranslatorService:
    def __init__(self) -> None:
        self._openai = AsyncOpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

    @property
    def available(self) -> bool:
        return self._openai is not None

    def language_label(self, code: str) -> str:
        return LANGUAGES.get(code, code)

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

        target_lang = None
        body_lower = body.lower()
        for alias, code in sorted(LANG_ALIASES.items(), key=lambda item: len(item[0]), reverse=True):
            for pattern in (f"на {alias}", f"to {alias}", alias):
                if body_lower.startswith(pattern):
                    body = body[len(pattern) :].strip().lstrip(":").strip()
                    target_lang = code
                    break
            if target_lang:
                break

        if not body:
            return None
        return ParsedTranslateRequest(text=body, target_lang=target_lang)

    async def translate(self, text: str, target_lang: str) -> TranslationResult | None:
        if not self._openai or not text.strip():
            return None

        if target_lang == "auto":
            target_instruction = (
                "Automatically detect the source language. "
                "If the text is Russian, translate to English. "
                "If the text is English, translate to Russian. "
                "For any other language, translate to Russian."
            )
            resolved_target = "auto"
        else:
            target_name = self.language_label(target_lang)
            target_instruction = f"Translate into {target_name} ({target_lang})."
            resolved_target = target_lang

        try:
            response = await self._openai.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a professional translator. "
                            f"{target_instruction} "
                            'Reply ONLY valid JSON: {"source_lang":"code","target_lang":"code","translation":"text"}'
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
            return TranslationResult(
                source_text=text,
                translated_text=translation,
                source_lang=data.get("source_lang", "?"),
                target_lang=data.get("target_lang", resolved_target),
            )
        except Exception:
            logger.exception("Translation failed")
            return None


translator_service = TranslatorService()
