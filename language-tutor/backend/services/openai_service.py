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


openai_service = OpenAIService()
