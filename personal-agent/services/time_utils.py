from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo


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
