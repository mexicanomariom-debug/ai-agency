from __future__ import annotations

import logging
import tempfile
from pathlib import Path

from aiogram import Bot
from openai import AsyncOpenAI

from config import settings

logger = logging.getLogger(__name__)


class SpeechToText:
    def __init__(self) -> None:
        self._client = AsyncOpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

    @property
    def available(self) -> bool:
        return self._client is not None

    async def transcribe_telegram_voice(
        self,
        bot: Bot,
        file_id: str,
        *,
        language: str | None = None,
    ) -> str | None:
        if not self._client:
            return None

        file = await bot.get_file(file_id)
        suffix = Path(file.file_path or "voice.ogg").suffix or ".ogg"
        tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        tmp_path = Path(tmp.name)
        tmp.close()

        try:
            await bot.download_file(file.file_path, tmp_path)
            with tmp_path.open("rb") as audio_file:
                kwargs: dict = {
                    "model": settings.openai_whisper_model,
                    "file": audio_file,
                }
                if language:
                    kwargs["language"] = language
                response = await self._client.audio.transcriptions.create(**kwargs)
            text = (response.text or "").strip()
            return text or None
        except Exception:
            logger.exception("Voice transcription failed")
            return None
        finally:
            tmp_path.unlink(missing_ok=True)


stt_service = SpeechToText()
