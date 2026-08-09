from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from config import settings
from database.models import Task, User

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]
CLIENT_CONFIG = {
    "web": {
        "client_id": settings.google_client_id,
        "client_secret": settings.google_client_secret,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": [settings.google_redirect_uri],
    }
}


class GoogleCalendarService:
    @property
    def available(self) -> bool:
        return settings.has_google_calendar

    def build_auth_url(self, telegram_id: int) -> str:
        flow = Flow.from_client_config(CLIENT_CONFIG, scopes=SCOPES, state=str(telegram_id))
        flow.redirect_uri = settings.google_redirect_uri
        auth_url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
        )
        return auth_url

    async def exchange_code(self, code: str) -> str | None:
        try:
            flow = Flow.from_client_config(CLIENT_CONFIG, scopes=SCOPES)
            flow.redirect_uri = settings.google_redirect_uri
            flow.fetch_token(code=code)
            credentials = flow.credentials
            return credentials.refresh_token or credentials.token
        except Exception:
            logger.exception("Google OAuth token exchange failed")
            return None

    def _credentials(self, user: User) -> Credentials | None:
        if not user.google_refresh_token:
            return None
        return Credentials(
            token=None,
            refresh_token=user.google_refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.google_client_id,
            client_secret=settings.google_client_secret,
            scopes=SCOPES,
        )

    def _service(self, user: User):
        creds = self._credentials(user)
        if not creds:
            return None
        return build("calendar", "v3", credentials=creds, cache_discovery=False)

    async def create_event(self, user: User, task: Task) -> str | None:
        service = self._service(user)
        if not service:
            return None
        try:
            start = task.due_at.astimezone(ZoneInfo(user.timezone))
            end_minute = start.minute + 30
            if end_minute >= 60:
                end = start.replace(hour=start.hour + 1, minute=end_minute - 60)
            else:
                end = start.replace(minute=end_minute)
            body = {
                "summary": task.title,
                "description": task.description or "Создано Personal Agent",
                "start": {"dateTime": start.isoformat(), "timeZone": user.timezone},
                "end": {"dateTime": end.isoformat(), "timeZone": user.timezone},
            }
            event = service.events().insert(calendarId="primary", body=body).execute()
            return event.get("id")
        except Exception:
            logger.exception("Failed to create Google Calendar event")
            return None

    async def delete_event(self, user: User, event_id: str) -> None:
        service = self._service(user)
        if not service:
            return
        try:
            service.events().delete(calendarId="primary", eventId=event_id).execute()
        except Exception:
            logger.exception("Failed to delete Google Calendar event %s", event_id)


google_calendar_service = GoogleCalendarService()
