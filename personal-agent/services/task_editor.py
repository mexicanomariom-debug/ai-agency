from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from zoneinfo import ZoneInfo

import dateparser
from openai import AsyncOpenAI

from config import settings
from services.task_parser import TaskParser, task_parser

EDIT_VERB_PATTERN = re.compile(
    r"\b(?:"
    r"измени(?:ть)?|редактир\w*|перенес\w*|перенести|сдвин\w*|"
    r"отлож\w*|переимену\w*|поменя\w*|обнови\w*|edit"
    r")\b",
    re.IGNORECASE,
)

TASK_ID_PATTERNS = (
    re.compile(r"(?:задач[ауеи]|task)\s*#?(\d+)", re.IGNORECASE),
    re.compile(r"#(\d+)\b"),
    re.compile(r"\b(\d+)\s*(?:—|-|на\s+в|:\s*)", re.IGNORECASE),
)

TIME_ONLY_PREFIX = re.compile(
    r"^(?:только\s+)?(?:новое\s+)?(?:время|дата|когда)\s*[—\-:]\s*",
    re.IGNORECASE,
)
TITLE_ONLY_PREFIX = re.compile(
    r"^(?:только\s+)?(?:новое\s+)?(?:название|текст|имя)\s*[—\-:]\s*",
    re.IGNORECASE,
)


@dataclass
class TaskEditChanges:
    title: str | None = None
    due_at: datetime | None = None
    notify_message: bool | None = None
    notify_call: bool | None = None
    notify_phone: bool | None = None


@dataclass
class TaskEditParseResult:
    task_id: int | None = None
    changes: TaskEditChanges = field(default_factory=TaskEditChanges)
    reply: str | None = None


class TaskEditor:
    def __init__(self) -> None:
        self._openai = AsyncOpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None
        self._parser = task_parser

    def is_edit_intent(self, text: str) -> bool:
        stripped = text.strip()
        if stripped.lower().startswith("/edit"):
            return True
        return bool(EDIT_VERB_PATTERN.search(stripped))

    def extract_task_id(self, text: str) -> int | None:
        for pattern in TASK_ID_PATTERNS:
            match = pattern.search(text)
            if match:
                return int(match.group(1))
        parts = text.strip().split()
        if parts and parts[0].startswith("/edit"):
            if len(parts) >= 2 and parts[1].isdigit():
                return int(parts[1])
        return None

    def _strip_edit_phrases(self, text: str, task_id: int | None) -> str:
        result = text.strip()
        if result.lower().startswith("/edit"):
            parts = result.split(maxsplit=2)
            if len(parts) >= 3:
                result = parts[2]
            else:
                return ""
        result = EDIT_VERB_PATTERN.sub("", result, count=1)
        if task_id is not None:
            for pattern in TASK_ID_PATTERNS:
                result = pattern.sub("", result, count=1)
            result = re.sub(rf"\b{task_id}\b", "", result, count=1)
        result = re.sub(r"^(?:задач[ауеи]|task)\s*", "", result, flags=re.IGNORECASE)
        return re.sub(r"\s+", " ", result).strip(" —-:.")

    async def parse_edit_request(
        self,
        text: str,
        timezone: str,
        *,
        task_id: int | None = None,
    ) -> TaskEditParseResult | None:
        if not self.is_edit_intent(text) and task_id is None:
            return None

        resolved_id = task_id or self.extract_task_id(text)
        body = self._strip_edit_phrases(text, resolved_id)
        if not body and resolved_id is None:
            return TaskEditParseResult(task_id=None, changes=TaskEditChanges())

        time_only = bool(TIME_ONLY_PREFIX.match(body))
        title_only = bool(TITLE_ONLY_PREFIX.match(body))
        if time_only:
            body = TIME_ONLY_PREFIX.sub("", body).strip()
        elif title_only:
            body = TITLE_ONLY_PREFIX.sub("", body).strip()

        changes = await self._parse_changes(body, timezone, time_only=time_only, title_only=title_only)
        if not changes.title and not changes.due_at and not any(
            v is not None
            for v in (
                changes.notify_message,
                changes.notify_call,
                changes.notify_phone,
            )
        ):
            if resolved_id is None and not self.is_edit_intent(text):
                return None
            return TaskEditParseResult(task_id=resolved_id, changes=changes)

        return TaskEditParseResult(task_id=resolved_id, changes=changes)

    async def _parse_changes(
        self,
        body: str,
        timezone: str,
        *,
        time_only: bool = False,
        title_only: bool = False,
    ) -> TaskEditChanges:
        if not body:
            return TaskEditChanges()

        if title_only:
            return TaskEditChanges(title=body[:500])

        parsed = await self._parser.parse(body, timezone)
        if parsed.tasks:
            item = parsed.tasks[0]
            if time_only:
                return TaskEditChanges(due_at=item.due_at)
            title = item.title if self._looks_like_real_title(item.title, body) else None
            return TaskEditChanges(
                title=title,
                due_at=item.due_at,
                notify_message=item.notify_message,
                notify_call=item.notify_call,
                notify_phone=item.notify_phone,
            )

        if time_only or not title_only:
            due_at = self._parse_time_only(body, timezone)
            if due_at:
                return TaskEditChanges(due_at=due_at)

        if self._openai and not time_only:
            try:
                return await self._parse_with_llm(body, timezone, title_only=title_only)
            except Exception:
                pass

        if not time_only:
            return TaskEditChanges(title=body[:500])
        return TaskEditChanges()

    def _looks_like_real_title(self, title: str, original: str) -> bool:
        if len(title) < 3:
            return False
        lower = original.lower()
        if title.lower() in lower:
            return True
        time_tokens = ("завтра", "сегодня", "через", "в ", ":")
        if any(token in title.lower() for token in time_tokens) and len(title) < 12:
            return False
        return True

    def _parse_time_only(self, text: str, timezone: str) -> datetime | None:
        settings_dict = {
            "TIMEZONE": timezone,
            "PREFER_DATES_FROM": "future",
            "RETURN_AS_TIMEZONE_AWARE": True,
        }
        due_at = dateparser.parse(text, settings=settings_dict, languages=["ru", "en"])
        if due_at:
            return due_at.astimezone(ZoneInfo("UTC"))
        return None

    async def _parse_with_llm(
        self,
        text: str,
        timezone: str,
        *,
        title_only: bool = False,
    ) -> TaskEditChanges:
        now = datetime.now(ZoneInfo(timezone))
        system = (
            "Ты парсер правок задачи. Извлеки только изменения из текста пользователя. "
            "Ответ — только JSON.\n"
            f"Сейчас у пользователя: {now.isoformat()}, пояс {timezone}.\n"
            "Поля (только если явно указаны): title, due_at (ISO 8601 с offset), "
            "notify_message, notify_call, notify_phone (bool).\n"
            "Если указано только время — title не включай. Если только название — due_at не включай."
        )
        if title_only:
            system += "\nПользователь меняет только название задачи."
        response = await self._openai.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": text},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        data = json.loads(response.choices[0].message.content or "{}")
        changes = TaskEditChanges()
        if data.get("title"):
            changes.title = str(data["title"])[:500]
        if data.get("due_at"):
            due = datetime.fromisoformat(data["due_at"])
            if due.tzinfo is None:
                due = due.replace(tzinfo=ZoneInfo(timezone))
            changes.due_at = due.astimezone(ZoneInfo("UTC"))
        for flag in ("notify_message", "notify_call", "notify_phone"):
            if flag in data:
                setattr(changes, flag, bool(data[flag]))
        return changes


task_editor = TaskEditor()
