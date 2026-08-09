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
