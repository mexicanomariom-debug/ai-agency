from collections.abc import AsyncIterator

from openai import AsyncOpenAI

from config import settings

_DEMO_REPLY = (
    "Привет! Сейчас бот работает в демо-режиме — OpenAI API ключ не настроен на сервере. "
    "Настройте OPENAI_API_KEY в /opt/opus5/.env и перезапустите контейнеры."
)


class OpenAIService:
    def __init__(self) -> None:
        self.client = AsyncOpenAI(api_key=settings.openai_api_key or "sk-placeholder")
        self.model = settings.openai_model

    def has_api_key(self) -> bool:
        return bool(settings.openai_api_key)

    def _demo_enabled(self) -> bool:
        return settings.demo_mode and not settings.openai_api_key

    async def create_embedding(self, text: str) -> list[float] | None:
        if not settings.openai_api_key:
            return None
        response = await self.client.embeddings.create(
            model="text-embedding-3-small",
            input=text,
        )
        return response.data[0].embedding

    async def transcribe_voice(
        self,
        audio_bytes: bytes,
        mime_type: str = "audio/ogg",
        *,
        language: str | None = None,
        prompt: str | None = None,
    ) -> str:
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is required for voice transcription")

        ext = "ogg"
        if "mpeg" in mime_type or "mp3" in mime_type:
            ext = "mp3"
        elif "wav" in mime_type:
            ext = "wav"
        elif "mp4" in mime_type or "m4a" in mime_type:
            ext = "m4a"

        # Bilingual learners mix Russian with the target language. A spelling
        # prompt reduces Whisper errors like "iiamo" for Spanish "llamo".
        # Do not force `language=` — auto-detect handles code-switching better.
        kwargs: dict = {
            "model": "whisper-1",
            "file": (f"voice.{ext}", audio_bytes, mime_type),
        }
        if prompt:
            kwargs["prompt"] = prompt
        if language:
            kwargs["language"] = language

        response = await self.client.audio.transcriptions.create(**kwargs)
        return response.text

    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
    ) -> str:
        if self._demo_enabled():
            user_text = messages[-1]["content"] if messages else ""
            return f"{_DEMO_REPLY}\n\n(Вы написали: {user_text[:200]})"

        full_messages: list[dict[str, str]] = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=full_messages,
            temperature=0.7,
        )
        return response.choices[0].message.content or ""

    async def stream_chat_completion(
        self,
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
    ) -> AsyncIterator[str]:
        if self._demo_enabled():
            yield _DEMO_REPLY
            return

        full_messages: list[dict[str, str]] = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)

        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=full_messages,
            temperature=0.7,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    async def synthesize_speech(
        self,
        text: str,
        voice: str | None = None,
        response_format: str = "mp3",
    ) -> bytes | None:
        """Synthesize speech. Use response_format="opus" for Telegram voice notes."""
        if not settings.openai_api_key:
            return None
        response = await self.client.audio.speech.create(
            model=settings.openai_tts_model,
            voice=voice or settings.openai_tts_voice,
            input=text[:4096],
            response_format=response_format,
        )
        return response.content


openai_service = OpenAIService()
