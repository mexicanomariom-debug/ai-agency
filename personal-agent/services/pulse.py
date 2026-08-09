from __future__ import annotations

import json
import logging
from datetime import datetime

from aiogram import Bot
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from zoneinfo import ZoneInfo

from config import settings
from database.models import User
from openai import AsyncOpenAI
from services.user_context import build_user_context

logger = logging.getLogger(__name__)

PULSE_ACTIVE_HOURS = range(8, 23)


class PulseService:
    def __init__(self, bot: Bot, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._bot = bot
        self._session_factory = session_factory
        self._openai = AsyncOpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

    async def run_hourly(self) -> None:
        if not self._openai:
            return
        async with self._session_factory() as session:
            result = await session.execute(select(User))
            users = result.scalars().all()
            for user in users:
                try:
                    await self._maybe_pulse(session, user)
                    await self._maybe_night(session, user)
                except Exception:
                    logger.exception("Pulse failed for user %s", user.telegram_id)
            await session.commit()

    async def _maybe_pulse(self, session: AsyncSession, user: User) -> None:
        if not user.pulse_enabled:
            return
        tz = ZoneInfo(user.timezone)
        now_local = datetime.now(tz)
        if now_local.hour not in PULSE_ACTIVE_HOURS:
            return

        hour_key = now_local.strftime("%Y-%m-%d-%H")
        if user.pulse_last_hour == hour_key:
            return

        context = await build_user_context(session, user)
        if now_local.hour == user.digest_hour:
            text = await self._morning_pulse(context)
            if text:
                await self._bot.send_message(chat_id=user.telegram_id, text=text)
                user.digest_last_sent = now_local.date().isoformat()
        else:
            text = await self._heartbeat_pulse(context)
            if text:
                await self._bot.send_message(chat_id=user.telegram_id, text=text)

        user.pulse_last_hour = hour_key

    async def _maybe_night(self, session: AsyncSession, user: User) -> None:
        if not user.night_enabled:
            return
        tz = ZoneInfo(user.timezone)
        now_local = datetime.now(tz)
        if now_local.hour != user.night_hour or now_local.minute >= 15:
            return

        today = now_local.date().isoformat()
        if user.night_last_sent == today:
            return

        from services.journal_service import journal_service

        context = await build_user_context(session, user)
        text = await self._night_process(context)
        if text:
            await self._bot.send_message(chat_id=user.telegram_id, text=text)
            await journal_service.add(
                session,
                user,
                kind="insight",
                content=text[:2000],
                day_key=today,
            )
            user.night_last_sent = today

    async def _morning_pulse(self, context) -> str | None:
        response = await self._openai.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Ты личный агент. Утренний пульс — коротко, по делу, на русском, HTML.\n"
                        "Формат:\n"
                        "☀️ <b>Доброе утро!</b>\n"
                        "1-2 предложения: что важно сегодня и почему\n"
                        "Список задач (если есть)\n"
                        "Одна мысль или вопрос на день\n"
                        "Не больше 1200 символов. Без воды."
                    ),
                },
                {"role": "user", "content": context.to_prompt_block()},
            ],
            temperature=0.6,
        )
        return (response.choices[0].message.content or "").strip() or None

    async def _heartbeat_pulse(self, context) -> str | None:
        if not context.overdue_tasks and not context.soon_tasks:
            return None

        response = await self._openai.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Ты пульс личного агента. Пишешь ТОЛЬКО если есть повод беспокоить пользователя.\n"
                        'Ответ JSON: {"notify": true/false, "message": "..."}\n'
                        "notify=true если: просрочено, скоро важное, противоречие в записях, "
                        "задача переносилась много раз.\n"
                        "message — 1-3 предложения на русском, HTML, с конкретикой. "
                        "Если всё ок — notify=false."
                    ),
                },
                {"role": "user", "content": context.to_prompt_block()},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        data = json.loads(response.choices[0].message.content or "{}")
        if not data.get("notify"):
            return None
        message = (data.get("message") or "").strip()
        if not message:
            return None
        return f"💓 {message}"

    async def _night_process(self, context) -> str | None:
        if not context.journal_today and not context.today_tasks and context.pending_count == 0:
            return (
                "🌙 <b>Итог дня</b>\n\n"
                "Сегодня тихо — ни задач, ни записей. "
                "Завтра можно начать с одного маленького дела."
            )

        response = await self._openai.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Ты ночной процессор личного агента. Подведи итог дня на русском, HTML.\n"
                        "Формат:\n"
                        "🌙 <b>Итог дня</b>\n"
                        "• Что заметно (задачи, настроение, решения, траты)\n"
                        "• Один инсайт или связь между записями\n"
                        "• Один вопрос на завтра (конкретный)\n"
                        "Тон: спокойный, без морали. До 1000 символов."
                    ),
                },
                {"role": "user", "content": context.to_prompt_block()},
            ],
            temperature=0.5,
        )
        return (response.choices[0].message.content or "").strip() or None


pulse_service: PulseService | None = None


def init_pulse_service(bot: Bot, session_factory: async_sessionmaker[AsyncSession]) -> PulseService:
    global pulse_service
    pulse_service = PulseService(bot, session_factory)
    return pulse_service
