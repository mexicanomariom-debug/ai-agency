from __future__ import annotations

import logging
import tempfile
from pathlib import Path

from aiogram import Bot

from services.openai_speech import openai_speech_service
from services.whisper_prompt import whisper_prompt_for

logger = logging.getLogger(__name__)


class SpeechToText:
    @property
    def available(self) -> bool:
        return openai_speech_service.available

    async def transcribe_telegram_voice(
        self,
        bot: Bot,
        file_id: str,
        *,
        language: str | None = None,
        target_lang: str | None = None,
        in_translator: bool = False,
    ) -> str | None:
        if not openai_speech_service.available:
            return None

        file = await bot.get_file(file_id)
        suffix = Path(file.file_path or "voice.ogg").suffix or ".ogg"
        tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        tmp_path = Path(tmp.name)
        tmp.close()

        try:
            await bot.download_file(file.file_path, tmp_path)
            audio_bytes = tmp_path.read_bytes()
            mime = "audio/ogg" if suffix in {".ogg", ".oga"} else "application/octet-stream"
            prompt = whisper_prompt_for(target_lang=target_lang, in_translator=in_translator)
            return await openai_speech_service.transcribe_bytes(
                audio_bytes,
                mime,
                language=language,
                prompt=prompt,
            )
        except Exception:
            logger.exception("Voice transcription failed")
            return None
        finally:
            tmp_path.unlink(missing_ok=True)


stt_service = SpeechToText()
