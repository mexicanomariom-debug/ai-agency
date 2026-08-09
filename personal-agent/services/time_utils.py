from __future__ import annotations

import re
import unicodedata
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

INVISIBLE_CHARS_RE = re.compile(r"[\u200b-\u200d\ufeff]")

TIMEZONE_TEXT = re.compile(
    r"(?i)^/?(?:timezone|таймзон|тайм\s*зон|часовой\s+пояс|пояс)(?:@\w+)?\s+(.+)$"
)
CMD_TIMEZONE_RE = re.compile(r"(?i)^/timezone(?:@\w+)?\s+(.+)$")

# Friendly names -> IANA timezone (per-user; each user sets their own)
TIMEZONE_ALIASES: dict[str, str] = {
    # Mexico / Caribbean
    "playa del carmen": "America/Cancun",
    "playa": "America/Cancun",
    "кармен": "America/Cancun",
    "плайя": "America/Cancun",
    "плая": "America/Cancun",
    "cancun": "America/Cancun",
    "канкун": "America/Cancun",
    "quintana roo": "America/Cancun",
    "мексика": "America/Mexico_City",
    "mexico": "America/Mexico_City",
    "mexico city": "America/Mexico_City",
    "ciudad de mexico": "America/Mexico_City",
    # Russia / CIS
    "moscow": "Europe/Moscow",
    "москва": "Europe/Moscow",
    "msk": "Europe/Moscow",
    "spb": "Europe/Moscow",
    "petersburg": "Europe/Moscow",
    "питер": "Europe/Moscow",
    "санкт-петербург": "Europe/Moscow",
    "kiev": "Europe/Kyiv",
    "kyiv": "Europe/Kyiv",
    "киев": "Europe/Kyiv",
    "minsk": "Europe/Minsk",
    "минск": "Europe/Minsk",
    "almaty": "Asia/Almaty",
    "алматы": "Asia/Almaty",
    "tashkent": "Asia/Tashkent",
    "ташкент": "Asia/Tashkent",
    # Europe
    "london": "Europe/London",
    "лондон": "Europe/London",
    "paris": "Europe/Paris",
    "париж": "Europe/Paris",
    "berlin": "Europe/Berlin",
    "берлин": "Europe/Berlin",
    "madrid": "Europe/Madrid",
    "мадрид": "Europe/Madrid",
    "rome": "Europe/Rome",
    "рим": "Europe/Rome",
    "istanbul": "Europe/Istanbul",
    "стамбул": "Europe/Istanbul",
    # Americas
    "new york": "America/New_York",
    "nyc": "America/New_York",
    "ny": "America/New_York",
    "нью-йорк": "America/New_York",
    "los angeles": "America/Los_Angeles",
    "la": "America/Los_Angeles",
    "miami": "America/New_York",
    "chicago": "America/Chicago",
    "toronto": "America/Toronto",
    "торонто": "America/Toronto",
    "vancouver": "America/Vancouver",
    "sao paulo": "America/Sao_Paulo",
    "buenos aires": "America/Argentina/Buenos_Aires",
    # Asia / Pacific
    "dubai": "Asia/Dubai",
    "дубай": "Asia/Dubai",
    "tokyo": "Asia/Tokyo",
    "токио": "Asia/Tokyo",
    "singapore": "Asia/Singapore",
    "сингапур": "Asia/Singapore",
    "hong kong": "Asia/Hong_Kong",
    "seoul": "Asia/Seoul",
    "сеул": "Asia/Seoul",
    "beijing": "Asia/Shanghai",
    "shanghai": "Asia/Shanghai",
    "пекин": "Asia/Shanghai",
    "bangkok": "Asia/Bangkok",
    "бангкок": "Asia/Bangkok",
    "sydney": "Australia/Sydney",
    "сидней": "Australia/Sydney",
    "melbourne": "Australia/Melbourne",
    # UTC
    "utc": "UTC",
    "gmt": "UTC",
}


def normalize_timezone_text(text: str) -> str:
    text = INVISIBLE_CHARS_RE.sub("", text)
    text = unicodedata.normalize("NFKC", text)
    return " ".join(text.strip().split())


def extract_timezone_argument(text: str) -> str | None:
    cleaned = normalize_timezone_text(text)
    if not cleaned:
        return None
    for pattern in (TIMEZONE_TEXT, CMD_TIMEZONE_RE):
        match = pattern.match(cleaned)
        if match:
            return match.group(1).strip()
    return None


def is_standalone_timezone_alias(text: str) -> bool:
    cleaned = normalize_timezone_text(text)
    if not cleaned or cleaned.startswith("/"):
        return False
    if len(cleaned) > 40:
        return False
    key = cleaned.lower()
    if key in TIMEZONE_ALIASES:
        return True
    return "/" in cleaned and resolve_timezone(cleaned) is not None


def resolve_timezone(name: str) -> str | None:
    """Resolve IANA timezone or friendly alias."""
    raw = normalize_timezone_text(name)
    if not raw:
        return None

    key = raw.lower().replace("_", " ")

    for prefix in (
        "/timezone ",
        "/timezone@",
        "timezone ",
        "таймзон ",
        "тайм зон ",
        "часовой пояс ",
        "пояс ",
    ):
        if key.startswith(prefix):
            tail = key[len(prefix) :]
            if prefix == "/timezone@" and " " in tail:
                tail = tail.split(" ", 1)[1]
            return resolve_timezone(tail)

    if key in TIMEZONE_ALIASES:
        return TIMEZONE_ALIASES[key]

    try:
        ZoneInfo(raw)
        return raw
    except ZoneInfoNotFoundError:
        pass

    for alias, tz in TIMEZONE_ALIASES.items():
        if key in alias or alias in key:
            return tz

    if " " in key:
        for part in reversed(key.split()):
            resolved = resolve_timezone(part)
            if resolved:
                return resolved

    return None


def ensure_utc(dt: datetime) -> datetime:
    """SQLite may return naive datetimes — treat them as UTC."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=ZoneInfo("UTC"))
    return dt.astimezone(ZoneInfo("UTC"))


def to_user_local(dt: datetime, timezone: str) -> datetime:
    return ensure_utc(dt).astimezone(ZoneInfo(timezone))


def format_google_datetime(dt: datetime, timezone: str) -> str:
    """Wall-clock time for Google Calendar API (no offset in dateTime)."""
    local = to_user_local(dt, timezone)
    return local.replace(tzinfo=None).strftime("%Y-%m-%dT%H:%M:%S")


def format_user_datetime(dt: datetime, timezone: str) -> str:
    local = to_user_local(dt, timezone)
    tz_label = local.tzname() or timezone
    return f"{local.strftime('%d.%m.%Y %H:%M')} ({tz_label})"
