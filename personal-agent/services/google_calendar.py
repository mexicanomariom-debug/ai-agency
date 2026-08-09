from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

import httplib2
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_httplib2 import AuthorizedHttp
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from config import settings
from database.models import Task, User
from services.time_utils import ensure_utc, format_google_datetime

logger = logging.getLogger(__name__)

GOOGLE_API_TIMEOUT_SEC = 15

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

    def _build_service(self, creds: Credentials):
        http = httplib2.Http(timeout=GOOGLE_API_TIMEOUT_SEC)
        authorized = AuthorizedHttp(creds, http=http)
        return build("calendar", "v3", http=authorized, cache_discovery=False)

    def _credentials(self, user: User) -> Credentials | None:
        if not user.google_refresh_token:
            return None
        creds = Credentials(
            token=None,
            refresh_token=user.google_refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.google_client_id,
            client_secret=settings.google_client_secret,
            scopes=SCOPES,
        )
        try:
            if not creds.valid and creds.refresh_token:
                creds.refresh(Request())
        except Exception:
            logger.exception("Failed to refresh Google credentials for user %s", user.telegram_id)
            return None
        return creds

    def _service(self, user: User):
        creds = self._credentials(user)
        if not creds:
            return None
        return build("calendar", "v3", credentials=creds, cache_discovery=False)

    async def _credentials_async(self, user: User) -> Credentials | None:
        try:
            return await asyncio.wait_for(
                asyncio.to_thread(self._credentials, user),
                timeout=GOOGLE_API_TIMEOUT_SEC,
            )
        except TimeoutError:
            logger.error("Google credentials refresh timed out for user %s", user.telegram_id)
            return None

    def _event_body(self, user: User, task: Task) -> dict:
        end_at = ensure_utc(task.due_at) + timedelta(minutes=30)
        return {
            "summary": task.title,
            "description": task.description or "Создано Personal Agent",
            "start": {
                "dateTime": format_google_datetime(task.due_at, user.timezone),
                "timeZone": user.timezone,
            },
            "end": {
                "dateTime": format_google_datetime(end_at, user.timezone),
                "timeZone": user.timezone,
            },
        }

    def _insert_event(self, creds: Credentials, body: dict) -> dict:
        service = self._build_service(creds)
        return service.events().insert(calendarId="primary", body=body).execute()

    def _delete_event(self, creds: Credentials, event_id: str) -> None:
        service = self._build_service(creds)
        service.events().delete(calendarId="primary", eventId=event_id).execute()

    async def create_event(self, user: User, task: Task, creds: Credentials | None = None) -> str | None:
        creds = creds or await self._credentials_async(user)
        if not creds:
            return None
        try:
            body = self._event_body(user, task)
            event = await asyncio.wait_for(
                asyncio.to_thread(self._insert_event, creds, body),
                timeout=GOOGLE_API_TIMEOUT_SEC,
            )
            return event.get("id")
        except TimeoutError:
            logger.error("Google Calendar create_event timed out for task %s", task.id)
            return None
        except Exception:
            logger.exception("Failed to create Google Calendar event for task %s", task.id)
            return None

    async def delete_event(
        self,
        user: User,
        event_id: str,
        creds: Credentials | None = None,
    ) -> None:
        creds = creds or await self._credentials_async(user)
        if not creds:
            return
        try:
            await asyncio.wait_for(
                asyncio.to_thread(self._delete_event, creds, event_id),
                timeout=GOOGLE_API_TIMEOUT_SEC,
            )
        except TimeoutError:
            logger.error("Google Calendar delete_event timed out for event %s", event_id)
        except Exception:
            logger.exception("Failed to delete Google Calendar event %s", event_id)


google_calendar_service = GoogleCalendarService()
