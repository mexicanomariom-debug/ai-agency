from __future__ import annotations

import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

RECURRENCE_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b(?:каждый\s+день|ежедневно|каждый\s+день)\b", re.I), "daily"),
    (re.compile(r"\b(?:каждую\s+неделю|еженедельно)\b", re.I), "weekly"),
    (re.compile(r"\b(?:по\s+будням|каждый\s+будний\s+день|будни)\b", re.I), "weekdays"),
    (re.compile(r"\b(?:каждый\s+месяц|ежемесячно)\b", re.I), "monthly"),
]

WEEKDAY_MAP = {
    "понедельник": 0,
    "вторник": 1,
    "среду": 2,
    "среда": 2,
    "четверг": 3,
    "пятницу": 4,
    "пятница": 4,
    "субботу": 5,
    "суббота": 5,
    "воскресенье": 6,
    "воскресенье": 6,
}

WEEKDAY_LABELS = (
    "понедельник",
    "вторник",
    "среда",
    "четверг",
    "пятница",
    "суббота",
    "воскресенье",
)

RECURRENCE_LABELS = {
    "daily": "каждый день",
    "weekly": "каждую неделю",
    "weekdays": "по будням",
    "monthly": "каждый месяц",
}


def detect_recurrence(text: str) -> str | None:
    lower = text.lower()
    for weekday_name, idx in WEEKDAY_MAP.items():
        if re.search(rf"\b(?:каждый|каждую|по)\s+{weekday_name}\b", lower):
            return f"weekly:{idx}"
    for pattern, rule in RECURRENCE_PATTERNS:
        if pattern.search(lower):
            return rule
    return None


def strip_recurrence_phrases(text: str) -> str:
    result = text
    for pattern, _ in RECURRENCE_PATTERNS:
        result = pattern.sub("", result)
    result = re.sub(
        r"\b(?:каждый|каждую|по)\s+"
        r"(?:понедельник|вторник|среду|среда|четверг|пятницу|пятница|субботу|суббота|воскресенье)\b",
        "",
        result,
        flags=re.IGNORECASE,
    )
    return re.sub(r"\s+", " ", result).strip(" ,—-")


def recurrence_label(rule: str | None) -> str:
    if not rule:
        return ""
    if rule.startswith("weekly:"):
        try:
            day = int(rule.split(":")[1])
            return f"каждый {WEEKDAY_LABELS[day]}"
        except (IndexError, ValueError):
            pass
    return RECURRENCE_LABELS.get(rule, rule)


def next_occurrence(
    current_due: datetime,
    rule: str,
    timezone: str,
) -> datetime:
    tz = ZoneInfo(timezone)
    local = current_due.astimezone(tz)

    if rule == "daily":
        candidate = local + timedelta(days=1)
    elif rule == "weekdays":
        candidate = local + timedelta(days=1)
        while candidate.weekday() >= 5:
            candidate += timedelta(days=1)
    elif rule == "weekly":
        candidate = local + timedelta(weeks=1)
    elif rule.startswith("weekly:"):
        target_day = int(rule.split(":")[1])
        candidate = local + timedelta(days=1)
        while candidate.weekday() != target_day:
            candidate += timedelta(days=1)
    elif rule == "monthly":
        month = local.month + 1
        year = local.year
        if month > 12:
            month = 1
            year += 1
        try:
            candidate = local.replace(year=year, month=month)
        except ValueError:
            candidate = local.replace(year=year, month=month, day=28) + timedelta(days=4)
            candidate = candidate.replace(day=1) - timedelta(days=1)
            candidate = candidate.replace(
                hour=local.hour,
                minute=local.minute,
                second=local.second,
                microsecond=local.microsecond,
            )
    else:
        candidate = local + timedelta(days=1)

    return candidate.astimezone(ZoneInfo("UTC"))
