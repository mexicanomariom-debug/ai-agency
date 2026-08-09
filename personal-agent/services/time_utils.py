from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

# Friendly names -> IANA timezone
TIMEZONE_ALIASES: dict[str, str] = {
    "playa del carmen": "America/Cancun",
    "playa": "America/Cancun",
    "кармен": "America/Cancun",
    "плайя": "America/Cancun",
    "cancun": "America/Cancun",
    "канкун": "America/Cancun",
    "quintana roo": "America/Cancun",
    "мексика": "America/Cancun",
    "mexico": "America/Cancun",
    "moscow": "Europe/Moscow",
    "москва": "Europe/Moscow",
    "msk": "Europe/Moscow",
}


def resolve_timezone(name: str) -> str | None:
    """Resolve IANA timezone or friendly alias."""
    raw = name.strip()
    if not raw:
        return None

    key = raw.lower().replace("_", " ")
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
