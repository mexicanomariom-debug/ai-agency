from __future__ import annotations

import logging

from twilio.rest import Client

from config import settings

logger = logging.getLogger(__name__)


class TwilioCallService:
    def __init__(self) -> None:
        self._client = (
            Client(settings.twilio_account_sid, settings.twilio_auth_token)
            if settings.has_twilio
            else None
        )

    @property
    def available(self) -> bool:
        return self._client is not None

    async def call_reminder(self, phone_number: str, text: str) -> bool:
        if not self._client:
            return False
        safe_text = text.replace("&", "и").replace("<", "").replace(">", "")
        twiml = f'<Response><Say language="ru-RU">{safe_text}</Say></Response>'
        try:
            self._client.calls.create(
                to=phone_number,
                from_=settings.twilio_from_number,
                twiml=twiml,
            )
            return True
        except Exception:
            logger.exception("Twilio call failed to %s", phone_number)
            return False


twilio_service = TwilioCallService()
