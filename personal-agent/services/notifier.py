from __future__ import annotations

import logging
from pathlib import Path

from aiogram import Bot
from aiogram.types import FSInputFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from bot.copy import REMINDER_CALL_CAPTION, REMINDER_MESSAGE, REMINDER_PHONE_SENT
from bot.keyboards.inline import task_actions_keyboard
from bot.keyboards.reply import main_menu_keyboard
from database.models import Task, TaskStatus
from services.tts import synthesize_voice_file
from services.twilio_calls import twilio_service

logger = logging.getLogger(__name__)


class Notifier:
    def __init__(self, bot: Bot, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._bot = bot
        self._session_factory = session_factory

    async def send_reminder(self, task_id: int) -> None:
        async with self._session_factory() as session:
            result = await session.execute(
                select(Task)
                .options(selectinload(Task.user))
                .where(Task.id == task_id, Task.status == TaskStatus.PENDING)
            )
            task = result.scalar_one_or_none()
            if not task or not task.user:
                return

            telegram_id = task.user.telegram_id
            voice_path: Path | None = None

            try:
                if task.notify_message:
                    await self._bot.send_message(
                        chat_id=telegram_id,
                        text=REMINDER_MESSAGE.format(title=task.title),
                        disable_notification=False,
                        reply_markup=main_menu_keyboard(),
                    )
                    await self._bot.send_message(
                        chat_id=telegram_id,
                        text="Быстрые действия:",
                        reply_markup=task_actions_keyboard(task.id),
                    )

                if task.notify_call:
                    voice_text = f"Напоминание. {task.title}"
                    voice_path = await synthesize_voice_file(voice_text)
                    await self._bot.send_chat_action(chat_id=telegram_id, action="record_voice")
                    await self._bot.send_voice(
                        chat_id=telegram_id,
                        voice=FSInputFile(voice_path),
                        caption=REMINDER_CALL_CAPTION.format(title=task.title),
                        disable_notification=False,
                    )

                if task.notify_phone and task.user.phone_number:
                    called = await twilio_service.call_reminder(
                        task.user.phone_number,
                        f"Напоминание. {task.title}",
                    )
                    if called:
                        await self._bot.send_message(
                            chat_id=telegram_id,
                            text=REMINDER_PHONE_SENT.format(title=task.title),
                            reply_markup=main_menu_keyboard(),
                        )

                from datetime import datetime
                from zoneinfo import ZoneInfo

                task.reminded_at = datetime.now(ZoneInfo("UTC"))
                await session.commit()
            except Exception:
                logger.exception("Failed to send reminder for task %s", task_id)
                await session.rollback()
            finally:
                if voice_path and voice_path.exists():
                    voice_path.unlink(missing_ok=True)


notifier: Notifier | None = None


def init_notifier(bot: Bot, session_factory: async_sessionmaker[AsyncSession]) -> Notifier:
    global notifier
    notifier = Notifier(bot, session_factory)
    return notifier
