from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database.models import JournalEntry, User
from services.journal_service import journal_service

logger = logging.getLogger(__name__)

KIND_LABELS = {
    "idea": "💡 идея",
    "thought": "💭 мысль",
    "decision": "⚖️ решение",
    "expense": "💸 расход",
    "mood": "🌡 настроение",
    "insight": "✨ инсайт",
}

KIND_ICONS = {
    "idea": "💡",
    "thought": "💭",
    "decision": "⚖️",
    "expense": "💸",
    "mood": "🌡",
    "insight": "✨",
}

SECTION_TITLES = {
    "idea": "💡 Идеи",
    "thought": "💭 Мысли",
    "decision": "⚖️ Решения",
    "expense": "💸 Траты",
    "mood": "🌡 Настроение",
    "insight": "✨ Инсайты",
}

_PREVIEW_LIMIT = 90
_BUTTON_PREVIEW_LIMIT = 38


@dataclass
class JournalCapture:
    kind: str
    content: str
    amount: float | None = None
    currency: str | None = None


class SmartJournalService:
    def __init__(self) -> None:
        self._openai = AsyncOpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

    def day_key_for_user(self, user: User, offset_days: int = 0) -> str:
        tz = ZoneInfo(user.timezone or "UTC")
        day = datetime.now(tz).date() + timedelta(days=offset_days)
        return day.isoformat()

    @staticmethod
    def preview_text(content: str, limit: int = _PREVIEW_LIMIT) -> str:
        from bot.utils.html import h

        one_line = " ".join(content.split())
        if len(one_line) <= limit:
            return h(one_line)
        return h(one_line[: limit - 1] + "…")

    @staticmethod
    def button_preview(content: str, limit: int = _BUTTON_PREVIEW_LIMIT) -> str:
        one_line = " ".join(content.split())
        if len(one_line) <= limit:
            return one_line
        return one_line[: limit - 1] + "…"

    def _entry_time(self, entry: JournalEntry, timezone: str) -> str:
        if not entry.created_at:
            return ""
        tz = ZoneInfo(timezone or "UTC")
        return entry.created_at.astimezone(tz).strftime("%H:%M")

    def _entry_day_label(self, entry: JournalEntry, timezone: str, *, today_key: str) -> str:
        if entry.day_key == today_key:
            return "сегодня"
        try:
            day = datetime.fromisoformat(entry.day_key).strftime("%d.%m")
        except ValueError:
            day = entry.day_key
        return day

    def format_entry(self, entry: JournalEntry, timezone: str = "UTC") -> str:
        from bot.utils.html import h

        icon = KIND_ICONS.get(entry.kind, "•")
        extra = ""
        if entry.amount is not None:
            extra = f" — {entry.amount:g} {entry.currency or ''}".rstrip()
        time_str = ""
        if entry.created_at:
            time_str = f" <i>{self._entry_time(entry, timezone)}</i>"
        return f"{icon} {h(entry.content)}{extra}{time_str}"

    def format_entry_detail(self, entry: JournalEntry, *, timezone: str = "UTC") -> str:
        from bot.utils.html import bold, h

        icon = KIND_ICONS.get(entry.kind, "📝")
        label = KIND_LABELS.get(entry.kind, entry.kind)
        lines = [
            f"{icon} {bold(label)} · #{entry.id}",
            f"<i>{entry.day_key} · {self._entry_time(entry, timezone)}</i>",
            "",
            h(entry.content),
        ]
        if entry.amount is not None:
            lines.append(f"\n💰 {entry.amount:g} {entry.currency or ''}".rstrip())
        return "\n".join(lines)

    def format_day_entries(
        self,
        entries: list[JournalEntry],
        *,
        title: str,
        empty_hint: str,
        filter_kind: str | None = None,
        timezone: str = "UTC",
        today_key: str | None = None,
        ideas_feed: bool = False,
    ) -> str:
        from bot.utils.html import bold, h

        if filter_kind:
            entries = [e for e in entries if e.kind == filter_kind]
            title = SECTION_TITLES.get(filter_kind, title)

        if not entries:
            return f"{bold(title)}\n\n{empty_hint}"

        if ideas_feed and filter_kind == "idea":
            return self._format_ideas_feed(entries, title=title, timezone=timezone, today_key=today_key or "")

        grouped: dict[str, list[JournalEntry]] = {}
        for entry in entries:
            grouped.setdefault(entry.kind, []).append(entry)

        order = ("idea", "thought", "decision", "expense", "mood", "insight")
        lines = [bold(title), f"<i>Записей: {len(entries)}</i>", ""]
        for kind in order:
            items = grouped.get(kind)
            if not items:
                continue
            if not filter_kind:
                lines.append(bold(SECTION_TITLES.get(kind, kind)))
            for idx, entry in enumerate(items, start=1):
                lines.extend(
                    self._format_entry_card_lines(
                        entry,
                        index=idx,
                        timezone=timezone,
                        today_key=today_key or entry.day_key,
                        compact=bool(filter_kind),
                    )
                )
            if not filter_kind:
                lines.append("")

        while lines and not lines[-1].strip():
            lines.pop()
        return "\n".join(lines)

    def _format_ideas_feed(
        self,
        entries: list[JournalEntry],
        *,
        title: str,
        timezone: str,
        today_key: str,
    ) -> str:
        from bot.utils.html import bold

        lines = [
            bold(title),
            f"<i>{len(entries)} идей · новые сверху</i>",
            "",
        ]
        for idx, entry in enumerate(entries, start=1):
            lines.extend(
                self._format_entry_card_lines(
                    entry,
                    index=idx,
                    timezone=timezone,
                    today_key=today_key,
                    compact=True,
                    show_day=True,
                )
            )
        return "\n".join(lines)

    def _format_entry_card_lines(
        self,
        entry: JournalEntry,
        *,
        index: int,
        timezone: str,
        today_key: str,
        compact: bool,
        show_day: bool = False,
    ) -> list[str]:
        from bot.utils.html import h

        icon = KIND_ICONS.get(entry.kind, "•")
        time_part = self._entry_time(entry, timezone)
        day_part = ""
        if show_day:
            day_part = f"{self._entry_day_label(entry, timezone, today_key=today_key)} · "
        header = f"<b>#{entry.id}</b> · {day_part}{time_part}"
        preview = self.preview_text(entry.content)
        extra = ""
        if entry.amount is not None:
            extra = f"\n💰 {entry.amount:g} {h(entry.currency or '')}".rstrip()

        if compact:
            return [f"{icon} {header}", preview + extra, ""]

        lines = [f"{index}. {icon} {header}", preview + extra]
        if not compact:
            lines.append("")
        return lines

    async def capture_text(
        self,
        session: AsyncSession,
        user: User,
        text: str,
    ) -> list[str]:
        captures = await self._extract(text)
        if not captures and self._openai:
            captures = [JournalCapture(kind="idea", content=text.strip()[:500])]
        elif not captures:
            captures = [JournalCapture(kind="thought", content=text.strip()[:500])]

        ack_lines: list[str] = []
        for item in captures[:3]:
            await journal_service.add(
                session,
                user,
                kind=item.kind,
                content=item.content,
                amount=item.amount,
                currency=item.currency,
            )
            label = KIND_LABELS.get(item.kind, "📝 запись")
            extra = ""
            if item.amount is not None:
                extra = f" — {item.amount:g} {item.currency or ''}".rstrip()
            ack_lines.append(f"{label}: {item.content}{extra}")
        return ack_lines

    async def summarize_day(
        self,
        session: AsyncSession,
        user: User,
        day_key: str | None = None,
    ) -> str:
        day_key = day_key or self.day_key_for_user(user)
        entries = await journal_service.list_for_day(session, user, day_key)
        if not entries:
            return "📔 За этот день записей нет — напишите идею или мысль, я всё сохраню."

        if not self._openai:
            return self._fallback_summary(entries, day_key)

        items = []
        for entry in entries:
            label = KIND_LABELS.get(entry.kind, entry.kind)
            extra = ""
            if entry.amount is not None:
                extra = f" ({entry.amount:g} {entry.currency or ''})"
            items.append(f"- [{label}] {entry.content}{extra}")

        try:
            response = await self._openai.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Ты умный блокнот личного агента. Сделай краткую сводку дня по записям "
                            "пользователя на русском, HTML-разметка Telegram (<b>, <i>).\n"
                            "Структура:\n"
                            "📊 <b>Сводка дня</b>\n"
                            "• Главные идеи (если есть)\n"
                            "• Решения и настроение\n"
                            "• Траты (сумма если можно)\n"
                            "• 1 короткий вопрос или совет на завтра\n"
                            "Не больше 900 символов. Не выдумывай то, чего нет в записях."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"День {day_key}:\n" + "\n".join(items),
                    },
                ],
                temperature=0.5,
            )
            text = (response.choices[0].message.content or "").strip()
            return text or self._fallback_summary(entries, day_key)
        except Exception:
            logger.exception("Journal summary failed")
            return self._fallback_summary(entries, day_key)

    def _fallback_summary(self, entries: list[JournalEntry], day_key: str) -> str:
        from bot.utils.html import bold

        counts: dict[str, int] = {}
        for entry in entries:
            counts[entry.kind] = counts.get(entry.kind, 0) + 1
        parts = [f"{KIND_ICONS.get(k, '•')} {counts[k]}" for k in counts]
        return (
            f"📊 {bold('Сводка')} за {day_key}\n"
            f"Записей: {len(entries)} ({', '.join(parts)})\n\n"
            + "\n".join(self.format_entry(e, "UTC") for e in entries[-5:])
        )

    async def _extract(self, text: str) -> list[JournalCapture]:
        if not self._openai:
            return self._heuristic_extract(text)

        stripped = text.strip()
        if len(stripped) < 2:
            return []

        try:
            response = await self._openai.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Ты умный блокнот. Разбери сообщение на записи для дневника.\n"
                            "Типы: idea (идея/проект/задумка), thought (мысль/наблюдение), "
                            "decision (решение с причиной), expense (трата), mood (настроение/энергия).\n"
                            "Не создавай задачи с временем — только записи блокнота.\n"
                            "Одно сообщение может дать 1-3 записи.\n"
                            'JSON: {"captures": [{"kind": "...", "content": "...", '
                            '"amount": null, "currency": null}]}'
                        ),
                    },
                    {"role": "user", "content": stripped},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
            )
            data = json.loads(response.choices[0].message.content or "{}")
            result: list[JournalCapture] = []
            for item in data.get("captures", []):
                kind = str(item.get("kind", "")).lower()
                content = str(item.get("content", "")).strip()
                if kind not in KIND_LABELS or len(content) < 2:
                    continue
                amount = item.get("amount")
                result.append(
                    JournalCapture(
                        kind=kind,
                        content=content[:500],
                        amount=float(amount) if amount is not None else None,
                        currency=(str(item["currency"])[:8] if item.get("currency") else None),
                    )
                )
            return result[:3]
        except Exception:
            logger.exception("Smart journal extract failed")
            return self._heuristic_extract(text)

    def _heuristic_extract(self, text: str) -> list[JournalCapture]:
        stripped = text.strip()
        lower = stripped.lower()
        if any(w in lower for w in ("идея", "idea", "придумал", "задумка")):
            kind = "idea"
        elif any(w in lower for w in ("решил", "решение", "буду ", "не буду")):
            kind = "decision"
        elif any(w in lower for w in ("потратил", "купил", "обед", "руб", "peso", "$")):
            kind = "expense"
        elif any(w in lower for w in ("устал", "настроение", "чувствую", "энергия")):
            kind = "mood"
        else:
            kind = "thought"
        return [JournalCapture(kind=kind, content=stripped[:500])]


smart_journal_service = SmartJournalService()
