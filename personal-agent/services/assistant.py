from __future__ import annotations

import json
import logging
import re
from enum import Enum

from services.llm_service import llm_service

logger = logging.getLogger(__name__)

NOTE_PREFIXES = ("заметка:", "note:", "запиши:", "📝")

_ASSISTANT_SYSTEM = (
    "Ты личный ассистент в Telegram. Помогаешь с задачами, напоминаниями и заметками. "
    "Отвечай кратко на русском. Не говори, что задача создана, если пользователь "
    "не указал время — подскажи формат: «Завтра в 9:00 напомни …»."
)

_INTENT_SYSTEM = (
    "Классифицируй сообщение пользователя личного ассистента. "
    'Ответ JSON: {"intent": "create_task|create_note|list_notes|list_tasks_today|list_tasks|general"}'
)


class Intent(str, Enum):
    CREATE_TASK = "create_task"
    CREATE_NOTE = "create_note"
    LIST_NOTES = "list_notes"
    LIST_TASKS_TODAY = "list_tasks_today"
    LIST_TASKS = "list_tasks"
    GENERAL = "general"


class AssistantService:
    async def classify_intent(self, text: str, timezone: str) -> Intent:
        stripped = text.strip().lower()
        if stripped.startswith(NOTE_PREFIXES) or stripped.startswith("заметка "):
            return Intent.CREATE_NOTE
        if stripped in ("заметки", "мои заметки", "📝 заметки", "блокнот", "💡 блокнот-идеи"):
            return Intent.LIST_NOTES
        if stripped in ("сегодня", "задачи на сегодня", "📆 сегодня"):
            return Intent.LIST_TASKS_TODAY
        if stripped in (
            "мои задачи",
            "список задач",
            "все задачи",
            "задачи",
            "tasks",
            "📋 мои задачи",
        ):
            return Intent.LIST_TASKS

        if llm_service.has_provider():
            try:
                return await self._classify_with_llm(text)
            except Exception:
                logger.exception("Intent classification failed")

        return Intent.GENERAL

    async def _classify_with_llm(self, text: str) -> Intent:
        raw_json = await llm_service.json_completion(
            [{"role": "user", "content": text}],
            system_prompt=_INTENT_SYSTEM,
        )
        data = json.loads(raw_json or "{}")
        raw = data.get("intent", "general")
        if raw == "list_tasks" and "сегодня" in text.lower():
            return Intent.LIST_TASKS_TODAY
        return Intent(raw if raw in Intent._value2member_map_ else "general")

    async def chat(self, text: str, history: list[dict[str, str]]) -> str:
        messages = [*history[-10:], {"role": "user", "content": text}]
        return await llm_service.chat_completion(
            messages,
            system_prompt=_ASSISTANT_SYSTEM,
            temperature=0.7,
        )

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
