from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

import dateparser
from openai import AsyncOpenAI

from config import settings

NOTIFY_KEYWORDS_CALL = (r"\bзвонок\b", r"\bзвонком\b", r"\bзвони\b", r"\bпозвони\b", r"\bголосов\w*\b", r"\bcall\b")
NOTIFY_KEYWORDS_MESSAGE = (r"\bсообщен\w*\b", r"\bнапиши\b", r"\bтекстом\b", r"\bmessage\b")
NOTIFY_KEYWORDS_BOTH = (r"сообщением\s+и\s+звонком", r"\bоба\b", r"\bвсё\b", r"\bвсе\b")


@dataclass
class ParsedTask:
    title: str
    due_at: datetime
    notify_message: bool = True
    notify_call: bool = False
    description: str | None = None


@dataclass
class ParseResult:
    tasks: list[ParsedTask]
    reply: str | None = None


class TaskParser:
    def __init__(self) -> None:
        self._openai = AsyncOpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

    async def parse(self, text: str, timezone: str) -> ParseResult:
        if self._openai:
            try:
                result = await self._parse_with_llm(text, timezone)
                if result.tasks:
                    return result
            except Exception:
                pass
        return self._parse_with_rules(text, timezone)

    async def _parse_with_llm(self, text: str, timezone: str) -> ParseResult:
        now = datetime.now(ZoneInfo(timezone))
        system = (
            "Ты парсер задач для личного ассистента. Извлеки из сообщения пользователя задачи "
            "с точным временем напоминания. Ответ — только JSON.\n"
            f"Текущее время пользователя: {now.isoformat()}, часовой пояс: {timezone}.\n"
            "Поля каждой задачи: title (кратко), due_at (ISO 8601 с offset), "
            "notify_message (bool), notify_call (bool).\n"
            "notify_call=true если пользователь просит звонок/голосовое напоминание.\n"
            "notify_message=true по умолчанию. Оба true если просит «сообщение и звонок».\n"
            'Формат: {"tasks": [...], "reply": "краткое подтверждение на русском"}'
        )
        response = await self._openai.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": text},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        raw = response.choices[0].message.content or "{}"
        data = json.loads(raw)
        tasks: list[ParsedTask] = []
        tz = ZoneInfo(timezone)
        for item in data.get("tasks", []):
            due = datetime.fromisoformat(item["due_at"])
            if due.tzinfo is None:
                due = due.replace(tzinfo=tz)
            tasks.append(
                ParsedTask(
                    title=item["title"],
                    due_at=due.astimezone(ZoneInfo("UTC")),
                    notify_message=bool(item.get("notify_message", True)),
                    notify_call=bool(item.get("notify_call", False)),
                )
            )
        return ParseResult(tasks=tasks, reply=data.get("reply"))

    def _parse_with_rules(self, text: str, timezone: str) -> ParseResult:
        notify_message, notify_call = self._detect_notify_flags(text)
        cleaned = self._strip_notify_phrases(text)
        settings_dict = {
            "TIMEZONE": timezone,
            "PREFER_DATES_FROM": "future",
            "RETURN_AS_TIMEZONE_AWARE": True,
        }
        due_at = self._extract_datetime(cleaned, settings_dict)
        if not due_at:
            return ParseResult(tasks=[])

        title = self._extract_title(cleaned, due_at)
        if not title:
            return ParseResult(tasks=[])

        return ParseResult(
            tasks=[
                ParsedTask(
                    title=title,
                    due_at=due_at.astimezone(ZoneInfo("UTC")),
                    notify_message=notify_message,
                    notify_call=notify_call,
                )
            ]
        )

    def _extract_datetime(self, text: str, settings_dict: dict) -> datetime | None:
        patterns = [
            r"через\s+\d+\s*(?:минут(?:у|ы)?|час(?:а|ов)?|дн(?:я|ей)?)",
            r"(?:завтра|послезавтра|сегодня)\s+в\s+\d{1,2}[:.]\d{2}",
            r"в\s+(?:понедельник|вторник|среду|четверг|пятницу|субботу|воскресенье)\s+в\s+\d{1,2}[:.]\d{2}",
            r"(?:завтра|послезавтра|сегодня)",
            r"\d{1,2}[:.]\d{2}",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if not match:
                continue
            due_at = dateparser.parse(match.group(), settings=settings_dict, languages=["ru", "en"])
            if due_at:
                return due_at

        return dateparser.parse(text, settings=settings_dict, languages=["ru", "en"])

    def _detect_notify_flags(self, text: str) -> tuple[bool, bool]:
        lower = text.lower()
        if any(re.search(k, lower) for k in NOTIFY_KEYWORDS_BOTH):
            return True, True
        notify_call = any(re.search(k, lower) for k in NOTIFY_KEYWORDS_CALL)
        notify_message = any(re.search(k, lower) for k in NOTIFY_KEYWORDS_MESSAGE)
        if notify_call and not notify_message:
            return False, True
        if notify_message and not notify_call:
            return True, False
        return True, notify_call

    def _strip_notify_phrases(self, text: str) -> str:
        patterns = [
            r",?\s*(сообщением\s+и\s+звонком|и\s+звонком|сообщением)",
            r",?\s*(напомни\s+сообщением|напомни\s+звонком)",
            r",?\s*звонок",
            r",?\s*сообщение",
        ]
        result = text
        for pattern in patterns:
            result = re.sub(pattern, "", result, flags=re.IGNORECASE)
        return result.strip(" ,—-")

    def _extract_title(self, text: str, due_at: datetime) -> str:
        title = text
        for token in ("напомни", "напомнить", "remind", "через"):
            title = re.sub(rf"\b{token}\b", "", title, flags=re.IGNORECASE)
        title = re.sub(r"\b(завтра|послезавтра|сегодня)\b", "", title, flags=re.IGNORECASE)
        title = re.sub(
            r"\bв\s+(понедельник|вторник|среду|четверг|пятницу|субботу|воскресенье)\b",
            "",
            title,
            flags=re.IGNORECASE,
        )
        title = re.sub(r"\bв\s+\d{1,2}[:.]\d{2}\b", "", title, flags=re.IGNORECASE)
        title = re.sub(r"\b\d{1,2}\s*(минут|минуты|час|часа|часов|дней|дня)\b", "", title, flags=re.IGNORECASE)
        title = re.sub(r"\s+", " ", title).strip(" ,—-:.")
        if len(title) < 3:
            title = text.strip()
        return title[:500]


task_parser = TaskParser()
