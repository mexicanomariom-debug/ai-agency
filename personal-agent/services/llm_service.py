"""Unified LLM access: Anthropic with OpenAI fallback."""

from __future__ import annotations

import logging

from anthropic import AsyncAnthropic
from openai import AsyncOpenAI

from config import settings

logger = logging.getLogger(__name__)

_NO_KEY_REPLY = (
    "Я понимаю задачи и заметки. Примеры:\n"
    "• Завтра в 9:00 позвонить маме\n"
    "• Заметка: идея для проекта\n\n"
    "Для свободного диалога добавьте OPENAI_API_KEY или ANTHROPIC_API_KEY."
)


class LLMService:
    def __init__(self) -> None:
        self._anthropic = (
            AsyncAnthropic(api_key=settings.anthropic_api_key) if settings.anthropic_api_key else None
        )
        self._openai = AsyncOpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

    def has_provider(self) -> bool:
        return bool(self._anthropic or self._openai)

    def _prefer_anthropic(self) -> bool:
        return self._anthropic is not None

    @staticmethod
    def _extract_anthropic_text(response: object) -> str:
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
            raise RuntimeError("Empty Anthropic response")
        return joined

    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        *,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1536,
    ) -> str:
        if not self.has_provider():
            user_text = messages[-1]["content"] if messages else ""
            return f"{_NO_KEY_REPLY}\n\n(Вы: {user_text[:200]})"

        if self._prefer_anthropic():
            return await self._anthropic_chat(
                messages,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        return await self._openai_chat(
            messages,
            system_prompt=system_prompt,
            temperature=temperature,
        )

    async def json_completion(
        self,
        messages: list[dict[str, str]],
        *,
        system_prompt: str,
        temperature: float = 0,
    ) -> str:
        """Structured JSON — OpenAI first (native JSON mode), else Anthropic."""
        if self._openai:
            full: list[dict[str, str]] = [{"role": "system", "content": system_prompt}, *messages]
            response = await self._openai.chat.completions.create(
                model=settings.openai_model,
                messages=full,
                response_format={"type": "json_object"},
                temperature=temperature,
            )
            return response.choices[0].message.content or "{}"

        if self._anthropic:
            prompt = system_prompt + "\n\nОтветь только валидным JSON, без markdown."
            text = await self._anthropic_chat(
                messages,
                system_prompt=prompt,
                temperature=temperature,
                max_tokens=512,
            )
            return text.strip()

        return "{}"

    async def _openai_chat(
        self,
        messages: list[dict[str, str]],
        *,
        system_prompt: str | None,
        temperature: float,
    ) -> str:
        if not self._openai:
            raise RuntimeError("OpenAI client not configured")
        full: list[dict[str, str]] = []
        if system_prompt:
            full.append({"role": "system", "content": system_prompt})
        full.extend(messages)
        response = await self._openai.chat.completions.create(
            model=settings.openai_model,
            messages=full,
            temperature=temperature,
        )
        return (response.choices[0].message.content or "").strip()

    async def _anthropic_chat(
        self,
        messages: list[dict[str, str]],
        *,
        system_prompt: str | None,
        temperature: float,
        max_tokens: int,
    ) -> str:
        if not self._anthropic:
            raise RuntimeError("Anthropic client not configured")

        models = [
            settings.anthropic_model,
            "claude-sonnet-4-5-20250929",
            "claude-sonnet-4-6",
        ]
        seen: set[str] = set()
        last_exc: Exception | None = None
        for model in models:
            if not model or model in seen:
                continue
            seen.add(model)
            try:
                kwargs: dict = {
                    "model": model,
                    "max_tokens": max_tokens,
                    "system": system_prompt or "",
                    "messages": [
                        {"role": m["role"], "content": m["content"]}
                        for m in messages
                        if m["role"] != "system"
                    ],
                }
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
                logger.warning("Anthropic model %s failed: %s", model, exc)
                continue

        if self._openai:
            logger.warning("Anthropic failed, falling back to OpenAI")
            return await self._openai_chat(
                messages,
                system_prompt=system_prompt,
                temperature=temperature,
            )
        raise last_exc or RuntimeError("Anthropic chat failed")


llm_service = LLMService()
