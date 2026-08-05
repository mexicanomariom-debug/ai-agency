from collections.abc import AsyncIterator

from anthropic import AsyncAnthropic
from openai import AsyncOpenAI

from config import settings

_DEMO_REPLY = (
    "Привет! Я ваш AI-учитель. Сейчас на сервере не настроен API ключ — "
    "добавьте ANTHROPIC_API_KEY или OPENAI_API_KEY."
)


class LLMService:
    def __init__(self) -> None:
        self._anthropic = (
            AsyncAnthropic(api_key=settings.anthropic_api_key) if settings.anthropic_api_key else None
        )
        self._openai = AsyncOpenAI(api_key=settings.openai_api_key or "sk-placeholder")

    def has_provider(self) -> bool:
        return bool(settings.anthropic_api_key or settings.openai_api_key)

    def _demo_enabled(self) -> bool:
        return settings.demo_mode and not self.has_provider()

    def _provider(self) -> str:
        if settings.anthropic_api_key:
            return "anthropic"
        return "openai"

    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
    ) -> str:
        if self._demo_enabled():
            user_text = messages[-1]["content"] if messages else ""
            return f"{_DEMO_REPLY}\n\n(Вы: {user_text[:200]})"

        if self._provider() == "anthropic":
            response = await self._anthropic.messages.create(
                model=settings.anthropic_model,
                max_tokens=1024,
                system=system_prompt or "",
                messages=[{"role": m["role"], "content": m["content"]} for m in messages if m["role"] != "system"],
            )
            return response.content[0].text

        full_messages: list[dict[str, str]] = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)

        response = await self._openai.chat.completions.create(
            model=settings.openai_model,
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

        if self._provider() == "anthropic":
            async with self._anthropic.messages.stream(
                model=settings.anthropic_model,
                max_tokens=1024,
                system=system_prompt or "",
                messages=[{"role": m["role"], "content": m["content"]} for m in messages if m["role"] != "system"],
            ) as stream:
                async for text in stream.text_stream:
                    yield text
            return

        full_messages: list[dict[str, str]] = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)

        stream = await self._openai.chat.completions.create(
            model=settings.openai_model,
            messages=full_messages,
            temperature=0.7,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta


llm_service = LLMService()
