from __future__ import annotations

import json
import logging
import re
from enum import Enum

from openai import AsyncOpenAI

from config import settings
from services.task_parser import task_parser

logger = logging.getLogger(__name__)

NOTE_PREFIXES = ("заметка:", "note:", "запиши:", "📝")


class Intent(str, Enum):
    CREATE_TASK = "create_task"
    CREATE_NOTE = "create_note"
    LIST_NOTES = "list_notes"
    LIST_TASKS = "list_tasks"
    GENERAL = "general"


class AssistantService:
    def __init__(self) -> None:
        self._openai = AsyncOpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

    async def classify_intent(self, text: str, timezone: str) -> Intent:
        stripped = text.strip().lower()
        if stripped.startswith(NOTE_PREFIXES) or stripped.startswith("заметка "):
            return Intent.CREATE_NOTE
        if stripped in ("заметки", "мои заметки", "📝 заметки"):
            return Intent.LIST_NOTES
        if stripped in ("сегодня", "задачи на сегодня"):
            return Intent.LIST_TASKS

        parsed = await task_parser.parse(text, timezone)
        if parsed.tasks:
            return Intent.CREATE_TASK

        if self._openai:
            try:
                return await self._classify_with_llm(text)
            except Exception:
                logger.exception("Intent classification failed")

        return Intent.GENERAL

    async def _classify_with_llm(self, text: str) -> Intent:
        response = await self._openai.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Классифицируй сообщение пользователя личного ассистента. "
                        'Ответ JSON: {"intent": "create_task|create_note|list_notes|list_tasks|general"}'
                    ),
                },
                {"role": "user", "content": text},
            ],
            response_format={"type": "json_object"},
            temperature=0,
        )
        data = json.loads(response.choices[0].message.content or "{}")
        return Intent(data.get("intent", "general"))

    async def chat(self, text: str, history: list[dict[str, str]]) -> str:
        if not self._openai:
            return (
                "Я понимаю задачи и заметки. Примеры:\n"
                "• Завтра в 9:00 позвонить маме\n"
                "• Заметка: идея для проекта\n\n"
                "Для свободного диалога добавьте OPENAI_API_KEY."
            )

        messages = [
            {
                "role": "system",
                "content": (
                    "Ты личный ассистент в Telegram. Помогаешь с задачами, напоминаниями и заметками. "
                    "Отвечай кратко на русском. Если пользователь хочет создать задачу — подскажи формат."
                ),
            },
            *history[-10:],
            {"role": "user", "content": text},
        ]
        response = await self._openai.chat.completions.create(
            model=settings.openai_model,
            messages=messages,
            temperature=0.7,
        )
        return (response.choices[0].message.content or "").strip()

    def extract_note_content(self, text: str) -> tuple[str | None, str]:
        for prefix in NOTE_PREFIXES:
            if text.lower().startswith(prefix):
                body = text[len(prefix) :].strip()
                return None, body
        if text.lower().startswith("заметка "):
            body = text[8:].strip()
            return None, body
        return None, text.strip()


assistant_service = AssistantService()
