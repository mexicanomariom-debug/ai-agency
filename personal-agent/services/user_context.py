from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from services.journal_service import journal_service
from services.task_flow import format_due_at
from services.user_service import task_service


@dataclass
class UserContext:
    timezone: str
    now_local: datetime
    day_key: str
    today_tasks: list[str] = field(default_factory=list)
    overdue_tasks: list[str] = field(default_factory=list)
    soon_tasks: list[str] = field(default_factory=list)
    journal_today: list[str] = field(default_factory=list)
    journal_recent: list[str] = field(default_factory=list)
    pending_count: int = 0

    def to_prompt_block(self) -> str:
        lines = [
            f"Сейчас: {self.now_local.strftime('%Y-%m-%d %H:%M')} ({self.timezone})",
        ]
        if self.today_tasks:
            lines.append("Задачи на сегодня:\n" + "\n".join(f"- {t}" for t in self.today_tasks))
        else:
            lines.append("Задач на сегодня нет.")
        if self.overdue_tasks:
            lines.append("Просрочено:\n" + "\n".join(f"- {t}" for t in self.overdue_tasks))
        if self.soon_tasks:
            lines.append("Скоро (2 ч):\n" + "\n".join(f"- {t}" for t in self.soon_tasks))
        if self.journal_today:
            lines.append("Записи дня:\n" + "\n".join(f"- {t}" for t in self.journal_today))
        if self.journal_recent:
            lines.append("Недавние записи:\n" + "\n".join(f"- {t}" for t in self.journal_recent))
        lines.append(f"Активных задач всего: {self.pending_count}")
        return "\n\n".join(lines)


async def build_user_context(session: AsyncSession, user: User) -> UserContext:
    tz = ZoneInfo(user.timezone)
    now_local = datetime.now(tz)
    day_key = now_local.date().isoformat()
    from datetime import timedelta

    soon_utc = (now_local.replace(second=0, microsecond=0)).astimezone(ZoneInfo("UTC"))

    soon_end = (now_local + timedelta(hours=2)).astimezone(ZoneInfo("UTC"))

    today = await task_service.list_today(session, user)
    pending = await task_service.list_pending(session, user)
    now_utc = datetime.now(ZoneInfo("UTC"))

    overdue = [t for t in pending if t.due_at < now_utc]
    soon = [t for t in pending if soon_utc <= t.due_at <= soon_end]

    journal_today = await journal_service.list_for_day(session, user, day_key)
    journal_recent = await journal_service.list_recent(session, user, limit=8)

    kind_labels = {
        "idea": "💡",
        "expense": "💸",
        "thought": "💭",
        "decision": "⚖️",
        "mood": "🌡",
        "insight": "✨",
    }

    def fmt_journal(entry) -> str:
        label = kind_labels.get(entry.kind, "•")
        extra = ""
        if entry.amount is not None:
            extra = f" ({entry.amount:g} {entry.currency or ''})".rstrip()
        return f"{label} {entry.content}{extra}"

    return UserContext(
        timezone=user.timezone,
        now_local=now_local,
        day_key=day_key,
        today_tasks=[
            f"#{t.id} {t.title} — {format_due_at(t.due_at, user.timezone)}"
            for t in today
        ],
        overdue_tasks=[
            f"#{t.id} {t.title} — было {format_due_at(t.due_at, user.timezone)}"
            for t in overdue[:8]
        ],
        soon_tasks=[
            f"#{t.id} {t.title} — {format_due_at(t.due_at, user.timezone)}"
            for t in soon[:5]
        ],
        journal_today=[fmt_journal(e) for e in journal_today if e.kind != "insight"],
        journal_recent=[fmt_journal(e) for e in journal_recent if e.kind != "insight"][-5:],
        pending_count=len(pending),
    )
