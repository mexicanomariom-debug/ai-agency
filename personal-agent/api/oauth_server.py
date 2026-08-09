from __future__ import annotations

import json
import logging

from aiohttp import web
from aiohttp.web_middlewares import middleware
from aiogram import Bot
from sqlalchemy import select

from config import settings
from database.models import User
from database.session import async_session_factory
from services.calendar_sync import sync_user_calendar_by_telegram_id
from services.google_calendar import google_calendar_service

logger = logging.getLogger(__name__)

VERCEL_ORIGIN = "https://ai-agency-drab.vercel.app"


@middleware
async def cors_middleware(request: web.Request, handler):
    if request.method == "OPTIONS":
        response = web.Response()
    else:
        response = await handler(request)
    origin = request.headers.get("Origin", "")
    if origin == VERCEL_ORIGIN or origin.endswith(".vercel.app"):
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, X-Internal-Secret"
    return response


async def google_oauth_callback(request: web.Request) -> web.Response:
    bot: Bot = request.app["bot"]
    code = request.query.get("code")
    state = request.query.get("state")
    error = request.query.get("error")

    if error:
        return web.Response(text=f"Ошибка авторизации: {error}", content_type="text/html; charset=utf-8")

    if not code or not state or not state.isdigit():
        return web.Response(text="Некорректный ответ OAuth", content_type="text/html; charset=utf-8")

    telegram_id = int(state)
    refresh_token = await google_calendar_service.exchange_code(code)
    if not refresh_token:
        return web.Response(text="Не удалось получить токен Google", content_type="text/html; charset=utf-8")

    saved = await _save_google_token(telegram_id, refresh_token)
    if not saved:
        return web.Response(text="Пользователь не найден", content_type="text/html; charset=utf-8")

    await _notify_calendar_connected(bot, telegram_id)

    return web.Response(
        text="<h2>Google Calendar подключён!</h2><p>Можете вернуться в Telegram.</p>",
        content_type="text/html; charset=utf-8",
    )


async def internal_google_token(request: web.Request) -> web.Response:
    if settings.internal_api_secret:
        secret = request.headers.get("X-Internal-Secret", "")
        if secret != settings.internal_api_secret:
            return web.json_response({"error": "unauthorized"}, status=401)

    try:
        data = await request.json()
    except json.JSONDecodeError:
        return web.json_response({"error": "invalid json"}, status=400)

    telegram_id = data.get("telegram_id")
    refresh_token = data.get("refresh_token")
    code = data.get("code")

    if not isinstance(telegram_id, int):
        return web.json_response({"error": "missing telegram_id"}, status=400)

    if isinstance(code, str) and code.strip():
        refresh_token = await google_calendar_service.exchange_code(code.strip())
        if not refresh_token:
            return web.json_response({"error": "code exchange failed"}, status=400)
    elif not refresh_token:
        return web.json_response({"error": "missing code or refresh_token"}, status=400)

    saved = await _save_google_token(telegram_id, refresh_token)
    if not saved:
        return web.json_response({"error": "save failed"}, status=500)

    bot: Bot = request.app["bot"]
    await _notify_calendar_connected(bot, telegram_id)

    return web.json_response({"ok": True})


async def _save_google_token(telegram_id: int, refresh_token: str) -> bool:
    if not refresh_token or not refresh_token.strip():
        logger.error("Empty refresh_token for telegram_id=%s", telegram_id)
        return False
    try:
        async with async_session_factory() as session:
            result = await session.execute(select(User).where(User.telegram_id == telegram_id))
            user = result.scalar_one_or_none()
            if not user:
                user = User(
                    telegram_id=telegram_id,
                    timezone=settings.default_timezone,
                )
                session.add(user)
                await session.flush()
            user.google_refresh_token = refresh_token.strip()
            user.google_calendar_enabled = True
            await session.commit()
            logger.info("Google token saved for telegram_id=%s user_id=%s", telegram_id, user.id)
        return True
    except Exception:
        logger.exception("Failed to save Google token for telegram_id=%s", telegram_id)
        return False


async def _notify_calendar_connected(bot: Bot, telegram_id: int) -> None:
    synced, failed = await sync_user_calendar_by_telegram_id(telegram_id)
    text = "✅ Google Calendar подключён!"
    if synced:
        text += f"\n📅 В календарь добавлено задач: {synced}"
    if failed:
        text += f"\n⚠️ Не удалось синхронизировать: {failed}"
    if not synced and not failed:
        text += "\nНовые задачи будут попадать в календарь автоматически."
    try:
        await bot.send_message(telegram_id, text)
    except Exception:
        logger.exception("Failed to notify user %s about calendar connect", telegram_id)


async def health(request: web.Request) -> web.Response:
    return web.json_response(
        {
            "ok": True,
            "google_calendar": google_calendar_service.available,
        }
    )


def create_oauth_app(bot: Bot) -> web.Application:
    app = web.Application(middlewares=[cors_middleware])
    app["bot"] = bot
    app.router.add_get("/health", health)
    app.router.add_get("/oauth/google/callback", google_oauth_callback)
    app.router.add_route("OPTIONS", "/internal/google-token", _options_internal)
    app.router.add_post("/internal/google-token", internal_google_token)
    return app


async def _options_internal(_request: web.Request) -> web.Response:
    return web.Response()


async def start_oauth_server(bot: Bot) -> web.AppRunner | None:
    app = create_oauth_app(bot)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", settings.oauth_server_port)
    await site.start()
    if google_calendar_service.available:
        logger.info("OAuth server listening on port %s (Google Calendar enabled)", settings.oauth_server_port)
    else:
        logger.warning(
            "OAuth server listening on port %s (Google Calendar disabled — set GOOGLE_CLIENT_ID/SECRET)",
            settings.oauth_server_port,
        )
    return runner
