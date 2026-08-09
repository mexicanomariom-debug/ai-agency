from __future__ import annotations

import logging
import re
from urllib.parse import parse_qs, urlparse

from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from services.calendar_sync import sync_pending_tasks_to_calendar
from services.google_calendar import google_calendar_service

logger = logging.getLogger(__name__)

GOOGLE_CODE_RE = re.compile(r"(?:^|code=)(4/[\w\-./]+)")
GOOGLE_CODE_CMD_RE = re.compile(r"^/google_code(?:@\w+)?\s+(.+)$", re.IGNORECASE | re.DOTALL)


def extract_google_auth_code(text: str) -> str | None:
    text = text.strip()
    cmd = GOOGLE_CODE_CMD_RE.match(text)
    if cmd:
        return cmd.group(1).strip()

    if "code=" in text:
        parsed = urlparse(text)
        query = parse_qs(parsed.query)
        if query.get("code"):
            return query["code"][0]

    match = GOOGLE_CODE_RE.search(text)
    if match:
        return match.group(1)
    return None


async def connect_google_calendar(session: AsyncSession, user: User, code: str) -> tuple[bool, str]:
    refresh_token = await google_calendar_service.exchange_code(code)
    if not refresh_token:
        return False, (
            "Не удалось подключить Google Calendar.\n"
            "Код устарел или уже использован — начните заново: /calendar"
        )

    user.google_refresh_token = refresh_token
    user.google_calendar_enabled = True
    await session.flush()

    try:
        synced, failed = await sync_pending_tasks_to_calendar(session, user)
    except Exception:
        logger.exception("Post-connect sync failed for user %s", user.telegram_id)
        synced, failed = 0, 0

    msg = (
        "✅ Google Calendar подключён!\n\n"
        "Новые задачи будут попадать в календарь автоматически.\n"
        "Выполненные и отменённые — удаляются из календаря."
    )
    if synced:
        msg += f"\n\n📅 В календарь добавлено активных задач: {synced}"
    if failed:
        msg += f"\n⚠️ Не удалось синхронизировать: {failed}"
    if not synced and not failed:
        msg += "\n\nЕсли есть старые задачи — выполните /calendar_sync"
    return True, msg
