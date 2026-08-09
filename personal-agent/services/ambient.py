from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass

from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database.models import User
from services.journal_service import journal_service

logger = logging.getLogger(__name__)

SKIP_PATTERNS = (
    r"^/[\w_]+$",
    r"^(привет|hello|hi|ок|ok|да|нет|спасибо)$",
)

KIND_LABELS = {
    "expense": "💸 расход",
    "thought": "💭 мысль",
    "decision": "⚖️ решение",
    "mood": "🌡 настроение",
}


@dataclass
class AmbientCapture:
    kind: str
    content: str
    amount: float | None = None
    currency: str | None = None


class AmbientService:
    def __init__(self) -> None:
        self._openai = AsyncOpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

    def _should_skip(self, text: str) -> bool:
        stripped = text.strip().lower()
        if len(stripped) < 8:
            return True
        for pattern in SKIP_PATTERNS:
            if re.match(pattern, stripped, re.IGNORECASE):
                return True
        return False

    async def capture_from_text(
        self,
        session: AsyncSession,
        user: User,
        text: str,
    ) -> list[str]:
        if not user.ambient_enabled or not self._openai or self._should_skip(text):
            return []

        captures = await self._extract(text)
        if not captures:
            return []

        ack_lines: list[str] = []
        for item in captures:
            await journal_service.add(
                session,
                user,
                kind=item.kind,
                content=item.content,
                amount=item.amount,
                currency=item.currency,
            )
            label = KIND_LABELS.get(item.kind, "📝")
            extra = ""
            if item.amount is not None:
                extra = f" — {item.amount:g} {item.currency or ''}".rstrip()
            ack_lines.append(f"{label}: {item.content}{extra}")
        return ack_lines

    async def _extract(self, text: str) -> list[AmbientCapture]:
        try:
            response = await self._openai.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Ты ambient-слой личного агента. Извлеки из сообщения скрытые записи "
                            "для дневника — только если они явно есть. Не выдумывай.\n"
                            "Типы: expense (трата), thought (мысль/идея), decision (решение с причиной), "
                            "mood (настроение/энергия/сон).\n"
                            "Не извлекай задачи с временем — их обрабатывает другой модуль.\n"
                            'Ответ JSON: {"captures": [{"kind": "...", "content": "...", '
                            '"amount": null, "currency": null}]}\n'
                            "Если нечего извлекать — пустой captures."
                        ),
                    },
                    {"role": "user", "content": text},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
            )
            data = json.loads(response.choices[0].message.content or "{}")
            result: list[AmbientCapture] = []
            for item in data.get("captures", []):
                kind = str(item.get("kind", "")).lower()
                content = str(item.get("content", "")).strip()
                if kind not in KIND_LABELS or len(content) < 2:
                    continue
                amount = item.get("amount")
                result.append(
                    AmbientCapture(
                        kind=kind,
                        content=content[:500],
                        amount=float(amount) if amount is not None else None,
                        currency=(str(item["currency"])[:8] if item.get("currency") else None),
                    )
                )
            return result[:3]
        except Exception:
            logger.exception("Ambient extract failed")
            return []


ambient_service = AmbientService()
