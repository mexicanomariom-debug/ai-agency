"""AI verification for recon alerts."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from openai import AsyncOpenAI

from config import settings

logger = logging.getLogger(__name__)


@dataclass
class VerificationResult:
    verdict: str
    confidence: float
    summary: str
    notify: bool


@dataclass
class InterestResult:
    relevant: bool
    summary: str
    confidence: float


class ReconVerifier:
    def __init__(self) -> None:
        self._openai = AsyncOpenAI(api_key=settings.openai_api_key) if settings.has_openai else None

    async def verify_change(
        self,
        *,
        source_label: str,
        old_preview: str | None,
        new_content: str,
        source_type: str,
    ) -> VerificationResult:
        if not self._openai:
            return VerificationResult(
                verdict="info",
                confidence=0.5,
                summary="Обнаружено изменение. OPENAI_API_KEY не настроен — верификация пропущена.",
                notify=True,
            )

        prompt = (
            f"Источник ({source_type}): {source_label}\n\n"
            f"Было:\n{old_preview or '—'}\n\n"
            f"Стало:\n{new_content[:2500]}\n\n"
            "Оцени: это важное событие/новость? Насколько достоверно звучит?\n"
            "Ответ JSON: "
            '{"verdict":"confirmed|unconfirmed|contradicted|unknown|info",'
            '"confidence":0.0-1.0,"summary":"кратко по-русски","notify":true|false}'
        )
        try:
            response = await self._openai.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Ты аналитик OSINT. Проверяй факты осторожно, без выдумок. "
                            "notify=true только если событие важное для пользователя."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
            )
            data = json.loads(response.choices[0].message.content or "{}")
            return VerificationResult(
                verdict=str(data.get("verdict") or "unknown"),
                confidence=float(data.get("confidence") or 0.5),
                summary=str(data.get("summary") or "Изменение в источнике."),
                notify=bool(data.get("notify", True)),
            )
        except Exception:
            logger.exception("Recon verification failed")
            return VerificationResult(
                verdict="unknown",
                confidence=0.0,
                summary="Не удалось верифицировать автоматически.",
                notify=True,
            )

    async def matches_interest(
        self,
        *,
        filter_query: str,
        text: str,
        source_label: str,
    ) -> InterestResult:
        if not filter_query.strip():
            return InterestResult(relevant=True, summary="Фильтр не задан.", confidence=1.0)

        if not self._openai:
            lowered_query = filter_query.lower()
            relevant = any(word in text.lower() for word in lowered_query.split() if len(word) > 3)
            return InterestResult(
                relevant=relevant,
                summary="Совпадение по ключевым словам (без AI)." if relevant else "Не совпало с интересом.",
                confidence=0.4 if relevant else 0.2,
            )

        prompt = (
            f"Источник: {source_label}\n"
            f"Интерес пользователя: {filter_query}\n\n"
            f"Сообщение/новость:\n{text[:2000]}\n\n"
            "Это сообщение относится к интересу пользователя? "
            "Ответ JSON: "
            '{"relevant":true|false,"confidence":0.0-1.0,"summary":"кратко по-русски почему да/нет"}'
        )
        try:
            response = await self._openai.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Ты фильтр OSINT-алертов. relevant=true только если сообщение явно про интерес пользователя. "
                            "Игнорируй рекламу, оффтоп и общие новости не по теме."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
            )
            data = json.loads(response.choices[0].message.content or "{}")
            return InterestResult(
                relevant=bool(data.get("relevant")),
                summary=str(data.get("summary") or ""),
                confidence=float(data.get("confidence") or 0.5),
            )
        except Exception:
            logger.exception("Interest match failed")
            return InterestResult(relevant=False, summary="Не удалось оценить релевантность.", confidence=0.0)

    async def verify_claim(self, claim: str) -> VerificationResult:
        if not self._openai:
            return VerificationResult(
                verdict="unknown",
                confidence=0.0,
                summary="Нужен OPENAI_API_KEY для верификации.",
                notify=True,
            )

        prompt = (
            f"Проверь утверждение на достоверность (без доступа к интернету — оцени логику и типичные признаки фейка):\n\n"
            f"{claim[:3000]}\n\n"
            'JSON: {"verdict":"confirmed|unconfirmed|contradicted|unknown","confidence":0-1,'
            '"summary":"по-русски","notify":true}'
        )
        try:
            response = await self._openai.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": "Ты фактчекер. Будь осторожен, указывай неопределённость."},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
            )
            data = json.loads(response.choices[0].message.content or "{}")
            return VerificationResult(
                verdict=str(data.get("verdict") or "unknown"),
                confidence=float(data.get("confidence") or 0.5),
                summary=str(data.get("summary") or ""),
                notify=True,
            )
        except Exception:
            logger.exception("Claim verification failed")
            return VerificationResult(
                verdict="unknown",
                confidence=0.0,
                summary="Ошибка верификации.",
                notify=True,
            )


recon_verifier = ReconVerifier()
