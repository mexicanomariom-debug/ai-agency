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

    @staticmethod
    def _extract_anthropic_text(response: object) -> str:
        """Claude 5+ may return thinking/tool blocks before text."""
        parts: list[str] = []
        for block in getattr(response, "content", None) or []:
            btype = getattr(block, "type", None)
            text = getattr(block, "text", None)
            if btype == "text" and text:
                parts.append(str(text))
            elif text and btype not in {"thinking", "redacted_thinking", "tool_use"}:
                parts.append(str(text))
        joined = "\n".join(parts).strip()
        if not joined:
            types = [getattr(b, "type", type(b).__name__) for b in (getattr(response, "content", None) or [])]
            raise RuntimeError(f"Empty Anthropic text (blocks={types})")
        return joined

    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
    ) -> str:
        if self._demo_enabled():
            user_text = messages[-1]["content"] if messages else ""
            return f"{_DEMO_REPLY}\n\n(Вы: {user_text[:200]})"

        if self._provider() == "anthropic":
            models = [
                settings.anthropic_model,
                "claude-sonnet-5",
                "claude-sonnet-4-5-20250929",
                "claude-sonnet-4-6",
            ]
            seen: set[str] = set()
            last_exc: Exception | None = None
            for model in models:
                if model in seen:
                    continue
                seen.add(model)
                try:
                    kwargs: dict = {
                        "model": model,
                        "max_tokens": 1536,
                        "system": system_prompt or "",
                        "messages": [
                            {"role": m["role"], "content": m["content"]}
                            for m in messages
                            if m["role"] != "system"
                        ],
                    }
                    # Prefer plain text replies for voice (disable adaptive thinking if supported)
                    try:
                        response = await self._anthropic.messages.create(
                            **kwargs,
                            thinking={"type": "disabled"},
                        )
                    except Exception:
                        response = await self._anthropic.messages.create(**kwargs)
                    return self._extract_anthropic_text(response)
                except Exception as exc:
                    last_exc = exc
                    continue
            raise last_exc or RuntimeError("Anthropic chat failed")

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
            models = [
                settings.anthropic_model,
                "claude-sonnet-5",
                "claude-sonnet-4-5-20250929",
                "claude-sonnet-4-6",
            ]
            seen: set[str] = set()
            last_exc: Exception | None = None
            for model in models:
                if model in seen:
                    continue
                seen.add(model)
                try:
                    async with self._anthropic.messages.stream(
                        model=model,
                        max_tokens=1536,
                        system=system_prompt or "",
                        messages=[
                            {"role": m["role"], "content": m["content"]}
                            for m in messages
                            if m["role"] != "system"
                        ],
                    ) as stream:
                        async for text in stream.text_stream:
                            yield text
                    return
                except Exception as exc:
                    last_exc = exc
                    continue
            if last_exc:
                raise last_exc
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
