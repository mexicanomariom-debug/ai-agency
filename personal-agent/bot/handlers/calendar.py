import asyncio
import logging
import re

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.copy import (
    CALENDAR_DISABLED,
    CALENDAR_ENABLED,
    CALENDAR_NOT_CONFIGURED,
    CALENDAR_NOT_CONNECTED,
    CALENDAR_STATUS,
)
from config import settings
from bot.utils.messages import answer_menu
from services.calendar_sync import (
    SYNC_OVERALL_TIMEOUT_SEC,
    count_calendar_sync_state,
    sync_user_calendar_by_telegram_id,
)
from services.google_oauth import connect_google_calendar, extract_google_auth_code
from services.google_calendar import google_calendar_service
from services.user_service import user_service

logger = logging.getLogger(__name__)

router = Router()

CALENDAR_SYNC_TEXT = re.compile(
    r"(?i)^(?:/)?calendar[\s_-]*sync$|^синхрониз(?:ировать|ация)\s+(?:с\s+)?(?:google\s+)?календар",
)
CALENDAR_RESYNC_TEXT = re.compile(
    r"(?i)^(?:/)?calendar[\s_-]*resync$|^пересинхрониз",
)


def _format_sync_idle_message(total: int, linked: int, unlinked: int) -> str:
    if total == 0:
        return (
            "Активных задач нет.\n\n"
            "Создайте задачу текстом или голосом — после подключения календаря она попадёт в Google Calendar.\n"
            "Архив: /tasks_done"
        )
    if unlinked == 0:
        return (
            f"Активных задач: {total}. Все {linked} уже привязаны к Google Calendar.\n\n"
            "Если в календаре их не видно — попробуйте /calendar_resync\n"
            "Или создайте новую задачу для проверки."
        )
    return (
        f"Активных задач: {total}, ожидают синхронизации: {unlinked}.\n"
        "Попробуйте /calendar_resync"
    )


async def _run_calendar_sync(
    message: Message,
    session: AsyncSession,
    *,
    resync: bool = False,
) -> None:
    user = await user_service.get_or_create(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )
    if not google_calendar_service.available:
        await answer_menu(message, CALENDAR_NOT_CONFIGURED)
        return
    if not user.google_refresh_token:
        await answer_menu(message, "Сначала подключите календарь: /calendar")
        return

    await answer_menu(
        message,
        "⏳ Пересинхронизирую задачи с Google Calendar…"
        if resync
        else "⏳ Синхронизирую задачи с Google Calendar…",
    )

    if not user.google_calendar_enabled:
        user.google_calendar_enabled = True

    total, linked, unlinked = await count_calendar_sync_state(session, user)
    telegram_id = message.from_user.id
    await session.commit()

    try:
        synced, failed = await sync_user_calendar_by_telegram_id(telegram_id, resync=resync)
    except TimeoutError:
        logger.error("calendar_sync timed out for user %s", telegram_id)
        await answer_menu(
            message,
            f"⏱ Синхронизация прервалась по таймауту ({SYNC_OVERALL_TIMEOUT_SEC} сек).\n"
            "Часть задач могла успеть синхронизироваться. Попробуйте /calendar_sync ещё раз.",
        )
        return
    except Exception:
        logger.exception("calendar_sync failed for user %s", telegram_id)
        await answer_menu(
            message,
            "❌ Не удалось синхронизировать календарь. Попробуйте позже или переподключите: /calendar",
        )
        return

    if synced == 0 and failed == 0:
        await answer_menu(message, _format_sync_idle_message(total, linked, unlinked))
        return

    lines = [f"📅 Синхронизация завершена: добавлено {synced}"]
    if failed:
        lines.append(f"⚠️ Ошибок: {failed}")
        lines.append("Проверьте подключение: /calendar")
    await answer_menu(message, "\n".join(lines))


@router.message(Command("calendar"))
async def cmd_calendar(message: Message, session: AsyncSession) -> None:
    if not google_calendar_service.available:
        await answer_menu(message, CALENDAR_NOT_CONFIGURED)
        return

    user = await user_service.get_or_create(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )

    if user.google_refresh_token:
        total, linked, unlinked = await count_calendar_sync_state(session, user)
        stats = f"\n\nАктивных задач: {total}"
        if total:
            stats += f" · в календаре: {linked} · ожидают: {unlinked}"
        if user.google_calendar_enabled:
            status = "подключён ✅"
        else:
            status = "подключён, синхронизация выкл (включить: /calendar_on)"
        await answer_menu(
            message,
            CALENDAR_STATUS.format(status=status, timezone=user.timezone) + stats,
        )
        return

    auth_url = google_calendar_service.build_auth_url(message.from_user.id)
    await answer_menu(message, CALENDAR_NOT_CONNECTED.format(url=auth_url))


@router.message(Command("google_code"))
async def cmd_google_code(message: Message, session: AsyncSession) -> None:
    code = extract_google_auth_code(message.text or "")
    if not code:
        await answer_menu(
            message,
            "Использование:\n/google_code КОД_ИЗ_GOOGLE\n\n"
            "Код показывается на странице после входа в Google (кнопка «Скопировать команду»).",
        )
        return

    user = await user_service.get_or_create(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )
    ok, text = await connect_google_calendar(session, user, code)
    await answer_menu(message, text)


@router.message(F.text.regexp(r"(?i)(?:code=4/|^4/0A)"))
async def msg_google_code_paste(message: Message, session: AsyncSession) -> None:
    if message.text and message.text.startswith("/calendar"):
        return
    code = extract_google_auth_code(message.text or "")
    if not code:
        return
    user = await user_service.get_or_create(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )
    ok, text = await connect_google_calendar(session, user, code)
    await answer_menu(message, text)


@router.message(Command("calendar_on"))
async def cmd_calendar_on(message: Message, session: AsyncSession) -> None:
    user = await user_service.get_or_create(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )
    if not user.google_refresh_token:
        await answer_menu(message, "Сначала подключите календарь: /calendar")
        return
    user.google_calendar_enabled = True
    await answer_menu(message, "⏳ Синхронизирую задачи с Google Calendar…")
    telegram_id = message.from_user.id
    await session.commit()
    try:
        synced, failed = await sync_user_calendar_by_telegram_id(telegram_id)
    except TimeoutError:
        await answer_menu(
            message,
            f"⏱ Синхронизация прервалась по таймауту ({SYNC_OVERALL_TIMEOUT_SEC} сек). "
            "Попробуйте /calendar_sync ещё раз.",
        )
        return
    except Exception:
        logger.exception("calendar_on sync failed for user %s", message.from_user.id)
        await answer_menu(message, "❌ Синхронизация включена, но задачи не удалось отправить. Попробуйте /calendar_sync")
        return
    msg = CALENDAR_ENABLED
    if synced:
        msg += f"\n📅 В календарь добавлено задач: {synced}"
    if failed:
        msg += f"\n⚠️ Не удалось синхронизировать: {failed}"
    await answer_menu(message, msg)


@router.message(Command("calendar_sync"))
@router.message(F.text.regexp(CALENDAR_SYNC_TEXT))
async def cmd_calendar_sync(message: Message, session: AsyncSession) -> None:
    await _run_calendar_sync(message, session)


@router.message(Command("calendar_resync"))
@router.message(F.text.regexp(CALENDAR_RESYNC_TEXT))
async def cmd_calendar_resync(message: Message, session: AsyncSession) -> None:
    await _run_calendar_sync(message, session, resync=True)


@router.message(Command("calendar_off"))
async def cmd_calendar_off(message: Message, session: AsyncSession) -> None:
    user = await user_service.get_or_create(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )
    user.google_calendar_enabled = False
    await answer_menu(message, CALENDAR_DISABLED)


@router.message(lambda m: m.text == "📅 Календарь")
async def btn_calendar(message: Message, session: AsyncSession) -> None:
    await cmd_calendar(message, session)
