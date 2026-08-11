"""OpenAI Whisper transcription and TTS (voice replies)."""

from __future__ import annotations

import logging

from openai import AsyncOpenAI

from config import settings

logger = logging.getLogger(__name__)


class OpenAISpeechService:
    def __init__(self) -> None:
        self._client = AsyncOpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

    @property
    def available(self) -> bool:
        return self._client is not None

    async def transcribe_bytes(
        self,
        audio_bytes: bytes,
        mime_type: str = "audio/ogg",
        *,
        language: str | None = None,
        prompt: str | None = None,
    ) -> str | None:
        if not self._client:
            return None

        ext = "ogg"
        if "mpeg" in mime_type or "mp3" in mime_type:
            ext = "mp3"
        elif "wav" in mime_type:
            ext = "wav"
        elif "mp4" in mime_type or "m4a" in mime_type:
            ext = "m4a"

        kwargs: dict = {
            "model": settings.openai_whisper_model,
            "file": (f"voice.{ext}", audio_bytes, mime_type),
        }
        if prompt:
            kwargs["prompt"] = prompt
        if language:
            kwargs["language"] = language

        try:
            response = await self._client.audio.transcriptions.create(**kwargs)
            text = (response.text or "").strip()
            return text or None
        except Exception:
            logger.exception("Whisper transcription failed")
            return None

    async def synthesize_speech(
        self,
        text: str,
        *,
        voice: str | None = None,
        response_format: str = "opus",
    ) -> bytes | None:
        if not self._client:
            return None
        try:
            response = await self._client.audio.speech.create(
                model=settings.openai_tts_model,
                voice=voice or settings.openai_tts_voice,
                input=text[:4096],
                response_format=response_format,
            )
            return response.content
        except Exception:
            logger.exception("OpenAI TTS failed")
            return None


openai_speech_service = OpenAISpeechService()
